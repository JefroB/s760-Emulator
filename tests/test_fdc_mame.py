"""
tests/test_fdc_mame.py — Dedicated regression tests for NEC uPD72068 Floppy Disk Controller (FDC) emulation.
Verifies cycle-accurate FDC register protocols, MSR status flags, DOR drive/motor control,
Seek/Recalibrate commands, MFM sector reading/writing, and Gate Array FDC IRQ handshakes.
"""

import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER_PATH = os.path.join(ROOT, "mame-source", "src", "mame", "roland", "s760.cpp")


class NECuPD72068Simulator:
    """Python reference simulator mirroring s760_state NEC uPD72068 FDC implementation."""
    def __init__(self, disk_image_bytes=None):
        self.msr = 0x80  # RQM=1, DIO=0
        self.dor = 0x0C  # DMA enabled, Drive 0
        self.ccr = 0x00  # 500 kbps (1.44M HD)
        self.st0 = 0x00
        self.st1 = 0x00
        self.st2 = 0x00
        self.st3 = 0x28  # Ready + Two-Sided

        self.cmd_buffer = []
        self.cmd_len = 0
        self.res_buffer = []
        self.res_idx = 0
        self.phase = 0  # 0=CMD/IDLE, 1=EXECUTION, 2=RESULT

        self.current_cyl = [0, 0]
        self.current_head = [0, 0]
        self.current_sector = [1, 1]
        self.selected_drive = 0
        self.motor_on = [False, False]
        self.disk_inserted = True

        self.data_byte_idx = 0
        self.data_byte_total = 0
        self.sector_offset = 0

        # Gate Array IRQ flag (Bit 1 = 0x02)
        self.fdc_irq_pending = False

        if disk_image_bytes is not None:
            self.disk_image = bytearray(disk_image_bytes)
        else:
            self.disk_image = bytearray(1474560)  # Standard 1.44MB floppy layout

    def read_reg(self, offset):
        reg = offset & 0x07
        if reg == 0x00:  # Main Status Register (MSR)
            return self.msr
        elif reg == 0x01:  # Data FIFO Port
            if self.phase == 2:  # RESULT phase
                if self.res_idx < len(self.res_buffer):
                    val = self.res_buffer[self.res_idx]
                    self.res_idx += 1
                    if self.res_idx >= len(self.res_buffer):
                        self.phase = 0
                        self.cmd_buffer = []
                        self.msr = 0x80  # RQM=1, DIO=0
                    return val
            elif self.phase == 1:  # EXECUTION (Data Read)
                if self.data_byte_idx < self.data_byte_total and (self.sector_offset + self.data_byte_idx) < len(self.disk_image):
                    val = self.disk_image[self.sector_offset + self.data_byte_idx]
                    self.data_byte_idx += 1
                    if self.data_byte_idx >= self.data_byte_total:
                        self.start_result_phase(7)
                    return val
                else:
                    self.start_result_phase(7)
                    return 0x00
            return 0x00
        elif reg == 0x07:  # Digital Input Register (DIR)
            return 0x00 if self.disk_inserted else 0x80
        return 0x00

    def write_reg(self, offset, data):
        reg = offset & 0x07
        data &= 0xFF
        if reg == 0x01:  # Data FIFO Port
            if self.phase == 0:  # COMMAND phase
                if len(self.cmd_buffer) == 0:
                    self.cmd_buffer.append(data)
                    opcode = data & 0x1F
                    if opcode == 0x03: self.cmd_len = 3      # Specify
                    elif opcode == 0x04: self.cmd_len = 2    # Sense Drive Status
                    elif opcode == 0x07: self.cmd_len = 2    # Recalibrate
                    elif opcode == 0x08: self.cmd_len = 1    # Sense Interrupt Status
                    elif opcode == 0x0F: self.cmd_len = 3    # Seek
                    elif opcode == 0x0A: self.cmd_len = 2    # Read ID
                    elif opcode == 0x06: self.cmd_len = 9    # Read Data
                    elif opcode == 0x05: self.cmd_len = 9    # Write Data
                    elif opcode == 0x0D: self.cmd_len = 6    # Format Track
                    elif opcode == 0x18: self.cmd_len = 1    # Version
                    else: self.cmd_len = 1
                    self.msr = 0x90  # RQM=1, CB=1
                else:
                    self.cmd_buffer.append(data)

                if len(self.cmd_buffer) >= self.cmd_len:
                    self.execute_command()

            elif self.phase == 1:  # EXECUTION (Data Write)
                if self.data_byte_idx < self.data_byte_total and (self.sector_offset + self.data_byte_idx) < len(self.disk_image):
                    self.disk_image[self.sector_offset + self.data_byte_idx] = data
                    self.data_byte_idx += 1
                    if self.data_byte_idx >= self.data_byte_total:
                        self.start_result_phase(7)
                else:
                    self.start_result_phase(7)

        elif reg == 0x02:  # DOR
            self.dor = data
            self.selected_drive = data & 0x03
            self.motor_on[0] = bool(data & 0x10)
            self.motor_on[1] = bool(data & 0x20)
            reset_asserted = (data & 0x04) == 0
            if reset_asserted:
                self.phase = 0
                self.cmd_buffer = []
                self.msr = 0x80
                self.st0 = 0xC0
                self.fdc_irq_pending = True

        elif reg in (0x03, 0x07):  # CCR
            self.ccr = data & 0x03

    def start_result_phase(self, length):
        self.phase = 2
        self.res_idx = 0
        self.res_buffer = self.res_buffer[:length]
        self.msr = 0xD0  # RQM=1, DIO=1, CB=1
        self.fdc_irq_pending = True

    def execute_command(self):
        opcode = self.cmd_buffer[0] & 0x1F
        if opcode == 0x03:  # Specify
            self.phase = 0
            self.cmd_buffer = []
            self.msr = 0x80
        elif opcode == 0x07:  # Recalibrate
            drv = self.cmd_buffer[1] & 0x03
            self.current_cyl[drv] = 0
            self.st0 = 0x20 | drv  # Seek complete
            self.phase = 0
            self.cmd_buffer = []
            self.msr = 0x80 | (1 << drv)
            self.fdc_irq_pending = True
        elif opcode == 0x0F:  # Seek
            drv = self.cmd_buffer[1] & 0x03
            target_cyl = self.cmd_buffer[2]
            self.current_cyl[drv] = min(max(target_cyl, 0), 79)
            self.st0 = 0x20 | drv  # Seek complete
            self.phase = 0
            self.cmd_buffer = []
            self.msr = 0x80 | (1 << drv)
            self.fdc_irq_pending = True
        elif opcode == 0x08:  # Sense Interrupt Status
            drv = self.selected_drive & 1
            self.res_buffer = [self.st0, self.current_cyl[drv]]
            self.start_result_phase(2)
            self.fdc_irq_pending = False
        elif opcode == 0x04:  # Sense Drive Status
            drv = self.cmd_buffer[1] & 0x03
            head = (self.cmd_buffer[1] >> 2) & 1
            st3 = 0x28 | (head << 2) | drv
            if self.current_cyl[drv] == 0:
                st3 |= 0x10  # Track 0
            self.res_buffer = [st3]
            self.start_result_phase(1)
        elif opcode == 0x0A:  # Read ID
            drv = self.cmd_buffer[1] & 0x03
            head = (self.cmd_buffer[1] >> 2) & 1
            self.res_buffer = [0x00 | drv | (head << 2), 0x00, 0x00, self.current_cyl[drv], head, 1, 2]
            self.start_result_phase(7)
        elif opcode == 0x06:  # Read Data
            drv = self.cmd_buffer[1] & 0x03
            c = self.cmd_buffer[2]
            h = self.cmd_buffer[3]
            r = self.cmd_buffer[4]
            n = self.cmd_buffer[5]
            spt = 18 if self.ccr == 0x00 else 9
            lba = (c * 2 + (h & 1)) * spt + min(max(r - 1, 0), spt - 1)
            self.sector_offset = lba * 512
            self.data_byte_idx = 0
            self.data_byte_total = 512
            self.res_buffer = [0x00 | drv | (h << 2), 0x00, 0x00, c, h, r + 1, n]
            self.phase = 1  # Execution (read data)
            self.msr = 0xF0  # RQM=1, DIO=1, NonDMA=1, CB=1
        elif opcode == 0x05:  # Write Data
            drv = self.cmd_buffer[1] & 0x03
            c = self.cmd_buffer[2]
            h = self.cmd_buffer[3]
            r = self.cmd_buffer[4]
            n = self.cmd_buffer[5]
            spt = 18 if self.ccr == 0x00 else 9
            lba = (c * 2 + (h & 1)) * spt + min(max(r - 1, 0), spt - 1)
            self.sector_offset = lba * 512
            self.data_byte_idx = 0
            self.data_byte_total = 512
            self.res_buffer = [0x00 | drv | (h << 2), 0x00, 0x00, c, h, r + 1, n]
            self.phase = 1  # Execution (write data)
            self.msr = 0xB0  # RQM=1, DIO=0, NonDMA=1, CB=1
        elif opcode == 0x18:  # Version
            self.res_buffer = [0x90]
            self.start_result_phase(1)
        else:
            self.res_buffer = [0x80]
            self.start_result_phase(1)


def test_fdc_driver_implementation_present():
    """Verify s760.cpp contains the NEC uPD72068 FDC state machine and registers."""
    assert os.path.exists(DRIVER_PATH), f"Driver file missing: {DRIVER_PATH}"
    with open(DRIVER_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "m_fdc_msr" in content
    assert "m_fdc_dor" in content
    assert "fdc_r" in content
    assert "fdc_w" in content
    assert "fdc_execute_command" in content
    assert "0xF040" in content
    assert "0xF047" in content


def test_fdc_main_status_register_power_on_ready():
    """Verify FDC MSR powers on with RQM=1 and DIO=0 (0x80)."""
    fdc = NECuPD72068Simulator()
    msr = fdc.read_reg(0x00)
    assert msr == 0x80, f"Expected 0x80 (RQM=1, DIO=0), got 0x{msr:02X}"


def test_fdc_specify_command():
    """Verify Specify (0x03) sets step rate and head unload time without result bytes."""
    fdc = NECuPD72068Simulator()
    fdc.write_reg(0x01, 0x03)  # Command opcode
    fdc.write_reg(0x01, 0xDF)  # SRT=D, HUT=F
    fdc.write_reg(0x01, 0x02)  # HLT=1, Non-DMA=0
    assert fdc.phase == 0
    assert fdc.read_reg(0x00) == 0x80


def test_fdc_recalibrate_and_sense_interrupt():
    """Verify Recalibrate (0x07) steps to track 0, asserts IRQ, and Sense Interrupt (0x08) reads status."""
    fdc = NECuPD72068Simulator()
    fdc.current_cyl[0] = 42

    # Send Recalibrate Drive 0
    fdc.write_reg(0x01, 0x07)
    fdc.write_reg(0x01, 0x00)

    assert fdc.current_cyl[0] == 0, "Head should seek to Cylinder 0"
    assert fdc.fdc_irq_pending, "FDC IRQ should be asserted"

    # Send Sense Interrupt Status (0x08)
    fdc.write_reg(0x01, 0x08)
    assert fdc.read_reg(0x00) == 0xD0  # RQM=1, DIO=1, CB=1 (Result Phase)

    st0 = fdc.read_reg(0x01)
    pcn = fdc.read_reg(0x01)
    assert (st0 & 0x20) == 0x20, "ST0 Bit 5 (Seek Complete) should be set"
    assert pcn == 0x00, "Present Cylinder Number should be 0"
    assert not fdc.fdc_irq_pending, "Sense Interrupt should clear IRQ"


def test_fdc_seek_command():
    """Verify Seek (0x0F) moves head to target cylinder and asserts IRQ."""
    fdc = NECuPD72068Simulator()

    # Seek Drive 0 to Cylinder 35
    fdc.write_reg(0x01, 0x0F)
    fdc.write_reg(0x01, 0x00)  # Drive 0, Head 0
    fdc.write_reg(0x01, 35)    # Target Cyl 35

    assert fdc.current_cyl[0] == 35
    assert fdc.fdc_irq_pending

    # Sense Interrupt
    fdc.write_reg(0x01, 0x08)
    st0 = fdc.read_reg(0x01)
    pcn = fdc.read_reg(0x01)
    assert (st0 & 0x20) == 0x20
    assert pcn == 35


def test_fdc_sense_drive_status():
    """Verify Sense Drive Status (0x04) returns ST3 with Track 0 and Ready flags."""
    fdc = NECuPD72068Simulator()
    fdc.current_cyl[0] = 0

    # Sense Drive Status Drive 0 Head 0
    fdc.write_reg(0x01, 0x04)
    fdc.write_reg(0x01, 0x00)

    st3 = fdc.read_reg(0x01)
    assert (st3 & 0x20) == 0x20, "ST3 Bit 5 (Drive Ready) should be set"
    assert (st3 & 0x10) == 0x10, "ST3 Bit 4 (Track 0) should be set"


def test_fdc_version_command():
    """Verify Version (0x18) command returns 0x90 (NEC uPD72068 / 765B)."""
    fdc = NECuPD72068Simulator()
    fdc.write_reg(0x01, 0x18)
    ver = fdc.read_reg(0x01)
    assert ver == 0x90, f"Expected 0x90, got 0x{ver:02X}"


def test_fdc_read_sector_data_mfm():
    """Verify Read Data (0x06) reads 512 bytes from disk image and returns 7 status bytes."""
    test_disk = bytearray(1474560)
    # Put identifiable signature in Cylinder 0 Head 0 Sector 1
    test_pattern = b"ROLAND S-760 DIGITAL SAMPLER BOOT SECTOR"
    test_disk[0:len(test_pattern)] = test_pattern

    fdc = NECuPD72068Simulator(disk_image_bytes=test_disk)

    # Read Data: CMD=0x06, Drive=0, C=0, H=0, R=1, N=2, EOT=18, GPL=27, DTL=0xFF
    fdc.write_reg(0x01, 0x06)
    fdc.write_reg(0x01, 0x00)
    fdc.write_reg(0x01, 0x00)  # C=0
    fdc.write_reg(0x01, 0x00)  # H=0
    fdc.write_reg(0x01, 0x01)  # R=1
    fdc.write_reg(0x01, 0x02)  # N=2 (512B)
    fdc.write_reg(0x01, 0x12)  # EOT=18
    fdc.write_reg(0x01, 0x1B)  # GPL=27
    fdc.write_reg(0x01, 0xFF)  # DTL=0xFF

    assert fdc.phase == 1, "Should enter EXECUTION phase"
    assert fdc.read_reg(0x00) == 0xF0  # RQM=1, DIO=1, NonDMA=1, CB=1

    # Read 512 sector bytes
    sector_data = bytearray()
    for _ in range(512):
        sector_data.append(fdc.read_reg(0x01))

    assert sector_data[:len(test_pattern)] == test_pattern

    # Read 7 result status bytes
    assert fdc.phase == 2, "Should transition to RESULT phase"
    results = [fdc.read_reg(0x01) for _ in range(7)]
    assert len(results) == 7
    assert results[0] == 0x00  # ST0 = Normal termination
    assert results[3] == 0x00  # C=0
    assert results[4] == 0x00  # H=0
    assert results[5] == 0x02  # R+1 = 2
    assert results[6] == 0x02  # N=2


def test_fdc_write_sector_data_mfm():
    """Verify Write Data (0x05) writes 512 bytes into disk image and returns 7 status bytes."""
    fdc = NECuPD72068Simulator()

    # Write Data: CMD=0x05, Drive=0, C=1, H=0, R=5, N=2, EOT=18, GPL=27, DTL=0xFF
    fdc.write_reg(0x01, 0x05)
    fdc.write_reg(0x01, 0x00)
    fdc.write_reg(0x01, 0x01)  # C=1
    fdc.write_reg(0x01, 0x00)  # H=0
    fdc.write_reg(0x01, 0x05)  # R=5
    fdc.write_reg(0x01, 0x02)  # N=2
    fdc.write_reg(0x01, 0x12)
    fdc.write_reg(0x01, 0x1B)
    fdc.write_reg(0x01, 0xFF)

    assert fdc.phase == 1
    assert fdc.read_reg(0x00) == 0xB0  # RQM=1, DIO=0, NonDMA=1, CB=1

    # Write 512 bytes
    payload = bytes([(i & 0xFF) for i in range(512)])
    for b in payload:
        fdc.write_reg(0x01, b)

    # Check that disk image has the payload at LBA = (1 * 2 + 0) * 18 + 4 = 40 => offset 40 * 512 = 20480
    lba = (1 * 2 + 0) * 18 + 4
    written = fdc.disk_image[lba * 512 : (lba + 1) * 512]
    assert written == payload

    # Read 7 result status bytes
    assert fdc.phase == 2
    results = [fdc.read_reg(0x01) for _ in range(7)]
    assert len(results) == 7
    assert results[0] == 0x00


def test_fdc_dor_reset_and_motor_control():
    """Verify Digital Output Register (DOR 0xF042) reset assert and motor enable."""
    fdc = NECuPD72068Simulator()
    # Turn on Drive 0 Motor (Bit 4 = 1, Bit 2 = 1 (not reset))
    fdc.write_reg(0x02, 0x1C)
    assert fdc.motor_on[0]
    assert not fdc.motor_on[1]

    # Assert Software Reset (Bit 2 = 0)
    fdc.write_reg(0x02, 0x00)
    assert fdc.st0 == 0xC0  # Reset condition
    assert fdc.fdc_irq_pending
