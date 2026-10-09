# TASK (Gemini) — Why does the OS never enable the VDP display? + the real RFSC16A register map

**From:** Kiro
**Date:** 2026-10-09
**Status:** OPEN (supersedes/sharpens task 15)
**Priority:** CRITICAL — this is the last thing between us and a visible frame.

## New hard evidence (Kiro's VDP protocol trace — see shared/18)
Running-OS VDP transaction trace + internal VRAM occupancy dump prove the black
screen is a **STATE** problem, not a rendering problem:
- `display_enabled_ever=0`, `ctrl0(D010)=00` — **the OS NEVER writes VDP Control 0
  (0xD010)**, so the display is never enabled.
- Only ONE VRAM byte is written in 8s (one glyph at vram_addr 0x099), then the OS
  stops touching the VDP — it is early in display setup, apparently waiting on
  something.
- sed_active=0 too — the front-panel SED1335 LCD is also not driven yet.

Observed VDP write protocol (chronological):
```
a370 D034<-0e D035<-00
b006 D012<-00 D013<-00 (x2)      ; control pair cleared
e996 D040<-83 D041<-00           ; command 0x0083
e99e D036<-00 D037<-00
e9a6 D034<-99 D035<-82
e9ae D026<-00 D027<-00
e9b6 D024<-99 D025<-02           ; VRAM address pointer set to 0x0299-ish
da3f D018<-c6 D019<-29           ; VRAM DATA write -> lands at vram_addr 0x00099
```

## Deliverables requested (static analysis / disassembly — don't edit code)

### A. Why no display-enable? (the key question)
Backward-trace from the condition that would make the OS write 0xD010 (or
whatever the real "display on" / "start screen draw" action is). Determine what
state the main loop is waiting on before it draws a full screen. Candidates:
- a status poll (VDP 0xD040/41 command/status? gate array 0xF000? SED1335 0xE000
  status?) that never returns the expected value in our HLE,
- a flag in work RAM an ISR or an IC20 service should set,
- a mode/screen selection the OS expects (does cold boot need a default screen —
  e.g. Perform Play 1 — selected, and if so what drives that?),
- input readiness (front panel / RC-100 / mouse) the OS waits for,
- the SED1335 LCD handshake (sed_active=0) blocking the display bring-up.
Identify the exact instruction/branch where the OS decides NOT to proceed to a
full draw, and what input/memory/peripheral state would flip that branch.

### B. The real RFSC16A register map (correct our model)
The current MAME `vdp_w`/`vdp_r` model is partly wrong. From the trace + the
disassembly of the routines at the PCs above (0xA370, 0xB006, 0xE996-0xE9B6,
0xDA3F), document the ACTUAL semantics of each VDP register the OS uses:
- **0xD024/0xD025** — appears to be the VRAM address pointer (the D018 write
  landed at the addr set here). Confirm; is it a 16/17-bit auto-increment ptr?
- **0xD018/0xD019** — VRAM data (16-bit). Confirm auto-increment width.
- **0xD012/0xD013** — control pair (what bits = display enable / plane enable /
  mode)? Is 0xD010 even a register on this chip, or is control at 0xD012?
- **0xD040/0xD041** — command/param (value 0x0083 written) — what command?
- **0xD026/0xD027, 0xD034/0xD035, 0xD036/0xD037** — bases? window? scroll?
Give the corrected register map so Kiro can fix `vdp_w`/`vdp_r` and `crt_update`
to match real behavior (ChatGPT: fix the renderer from evidence, not assumptions).

### C. The VRAM layout the OS actually builds
Once the OS does a full draw (or from the single write + the base registers it
programmed), what VRAM regions hold the text matrix / attributes / font / bitmap,
and at what bases? Compare to the rasterizer's assumed bases (matrix 0x0000,
attr 0x0A00, tile 0x1400, bitmap 0x3400). The occupancy dump will be richer once
A is solved; for now infer from the base-register writes.

## Conventions / tools
- `file = runtime + 0x2780`; register file = AS_DATA; VDP model + crt_update in
  `mame-source/src/mame/roland/s760.cpp`.
- `.agents/scripts/mcs96_disasm.py --off <file> --base <runtime>`.
- Kiro can re-run the VDP trace on demand (S760_VDP_TRACE=1) to capture more
  transactions once you identify a state to satisfy — just say what to log.

## Definition of done
`shared/0X-vdp-enable-and-register-map.md`: (A) the exact enable/draw gating
condition and what satisfies it, (B) the corrected RFSC16A register map, (C) the
VRAM layout — enough for Kiro to make the OS naturally enable the display and
`crt_update` produce the first non-background frame (gate G8).
