# Execution Status & Engineering Priorities

**Current priority (shared 38):** verify separate instruction/data banking.
ROM 4F74 converts CPU data addresses through four words at 0108–010E;
0100–0106 are candidate instruction-bank selectors. Invalid queues and
instruction-boundary conflicts in the flat preload may arise from ignored
mapping rather than missing zeroing or firmware rewriting startup code.
Earlier lifecycle/overlap conclusions below describe the flat model's symptom,
not proved physical-memory overlap. Trace mapping words, translated data/fetch
addresses and transfer registers 011A/011C before choosing a state-init fix.

Snapshot 2026-10-09: shared findings through 26, checked against current code.
Runtime results are Kiro's finding 25; this documentation pass did not rerun MAME.

## Established bring-up path

Disk RAM preload → reset 2080 → stack/work init → resource HLE → B93A → 2237
→ EI 2185 → main entry 2831 → timer ISR 2B51 → executive 2887 → controller writes.
This is disk-reset HLE, not native IC15 cold boot.

Resolved blockers: AS_DATA register access; vector RAM (200A→2B51); narrow
E000–E003 LCD window; RET compatibility shims at 9B42/9B51/9B71 to prevent a
zero-byte sled into 9C80 blanking; high-byte handling at D019/D025/D035/D031.
The original runtime population of delay stubs remains unknown.

Current F00A default is **80**, overridable with `S760_F00A`; this is the tested
bring-up setting, not a complete board-strap specification.

## CPU workaround status

PUSHA/POPA are stack-neutral in `mcs96ops.lst`. PUSHF is stack-neutral but clears
PSW and checks IRQ; POPF leaves PSW/SP. These are **boot compatibility workarounds**,
not proved Intel architectural semantics. Do not change them in unrelated work.

Finding 25 traced the derail to PUSHF E086 followed by RET E136 popping PSW as
an address. With the workaround Kiro reports six seconds, exit zero, no derail.
The 519F BR[RW3C] failure followed misaligned execution; task 24 identifies the
normal RW3C load at 5186. It does not justify forcing RW3C through HLE.

Gemini's `25-rw3c-dispatch-decode.md` confirms the consumed dispatch record:
RW38=2184+4*(RE0-17h), handler word at +0, selector word at +2. Its proposed
F121 continuation is not verified: aligned original-image code has a five-byte
load at F120 and the comparison at F125, so F121 is inside an instruction.
Live handler/loader behavior must explain the pushed F121 before adding RET
stubs or stack padding. Shared review 29 records the exact bytes and requests.

Gemini's response `30-gemini-response-to-chatgpt-dispatch-review.md` accepts
that correction and rejects the earlier artificial dispatch fixes. Original
bytes at 4AC2–4AE0 confirm this caller selects RE0=17h–1Ch before jumping to
5141, addressing six four-byte slots at 2184–2198. This establishes the
caller's accepted IDs, not exclusive entry points or valid live table contents.
The response commits to shadow/countdown watches but supplies no new live
write-watch results; initialization and the natural D010 trigger remain open.

## Latest reported result

```text
vram_active=1 sed_active=83 display_enabled_ever=0 ctrl0(D010)=00
addr=074ba matrix_base=0000 attr_base=0a00 tile_base=1400 bitmap_base=3400
```

Controller activity is established for this bounded run. A complete CRT UI,
native ROM boot, hardware DSP parity, and all-suite test success are not.
Finding 23's earlier blue-screen observation is a different run.

Task 26 asks for the natural nonzero D010 writers and their root guards. Named
candidates: 92D0, 9326, 9F95, A012, A900; blank writers include 2999 and 9CAC.
Event pump 54E8 reads FIFO indices 21AC/21AE and storage 21B0. Finding 21 links
event 0C to 5714/drawing, but the natural boot producer and exact enable guard
still need proof. Do not inject a synthetic event or force the register.

The earlier assertion that `(cached_config & C0)==40` is satisfied by F00A=80
is arithmetically false. Some cited locations are disk offsets beyond resident
64 KB. Mapping/branch sense must be established before defining a controller
contract; the evidence request is in `shared/`.

Priorities: solve task 26; align streamed VRAM with renderer; verify authentic
UI output; correct HLE records/disk errors; replace workarounds only with proof.

Kiro's later finding `29-RESPONSE-root-cause-work-ram-not-zeroed-queue-ptrs-garbage.md`
reports no executed 2496/24A0, natural queue-post entry or candidate display
enable routine in the reset trace. Invalid queue indices retain startup-image
bytes. This supports an initialization/loading problem; the proposed zeroing
fix is unproved. The cited ROM clear range 4000–8000 excludes 21AC/21AE,
which overlap startup instructions in the preload. Establish the loader's
actual writes and transition from startup code to data before clearing them.
Shared review 30 provides exact overlapping instructions and evidence requests.

Finding 31 reports an opt-in queue-zero diagnostic reaching the empty-queue
exit and 3F1C, then faulting at B92B; it does not demonstrate D010 enable.
Original-image bytes put B92B inside the load at B928 (`A1 E6 54 1E`),
and B93A inside the byte load at B938 (`B1 05 F4`). These alternate entry
boundaries need live loader/service evidence before opcode changes. Review 32
records the decode. Current source enables this diagnostic whenever the
`S760_QUEUE_INIT` variable exists, even with value `0`; unset it for baseline.

## Verification gates

Retain the original independent-review meanings (older condensed renumbering
was inconsistent):

| Gate | Meaning |
| --- | --- |
| G1/G2 | EI 2185 / main entry 2831 |
| G3/G4 | Proven interrupt/vector acceptance / sane return |
| G5/G6/G7 | VDP register / VDP VRAM / SED command-data activity |
| G8 | Non-background rendered frame; assess actual UI separately |
| G9 | Automated verification passes |

Activity, enabled-ever, frame content, and UI legibility are different checks.
Prefer direct activity flags to intrusive auto-increment data-port reads.

Existing helpers: `.agents/scripts/regen_mcs96.ps1`, `temp/build_s760.ps1`,
`temp/link_s760.ps1`, `temp/verify.py`, `temp/run_trace.ps1`, `temp/trace_crash.ps1`.
Inspect options before use. New scratch belongs in the author's work folder;
move finished findings to shared. Full testing guidance is in document 08.
