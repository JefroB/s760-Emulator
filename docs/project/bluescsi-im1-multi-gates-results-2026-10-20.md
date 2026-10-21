# IM1 batch: conversion, recall, controller and parent screens

2026-10-20. Three scoped gates pass on unchanged candidate `19448d85773dd99081a45cdc33ca7defd82f4a4bd3b9cb28a2b533676d68a45c`. The wider parent-screen matrix also exposed **BUG-165**, so complete parent-context acceptance remains open. Volume Dump FD initialization passes; populated dump save/reload remains open.

The candidate retains GB-6 v9 and the existing selectable boot ROM. Its allocation remains **6,487/8,002 bytes**, with **1,515 free** and **1,297 contiguous after code**. No firmware, emulator or production runtime code changed in this batch. All native actions use physical input or the normal checkpoint API; observers do not force guest RAM, registers or PC.

## Completed scoped checks

| Check | Evidence | Limit |
| --- | --- | --- |
| Browser-mounted Akai Convert Load | Select `StringEnsembles.iso` through the browser on CD1, enter native Convert Load, import the first volume, assign its patch and play/release notes 55/72/96. All 30 samples, totaling **13,568,196 PCM bytes**, match the established original-firmware conversion hashes. | One supplied Akai S1000 CD/volume. The hashes include the original firmware's documented loop-tail adjustments; arbitrary Akai/Roland media remain separate. |
| Same-process checkpoint recovery | Save the native B image Load screen, select/load A, restore the checkpoint, attempt Load, then explicitly select B again. The stale attempt leaves the allocation cursor at zero. A second run saves an explicitly marked selection; read-only bus tracing captures native TUR returning **CHECK CONDITION 02**. Explicit reselection restores **119,808 exact B bytes**, playback and release. | The emulator fixture deliberately invalidates selected media after recall. This is not physical BlueSCSI reset handling, cold checkpoint recall or active-transaction restoration. The trace retains the relevant TUR/status prefix but drops 74 later records; it is not a complete transcript. |
| Current-build Mouse+CRT recovery | Genuinely saved controller 1: D7 cancellation drains 4,000 bytes; interrupted D8 queues no follow-on command or Load. Fresh selection/index 99 loads 119,808 exact bytes and plays/releases. Retained SDS cancel/retry preserves those samples and publishes 160 exact new bytes. | Current controller/transport/SDS evidence, not a new complete IRQ, concurrency or hardware timing matrix. |

The Akai source contains 15 distinct left/right pairs. Both output channels are active and different for each auditioned note. This directly demonstrates stereo content through this conversion path; it does not replace the remaining native Roland stereo/geometry matrix. Opening/exiting the browser after conversion also preserves playback.

## Parent-screen result and BUG-165

The final native GB-6 run completes two browser/catalog/Exit cycles from each of 13 distinct screens:

| Parent | Screen |
| --- | --- |
| Perform | `0025` |
| Patch | `006C` |
| Partial | `0085` |
| Sample | `00AE` |
| System Parameter | `0121` |
| Load / Save / Copy / Delete | `00F6 / 00F8 / 00FA / 00FC` |
| Utility / Save System / Optimize / Convert Load | `0104 / 0112 / 0114 / 0100` |

All **26 cycles** return to the expected screen ID and preserve the browser/SDS code and loaded PCM. Final native Mode → Performance selection restores playback with the same peak as before the matrix and a silent release. The matrix qualifies these functional checks, not complete visual/context restoration.

Visual review found that System returns with **Perform highlighted**, despite still displaying System Parameter. A matched Mouse+CRT comparison establishes the regression:

- Original OS: menu depth `3 → 4 → 3`; ancestor `8120` and System page `0121` survive.
- Browser candidate: depth `3 → 4 → 2`; System page `0121` becomes the root and the `8120` mode ancestor is lost.

The read-only stack observations use physical `0B6ED8` for depth and `0B6CE4` for the screen entries. Convert Load also shows a changed top highlight in the broader matrix. Native Mode selection is a demonstrated workaround. **BUG-165 must be repaired before full parent-context/IM1 GO**, with nested-mode restoration and existing Load/LCD/Exit behavior regressed on the resulting new binary.

Compare [original System return](../condensed/validation/bluescsi-im1-multi-gates-system-stock-return-2026-10-20.png) and [browser System return](../condensed/validation/bluescsi-im1-multi-gates-system-browser-return-2026-10-20.png).

## Volume Dump FD and remaining work

Native initialization of a private 720 KiB floppy reaches the empty four-slot Volume Dump directory. Export changes 14 bytes relative to the formatted input; all observed browser/SDS code survives. The loaded performance fixture has no selected Volume, and the exercised Save inputs create no populated dump. This is **initialization-only evidence**, not a save/load/delete roundtrip.

Early probes with wrong test counters, missed GB-6 row interiors, a wrong input-field name or a report-path error are explicitly excluded from full acceptance. The final tests use observed cursor positions and screen IDs; no production repair is inferred from a harness correction.

Next work is BUG-165, then the remaining stack/resource-lifetime and conflicting-operation contracts. Populated Volume Dump, broader media/geometry/reset/cold-checkpoint cases and physical BlueSCSI configuration/library acceptance remain separate open items. RC-100 testing stays waived under the user's accepted compatibility assumption. **IM1 remains open.**

[Validation, fixture identities, commands and limits](../condensed/validation/bluescsi-im1-multi-gates-2026-10-20.json). [Active roadmap](bluescsi-image-mount-plan.md).
