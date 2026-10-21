# BlueSCSI V2 image mount/eject command research

**Date:** 2026-10-19. **Evidence:** upstream source inspection; no commands executed against an emulator or physical BlueSCSI in this research batch. No firmware or emulator implementation changed.

BlueSCSI V2 already implements image selection and virtual media eject/load. The S-760 can issue those commands. The important constraint is how the existing command chooses an image: the Toolbox picker uses a target-specific `CD<id>` directory, not an arbitrary pathname or the shared-file working directory.

[Follow-up IM1 results](bluescsi-im1-results-2026-10-19.md) add host-source execution, native guest image switching, Disk Load/playback and regression evidence. The source-only claims below describe the earlier research batch.

## Source identities

Reviewed upstream main commit `5e64e3b4a09088c67a2a6728385600ea67ddbe0d` and official release `v2026.08.17`, commit `4d0f96fe520688c666f34e6282a2f448f340a617`. The [official download page](https://bluescsi.com/downloads) names that release on the research date. This does not identify the user's installed build.

Toolbox implementation/header, CD-ROM implementation, SCSI dispatcher and vendor dispatcher are byte-identical between these two revisions. The disk source differs elsewhere, but the six inspected functions for switching, cycling, tray state, block size and readiness are individually byte-identical. Source hashes, URLs and function comparisons are in the [validation record](../condensed/validation/bluescsi-image-mount-protocol-2026-10-19.json).

Primary source references below use main's pinned line numbers:

- [Toolbox commands and directory selection](https://github.com/BlueSCSI/BlueSCSI-v2/blob/5e64e3b4a09088c67a2a6728385600ea67ddbe0d/src/BlueSCSI_Toolbox.cpp).
- [Command constants and 100-entry maximum](https://github.com/BlueSCSI/BlueSCSI-v2/blob/5e64e3b4a09088c67a2a6728385600ea67ddbe0d/src/BlueSCSI_Toolbox.h).
- [Image switching, configuration, generic disk commands and readiness](https://github.com/BlueSCSI/BlueSCSI-v2/blob/5e64e3b4a09088c67a2a6728385600ea67ddbe0d/src/BlueSCSI_disk.cpp).
- [CD-ROM tray and START STOP UNIT implementation](https://github.com/BlueSCSI/BlueSCSI-v2/blob/5e64e3b4a09088c67a2a6728385600ea67ddbe0d/src/BlueSCSI_cdrom.cpp).
- [Official developer command documentation](https://bluescsi.com/docs/Toolbox-Developer-Docs), [user Toolbox documentation](https://bluescsi.com/docs/Toolbox), and [configuration reference](https://bluescsi.com/docs/bluescsi.ini).

## Commands to implement in the S-760 client

All bytes shown are hexadecimal. Select the intended SCSI target separately. Toolbox CDBs are ten bytes; standard commands below are six bytes unless stated otherwise. All reserved bytes are zero.

| Operation | CDB | Data/result and source behavior |
| --- | --- | --- |
| Count selectable images | `DA 00 00 00 00 00 00 00 00 00` | One-byte count from `CD<id>`. Count rejects more than 100 qualifying files. |
| List selectable images | `D7 00 00 00 00 00 00 00 00 00` | Up to 100 rows of 40 bytes from the same directory; no subdirectories. |
| Select/switch image | `D8 ii 00 00 00 00 00 00 00 00` | `ii` is the returned zero-based wire index. No data phase. Opens that file immediately, retaining the target's device class. |
| Eject virtual media | `1B 00 00 00 02 00` | Ejects and advances to the next configured image when the tray is closed. Calling eject again while open closes it in this implementation. |
| Load/close tray | `1B 00 00 00 03 00` | Makes selected media available; this command does not carry an image index or pathname. |
| Check readiness | `00 00 00 00 00 00` | TEST UNIT READY; inspect status and follow CHECK CONDITION with REQUEST SENSE. |
| Read sense | `03 00 00 00 12 00` | Requests 18 bytes; retain actual received length and original command outcome. |
| Read new capacity | `25 00 00 00 00 00 00 00 00 00` | READ CAPACITY(10), after readiness. Native media metadata must also be refreshed. |
| Allow/prevent removal | `1E 00 00 00 pp 00` | Generic disk implementation is a no-op; do not treat it as a protection/ownership mechanism. |

The list row contains index, type, 33-byte name and five-byte big-endian size. Actual source type values are directory=0 and file=1. Names are truncated to 32 characters, while `D8` resolves the index back to the full file name. Preserve returned indices; sorting display rows must not change their association. These lists follow directory iteration, not a guaranteed alphabetical sorting contract. Count before listing: list alone stops at 100, while count supplies the overflow error.

## What switching and unmounting mean

`onSetNextCD` (Toolbox lines 408–419) resolves the index, constructs `CD<id>/<full filename>` and calls `switchNextImage` immediately. Despite the command's name, it does not merely queue a future selection.

`switchNextImage` (disk lines 1470–1521) closes the old backing file, opens the new one with the target's existing device type and derived block size, then marks it ejected with automatic reinsertion enabled. For optical targets it also sets a new-media event. The next readiness check reports medium absent and closes the virtual tray for a later check. Closing can queue UNIT ATTENTION if enabled. The client must handle bounded not-ready/unit-attention transitions and read the new media again.

Do **not** automatically send eject after `D8`: eject also cycles images, and its meaning depends on the current tray state. A suitable sequence to qualify is count/list, select `D8`, then bounded readiness/sense handling, capacity/media validation and native Disk refresh. An explicit close-tray command is available if the host workflow requires it.

SCSI eject is a virtual media state change, not an SD filesystem unmount. The eject handler may open the next backing image while presenting the tray as empty. Generic fixed-disk START/STOP with byte 4 equal to 0 or 1 controls the target's started state; that is distinct from load/eject byte 4 equal to 2 or 3. Automatic reinsertion options and reset behavior must be included in qualification. CD bus reset can restart from the first configured image; selection is not guaranteed to survive reset.

## Multiple folders: established constraint

Toolbox lines 645–669 independently construct the directory `CD<target ID>` for **all three** of `D7`, `D8` and `DA`. The header defines that directory template directly. Listing and index resolution explicitly skip directories (lines 175–176 and 221–225). These commands neither traverse subfolders nor accept a path.

`D9/02` changes the shared-file effective path used by `D0`, `D2`, `D1` and file uploads. It is not consulted by the CD count/list/switch branches. Therefore browsing `/Library/ISO_B` with shared-file commands and sending its row index to `D8` would still select from `CD<id>`, potentially mounting the wrong image. This combination must not be implemented as if it were path-based mounting.

`ImgDir` is a real per-target configuration setting: normal image cycling reads it through `scsiDiskGetNextImageName` (disk lines 1299–1362). Configured `IMG0`, `IMG1`, etc. can also name images for cycling. However, the Toolbox picker does not read `ImgDir` or that configured image list. Configuring an alternate directory for cycling does not redirect `D7`/`D8`/`DA`.

**Consequences for the plan:** multiple `CD<id>` directories can serve multiple targets, each holding up to 100 images. That supports several collections within the available SCSI IDs. It does not provide an arbitrary number of collection folders selectable on one target. The reviewed SCSI command path contains no arbitrary-path mount or runtime change of the CD image directory. Folder-based collection switching on one target therefore needs a concrete additional mechanism; it is not just a missing S-760 invocation of `D9/02` followed by `D8`.

This conclusion is limited to the two reviewed stock revisions and their SCSI interface. It does not establish what a separate front-panel/beta firmware interface can expose. Configuration-file rewriting is not adopted as a workaround; live reload, recovery and write safety would need independent research.

## IMG images and device classes

The Toolbox command dispatcher is not restricted to optical targets. `D8` calls the generic image switcher, which preserves the current configured device class. The filename filter does not reject `.img` or `.iso` merely on their suffix. This gives a source-supported route to test IMG switching on a configured compatible disk/removable target, but the Toolbox directory is still named `CD<id>` even for that target.

For example, a disk target at ID 4 with compatible IMG files under `CD4` is a mechanism to qualify, not a claim of S-760 acceptance. Ordinary cycling on that same disk might use `HD4`, `RE4` or `ImgDir`, so mixing explicit selection and eject-to-next requires deliberate configuration and testing. Use an explicit block-size/device-class contract; switching does not convert an HDD image into a CD filesystem or change device class based on `.img` versus `.iso`.

## Error reporting and implementation requirements

The inspected `onSetNextCD` discards the Boolean return from `switchNextImage`, with no explicit mapping of an invalid index or open failure to CHECK CONDITION in that handler. The switcher closes the previous file before attempting the new open. A successful command status is therefore insufficient proof of a successful mount, and preserving the old image on failure cannot be assumed. This source-level risk is tracked as BUG-137; physical behavior remains to be reproduced.

The client must validate the current list/count and index, preserve raw status/sense, use bounded readiness recovery, and verify the selected media's capacity and identifying contents before handing it to native Disk Load. Do not update the emulator to invent stronger failure behavior than upstream. Include invalid index, missing/unopenable file, repeated eject, not-ready, UNIT ATTENTION, reset and successful follow-on load in the command qualification.

## Research conclusion

The existing stock image switch/eject/load commands are concrete implementation targets. Direct selection within a target's `CD<id>` folder is source-confirmed. Native S-760 command execution, refresh, image geometry and error recovery remain to be qualified. Arbitrary collection-folder selection on one target is constrained by the reviewed protocol and requires an explicit design choice before the many-folder workflow can be promised.

## Filename length and filtering qualification (2026-10-19)

The wire record carries32 name bytes plus a NUL, including the `.iso`/`.img` extension. The current S-760 screen displays those32 printable ASCII characters. A fully visible name therefore has at most28 characters before a four-character extension. Unicode glyphs/byte lengths are not qualified; the prototype substitutes `?` for bytes outside printable ASCII.

The full SD filename can be longer than the returned name: D8 re-enumerates its index and retrieves a64-byte filename buffer. However, `switchNextImage` copies the complete `CD<id>/<filename>` into a64-byte local array without forcing a terminator at the limit (BUG-146). For the reviewed `CD1/` etc. layout, a59-byte full filename including extension yields a63-byte path plus NUL. Treat this as a bounded candidate, not a universal long-name guarantee. Ordinary31/32/33/59-byte ISO names mount in the pinned upstream-code host harness; source-backed/native-fixture agreement is distinct from physical acceptance.

BUG-145 is a separate enumerator defect: DA and D8 truncate before filtering; D7 filters before truncating. The14-assertion host harness reproduces count2/list1 and a raw index0 selecting a long `.txt` instead of displayed `Z.iso`. It also reproduces count0/list1 for a valid36-byte ISO whose32-byte prefix ends in `.txt`. The image client must reject mismatched or ambiguous catalogs, preserve indices and never reconstruct a mount path from displayed text. Count/length equality alone does not prove complete filtering equivalence if opposite differences cancel. Keep leaves restricted to intended images and qualify naming rules. Names sharing their first32 bytes cannot be distinguished by the current text alone; D7 has no full-name field to scroll beyond32 bytes.

For the first supported profile, use fully distinguishable printable ASCII names within32 bytes including extension. Longer names up to59 bytes remain a qualified-case extension pending collision/filter policy, SD preflight and hardware checks. Do not impose a32-byte SD filesystem limit or promise64/255-character names from this protocol. [Boundary evidence](../condensed/validation/bluescsi-filename-boundaries-2026-10-19.json).


## First-profile preflight implementation

The [read-only library preflight](bluescsi-library-preflight.md) enforces visible32-byte names and homogeneous image leaves, rejects ambiguous/unsafe entries and reports100-entry and sector-alignment failures. Eighteen tests plus810 pinned-upstream host assertions establish400 displayed-name/index mount matches for the supported profile. Numeric prefixes after the first underscore can override target block size through getBlockSize; preflight rejects them. This is a host-side restriction, not a firmware filter repair or physical acceptance.
