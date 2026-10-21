# IM1 ROM-loader and MIDI-redraw fixes

**Date:** 2026-10-20. Full IM1 remains open; the timing candidate is not promoted.

The malformed authored-image header and the browser's redraw-related MIDI loss are repaired. The latter is now tracked as BUG-175, separately from BUG-168's wider timer-wrap/deadline requirement. Separating those defects prevents a passing receive-byte test from being mistaken for a complete timing proof.

[Roadmap](bluescsi-image-mount-plan.md) · [Validation](../condensed/validation/bluescsi-im1-bug-fixes-2026-10-20.json)

## BUG-174: native ROM loading

The minimal example previously started its header with `S770 MR25A`. Original IC15 code at `4E69..4E96` compares a 15-byte signature including four leading zero bytes and a terminating NUL, then requires floppy type `0x50`. The malformed header therefore stopped loading after the first512-byte transfer on both tested emulator builds.

[The example header](../../examples/minimal_os/project.json) now satisfies that exact contract. The [loader test](../../tests/test_rom_boot_os_loader.py) uses a private working/configuration directory, checks process exit, observes the first original-ROM handoff at `4755`, and compares all **1,032,192 loaded bytes** with disk `0x4800..0x1007FF`. The unchanged DMA verifier still requires all **112 contiguous track transfers**, following the header read. The example-build regression also checks the full16-byte signature.

The initial header correction caused repeated boot transfers because the incomplete example continued executing after handoff. Stopping this LOAD-only test at its first actual handoff prevents that unrelated execution from polluting the transfer census. The observer only reads state and exits the emulator; it does not change guest RAM, registers, PC or firmware. This is not a claim that the minimal example is a complete runnable OS.

## BUG-175: MIDI starvation during CRT redraw

On timeout, the browser clears880 CRT characters while its callback keeps interrupts masked. The previous simultaneous-stall test observed a107.53925ms post-release gap between native MIDI reads and only585 of775 expected reads. This receive-starvation defect was initially recorded under BUG-168 before its cause was narrowed.

The candidate now calls its existing caller-qualified cooperative service at each character clear. That adds **three code bytes**, retaining the native display functions, GB-6 v9, SDS fixes, warning correction and Verify Medium repair. The synchronous composed stack maximum remains **166 bytes**; this is still not a universal outer-caller/IRQ bound.

| Artifact | SHA-256 / size |
| --- | --- |
| Repaired combined timing candidate | `5e5ec01692ca7218f0a39e01aaff6ed0c45237cfd94af5f8f227dd86d0d19064` |
| Predecessor | `5581ee53a84ea5395ee0bb554fc2b31128bb5740835789b335c83b4c9a548f94` |
| Unchanged selectable boot ROM | `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb` |
| Unchanged emulator | `a42d26f755d2d902ac1adb79b76c60b3373be167e849c35ad09a568691bfa937` |
| Resident allocation | **6,583 / 8,002 bytes; 1,419 free** |

An independent rebuild matches exactly. Static decoding/branch-target checks, a source-delta assertion and bounded changed-offset audit pass. No boot-ROM change or new memory region is required.

## Native regression scope

Ten cases pass on this exact candidate:

- Simultaneous MIDI with D7 stalled after byte1 and before byte3,999: all775 reads including audition, exact239,616-byte resident stereo content, explicit retry, playback and silent release. Both contain actual MIDI arrivals during the stall.
- Original dense-note D7 reproduction: all769 stress bytes, exact119,808-byte resident content and playback/release; maximum observed service27.990375ms.
- CRT cancellation/retry/Load plus SDS cancellation/retry and exact publication.
- LCD cancellation/retry/Load and separate full32-byte filename/selection/Load case.
- Incoming SDS during listing and mounting: native receive ownership excludes inappropriate switching/handoff and cancellation restores idle.
- Foreground Remote Mode admission during listing and mounting.

The two stalled-target runs release after86.73375ms and112.865375ms respectively. These are finite workload observations, not worst-case deadlines. Matched service entries/exits preserve stack, selectors, masks and saved scratch registers, except the intentional RW38 idle-time adjustment. Snapshot counts and full backend totals are recorded in the validation and final verification section below.

## Remaining active bugs and disposition

| Bug | Scope after this batch |
| --- | --- |
| BUG-005 | Unrelated audio/ramp accuracy target; remains open |
| BUG-137 | Reviewed upstream BlueSCSI discards switch failure; local readiness checks do not repair the device firmware |
| BUG-140 | Retired full-screen descriptor experiment; WONTFIX because the selected and qualified browser uses the popup contract |
| BUG-145 | Reviewed upstream filename-filter/index mismatch; first-profile naming/preflight restrictions remain necessary |
| BUG-146 | Reviewed upstream long-path termination defect; first-profile path restriction remains necessary |
| BUG-168 | Still IN-PROGRESS: worst-case single-byte/control service and wrap-safe total deadline remain unproved |
| BUG-174 | FIXED: correct header, first-handoff transfer and byte-exact RAM acceptance |
| BUG-175 | FIXED: redraw service prevents the reproduced MIDI loss; scoped native regressions pass |

No upstream BlueSCSI firmware was modified or flashed. The upstream entries refer to the pinned revisions already reviewed, not a fresh audit of whatever firmware is currently installed. No physical S-760/BlueSCSI timing or MIDI-FIFO equivalence is inferred from these emulator runs. Full native ownership/IRQ and other write-reset gates remain separate.

## Final verification

**1089 passed, 3 skipped, zero failures/errors** in the full serial backend suite. The ten native cases contribute **104 snapshots**, preserving7,360 immutable/gap bytes with642 mutable bytes explicitly excluded, plus the native parser hook and Verify Medium repair. Original firmware hashes remain unchanged. The native executable was unchanged in this batch; the prior default-disabled equivalence evidence retains its exact build scope.
