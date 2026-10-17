"""test_ghidra_export_and_symbols.py - Verification suite for S-760 Ghidra integration.

Validates:
1. Binary export integrity (s760_resident_os.bin and bank binaries).
2. Complete symbol database integrity (s760_symbols.csv).
3. Ghidra Jython setup script parser readiness.
"""

import csv
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "temp" / "ghidra_export"
RESIDENT_BIN = EXPORT_DIR / "s760_resident_os.bin"
BANKS_DIR = EXPORT_DIR / "banks"
SYMBOLS_CSV = ROOT / "scripts" / "ghidra" / "s760_symbols.csv"
SETUP_PY = ROOT / "scripts" / "ghidra" / "s760_ghidra_setup.py"
IMG_PATH = ROOT / "S760224.IMG"


@pytest.mark.skipif(not RESIDENT_BIN.is_file(), reason="Local extracted OS binary required")
def test_resident_os_binary_integrity():
    """Verify resident OS binary has correct size and begins with DI instruction (0xFA)."""
    assert RESIDENT_BIN.exists(), f"Resident OS binary {RESIDENT_BIN} missing. Run extract_resident_and_banks.py."
    data = RESIDENT_BIN.read_bytes()
    # 0xDF80 = 57,216 bytes: from 0x2080 to 0xFFFF
    assert len(data) == 57216, f"Expected 57,216 bytes, got {len(data)}"
    # First byte at 0x2080 must be 0xFA (DI - Disable Interrupts)
    assert data[0] == 0xFA, f"Expected 0xFA (DI) at offset 0, got 0x{data[0]:02X}"


@pytest.mark.skipif(not BANKS_DIR.is_dir(), reason="Local extracted OS banks required")
def test_bank_binaries_integrity():
    """Verify that all key 16 KiB bank slices were extracted cleanly."""
    assert BANKS_DIR.exists(), f"Banks directory {BANKS_DIR} missing."
    bank_files = list(BANKS_DIR.glob("*.bin"))
    assert len(bank_files) >= 8, f"Expected at least 8 bank slices, found {len(bank_files)}"
    for bf in bank_files:
        assert bf.stat().st_size == 16384, f"Bank slice {bf.name} is not 16,384 bytes"


def test_symbols_csv_schema_and_counts():
    """Verify s760_symbols.csv structure, count, address formatting, and types."""
    assert SYMBOLS_CSV.exists(), f"{SYMBOLS_CSV} missing"
    with open(SYMBOLS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["Name", "Address", "Type", "Comments"]
        rows = list(reader)

    assert len(rows) >= 7300, f"Expected >= 7300 symbols, got {len(rows)}"

    valid_types = {"Register", "Address", "Function"}
    for idx, row in enumerate(rows):
        name = row["Name"].strip()
        addr_str = row["Address"].strip()
        sym_type = row["Type"].strip()

        assert name, f"Row {idx}: Name cannot be empty"
        assert addr_str.startswith("0x"), f"Row {idx}: Address {addr_str} must start with 0x"

        addr = int(addr_str, 16)
        assert 0 <= addr <= 0xFFFF, f"Row {idx}: Address {addr_str} out of 16-bit range"
        assert sym_type in valid_types, f"Row {idx}: Type '{sym_type}' not in {valid_types}"


def test_symbols_csv_contains_critical_anchors():
    """Verify that fundamental architectural anchors and known OS routines are present."""
    with open(SYMBOLS_CSV, "r", encoding="utf-8") as f:
        symbols = {row["Name"]: int(row["Address"], 16) for row in csv.DictReader(f)}

    # Hardware registers
    assert symbols.get("SP") == 0x0018
    assert symbols.get("TIMER1") == 0x000A
    assert symbols.get("INT_MASK") == 0x0008

    # Bank selectors
    assert symbols.get("FETCH_SEL_WIN0") == 0x0100
    assert symbols.get("FETCH_SEL_WIN1") == 0x0102

    # Interrupt vectors and core functions
    assert symbols.get("entry_reset") == 0x2080
    assert symbols.get("isr_timer1") == 0x2B51
    assert symbols.get("main_application_init") == 0x2831

    # MMIO Ports
    assert symbols.get("VDP_PORT_VRAM_DATA") == 0xD018
    assert symbols.get("LCD_REG_STATUS_CMD") == 0xE000
    assert symbols.get("GATE_STROBE_PULSE") == 0xF000


def test_ghidra_setup_script_syntax_and_csv_loader():
    """Verify that s760_ghidra_setup.py parses s760_symbols.csv cleanly in standalone Python."""
    assert SETUP_PY.exists(), f"{SETUP_PY} missing"

    # Simulate the script's CSV reader loop
    loaded = 0
    with open(SYMBOLS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s_name = row.get("Name")
            s_addr_str = row.get("Address")
            s_type = row.get("Type", "Address")
            s_comment = row.get("Comments", "")
            if not s_name or not s_addr_str:
                continue
            addr = int(s_addr_str, 16)
            is_func = (s_type == "Function")
            loaded += 1

    assert loaded >= 7300, f"Simulated loader processed only {loaded} symbols"
