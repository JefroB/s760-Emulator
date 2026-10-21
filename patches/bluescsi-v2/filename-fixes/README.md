# BlueSCSI-v2 filename and switch-error fixes: BUG-137, BUG-145 and BUG-146

These are **BlueSCSI device-firmware source patches**. They do not modify the S-760 OS or boot ROM, build a UF2, or install firmware on an SD card/device.

| Patch | Reviewed upstream revision |
| --- | --- |
| [main.patch](main.patch) | `5e64e3b4a09088c67a2a6728385600ea67ddbe0d` |
| [release.patch](release.patch) | `4d0f96fe520688c666f34e6282a2f448f340a617` |

Source repository: [BlueSCSI/BlueSCSI-v2](https://github.com/BlueSCSI/BlueSCSI-v2). Revision names describe the pinned research inputs; they do not identify the user's currently installed build or assert that these revisions are newest.

The patches change `src/BlueSCSI_Toolbox.cpp` and `src/BlueSCSI_disk.cpp`:

- Count, list and selection apply the same filename filter before shortening the wire label to32 bytes. Long `.txt` sidecars cannot shift image indices, and a valid `.iso` is not rejected because its visible prefix happens to end in `.txt`.
- Explicit switch paths must fit in63 bytes plus NUL. The switcher rejects longer paths before stopping audio or closing the current image, and copies accepted paths with their terminator. It never silently mounts a shortened pathname.
- D8 rejects invalid indices, unreadable names and overlong paths with CHECK CONDITION/ILLEGAL REQUEST, ASC/ASCQ `24/00`. A failed backing-image open also propagates failure rather than reporting success (the shared BUG-137 handler). A genuine open failure still follows the upstream close-before-open behavior; rollback is not added.

The32-byte visible-name limit and100-image folder limit remain. For a three-character `CD<id>` directory, the switch path allows a59-byte filename including extension. This does not qualify arbitrary long names for the S-760 UI. Keep the existing32-byte/preflight profile until the installed firmware and actual library are qualified.

## Apply to a full upstream checkout

Choose the patch matching the checkout. From that checkout, review and apply it:

```powershell
git apply --check D:/S-760/patches/bluescsi-v2/filename-fixes/main.patch
git apply D:/S-760/patches/bluescsi-v2/filename-fixes/main.patch
```

Use `release.patch` for the pinned release. Do not force a patch into another revision after a failed check. Build with upstream's instructions for the exact BlueSCSI board; this repository does not provide a new device-firmware binary.

Alternatively, the guarded preparer verifies both complete input files and writes two patched files, a diff and a manifest to a **new** directory:

```powershell
python D:/S-760/scripts/patch_bluescsi_filenames.py D:/BlueSCSI-v2 D:/BlueSCSI-filename-patch
```

The source checkout stays untouched by that preparer. The output contains only the two replacement source files, not a complete buildable checkout. It accepts the recorded source-byte hashes; a checkout with converted line endings must be normalized to its pinned upstream bytes first, or use the reviewed Git patch.

## Verification and limitations

The focused tests compile and execute the actual pinned Toolbox implementation and switch functions with host filesystem/SCSI substitutes. They first reproduce the original failures, then check filtering/index/content agreement,31/32/33/59-byte names, all100 indices on IDs1/2/3/6,101-image overflow, direct63/64/65/127/128/255-byte paths, rejected-D8 state preservation and explicit errors. Three `getName` return conventions are exercised so safety does not depend on whether a truncated name reports its original length, copied length, or zero.

Both patches were applied to the two full pinned source trees and compared with independently generated replacements, normalizing Git worktree CRLF conversion. This is source/host acceptance. No RP2040/RP2350 cross-build or physical flash/acceptance is claimed.

[Results](../../../docs/project/bluescsi-filename-fixes-results-2026-10-20.md) · [Validation](../../../docs/condensed/validation/bluescsi-filename-fixes-2026-10-20.json)

The upstream source and patches to it retain **GPL-3.0-or-later**, including the upstream copyright notices (Eric Helgeson and the SCSI2SD/ZuluSCSI contributors). See the upstream source headers and [GPL version3](https://www.gnu.org/licenses/gpl-3.0.html). The project-owned host test driver follows this repository's license.

## BUG-137 verification

The D8 failure handler in these same patches also fixes BUG-137. An existing application of the filename patch already includes this code; the patch files have not changed. The preparer manifest now lists all three bug IDs.

The expanded33-test focused suite isolates invalid-index, missing-directory and forced backing-open failures. Original source reports false success in each independent reproduction. Patched source supplies CHECK CONDITION, STATUS phase, zero data length and sense5/24/00 on IDs1/2/3/6. Across three `getName` host variants,36 error cases and36 explicit retries pass552 dedicated assertions; retry selects the exact requested image and normal tray close posts unit attention. Invalid inputs retain the old backing. A real backing-open failure still closes it before returning error, so the fix does not provide rollback.

Source-defect closure and installed-device qualification are tracked separately. See the [BUG-137 results](../../../docs/project/bluescsi-switch-error-fix-results-2026-10-20.md) and [validation](../../../docs/condensed/validation/bluescsi-switch-error-fix-2026-10-20.json).
