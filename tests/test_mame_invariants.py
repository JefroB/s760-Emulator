"""
test_mame_invariants.py — Test suite for MAME Roland S-760 driver configuration
"""
import os
import hashlib
import zlib
from conftest import ROOT, IMAGE

MAME_DRIVER_PATH = os.path.join(ROOT, "docs", "mame", "src", "mame", "roland", "s760.cpp")
LUA_SCRIPT_PATH = os.path.join(ROOT, "docs", "mame", "s760_test.lua")


def test_mame_driver_file_exists():
    assert os.path.exists(MAME_DRIVER_PATH), f"MAME driver missing: {MAME_DRIVER_PATH}"


def test_mame_driver_contains_mcs96_cpu():
    with open(MAME_DRIVER_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "I8096" in content or "i8096" in content
    assert "0x2080" in content  # Reset vector load address
    assert "0xF000" in content  # MMIO window


def test_mame_lua_script_exists():
    assert os.path.exists(LUA_SCRIPT_PATH), f"Lua test script missing: {LUA_SCRIPT_PATH}"


def test_mame_rom_hashes_match_image():
    assert os.path.exists(IMAGE), f"Image missing: {IMAGE}"
    with open(IMAGE, "rb") as f:
        data = f.read()
    
    crc32_val = f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"
    sha1_val = hashlib.sha1(data).hexdigest()

    with open(MAME_DRIVER_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert crc32_val.lower() in content.lower(), f"CRC32 mismatch: {crc32_val}"
    assert sha1_val.lower() in content.lower(), f"SHA1 mismatch: {sha1_val}"
