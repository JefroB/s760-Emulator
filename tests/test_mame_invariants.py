"""
test_mame_invariants.py — Test suite for MAME Roland S-760 driver configuration
"""
import os
import hashlib
import zlib
from pathlib import Path
from types import SimpleNamespace
from conftest import ROOT, IMAGE

MAME_DRIVER_PATH = os.path.join(ROOT, "mame-source", "src", "mame", "roland", "s760.cpp")


def test_mame_driver_file_exists():
    assert os.path.exists(MAME_DRIVER_PATH), f"MAME driver missing: {MAME_DRIVER_PATH}"


def test_mame_driver_contains_mcs96_cpu():
    with open(MAME_DRIVER_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "I80C196KB(config, m_maincpu, 16_MHz_XTAL)" in content
    assert "N8097BH(config, m_maincpu, 16_MHz_XTAL)" in content
    assert "0x2080" in content  # Reset vector load address
    assert "0xF000" in content  # MMIO window


def test_mame_harness_supplies_generated_lua(tmp_path, monkeypatch):
    """The harness generates each script; there is no static s760_test.lua."""
    import mame_harness
    monkeypatch.setattr(mame_harness, "SCRATCH_DIR", str(tmp_path))
    # A provisioned executable is not needed to verify script delivery.
    monkeypatch.setattr(mame_harness, "MAME_EXE", __file__)
    body = "results.probe = 760\nsave_and_exit()"
    def launch(cmd, **kwargs):
        script = Path(cmd[cmd.index("-autoboot_script") + 1]).read_text()
        assert body in script
        assert 'local json = require("json")' in script
        assert "manager.machine:exit()" in script
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(mame_harness.subprocess, "run", launch)
    assert mame_harness.MameTestSession(body).run()["returncode"] == 0


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
