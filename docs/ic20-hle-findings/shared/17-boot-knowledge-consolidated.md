# Finding 17 — Consolidated S-760 MAME Boot Knowledge (steering mirror)

**Author:** Kiro
**Status:** SHARED / FINAL (living summary)
**Date:** 2026-10-09

This is the committed, repo-tracked mirror of the local steering/rules files
(`.kiro/steering/ic20-hle-boot.md` and `.agents/rules/ic20-hle-boot.md`, which are
git-ignored). It consolidates findings 00-16 into a single authoritative summary
of how the MAME `s760` driver boots the Ver. 2.24 OS from `S760224.IMG`.

## Headline status (2026-10-09)
The OS **boots to its main executive loop and genuinely drives the RFSC16A VDP**
(ground truth: `vdp_w` offset 0x18 → `m_vdp_vram_active=true`, observed
`[VDP] first VRAM write: addr=00099 ... PC=da3f`). Confirmed chain:
reset → record loop (sel 0x4B) → 0xB93A (PUSHA) → 0x2237 → EI (0x2185) →
0x2831 main entry → timer ISR (0x2B51) → main loop in resident 0xE000-0xFFFF →
VDP VRAM writes (0xD018). Remaining to a VISIBLE frame (G8): the render path and
a verification-harness detection fix.

## Root cause
The OS calls into low memory (0x0000-0x01FF) expecting the Roland **IC20 BOOT
ROM** services, which are NOT on the disk (IC20 is flat-pack, not dumpable).
Without them the CPU derails and resets forever (black CRT). Fix = HLE the IC20
services + add the missing MCS-96/80C196 opcodes. HLE is the path — do not
assume an IC20 dump is required to boot.

## CPU core: Intel S80C196KB (`mame-source/src/devices/cpu/mcs96/`)
S80C196KB = 8x9x peripherals + 196 extended opcodes (MAME split them; the i8x9x
core was extended to carry both).
- `mcs96make.py` includes the 196 opcodes for the `i8x9x` target; declarations in
  `mcs96.h`; regenerate `.hxx` with `.agents/scripts/regen_mcs96.ps1` (generated
  files under `build/generated/emu/cpu/mcs96/`, not committed).
- Implemented in `mcs96ops.lst`: BMOV(C1), CMPL(C5), BMOVI(CD), POP-196(CE/CF),
  DJNZW(E1), IDLPD(F6), XCH(04), XCHB(14).
- **PUSHA(F4)/POPA(F5) are STACK-NEUTRAL no-ops** — the OS has PUSHA-at-entry /
  RET-at-exit routines (e.g. 0xB93A) with no matching POPA; a real 2-word push
  derails RET to 0x0000. Deliberate bring-up simplification; don't change without
  re-proving 0xB93A.

## Memory map (`src/mame/roland/s760.cpp`)
`file = runtime + 0x2780` (file 0x4800 == rt 0x2080), uniform/linear across the
whole resident 0x2080-0xFFFF. **No code banking** for 0xE000-0xFFFF.
- `0x0000-0x1FFF` RAM (reg file/SFRs < 0x100 → AS_DATA; SP=0x1120).
- `0x2000-0x207F` IRQ vector RAM: vectors in initial contents — RET stub 0x2B22
  default; **0x200A→0x2B51** (timer ISR); 0x200E→0x2C4F.
- `0x2080-0xFFFF` resident image as RAM (`m_os_ram`). Write audit: OS writes only
  0x2080-0xCFFF state + the 0xD400 block; code is read-only (ROM+holes refinement
  deferred, finding 16).
- Peripheral windows re-installed on top in `machine_start` (order matters),
  narrowed to real ports: VDP `0xD000-0xD0FF` (0xD018=VRAM data → vram_active;
  addr ptr 0xD034/0xD036); SED1335 `0xE000-0xE003` (only 0xE000/0xE002 — never
  widen); gate array `0xF000-0xF01F`; SCSI `0xF020-0xF02F`; FDC `0xF040-0xF047`;
  `0xD400-0xD41C` peripheral block (TVF/MEQ or VDP companion?).

## IC20 HLE (`ic20_hle_install`)
- **AS_DATA vs AS_PROGRAM**: register file (< 0x100) is AS_DATA; buffers/ports
  (>= 0x100) are AS_PROGRAM. External AS_PROGRAM access < 0x100 hits work RAM.
- 14 IC20 entry points get RET read-handler stubs (0xF0F0), as read handlers (not
  RAM pokes — low RAM is cleared after machine_start).
- Selector dispatch on write-tap to slot 0x0104:
  - 0x4B record enum: RW4E→buffer, write 0x7F header.
  - 0x3B CHS read: RF0=sec/RF1=cyl/RF2=head, RW1E=dest;
    LBA=((cyl*2)+head)*18+((sector-1)%18); copy 512; clear carry.
  - 0x1F bulk read: RW4C=count, RW48/RW4A=LBA, RW1E=dest; copy count*512;
    clear carry.

## Build / verify (Windows cmd → PowerShell files; inline $var gets stripped)
- Regen: `temp\regen_mcs96.ps1`; build: `temp\build_s760.ps1`; link:
  `temp\link_s760.ps1` (kill stale `mames760` first). Verify: `python
  temp\verify.py` (wraps `tests/mame_harness.py`). Debugger: `-debug
  -debugscript`; use breakpoint halt-detection.

## Known gaps / next
1. Verification heuristic reads 0xD018 via the shared auto-incrementing VRAM ptr
   and misses writes (reports vdp inactive despite the flag). Fix the detection.
2. Visible frame (G8): confirm VDP display-enable (0xD010) + VRAM bases vs.
   `crt_update` (Gemini task 15).
3. ROM+holes upper-region refinement (finding 16) — deferred.

## Collaboration protocol
Findings in `docs/ic20-hle-findings/`: edit only your own `*-work/`; MOVE finished
docs to `shared/`. Read `shared/` before changing boot code.
