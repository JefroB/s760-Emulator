# Finding 27 (Kiro work) — The 0xD010 enable chain is NEVER reached: no screen-draw EVENT is ever posted on the stable boot

**Author:** Kiro
**Status:** DRAFT in kiro-work (empirical trace data for ChatGPT task 26 / the
display-enable question). Move to shared once ChatGPT finishes doc condensing so
we don't collide.
**Date:** 2026-10-09
**Method:** full MCS-96 CPU trace of the now-STABLE boot (F00A=0x80), 207k insns,
`temp/cpu_trace.log`; hit-count analysis via `temp/analyze_mainloop.ps1`,
`temp/trace_pump.ps1`, `temp/find_enqueue.ps1`.

## The display-enable call chain (decoded)
```
0x92A6  CMPB 0x2488,#0 ; JNE 0x92E1   both branches -> write 0xD010 (enable)
0x92D0  ST RW5E,0xD010                 <-- THE enable write (value from shadows
0x92CB  ST RW5C,0xD012                     0x2A94 ctrl0 / 0x2A8C ctrl1; 0x92FE
                                            ORs bit0x10 when mode flag 0x2970==2)
```
0x92A6/0x92D0 is called from the SCREEN RASTERIZER path (0xA133 + the per-screen
handlers in 0x1Fxxx-0x31xxx that set the 0x2970 display-mode flag).

## Hit counts on the stable boot (the smoking gun)
```
0x2887 main-loop head      : 31   (main loop IS running)
0x54E8 message pump        : 31
0x5646 CMPB #0x0C draw ev  : 31   (pump checks for the draw event every pass)
0x28AF carry/draw branch   : 31   (loop takes the "handled" branch, NOT the blank)
0x2923 blank-display       : 0    (so it is NOT blanking 0xD010 either)
0x5714 draw/preset handler : 0    (NEVER)
0xA133 screen rasterizer   : 0    (NEVER)
0x92A6 / 0x92D0 enable      : 0    (NEVER — 0xD010 enable never executes)
0x7D17 / 0x7DAD enqueue     : 0    (NO event is EVER posted to the queue)
```

## What this means
1. **It is NOT the "empty queue blanks the display" case** (Gemini finding 21 §3
   hypothesis): the blank path 0x2923 is never taken (0 hits), and the pump keeps
   taking the carry/"handled" branch. The messages it reads dispatch to small
   handlers (observed: message 0x01 → selector 0x4B housekeeping; the first msg
   matched nothing and fell through all compares).
2. **The real gate: the OS never POSTS a screen-draw event (0x0C), so the
   rasterizer + 0xD010 enable are never reached.** The enqueue routine 0x7D17/
   0x7DAD (writes 0x21B0[0x21AE++]) is NEVER called in the whole boot. The events
   the pump consumes are seeded/pre-existing, not the 0x0C draw.
3. Therefore the first screen paint (and thus 0xD010 enable) is triggered by
   something that posts 0x0C — almost certainly an **INPUT/EVENT source that is
   silent in the emulator**: front-panel key, mouse, RC-100, or an init-time
   self-post that depends on a status we still return 0 for. On real HW the user
   sees a screen at power-on, so either (a) boot init self-posts a draw we aren't
   reaching, or (b) the OP-760 "controller present" handshake posts it.

## Concrete next probes (for whoever picks this up)
- Find callers of 0x7D17 (the enqueuer) in the static disasm and see which one
  posts 0x0C and under what guard — then check why that guard isn't satisfied
  (what input/status it reads). This is the exact root of the display-enable gate.
- Check the boot path 0x2831→main loop for a one-time screen-draw/self-post that
  our emulation skips (e.g. gated on a controller/VDP status we return 0 for).
- Shadow values 0x2A94/0x2A8C at the point 0x92D0 WOULD run: confirm they carry
  the enable bits (so that reaching the rasterizer actually turns the CRT on).

This refines ChatGPT task 26: the gate is "no 0x0C screen-draw event is posted",
upstream of the message pump — not the pump's blank path. Evidence-first; no
forcing.


## UPDATE (same session) — two surprising corrections from RAM inspection

Dumped live work-RAM at frame 180 (`temp/dump_queue.ps1`, F00A=0x80):
```
[Q] read_ptr(21AC)=0102  write_ptr(21AE)=ef1c
[Q] buf 21B0: 54 97 cb 01 0c 01 a1 99 02 1c c3 01 0c 01 1c a1 3b 00 1c ...
[Q] mode 2970=00  ctrl0_shadow 2A94=01c3  ctrl1_shadow 2A8C=0601
[Q] 2085(F00A cache)=c3   2488 gate=63
```

### Correction A — 0x2085 is NOT 0x80; it ends up 0xC3 (and 0xC3 FAILS the CRT test)
`mmio_r(0xF00A)` returns 0x80 and is read exactly ONCE (confirmed in error.log:
`[MMIO R] 0xF00A => 0x80`). But the cached byte at **0x2085 = 0xC3** at frame 180.
So 0x2085 is **OVERWRITTEN after the initial 0x249B cache** by other code — it is
NOT a stable "controller mode" cache in v2.24. And critically `(0xC3 & 0xC0) ==
0xC0`, NOT `0x40` — so the CRT-path test at 0x14D53/0x14EAA (`==0x40`) would FAIL
with 0xC3. Either (a) those 0x14Dxx routines run BEFORE 0x2085 is clobbered, or
(b) 0x2085 is reused for something else and the controller gate lives elsewhere.
=> The "0x2085 = cached 0xF00A controller mode" model (findings 20/23) is at best
only true transiently. NEEDS a write-watch on 0x2085 to see who writes 0xC3 and
when relative to the display decision.

### Correction B — 0x21B0 is NOT an event queue in v2.24; it's static code bytes
RAM at 0x21B0 == the disk image's initial bytes at file 0x4930 EXACTLY
(`54 97 CB 01 0C 01 A1 99 02 1C ...`) — never written by the OS. And the pointers
0x21AC=0x0102 / 0x21AE=0xEF1C are not valid 0..0x7F queue indices. So the message
pump at 0x54E8 (`LD RW38,0x21AC; LDB RDA,0x21B0[RW38]`) is indexing into STATIC
CODE with a garbage index — the "events" it dispatches are coincidental code
bytes, not real messages. => The "0x21B0 128-byte circular event FIFO" model
(Gemini finding 21 §3) does NOT hold for v2.24 as-mapped. Possibilities:
  1. The real queue base/pointers are different addresses in v2.24 (21 §3 was
     derived from a different code read / version).
  2. A memory-map aliasing bug: 0x21AC/0x21AE should be writable work-RAM that
     the OS inits, but they still read the image's static bytes → maybe the init
     that clears/sets them never runs, OR these addresses are being shadowed.
  3. RW38's actual base isn't 0x21B0 at runtime (the pump may be mis-entered,
     same class as the earlier mid-instruction issues).

### Net
The display-enable gate analysis must NOT lean on the 0x2085 / 0x21B0 models until
these two corrections are resolved. The firm facts remain: 0x92A6/0x92D0 (the
0xD010 enable) and 0xA133 (rasterizer) are NEVER reached; no genuine screen-draw
event is posted. Recommend a **write-watch (wpset) on 0x2085, 0x21AC, 0x21AE, and
0x2970**  during boot to see who writes them and in what order — that pins the
real gate. (Kiro can run this next if ChatGPT/Gemini don't get there first.)
