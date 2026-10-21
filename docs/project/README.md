# Project planning and status

[Documentation home](../README.md)

Completion gates, known defects, licensing and proposed controller/storage work.

## References

- [BlueSCSI hardware-test OS and SD layout](bluescsi-hardware-test-guide.md) - Experimental606e277e... OS, GB-6 v9 retained; exact CD1/CD2/CD3/CD6 layout and controlled test order. Full IM1 remains open.

- [BlueSCSI transition ownership and recovery](bluescsi-im1-owner-and-recovery-results-2026-10-21.md) - BUG176 fixed,16 final-image native workflows,236 commands/891942 exact timer samples, CRT/LCD/IRQ ancestry and three incomplete-WRITE reset/recovery cases.1123 backend passes/3 skips.

- [BlueSCSI BUG137 switch-error closure](bluescsi-switch-error-fix-results-2026-10-20.md) - Dedicated original false-success reproductions and36 patched error/retry cases;33 focused tests and1,122 backend passes/3 skips. The existing filename patch already includes the source repair. Installed-device qualification remains separate.

- [BlueSCSI filename source fixes](bluescsi-filename-fixes-results-2026-10-20.md) - BUG145/146 source patches for both pinned revisions: consistent count/list/selection and safe path rejection.21 focused tests/10,002 host assertions;1,110 backend passes/3 skips. Device firmware build/installation remains separate.

- [BlueSCSI IM1 ROM-loader and redraw MIDI fixes](bluescsi-im1-bug-fixes-results-2026-10-20.md) - BUG174/175 fixed;10 native cases/104 snapshots, 1089 backend passes/3 skips. Exact simultaneous-stall MIDI and stereo recovery pass. Three added bytes,1419 free; BUG168 full timing proof remains open.

- [BlueSCSI IM1 Verify Medium, stalled targets and native bounds](bluescsi-im1-verify-stall-bounds-results-2026-10-20.md) - Nine accepted native cases/93 snapshots; inherited last-sector omission fixed with zero growth. Immediate dispatcher frames and parser scan bounded. Simultaneous stalled-target/MIDI byte check fails, keeping timing/recovery open.1,088 suite passes,3 skips,1 baseline-reproduced loader failure;44 focused passes.

- [BlueSCSI IM1 Format, FDD, stack and warning correction](bluescsi-im1-format-fdc-stack-results-2026-10-20.md) - Eleven native cases and91 snapshots; Format/conversion/FDD input exclusion, exact stereo Save/cold Load and synchronous native-callee stack composition pass. CRT/LCD warning fixed with zero growth; fixture FORMAT UNIT fixed.1,067 tests pass,3 skip. Timing, total stack/ownership and recovery remain open; BUG173 records the unread last sector during Verify Medium.

- [BlueSCSI IM1 timing and checkpoint recovery](bluescsi-im1-timing-recovery-results-2026-10-20.md) -13 native cases: Load/quick Initialize/Copy/Delete exclusion and partial-D8 recall repaired (BUG170);959 tests and32MiB disabled-path equivalence. Experimental parser trial passes dense MIDI plus seven regressions,111 snapshots;6580/8002,1422 free. BUG168 worst-case timing and native stack/ownership remain open.

- [BlueSCSI IM1 safety and compatibility batch](bluescsi-im1-safety-batch-results-2026-10-20.md) - Sixteen native cases: Volume Dump restore, Roland stereo32MiB IMG, current LCD paging/Save System, three reset boundaries, changed-catalog D8 checkpoint recovery, Save exclusion and mounted Delete.177 new memory snapshots pass. BUG168 exposes lost timer wraps during dense MIDI; full native safety/physical gates remain open.

- [BlueSCSI IM1 writable IMG and compatibility gates](bluescsi-im1-final-gates-results-2026-10-20.md) - Native mounted IMG Save/reselect/cold Load, Copy Yes/No, both Optimize options on fragmented media and current Akai stereo pass. BUG167 fixed;773 tests. Its partial Volume Dump result is superseded by the later matching-source restore above.

- [BlueSCSI IM1 Exit/full-CD/recovery closeout](bluescsi-im1-closeout-results-2026-10-20.md) - BUG165/166 fixed; full606.7MB CD, cold/active-D7 recall, LCD/IMG/cancellation and MIDI ownership pass.6452/8002,1550 free;769 tests. Native safety/compatibility and physical gates remain explicit.


- [BlueSCSI IM1 conversion/recall/controller/parent batch](bluescsi-im1-multi-gates-results-2026-10-20.md) - Current-build Akai conversion/stereo playback, checkpoint reselection and Mouse cancellation/Load/SDS pass. The26-cycle/13-screen matrix exposes BUG-165 nested-mode loss; Volume Dump initialization only.6487/8002,1515 free; full IM1 remains open.

- [BlueSCSI native Copy/overwrite Cancel](bluescsi-im1-native-copy-results-2026-10-20.md) - Private HD2→HD0 hierarchy copy/export/fresh exact Load/playback and separate overwrite Cancel no-write pass on19448d85... . Remaining IM1 gates open.

- [BlueSCSI native Optimize roundtrip](bluescsi-im1-optimize-roundtrip-results-2026-10-20.md) - Already-packed/no-change export and fresh exact Load/playback pass on19448d85...; no fragmented-relocation claim. Remaining IM1 gates open.

- [BlueSCSI native Delete/cold directory](bluescsi-im1-native-delete-results-2026-10-20.md) - Preconfirmation no-write and confirmed selected hierarchy deletion/cold empty native directory pass on19448d85... . Current-candidate roadmap table separates completed/remaining scope. Remaining IM1 gates open.

- [BlueSCSI current-build HDD Save/cold Load](bluescsi-im1-hdd-save-current-results-2026-10-20.md) - Browser ISO index99, native HDD quick initialization/Save/export/fresh Load119808 exact bytes/playback pass on19448d85... . RC100 testing waived by user; assumed compatibility remains explicit. Remaining IM1 gates open.

- [BlueSCSI LCD Save System and cold boot](bluescsi-im1-lcd-cold-system-results-2026-10-20.md) - Native blank-floppy format/Save System/export/fresh-process cold boot, cleared context and exact Load/playback pass. Browser/LCD/SDS/GB6v9 preserved; unchanged19448d85... . Remaining IM1 gates open.

- [BlueSCSI LCD error/cancellation recovery](bluescsi-im1-lcd-recovery-results-2026-10-20.md) - Ordinary-target refusal, bounded silent D8 failure, D7 drain and interrupted D8/no-follow-on pass, with explicit exact Load/playback recovery. Unchanged19448d85...; remaining IM1 gates open.

- [BlueSCSI LCD collections/IMG and Disk options](bluescsi-im1-lcd-collections-img-results-2026-10-20.md) - All4 collection identities/Back/reopen, target2 IMG exact Load/playback and9 Disk labels/scroll/Exit/native Load route pass on unchanged19448d85... . Remaining IM1 gates open.

- [BlueSCSI LCD paging and boundary recovery](bluescsi-im1-lcd-paging-results-2026-10-20.md) - Current candidate19448d85... passes all100 names forward/back, final-page no-op/Previous, Collections, full-name/exact Load and CRT cancellation/SDS. BUG164 fixed without growth;6487/8002,1515 free. Remaining IM1 gates open.

- [BlueSCSI image mounting plan](bluescsi-image-mount-plan.md) - Established wording successor ecdbd721... retains6452/8002 bytes,1550 free/1332 code-adjacent; timing-trial successor79124692... remains unpromoted at6580/8002. Named CRT/LCD, writable IMG, stereo and operation workflows pass. BUG168 timing, total native stack/ownership, recovery and BUG173 verification coverage keep IM1 open; physical qualification is separate.
- [BlueSCSI LCD full-name confirmation](bluescsi-im1-lcd-name-results-2026-10-19.md) - All32 ASCII filename bytes plus CD identity before Mount; shared-prefix/Back/held-key and exact Load/playback pass. Trial6487/8002,1515 free; full LCD matrix remains open.
- [BlueSCSI LCD feasibility prototype](bluescsi-im1-lcd-results-2026-10-19.md) - Shared-protocol LCD browser reaches native exact Load/playback; short-name/paging scope only. Trial6141/8002,1861 free; prior CRT baseline and remaining qualification are explicit.
- [BlueSCSI controller checkpoint](bluescsi-im1-controller-results-2026-10-19.md) - Mouse+CRT current-hash navigation/Load/playback/cancellation/SDS pass; stock LCD Disk path is separate. Dedicated LCD browser and RC100 input remain open. Firmware unchanged5408/8002.
- [BlueSCSI fresh-entry and Save System cold boot](bluescsi-im1-entry-state-results-2026-10-19.md) - BUG160 fixed; native reopen/export/cold exact Load/playback and retained SDS pass. Latest5408/8002,2594 free; external checkpoint and remaining IM1 gates open.
- [BlueSCSI contextual help and collection identity](bluescsi-im1-help-identity-results-2026-10-19.md) - Final candidate5393/8002,2609 free; all4 collection titles, cold Disk options label and exact Load/playback/SDS pass in two native workflows. Remaining IM1 gates stay open.
- [BlueSCSI library preflight](bluescsi-library-preflight.md) - Read-only SD naming/layout check;18 tests and400 upstream-code host mounts pass. Physical images and target configuration remain open.
- [BlueSCSI mount/eject protocol research](bluescsi-image-mount-protocol.md) - Exact commands, media-change behavior and the target-folder constraint in stock release/main source.
- [Earlier BlueSCSI Files/Folders research](bluescsi-files-roadmap.md) - Retained WAV-import prototype and checkpoints 1-79; direct WAV import deferred. Transport, discovery, UI and memory evidence feeds the image mounting plan.
- [Earlier BlueSCSI SD library-image proposal](bluescsi-sd-browser-plan.md) — superseded architecture; retained research reference.
- [S-760 Bug Backlog](bug-backlog.md)
- [S-760 completion roadmap](completion-roadmap.md)
- [Sony GB-6 controller option — deferred plan](gb6-controller-plan.md)
- [Licensing, project purpose and hardware use](licensing.md)
- [Roland S-760 — Hardware Fidelity Assessment & Low-Level Emulation (LLE) Roadmap](lle-roadmap-and-fidelity-assessment.md)
