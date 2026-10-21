# IM1 timing, operation exclusion and checkpoint recovery

**Date:** 2026-10-20. **Decision:** IM1 remains open. Thirteen native acceptance cases pass, including four additional operation-conflict checks and a repaired partial-command checkpoint boundary. The MIDI timing repair is a promising experimental OS, not a replacement for the established candidate yet.

[Validation data](../condensed/validation/bluescsi-im1-timing-recovery-2026-10-20.json) records each case's firmware/executable identity, commands, physical inputs, matched observations, builder/probe sources and limitations. Findings 298 and earlier remain valid within their stated scopes; this result extends their recovery coverage and supersedes the unbounded-parser trial for the named MIDI stress case only.

## Exact builds and fit

| Artifact | SHA-256 / allocation |
| --- | --- |
| Established combined OS, unchanged | `6297274dd5c33b0b37409d3cddcd53e40b8af6140f2c416fc0213181cd3ba628`; 6,452/8,002 bytes, 1,550 free |
| Experimental bounded-parser OS | `367f067d78c8e69a1b670efda1d7146b8843d79c59c16ab207df0fdbc0ce496c`; 6,580/8,002 bytes, 1,422 free |
| GB-6 selectable boot ROM, unchanged | `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb` |
| Prior native executable | `7c994e8679c51e71801ce7c4ad570983b5a7a7e55f1ae135ed5fc58dda658962` |
| Native executable with checkpoint fix | `4cf1cfabaab8d3a9068ddac0ec81f60afb0dc92c903ae66cb5ed4ddac58fc4ee` |

Original Roland OS/boot hashes remain unchanged. Both OS candidates retain mandatory GB-6 **v9**, the existing SDS repairs and the CRT/LCD browser. No additional boot ROM change is needed. The experimental image rebuilds byte-for-byte and all new code disassembles; the largest contiguous remaining code gap is 1,191 bytes. Another memory region is not required for this trial.

## Established-OS gates completed

All actions use ordinary panel/pointer/media/checkpoint input and read-only observation. Private writable media isolate the source library.

| Native check | Observed acceptance |
| --- | --- |
| Load conflict | Verified Disk-header click plus Mode overlaps native READ(6) commands; no Toolbox command is admitted. All 119,808 PCM bytes load correctly and audition/release passes. |
| Quick Initialize conflict | Mode overlaps native writes to a browser-mounted 32 MiB IMG; no Toolbox command. Final Roland header and all five hierarchy counts are valid/empty. This is quick Initialize, not full-surface formatting. |
| Delete conflict | Mode overlaps confirmed hierarchy deletion on mounted HD2. No Toolbox command or preconfirmation write; resulting disk has zero hierarchy counts and no sample data entries. |
| Copy conflict | Mode overlaps HD2-to-HD0 native writes. No Toolbox command; source stays byte-identical and destination retains 13 samples/119,808 exact PCM bytes. |
| Partial-D8 checkpoint recovery | Three recalls after the first D8 CDB byte, including a renamed/replaced catalog, now return failure and leave the browser in Collections with no native handoff/allocation. Explicit fresh selection loads the replacement's exact 119,808 PCM bytes and plays/releases. |

The last three checks use the rebuilt executable. Load and Initialize used the preceding executable; their per-case identities are retained rather than relabelled.

## BUG-170: checkpoint command replay repaired

Before the fix, restoring a partly sent D8 automatically completed the saved index against the current host catalog. Replacing B.iso/index1 with C.iso containing A caused the native loader to load A without a new selection. Exact PCM comparison confirmed the wrong media, not merely a changed display label.

The opt-in fixture now marks an active COMMAND phase as invalid when a checkpoint is restored. Completing that saved command returns CHECK CONDITION / UNIT ATTENTION `06/28` and cannot select external media. A new target selection starts a new command. The guard is recomputed from the recalled controller state; it is host-timeline state, not serialized guest state.

Twelve synthetic SPC cases cover 0, 1, 5 and 9 transmitted CDB bytes on optical ID1, writable IMG ID2 and ordinary ID0. The opt-in targets reject the stale command and accept a fresh selection; the ordinary target retains its normal behavior. The regression demonstrably fails on the old executable. The separate native browser test establishes visible recovery and exact subsequent Load/playback. This does not claim that every possible preselection, DATA IN/OUT, reset or physical-device boundary is qualified.

The complete backend suite passes **959 tests, zero failures/errors/skips**. Ordinary fixture-disabled native boot, menu/pointer input, MIDI audio and note release pass before and after the rebuild. The complete **33,554,432-byte wave memory is identical**, SHA-256 `a6a2fdc2e0afbbe863f1f64240c7627bf5fa309023a485884f7b143412d25699`.

## BUG-168: bounded-parser trial

The native parser at `000F:213A` normally drains its live MIDI ring. The experimental hook calls an 89-byte admission helper at `000F:1400`, physical `005000`, file `009800`. While browser service is active, context word physical `005BDA` permits at most 32 parser admissions and stops admitting further bytes after 16,000 timer ticks. Pending work is scheduled after browser service returns to its masked context. Outside browser service, the helper restores native context and follows the original parser path.

The nominal total transfer budget becomes 32 × 65,536 ticks (2.097152 seconds); this is not yet a proven wall-time limit. A single admitted MIDI byte or native control interrupt can run beyond the admission threshold.

The dense-note stress case now passes:

- 769 incoming bytes during a 100-entry D7, plus six subsequent audition bytes: **all 775 parsed exactly in order**.
- No observed ring overflow; maximum pending distance 426 in the 512-byte ring.
- All 188 service pairs preserve scratch/mapping/mask/SP contracts. Longest service is **28.006625 ms**, compared with the established OS's 479.111125 ms.
- Actual timer-read duration agrees with the modulo tick delta in every service pair; **no complete timer wraps are lost in this run**.
- All 119,808 resident PCM bytes remain exact; before/after audition and note release pass.

Seven additional native regressions pass on the same experimental OS: CRT D7/D8 cancellation and fresh Load/SDS retry; SDS ownership during listing and mounting; LCD cancellation/retry and failed-target recovery; Remote Mode admission/cancellation during listing and mounting. The data identifies the old/new executable used in each run.

Earlier private trials are rejected. The eight-byte/four-millisecond trial with continuation scheduled inside the parser caused sustained audio after all 775 bytes had been parsed (BUG-169). Moving continuation scheduling alone at that small quota still overflowed the ring and timed out after 2,528 D7 bytes. The final combined quota/threshold/scheduling revision passes; the precise native control/envelope mechanism behind the first trial's release failure remains a hypothesis. BUG-169 is fixed in the new experimental revision; BUG-168 remains **IN-PROGRESS** pending a full timing bound.

## Memory and remaining feasibility work

All 7,360 immutable/gap bytes in physical `003D3E..005C7F` survive **111 additional snapshots**: 18 on the established OS and 93 on the experimental OS. The 642 declared mutable bytes are excluded. Experimental snapshots also preserve the three-byte native parser hook. The new helper uses eight local stack bytes; neither that value nor the earlier 166-byte custom bound establishes the whole native caller/callee/ISR depth.

The remaining decision gates are specific:

1. Prove the maximum native single-byte/control-ISR duration and wrap-safe total deadline; passing this finite MIDI workload is insufficient.
2. Complete the combined native stack and indirect-alias/DMA ownership contracts.
3. Finish FDC, conversion and full-surface-format conflict coverage, plus broader target faults and reset during native writes.
4. Qualify the experimental timing hash across the remaining established compatibility matrix before promoting it.

Physical BlueSCSI configuration/timing and real-machine release qualification remain separate. RC-100 input testing remains waived by the user, with compatibility assumed for the untouched path. The stock four-target collection layout, 100 entries per folder and writable IMG/read-only ISO policy are unchanged.
