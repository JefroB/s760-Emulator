"""
tests/test_gate_array_mame.py — Dedicated regression tests for Roland Gate Array MMIO, AK93C45 EEPROM, and Interrupt Subsystem.
Verifies cycle-accurate register behavior, status flags, SIMM memory banking, serial EEPROM protocol, and 60Hz Timer / Peripheral IRQ delivery.
"""

import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER_PATH = os.path.join(ROOT, "mame-source", "src", "mame", "roland", "s760.cpp")


class RolandGateArraySimulator:
    """Python reference simulator mirroring s760_state Gate Array, AK93C45, and Interrupt Subsystem implementation."""
    IRQ_TIMER_60HZ = 0x01
    IRQ_FDC        = 0x02
    # Bit 2 (0x04) is Peripheral Bus Ready status flag
    IRQ_SCSI       = 0x08
    IRQ_VDP_VBLANK = 0x10
    IRQ_MIDI_RX    = 0x20

    def __init__(self):
        self.mmio = [0] * 16
        self.ga_ctrl = 0x80
        self.ga_status = 0x04  # Bit 2 = Bus Ready
        self.simm_bank = 0x00
        self.ga_chip_select = 0x00
        self.dsp_cmd_latch = 0x00
        self.dsp_addr_latch = 0x00
        self.eeprom_latch = 0x00
        self.eeprom_do = 0x00
        self.peripherals_enabled = False

        # Interrupt Subsystem State
        self.irq_pending = 0
        self.irq_mask = 0x3B  # Bits 0, 1, 3, 4, 5 unmasked
        self.int_line_asserted = False

        # 64 x 16-bit EEPROM array
        self.eeprom_data = [0] * 64
        self.eeprom_data[0] = 0x414A  # Roland Magic ID ('AJ')
        self.eeprom_data[1] = 0x0224  # Version 2.24
        self.eeprom_data[2] = 0x0007  # SCSI Host ID 7
        self.eeprom_data[3] = 0x01B8  # Master Tune: 440.0 Hz
        self.eeprom_data[4] = 0x0008  # LCD Contrast: 8
        self.eeprom_data[5] = 0x0002  # Mouse Speed: 2x

        self.eeprom_shift_reg = 0
        self.eeprom_bit_count = 0
        self.eeprom_state = 0  # 0=IDLE, 1=CMD, 2=DATA_IN, 3=SHIFT_OUT
        self.eeprom_cs = False
        self.eeprom_clk = False
        self.eeprom_di = False
        self.eeprom_ewen = False

    def trigger_irq(self, source_mask):
        """Assert hardware interrupt source in Gate Array."""
        self.irq_pending |= (source_mask & ~0x04)
        self.ga_status = (self.ga_status & 0x04) | self.irq_pending
        self.check_irq_state()

    def clear_irq(self, clear_mask):
        """Acknowledge / clear interrupt sources (write-to-clear)."""
        self.irq_pending &= ~clear_mask
        self.ga_status = (self.ga_status & 0x04) | self.irq_pending
        self.check_irq_state()

    def check_irq_state(self):
        """Update CPU External Interrupt Line (MCS-96 EXTINT / INT)."""
        should_assert = bool((self.irq_pending & self.irq_mask) != 0)
        self.int_line_asserted = should_assert

    def read(self, offset):
        reg = offset & 0x1F
        if reg == 0x00:
            return self.ga_ctrl | 0x80
        elif reg == 0x01:
            return (self.ga_status & 0x04) | self.irq_pending
        elif reg == 0x02:
            return self.simm_bank
        elif reg == 0x03:
            return 0x00
        elif reg == 0x04:
            return self.ga_chip_select
        elif reg == 0x06:
            return self.dsp_cmd_latch
        elif reg == 0x08:
            return self.dsp_addr_latch
        elif reg == 0x0E:
            return self.eeprom_latch
        elif reg == 0x10:
            return self.eeprom_do & 0x01
        elif reg == 0x12:
            return 0x00
        return self.mmio[offset & 0x0F]

    def write(self, offset, data):
        reg = offset & 0x1F
        if reg == 0x12:
            return
        self.mmio[offset & 0x0F] = data & 0xFF
        if reg == 0x00:
            self.ga_ctrl = data & 0xFF
            if data & 0x01:
                self.peripherals_enabled = True
        elif reg == 0x01:
            self.clear_irq(data & 0xFF)
        elif reg == 0x02:
            self.simm_bank = data & 0x0F
        elif reg == 0x04:
            self.ga_chip_select = data & 0xFF
        elif reg == 0x06:
            self.dsp_cmd_latch = data & 0xFF
        elif reg == 0x08:
            self.dsp_addr_latch = data & 0xFF
        elif reg == 0x0E:
            self.eeprom_latch = data & 0xFF
            new_cs = bool(data & 0x01)
            new_clk = bool(data & 0x02)
            new_di = bool(data & 0x04)

            if not new_cs:
                self.eeprom_cs = False
                self.eeprom_state = 0
                self.eeprom_bit_count = 0
                self.eeprom_do = 0
            else:
                self.eeprom_cs = True
                if not self.eeprom_clk and new_clk:  # Rising clock edge
                    if self.eeprom_state == 0:
                        if new_di:
                            self.eeprom_state = 1
                            self.eeprom_shift_reg = 0
                            self.eeprom_bit_count = 0
                    elif self.eeprom_state == 1:
                        self.eeprom_shift_reg = (self.eeprom_shift_reg << 1) | (1 if new_di else 0)
                        self.eeprom_bit_count += 1
                        if self.eeprom_bit_count == 8:
                            op = (self.eeprom_shift_reg >> 6) & 0x03
                            addr = self.eeprom_shift_reg & 0x3F
                            if op == 0x02:  # READ
                                self.eeprom_shift_reg = self.eeprom_data[addr & 0x3F]
                                self.eeprom_bit_count = 0
                                self.eeprom_state = 3
                                self.eeprom_do = 0
                            elif op == 0x01:  # WRITE
                                self.eeprom_bit_count = 0
                                self.eeprom_shift_reg = 0
                                self.eeprom_state = 2
                            elif op == 0x00:  # EWEN / EWDS
                                if (addr & 0x30) == 0x30:
                                    self.eeprom_ewen = True
                                elif (addr & 0x30) == 0x00:
                                    self.eeprom_ewen = False
                                self.eeprom_state = 0
                    elif self.eeprom_state == 2:
                        self.eeprom_shift_reg = (self.eeprom_shift_reg << 1) | (1 if new_di else 0)
                        self.eeprom_bit_count += 1
                        if self.eeprom_bit_count == 16:
                            addr = self.mmio[0x0E] & 0x3F
                            if self.eeprom_ewen:
                                self.eeprom_data[addr & 0x3F] = self.eeprom_shift_reg & 0xFFFF
                            self.eeprom_state = 0
                    elif self.eeprom_state == 3:
                        self.eeprom_do = 1 if (self.eeprom_shift_reg & 0x8000) else 0
                        self.eeprom_shift_reg = (self.eeprom_shift_reg << 1) & 0xFFFF
                        self.eeprom_bit_count += 1
                        if self.eeprom_bit_count == 16:
                            self.eeprom_state = 0

                self.eeprom_clk = new_clk
                self.eeprom_di = new_di


def test_gate_array_driver_implementation_present():
    """Verify s760.cpp contains the Gate Array, EEPROM, and Interrupt subsystem code."""
    assert os.path.exists(DRIVER_PATH), f"Driver file missing: {DRIVER_PATH}"
    with open(DRIVER_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "m_ga_ctrl" in content
    assert "m_ga_status" in content
    assert "m_simm_bank" in content
    assert "m_eeprom_data" in content
    assert "0x414A" in content  # Roland Magic ID in EEPROM
    assert "0x0224" in content  # OS version in EEPROM
    assert "m_timer_60hz" in content
    assert "trigger_irq" in content
    assert "clear_irq" in content
    assert "IRQ_TIMER_60HZ" in content


def test_gate_array_control_and_reset_latch():
    """Verify 0xF000 control latch handles reset un-assert and peripheral enable."""
    ga = RolandGateArraySimulator()
    assert not ga.peripherals_enabled

    # Write 0x01 to 0xF000 (OS startup at 0x00487D)
    ga.write(0x00, 0x01)
    assert ga.peripherals_enabled
    assert (ga.read(0x00) & 0x01) == 0x01


def test_gate_array_status_register_bus_ready():
    """Verify 0xF001 status register returns Bit 2 (Bus Ready) for OS loop pass."""
    ga = RolandGateArraySimulator()
    status = ga.read(0x01)
    assert (status & 0x04) != 0, "Gate Array Bit 2 (Peripheral Bus Ready) must be set"


def test_gate_array_simm_banking():
    """Verify 0xF002 SIMM banking register sets 0-15 banks (up to 32MB)."""
    ga = RolandGateArraySimulator()
    for bank in range(16):
        ga.write(0x02, bank)
        assert ga.read(0x02) == bank
        assert ga.simm_bank == bank


def test_gate_array_ak93c45_eeprom_read_protocol():
    """Verify serial bit-banging read of AK93C45 factory calibration words."""
    ga = RolandGateArraySimulator()

    def read_eeprom_word(addr):
        # 1. Assert CS
        ga.write(0x0E, 0x01)  # CS=1, CLK=0, DI=0

        # Helper to clock a single bit in
        def clock_in_bit(bit):
            di = 0x04 if bit else 0x00
            ga.write(0x0E, 0x01 | di)           # Set DI, CLK=0
            ga.write(0x0E, 0x01 | 0x02 | di)    # Rising edge CLK=1
            ga.write(0x0E, 0x01 | di)           # Fall CLK=0

        # Send Start bit (1)
        clock_in_bit(1)
        # Send Opcode (READ = 1 0)
        clock_in_bit(1)
        clock_in_bit(0)
        # Send 6-bit Address
        for b in range(5, -1, -1):
            clock_in_bit((addr >> b) & 1)

        # Read 16 bits out
        result = 0
        for _ in range(16):
            ga.write(0x0E, 0x01)          # CLK=0
            ga.write(0x0E, 0x01 | 0x02)   # CLK=1
            bit_out = ga.read(0x10) & 0x01
            result = (result << 1) | bit_out
            ga.write(0x0E, 0x01)          # CLK=0

        # De-assert CS
        ga.write(0x0E, 0x00)
        return result

    # Read Address 0 (Roland Magic ID = 0x414A)
    magic_id = read_eeprom_word(0)
    assert magic_id == 0x414A, f"Expected 0x414A, got 0x{magic_id:04X}"

    # Read Address 1 (Version 2.24 = 0x0224)
    ver = read_eeprom_word(1)
    assert ver == 0x0224, f"Expected 0x0224, got 0x{ver:04X}"

    # Read Address 2 (SCSI ID = 7)
    scsi_id = read_eeprom_word(2)
    assert scsi_id == 0x0007, f"Expected 0x0007, got 0x{scsi_id:04X}"

    # Read Address 3 (Master Tune = 0x01B8 / 440Hz)
    tune = read_eeprom_word(3)
    assert tune == 0x01B8, f"Expected 0x01B8, got 0x{tune:04X}"


def test_interrupt_subsystem_timer_60hz_irq_assertion():
    """Verify 60Hz timer tick sets Bit 0 in status register (0xF001) and asserts CPU INT line."""
    ga = RolandGateArraySimulator()
    assert not ga.int_line_asserted
    assert (ga.read(0x01) & 0x01) == 0

    # Trigger 60Hz periodic timer tick
    ga.trigger_irq(RolandGateArraySimulator.IRQ_TIMER_60HZ)

    assert ga.int_line_asserted, "CPU INT line should assert on 60Hz timer tick"
    assert (ga.read(0x01) & 0x01) == 0x01, "Bit 0 should be set in 0xF001 status register"
    assert (ga.read(0x01) & 0x04) == 0x04, "Bit 2 (Bus ready) must stay preserved"


def test_interrupt_subsystem_write_to_clear_ack():
    """Verify writing bitmask to 0xF001 clears pending IRQ and de-asserts CPU INT line."""
    ga = RolandGateArraySimulator()
    ga.trigger_irq(RolandGateArraySimulator.IRQ_TIMER_60HZ)
    assert ga.int_line_asserted

    # OS acknowledges Timer IRQ by writing 0x01 to 0xF001
    ga.write(0x01, 0x01)

    assert not ga.int_line_asserted, "CPU INT line should de-assert once IRQ is acknowledged"
    assert (ga.read(0x01) & 0x01) == 0x00, "Bit 0 should be cleared"
    assert (ga.read(0x01) & 0x04) == 0x04, "Bus Ready bit 2 must remain asserted"


def test_interrupt_subsystem_multiple_irqs_and_line_deassertion():
    """Verify multiple simultaneous IRQs (Timer + SCSI + VDP) keep INT asserted until all are acknowledged."""
    ga = RolandGateArraySimulator()

    # Trigger Timer (Bit 0) and SCSI (Bit 3)
    ga.trigger_irq(RolandGateArraySimulator.IRQ_TIMER_60HZ)
    ga.trigger_irq(RolandGateArraySimulator.IRQ_SCSI)

    assert ga.int_line_asserted
    assert ga.read(0x01) & 0x09 == 0x09  # Bits 0 and 3 set

    # Acknowledge only Timer IRQ
    ga.write(0x01, 0x01)
    assert ga.int_line_asserted, "CPU INT line must stay asserted while SCSI IRQ is still pending"
    assert (ga.read(0x01) & 0x01) == 0x00
    assert (ga.read(0x01) & 0x08) == 0x08

    # Acknowledge SCSI IRQ
    ga.write(0x01, 0x08)
    assert not ga.int_line_asserted, "CPU INT line must de-assert once all IRQs are acknowledged"
    assert (ga.read(0x01) & 0x08) == 0x00


def test_interrupt_subsystem_vblank_and_fdc_irq_routing():
    """Verify VBlank (Bit 4) and FDC (Bit 1) IRQs assert and clear properly."""
    ga = RolandGateArraySimulator()

    # Trigger VDP VBlank and FDC IRQ
    ga.trigger_irq(RolandGateArraySimulator.IRQ_VDP_VBLANK)
    ga.trigger_irq(RolandGateArraySimulator.IRQ_FDC)

    assert ga.int_line_asserted
    status = ga.read(0x01)
    assert (status & 0x10) == 0x10, "VDP VBlank Bit 4 pending"
    assert (status & 0x02) == 0x02, "FDC IRQ Bit 1 pending"

    # Clear both at once with 0x12
    ga.write(0x01, 0x12)
    assert not ga.int_line_asserted
    assert (ga.read(0x01) & 0x12) == 0x00


def test_interrupt_subsystem_irq_masking():
    """Verify IRQ masking prevents unmasked IRQs from asserting INT line."""
    ga = RolandGateArraySimulator()
    ga.irq_mask = 0x00  # Mask all IRQs

    ga.trigger_irq(RolandGateArraySimulator.IRQ_TIMER_60HZ)
    assert (ga.read(0x01) & 0x01) == 0x01  # Pending flag still sets
    assert not ga.int_line_asserted        # But CPU INT line is not asserted due to mask


def test_bug081_encoder_latch_f012_does_not_alias_f002():
    """Verify F012 rotary encoder latch does not read or corrupt F002 control state (BUG-081)."""
    ga = RolandGateArraySimulator()
    # Write 0xDC to F002 (Control / bank / reset latch)
    ga.write(0x02, 0xDC)
    assert ga.mmio[2] == 0xDC
    assert ga.read(0x02) == 0x0C  # simm_bank masked with 0x0F

    # Reading F012 must return 0 (no encoder movement), NOT 0xDC (m_mmio[2])
    assert ga.read(0x12) == 0x00, "Reading F012 must return 0, not alias m_mmio[2]"

    # Writing 0x00 to F012 (firmware clear latch) must NOT overwrite m_mmio[2]
    ga.write(0x12, 0x00)
    assert ga.mmio[2] == 0xDC, "Writing to F012 must not overwrite m_mmio[2] at F002"

    # Source check on driver s760.cpp to ensure no fallback to m_mmio[2]
    with open(DRIVER_PATH, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()
    assert "val = m_mmio[2];" not in src, "s760.cpp must not alias F012 to m_mmio[2]"


def test_bug004_ic4_midi_fifo_and_priority_arbitration():
    """Verify IC4 natural interrupt priority arbitration and 64-byte FIFO queuing (BUG-004)."""
    with open(DRIVER_PATH, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    # 1. Verify 64-byte FIFO data structure & member declarations
    assert "static constexpr size_t NATIVE_MIDI_FIFO_SIZE = 64;" in src
    assert "u8 m_native_midi_fifo[NATIVE_MIDI_FIFO_SIZE]" in src
    assert "u32 m_native_midi_fifo_head = 0;" in src
    assert "u32 m_native_midi_fifo_tail = 0;" in src
    assert "u32 m_native_midi_fifo_count = 0;" in src

    # 2. Verify state saving for checkpoint persistence
    assert "save_item(NAME(m_native_midi_fifo));" in src
    assert "save_item(NAME(m_native_midi_fifo_head));" in src
    assert "save_item(NAME(m_native_midi_fifo_tail));" in src
    assert "save_item(NAME(m_native_midi_fifo_count));" in src

    # 3. Verify rcv_complete pushes to FIFO without single-byte drop
    assert "if (m_native_midi_fifo_count >= NATIVE_MIDI_FIFO_SIZE)" in src
    assert "m_native_midi_fifo[m_native_midi_fifo_tail] = data;" in src
    assert "++m_native_midi_fifo_count;" in src

    # 4. Verify banked_r(0x116) pops FIFO and edge-reasserts EXTINT if bytes remain
    assert "m_native_midi_fifo_head = (m_native_midi_fifo_head + 1) % NATIVE_MIDI_FIFO_SIZE;" in src
    assert "--m_native_midi_fifo_count;" in src
    assert "m_maincpu->set_input_line(i8x9x_device::EXTINT_LINE, CLEAR_LINE);" in src

    # 5. Verify natural IC4 vector priority arbitration ordering:
    # Source 0 (FDC) > Source 2 (Wave) > Source 4 (SCSI) > Source 6 (MIDI)
    fdc_pos = src.find("if ((m_irq_pending & IRQ_FDC) && BIT(m_bank_regs[0x15], 0))")
    wave_pos = src.find("if (m_native_midi_experiment && m_native_loop_monitor && m_native_wave_end_pending")
    scsi_pos = src.find("if (m_native_scsi_dma_pending && BIT(m_bank_regs[0x15], 4))")
    midi_pos = src.find("if (m_native_midi_experiment && m_native_midi_pending && BIT(m_bank_regs[0x15], 6))")

    assert -1 < fdc_pos < wave_pos < scsi_pos < midi_pos, (
        "IC4 priority arbitration order must strictly be: FDC (0) > Wave (2) > SCSI (4) > MIDI (6)"
    )


class IC4InterruptArbiterSimulator:
    """Python simulator replicating IC4 external interrupt priority arbitration and MIDI FIFO."""
    FIFO_SIZE = 64

    def __init__(self):
        self.bank_15 = 0x00  # Interrupt mask register
        self.irq_fdc = False
        self.wave_end_pending = False
        self.scsi_dma_pending = False
        self.fifo = []
        self.extint_asserted = False

    def push_midi_byte(self, byte_val):
        if len(self.fifo) < self.FIFO_SIZE:
            self.fifo.append(byte_val)
        self.update_extint()

    def read_midi_port_116(self):
        if not self.fifo:
            return 0x00
        val = self.fifo.pop(0)
        # Edge reassertion simulation: pulse low then re-evaluate
        self.extint_asserted = False
        self.update_extint()
        return val

    def status_114(self):
        return 0x01 if len(self.fifo) > 0 else 0x00

    def update_extint(self):
        active = False
        if (self.bank_15 & 0x01) and self.irq_fdc:
            active = True
        if (self.bank_15 & 0x04) and self.wave_end_pending:
            active = True
        if (self.bank_15 & 0x10) and self.scsi_dma_pending:
            active = True
        if (self.bank_15 & 0x40) and len(self.fifo) > 0:
            active = True
        self.extint_asserted = active

    def arbitrate_vector_203a(self):
        # Priority: Source 0 (FDC) > Source 2 (Wave) > Source 4 (SCSI) > Source 6 (MIDI)
        if (self.bank_15 & 0x01) and self.irq_fdc:
            return 0x20
        if (self.bank_15 & 0x04) and self.wave_end_pending:
            return 0x28
        if (self.bank_15 & 0x10) and self.scsi_dma_pending:
            self.scsi_dma_pending = False
            self.update_extint()
            return 0x30
        if (self.bank_15 & 0x40) and len(self.fifo) > 0:
            return 0x38
        return None


def test_ic4_priority_and_fifo_queuing_behavior():
    arb = IC4InterruptArbiterSimulator()
    arb.bank_15 = 0x55  # Enable Source 0, 2, 4, 6

    # Push 3 MIDI bytes into FIFO
    for b in [0x90, 0x3C, 0x7F]:
        arb.push_midi_byte(b)

    assert arb.status_114() == 0x01
    assert arb.extint_asserted

    # When all 4 sources are simultaneously active
    arb.irq_fdc = True
    arb.wave_end_pending = True
    arb.scsi_dma_pending = True

    # 1st vector request -> FDC (Source 0)
    assert arb.arbitrate_vector_203a() == 0x20

    # Clear FDC
    arb.irq_fdc = False
    arb.update_extint()

    # 2nd vector request -> Wave (Source 2)
    assert arb.arbitrate_vector_203a() == 0x28

    # Clear Wave
    arb.wave_end_pending = False
    arb.update_extint()

    # 3rd vector request -> SCSI (Source 4)
    assert arb.arbitrate_vector_203a() == 0x30
    assert not arb.scsi_dma_pending

    # 4th vector request -> MIDI (Source 6)
    assert arb.arbitrate_vector_203a() == 0x38

    # Read bytes sequentially from FIFO
    assert arb.read_midi_port_116() == 0x90
    assert arb.extint_asserted  # Still asserted because 2 bytes remain!
    assert arb.status_114() == 0x01

    assert arb.read_midi_port_116() == 0x3C
    assert arb.extint_asserted
    assert arb.status_114() == 0x01

    assert arb.read_midi_port_116() == 0x7F
    assert not arb.extint_asserted  # De-asserts once FIFO is empty!
    assert arb.status_114() == 0x00
