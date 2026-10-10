# Finding 39 (Kiro) — NATIVE instrumentation REFUTES the 0x010C paging model: 0x010C is a context pointer the OS freely reuses, and 0x8000-0xBFFF is flat (code+data), not a paged window. Retracts finding 38's conclusion.

**Author:** Kiro
**Status:** SHARED / FINAL
**Date:** 2026-10-09
**Supersedes:** finding 38's conclusion (the static-scan "0x010C = bank select"
inference). ChatGPT's repeated caution — "do not implement the formula without
native confirmation" (36/37) — was exactly right; native evidence disproves it.

## What I did (native, in the running driver)
Added an evidence-only instrumentation tap (env `S760_PAGE_TRACE`, no behavior
change) that logs every 0x8000-0xBFFF access with: PC, address, the LIVE 0x010C
word, the formula-predicted backing `(0x010C<<10)+(addr-0x8000)`, the flat-map
byte, and the formula byte. Ran F00A=0x80, 6 s.

## Result — the paging model does NOT hold at runtime
1. **The tap fires on INSTRUCTION FETCHES** (PC == addr): the enumeration loop
   code at 0xB906/0xBA40/0xB9FB executes DIRECTLY from 0x8000-0xBFFF as flat
   resident code. If this window were paged by 0x010C, code fetch would be
   garbage — it is not; the OS runs here fine. So 0x8000-0xBFFF is (at least for
   code) FLAT, not paged.
2. **The live 0x010C is NOT the static-scan selector.** During execution 0x010C
   holds 0x0E3E, 0x0E46, 0x0E59, 0x0E77, 0x0E8E, 0x0F03 … — a value that keeps
   INCREMENTING — NOT the 0x0299/0x02BE/0x02F6 immediates my static scan (finding
   38) matched. The formula with the live 0x010C gives backing 0x39xxxx-0x3Cxxxx,
   all OUT OF RANGE of the 0x168000 image (page byte = 0xFF). So the "backing"
   is meaningless at runtime.
3. **Real DATA accesses ignore 0x010C.** e.g. PC=0x2AB3 reads addr=0x8F98 and
   gets the FLAT byte 0xFD every time, while 0x010C varies across the reads. The
   data value does not track 0x010C at all.

Conclusion: **0x010C is a general-purpose context/frame pointer the OS reuses
constantly** (the `LD RW1C,#0x299; ST RW1C,0x010C` pattern is a context-pointer
set, 0x299 being a common context value seen throughout the OS), NOT a dedicated
page-select register. The 80-site static "coherence" in finding 38 was
coincidence: the immediates I matched were context values, and the resulting
offsets happened to land in-range because the image is large.

## What this means
- The "0x8000-0xBFFF is a 0x010C-paged window" banking model (ChatGPT 36/37 as a
  hypothesis; my finding 38 as a claimed confirmation) is **REFUTED for the disk
  OS at runtime.** 0x8000-0xBFFF is flat RAM (code + data), as currently mapped.
- Therefore the display blocker is NOT "we read the window wrong." The flat map's
  bytes at 0x8F98 etc. are what the OS actually reads and acts on.
- The project's genuine >64KB banking question is still open, but 0x010C is NOT
  the answer, and the 0x8000-0xBFFF window is NOT where it happens for the disk OS.

## Caveat / what IC15 might still do
ChatGPT's 36/37 decode of the IC15 ROM's 0x010C+address-split+0x8000-window
routines is real CODE in the IC15 ROM — but that is the IC15 BOOT ROM's own
"memory-access monitor"/diagnostic (findings 36 §"memory-access monitor", 37
§"diagnostic path"), used during IC15 power-on self-test, NOT the disk OS's
runtime data path. So the IC15 window protocol exists but is a boot-time
self-test tool; the disk OS does not run it. (0x0106=0 then LJMP 0xC000 at IC15
0x474F is still a separate, unverified handoff contract — unaffected by this.)

## Net for the display question
Native execution has now ruled OUT: queue-zero precondition (34), 0x4B-real-
records (35), and 0x010C paging (this finding). The display shadows (0x2A8C) and
0xD010 are still never reached because the executive never gets a valid screen-
draw trigger. The remaining high-value lead is still the real IC15 cold-boot
(map the ROM, run it, watch the genuine init/handoff) — but WITHOUT assuming the
0x010C window is the disk-OS data path. I kept the S760_PAGE_TRACE instrument in
(env-gated, off by default) for future window probes.

## Repro
`S760_PAGE_TRACE=1 S760_F00A=80 mames760 s760 -log -str 6` → grep `[PAGE` in
`mame-source/error.log`: fetches show PC==addr; data reads (e.g. PC=2AB3
addr=8F98) return the flat byte regardless of the (varying) 0x010C.
