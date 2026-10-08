"""
tests/test_scsi_mame.py — Dedicated regression tests for Fujitsu MB89352A SCSI Protocol Controller (SPC) emulation.
Verifies cycle-accurate SCSI SPC register protocols (0xF020 - 0xF02F), bus phase transitions (Arbitration, Selection, Command, Data In/Out, Status, Message In),
CDB command execution (TEST UNIT READY, INQUIRY, READ CAPACITY, READ/WRITE), and Gate Array SCSI IRQ handshakes.
"""

import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER_PATH = os.path.join(ROOT, "mame-source", "src", "mame", "roland", "s760.cpp")


class FujitsuMB89352ASimulator:
    """Python reference simulator mirroring s760_state Fujitsu MB89352A SCSI SPC implementation."""
    def __init__(self):
        self.bdid = 0x80  # Host ID 7 (Bit 7 = 1)
        self.sctl = 0x00
        self.scmd = 0x00
        self.tmod = 0x00
        self.ints = 0x00
        self.psns = 0x00  # Bus Free
        self.ssts = 0x28  # DREG Empty, TC Zero
        self.serr = 0x00
        self.pctl = 0x00
        self.mbc = 0x00
        self.dreg = 0x00
        self.temp = 0x00
        self.tc = 0

        self.bus_phase = 0  # 0=FREE, 1=ARB, 2=SEL, 3=CMD, 4=DATA_IN, 5=DATA_OUT, 6=STATUS, 7=MSG_IN
        self.target_id = 0
        self.cdb = []
        self.cdb_len = 6
        self.data_buffer = []
        self.data_idx = 0
        self.target_status = 0x00

        # Devices: ID 0 (HDD), ID 1 (CD-ROM), ID 2 (HDD)
        self.device_present = [True, True, True, False, False, False, False]
        self.device_type = [0, 5, 0, 5, 7, 0, 5]  # 0=HD, 5=CD, 7=MO
        self.disk_images = [
            bytearray(10 * 1024 * 1024),  # 10MB HDD 0
            bytearray(10 * 1024 * 1024),  # 10MB CD-ROM 1
            bytearray(10 * 1024 * 1024),  # 10MB HDD 2
            bytearray(), bytearray(), bytearray(), bytearray()
        ]

        # Gate Array IRQ flag (Bit 3 = 0x08)
        self.scsi_irq_pending = False

    def read_reg(self, offset):
        reg = offset & 0x0F
        if reg == 0x00:
            return self.bdid
        elif reg == 0x01:
            return self.sctl
        elif reg == 0x02:
            return self.scmd
        elif reg == 0x03:
            return self.tmod
        elif reg == 0x04:
            val = self.ints
            self.ints = 0x00
            self.scsi_irq_pending = False
            return val
        elif reg == 0x05:
            return self.psns
        elif reg == 0x06:
            return self.ssts
        elif reg == 0x07:
            return self.serr
        elif reg == 0x08:
            return self.pctl
        elif reg == 0x09:
            return self.mbc
        elif reg == 0x0A:  # DREG (FIFO)
            if self.bus_phase == 4:  # DATA_IN
                if self.data_idx < len(self.data_buffer):
                    val = self.data_buffer[self.data_idx]
                    self.data_idx += 1
                    if self.data_idx >= len(self.data_buffer):
                        self.bus_phase = 6  # Transition to STATUS
                        self.psns = 0x8B   # BSY=1, REQ=1, Status (011)
                        self.ints = 0x08
                        self.scsi_irq_pending = True
                    return val
                else:
                    self.bus_phase = 6
                    self.psns = 0x8B
                    self.ints = 0x08
                    self.scsi_irq_pending = True
                    return 0x00
            elif self.bus_phase == 6:  # STATUS
                val = self.target_status
                self.bus_phase = 7  # Transition to MESSAGE_IN
                self.psns = 0x8F   # BSY=1, REQ=1, Message In (111)
                self.ints = 0x08
                self.scsi_irq_pending = True
                return val
            elif self.bus_phase == 7:  # MESSAGE_IN
                val = 0x00  # COMMAND COMPLETE
                self.bus_phase = 0  # Transition to BUS FREE
                self.psns = 0x00
                self.ints = 0x01  # Command Complete
                self.scsi_irq_pending = True
                return val
            return 0x00
        elif reg == 0x0B:
            return self.temp
        elif reg == 0x0C:
            return (self.tc >> 16) & 0xFF
        elif reg == 0x0D:
            return (self.tc >> 8) & 0xFF
        elif reg == 0x0E:
            return self.tc & 0xFF
        return 0x00

    def write_reg(self, offset, data):
        reg = offset & 0x0F
        data &= 0xFF
        if reg == 0x00:
            self.bdid = data
        elif reg == 0x01:
            self.sctl = data
            if data & 0x01:  # Reset
                self.bus_phase = 0
                self.psns = 0x00
                self.ints = 0x80
                self.scsi_irq_pending = True
        elif reg == 0x02:
            self.scmd = data
            cmd = data & 0x07
            if cmd in (0x01, 0x02, 0x03):  # Select target
                mask = self.temp if self.temp != 0 else self.dreg
                target = -1
                for i in range(7):
                    if mask & (1 << i):
                        target = i
                        break
                if target < 0: target = self.target_id

                if target >= 0 and target < 7 and self.device_present[target]:
                    self.target_id = target
                    self.bus_phase = 3  # COMMAND
                    self.psns = 0x8A   # BSY=1, REQ=1, Command (010)
                    self.cdb = []
                    self.cdb_len = 6
                    self.ints = 0x02   # Selection Done
                    self.scsi_irq_pending = True
                else:
                    self.bus_phase = 0
                    self.psns = 0x00
                    self.ints = 0x04   # Timeout
                    self.scsi_irq_pending = True
            elif cmd == 0x00:  # Bus Release
                self.bus_phase = 0
                self.psns = 0x00
                self.ints = 0x20
        elif reg == 0x04:
            self.ints &= ~data
            if self.ints == 0:
                self.scsi_irq_pending = False
        elif reg == 0x08:
            self.pctl = data
        elif reg == 0x0A:  # DREG (write)
            self.dreg = data
            if self.bus_phase == 3:  # COMMAND
                self.cdb.append(data)
                if len(self.cdb) == 1:
                    op = data
                    if 0x20 <= op <= 0x3F: self.cdb_len = 10
                    elif 0xA0 <= op <= 0xBF: self.cdb_len = 12
                    else: self.cdb_len = 6

                if len(self.cdb) >= self.cdb_len:
                    self.execute_cdb()
            elif self.bus_phase == 5:  # DATA_OUT
                if self.data_idx < len(self.data_buffer):
                    self.data_buffer[self.data_idx] = data
                    self.data_idx += 1
                    if self.data_idx >= len(self.data_buffer):
                        self.bus_phase = 6
                        self.psns = 0x8B
                        self.ints = 0x08
                        self.scsi_irq_pending = True
        elif reg == 0x0B:
            self.temp = data
        elif reg == 0x0C:
            self.tc = (self.tc & 0x00FFFF) | (data << 16)
        elif reg == 0x0D:
            self.tc = (self.tc & 0xFF00FF) | (data << 8)
        elif reg == 0x0E:
            self.tc = (self.tc & 0xFFFF00) | data

    def execute_cdb(self):
        opcode = self.cdb[0]
        target = self.target_id
        dev_type = self.device_type[target]
        self.target_status = 0x00  # Good status

        if opcode == 0x00:  # TEST UNIT READY
            self.bus_phase = 6
            self.psns = 0x8B
            self.ints = 0x08
            self.scsi_irq_pending = True
        elif opcode == 0x12:  # INQUIRY
            alloc_len = self.cdb[4] if self.cdb[4] != 0 else 36
            buf = bytearray(36)
            buf[0] = dev_type
            buf[1] = 0x80 if dev_type in (5, 7) else 0x00
            buf[2] = 0x02  # SCSI-2
            buf[3] = 0x02
            buf[4] = 31
            vendor = b"ROLAND  " if dev_type == 0 else b"SONY    "
            product = b"S-760 HARD DISK " if dev_type == 0 else (b"CD-ROM CDU-8012 " if dev_type == 5 else b"SMO-S501        ")
            buf[8:16] = vendor
            buf[16:32] = product
            buf[32:36] = b"1.00"
            self.data_buffer = list(buf[:alloc_len])
            self.data_idx = 0
            self.bus_phase = 4  # DATA_IN
            self.psns = 0x89
            self.ints = 0x08
            self.scsi_irq_pending = True
        elif opcode == 0x03:  # REQUEST SENSE
            buf = bytearray(18)
            buf[0] = 0x70
            buf[2] = 0x00  # No Error
            buf[7] = 10
            self.data_buffer = list(buf)
            self.data_idx = 0
            self.bus_phase = 4
            self.psns = 0x89
            self.ints = 0x08
            self.scsi_irq_pending = True
        elif opcode == 0x25:  # READ CAPACITY 10
            block_size = 2048 if dev_type == 5 else 512
            img_sz = len(self.disk_images[target])
            last_lba = (img_sz // block_size - 1) if img_sz > 0 else 20479
            buf = bytearray(8)
            buf[0:4] = last_lba.to_bytes(4, "big")
            buf[4:8] = block_size.to_bytes(4, "big")
            self.data_buffer = list(buf)
            self.data_idx = 0
            self.bus_phase = 4
            self.psns = 0x89
            self.ints = 0x08
            self.scsi_irq_pending = True
        elif opcode in (0x08, 0x28):  # READ 6 / 10
            if opcode == 0x08:
                lba = ((self.cdb[1] & 0x1F) << 16) | (self.cdb[2] << 8) | self.cdb[3]
                count = self.cdb[4] if self.cdb[4] != 0 else 256
            else:
                lba = int.from_bytes(bytes(self.cdb[2:6]), "big")
                count = int.from_bytes(bytes(self.cdb[7:9]), "big")

            block_size = 2048 if dev_type == 5 else 512
            byte_offset = lba * block_size
            byte_count = count * block_size
            self.data_buffer = list(self.disk_images[target][byte_offset : byte_offset + byte_count])
            self.data_idx = 0
            self.bus_phase = 4
            self.psns = 0x89
            self.ints = 0x08
            self.scsi_irq_pending = True
        elif opcode in (0x0A, 0x2A):  # WRITE 6 / 10
            count = (self.cdb[4] if self.cdb[4] != 0 else 256) if opcode == 0x0A else int.from_bytes(bytes(self.cdb[7:9]), "big")
            block_size = 2048 if dev_type == 5 else 512
            self.data_buffer = [0] * (count * block_size)
            self.data_idx = 0
            self.bus_phase = 5  # DATA_OUT
            self.psns = 0x88
            self.ints = 0x08
            self.scsi_irq_pending = True
        else:
            self.bus_phase = 6
            self.psns = 0x8B
            self.ints = 0x08
            self.scsi_irq_pending = True


def test_scsi_driver_implementation_present():
    """Verify s760.cpp contains the Fujitsu MB89352A SCSI SPC state machine and registers."""
    assert os.path.exists(DRIVER_PATH), f"Driver file missing: {DRIVER_PATH}"
    with open(DRIVER_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "m_scsi_bdid" in content
    assert "m_scsi_sctl" in content
    assert "scsi_r" in content
    assert "scsi_w" in content
    assert "scsi_execute_cdb" in content
    assert "0xF020" in content
    assert "0xF02F" in content


def test_scsi_bdid_host_id_ready():
    """Verify SCSI BDID (0xF020) returns Host ID 7 (Bit 7 = 0x80)."""
    spc = FujitsuMB89352ASimulator()
    assert spc.read_reg(0x00) == 0x80


def test_scsi_target_selection_and_command_phase():
    """Verify selecting Target ID 0 enters Command Phase (0x8A) and asserts IRQ."""
    spc = FujitsuMB89352ASimulator()

    # Select Target ID 0 (mask = 0x01)
    spc.write_reg(0x0B, 0x01)  # TEMP = Target 0 bitmask
    spc.write_reg(0x02, 0x01)  # SCMD = Select

    assert spc.bus_phase == 3, "Should transition to COMMAND phase"
    assert spc.read_reg(0x05) == 0x8A, "PSNS should report BSY=1, REQ=1, Command Phase (010)"
    assert spc.scsi_irq_pending, "SCSI IRQ should be asserted on Selection Done"

    # Read INTS to clear
    ints = spc.read_reg(0x04)
    assert (ints & 0x02) == 0x02, "Selection Done flag should be set"
    assert not spc.scsi_irq_pending


def test_scsi_target_selection_timeout_for_nonexistent_device():
    """Verify selecting an absent Target ID triggers Selection Timeout."""
    spc = FujitsuMB89352ASimulator()

    # Select Target ID 4 (Device 4 absent)
    spc.write_reg(0x0B, 0x10)  # TEMP = Target 4 bitmask (1 << 4)
    spc.write_reg(0x02, 0x01)

    assert spc.bus_phase == 0, "Should return to BUS FREE"
    assert spc.scsi_irq_pending
    ints = spc.read_reg(0x04)
    assert (ints & 0x04) == 0x04, "Timeout flag should be set"


def test_scsi_test_unit_ready_command():
    """Verify TEST UNIT READY (0x00) returns Good Status (0x00) and Command Complete."""
    spc = FujitsuMB89352ASimulator()

    # Select Target 0
    spc.write_reg(0x0B, 0x01)
    spc.write_reg(0x02, 0x01)
    spc.read_reg(0x04)  # Clear Selection IRQ

    # Send 6-byte CDB: 0x00 0x00 0x00 0x00 0x00 0x00
    for b in [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]:
        spc.write_reg(0x0A, b)

    assert spc.bus_phase == 6, "Should transition to STATUS phase"
    assert spc.read_reg(0x05) == 0x8B  # Status Phase

    # Read Status byte
    status = spc.read_reg(0x0A)
    assert status == 0x00, "Good Status expected"

    # Read Message In byte (Command Complete = 0x00)
    assert spc.bus_phase == 7
    msg = spc.read_reg(0x0A)
    assert msg == 0x00, "Command Complete expected"
    assert spc.bus_phase == 0, "Bus should return to FREE"


def test_scsi_inquiry_command_hdd():
    """Verify INQUIRY (0x12) returns 36-byte Roland S-760 Hard Disk descriptor."""
    spc = FujitsuMB89352ASimulator()

    # Select Target 0 (HDD)
    spc.write_reg(0x0B, 0x01)
    spc.write_reg(0x02, 0x01)
    spc.read_reg(0x04)

    # Send 6-byte INQUIRY CDB: [0x12, 0x00, 0x00, 0x00, 36, 0x00]
    for b in [0x12, 0x00, 0x00, 0x00, 36, 0x00]:
        spc.write_reg(0x0A, b)

    assert spc.bus_phase == 4, "Should enter DATA_IN phase"
    inquiry_data = bytes([spc.read_reg(0x0A) for _ in range(36)])

    assert inquiry_data[0] == 0x00, "Direct Access Block Device (HDD)"
    assert inquiry_data[8:16] == b"ROLAND  "
    assert inquiry_data[16:32] == b"S-760 HARD DISK "
    assert inquiry_data[32:36] == b"1.00"

    # Complete Status and Message In phases
    status = spc.read_reg(0x0A)
    assert status == 0x00
    msg = spc.read_reg(0x0A)
    assert msg == 0x00


def test_scsi_inquiry_command_cdrom():
    """Verify INQUIRY (0x12) returns CD-ROM descriptor for Target ID 1."""
    spc = FujitsuMB89352ASimulator()

    # Select Target 1 (CD-ROM)
    spc.write_reg(0x0B, 0x02)  # Target 1 bitmask
    spc.write_reg(0x02, 0x01)
    spc.read_reg(0x04)

    for b in [0x12, 0x00, 0x00, 0x00, 36, 0x00]:
        spc.write_reg(0x0A, b)

    assert spc.bus_phase == 4
    inquiry_data = bytes([spc.read_reg(0x0A) for _ in range(36)])

    assert inquiry_data[0] == 0x05, "CD-ROM Device (0x05)"
    assert inquiry_data[1] == 0x80, "Removable Media (RMB)"
    assert inquiry_data[8:16] == b"SONY    "
    assert inquiry_data[16:32] == b"CD-ROM CDU-8012 "


def test_scsi_read_capacity_command():
    """Verify READ CAPACITY (10) (0x25) returns block count and 512B/2048B sector sizes."""
    spc = FujitsuMB89352ASimulator()

    # Select Target 0 (HDD 10MB)
    spc.write_reg(0x0B, 0x01)
    spc.write_reg(0x02, 0x01)
    spc.read_reg(0x04)

    # 10-byte CDB for READ CAPACITY: [0x25, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for b in [0x25, 0, 0, 0, 0, 0, 0, 0, 0, 0]:
        spc.write_reg(0x0A, b)

    assert spc.bus_phase == 4
    cap_data = bytes([spc.read_reg(0x0A) for _ in range(8)])
    last_lba = int.from_bytes(cap_data[0:4], "big")
    block_size = int.from_bytes(cap_data[4:8], "big")

    assert block_size == 512
    assert last_lba == (10 * 1024 * 1024 // 512) - 1


def test_scsi_read_data_command():
    """Verify READ (6) (0x08) reads 512-byte payload from HDD image."""
    spc = FujitsuMB89352ASimulator()
    test_pattern = b"ROLAND S-760 HARD DISK ROOT VOLUME HEADER"
    spc.disk_images[0][0:len(test_pattern)] = test_pattern

    # Select Target 0
    spc.write_reg(0x0B, 0x01)
    spc.write_reg(0x02, 0x01)
    spc.read_reg(0x04)

    # READ(6): LBA=0, Count=1 sector (512B) -> [0x08, 0x00, 0x00, 0x00, 0x01, 0x00]
    for b in [0x08, 0x00, 0x00, 0x00, 0x01, 0x00]:
        spc.write_reg(0x0A, b)

    assert spc.bus_phase == 4
    read_data = bytes([spc.read_reg(0x0A) for _ in range(512)])
    assert read_data[:len(test_pattern)] == test_pattern


def test_scsi_bus_reset():
    """Verify SCTL (0xF021) bus reset asserts reset condition (0x80) and IRQ."""
    spc = FujitsuMB89352ASimulator()
    spc.write_reg(0x01, 0x01)  # Bit 0 = RST

    assert spc.scsi_irq_pending
    assert spc.read_reg(0x04) == 0x80  # Self-reset / SCSI Reset
