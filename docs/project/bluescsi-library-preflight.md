# BlueSCSI image-library preflight

Run the read-only checker before using an SD library with the IM1 browser:

```powershell
python scripts/bluescsi_image_preflight.py E:\ --self-id 7
```

Replace `E:\` with the actual SD root and `7` with the sampler's actual SCSI ID. The checker prints findings and exits0 for a passing layout,1 for a failed layout, or2 for invalid command syntax. It never renames, moves or writes image files. Add `--json` for a report on stdout.

The default profile matches the current firmware candidate:

| Directory at SD root | Collection | Sector bytes |
| --- | --- | --- |
| CD1 | ISO A | 2048 |
| CD2 | IMG | 512 |
| CD3 | ISO B | 2048 |
| CD6 | ISO C | 2048 |

All target IDs must differ from the sampler's self ID. An explicit subset can be checked with repeated options, for example `--collection 1:iso --collection 2:img`. Custom target maps only change what the host checker inspects; they do not reconfigure BlueSCSI or alter the firmware's four collection buttons. Actual target configuration remains a hardware gate.

Each leaf must contain at most100 total entries, all regular images of its assigned type. Empty leaves produce a warning and pass. Nested folders, sidecars, links and junctions fail this conservative profile. The stock CD picker skips directories and filters some files; the total-entry policy deliberately avoids relying on those exclusions. Files elsewhere in the SD root, including existing boot/save images and configuration, are outside this scan.

Names must fit32 printable ASCII bytes including `.iso` or `.img`, start with a letter/digit, use portable FAT characters and remain distinct case-insensitively within each collection. This shows the entire name and avoids the reviewed count/list/index filter disagreement (BUG-145). The checker separately reports first32-byte collisions and paths reaching64 bytes (BUG-146), so long-name failures have actionable explanations. These are first-profile restrictions, not claims about the SD filesystem's maximum name length. Qualified longer-name experiments remain historical evidence.

Avoid a first underscore followed by a number from8 through65536. The reviewed BlueSCSI `getBlockSize` treats that numeric prefix as a block-size override, even inside a collection filename: `Disc_512.iso` changes a2048-byte target to512. A name such as `Disc_Collection.iso` retains the configured default. The checker rejects numeric overrides even if they equal the expected size, keeping geometry in the target configuration.

Images must be nonempty and a multiple of the profile's sector size. Passing these checks does **not** verify the Roland filesystem, image contents, write protection, target device class, firmware version, physical configuration or S-760 loading. It also cannot prevent later SD changes or prove that firmware will refuse a library that bypasses preflight. Recheck after changing names or library contents; do not modify a collection during a browser session.

## Acceptance evidence

Eighteen automated tests cover valid32-byte names,100/101 entries, empty leaves, both BUG-145 filename examples, prefix/path collisions, unsupported/hidden names, FAT portability, numeric overrides, geometry alignment, self-ID conflicts, missing/unreadable directories, link refusal and CLI reports. A generated400-image library passes preflight. Execution of the pinned upstream Toolbox/switch functions passes810 assertions, mounting all100 indices on each of IDs1/2/3/6 with exact displayed-name agreement. Fixture content hashes are unchanged after checking and mounting.

This is host execution with filesystem/SCSI stubs, not physical parity or a new native firmware qualification. No firmware bytes changed; at preflight acceptance the browser used the owned-footer candidate SHA256 `18421aaa97280374c57eac337b31b2d2f0f5e79558401ffb730b0aba25a0f28a`, with4982/8002 allocated bytes and3020 free.

[Durable validation](../condensed/validation/bluescsi-im1-preflight-2026-10-19.json) records source identities, raw upstream assertions, fixture hashes and test scope. [IM1 roadmap](bluescsi-image-mount-plan.md).


The newer experimental LCD [full-name confirmation](bluescsi-im1-lcd-name-results-2026-10-19.md) shows the supported32-byte ASCII name in two16-byte lines before explicit mounting, including shared21-byte list prefixes. The list itself remains21 bytes wide. This resolves that scoped display ambiguity; complete LCD/controller and hardware acceptance remain open.

## Source-repair availability (2026-10-20)

BUG145/146 now have [reviewed BlueSCSI source patches](bluescsi-filename-fixes-results-2026-10-20.md), with consistent enumeration and safe explicit path rejection. The checker's existing32-byte/name/path restrictions remain: the patches have not been installed or physically qualified on the user's BlueSCSI, and visible names remain32 bytes. Do not relax SD policy based solely on host test acceptance.
