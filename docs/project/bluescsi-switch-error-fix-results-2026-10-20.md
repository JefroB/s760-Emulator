# BUG-137: BlueSCSI failed-switch error propagation

**Date:** 2026-10-20. The ignored-return source defect is fixed and independently verified. The error handler was already included in the BUG-145/146 source patch; this batch adds targeted evidence and corrects BUG-137's status. The same patch files supply all three fixes.

[Patch package](../../patches/bluescsi-v2/filename-fixes/README.md) · [Validation](../condensed/validation/bluescsi-switch-error-fix-2026-10-20.json) · [Backlog](bug-backlog.md)

## Resulting behavior

The pinned original `onSetNextCD` discards `switchNextImage`'s Boolean result and reports successful D8 completion even when selection/opening fails. The repaired handler checks both the selected entry and the switch result. Rejected D8 commands produce CHECK CONDITION, STATUS phase, zero data length, and ILLEGAL REQUEST with ASC/ASCQ24/00.

| Condition | Patched behavior |
| --- | --- |
| Invalid image index | Error before switching; old image/content/media flags preserved |
| Missing collection directory | Error before switching; old image/content/media flags preserved |
| Backing-image open returns false | Error propagated; success/media-change flags are not published |
| Explicit valid retry | Correct requested image and contents selected; normal ejected/media-change state published |
| Tray close following retry | Ejected state cleared and medium-change unit attention posted |

A real backing-image open failure retains upstream's close-before-open behavior. The old image can therefore be closed when the error is reported. This repair makes that failure visible; it does not implement a backing-file rollback or permit the caller to assume the prior medium survived.

## Independent reproduction and regression

Three separate original-source runs reproduce false success for invalid index, missing directory and forced backing-open failure. These cases use short valid filenames and isolate BUG-137 from the filename/path failures.

The patched source passes **36 error cases and36 explicit retries**, across IDs1/2/3/6 and three `getName` host conventions. The dedicated cases contain **552 passing host assertions**, with raw status/sense/phase rows and before/after executable identities retained in the validation. The expanded focused suite passes **33 tests**, retaining the earlier filename/path/index regressions and source-patcher guards.

Both reviewed full BlueSCSI source revisions still pass standard Git patch checks/application and match generated replacements after normalizing Windows line endings. Patch hashes are byte-identical to the earlier BUG-145/146 package. The guarded preparer now lists137/145/146 in its manifest.

## Scope of closure

These tests execute the actual pinned upstream Toolbox/switch/tray functions against host filesystem and SCSI-state substitutes. Status and sense observations are host model state, not captured physical SCSI packets. They establish the repaired source control flow and error/retry contract.

BUG-137's earlier backlog entry combined this source defect with wider native/device recovery qualification. Its source defect is now closed, using the same scope as BUG-145/146. Installed-board build/flash/acceptance remains an IM1 deployment gate. The patch has not been compiled into a new RP2040/RP2350 firmware image or installed on the user's BlueSCSI in this batch. Existing S-760/GB-6 firmware is unchanged; full IM1 GO is not claimed.

## Final verification

Full serial backend suite: **1,122 passed, three skipped, zero failures/errors**. Focused upstream suite: **33 passed, zero skips**. No additional firmware patch is required beyond the existing filename package; its published main/release patch hashes remain unchanged. The dedicated source tests establish the BUG-137 failure/retry contract; physical firmware installation and device acceptance remain outstanding.
