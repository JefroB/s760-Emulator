"""
Shared pytest fixtures and ground-truth constants for the S-760 RE test suite.

Design: these tests encode every structural claim we make about the image and
our tooling, so the docs/steering are backed by runnable checks and we catch
regressions when scripts change. Host-side only (no hardware needed).
"""
import os
import subprocess
import sys
from pathlib import Path
import pytest

# --- repo layout -------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CANDIDATE_IMAGES = [
    os.path.join(ROOT, "roms", "System", "s760.rom"),
    os.path.join(ROOT, "roms", "s760", "System", "s760.rom"),
    os.path.join(ROOT, "roms", "System", "S760224.IMG"),
    os.path.join(ROOT, "roms", "s760", "s760.rom"),
    os.path.join(ROOT, "S760224.IMG"),
]
IMAGE = next((p for p in _CANDIDATE_IMAGES if os.path.exists(p)), os.path.join(ROOT, "S760224.IMG"))
SCRIPTS = os.path.join(ROOT, ".kiro", "scripts")
TEMP_WORK = os.path.join(ROOT, "temp", "work")

# --- ground-truth constants (single source of truth; keep in sync w/ docs) ---
IMAGE_SIZE = 0x168000            # 1,474,560 bytes = 2880 x 512 HD floppy
PAYLOAD_FILE_OFF = 0x4800        # OS payload start (file offset)
LOAD_BASE = 0x2080               # runtime address that file 0x4800 maps to (MCS-96 reset)
RESET_FIRST_BYTE = 0xFA          # DI (disable interrupts) at payload start

# Known ASCII anchors: (file_offset, bytes)
BANNER_TAG = (0x0004, b"S770 MR25A")
BANNER_TITLE = (0x0021, b"S-760 System Disk    Ver. 2.24")

# "Ver. 2.24" occurrences we rely on (file offsets of the 9-byte string)
VER_STRING = b"Ver. 2.24"
VER_MAIN_SCREEN = 0x0BD3AA       # main version display (grouped w/ CRT strings)
VER_STATUS_LINE = 0x0C1D46       # "Roland S-760 Ver. 2.24 ... Volume"
VER_ISOLATED = 0x87FDB           # space-padded isolated copy

PYTHON = sys.executable


@pytest.fixture
def synthetic_completion_root(tmp_path):
    """Scope-rule tests use invented input bytes and committed evidence metadata."""
    from pathlib import Path
    import hashlib
    import json
    root = Path(ROOT)
    validation = tmp_path / 'docs/condensed/validation'
    validation.mkdir(parents=True)
    # Keep the evidence real while replacing only private firmware identities.
    for source in (root / 'docs/condensed/validation').glob('*.json'):
        (validation / source.name).write_bytes(source.read_bytes())
    for relative, label, size in [
        ('S760224.IMG', 'os', IMAGE_SIZE),
        ('roms/BOOT/Roland_S-760_v1.11.BIN', 'ic15', 32768),
    ]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(bytes(size))
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        inventory = validation / f'{label}-exploration-coverage-2026-10-16.json'
        data = json.loads(inventory.read_text())
        data['input_sha256'] = digest
        inventory.write_text(json.dumps(data))
        scope = validation / f'{label}-completion-scope-v1.json'
        data = json.loads(scope.read_text())
        data['input_sha256'] = digest
        if label == 'ic15':
            data['assumptions'][0]['bytes'] = 0
        scope.write_text(json.dumps(data))
    return tmp_path


@pytest.fixture(scope="session")
def image_bytes():
    return require_system_image().read_bytes()


def require_system_image():
    """Resolve private firmware only for tests that actually need original bytes."""
    source = Path(IMAGE)
    if not source.is_file():
        pytest.skip(f"Local Roland system image required: {source}")
    return source


@pytest.fixture(scope="session")
def original_sha():
    """Hash of the original image; a canary that we never mutate it in place."""
    import hashlib
    if not os.path.exists(IMAGE):
        pytest.skip(f"Local Roland system image required: {IMAGE}")
    with open(IMAGE, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run_s760(*args):
    """Invoke the s760.ps1 analyzer, return (rc, stdout+stderr)."""
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File",
           os.path.join(SCRIPTS, "s760.ps1")] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout + p.stderr


def run_py(script, *args):
    cmd = [PYTHON, os.path.join(SCRIPTS, script)] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout + p.stderr
