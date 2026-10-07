"""
disk_formats.py — Native Roland S-760 and Akai S1000 Disk & ISO Image Parser & Converter
"""
import struct
import math


class RolandS760Disk:
    """
    Parser and generator for Roland S-760 / S-770 / S-750 1.44MB Floppy & SCSI Disk Images.
    Format specifications:
    - 1.44MB 2HD: 80 cylinders, 2 heads, 18 sectors/track, 512 bytes/sector (1,474,560 bytes)
    - Sector 0: Volume Header with 'S770 MR25A' / 'S-760 System Disk' banner
    - Sector 1-35: Allocation bitmap (0x0F = free, 0x00 = allocated)
    - Sector 36+: OS Payload / Sample Library records
    - 256-byte Patch Records & Sample Header blocks
    """
    SECTOR_SIZE = 512
    TOTAL_SECTORS = 2880
    DISK_SIZE = TOTAL_SECTORS * SECTOR_SIZE

    def __init__(self, volume_name="S-760 SOUND"):
        self.volume_name = volume_name[:16].ljust(16)
        self.patches = []
        self.samples = []

    def add_patch(self, patch_id, patch_name, partial_ids=None, level=127, pan=0):
        if partial_ids is None:
            partial_ids = [1, 2]
        self.patches.append({
            "id": patch_id,
            "name": patch_name[:16].ljust(16),
            "partials": partial_ids,
            "level": level,
            "pan": pan
        })

    def add_sample(self, sample_id, sample_name, sample_rate, pcm_data, loop_start=0, loop_end=None, root_key=60):
        if loop_end is None:
            loop_end = len(pcm_data) // 2
        self.samples.append({
            "id": sample_id,
            "name": sample_name[:16].ljust(16),
            "sample_rate": sample_rate,
            "data": pcm_data,
            "loop_start": loop_start,
            "loop_end": loop_end,
            "root_key": root_key
        })

    def build_image(self) -> bytes:
        img = bytearray(self.DISK_SIZE)

        # Sector 0: Volume Header
        header = bytearray(self.SECTOR_SIZE)
        banner = b"S770 MR25A\x00S-760 Disk Ver. 2.24\x00Copyright Roland\x00"
        header[0:len(banner)] = banner
        header[0x40:0x40 + len(self.volume_name.encode('ascii'))] = self.volume_name.encode('ascii')
        header[0x60:0x64] = struct.pack("<I", len(self.patches))
        header[0x64:0x68] = struct.pack("<I", len(self.samples))
        img[0:self.SECTOR_SIZE] = header

        # Sector 1-35: Allocation Map (0x0F = free)
        for i in range(self.SECTOR_SIZE, 36 * self.SECTOR_SIZE):
            img[i] = 0x0F

        # Offset 0x4800 (Sector 36): Patch Records (256 bytes each)
        offset = 36 * self.SECTOR_SIZE
        for p in self.patches:
            rec = bytearray(256)
            rec[0x00:0x02] = struct.pack("<H", p["id"])
            rec[0x02:0x12] = p["name"].encode('ascii')
            rec[0x12] = p["level"]
            rec[0x13] = p["pan"] & 0xFF
            rec[0x20:0x28] = struct.pack("<4H", *([p["partials"][i] if i < len(p["partials"]) else 0 for i in range(4)]))
            img[offset:offset + 256] = rec
            offset += 256

        # Sample Records & Waveform blocks
        offset = 0x10000
        for s in self.samples:
            s_hdr = bytearray(256)
            s_hdr[0x00:0x02] = struct.pack("<H", s["id"])
            s_hdr[0x02:0x12] = s["name"].encode('ascii')
            s_hdr[0x12:0x16] = struct.pack("<I", s["sample_rate"])
            s_hdr[0x16:0x1A] = struct.pack("<I", s["loop_start"])
            s_hdr[0x1A:0x1E] = struct.pack("<I", s["loop_end"])
            s_hdr[0x1E] = s["root_key"]
            s_len = len(s["data"])
            s_hdr[0x20:0x24] = struct.pack("<I", s_len)
            img[offset:offset + 256] = s_hdr
            offset += 256

            # Audio PCM Data
            img[offset:offset + s_len] = s["data"]
            offset += (s_len + 511) & ~511  # Align to sector

        return bytes(img)

    @classmethod
    def parse(cls, data: bytes) -> dict:
        if len(data) < 512:
            raise ValueError("Disk image too small")
        
        banner = data[0:32]
        is_roland = (b"S770" in banner) or (b"S-760" in banner) or (b"Roland" in banner)
        vol_name = data[0x40:0x50].decode('ascii', errors='replace').strip()
        num_patches = struct.unpack_from("<I", data, 0x60)[0]
        num_samples = struct.unpack_from("<I", data, 0x64)[0]

        parsed_patches = []
        offset = 36 * cls.SECTOR_SIZE
        for _ in range(min(num_patches, 64)):
            if offset + 256 <= len(data):
                pid = struct.unpack_from("<H", data, offset)[0]
                pname = data[offset + 2:offset + 18].decode('ascii', errors='replace').strip()
                parsed_patches.append({"id": pid, "name": pname})
                offset += 256

        return {
            "is_roland": is_roland,
            "volume_name": vol_name,
            "num_patches": num_patches,
            "num_samples": num_samples,
            "patches": parsed_patches
        }


class AkaiS1000Disk:
    """
    Parser and generator for Akai S1000 / S1100 Floppy, Hard Disk & CD-ROM ISO Images.
    Format specifications (Maxim Digital Audio spec):
    - 1024-byte sectors (Floppy) or 2048-byte blocks (CD-ROM ISO)
    - Partition Header -> Volume Table -> Program & Sample Directories
    - 150-byte Program Parameter Header
    - Sample Header (12-char name, sample rate, loop markers, 16-bit linear signed PCM)
    """
    SECTOR_SIZE = 1024
    CD_BLOCK_SIZE = 2048

    def __init__(self, volume_name="AKAI S1000 VOL"):
        self.volume_name = volume_name[:12].ljust(12)
        self.programs = []
        self.samples = []

    def add_program(self, prog_num, prog_name, midi_channel=1, keygroup_count=1):
        self.programs.append({
            "num": prog_num,
            "name": prog_name[:12].ljust(12),
            "midi_channel": midi_channel,
            "keygroups": keygroup_count
        })

    def add_sample(self, sample_name, sample_rate, pcm_data, loop_start=0, loop_end=None, root_key=60):
        if loop_end is None:
            loop_end = len(pcm_data) // 2
        self.samples.append({
            "name": sample_name[:12].ljust(12),
            "sample_rate": sample_rate,
            "data": pcm_data,
            "loop_start": loop_start,
            "loop_end": loop_end,
            "root_key": root_key
        })

    def build_iso(self, total_mb=4) -> bytes:
        total_bytes = total_mb * 1024 * 1024
        img = bytearray(total_bytes)

        # Block 0: Akai S1000 Disk & Partition Header
        hdr = bytearray(self.CD_BLOCK_SIZE)
        magic = b"AKAI S1000 CD-ROM VOL"
        hdr[0:len(magic)] = magic
        hdr[0x20:0x2C] = self.volume_name.encode('ascii')
        hdr[0x30:0x34] = struct.pack("<I", len(self.programs))
        hdr[0x34:0x38] = struct.pack("<I", len(self.samples))
        img[0:self.CD_BLOCK_SIZE] = hdr

        # Block 1..N: Program Directory (150-byte Program records)
        offset = self.CD_BLOCK_SIZE
        for p in self.programs:
            p_rec = bytearray(150)
            p_rec[0x00:0x02] = struct.pack("<H", p["num"])
            p_rec[0x02:0x0E] = p["name"].encode('ascii')
            p_rec[0x0E] = p["midi_channel"]
            p_rec[0x0F] = p["keygroups"]
            img[offset:offset + 150] = p_rec
            offset += 150

        # Sample Directory & Waveform Blocks
        offset = 4 * self.CD_BLOCK_SIZE
        for s in self.samples:
            s_hdr = bytearray(150)
            s_hdr[0x00:0x0C] = s["name"].encode('ascii')
            s_hdr[0x0C:0x10] = struct.pack("<I", s["sample_rate"])
            s_hdr[0x10:0x14] = struct.pack("<I", s["loop_start"])
            s_hdr[0x14:0x18] = struct.pack("<I", s["loop_end"])
            s_hdr[0x18] = s["root_key"]
            s_len = len(s["data"])
            s_hdr[0x1A:0x1E] = struct.pack("<I", s_len)
            img[offset:offset + 150] = s_hdr
            offset += 150

            # Write raw PCM sample data
            img[offset:offset + s_len] = s["data"]
            offset += (s_len + 2047) & ~2047  # Align to CD block

        return bytes(img)

    @classmethod
    def parse(cls, data: bytes) -> dict:
        if len(data) < 1024:
            raise ValueError("Akai image too small")

        is_akai = (b"AKAI" in data[0:64]) or (b"S1000" in data[0:64])
        vol_name = data[0x20:0x2C].decode('ascii', errors='replace').strip()
        num_programs = struct.unpack_from("<I", data, 0x30)[0] if len(data) >= 0x38 else 0
        num_samples = struct.unpack_from("<I", data, 0x34)[0] if len(data) >= 0x38 else 0

        programs = []
        offset = 2048
        for _ in range(min(num_programs, 32)):
            if offset + 150 <= len(data):
                pnum = struct.unpack_from("<H", data, offset)[0]
                pname = data[offset + 2:offset + 14].decode('ascii', errors='replace').strip()
                programs.append({"num": pnum, "name": pname})
                offset += 150

        samples = []
        offset = 4 * 2048
        for _ in range(min(num_samples, 32)):
            if offset + 150 <= len(data):
                sname = data[offset:offset + 12].decode('ascii', errors='replace').strip()
                srate = struct.unpack_from("<I", data, offset + 0x0C)[0]
                slen = struct.unpack_from("<I", data, offset + 0x1A)[0]
                samples.append({"name": sname, "sample_rate": srate, "length": slen})
                offset += 150 + ((slen + 2047) & ~2047)

        return {
            "is_akai": is_akai,
            "volume_name": vol_name,
            "num_programs": num_programs,
            "num_samples": num_samples,
            "programs": programs,
            "samples": samples
        }


class S760AkaiConverter:
    """
    Emulates the Roland S-760 'Convert LD[S]' and 'Convert LD[A]' engine:
    Converts Akai S1000/S1100 Programs & Samples into native Roland S-760 Patches, Partials, and Waves.
    """
    @staticmethod
    def convert(akai_disk: AkaiS1000Disk, target_volume_name="S760 CONVERT") -> RolandS760Disk:
        s760 = RolandS760Disk(volume_name=target_volume_name)

        # 1. Convert Samples
        for idx, s in enumerate(akai_disk.samples):
            s760.add_sample(
                sample_id=idx + 1,
                sample_name=s["name"],
                sample_rate=s["sample_rate"],
                pcm_data=s["data"],
                loop_start=s["loop_start"],
                loop_end=s["loop_end"],
                root_key=s["root_key"]
            )

        # 2. Convert Programs to Patches
        for idx, p in enumerate(akai_disk.programs):
            s760.add_patch(
                patch_id=p["num"],
                patch_name=p["name"],
                partial_ids=[1, 2],
                level=127,
                pan=0
            )

        return s760
