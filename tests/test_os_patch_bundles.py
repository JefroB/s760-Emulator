"""Public input guards and exact-candidate reconstruction after patch relocation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "patches/gb6-scsi/build.py"


def test_scsi_bundle_rejects_unknown_inputs_without_creating_outputs(tmp_path):
    spec = importlib.util.spec_from_file_location("scsi_bundle_entry", ENTRY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    boot, disk = tmp_path / "boot.bin", tmp_path / "disk.img"
    boot.write_bytes(bytes(32768))
    disk.write_bytes(bytes(1474560))
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="Unrecognized original firmware"):
        module.build(boot, disk, output)
    assert not output.exists()
    assert boot.read_bytes() == bytes(32768)
    assert disk.read_bytes() == bytes(1474560)


def test_scsi_bundle_reproduces_hardware_candidate_from_another_directory(tmp_path):
    boot = ROOT / "roms/BOOT/Roland_S-760_v1.11.BIN"
    disk = ROOT / "S760224.IMG"
    if not all(p.is_file() for p in (boot, disk)):
        pytest.skip("User-owned original firmware required")
    pytest.importorskip("pypcode")
    originals = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (boot, disk)]
    output = tmp_path / "candidate"
    command = [sys.executable, str(ENTRY), "--boot-input", str(boot),
               "--os-input", str(disk), "--out-dir", str(output)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["os_sha256"] == "606e277e5f11a4ca1b59dadaf4e9a8395e6c8eed1e3674b4efa78bf3bf1767e4"
    assert manifest["boot_sha256"] == "a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb"
    for role in ("os", "boot"):
        data = (output / manifest[f"{role}_file"]).read_bytes()
        assert len(data) == manifest[f"{role}_bytes"]
        assert hashlib.sha256(data).hexdigest() == manifest[f"{role}_sha256"]
    repeated = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert repeated.returncode != 0
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in (boot, disk)] == originals
