# 03 — CPU / Instruction Set — SOLVED

## Answer: Intel MCS-96 (80C196KB), 16-bit, little-endian
Confirmed two ways:
1. **Service manual** names the CPU: **`S80C196KB`** (with a `16M`/16 MHz part
   marking). This is Intel's MCS-96 family — the 8xC196 16-bit microcontroller.
2. **Byte-level evidence** in the OS payload matches MCS-96 encoding exactly.

## Why the byte evidence fits MCS-96
The MCS-96 is a **register–memory architecture**: most instructions operate on
an on-chip "register file" (RAM at low addresses), so a typical instruction is
`opcode + register-byte(s)`, giving mostly **3-byte** and some **5-byte**
instructions. That explains everything we saw earlier:

- Earlier we found `0xDA` (and friends) recurring at **3- and 5-byte** spacing
  with no 2/4-byte alignment. That is the MCS-96 instruction cadence, not 68k
  (word-aligned) or x86.
- The Wikipedia MCS-96 example `memcpy` shows the shape precisely:
  `A2 1D 1A` (LD, 3 bytes), `C2 1A 21` (ST, 3 bytes), `E1 1E F7` (DJNZW),
  `F0` (RET, 1 byte).

## Opcode-density scan of the payload (0x4800–0x40000, 243,712 bytes)
Run: `s760.ps1 opcodes -Arch mcs96`
| Opcode | Meaning | Count | Note |
|--------|---------|-------|------|
| `F0` | RET | 3462 (1.42%) | subroutine-dense, expected range |
| `EF` | SCALL (rel11 call) | 3902 | lots of calls |
| `E7` | LJMP (rel16) | 284 | |
| `27` | SJMP (rel8) | 487 | |
| `A0–A3` | LD variants | 14022 | load-heavy |
| `C0–C3` | ST variants | 6742 | ~half the loads (reads > writes = real code) |
| `D0–DF` | conditional jumps | 16346 | abundant branching |
| `FE` | signed mul/div prefix | 497 | |

This is a coherent instruction profile, not random data.

## Key architecture facts (for disassembly)
- **16-bit, little-endian.** Multi-byte operands are low-byte-first.
- **Register–memory:** operands are usually addresses into the on-chip register
  file (first 256 bytes / the "lower register file"). SFRs (special function
  registers) live in low memory too.
- **Variable-length instructions** (1–5+ bytes). Three-operand forms exist.
- **Flat addressing** of 64 KB (banking/windowing extends this on some parts;
  the manual's `16M`/address details should be checked for the exact map).
- `F0` = RET, `EF` = SCALL, `E7` = LJMP, `27` = SJMP, `D0–DF` = conditional
  short jumps, `A0–A3`/`C0–C3` = LD/ST families.

## What this unlocks — DONE (Session 5)
- **Disassembler:** SOLVED. `pip install pypcode` provides Ghidra's SLEIGH
  engine with the bundled `MCS96:LE:16:default` language (the NSA/Ghidra MCS-96
  processor module) — an authoritative decoder. Reusable wrapper:
  `.kiro/scripts/mcs96_disasm.py`. This replaced the abandoned hand-coded
  opcode table (no more guessing).
- **Load/base address:** SOLVED = **0x2080, at file offset 0x4800.**
  Disassembling file 0x4800 at base 0x2080 yields a textbook MCS-96 reset
  routine starting with `DI` (0x2080 is the MCS-96 reset execution address).
  Verified: 283/307 (92.2%) of call/jump targets land on clean instruction
  boundaries at this base. See findings F21-F22.
- **Register/SFR map:** SLEIGH names the SFRs automatically and they match the
  code's usage: SP=0x18, IOS0=0x15, IOS1=0x16, INT_MASK=0x08, INT_PEND=0x09,
  INT_MASK1=0x13, INT_PEND1=0x12, PORT1=0x0F, PORT2=0x10, TIMER1, AD_result.
- **I/O window:** hardware is memory-mapped at **0xF000-0xF00A** (gate array /
  peripheral latches). Data/state window ~0x8000-0x9CFF. See F24 for the full
  derived memory map.
- **Open:** the payload is >64KB (530KB on disk) so the OS uses banked/extended
  addressing; the first ~52KB maps linearly at base 0x2080. Finding the bank
  switch (likely in the 0xF000 I/O window) is the next code-mapping task (F25).

## How to disassemble (quick reference)
```
pip install pypcode   # once
python .kiro\scripts\mcs96_disasm.py S760224.IMG --off 0x4800 --len 0x200 --base 0x2080
```
`--off/--len` are file offsets; `--base` is the runtime address of the first
byte (use 0x2080 for the main segment; add file_off-0x4800 to 0x2080 for any
other in-segment address).

## Ruled out (recorded for completeness)
- Motorola 68000 — 0 aligned signatures, both byte orders. NO.
- x86 for the OS — the only x86 was the MS-DOS boot template (data). NO.
- Compression — entropy ~6.3–6.8, so the code is plain. NO.
