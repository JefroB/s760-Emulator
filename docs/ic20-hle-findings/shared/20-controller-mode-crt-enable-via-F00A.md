# Finding 20 — The CRT is gated by the controller/board config the OS reads at 0xF00A (hardware context from the user)

**Author:** Kiro
**Status:** SHARED / FINAL
**Date:** 2026-10-09

## Decisive hardware context (from the user, who owns the S-760)
On the real unit the user has **System → Controller set to CRT + mouse/remote**
(i.e. "Mouse+CRT" or "RC-100+CRT", OP-760 video board enabled). The emulated OS
boots the SAME disk but reads its controller/display mode from hardware config —
and if that config says front-panel-only ("Panel+LCD"), the OS **correctly does
NOT enable the VDP/CRT**. That is exactly our symptom: `display_enabled_ever=0`,
0xD010 never written non-zero, CRT black. So the black screen is a
**configuration/state** issue, not a boot or render bug.

## Evidence: the OS reads board config from gate-array MMIO 0xF00A
Early init (runtime ~0x2496, file ~0x4C16):
```
2496: STB ZRlo, 0xF00A      ; (strobe/latch 0xF00A)
249B: LDB RDA, 0xF00A       ; read gate-array status 0xF00A
24A0: STB RDA, 0x2085       ; store board/controller config to 0x2085
```
0xF00A is the CPU GATE ARRAY status port that, on real hardware, reflects the
installed OP-760 video board + the controller selection. The OS caches it at
0x2085 and later branches on it to decide Panel+LCD vs Mouse+CRT vs RC-100+CRT
and whether to drive the RFSC16A VDP.

## The emulator bug
`mmio_r` has **no case for offset 0x0A** — 0xF00A falls through to `default` and
returns `m_mmio[0x0A]` = 0. So the OS reads "0" = (most likely) no video board /
Panel+LCD → never enables the CRT. We must make 0xF00A report the user's actual
hardware: OP-760 video board present, controller = CRT + mouse/remote.

## Do NOT just force pixels
Per ChatGPT's review and the RE workflow: don't force display-enable or invent a
value to make pixels. Model the real board config. Needed, evidence-first:
1. **Which bit(s) of 0xF00A** the OS tests (via the cached 0x2085) to select the
   controller mode and gate CRT. (Static analysis — handed to Gemini, task 21.)
2. The 0xF00A value that corresponds to "Mouse+CRT" / "RC-100+CRT" with the
   OP-760 board present — i.e. what the user's real unit returns.
3. Then set `mmio_r` case 0x0A to return that value (optionally selectable to
   match System Parameter 2 Controller: Panel+LCD / Mouse+CRT / RC-100+CRT).

## Related gates seen in the same region
- `0x24A0 → 0x2085` is the cached config.
- Gemini finding 17 noted `0x92A6: CMPB ZRlo, 0x2488` gating the display update
  at 0x92D0, and the display-enable writes to 0xD010 at 0x92D0/0x9326/0x9F95/
  0xA012/0xA900. The chain from 0x2085 (board config) → the mode decision →
  0x2488 → the 0x92D0 display-enable path is what we need mapped.

## Probe result (Kiro, empirical)
Added an env-selectable `mmio_r(0xF00A)` return (`S760_F00A=<hex>`, default 0xFF)
and a dedicated case 0x0A (independent of m_mmio so the OS's 0x2496 strobe-write
doesn't clobber it). Ran with 0xF00A=0xFF + VDP trace:
- STILL `display_enabled_ever=0`, 0xD010 never non-zero, only 18 VDP writes,
  VRAM nonzero only at 0x8000-0x83ff (the OS IS writing font/tile data to the
  0x8000 tile base per finding 17, i.e. early display setup — but not enabling).
=> Raw 0xF00A=0xFF alone does NOT flip the OS into CRT mode. So the controller
mode is EITHER a specific bit pattern in 0xF00A, OR (more likely) it ALSO/INSTEAD
reads the **System Parameter 2 "Controller" setting persisted in EEPROM / saved
SysPRM** on the system disk, which our emulated EEPROM leaves at the default
(Panel+LCD). This is exactly what Gemini task 21 must decode: the full branch
chain and where the Controller setting is stored. Do NOT keep blind-probing
values (forcing anti-pattern) — need the static decode.

## Second probe: live VDP raster readback (card-present) — also no change
Hypothesis: the OS detects the OP-760 card by reading back the VDP raster
counters (0xD004 beam-X/HBlank, 0xD006 scanline-Y/VBlank per Gemini finding 17);
a static-0 readback = "no card" = Panel+LCD. Made `vdp_r` return the live
screen hpos/vpos for 0xD004-0xD007 (models an installed card generating raster
timing). Result: UNCHANGED — still exactly 18 VDP writes, `display_enabled_ever=0`,
VRAM only at 0x8000. So neither 0xF00A=0xFF nor a live raster flips it.

### What the 18 fixed writes tell us
The OS does the SAME 18 VDP writes every run regardless of what 0xF00A or the
raster counters return — i.e. an UNCONDITIONAL early VDP init (it writes font/
tile data to the 0x8000 tile base) — and then the display-enable decision is
gated by something UPSTREAM that we have not satisfied. Blind value-probing is
not converging; the exact gate needs the static branch trace (Gemini task 21).
Most likely candidates now, in priority order:
1. The System Parameter 2 **Controller** setting persisted in EEPROM / saved
   SysPRM (our EEPROM defaults leave it Panel+LCD). The user set CRT+mouse on
   real hardware, which wrote that param to their disk/EEPROM.
2. A board-detect that reads a VDP/gate-array location we still return 0 for
   (not 0xF00A, not 0xD004/06).
3. An input/handshake (RC-100/mouse present) the OS waits on.

## Register fixes already applied (Gemini finding 17), still valid
The 16-bit word-splitting fixes (vdp_w 0x18/0x19, 0x30/0x31, 0x34/0x35/0x36),
display-enable condition `(data & 0x19)`, and SED1335 `offset & 0x02` decode are
in. They are necessary but not sufficient while 0xF00A reports no CRT board — the
OS never reaches the 0xD010 writes. Fixing 0xF00A is the unlock.
