"""
Shared pytest fixtures and ground-truth constants for the S-760 RE test suite.

Design: these tests encode every structural claim we make about the image and
our tooling, so the docs/steering are backed by runnable checks and we catch
regressions when scripts change. Host-side only (no hardware needed).
"""
import os
import subprocess
import sys
import pytest

# --- repo layout -------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE = os.path.join(ROOT, "S760224.IMG")
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


@pytest.fixture(scope="session")
def image_bytes():
    assert os.path.exists(IMAGE), f"original image missing: {IMAGE}"
    with open(IMAGE, "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def original_sha():
    """Hash of the original image; a canary that we never mutate it in place."""
    import hashlib
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
