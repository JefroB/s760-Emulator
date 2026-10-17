"""Compile and apply MCS-96 SLEIGH fixes for BUG-084 and BUG-086.

Fixes:
- BUG-086: SKIP length corrected to 2 bytes; IDLPD length corrected to 1 byte.
- BUG-084: PUSHA pushes flags word before extension word; extension word uses INT_MASK1 (RAM 0x13)
  and WSR (RAM 0x14); clears PSW and INT_MASK1. POPA restores extension first, then flags.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import pypcode

SLEIGH_DIR = Path(__file__).resolve().parent
SPEC_FILE = SLEIGH_DIR / 'MCS96.slaspec'
SINC_FILE = SLEIGH_DIR / 'MCS96.sinc'

PYPCODE_DIR = Path(pypcode.__file__).resolve().parent
TARGET_LANG_DIR = PYPCODE_DIR / 'processors/MCS96/data/languages'
SLEIGH_BIN = PYPCODE_DIR / 'bin/sleigh.exe'


def compile_sla(target_sla: Path):
    if not SLEIGH_BIN.is_file():
        raise FileNotFoundError(f'sleigh.exe not found at {SLEIGH_BIN}')
    cmd = [str(SLEIGH_BIN), str(SPEC_FILE), str(target_sla)]
    print(f'Compiling {SPEC_FILE} -> {target_sla}...')
    subprocess.check_call(cmd)
    print('Compilation successful.')


def install_to_pypcode():
    if not TARGET_LANG_DIR.is_dir():
        raise FileNotFoundError(f'Target pypcode languages directory not found at {TARGET_LANG_DIR}')

    target_sinc = TARGET_LANG_DIR / 'MCS96.sinc'
    target_sla = TARGET_LANG_DIR / 'MCS96.sla'

    # Backup originals if not already backed up
    sinc_orig = TARGET_LANG_DIR / 'MCS96.sinc.orig'
    sla_orig = TARGET_LANG_DIR / 'MCS96.sla.orig'
    if not sinc_orig.is_file() and target_sinc.is_file():
        shutil.copyfile(target_sinc, sinc_orig)
    if not sla_orig.is_file() and target_sla.is_file():
        shutil.copyfile(target_sla, sla_orig)

    # Copy sinc and compile sla directly in target directory
    shutil.copyfile(SINC_FILE, target_sinc)
    compile_sla(target_sla)
    print(f'Installed patched MCS96.sinc and compiled MCS96.sla to {TARGET_LANG_DIR}.')


if __name__ == '__main__':
    install_to_pypcode()
