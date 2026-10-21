# BlueSCSI BUG-145 and BUG-146 source fixes

**Date:** 2026-10-20. Both bugs are fixed in the supplied local BlueSCSI source patches. Applying, cross-building and installing device firmware remain separate from this source/host acceptance. The S-760 firmware and installed BlueSCSI have not changed.

[Patch package and application instructions](../../patches/bluescsi-v2/filename-fixes/README.md) · [Guarded source preparer](../../scripts/patch_bluescsi_filenames.py) · [Validation](../condensed/validation/bluescsi-filename-fixes-2026-10-20.json)

## Implemented behavior

**BUG-145:** DA/D2 count and D8/D1 index lookup now validate the same pre-display-truncation filename that D7/D0 listing validates. Only the wire label is shortened to32 bytes. This repairs both reported cases: a33-byte ignored `.txt` sidecar no longer consumes an image index, and a valid36-byte `.iso` whose first32 bytes end in `.txt` remains selectable. The combined fixture also catches the harder case where count and list lengths agree but their index identities differ.

**BUG-146:** `switchNextImage` checks the explicit input for a terminator within its64-byte buffer before doing anything to the current medium or audio. Inputs of up to63 bytes are copied including their terminator. Longer inputs return failure; a truncated prefix is never used as a filename. D8 checks the constructed path before calling the switcher and reports CHECK CONDITION/ILLEGAL REQUEST, ASC/ASCQ24/00 for rejected requests. Invalid indices and failed image opens also report errors through the same handler. A real backing-file open failure still has upstream's close-before-open behavior; rollback is not introduced.

## Supplied revisions

| Patch | Upstream revision |
| --- | --- |
| [main.patch](../../patches/bluescsi-v2/filename-fixes/main.patch) | `5e64e3b4a09088c67a2a6728385600ea67ddbe0d` |
| [release.patch](../../patches/bluescsi-v2/filename-fixes/release.patch) | `4d0f96fe520688c666f34e6282a2f448f340a617` |

Each modifies only `src/BlueSCSI_Toolbox.cpp` and `src/BlueSCSI_disk.cpp`. Standard Git check/application passes against both complete pinned source files. Applied worktree content matches the guarded preparer's replacements after normalizing Git's Windows CRLF conversion. The compiled switch body is checked against the patched function in each full source revision. Source/patch hashes are retained in the validation.

The preparer refuses unknown source hashes, repeated application and an existing output directory. It writes a new patch package without modifying its input checkout. The two revisions' Toolbox source is byte-identical; the disk source differs elsewhere, so each has its own reviewed patch.

## Verification

**21 focused tests pass**, including three deliberate original-source reproductions. The original failures are detected without executing an undefined C-string read: the host open stub checks the old64-byte stack array for a terminator before interpreting it as a string.

The compiled patched functions pass **10,002 host assertions** across15 scenario/mode combinations:

- Both long-name filter failures, including a count-equals-list/index-mismatch case, hidden files, ignored extensions and subdirectories.
- 31/32/33/59-byte names and all100 indices on each of IDs1/2/3/6, verifying displayed indices, opened filenames and file contents.101 images still report explicit overflow.
- Direct63-byte accepted paths and64/65/127/128/255-byte rejected paths; automatic image cycling still works.
- D8 rejection of60/61/63/64/100/127-byte filenames, retaining the old medium, its contents and media flags without switching or stopping audio. Invalid-index and forced-open-failure errors are checked separately within the scenario.
- Three `getName` stub return conventions: original length, copied length, or zero on truncation. These are defensive host variants, not a claim to reproduce SdFat internals.

The full serial backend suite reports **1,110 passed, three skipped, zero failures/errors**. Original sampler OS/boot-ROM hashes remain unchanged. No MAME executable or S-760 OS/GB-6 code was modified in this batch.

## Deployment scope

These fixes live in **BlueSCSI's firmware**, so an S-760 OS patch cannot install them. No RP2040/RP2350 firmware image was built or flashed. The pinned revisions do not identify the user's installed build. Actual-board build/configuration, installation and device acceptance remain open.

The32-byte S-760 visible-name/preflight profile and100-image-per-folder limit stay in place. A `CD1/`-style path can contain a59-byte filename within the63-byte switch-path bound, but this does not promise arbitrary long filenames, Unicode handling or hidden-tail UI identification. Keep catalog contents stable during selection. Existing stock-firmware restrictions remain necessary until a repaired BlueSCSI build is installed and qualified.

The D8 error handler also addresses the source-level failure-propagation concern recorded under BUG-137. That entry's separate native/device recovery qualification is not closed here. BUG-168's timing proof and the other IM1 safety/physical gates remain open; this batch is not a full IM1 GO.
