"""Unit and integration regressions for broader malformed media and recovery stress."""
import struct
from scripts.verify_final_recovery_stress import (
    make_dos_fat12,
    generate_broader_malformed_media,
)


def test_dos_fat12_geometry():
    """Verify standard MS-DOS FAT12 geometry generation."""
    dos = make_dos_fat12(737280)
    assert len(dos) == 737280
    assert dos[0:3] == b'\xeb\x3c\x90'
    assert dos[3:11] == b'MSDOS5.0'
    assert dos[510:512] == b'\x55\xaa'  # Boot signature
    # Media descriptor in BPB and FAT table
    assert dos[21] == 0xF9
    assert dos[512:515] == b'\xf9\xff\xff'
    assert dos[512 * 4:512 * 4 + 3] == b'\xf9\xff\xff'


def test_broader_malformed_profiles_generated(tmp_path):
    """Verify that all 7 broader malformed media profiles are correctly produced."""
    # These are byte-mutation/geometry checks, not firmware acceptance. Use
    # invented nonzero bytes so preservation and zero-fill are checked in CI.
    source = bytearray(b'\x5a' * 737280)
    source[:32] = b'SYNTHETIC TEST MEDIA'.ljust(32, b' ')
    source_bytes = bytes(source)

    profiles = generate_broader_malformed_media(tmp_path, source_bytes)
    assert len(profiles) == 7

    # Check corrupt banner 720K
    p1 = profiles['corrupt_banner_720k'].read_bytes()
    assert len(p1) == 737280
    assert b'NON_ROLAND_FORMAT_MAGIC' in p1[:64]
    assert b'S770 MR25A' not in p1[:64]

    # Check DOS FAT12 720K
    p2 = profiles['msdos_fat12_720k'].read_bytes()
    assert len(p2) == 737280
    assert p2[3:11] == b'MSDOS5.0'
    assert p2[510:512] == b'\x55\xaa'

    # Check corrupt catalog 720K
    p3 = profiles['corrupt_catalog_720k'].read_bytes()
    assert len(p3) == 737280
    assert p3[0x200:0x204] == b'\xff\xf0\xff\xf0'

    # Check corrupt sample header 720K
    p4 = profiles['corrupt_sample_hdr_720k'].read_bytes()
    assert len(p4) == 737280
    length, = struct.unpack_from('<I', p4, 0x18e00 + 24)
    assert length == 0x7FFFFFFF

    # Check pseudo-formatted 720K
    p5 = profiles['pseudo_formatted_720k'].read_bytes()
    assert len(p5) == 737280
    assert p5[0:32] == source_bytes[0:32]
    assert p5[512:] == b'\x00' * (737280 - 512)

    # Check corrupt banner 1.44M
    p6 = profiles['corrupt_banner_144m'].read_bytes()
    assert len(p6) == 1474560
    assert b'CORRUPT_144MB_BANNER' in p6[:64]

    # Check corrupt catalog 1.44M
    p7 = profiles['corrupt_catalog_144m'].read_bytes()
    assert len(p7) == 1474560
    assert p7[0x200:0x204] == b'\xff\xfe\xff\xfe'
