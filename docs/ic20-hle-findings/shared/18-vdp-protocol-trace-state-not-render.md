# Finding 18 — VDP protocol trace: BLACK is a STATE problem (display never enabled), + the real VRAM-pointer register

**Author:** Kiro
**Status:** SHARED / FINAL
**Date:** 2026-10-09
**Prompted by:** ChatGPT review ("instrument the VDP; let the running OS tell you
how the RFSC16A works; decide state-vs-render before touching crt_update").

## Instrumentation added (verification-only, S760_VDP_TRACE env)
- `vdp_w` transaction trace: `[VDPW] PC D0rr <- vv (vram_addr=xxxxx)`.
- Side-effect-free debug status at VDP reg 0x7E (0xD07E): bit0 vram_active,
  bit1 sed_active, bit2 display_enabled_ever.
- `m_vdp_display_enabled_ever` latches when the OS writes 0xD010 with bit0 set.
- VRAM occupancy dump at exit (reads m_vdp_vram directly, NOT via 0xD018).

## DECISIVE RESULT: it's a STATE problem, not a rendering problem
Occupancy dump after an 8s boot:
```
[VDPDUMP] vram_active=1 sed_active=0 display_enabled_ever=0 ctrl0(D010)=00
          addr=0009a matrix_base=0000 attr_base=0a00 tile_base=1400 bitmap_base=3400
[VDPDUMP]   00000-003ff: 1 non-zero
```
- `display_enabled_ever=0`, `ctrl0(D010)=00`: **the OS NEVER writes VDP Control 0
  (0xD010)** → the display is never enabled. crt_update() rendering a disabled
  display = black. So forcing crt_update changes would be premature — the OS has
  not asked for a visible display yet.
- Only **1 VRAM byte** written in 8s: the OS wrote a single glyph then stopped —
  it is early in display setup, likely waiting on some state before a full draw.

## The real VDP register protocol (from the transaction trace)
First writes (chronological):
```
a370 D034<-0e D035<-00        ; (some pointer/param pair)
b006 D012<-00 D013<-00 (x2)   ; control pair, cleared
e996 D040<-83 D041<-00        ; D040/41 = command/param (0x0083)
e99e D036<-00 D037<-00
e9a6 D034<-99 D035<-82
e9ae D026<-00 D027<-00
e9b6 D024<-99 D025<-02        ; <-- VRAM ADDRESS POINTER = 0x0299? then...
da3f D018<-c6 D019<-29        ; <-- VRAM DATA write lands at vram_addr=0x00099
```
KEY CORRECTION to the current MAME model:
- The VRAM data write at 0xD018 lands at **vram_addr=0x00099**, and that address
  was set by **0xD024/0xD025** (`D024<-99 D025<-02`), NOT by 0xD034/0xD036 as the
  current `vdp_w` assumes (case 0x34/0x36). i.e. **0xD024/0xD025 is (at least one
  of) the VRAM address-pointer register(s)**; the current model's 0x34/0x36
  mapping is wrong or incomplete.
- Registers the OS actually drives: D012/D013 (control pair), D018/D019 (VRAM
  data, 16-bit), D024-D027, D034-D037, D040/D041 (command 0x0083). The current
  model's assumed semantics (0x10 ctrl0, 0x20-0x24 mouse, 0x30-0x36 bases/ptr,
  0x40 cmd) do NOT match — needs a full re-map from the trace.

## What this means for the plan (aligns with ChatGPT)
1. Do NOT force display-enable or hack crt_update to make pixels. The OS itself
   must reach the point where it writes 0xD010 enable + streams a full screen.
2. The next question is a backward trace: **what is the OS waiting for before it
   enables the display and does a full draw?** (A status poll? Input? A mode/
   screen selection? The SED1335 path? Note sed_active=0 too — the front-panel
   LCD is also not driven yet.)
3. Correct the VDP register map in the driver from the trace (0xD024/25 pointer,
   D040/41 command, control pair D012/13 vs D010) — but only after we understand
   the enable condition, so we fix the model against real behavior not guesses.

## Harness note
The side-effect-free 0xD07E status port (and the internal occupancy dump) are the
correct way to observe activity — the old 0xD018 read-back heuristic is abandoned
per ChatGPT. The harness should read 0xD07E (bit0) for vram_active and gate G8 on
snapshot pixels once display-enable happens.
