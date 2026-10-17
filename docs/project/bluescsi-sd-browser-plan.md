# BlueSCSI V2 SD browser for the Roland S-760

**Date:** 2026-10-13
**Status:** researched implementation proposal; no firmware implementation or hardware test performed.
**User decision:** pursue an SD library browser instead of larger Roland disk images. This request authorizes research and this document, not firmware flashing or OS patching.

## Intended experience

Add an **SD Library** entry to the S-760 Disk interface. It opens a folder browser on the BlueSCSI SD card. Selecting a Roland library image opens that image's volumes/performances/patches through the existing load interface. Selecting content loads it into the sampler's normal memory and synthesis structures.

The library can occupy much more SD space than a single Roland disk, while each image retains its original filesystem. This does **not** increase sample RAM, create a larger Roland filesystem, or make arbitrary file formats playable. First release should be read-only library access; existing ordinary SCSI disks remain available as save destinations.

A later WAV importer is a separate feature. It must decode WAV and create valid sample/partial/patch records; a directory listing alone cannot do that.

## Feasibility conclusion

**Promising, but a substantial native OS extension.** Stock BlueSCSI V2 provides directory and file-transfer operations. The S-760 needs the browser, a Toolbox command client, and a bridge between file reads and its existing Roland loader. A boot-ROM replacement is not an inherent protocol requirement; whether an OS-disk-only implementation fits cleanly remains unproved.

The major unknown is the guest loader contract: identify its block-read call sites, destination memory, bank selection, completion/error behavior, and any DMA path that bypasses ordinary CPU buffers. Do not treat this as a UI-only change or promise a small byte patch.

## Firmware and configuration

Recommended baseline at research date: **BlueSCSI V2 v2026.08.17**, stable release, Universal build:

`BlueSCSI_V2_Universal_2026-08-17_4d0f96f.uf2`

The directory-selection commands needed for a nested browser were introduced in **v2026.04.27**. That is the minimum release verified here for this design, not the earliest firmware supporting flat shared-folder transfers. Directory APIs were introduced as preview features; pin implementation/testing to a known release and detect capabilities at runtime.

Use the normal V2 Universal firmware, not Ultra or an unrelated hardware build. Neither Wi-Fi nor the SPDIF audio build is required. The installed version is currently unknown; inspect the SD `log.txt` or extended INQUIRY response before planning an update. Updating BlueSCSI alone will not add an S-760 browser.

Suggested additive configuration, preserving all existing per-device settings:

```ini
[SCSI]
EnableToolbox = Yes
ToolBoxSharedDir = /S760
```

Toolbox is normally enabled already. Keep normal FAT32/exFAT file-backed operation and existing emulated SCSI targets; do not use RAW mode for this feature. The sampler remains the SCSI initiator and BlueSCSI remains a target. Keep the S-760's ID separate from emulated targets.

Suggested library layout:

```text
/S760/
    Drums/
        Acoustic.img
        Electronic.img
    Keys/
        Pianos.img
        Electric.img
    Synth/
        Pads.img
```

These are library files opened by Toolbox, not automatically mounted SCSI targets. A file extension is not proof of a valid Roland image; inspect its structure before offering Load.

Firmware update reference: [official update instructions](https://bluescsi.com/docs/Updating-Firmware). USB UF2 is the baseline method when bringing an older device forward; the SD ZIP update mechanism requires a sufficiently recent installed bootloader/firmware. No update was performed during this study.

## Confirmed BlueSCSI interface

The released source was inspected at tag **v2026.08.17**, not just the moving main branch. All commands below use **10-byte CDBs**, including the vendor opcodes that a generic SCSI command-length decoder might otherwise classify as six-byte commands.

| Operation | Command | Host responsibility |
| --- | --- | --- |
| Identify target | INQUIRY `0x12`; vendor MODE SENSE page `0x31` | Validate actual BlueSCSI identity, not only a user-configured disk vendor string |
| Get capabilities | `D9 01 00 00 00 00 00 00 08 00` | Require working-directory support for this browser; handle unsupported commands |
| Set folder | `0xD9`, subcommand2 | DATA OUT carries an absolute path including NUL; CDB byte8 is its byte length |
| Get folder | `0xD9`, subcommand3 | Optional confirmation; explicitly request a bounded response |
| Count/list | `0xD2` / `0xD0` | Receive bounded list, retain original firmware indices |
| Read file | `0xD1` | Select index and 4KB offset; open by first reading offset0 |

Capability bits are large reads=`0x01`, large sends=`0x02`, and working-directory selection=`0x04`. The client should accept API0 with the required capability rather than assuming a missing capability query is sufficient for nested browsing. If unsupported, show a clear firmware requirement or offer a deliberately limited flat-folder mode.

### Important source-level details

The source and wiki have inconsistencies. Use the pinned source plus wire tests as the executable contract:

- A list entry is40 bytes. The released implementation emits **type0 for a directory, type1 for a file**, opposite the wiki's explanatory comment at research time. Test both with a known folder/file pair.
- `SET_WORKING_DIR` with a zero DATA OUT length does nothing. Send a one-byte NUL path to restore the configured shared directory. Always include NUL in the transmitted path length; do not copy the wiki's ambiguous root-path example literally.
- Names returned in listings are limited to32 characters. Use short library file/folder names, especially for folder navigation: truncated names cannot reliably reconstruct longer full paths.
- Listings have a100-entry cap and no observed pagination mechanism. Initially require at most100 visible entries per directory, including folders. Display overflow instead of silently making a larger directory seem complete.
- Directory paths passed by this API are at most64 bytes. Budget for NUL and enforce a conservative63-character absolute path limit.
- The working-directory override and open file handle are shared device state. Serialize operations; do not interleave two clients/targets or change folders during an active image load.
- GET_FILE uses a 32-bit file size and 32-bit computed byte offset in the inspected release. Treat individual files as smaller than4GB even though directory entries advertise wider sizes. Ordinary Roland-sized images fit this restriction.
- Opening/counting/listing a nonexistent shared folder can cause BlueSCSI to create it. A nominally read-only client must use prepared existing directories and should not promise that every discovery operation is storage-neutral.

Source references: [released Toolbox implementation](https://github.com/BlueSCSI/BlueSCSI-v2/blob/v2026.08.17/src/BlueSCSI_Toolbox.cpp), [released constants](https://github.com/BlueSCSI/BlueSCSI-v2/blob/v2026.08.17/src/BlueSCSI_Toolbox.h). These source observations correct earlier assumptions; they do not establish S-760 hardware compatibility.

## Proposed software architecture

```text
S-760 Disk UI
    -> SD folder browser
    -> selected library file (read-only virtual source)
    -> existing Roland catalog / performance / patch loader
    -> virtual block-read adapter
    -> bounded 4KB cache + BlueSCSI Toolbox client
    -> native SCSI transport -> BlueSCSI -> SD filesystem
```

### 1. Discovery and command client

Reuse the native SPC transport rather than inventing register behavior. The wrapper needs target ID, a10-byte CDB, transfer direction, destination/source buffer, expected byte count, timeout/cancel handling, status and REQUEST SENSE.

Sequence: identify BlueSCSI; query capabilities; select an existing library directory; list entries; then open/read one small fixture. Do not attempt loader integration before byte-exact transfers work on hardware.

Use4KB read requests initially, even when larger transfers are supported. They keep memory requirements predictable and simplify final partial transfers. Directory listings require up to4,000 bytes for100 entries; allocate a real bounded buffer and respect actual returned length.

### 2. Browser state

Maintain current absolute path, displayed entries with original BlueSCSI indices, selection/scroll position, selected target, active-file identity and error state. Sorting the displayed list must not change the index sent to BlueSCSI. Refresh invalidates indices and caches; do not retain an index across directory changes or SD content changes.

Folder entry changes the working directory and refreshes; Parent reconstructs a bounded absolute path. Restrict navigation to the configured library subtree for the first product interface. Leave root firmware/configuration files out of the ordinary Load flow. Back/Exit cancels work and restores usable native disk controls.

The normal CRT disk list is a UI reuse candidate, not an identified patch point. Account for panel navigation and actual guest frames; do not substitute a host-side React browser and claim native sampler support.

### 3. Library-image adapter — preferred first loading backend

Represent a selected ordinary-sized Roland image as an internal read-only virtual disk source. Do **not** switch the BlueSCSI target image or copy the whole library image into sampler RAM. Keep ordinary target media identity separate from this virtual source.

For a requested image byte range `[offset, offset+length)`:

1. Validate range against the selected file size using overflow-safe arithmetic.
2. Compute `page = offset // 4096`, `within = offset % 4096`.
3. Fetch/cache page with GET_FILE; copy the requested subrange.
4. Continue across page boundaries until the caller's requested bytes are supplied.

Translate512-byte hard-disk or2048-byte CD logical blocks into byte ranges before this step. Do not assume one Toolbox read equals one Roland cluster: the known9,216-byte clusters cross4KB pages.

GET_FILE opens the selected index only on offset0. On opening an image, read/cache page0 first even if the loader's first requested page is elsewhere. Subsequent requests can seek within that open file in the inspected implementation. EOF closes the handle; reset/reopen from0 before further reads if EOF, cancellation or another transfer invalidated it. The exact abort/reopen lifecycle must be wire-tested; there is no assumed general close-file command.

Cache tags must include target, directory/file identity, page and a selection generation. Start with a single4KB page and measure before adding a second. Reserve scratch RAM through an audited allocator/banked-memory contract, never by guessing unused addresses. Preserve the loader's destination-bank contract and wave-RAM transfer path; PCM may require staging through an existing copy/DMA routine rather than returning an ordinary pointer.

The adapter is the largest reverse-engineering task. Existing capacity/catalog reads may also need to see virtual source metadata. Every save/format/delete path must reject this read-only source, not accidentally target its backing SD file or the ordinary SCSI disk.

### 4. Format scope

First support validated Roland S-7xx library images using the existing catalog loader. Preserve the per-image filesystem constraints. Large total SD capacity comes from many files/folders, not changing16-bit allocation links.

Do not use the repository's synthetic disk generators as ground truth for hard-disk structures. The current `roms/SCSI/HD00_512.img` is a small generated fixture, not sufficient evidence of a real Roland-formatted library. Use a known authentic image and compare existing native loading against virtual loading.

Later consider WAV import with a narrowly specified PCM subset, explicit sample-rate/root-key handling and correct partial/patch construction. AKAI or other formats would need separate validation; their extensions alone are not sufficient.

## S-760 reverse-engineering findings and next tracing targets

Read-only disassembly identified promising transport code in original OS2.24:

- File `0x16992` begins a routine that saves data selector `0x010A`, sets it to`0x02CC`, copies a caller-provided command descriptor into CPU buffer `0x5F12`, and retains its byte count inR42. File `0x169FA` reloads the command buffer pointer; the send loop near `0x16A17..0x16A31` transmits bytes and decrementsR42. This suggests a supplied-length command sender, not an inherent six-byte restriction. The full call/return and descriptor contract still needs tracing.
- A nearby receive path at file `0x16A47` onward programs SPC transfer registers `E418/E41A/E41C`, reads data through`E414`, stores throughRW48, and decrements a wider remaining count usingRWBC/RWBE. This is a lead for bounded DATA IN, not a complete callable ABI.
- Data-window addressing matters: `0x5F12` is a CPU address under a selected data bank. Preserve selector save/restore; never treat it as an absolute image offset or a permanently allocated flat-RAM address.
- The boot ROM also contains SPC routines, but this investigation does not establish that they must be patched. Trace whether the OS wrapper delegates any required transport or loader step to ROM services.

Use file offsets as the stable leads above. The same physical code can be addressed through different CPU windows/selectors; actual bank:PC entry points and caller state must be confirmed from a native trace before hooking anything.

The known device window is SCSI atCPU`E400` under the native peripheral data mapping. Separate code/data selectors at`0100..010E` and their restoration are essential, especially after the prior GB-6 experiment demonstrated the danger of assuming fetch and data banks match.

Unresolved contracts to record before implementation: transport entry points, command descriptor layout, buffer ownership/capacity, interrupt expectations, actual CDB length handling, DMA/completion behavior, timeout/cancel service, loader read ABI, and permitted scratch/code placement. CPU timing and IRQ behavior cannot be inferred solely from linear disassembly.

## Emulator preparation

**User requirement: emulator and physical hardware must provide the same capability for this feature.** Emulator support is a prerequisite for meaningful browser/loader testing, not an optional convenience after hardware implementation. Run the same patched OS disk against the same library fixture set on both. Pin the emulated BlueSCSI profile to the firmware installed on the physical V2 and explicitly record that version and any configuration differences. Unknown behavior must remain an open parity question, not be replaced with invented success responses.

Required parity includes command discovery, capability bits, exact10-byte vendor CDB framing, INQUIRY/vendor-page identification, DATA IN/OUT lengths and phases, directory type encoding, original listing indices, name/path/listing limits, shared working-directory/open-file state, reset/EOF/cancel behavior, short reads, sense/status errors, and file-write behavior if advertised or used. An emulator profile must not advertise capabilities it has not implemented. Preserve ordinary disk behavior alongside Toolbox access; changes to CDB length handling must be scoped to the appropriate target/vendor profile.

The emulated target should operate on a real fixture-backed SD directory tree and image files. The guest must discover, browse and load those bytes through its native SPC/SCSI transport. A mocked UI, host-injected guest events/catalog records, forced firmware state, or direct host load into sampler memory cannot qualify this feature. The emulator model may be implemented independently, but its observable behavior must be checked against the pinned released source and physical command traces; reusing BlueSCSI code where practical should be evaluated rather than assumed.

Use paired tests: capture commands, lengths, statuses, sense data, listings and payload hashes on hardware; replay the same requests in the emulator; compare the results. Then compare native guest catalog/PCM outcomes and visible browser behavior. A standalone protocol test is necessary but insufficient: the actual OS load path must pass. Timing need not be claimed cycle-identical before measured, but timeouts, phase sequencing, cancellation, UI/MIDI servicing and error recovery must be tested on both. Report functional parity separately from timing fidelity.

Current `mame-source/src/mame/roland/s760.cpp` command assembly around lines3838–3840 gives10-byte length only to`0x20..0x3F`,12 bytes to`0xA0..0xBF`, otherwise6. Therefore Toolbox`0xD0..0xDA` would currently dispatch after6 bytes. These are not implemented targets today; future testing must explicitly add the correct vendor lengths and a Toolbox target model.

The target model should expose a bounded fixture directory, source-accurate type encoding,100-entry behavior,64-byte directory protocol, short final reads, one shared open handle, EOF/reopen behavior, capability errors and REQUEST SENSE responses. Do not inject catalog entries directly into guest RAM or bypass the native SCSI command path to make the UI appear functional.

Existing emulator support for READ/WRITE(6)/(10) and READ CAPACITY is host-side implementation evidence, not proof that the guest loader already supports arbitrary Toolbox commands. Preserve ordinary-target regressions when adding this future feature. SCSI snapshots/session recall would also need the added target state or an explicit unsupported-state policy.

## Staged implementation and acceptance

| Stage | Work | Required evidence |
| --- | --- | --- |
| 0 — trace | Map transport/loader ABI, UI entry and safe code/RAM placement | Bank-aware native trace; annotated calls and buffer ownership |
| 0a — emulator/hardware parity gate | Implement pinned V2 target capabilities and native SCSI framing; validate paired fixtures | Matching command/response/payload traces and ordinary-target regressions before browser acceptance |
| 1 — transport | Capability query, directory selection, file list, small read | Physical V2 returns expected entries and fixture bytes; error/timeout exits work |
| 2 — browser | Guest-native folders, parent/back, scrolling and refresh | Mouse/GB-6 and panel operation; path/name/entry limits handled |
| 3 — image read source | Page cache and virtual capacity/catalog reads | Boundary/EOF comparisons against authentic image; no whole-image RAM dependency |
| 4 — native load | Existing performance/patch/sample loader uses source | Loaded records and PCM match ordinary-image load; playback and cancellation work |
| 5 — qualify | Larger library, repeated loads, ordinary disk regressions | Multiple folders/images, stable memory, idle/playback responsiveness, no source writes |

Boundary cases include0/1/100/>100 entries, both entry types, long names, maximum paths, empty/short files, reads spanning4KB pages and9KB clusters, EOF reopening, media change, missing target, unsupported API, bus reset and cancellation. A browser-only demo is not acceptance of playable loading.

Measure real listing latency and sustained load throughput. Do not promise BlueSCSI's advertised maximum speed on the S-760. All transfers must yield or finish within the firmware's service constraints; avoid unbounded polling that stalls UI, MIDI or audio servicing.

First source-access prototype should not send file-write commands`D3/D4/D5`. BlueSCSI count/list can create a nonexistent directory, so prepare known directories and include a before/after SD content check. Adding SD saves/export later needs its own ownership, failure and recovery design.

## Scope, recovery and remaining decisions

Implement future experiments on copies of OS2.24; retain the original system disk, successful GB-6 disk and boot EPROM. Identify the final GB-6 baseline by hash before merging its decoder with a browser extension. Keep SCSI images and SD library backed up before eventual hardware trials.

Original root `S760224.IMG`: SHA256 `3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd`. Boot v1.11: SHA256 `ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6`. Both were read, not changed, during this study.

Decisions still needed when implementation is authorized: supported first image variant, exact guest UI entry, fallback for old firmware, memory budget, image-open/cancel ownership, and where additional banked code can live. If hooking the native loader proves excessively invasive, a constrained file importer is a fallback; increasing Roland disk size is not the selected path.

No timeline is asserted before stage0. Stock BlueSCSI appears sufficient for the first browser/reader; only later requirements such as more than100 entries per directory, full long-name retrieval or wider file offsets might justify an upstream/custom BlueSCSI change.

## Sources

- [BlueSCSI V2 v2026.08.17 release](https://github.com/BlueSCSI/BlueSCSI-v2/releases/tag/v2026.08.17).
- [v2026.04.27 directory API introduction](https://github.com/BlueSCSI/BlueSCSI-v2/releases/tag/v2026.04.27).
- [Toolbox developer protocol](https://bluescsi.com/docs/Toolbox-Developer-Docs); source discrepancies are identified above.
- [Released Toolbox implementation](https://github.com/BlueSCSI/BlueSCSI-v2/blob/v2026.08.17/src/BlueSCSI_Toolbox.cpp) and [constants](https://github.com/BlueSCSI/BlueSCSI-v2/blob/v2026.08.17/src/BlueSCSI_Toolbox.h).
- [BlueSCSI configuration](https://bluescsi.com/docs/bluescsi.ini) and [firmware update instructions](https://bluescsi.com/docs/Updating-Firmware).
- Independent Roland format reader: [data types](https://github.com/transverberate/smpl_extract/blob/main/smpl_extract/roland/s7xx/data_types.py), [allocation table](https://github.com/transverberate/smpl_extract/blob/main/smpl_extract/roland/s7xx/fat.py). Reader behavior is corroborating evidence, not an authoritative complete firmware specification.
- Local original firmware and disassembler: `S760224.IMG`, `roms/BOOT/Roland_S-760_v1.11.BIN`, `.agents/scripts/mcs96_disasm.py`; native memory map in `docs/condensed/01-hardware-and-memory-map.md`; emulator transport in `mame-source/src/mame/roland/s760.cpp`. Existing screen research in `docs/hardware/screens/01-disk-screens.md` is a UI lead, not verified hook metadata.

This document is the deliverable of the current research. No OS patch, emulator change, BlueSCSI configuration edit, firmware update or device operation was performed.
