# BlueSCSI BS1 workaround evaluation

2026-10-19. **The original memory-based objection is resolved at component level;
BS1 remains REVISE until the complete design is linked and qualified.**
No firmware was released; the original OS and boot ROM remain unchanged.
The native emulator was rebuilt for the opt-in Toolbox fixture. Mono/stereo and 100 total directory entries remain requirements.

## Measured results

| Checkpoint | Result | Qualification boundary |
| --- | --- | --- |
| 42: bounded receive windows | Eight native cases drain full 4 KiB responses while retaining at most 1 KiB; selected offsets 0, 1024, 2048, 3072 and 3960 match, including the 136-byte final window. Unsupported command, sense and absent target return expected outcomes. | Standard READ(10), not Toolbox; all 4 KiB sentinel bytes checked in the first experiment. |
| 43: actual smaller receive allocation | The same eight cases pass after relocation to a guarded 1 KiB receive buffer. Subsequent HDD load/playback preserves 119,808 PCM bytes and the complete exported image. | Diagnostic resource map, not the final full-client layout. |
| 44: branch compaction | Stereo diagnostic shrinks 1,882 to 1,792 bytes; cancellation after left-channel completion and successful retry pass under note/controller input. All existing PCM, public descriptors and 239,616 pair PCM bytes match. | Only branch forms changed; diagnostic generators/delays remain in the harness. Full production compaction is still pending. |
| 45: in-place stereo split | Input is at most 1,024 bytes. Left samples compact into the consumed input prefix; right samples occupy a separate 512-byte region. 1/511/512/513-frame cases pass both channels and all eight 8 KiB destination/sentinel regions. | 1,536-byte working set; isolated DMA diagnostic, not concurrent transport/publication. |
| 46: guest RIFF validation | Actual guest execution matches the host reference on 88 cases: mono/stereo, eight rates, unsupported formats, malformed structure, every truncation of a small WAV, reversed fmt/data order and odd padding. | Bounded immutable-RAM read provider; no sparse 32-bit or transport-failure acceptance claim. The validator is no longer static-only. |
| 47: file and directory scheduling | Host reference passes 128 WAV cases, including header reads crossing 4 KiB boundaries and repeated access after EOF; status, short and excess responses reject. Twelve pages preserve all original indices of a 100-entry listing with at most 360 bytes per page. | Model only; no guest directory UI or physical Toolbox acceptance. |
| 48: parser plus real SCSI | A 2,126-byte diagnostic links the compact guest validator, bounded receive-window transport and READ(10) adapter. Ten valid/invalid cases return expected metadata/status from private HDD fixtures. | Real guest PIO reads, but READ(10)'s sector addressing is not GET_FILE's block/open-file contract. No full importer claim. |

Every native result includes binary/source identities and ordinary-input execution.
[Validation and reproduction sources](../condensed/validation/bluescsi-workarounds-2026-10-19.json).

## Selected design to integrate

Use one 1,536-byte workspace for paged listing or import. Import uses a 1,024-byte
receive/input region and 512-byte right-channel output region. Store the selected
original entry and path separately; invalidate the visible page before reuse and
refetch it on return. No whole-directory cache is required, but the 100-entry
protocol limit remains unchanged. Frame carry and arbitrary metadata must still
be integrated with the parser and writer.

The protocol returns 4 KiB file blocks. Retain only the requested window while
draining the entire response, then reread as needed. Upstream code opens on block
zero and closes at EOF, so a nonzero read after EOF needs reopening through block
zero. This is included in the host scheduling model. The physical firmware build
still needs qualification. [Protocol documentation](https://bluescsi.com/docs/Toolbox-Developer-Docs),
[current upstream implementation](https://raw.githubusercontent.com/BlueSCSI/BlueSCSI-v2/main/src/BlueSCSI_Toolbox.cpp).

The cost is bandwidth: four 1 KiB windows require four full-block reads, with
additional reopen/close traffic in some paths. The small-buffer native runs take
376,730–383,612 TIMER1 ticks per full response for the four regular windows.
Their sum is 1,520,716 ticks for 4 KiB retained. These are emulator measurements,
not a physical import-speed promise. No DMA is launched while draining a response.

## Revised memory accounting

| Resource | Bytes | Proposed physical interval, end-exclusive |
| --- | ---: | --- |
| Code, constants and UI ceiling | 5,634 | 003D3E..005340 |
| Shared input/list page | 1,024 | 005340..005740 |
| Right-channel output | 512 | 005740..005940 |
| Existing path/state/CDB/sense/staging/carry allowances | 832 | 005940..005C80 |

The separate 512-byte native-stack allowance remains unproved and is not added
to these local bytes. The new workspace saves 2,560 bytes relative to the old
4,096-byte workspace. Its exact final placement and all combined lifetimes are
proposed, even though smaller receive and in-place split mechanisms passed.

The checkpoint42-48 component census totaled **3,749 bytes**, leaving **1,885 bytes**
(historical; superseded by the combined 4,343-byte census below)
under the new ceiling. It counts both the transport and pair service routines,
all 831 bytes of retained SDS repairs, the menu resources/index, the parser and
rate table, a READ(10) provider, allocation/writer helpers and a 224-byte wrapper.
It does not assume unqualified sharing. The READ(10) provider is a measured
prototype cost, not a substitute for the missing Toolbox provider. This is not
a complete linked production footprint or a minimum possible size.

## Reuse decisions and remaining gate

- Native menu rendering/input reuse is supported by earlier clone/callback runs; keep private mutable resources. Full list, LCD/controller and navigation behavior remain to be measured.
- Retain the native wave-DMA mechanism through the bounded adapter. Reject unchanged fixed-source, fixed-block and unbounded-wait wrappers as general importer services.
- Keep the bounded private SCSI handshake. Native unbounded waits and CDB-byte mutation prevent counting the existing sender as a safe drop-in replacement.
- A scoped WAV-to-public constructor now passes checkpoints 74-78 for fresh fixed slots and one block per channel. Arbitrary descriptor construction, general allocation and persistence remain unqualified; count no speculative savings from them. Existing manual stereo object workflows are reference behavior, not callable ABIs.
- Short conditional branches are accepted where decoded control-flow equivalence and the native regression passed. Do not remove retained error/ownership fixes for space.
- Additional RAM, overlays and a boot-ROM change are held as contingencies. They are neither required by current measurements nor ruled out; decide after the complete integrated build is measured.

The next gate is one integrated implementation/map covering the Toolbox state
machine, general metadata/allocation/publication and browser callbacks, followed
by independent-target recovery and stack/interrupt qualification. Neither the
old 213-byte overrun nor a partial component residual is a feature-level verdict.
There is presently **no demonstrated reason to abandon the feature**, and also
insufficient evidence to mark the complete BS1 gate PASS.

### Checkpoints 49-52: combined pipeline and failure boundaries (2026-10-19)

- **49:** Guest RIFF validation, bounded SCSI reads, in-place stereo splitting and wave DMA execute together. Eight mono/stereo 1/511/512/513-frame cases match 131,072 guarded wave bytes, including under 192 injected MIDI controller bytes. This uses READ(10), not Toolbox GET_FILE, and dedicated destinations rather than public samples.
- **50:** The old image ignores Exit and writes PCM. The repaired image activates cancellation scanning and checks the latch after draining; operation7 returns with both first-case 8 KiB wave regions entirely sentinel (16,384 bytes). Error B5FF is distinct from success B502.
- **51:** Excluding native interrupt-service time from target inactivity avoids the observed false timeout at byte906. A deliberate initiator-held ACK still returns transport3/operation2 with zero payload bytes. This does not qualify an independently stuck target.
- **52:** Ordinary UI re-entry after cancellation succeeds in the same native session; all eight cases and 131,072 guarded wave bytes match. No guest state was forced.

BUG-129/130/131 are fixed in the private integration diagnostic. No firmware was released. The combined diagnostic is 2,830 code bytes. A conservative census retaining the other measured helpers is 4,343 bytes, leaving 1,291 of the proposed 5,634-byte ceiling; it includes diagnostic overhead and still omits unfinished required code. Final context layout, public metadata/lifecycle, Toolbox and UI integration, independent-target recovery and stack bounds remain open. BS1 stays REVISE.
[Pipeline validation](../condensed/validation/bluescsi-pipeline-2026-10-19.json).

### Checkpoints 53-56: wire-block boundaries, reuse and stack (2026-10-19)

- **53:** Eight mono/stereo 255/257/1023/1537-frame WAVs pass with a 457-byte odd JUNK chunk and PCM starting at byte510. All 131,072 guarded wave bytes match under 192 MIDI controller bytes. A too-short backing-image negative control returns original SCSI status02; BUG-132 fixes that fixture extent, not the target.
- **54:** Shared context copying reduces the combined diagnostic from2,830 to2,681 code bytes (149 saved); exact native boundary/MIDI checks pass. The helper preserves updated native R60..R74 while restoring streaming locals.
- **55:** Guest fixed-4-KiB scheduling assembles two response fragments into the same <=1KiB input buffer. At the wire boundary, a stereo frame is split after its left word; the combined PCM remains exact. The 2,925-byte intermediate passes MIDI and same-session cancellation/retry. READ(10) still supplies the blocks; actual Toolbox EOF/open behavior is not claimed.
- **56:** ABI-based save/restore reduction brings this integrated fixed-block diagnostic to2,783 code bytes and the decoded extension-stack bound from330 to264 bytes including the hook return. MIDI, same-session cancel/retry and initiator-held-ACK error checks pass. All decoded exits balance the extension stack; native ISR/pre-entry stack remains outside this bound.

Current conservative census: **4,285 bytes**, with **1,349 bytes** left under the proposed5,634-byte code/UI ceiling. It includes diagnostic overhead and separately retained helpers, counting the now-shared11-byte copy helper once. Required Toolbox, public metadata/lifecycle, browser behavior and final integration are still absent. No complete fit or GO is claimed. The actual emulator also needs target-scoped ten-byte vendor framing: current generic framing treats D1/D9 as six-byte commands and has no Toolbox handler. Full32-bit file offsets, short EOF blocks, independent target recovery and final stack/ownership qualification remain open.

[Block-window evidence and reproduction sources](../condensed/validation/bluescsi-block-windows-2026-10-19.json).

### Checkpoints 57-61: native Toolbox D1 path (2026-10-19)

- **57:** Added an opt-in, target-scoped read-only D1 fixture and ten-byte framing. The device test fails on the old executable at early command completion, then passes12 cases covering exact blocks, short/empty EOF, reopening, missing/closed files, sense isolation, unsupported requests and ordinary READ afterward. D0/D2/D9/discovery remain unimplemented; no capabilities are advertised.
- **58:** The guest provider now sends D1 commands, reopens through block0 before each nonzero block, and validates actual short response lengths. All eight odd-padded mono/stereo fixtures pass under192 MIDI bytes with131,072 exact guarded wave bytes. This replaces the READ(10) stand-in for this named pipeline.
- **59:** Same-session cancellation/retry passes all eight cases. Deliberately omitting the eighth fixture returns original SCSI status02/operation2 while114,688 guarded bytes from the first seven cases remain exact.
- **60:** Read-only tracing accounts for69 ten-byte D1 commands,46 short responses, five nonzero blocks and64 retained windows. The independent trace audit verifies open/EOF sequencing, lengths, status and final closure; PCM checks also pass.
- **61:** The rebuilt emulator passes743 backend tests and ordinary native boot/load/playback. With the fixture disabled, all33,554,432 wave-RAM bytes match the prior executable in the named READ(10) pipeline.

The D1 diagnostic is2,880 code bytes; the conservative partial census is4,382 bytes, leaving1,252 under the5,634-byte ceiling. Static extension stack is266 bytes including the hook return, excluding native ISR/caller use. BS1 remains REVISE. The fixture's numeric file mapping,32MiB cap and deterministic closed-handle errors are an explicit test profile, not complete physical BlueSCSI behavior. Discovery/directories, full32-bit guest offsets, public sample creation, UI, final fit and independent-target recovery remain open.

[Fixture contract](bluescsi-toolbox-fixture.md) · [Evidence](../condensed/validation/bluescsi-toolbox-native-2026-10-19.json).

### Checkpoints 62-66: directory-to-WAV integration (2026-10-19)

- **62:** The opt-in native fixture adds ten-byte D0/D2 listing/count and D9 capability/path commands, including DATA OUT directory changes. The new synthetic SPC test fails against the previous D1-only executable and passes25 cases after rebuild: 100 entries, overflow rejection, path failures, index99 reads, capability fields and ordinary READ after DATA OUT. This is device-model evidence, separate from firmware acceptance.
- **63:** The ordinary guest callback checks capabilities, selects `/Files/Keys`, verifies the returned path/count, then drains each320-byte list while retaining one40-byte entry. Actual wire indices and sizes drive D1 reads; the old catalog table is zeroed. Eight odd-padded mono/stereo WAVs produce131,072 exact guarded wave bytes under192 MIDI bytes. The target/path/count are diagnostic constants, not a finished browser.
- **64:** Ordinary Exit cancellation and same-session directory/import retry pass. A missing Keys directory returns original SCSI status02/operation2 before any per-file results or diagnostic PCM writes;112 result bytes remain zero and all33,554,432 wave bytes match an independent boot baseline. BUG-133 corrects the verifier to count12 DATA OUT path bytes and compare initialized wave RAM instead of assuming zeros.
- **65:** Read-only tracing verifies81 commands: threeD9, oneD2, eightD0 and69D1, with46 short responses and five nonzero file blocks. Selected-row windows and expected lengths/status pass. Decoded extension stack remains266 bytes including the hook return, excluding native ISR/caller depth.
- **66:** All744 backend tests and ordinary boot/load/playback pass. With the fixture disabled, all33,554,432 wave-RAM bytes match the earlier executable. Original OS/ROM hashes remain unchanged.

The diagnostic is3,346 code bytes. Retaining the same1,502-byte allowance for previously measured separate helpers yields a **4,848-byte partial census**, leaving **786 bytes** under5,634. This supersedes the4,382/1,252 sizing headline, but is still not complete integration: discovery, general32-bit guest files, public sample metadata/lifecycle, UI, ownership/recovery and final fit remain open. BS1 stays **REVISE**. The fixture uses sorted host entries, a virtual `/Files` root and stricter overflow/path behavior; physical parity is unclaimed.

[Directory fixture contract](bluescsi-toolbox-fixture.md) · [Identity-bound evidence and reproduction sources](../condensed/validation/bluescsi-directory-native-2026-10-19.json).

### Checkpoints 67-79: discovery, public samples and native audition (2026-10-19)

- **67 — Full directory boundary:** The guest handles100 mixed entries, retaining one40-byte row per4000-byte response. It skips92 folders and loads files with actual wire indices92-99 into separate diagnostic destinations. Eight mono/stereo files and131,072 guarded wave bytes pass. BUG-134 fixes a reversed diagnostic result-capacity branch.
- **68 — Wider file addressing:** The provider now carries32-bit file lengths and offsets through RIFF reads and D1 block construction. Eight mono/stereo files whose PCM starts at66,046 bytes pass under192 MIDI bytes. This does not make the public constructor a general large-sample importer.
- **69 — Address crossings:** A stereo frame split at byte65,534 crosses both4KiB and64KiB boundaries without channel loss. A separate file exercises D1 block256 above1MiB. Exact PCM and read-only command traces pass.
- **70 — Discovery model:** Opt-in INQUIRY adds a clearly marked test identity and API byte; MODE SENSE(6), DBD, current page31 returns the source-backed vendor signature. Nine named device checks pass. BUG-135 fixes the missing API-byte allocation. Discovery source is pinned to commit5e64e3b4a09088c67a2a6728385600ea67ddbe0d, not the user's installed build.
- **71 — Guest discovery:** The client scans IDs0-6, checks the extended identification/API and full vendor page, then selects the discovered target for Toolbox commands. IDs2 and6 pass; target6 is reached after six absent targets. BUG-136 corrects its test image to the emulator's CD6 slot. No valid target returns operation8 without PCM/allocation changes.
- **72 — Negative inputs:** Empty directories complete without sample writes. Count overflow returns original status02. Invalid bit depth, truncated RIFF and empty files reject before allocation; a one-frame sample rejects the constructor's declared minimum. All seven negative/empty runs preserve every wave-RAM byte, all512 public descriptors and allocation mirrors.
- **73 — Real menu dispatch:** The reused268-byte native menu runs the combined directory/WAV client through its banked callback, preserving the original Save System hook. It is a private first-row callback experiment, not a completed Files/Folders browser. Native menu resources are mutable; two observed field updates are recorded separately from immutable code/constants.
- **74 — Actual public samples:** Eight WAVs create12 public mono/stereo descriptors and12 reserved channel blocks. All source PCM, zero padding within the one-block reservations, all512 descriptors and all33,554,432 wave bytes match independently constructed expectations. Rate/root/OneShot fields and stereo names are generated from the declared diagnostic policy; these are no longer synthetic PCM-only destinations.
- **75 — Public rollback/retry:** Exit during the first owned transfer drains the command, restores cursor and both mirrors, leaves all public slots unchanged and clears the96-byte staging area. Same-session retry publishes the complete exact12-sample set. General competing-SysEx exclusion and stalled-DMA recovery are not established.
- **76 — Native selection/audition:** Ordinary Loop/Smoothing selection builds preview references512/513 from imported blocks4/5. Mono output channels match; stereo channels are nonzero and distinct; both release to silence. Public descriptors survive selection. This is preview audition, not permanent playable assignment or exact endpoint/persistence qualification.
- **77 — Publication protection:** Repeating the completed import rejects occupied slots with operation9, preserves all published records/allocation state and leaves wave RAM exact. The compact constructor's invalid-frame path likewise preserves the complete boot baseline.
- **78 — Reuse, stack and combined menu:** Sharing the constructor epilogue and narrowing its register saves reduces code from4,647 to4,507 bytes; invalid input, cancellation/retry and audition still pass. The final menu image combines discovery, WAV parsing, public publication and audition. Decoded extension stack is268 bytes including the call return; native ISR/caller depth remains excluded. The current conservative partial census is6,009 bytes,375 over5,634, and still includes potentially duplicate standalone helpers.
- **79 — Regressions:** All745 backend tests and ordinary native boot/load/playback pass. With Toolbox disabled, all33,554,432 wave bytes match the earlier executable. Original OS/ROM identities remain unchanged. No release firmware or physical qualification is claimed.

**BS1 remains REVISE.** The private constructor uses fresh fixed slots, cursor<=12,2..4594 frames/channel, one4608-word block per channel, generated names and the tested44.1kHz/root60/OneShot policy. It does not yet supply general allocation/ownership, full-length samples, permanent Partial/Patch assignment, Save/cold Load, complete browser UI or independent-target recovery. The6,009-byte tally is conservative and incomplete, not a proof that every implementation must exceed the budget. Next: reconcile demonstrated helper reuse and final RAM/state placement, integrate competing-operation ownership, then qualify general metadata/allocation and persistence before declaring GO.

[Integrated client evidence and reproduction sources](../condensed/validation/bluescsi-integrated-client-2026-10-19.json).
