#!/usr/bin/env python3
"""Build modified Roland S-760 IC15 Boot ROM v1.11 and OS 2.24 System Disk
with a 4th selectable controller option: mode 3 = 'GB-6 +CRT' (Sony GB-6 trackball).

Controller modes supported by the resulting combo:
  0: Panel+LCD  (front panel + 160x64 LCD)
  1: Mouse+CRT  (Roland MU-1 / MSX 4-nibble mouse + CRT, 100% preserved)
  2: RC100+CRT  (Roland RC-100 + CRT, 100% preserved)
  3: GB-6 +CRT  (Sony GB-6 trackball + CRT, selectable in both IC15 Setup & OS System menu)

Never modifies original source binaries in place.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BOOT_SOURCE = ROOT / "roms" / "BOOT" / "Roland_S-760_v1.11.BIN"
DEFAULT_OS_SOURCE = ROOT / "S760224.IMG"
DEFAULT_OUT_DIR = ROOT / "temp" / "work" / "gb6_combo"

BOOT_SOURCE_SHA256 = "ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6"
BOOT_SIZE = 0x8000  # 32,768 bytes

OS_SOURCE_SHA256 = "3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd"
OS_SIZE = 0x168000  # 1,474,560 bytes


def build_os_gb6_poll_stub(profile: str = "v9") -> bytes:
    """Assemble the Mode 1 / Mode 3 dispatcher and Sony GB-6 decoder for 0x004B:0x7A20 (file 0x01AE20)."""
    if profile not in ("v8", "v9"):
        raise ValueError("profile must be 'v8' or 'v9'")
    shift_x = 3 if profile == "v8" else 2
    shift_y = 2
    base_cpu = 0x7A20
    code = bytearray()

    def emit(hex_bytes: str) -> None:
        code.extend(bytes.fromhex(hex_bytes))

    def lcall(target_cpu: int) -> None:
        next_pc = base_cpu + len(code) + 3
        disp = (target_cpu - next_pc) & 0xFFFF
        code.append(0xEF)
        code.extend(struct.pack("<H", disp))

    def ljmp(target_cpu: int) -> None:
        next_pc = base_cpu + len(code) + 3
        disp = (target_cpu - next_pc) & 0xFFFF
        code.append(0xE7)
        code.extend(struct.pack("<H", disp))

    # 7A20: Mode 1 (Mouse+CRT) -> jump back to 0x57B4 (PUSHA) in original MU-1 mouse routine
    emit("99 01 DA")        # CMPB RDA, #0x01
    emit("D7 03")           # JNE  0x7A28
    ljmp(0x57B4)            # LJMP 0x57B4

    # 7A28: Mode 3 (GB-6+CRT) -> fall through to 0x7A2E; else RET
    emit("99 03 DA")        # CMPB RDA, #0x03
    emit("DF 01")           # JE   0x7A2E
    emit("F0")              # RET

    # 7A2E: Sony GB-6 trackball polling + v8/v9 movement decoder
    emit("F4")              # PUSHA
    emit("B1 BF DA C7 01 08 F0 DA")  # select('BF'): Pin 8 low = X axis
    lcall(0x5876)           # LCALL 0x5876 (button sample & debounce helper)
    lcall(0x586F)           # LCALL 0x586F (short settling delay)
    emit(f"B3 01 08 F0 28 71 0F 28 79 08 28 B0 28 AD 19 {shift_x:02X} AD")
    emit("B1 40 DA C7 01 08 F0 DA")  # select('40'): Pin 8 high = Y axis (resets X counter)
    lcall(0x586F)           # LCALL 0x586F (short settling delay)
    emit(f"B3 01 08 F0 2A 71 0F 2A 79 08 2A B0 2A D3 19 {shift_y:02X} D3")
    emit("B1 BF DA C7 01 08 F0 DA")  # select('BF'): Pin 8 low (resets Y counter)

    # Negative-endpoint clamp (-64 -> -63) matching verified v8/v9 hardware experiment
    for reg in ("AD", "D3"):
        emit(f"99 C0 {reg} D7 03 B1 C1 {reg}")

    emit("F5")              # POPA

    # Update RDD button flags from 0x2132/0x2134/0x2135 (same as 0x5812..0x582C) and RET
    # without running the disconnected-mouse heuristic at 0x582D
    emit("B3 01 32 21 DD")  # LDB  RDD, 0x2132[0]
    emit("B3 01 34 21 DA")  # LDB  RDA, 0x2134[0]
    emit("18 04 DA")        # SHRB RDA, #0x04
    emit("90 DA DD")        # ORB  RDD, RDA
    emit("B3 01 35 21 DA")  # LDB  RDA, 0x2135[0]
    emit("18 02 DA")        # SHRB RDA, #0x02
    emit("90 DA DD")        # ORB  RDD, RDA
    emit("F0")              # RET

    return bytes(code)


def build_os_lcd_status_selector() -> bytes:
    """Assemble the 38-byte LCD status controller string selector at 0x003B:0x6DBD (file 0x0161BD..0x0161E2)."""
    code = bytearray()
    code.extend(bytes.fromhex("B3 01 76 24 DA"))     # 6DBD: LDB   RDA, 0x2476[0]
    code.extend(bytes.fromhex("99 03 DA"))           # 6DC2: CMPB  RDA, #0x03
    code.extend(bytes.fromhex("D7 06"))              # 6DC5: JNE   0x6DCD
    code.extend(bytes.fromhex("A1 54 7A 2A"))        # 6DC7: LD    RW2A, #0x7A54 ("GB-6  +CRT")
    code.extend(bytes.fromhex("20 16"))              # 6DCB: SJMP  0x6DE3
    code.extend(bytes.fromhex("7D 0A DA"))           # 6DCD: MULUB RWDA, #0x0A
    code.extend(bytes.fromhex("45 72 5F DA 2A"))     # 6DD0: ADD   RW2A, RWDA, #0x5F72
    if len(code) > 38:
        raise ValueError("LCD status selector exceeds 38-byte span")
    code.extend([0xFD] * (38 - len(code)))           # 6DD5..6DE2: NOP padding
    return bytes(code)


def patch_boot_rom_bytes(source_bytes: bytes) -> bytearray:
    """Apply the 4th controller option ('GB-6 +CRT', mode 3) patches to IC15 Boot ROM v1.11 bytes."""
    if len(source_bytes) != BOOT_SIZE or hashlib.sha256(source_bytes).hexdigest() != BOOT_SOURCE_SHA256:
        raise ValueError("Input Boot ROM must be the unmodified Roland_S-760_v1.11.BIN baseline")

    rom = bytearray(source_bytes)

    # 1. Replace 4th placeholder entry ("?????????\x00") in controller label table at 0x63CC..0x63D5
    assert rom[0x63CC:0x63D6] == b"?????????\x00"
    rom[0x63CC:0x63D6] = b"GB-6 +CRT\x00"

    # 2. Boot status banner controller range check at 0x489A: CMPB RDA, #0x02 -> #0x03
    assert rom[0x489A:0x489D] == bytes.fromhex("99 02 DA")
    rom[0x489B] = 0x03

    # 3. Startup EEPROM controller validation at 0x5199: CMPB RDA, #0x02 -> #0x03
    assert rom[0x5199:0x519C] == bytes.fromhex("99 02 DA")
    rom[0x519A] = 0x03

    # 4. 4-field Power-On Setup Menu controller increment limit at 0x58C3: CMPB R29, #0x02 -> #0x03
    assert rom[0x58C3:0x58C6] == bytes.fromhex("99 02 29")
    rom[0x58C4] = 0x03

    # 5. 5-field Power-On Setup Menu controller increment limit at 0x5C94: CMPB R29, #0x02 -> #0x03
    assert rom[0x5C94:0x5C97] == bytes.fromhex("99 02 29")
    rom[0x5C95] = 0x03

    assert len(rom) == BOOT_SIZE
    return rom


def patch_os_disk_bytes(source_bytes: bytes, profile: str = "v9") -> bytearray:
    """Apply the 4th controller option ('GB-6 +CRT', mode 3) patches to S760224.IMG bytes."""
    if len(source_bytes) != OS_SIZE or hashlib.sha256(source_bytes).hexdigest() != OS_SOURCE_SHA256:
        raise ValueError("Input OS image must be the unmodified S760224.IMG v2.24 baseline")

    img = bytearray(source_bytes)

    # 1. Main executive loop controller input dispatcher (file 0x0066DD..0x0066E1, CPU 0xDEDD..0xDEE1):
    #    Route mode 3 (RDA != 0, 1, 2) back to 0xDECA (which calls 0x004B:0x57A9)
    assert img[0x0066DD:0x0066E2] == bytes.fromhex("99 02 DA D7 0E")
    img[0x0066E1] = 0xE8  # JNE 0xDECA

    # 2. Modal/wait loop controller input dispatcher (file 0x013421..0x013425, page 0x0032:0x4021..0x4025):
    #    Route mode 3 (RDA != 0, 1, 2) back to 0x4018 (SCALL 0x4030; JC 0x401F; LCALL 0x40B9)
    assert img[0x013421:0x013426] == bytes.fromhex("99 02 DA D7 09")
    img[0x013425] = 0xF2  # JNE 0x4018

    # 3. LCD status screen in CRT mode (file 0x0161BD..0x0161E2, page 0x003B:0x6DBD..0x6DE2)
    #    and 10-byte string "GB-6  +CRT" in bank 0x02DB free space at file 0x0BEE54 (CPU 0x7A54)
    assert img[0x0BEE54:0x0BEE5E] == b"\x00" * 10
    img[0x0BEE54:0x0BEE5E] = b"GB-6  +CRT"
    lcd_sel = build_os_lcd_status_selector()
    assert len(lcd_sel) == 0x0161E3 - 0x0161BD
    img[0x0161BD:0x0161E3] = lcd_sel

    # 4. Controller hardware init (file 0x018777..0x01877B, page 0x004B:0x5377..0x537B):
    #    Route mode 3 (RDA != 0, 1, 2) back to 0x5333 (writes 0x00 to 0xF006, sets 0x2136=100, primes 0x57A9)
    assert img[0x018777:0x01877C] == bytes.fromhex("99 02 DA D7 59")
    img[0x01877B] = 0xB7  # JNE 0x5333

    # 5. Mouse & GB-6 polling entry hook (file 0x018BAE..0x018BB3, page 0x004B:0x57AE..0x57B3)
    #    and Mode 1 / Mode 3 dispatcher + GB-6 decoder at file 0x01AE20 (page 0x004B:0x7A20)
    assert img[0x018BAE:0x018BB4] == bytes.fromhex("99 01 DA DF 01 F0")
    img[0x018BAE:0x018BB4] = bytes.fromhex("E7 6F 22 FD FD F0")  # LJMP 0x7A20; NOP; NOP; RET
    gb6_stub = build_os_gb6_poll_stub(profile)
    assert img[0x01AE20:0x01AE20 + len(gb6_stub)] == b"\x00" * len(gb6_stub)
    img[0x01AE20:0x01AE20 + len(gb6_stub)] = gb6_stub

    # 6. Panel+LCD switch screen controller banner range check (file 0x01EA99, page 0x0068:0x4299)
    #    and 4th 10-byte label slot at file 0x0BEE2F..0x0BEE38 (bank 0x02E9:0x422F)
    assert img[0x01EA99:0x01EA9C] == bytes.fromhex("99 02 DA")
    img[0x01EA9A] = 0x03
    assert img[0x0BEE2F:0x0BEE39] == b"?????????\x00"
    img[0x0BEE2F:0x0BEE39] = b"GB-6 +CRT\x00"

    # 7. System -> Controller menu parameter descriptor & labels (file 0x0BCEF8, 0x0BCF18..0x0BCF35)
    #    and full 4-option hint string at file 0x0BEE60 (bank 0x02DB:0x7A60)
    assert img[0x0BCEF6:0x0BCEFA] == bytes.fromhex("00 00 02 00")
    img[0x0BCEF8] = 0x03  # max = 3
    assert img[0x0BCF18:0x0BCF22] == b"*********\x00"
    img[0x0BCF18:0x0BCF22] = b"GB-6 +CRT\x00"
    assert img[0x0BCF22:0x0BCF36] == b"Panel,Mouse,RC100\x00\x00\x00"
    img[0x0BCF22:0x0BCF36] = b"Panel,Mouse,RC,GB6\x00\x00"
    assert img[0x0BEE60:0x0BEE78] == b"\x00" * 24
    img[0x0BEE60:0x0BEE78] = b"Panel,Mouse,RC100,GB-6\x00\x00"
    assert img[0x076E90:0x076E94] == bytes.fromhex("A1 22 5B E2")
    img[0x076E91:0x076E93] = bytes.fromhex("60 7A")
    assert img[0x077097:0x07709B] == bytes.fromhex("A1 22 5B E2")
    img[0x077098:0x07709A] = bytes.fromhex("60 7A")

    assert len(img) == OS_SIZE
    return img


def verify_disassembly(boot_bytes: bytes, os_bytes: bytes) -> dict[str, int]:
    """Verify with pypcode that all patched code regions decode cleanly without overlap."""
    from pypcode import Context

    ctx = Context("MCS96:LE:16:default")
    counts: dict[str, int] = {}

    def check_span(buf: bytes, file_off: int, length: int, cpu_addr: int, name: str) -> None:
        chunk = bytes(buf[file_off:file_off + length])
        res = ctx.disassemble(chunk, cpu_addr, 0, length, 0)
        total = sum(ins.length for ins in res.instructions)
        if total != length:
            raise ValueError(f"Disassembly length mismatch in {name}: decoded {total} != expected {length}")
        counts[name] = len(res.instructions)

    check_span(boot_bytes, 0x489A, 3, 0x489A, "boot_banner_check")
    check_span(boot_bytes, 0x5199, 3, 0x5199, "boot_eeprom_check")
    check_span(boot_bytes, 0x58C3, 3, 0x58C3, "boot_setup4_inc")
    check_span(boot_bytes, 0x5C94, 3, 0x5C94, "boot_setup5_inc")

    check_span(os_bytes, 0x0066B9, 0x37, 0xDEB9, "os_main_loop_poll_dispatch")
    check_span(os_bytes, 0x013400, 0x30, 0x4000, "os_modal_poll_dispatch")
    check_span(os_bytes, 0x0161BD, 38, 0x6DBD, "os_lcd_status_selector")
    check_span(os_bytes, 0x018722, 0xB4, 0x5322, "os_controller_hw_init")
    check_span(os_bytes, 0x018BA9, 12, 0x57A9, "os_mouse_poll_entry")
    stub_len = len(build_os_gb6_poll_stub("v9"))
    check_span(os_bytes, 0x01AE20, stub_len, 0x7A20, "os_gb6_poll_stub")

    return counts


def build_combo(
    boot_source: Path = DEFAULT_BOOT_SOURCE,
    os_source: Path = DEFAULT_OS_SOURCE,
    out_dir: Path = DEFAULT_OUT_DIR,
    profile: str = "v9",
    overwrite: bool = True,
    boot_output: Path | None = None,
    os_output: Path | None = None,
) -> dict[str, Any]:
    """Build both modified Boot ROM and OS disk images and verify them."""
    boot_source = Path(boot_source).resolve()
    os_source = Path(os_source).resolve()
    out_dir = Path(out_dir).resolve()

    boot_out = Path(boot_output).resolve() if boot_output else (out_dir / "Roland_S-760_v1.11.GB6.BIN")
    os_out = Path(os_output).resolve() if os_output else (out_dir / f"S760224.GB6-SELECTABLE-{profile}.IMG")
    boot_out.parent.mkdir(parents=True, exist_ok=True)
    os_out.parent.mkdir(parents=True, exist_ok=True)

    if boot_out == boot_source or os_out == os_source:
        raise ValueError("Output paths must never equal original source files")

    boot_orig = boot_source.read_bytes()
    os_orig = os_source.read_bytes()

    boot_patched = patch_boot_rom_bytes(boot_orig)
    os_patched = patch_os_disk_bytes(os_orig, profile=profile)
    disasm_counts = verify_disassembly(boot_patched, os_patched)

    mode = "wb" if overwrite else "xb"
    with boot_out.open(mode) as f:
        f.write(boot_patched)
    with os_out.open(mode) as f:
        f.write(os_patched)

    boot_diff_bytes = sum(1 for a, b in zip(boot_orig, boot_patched) if a != b)
    os_diff_bytes = sum(1 for a, b in zip(os_orig, os_patched) if a != b)

    return {
        "profile": profile,
        "boot_source": str(boot_source),
        "boot_source_sha256": BOOT_SOURCE_SHA256,
        "boot_output": str(boot_out),
        "boot_output_sha256": hashlib.sha256(boot_patched).hexdigest(),
        "boot_size": len(boot_patched),
        "boot_diff_bytes": boot_diff_bytes,
        "os_source": str(os_source),
        "os_source_sha256": OS_SOURCE_SHA256,
        "os_output": str(os_out),
        "os_output_sha256": hashlib.sha256(os_patched).hexdigest(),
        "os_size": len(os_patched),
        "os_diff_bytes": os_diff_bytes,
        "disasm_instruction_counts": disasm_counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boot-input", type=Path, default=DEFAULT_BOOT_SOURCE, help="Path to unmodified Roland_S-760_v1.11.BIN")
    parser.add_argument("--os-input", type=Path, default=DEFAULT_OS_SOURCE, help="Path to unmodified S760224.IMG")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory for patched binaries")
    parser.add_argument("--boot-output", type=Path, default=None, help="Optional explicit output path for patched Boot ROM")
    parser.add_argument("--os-output", type=Path, default=None, help="Optional explicit output path for patched OS Disk")
    parser.add_argument("--profile", choices=("v8", "v9"), default="v9", help="GB-6 scaling profile: v9 (X*4, Y*4) or v8 (X*8, Y*4)")
    args = parser.parse_args()

    manifest = build_combo(
        boot_source=args.boot_input,
        os_source=args.os_input,
        out_dir=args.out_dir,
        profile=args.profile,
        overwrite=True,
        boot_output=args.boot_output,
        os_output=args.os_output,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
