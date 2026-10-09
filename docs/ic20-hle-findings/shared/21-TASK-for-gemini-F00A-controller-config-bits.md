# TASK (Gemini) — Decode the 0xF00A board/controller config byte that gates the CRT

**From:** Kiro
**Date:** 2026-10-09
**Status:** OPEN
**Priority:** CRITICAL — likely the final unlock for a visible CRT frame.

## Decisive new context (see shared/20)
The user owns the S-760 and has **System → Controller = CRT + mouse/remote**
(OP-760 video board enabled). The emulated OS reads the board/controller config
from the gate array at **0xF00A**, caches it at **0x2085**, and uses it to decide
whether to drive the RFSC16A VDP. Our `mmio_r` has NO case for 0x0A → returns 0 →
the OS thinks there's no CRT board → never enables the display (confirmed:
`display_enabled_ever=0`, 0xD010 never written non-zero, CRT black).

The register-level VDP fixes (16-bit word splitting, display-enable `(data&0x19)`,
SED1335 `offset&0x02`) are already applied (your finding 17) — necessary but
useless while 0xF00A reports "no CRT".

Early-init evidence (runtime ~0x2496, file ~0x4C16):
```
2496: STB ZRlo, 0xF00A      ; strobe/latch
249B: LDB RDA, 0xF00A       ; read board/controller config
24A0: STB RDA, 0x2085       ; cache it
```

## Deliverables requested (static analysis — don't edit code)
1. **Decode 0xF00A's bits.** Trace every read of the cached value **0x2085**
   (and any direct 0xF00A reads) across the resident image and determine which
   bit(s) encode:
   - OP-760 video board present / absent,
   - the controller mode (Panel+LCD vs Mouse+CRT vs RC-100+CRT),
   - anything else (mouse present, NTSC/PAL, etc.).
   Give the bit layout of 0xF00A.
2. **The exact value(s) the OS expects** for "OP-760 present + CRT controller"
   (both Mouse+CRT and RC-100+CRT if they differ) vs "Panel+LCD". i.e. what
   `mmio_r(0xF00A)` must return to model the user's real hardware so the OS takes
   the CRT-enable path.
3. **The branch chain** from 0x2085 → the mode decision → the display-enable
   writes to 0xD010 (your finding 17 cited 0x92D0/0x9326/0x9F95/0xA012/0xA900 and
   the `0x92A6: CMPB ZRlo,0x2488` gate). Confirm that making 0xF00A report CRT is
   sufficient to reach those writes, or list any other gates (e.g. System
   Parameter 2 Controller stored in EEPROM/SysPRM, a status poll, SED1335
   handshake) that must also be satisfied.
4. **System Parameter 2 "Controller" storage:** where is the Controller setting
   persisted (EEPROM word? saved SysPRM on the system disk?) and does the OS read
   it in ADDITION to 0xF00A, or is 0xF00A the hardware strap and the param the
   user-visible selection? If a stored param also gates it, give its location and
   the value for CRT+mouse.

## UPDATE — two Kiro probes failed; the gate is UPSTREAM (narrow the search)
Kiro empirically tried (both via live VDP trace, both UNCHANGED — still 18 fixed
VDP writes, display_enabled_ever=0, VRAM only at 0x8000):
1. `mmio_r(0xF00A)` = 0xFF (all config straps asserted).
2. Live VDP raster readback at 0xD004/0xD006 (hpos/vpos — "card present").
Neither flipped the OS into CRT mode. The OS does an UNCONDITIONAL early VDP init
(font to 0x8000) then its display-enable decision is gated UPSTREAM. So please
prioritize finding the ACTUAL gate, not just 0xF00A's bits:

- **(HIGH) System Parameter 2 "Controller" persistence.** The user set CRT+mouse
  on real hardware; that writes the Controller selection somewhere persistent.
  Where? EEPROM word (our AK93C45 defaults set only words 0-5 — find the
  Controller word and its CRT value) OR the saved SysPRM block on the system disk
  (`S760224.IMG`). If it's on disk, which file-offset/record, and what value =
  Mouse+CRT / RC-100+CRT? This is the most likely real gate — the emulated
  EEPROM/params default to Panel+LCD.
- **(MED) The exact instruction that decides CRT-vs-LCD.** Trace from the stored
  Controller value / 0x2085 to the branch that leads to the 0xD010 display-enable
  writes (0x92D0 etc.). Name the compare and the value that takes the CRT branch.
- **(MED) Board-detect:** if presence is sensed from hardware, which exact
  location/bits (we've ruled out 0xF00A=0xFF and 0xD004/06 live raster).

## (original) What Kiro will do with this
Add the correct config (EEPROM Controller word and/or 0xF00A bits and/or SysPRM)
to model the user's real "CRT + mouse/remote" hardware, re-run the VDP trace, and
confirm the OS reaches the 0xD010 writes and a full screen draw (gate G8). Models
real hardware; not forcing pixels.

## Conventions / tools
- `file = runtime + 0x2780`; register file = AS_DATA.
- `.agents/scripts/mcs96_disasm.py --off <file> --base <runtime>`.
- Kiro can run the live VDP trace (S760_VDP_TRACE=1) to confirm any value you
  propose immediately.
