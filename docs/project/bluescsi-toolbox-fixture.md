# Native Toolbox qualification fixture

2026-10-19. This opt-in, read-only emulator fixture supports ten-byte D0/D1/D2/D9 commands. It is an intermediate BS1/BS2 test facility, not a complete BlueSCSI target or released importer. BS1 remains **REVISE**.

The separate [IM1 image-switch fixture](bluescsi-im1-results-2026-10-19.md#fixture-contract-and-remaining-work) uses `S760_TOOLBOX_IMAGE_ROOT` for D7/DA/D8 and selected media. It has its own scope and tests; do not combine the two fixture flags in these qualifications.

Set `S760_TOOLBOX_TEST_ROOT` to a private fixture directory and `S760_TOOLBOX_TEST_TARGET` to one existing image target ID,0 through 6. Both are required. Otherwise the fixture is disabled. Ordinary SCSI commands continue to use the attached image. There is no host file-writing command.

## Directory and capability profile

The configured host root represents virtual `/Files`. D0 returns 40-byte rows: index, type (0 directory/1 file),33-byte terminated name and five-byte big-endian size. Names are truncated to 32 bytes. D2 returns a one-byte count. Host entries are sorted by name; dot names, symlinks and non-file/non-directory entries are excluded. Both commands reject more than 100 entries. This is deterministic fixture behavior, not FAT enumeration order or upstream D0 truncation behavior.

D9/00 reports the configured fixed-disk target only. D9/01 reports API0 and capability bit 4 (SET_WORKING_DIR), with no multi-block or send capability. D9/02 receives at most 64 path bytes through DATA OUT. It selects an existing directory beneath virtual `/Files`; parent traversal, invalid components and symlink components are rejected. It creates no directories. A NUL-first path resets to `/Files`; zero transfer length does nothing. A failed path preserves the previous directory and closes an open file snapshot. D9/03 returns the current path, zero-padded to the allocation length (zero means 256 bytes).

These choices follow the inspected [upstream source](https://raw.githubusercontent.com/BlueSCSI/BlueSCSI-v2/main/src/BlueSCSI_Toolbox.cpp) where stated, but are not pinned to the user's firmware. The fixture's virtual root, immediate missing-path rejection, sorted entries and stricter overflow handling are deliberate limits. Opt-in INQUIRY returns the extended BlueSCSI identity and API byte; MODE SENSE(6), DBD=8, current page 31 returns the vendor signature. Discovery behavior is pinned to upstream commit 5e64e3b4a09088c67a2a6728385600ea67ddbe0d, not the installed physical firmware. D9/00 still advertises fixed-disk type even for the target-6 CD test backing; device-type parity remains open. Reset/checkpoint load resets the directory and closes transient snapshots; Toolbox session recall itself remains unqualified.

## File profile

D1 block 0 resolves the wire index from the current directory and opens an immutable snapshot, replacing any previous file. Nonzero blocks use that open snapshot. Each command supports one 4KiB block (CDB byte 6 is 0 or 1), returns the actual remaining length and closes at EOF. Empty files return GOOD without payload. Missing files, invalid fields, directories, closed handles and offset overflow return CHECK CONDITION. Files above 32MiB are outside this fixture. Directory indices can change if host contents change; no stable catalog is promised between listing and opening. Physical error/handle parity is open.

## Qualified guest path and limits

The private diagnostic scans target IDs 0 through 6 using extended INQUIRY and the vendor mode page, checks capability bit 4, selects `/Files/Keys`, and drains directory lists while retaining one 40-byte row. A 100-entry mixed directory (92 directories and eight files) passes with wire indices 92 through 99. File lengths, PCM offsets and block construction carry 32-bit values; separate 64KiB boundary and block-256 cases pass. Automatic selection of at most eight files and the fixed path remain diagnostic constraints, not a browser.

Eight mono/stereo PCM16 WAVs produce twelve public samples with exact PCM, padding, all 512 descriptors and full 32MiB wave RAM checked. The scoped constructor requires fresh fixed slots, cursor at most 12, 2 through 4,594 frames per channel and one allocation block per channel. The tested profile is 44.1kHz, root 60, OneShot. Generated names and candidate endpoints are not a qualified general import policy. Native mono/stereo preview audition and silent release pass; permanent Partial/Patch assignment and Save/cold Load remain open.

Ordinary Exit cancellation drains the command, restores allocation cursor/mirrors and clears staging; same-session retry succeeds. Occupied-slot re-entry rejects without mutation. Seven empty/negative profiles preserve public descriptors, allocation state and wave RAM. Relocated native menu dispatch invokes the integrated client through window 2. Synthetic SPC discovery, directory and file tests remain distinct from firmware acceptance. Final backend validation passes 745 tests and ordinary boot/load/playback; the disabled fixture matches all 33,554,432 reference wave bytes.

Integrated code is 4,507 bytes. The conservative partial census with retained helpers is 6,009 bytes, 375 over the proposed 5,634-byte ceiling. Possible helper duplication remains to be reconciled; this is neither a proven minimum nor a complete production footprint. The decoded extension stack is 268 bytes including the hook return, excluding native ISR/caller depth. General allocation and competing-SysEx ownership, browser UI, recovery, persistence, physical qualification and complete code/RAM/stack fit remain open. The reservation flag is not a complete ownership gate.

[Identity-bound results and reproduction sources](../condensed/validation/bluescsi-integrated-client-2026-10-19.json).

## Full-size image fixture qualification (2026-10-20)

The opt-in image-switch fixture now permits aligned images up to1GiB, replacing its64MiB test ceiling (BUG-166). The606709760-byte JMD CD mounts through the native browser and loads79 exact sample allocations. This is a bounded host allocation policy, not an upstream BlueSCSI or sampler limit. Six synthetic fixture tests,769 backend tests and fixture-disabled native acceptance pass. [Results](bluescsi-im1-closeout-results-2026-10-20.md).


## One-shot PIO D7 stall diagnostic (2026-10-20)

`S760_TOOLBOX_IMAGE_STALL_AFTER` accepts decimal0..3999 only with an enabled image root. At the selected D7 byte count, the opt-in profile holds BSY/data-in and withholds REQ (`PSNS=09`). Bus release, SPC controller reset or SCSI bus reset clears the active fault; it fires once per process, so an explicit retry can complete. Disabled/invalid configuration leaves normal behavior unchanged. Host-timeline fault state is not checkpointed; this is not a DMA or physical BlueSCSI timing model.

Nine synthetic tests cover thresholds0/1/3999 and all three release mechanisms on target1. Four native fault/retry cases pass. The actual simultaneous-MIDI case fails exact byte preservation and is excluded from acceptance; before/after-stall MIDI tests do not replace it. Both default-disabled builds preserve all32MiB of wave memory and ordinary boot/input/playback/release. See [results](bluescsi-im1-verify-stall-bounds-results-2026-10-20.md).
