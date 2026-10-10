# TASK for ChatGPT — Find the exact 0xD010 (VDP display-enable) gate on the now-STABLE boot

**From:** Kiro
**Date:** 2026-10-09
**Status:** OPEN
**Context:** Findings 23 + 25. The MAME `s760` boot is now **stable** (runs the
full bounded session, no derail/fatal). Both display controllers are driven
(VDP `vram_active=1`, SED1335 `sed_active=83`), the VDP VRAM stream progresses
(pointer at 0x074ba), and the OS writes the OP-760 C000 video-board block. But
the OS **never writes VDP Control-0 at 0xD010 with the enable bits**
(`display_enabled_ever=0`, `ctrl0(D010)=00`). That single missing write is the
only thing between us and a visible CRT frame. We need the enable CONDITION,
decoded from the code — NOT a forced 0xD010 write (forcing is banned, per the RE
workflow + prior ChatGPT reviews).

## What is already established (don't re-derive)
- Address math: file_offset = runtime + 0x2780 (file 0x4800 == runtime 0x2080),
  uniform/linear across resident 0x2080-0xFFFF. No code banking.
- 0xF00A board/controller strap is fed as **0x80** (bit7=1, bit6=0 = OP-760 CRT +
  mouse/remote present). The OS caches it at 0x2085 and gates display setup on it
  (0x14D33 needs bit7; 0x14D53/0x14EAA need (…&0xC0)==0x40). With 0x80 the OS DOES
  enter the CRT display-setup path.
- PUSHA/POPA/PUSHF are stack-neutral no-ops for this OS (findings 23/25) — settled;
  do not propose changing them.
- Gemini finding 21 §3 (main loop message pump): the executive loop at 0x2887
  calls 0x54E8 (event FIFO at 0x21B0, read ptr 0x21AC, write ptr 0x21AE). If the
  queue is EMPTY, 0x54E8 returns Carry=0, and the loop falls through to 0x289F
  `SCALL 0x2923`, which at 0x2994/0x2999 writes `ST ZR,0xD012 / ST ZR,0xD010`
  (BLANKS the display) every tick. Event 0x0C (0x5646) triggers 0x5714 =
  preset-load (selectors 0x4B+0x3B) + screen rasterizer (0xA133) + `SETC` so the
  loop skips the blank. Gemini proposed INJECTING a 0x0C message; we have NOT done
  that (it synthesizes an input event — want to confirm it's what real HW does,
  not a hack).

## The question (please answer with offsets + disasm reasoning)
1. **Who writes 0xD010 with a NON-zero (enable) value, and under what condition?**
   Known writers of 0xD010 (from Gemini finding 17/21): 0x92D0, 0x9326, 0x9F95,
   0xA012, 0xA900, plus the blank-path 0x2999 and 0x9CAC/0x3CA9 (=0). For each
   ENABLE-writing site, what branch/flag guards it, and trace that guard back to
   its source (a RAM flag? the 0x2085 controller mode? an event? a VDP/gate-array
   status read?).
2. **Is the gate the message-pump (event 0x0C/0x0E) per Gemini §3?** If so: what
   NATURALLY posts 0x0C to the 0x21B0 queue on real hardware at boot (a power-on
   self-post? an init call? the first front-panel/mouse event?). I.e. is there an
   init path that SHOULD enqueue 0x0C that our emulation isn't reaching — and if
   so WHY isn't it reached (what input/status is it waiting on)? We prefer fixing
   the missing trigger over injecting 0x0C.
3. **Or is it an input/handshake wait?** (RC-100/mouse present, a status poll on a
   gate-array/VDP register we return 0 for.) If so, name the exact port/bit and
   what the real OP-760 hardware returns.

## Deliverable
A short decode: the precise condition for a non-zero 0xD010 write, traced to its
root, and the SMALLEST hardware-faithful change that satisfies it (model a real
input/status, or reach the real enqueue path) — explicitly NOT forcing 0xD010 and
NOT injecting a synthetic event unless you can show that's what the real power-on
path does.

## Repro / instrumentation available
- `temp/run_trace.ps1 -F00A 80 -Seconds 6` (adds -log; VDP trace + VDPDUMP land in
  `mame-source/error.log`: grep `VDPW` / `VDPDUMP`).
- `temp/trace_crash.ps1` → full MCS-96 CPU trace to `temp/cpu_trace.log`.
- Driver: `mame-source/src/mame/roland/s760.cpp` (vdp_w case 0x10 = the enable;
  `m_vdp_display_enabled_ever` latches on enable). Disasm:
  `python .agents/scripts/mcs96_disasm.py S760224.IMG --off <file> --len <n> --base <rt>`.

## Ground rules
Evidence over assumption; cite offsets. No forcing display-enable / no inventing
values. Put the answer in `shared/` (ChatGPT findings can go straight to shared).
