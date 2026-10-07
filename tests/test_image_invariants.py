"""
Ground-truth facts about S760224.IMG. Each test encodes a claim from the docs
so the claim stays true (regression guard) and is independently verifiable.
"""
from conftest import (
    IMAGE_SIZE, PAYLOAD_FILE_OFF, RESET_FIRST_BYTE,
    BANNER_TAG, BANNER_TITLE,
    VER_STRING, VER_MAIN_SCREEN, VER_STATUS_LINE, VER_ISOLATED,
)


def test_image_size_is_exact_floppy(image_bytes):
    assert len(image_bytes) == IMAGE_SIZE  # 2880 x 512


def test_no_dos_boot_signature(image_bytes):
    # custom Roland format: sector 0 has NO 0x55AA boot signature
    assert image_bytes[0x1FE:0x200] != b"\x55\xAA"


def test_banner_tag_present(image_bytes):
    off, want = BANNER_TAG
    assert image_bytes[off:off + len(want)] == want


def test_banner_title_present(image_bytes):
    off, want = BANNER_TITLE
    assert image_bytes[off:off + len(want)] == want


def test_payload_starts_at_4800(image_bytes):
    # 0x0F fill runs 0x200..0x47FF, payload begins at 0x4800 with DI (0xFA)
    assert image_bytes[PAYLOAD_FILE_OFF] == RESET_FIRST_BYTE


def test_0f_fill_region_before_payload(image_bytes):
    # spot-check the 0x0F fill just before the payload
    chunk = image_bytes[0x4000:PAYLOAD_FILE_OFF]
    assert set(chunk) == {0x0F}


def test_known_version_string_offsets(image_bytes):
    for off in (VER_MAIN_SCREEN, VER_STATUS_LINE, VER_ISOLATED):
        assert image_bytes[off:off + len(VER_STRING)] == VER_STRING, hex(off)


def test_ver_string_occurrence_count(image_bytes):
    # documented: 12 copies of "Ver. 2.24" in the image
    count = image_bytes.count(VER_STRING)
    assert count == 12, f"expected 12, found {count}"


def test_dos_template_is_data_not_code(image_bytes):
    # the only x86 on disk is the MS-DOS FAT12 boot template (~0x887A0):
    # it carries INT 13h (CD 13) and DOS error strings -> it's DATA
    region = image_bytes[0x88000:0x89000]
    assert b"\xCD\x13" in region or b"Non-System" in region
