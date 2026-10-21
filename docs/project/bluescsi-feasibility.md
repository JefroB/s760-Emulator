# BlueSCSI Files/Folders feasibility evidence

**2026-10-19 update:** the [workaround evaluation](bluescsi-workaround-evaluation.md) proposes a 1,536-byte workspace and 5,634-byte code ceiling backed by scoped native tests. Earlier 4 KiB workspace arithmetic below is historical; complete integrated fit remains open.

**2026-10-18 twenty-fourth checkpoint — BS1 IN PROGRESS, gate not passed.**

The feasibility work now includes executable guest transport experiments entered through ordinary Disk controls in private patched OS copies. They preserve CDB bytes, handle short/status-only responses, transfer exact 4 KiB buffers in both directions, distinguish deliberate command failures from successful sense retrieval, and return to ordinary HDD Load/playback. Explicit service points allow timer and MIDI interrupts; ordinary Exit now cancels through bounded completion of the current command and stops later commands. Broader ISR/input/stack bounds, complete memory ownership, independent target-fault recovery and the stereo import lifecycle remain open. Original firmware files remain unchanged; the native emulator rejects unsupported commands and explicitly handles the boot ROM's START UNIT request (BUG-113).

This is supporting evidence for the [feature roadmap](bluescsi-files-roadmap.md), not a completed importer or a physical BlueSCSI test. The [validation record](../condensed/validation/bluescsi-feasibility-2026-10-18.json) contains input/build hashes, 1,952 byte-checked assembly annotations, additional instruction decodes, selected raw native contexts, RAM observations and the observer/analyzer sources.

The [second validation record](../condensed/validation/bluescsi-stereo-ui-followup-2026-10-18.json) adds 12 snapshots in a fresh native instance, five audio cases, 970 checked annotations and 299 additional decodes. Annotation counts overlap the first checkpoint and must not be added as unique coverage.

The [third validation record](../condensed/validation/bluescsi-memory-transport-2026-10-18.json) adds two native instances, 11 snapshots, exact 8,002-byte marker persistence through Save System, cold stereo playback, 512 guest TIMER1 reads, 1,024 periodic timer observations, 165 checked annotations and 90 decodes. Eight host arithmetic cases support the proposed deadline design; they are not guest transport tests.

The [fourth validation record](../condensed/validation/bluescsi-guest-transport-2026-10-18.json) retains the experimental image builders, 325 decoded instructions, four guest runs, 16 snapshots, raw SPC/timer observations, caller restoration checks, BUG-113 regression history and final-build HDD/CD/runtime results. The final experiment executes 14 cases; two earlier runs execute 13 and document the original emulator defect. These are transport diagnostics, not BlueSCSI protocol or physical-device acceptance.

The [fifth validation record](../condensed/validation/bluescsi-transfer-errors-2026-10-18.json) adds one passing 16-case run, four snapshots, 349 decoded instructions and an expected red experiment exposing the previous prototype's 20 ms/DATA OUT limits. It retains complete per-case scratch-image/buffer captures, transmitted-byte checks, measured timer wraps and source identities. The native executable remains the fourth checkpoint's final build; its 561-test result is not presented as a newly rerun suite.

The [sixth validation record](../condensed/validation/bluescsi-interrupt-cooperation-2026-10-18.json) adds three fresh interrupt-cooperative runs, the final 20-case matrix, 468 decoded instructions, byte-checked ISR code and complete stack-write observations. Timer/MIDI progress, state preservation, exact buffers/media and subsequent HDD Load/playback pass. These are idle native workload results; the emulator and original firmware inputs remain unchanged.

The [seventh validation record](../condensed/validation/bluescsi-cancellation-2026-10-18.json) adds an expected negative control and five fresh passing processes: ordinary read cancel, held-Exit write cancel, unrelated-key control, cancellation followed by a deliberate initiator-stall timeout, and clear-on-re-entry. Six invocations execute 45 cases and all return to exact native HDD Load/playback. No physical abort/reset or importer-publication acceptance is claimed.

The [eighth validation record](../condensed/validation/bluescsi-memory-lifecycle-2026-10-18.json) adds seeded code/workspace lifetime through stereo capture, Save, cold Load and armed session restore, followed by a fresh 20-case seeded-workspace transport/HDD run. Four processes and 29 snapshots include one deliberate pre-restore zero state. The [memory contract](bluescsi-memory-contract.md) records DMA evidence, alias arithmetic, shared-buffer lifetime rules and a corrected split between local data and native stack. Full ownership and complete-client fit remain open.

The [ninth validation record](../condensed/validation/bluescsi-sample-contract-2026-10-18.json) adds twelve stock-OS snapshots, ten exact sample allocations/92,160 bytes, all eight rate labels and measured preview pitches, Forward/OneShot and distinct playback-point controls. BUG-114/115 correct the fixture builder while preserving historical preset bytes; 588 backend tests pass with zero skips. The [sample contract](bluescsi-sample-contract.md) separates this metadata evidence from proposed stereo transaction ownership. Permanent assignment and arbitrary-length allocation/publication/rollback remain open.

The [tenth validation record](../condensed/validation/bluescsi-permanent-assignment-2026-10-18.json) adds two stock-OS processes, 25 snapshots, 238 completely replayed object stores and seven stereo audio cases. Ordinary Partial/Patch/Perform assignment and naming produce a saved hierarchy with one performance, one patch, one partial and two samples. Cold Load restores all 736 record bytes and 239,616 PCM allocation bytes; Perform Play works before preview initialization. Eleven byte-checked store anchors identify construction points but do not establish callable ABIs. The [permanent hierarchy contract](bluescsi-sample-contract.md#permanent-playable-hierarchy-and-persistence) distinguishes this native workflow from the still-unimplemented importer. Original firmware and runtime/source hashes remain unchanged, and the earlier 588-test suite was not rerun.

The [eleventh validation record](../condensed/validation/bluescsi-length-contract-2026-10-18.json) adds 18 SDS length cases and one settled mono cancellation/retry, 54 snapshots, 249,760 exact transmitted bytes, 3,143 acknowledgment messages and 399 bounded original-OS instruction decodes. BUG-116/117 fix native MIDI output and sequential wave writes; both component regressions first failed. All 590 backend tests pass with zero skips, and ordinary runtime boot/media/audio, scheduled MIDI and variable-block rendering pass. The native SDS packet/zero-fill extents can exceed their reservations, excluding direct reuse as a bounded WAV writer. Early retry during cancellation exposed BUG-118, addressed below. [Bounds and ownership consequences](bluescsi-sample-contract.md#sds-length-boundaries-and-cancellation).

The [twelfth validation record](../condensed/validation/bluescsi-cancel-ownership-2026-10-18.json) identifies the stock supervisor's write that clears a newly active retry and supplies a reproducible private OS guard for BUG-118. Three positive timing runs and one negative control retain 63 snapshots. Busy rejection preserves the current allocation/staging/public table and PCM; settled retries and follow-on transfers publish nine samples with 28,800 exact PCM bytes. The OS emits 375 exact ACKs and six CANCEL responses. Three focused tests pass, including 65,536 decoded command/state combinations and immutable-image safeguards; ordinary patched-OS boot/playback, scheduled MIDI and variable-block audio also pass. The existing native executable/source and original firmware remain unchanged; the prior 590-test suite was not rerun. Completion/error paths that clear transfer state early still require an explicit owner, and no stereo transaction, bounded WAV writer or physical qualification is claimed. [Repair and reproduction](../firmware/os/os-transfer-lifecycle.md#native-cancellation-overlap-and-private-os-guard).

The [thirteenth validation record](../condensed/validation/bluescsi-header-lifecycle-2026-10-18.json) closes BUG-119's observed header overlaps with an extended private OS patch. Completion remains busy as FF until publication/cleanup; allocation errors keep their state until the shared final clear. Two negative controls and four passing native runs retain 78 snapshots, eleven samples/10,800 exact PCM bytes, 148 ACKs and five CANCEL responses. A short receive completes before supervisor entry and publishes correctly; cancellation still passes. Seven focused tests include 841 unsigned completion pairs and the previous command/state matrix. The initial 80-marker trial and incorrect JGT test semantics are explicitly excluded; the corrected final image passes ordinary playback, MIDI and audio checks. Originals and the emulator are unchanged, and the full backend suite was not rerun. This establishes incoming-header exclusion, not atomic stereo publication or exclusion of other SDS/disk commands. [Contract](../firmware/os/os-transfer-lifecycle.md#header-admission-through-publication-and-error-cleanup).

The [fourteenth validation record](../condensed/validation/bluescsi-command-exclusion-2026-10-18.json) closes BUG-120's outgoing-request overlap with an extended private OS patch. Requests during active receive, publication, invalid-slot error cleanup and cancellation now return CANCEL before decoding or sender setup. Two prior-image failures, a prior ACK compatibility control and seven final native runs retain 118 snapshots. Eighteen samples match 2,880 transmitted PCM bytes; 56 ACKs and five CANCEL replies match. An idle dump sends all 9,216 sample bytes with an exact retransmission, then accepts another receive. Ten focused tests and ordinary patched-OS playback/MIDI/audio pass. Original firmware and native runtime sources are unchanged; the full backend suite was not rerun. Already-active outgoing sessions, disk exclusion, stereo publication and bounded WAV writing remain open. [Contract](../firmware/os/os-transfer-lifecycle.md#receive-owner-exclusion-for-outgoing-requests).

The [fifteenth validation record](../condensed/validation/bluescsi-sender-ownership-2026-10-18.json) closes BUG-121's active-sender overlaps. Commands 01 and 03 now require receive state 0 and sender state FF. Two failing prior-image controls and ten final native runs retain 182 snapshots. Twenty-eight received samples match 4,480 transmitted PCM bytes; four complete dumps retain 36,864 source bytes. All 86 ACKs, nine CANCEL replies and 469 data packets match, including retransmission and a cancelled partial dump. Completion/explicit cancellation allows a later receive, whose counters and PCM survive stale ACK/NAK. Thirteen focused tests include 131,072 state/entry combinations and header setup/error ordering. Normal patched-OS playback/MIDI/audio pass with immutable original firmware and unchanged native sources. Disk exclusion, abandoned-sender recovery/timeouts, stereo atomicity and bounded WAV writing remain open. [Contract](../firmware/os/os-transfer-lifecycle.md#shared-admission-for-active-senders-and-receivers).

The sixteenth checkpoint fixes BUG-122, a regression in the private sender guard: local Sample Dump exits left B1AE=0, blocking the next receive. Three existing cleanup tails now share a bank-preserving FF release after parser/display cleanup. Four local completion/cancellation cases and one remote-stall/recovery case preserve 15 received samples/2,400 exact PCM bytes and two complete outgoing dumps/18,432 bytes; all 45 ACKs, two CANCEL replies and 251 data packets match. Three negative controls bring the retained total to 115 snapshots. Twenty-four focused tests and ordinary playback/MIDI/audio pass. At this checkpoint BUG-123 was OPEN: a remotely requested dump stays busy after 60 seconds without ACK and panel Exit, while MIDI CANCEL restores admission. Third-tail error coverage is decoded/unit only; local UI races, disk exclusion, timeouts, stereo transactions and bounded WAV writing remain open. [Cleanup contract](../firmware/os/os-transfer-lifecycle.md#local-sample-dump-cleanup-and-remote-stalls), [evidence](../condensed/validation/bluescsi-local-sender-lifecycle-2026-10-18.json).

The seventeenth checkpoint: BUG-123 is fixed in experimental firmware: successful remote requests claim foreground state 7; five seconds without packet-counter progress or panel Exit cancels safely. Seven remote scenarios and four local compatibility cases preserve 33 received samples/5,280 exact PCM bytes and three complete dumps/27,648 bytes. All 99 ACKs, seven CANCEL replies and 371 data packets match; one prior-image negative control brings the total to 180 snapshots. Thirty focused tests and ordinary playback/MIDI/audio pass. The 640-byte helper leaves 863 bytes of the proposed code/UI budget, with combined placement and full fit still unqualified. Observed stack use is 182 bytes and maximum TIMER1 read gap 42.710 ms in these workloads. Local UI races, native Disk exclusion, full stack bounds, stereo transactions and bounded WAV writing remain open. [Recovery contract](../firmware/os/os-transfer-lifecycle.md#foreground-remote-sender-recovery), [evidence](../condensed/validation/bluescsi-remote-recovery-2026-10-18.json).

The eighteenth checkpoint: BUG-124 is fixed in experimental firmware. A final local-send ACK followed immediately by a receive header previously leaked a sample block; a queued remote request was also discarded by local cleanup. Local entry now checks shared admission and claims state 8, retaining ownership through display cleanup and releasing atomically. Nine accepted native cases preserve 27 samples/4,320 received PCM bytes and five complete dumps/46,080 bytes; all 81 ACKs, six CANCEL replies and 601 packets match. Two prior-image controls bring the total to 175 snapshots. All 96 focused tests and ordinary playback/MIDI/audio pass. The added 160 bytes leave 703 bytes of the proposed code/UI budget; complete fit and stack bounds remain open. Busy local entry and setup-failure handling have decoded/model coverage. Native Disk exclusion, remaining preparation/cancel timing, stereo transactions and bounded WAV writing are still unqualified. [Local owner contract](../firmware/os/os-transfer-lifecycle.md#local-ownership-through-setup-and-cleanup), [evidence](../condensed/validation/bluescsi-local-owner-2026-10-18.json).

The nineteenth checkpoint qualifies four ordinary Disk Load cases with the unchanged BUG-124 experimental image: floppy/HDD crossed with ten SDS receive headers or ten remote dump requests. Each preserves all 13 allocations/119,808 PCM bytes, passes playback/release, then accepts and publishes a new sample with 160 exact PCM bytes. The HDD exports remain byte-identical. Read-only traces show 153/152 overlapping FDC command writes and 98/98 SCSI command writes, with no SDS state/saved-cursor writes or MIDI replies during Load. These are serial-delivery and interoperation results, not proof of parser dispatch, an explicit busy reply, or every payload-phase boundary. Save, Disk entry during an existing SDS owner, manufacturer41 SCSI sessions and controller/hardware cases remain open. No firmware/runtime changes or new confirmed defect were needed. [Disk Load evidence](../condensed/validation/bluescsi-disk-load-2026-10-18.json).

The twentieth checkpoint adds two floppy Save cases with the unchanged experimental image: ten SDS headers or ten remote dump requests over 27 seconds, followed by two separate stock-OS cold Loads. Each Save clears four active notes and remains silent over 1,543,500 frames; 166 observed FDC writes overlap serial delivery. No SDS state/saved-cursor writes or MIDI replies occur during the measured Save interval. Both saved disks recover all 13 allocations/119,808 PCM bytes with matching playback/release under stock firmware. Each experimental process also receives/publishes another 160 exact PCM bytes after Save. Originals remain unchanged. Partial disk traces prove positive overlap only; parser handling, deliberate busy replies, HDD Save, entry during an active owner, manufacturer41 sessions and hardware/controller variants remain open. No firmware/runtime changes or new confirmed defect. [Save and stock reload evidence](../condensed/validation/bluescsi-disk-save-2026-10-18.json).

The twenty-first checkpoint adds two HDD overwrite Save cases on copies of the previously native-saved 10 MiB image: ten SDS headers or ten remote dump requests over 27 seconds, followed by separate stock-OS cold Loads. Both exported images change, while independent Roland allocation extraction and cold Load preserve all 13 samples/119,808 PCM bytes. Playback/release match before and after cold Load; each experimental process also receives/publishes another 160 exact PCM bytes after Save. Partial traces show 209/209 SCSI command writes overlapping serial delivery, with no SDS state/saved-cursor writes or MIDI replies during the measured Save interval. Four active notes are cleared on Disk entry and 1,543,500 captured Disk-mode frames remain silent in each case. Originals remain unchanged. The excluded trials failed to activate the HDD-specific Yes button or encountered a host snapshot-file sharing conflict; neither is firmware-defect evidence. Active-owner Disk entry, manufacturer41 sessions, remaining phase boundaries and hardware/controller qualification remain open. [HDD Save evidence](../condensed/validation/bluescsi-hd-save-2026-10-18.json).

The twenty-second checkpoint tests Disk-menu entry during active SDS ownership. Receive (state1) and remote send (state7) retain ownership across both Load/Save menu attempts when ordinary packet progress prevents timeout; no allocation/backup/owner writes occur between the measured active snapshots. Peer cancellation then restores idle and Disk Load entry. Local send behaves differently: separate Load/Save click attempts trigger cancellation and release state8 while remaining on System MIDI; a matched no-click ACK-stream control stays active. These cases qualify cancellation/recovery, not local ownership retention. Five native processes/79 snapshots preserve the two existing descriptors and full allocations, finish with three samples/480 exact received PCM bytes each, and byte-check 47 transmitted packets in total. Disk Load screens after release show the expected system-floppy rejection; no media Load/Save is executed in these menu-entry tests. Exact mouse-cancel dispatch, manufacturer41 sessions, pre-supervisor timing and hardware/controller cases remain open. No firmware/runtime change or confirmed new defect. [Active-owner evidence](../condensed/validation/bluescsi-active-disk-2026-10-18.json).

The twenty-third checkpoint qualifies the separate manufacturer41 Remote Mode (MIDI/SCSI) session using ordinary MIDI requests. Five native cases cover remote-send timeout, peer cancellation, full completion, session exit requested during a stalled send, and receive publication. All return through the session caller at0166:8C68 and exit cleanly where applicable; remote scratch RW1C..6A, bank selectors and WSR match entry, with the expected18-byte wrapper/return stack difference. The two timeouts measure5,000,069 and5,000,056 timer microseconds. An exit request clears1FA4 while state7 remains owned, then the session exits after timeout recovery; it is not an immediate transfer abort. Across76 snapshots,16 received samples/2,560 PCM bytes and118 sent packets match exactly, including a full9,216-byte allocation and wire padding. All ten manufacturer entry/exit notifications match their bytes and checksum. Observed stack use reaches196 bytes relative to the session continuation, and the largest observed clock-service gap is42.780 ms; these are not complete stack/ISR bounds. No firmware/runtime changes or new confirmed defect. External SCSI initiator operations, enumeration/deletion, remaining entry/cancel boundaries and hardware/controller cases remain open. [Session evidence](../condensed/validation/bluescsi-session-2026-10-18.json).

The twenty-fourth checkpoint fixes BUG-125 in experimental firmware. A receive header immediately followed by CANCEL previously left one reserved block unreachable: idle cursor3 with only two samples, then retry at block3/cursor4. Two of three prior-image controls reproduce it; the session-start burst does not admit the receive and therefore does not test rollback. The new31-byte helper retains receive cancellation as stateFE for active1, completed-but-unpublishedFF and already-cancelledFE, while other owners keep generic0A. FE follows the existing receive rollback path; duplicate CANCEL cannot erase its ownership. Ten native cases cover ordinary/session entry bursts, duplicate cancellation, a one-packet completion/CANCEL boundary, active receive cancellation, remote cancellation/timeout and local cancellation/full completion. All end with three samples/cursor3 and exact480 received PCM bytes each; 118 sent packets match. Including controls, 181 snapshots preserve both seed descriptors and allocations. All113 focused tests and ordinary native playback/MIDI/audio pass. The helper adds no RAM or call frame; total proposed code use becomes2,402 bytes, leaving672 arithmetic bytes (641 contiguous after0ABF). Exact pre-supervisor instruction ordering remains unproved because an exploratory read tap targeted the replaced entry instruction; ownership writes prove the defect and rollback. Complete memory/stack fit, remaining timing and transactional stereo/bounded WAV writing remain open. [Early cancellation evidence](../condensed/validation/bluescsi-early-cancel-2026-10-18.json).

## Baseline and method

| Input | Identity / choice |
| --- | --- |
| OS 2.24, both local original copies | 1,474,560 bytes; SHA-256 `3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd` |
| IC15 v1.11 | 32,768 bytes; SHA-256 `ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6` |
| Native MAME executable, checkpoints 1–3 and initial guest probes | SHA-256 `b02811c0054209fbb64e8e6dabca10e1d84466869221273d7fb17cc216cc8e65` |
| Native MAME executable, final fourth-checkpoint qualification | SHA-256 `b5036f4de04d0eb1007730a9120efb85278e219663bb73026ab32e4f0ec24524` |
| Native MAME executable, eleventh checkpoint / BUG-116/117 fixes | SHA-256 `ccb370a3f37c5fd7a9b2aa761ef339b9b5965d6211b64751dd7520557efb4dda` |
| Experimental OS cancellation guard, twelfth checkpoint | SHA-256 `0c24823eac6370ed9d9a382f499a602a2b8cb6593072c10f7fbf16ccb8cff59e`; 36 changed bytes confined to the existing 51-byte dispatcher span |
| Experimental OS header lifecycle guard, thirteenth checkpoint | SHA-256 `54c7b7ecb36b16c0f17b06b8f0ab2a0cbab5f04fad407e46cebc78db0f3f81e2`; 96 changed bytes in six existing spans totaling 123 bytes |
| Experimental OS request guard, fourteenth checkpoint | SHA-256 `cb5f65ef1ea15646ccee1ec3e20eddc801e1ccc80d6198dac5a3022524537e40`; 115 changed bytes in eight existing spans totaling 167 bytes |
| Experimental OS sender guard, fifteenth checkpoint | SHA-256 `a5817b0f891242b3f8e40f5caa86b46861f8feed58089bf279b78ba4d5f38684`; 146 changed bytes in eight spans totaling 204 bytes; temporary two-byte admission/counter calls |
| Experimental OS local sender cleanup, sixteenth checkpoint | SHA-256 `472b656b5ab859d1c6eb9814e25a3d1ecad69785db47b50e72fe20d96649dbd3`; 226 changed bytes in eleven existing spans totaling 288 bytes; temporary two-byte selector save in cleanup |
| Controls and RAM | Fresh private Mouse+CRT profile, ordinary mouse/panel input, 32 MiB wave RAM |
| Controller integration intent | Establish the extension on stock firmware first; separately qualify the selectable GB-6 v9 combination documented in [GB-6 patches](../firmware/os/gb6-os-patch.md). No assumption about the user's installed ROM/controller patch. |
| BlueSCSI | User reports V2 with current firmware. Exact installed build/capabilities and physical command traces remain to be read at device qualification. |

The observers read MAME's saved RAM backing and CPU register spaces without changing them. CPU write taps return no replacement value. They record selector/call contexts and writes into candidate regions. Four fresh emulator instances completed the two retained workflows. There are 22 RAM snapshots: 18 across stereo capture/reload and four across HDD Save/reload.

CPU taps do **not** see direct DMA writes in this driver. Snapshot differences include net DMA effects; neither method proves that an unchanged region is unused. The observations deliberately preserve this distinction. Timing is emulator timing, not physical SCSI timing. The stereo input uses the existing opt-in offline ADC model.

## BS1.1: memory exclusions and remaining candidate

Addresses below are **physical CPU RAM**, with end-exclusive ranges. For loaded bytes, add `0x4800` to obtain the original OS file offset. The boot loader supplies physical `0..0xFBFFF`; the following 16 KiB is not part of that loaded payload.

| Physical range | Size | Evidence | Allocation conclusion |
| --- | ---: | --- | --- |
| `003D3E..005C80` | 8,002 | Marker survives Save System/cold boot; seeded code/workspace survives sampling, Save/cold Load and session restore; declared transport workspace writes remain bounded | Candidate only; indirect users, broader UI/controller ownership, full-client sizing and lifecycle audit remain open |
| `0DABE4..0E435C` | 38,776 | Native writes during startup and media workflows; includes existing object/state storage | Exclude as a permanent extension region |
| `0E435E..0E7C00` | 14,498 | Native media workflows write it; HDD reload leaves 4,980 bytes different from initial contents | Exclude |
| `0E8010..0EC000` | 16,368 | HDD reload changes 11,060 bytes despite **zero CPU-write observations**; existing page `03A0` transfer buffers also reference this area | Exclude; demonstrates why CPU-only tracing is insufficient |
| `0EC000..0ED338` | 4,920 | Native writes; page `03B0:8180..9337` is the deletion mark area | Exclude |
| `0ED3F8..0F0000` | 11,272 | Contains `0ED712` transfer staging; stereo reload changes 4,106 bytes despite zero CPU-write observations in this region | Exclude |
| `0F53D4..0FC000` | 27,692 | Follow-up bounds the CRT backup slots across `0F0000..0FFFFB`; accepted LCD depths also use this tail | Exclude as permanent storage; see [screen-backup ownership](../firmware/os/os-screen-backup-storage.md) |
| `0FC000..100000` | 16,384 | ROM and OS initialize/use it; `010A:8D43..8D67` can fill page `03F0:8000..BFFF` with `FFFF` | Exclude |

The write counts are observations, not unique-byte counts. For example, zero-filled state can be rewritten many times while remaining byte-identical to the initial image. The evidence retains both counts and net differences.

### Lower candidate: marker and Save System follow-up

A private OS image replaces only file `00853E..00A47F` with an 8,002-byte nonzero pattern. The original range is zero-filled. Every byte in that range changes; all other input bytes and all executable instructions remain original. The surrounding interrupt stubs end at physical `003D3D` (`POPA; RET`), and resident low-page code begins at `005C80`.

The startup clear uses data page `0204`: logical `0120..111F` maps to physical `081120..08211F`, followed by SP `1120`. It therefore does not clear this candidate. A proposed contiguous code alias is fetch selector `0102 = 000F`, logical `413E..607F`; this is address arithmetic, not a validated executable overlay. Fixed low fetch, interrupt paths, indirect accesses and callees still need a complete preservation audit.

Through ordinary Mouse+CRT controls, the marker image boots, opens Disk → Save System, formats a private blank 1.44 MB floppy and writes the system. The exported system retains all 8,002 marker bytes exactly. A second process cold boots that export, loads the recorded stereo fixture and enters Loop/Smoothing. All 11 snapshots across both instances retain the marker; CPU data-read/write taps observe no candidate accesses. Instruction fetch and direct DMA bypass these taps, so this is qualified workflow evidence, not proof that the range is unused.

The saved system's SHA-256 is `7e7b2dc3c7d57f1769e83ddf0d5abbb8362346cf2262de067efb439756554bea`. It differs from the marker input in 969 other bytes; whole-image equality is neither expected nor claimed. The cold stereo test retains all 239,616 allocated PCM bytes, matches both output channels at the same source position with relative RMS error below `4.02e-8`, and releases to a silent final second.

**Save System copies this candidate into the saved image.** Any future mutable workspace placed here must be explicitly initialized on boot/entry; saved bytes must never be trusted as live pointers, open-file state or current buffer validity. The experiment has not tested executable extension code, sampling with the marker present, nested popups, LCD/GB-6 operation or session restore. It strengthens one lifetime claim without reserving the region. [Marker, source hashes, snapshots, timer rows and reproduction sources](../condensed/validation/bluescsi-memory-transport-2026-10-18.json).

Existing code at `004B:647D..64CF` chooses data pages `03C0/03D0/03E0/03F0` from the upper bits of an offset and stores through the lower 14 bits. The follow-up establishes three CRT slots at offsets `0000/5554/AAA8`: each holds four geometry bytes, 2,000 text bytes and `32 * width * height` pixel bytes, with a permitted product up to 620 for valid nonzero dimensions. Each maximum slot is `5554` bytes, so the three slots cover through physical `0FFFFB`. A separate conditional clear covers the full final page. LCD saves use `2200` bytes on each of pages `03C0/03D0/03E0`; the normal save guard rejects depth 3 despite an encoded fourth dispatch arm. These byte-checked users exclude the tail without claiming every byte was dynamically exercised. The lower 8,002-byte candidate has no equivalent ownership proof yet.

### Preliminary working-memory budget

| Resource | Proposed allowance |
| --- | ---: |
| 100 returned directory records | 4,000 bytes |
| One file-read block | 4,096 bytes |
| Current and pending paths | 128 bytes |
| Browser/transport state | 256 bytes |
| CDB scratch | 32 bytes |
| Sense/discovery state (INQUIRY payload reuses read buffer) | 64 bytes |
| Two staged sample descriptors | 96 bytes |
| RIFF/deinterleave carry and scratch | 256 bytes |
| Additional stack headroom | 512 bytes |
| **Provisional subtotal** | **9,440 bytes** |

Code, UI descriptors/strings and any additional native-call scratch remain unmeasured. These numbers are a design allowance, not measured stack usage or a RAM reservation. Stereo can be deinterleaved in bounded chunks, but the native write path and its scratch requirements still need qualification. The initial separate-buffer working set exceeds the lower 8,002-byte candidate.

The proposed revision shares one 4,096-byte workspace between the listing and file-read block. Before import, retain the selected record identity/name and path in browser state; invalidate the listing when reusing its storage, then refresh it before returning to browsing. This saves 4,000 bytes, giving a **5,440-byte combined working allowance**. The eighth checkpoint corrects its placement accounting: **4,928 bytes are local data and 512 bytes are additional native stack allowance outside the candidate**. This leaves a **3,074-byte ceiling for code/UI/constants**, rather than the earlier 2,562-byte calculation that charged stack to this region. The stack allowance, complete-client fit and shared-buffer lifetime remain unproved. [Proposed extents and ownership rules](bluescsi-memory-contract.md#corrected-budget-and-proposed-placement).

**Next:** complete the lower candidate's access/interrupt/lifecycle audit and find a complete code-plus-working-set placement. The marker Save System round trip passes; saved mutable state requires explicit initialization. Any borrowed native storage still needs a preservation contract covering interrupts, dialogs, native Disk transitions and session restore. The upper tail is no longer a free-space candidate.

### Seeded workspace, sampling and session-restore follow-up

The new private image preserves the 1,571-byte helper and 480-byte case table,
and seeds the other 5,951 candidate bytes. Its SHA-256 is
`d7f0d3e174a457ab0c0022d1454ab9850006bb1ea8f683d0ce959d1def6f9a97`.
All 24 initialized sampling/Save/cold-Load snapshots retain the full candidate.
A separate fresh-process snapshot is zero before the armed checkpoint restores
the code/table/pattern. Native stereo capture then succeeds with 56,737 exact
frames/channel and 239,616 allocation bytes identical in RAM, saved disk and
cold-loaded RAM. CPU data taps see no candidate accesses in this passive
sampling workflow. Logged completed DMA copies overlap it only during the two
system boots; four such intervals have the expected file-to-RAM translation.

A fourth process enters the helper through ordinary Disk controls with its
workspace still seeded. All 20 cases pass, including original errors/sense and
timeout/poll exits. The prefilled cancel word clears; changes stay within the
declared buffer/guards, result records and context. Code, table and unused
pattern bytes remain exact. Subsequent HDD Load/playback retains all 13 samples
and 119,808 allocation bytes, with unchanged exported media and silent release.
The 1,800 interrupt service points retain saved scratch/bank state.

This is modeled lifetime and initialization evidence. It does not reserve the
region, relocate the production buffer, prove all indirect aliases, or qualify
LCD/GB-6/nested UI and external BlueSCSI session recovery. The retained report
documents a host-only final path-reporting failure and its independent
read-only validation; the guest acceptance outputs remain unchanged.
[Detailed memory contract](bluescsi-memory-contract.md),
[eighth evidence record](../condensed/validation/bluescsi-memory-lifecycle-2026-10-18.json).

## BS1.2: transport observations and reuse boundary

The [timeout and recovery design](bluescsi-transport-contract.md) records the timer-source evidence and required exit behavior. TIMER1 reads progress at the expected nominal rate in the current build, including reads with interrupts masked. A 16-bit counter still requires a qualified sampling interval shorter than its wrap; a finite independent poll budget is also required. The later guest experiments below qualify limited deadline/poll exits; independently faulted-target and reset recovery remain open.

The native initializer `004B:794A` clears `RW2E`, so its normal entry skips the conditional SCMD bus-reset branch. It also updates native self-ID, configuration and failure state. Native sense handling can clear `RBB` while changing shared cache state. Neither routine is transparent cleanup for the browser; the new client must preserve original command status and coordinate drive-state invalidation after recovery.

Ordinary native calls enter `003B` through `0000:CE14`. The wrapper saves fetch selector `0102` and `RW28/2A/2C/2E/42`; the retained observations distinguish the pre-call selector write at `CE22` from the restoring write at `CE36`. At the latter tap the POP has already advanced SP, so observed SP is 12 bytes above the entry snapshot. Register and selector values in the sidecar are observations at those boundaries, not an assertion that every callee preserves them.

Observed caller mappings include low fetch `000F`, resident fetch `0000`, low data `0204`, peripheral data `0400`, and command-caller fetch `0068`. Operand mappings must remain explicit: an address in the `4000..7FFF` window does not identify its data without `010A`.

| Routine / path | Established at this checkpoint | Still open |
| --- | --- | --- |
| `003B:7482` selection | Real entry/return contexts in boot/discovery and media operations | Complete retry bounds, absent-device timing and cleanup |
| `003B:7592` command sender | Count-prefixed templates include six-byte REQUEST SENSE/INQUIRY/TEST UNIT READY and ten-byte READ CAPACITY/READ/WRITE | Vendor-byte preservation, full clobbers, bounded handshake and cancellation |
| `003B:7B14` PIO | Matched native sense read: `RW48=2E0E`, `RWBC=10` becomes `RW48=2E18`, `RWBC=0`; caller data selector `010A=02FA` restored | Short/zero transfers and failure paths; interrupt latency |
| `003B:7724/77A9/79A4/7A5C` | Ordinary media workflow reaches these additional data/DMA paths; entry/return contexts retained | Exact reusable contracts and ownership |
| `003B:7647/76BC` PIO alternatives | Direct byte-level decoding confirms input pointer/count loops and unbounded FIFO polls | Not observed as calls in these retained workflows; do not label them dynamically qualified |
| `003B:7D2A` completion | Native entry/return contexts; static status/message/sense path | Error, unexpected phase, cancellation and timeout recovery |

The ten-byte templates observed by the native caller include:

```text
0A 25 00 00 00 00 00 00 00 00 00   READ CAPACITY
0A 28 00 00 00 00 01 00 00 01 00   READ(10), one block at LBA 1
0A 2A 00 00 00 00 00 00 00 02 00   WRITE(10), two blocks at LBA 0
```

The leading `0A` is the local descriptor count, not a byte transmitted as part of the CDB. This proves the existing native ten-byte route for ordinary commands; it does not prove Toolbox behavior.

The sender changes data selector `010A` to `02CC` before reading the descriptor. Native REQUEST SENSE demonstrates why this matters: its caller's `010A` is `02FA`, while `RW48=5F4E` denotes the template on `02CC`. The observer retains both the caller-mapped bytes and the actual fixed-page template, rather than interpreting the former as the command.

The same sender copies into `02CC:5F12`, then, for disk classification `3626==87`, ORs a shifted native target field into CDB byte 1. A Toolbox client must preserve the requested byte exactly and must not alter global disk classification simply to bypass this branch.

Static waits without a local timeout include `7592`'s REQ/command waits, the FIFO loops at `7684` and `76EC`, and completion waits beginning `7D2C/7D44/7D5E/7D79/7D93`. The PIO `7B14` and completion `7D2A` paths also disable interrupts locally. An outer timeout cannot make a non-returning inner loop safe. The existing 35-byte INQUIRY request also cannot retrieve the extended BlueSCSI identity unchanged.

**Design constraint:** adapt the relevant bus operations into an isolated, bounded client. Every poll must check a qualified deadline and relevant phase/error conditions; DATA IN must report actual bytes, including short/empty responses. Keep vendor CDB bytes exact and restore shared native state. The experiment below qualifies a limited guest implementation; interruption policy, full command coverage and bus recovery remain research tasks.

### Guest transport experiment and executable placement

The private v4 OS changes the lower candidate and an eight-byte hook at fetch `0181:9040`. Ordinary Disk → Save System enters CRT screen index `0112`, descriptor data `023F:B22A`, whose first callback reaches that hook. The earlier static lead `0181:AEA6` was not reached; that exploratory run is excluded. The hook calls the diagnostic, then replays the two displaced `LD` instructions and continues the original callback. An unpatched-OS negative control produces no probe result. No host writes to guest RAM, registers or PC establish the acceptance state.

| Experimental component | Mapping / measured size |
| --- | --- |
| Executable code | Fixed-low fetch page `000F`, logical `013E..04EB`, physical `003D3E..0040EB`; 942 bytes |
| Transaction and helper portion | Logical `02AC..04EB`; 576 bytes of that total |
| Fourteen case records | Data page `000F:5000`, physical `004C00`; 336 bytes |
| Results | Data page `000F:5400`, physical `005000`; 1,344 bytes |
| Control words | Data page `000F:5FF0/5FF2`, physical `005BF0/005BF2` |
| Stack growth | 84 bytes inside the helper, 86 including the hook's call |

The v4 image SHA-256 is `5161b0b72dc79bc219d5911175d2339b20faee3ba92e527f3626b332c17fd1f6`. The validation reconstructs every changed byte from the original and checks all 325 decoded instructions. The diagnostic footprint is not a size estimate for the full client, browser or WAV importer. All four runs preserve code/table bytes across boot, probe return and subsequent HDD Load/playback; the complete 8,002-byte candidate is unchanged between the three post-probe snapshots in each run. This adds executable-path evidence without establishing complete ownership.

| Case | Observed native result |
| --- | --- |
| TEST UNIT READY | GOOD, zero data, completed message |
| Byte-sensitive READ CAPACITY | All ten bytes `25 A5 5A 12 34 56 78 9A BC DE` reach the command phase unchanged; eight response bytes `00004FFF00000200` |
| Short INQUIRY | Three bytes returned into a 64-byte-capacity buffer, followed by GOOD |
| Out-of-range READ(10), then sense | CHECK CONDITION retained; separate 18-byte sense has key `05`, ASC/ASCQ `21/00` |
| REQUEST SENSE allocation zero | Status-only GOOD without a mandatory data read |
| Absent target 5 | Distinct selection-failure outcome, no CDB sent |
| Eight-byte response into capacity three | Stops after three bytes and returns capacity failure |
| Deliberately held initiator ACK | Inactivity deadline exits at 5,010–5,011 TIMER1 ticks; a separate eight-poll case exits at 165 ticks |
| Commands after errors | TUR and READ CAPACITY succeed |
| Unsupported opcode, then sense | Final build returns CHECK CONDITION and key `05`, ASC/ASCQ `20/00`; the baseline incorrectly returned GOOD |

The sensitive CDB deliberately contains reserved/nonzero fields ignored by this emulator: it proves byte preservation, not valid physical READ CAPACITY semantics. Holding initiator ACK creates a guest-controlled non-progress condition; it is not an independently faulted target. Every retained case ends with model PSNS zero. Cleanup releases ACK/bus, clears transfer count/PCTL and acknowledges INTS through a finite path; no controller reset or SCSI bus reset is tested.

Read-only entry/exit taps show all 114 observed general-register words, the 48-byte native target-state region and unrelated selectors restored exactly; data selector `010A` returns to the caller's `02FA`. The saved PSW/window/mask frame is preserved. PUSH/POP tap timing accounts for the observed two-byte SP difference; this is not a stack leak. Maximum gap between TIMER1 reads is below 201 microseconds. One ordinary-input replay crosses a timer wrap **inside** the held-ACK deadline case and still exits correctly. The helper accumulates elapsed time in two words, checks the high word before expiry can overflow, and maintains an independent finite poll budget.

The final 14-case sequence masks interrupts for **20.32825 ms** (the 13-case baseline takes 18.181625 ms). This is a measured limitation, not acceptable UI/MIDI latency. At that checkpoint, cancellation, DATA OUT, 4 KiB transfers, independently stuck targets, unexpected-phase injection, sense failure, interrupt cooperation and actual Toolbox commands were unqualified. The follow-ups below add scoped full-transfer and interrupt evidence. [Detailed contract and remaining cases](bluescsi-transport-contract.md).

### Full-buffer and command-error follow-up

The v5 private image extends the same ordinary callback with full DATA IN/OUT.
Its code occupies 1,029 bytes at fixed-low `000F:013E..0542` (physical
`003D3E..004142`). The 4 KiB buffer is data `000F:4800..57FF`, physical
`004400..0053FF`, with guard words immediately before and after it. The 384-byte
case table begins at data `5804`, the 512-byte results area at `5A00`, and control
words at `5FF0`. These regions fit this diagnostic; complete browser/importer
placement and concurrent buffer lifetimes remain unqualified.

The image SHA-256 is
`579fdefbaaf9487a2bd796690876ecdb4703dfca0094b6036b43701c0ea218f7`.
The previous prototype's red trial stops a 4 KiB read at 258 bytes on its 20 ms
deadline and rejects DATA OUT. The new experiment uses a 1,048,576-tick total
limit with finite inactivity/poll guards. It transfers exact 4 KiB payloads and
retains error status separately from sense for unsupported opcode, invalid START
fields, out-of-range WRITE and protected-CD WRITE. The corresponding sense is
`05/20/00`, `05/24/00`, `05/21/00` and `07/27/00`; these failures transfer zero
data bytes. [Complete error contract](bluescsi-transport-contract.md#full-buffer-and-deliberate-error-matrix).

One successful WRITE changes exactly one 4 KiB range in a generated 16 KiB HD2
fixture. Full media captures after every case prove no other changes, including
after a capacity-limited 4,095-byte WRITE. This staging behavior is specific to
the emulator; physical rollback must not rely on command-level write atomicity.
The generated CD1 fixture verifies raw protected-write/read behavior, not native
Roland CD Load. Both guards, unread buffer tails, caller registers/target state
and the complete post-probe candidate contents survive. The final ordinary HD0
Load/audition retains 13 samples / 119,808 exact bytes, silent release and
byte-identical exported HD0 content.

The six long transfers cross 28 timer wraps; elapsed counts agree with machine
time within one tick per case. Measured stack growth is 82 bytes inside the
helper and 84 with the hook; the larger fourth-checkpoint stack result included
an extra nested held-ACK test path absent here. Full commands take about 295–297
ms, and the entire sequence masks interrupts for **1.897658 seconds**. This
proves the need to resolve interrupt servicing before production use. The
extended deadline is an experiment setting, not a solution to responsiveness.
The [fifth evidence record](../condensed/validation/bluescsi-transfer-errors-2026-10-18.json)
contains all 16 case captures, 99,356 timer-read and 58,201 SPC-write summary
checks, selected raw rows and the hash of the complete private trace.

### Interrupt-cooperative transfer follow-up

The new helper adds service points during buffer preparation and every 64 budget
polls. It saves transport scratch, returns the data bank to the native mapping,
restores the caller's interrupt masks and conditionally enables interrupts, then
restores the workspace mapping and scratch. Native IRQ-owned state advances
normally. The native SCSI/DMA interrupt source stays masked while the probe owns
the controller; the caller's full IC4 mask is restored on exit. The byte audit
and native/physical distinction are in the [interrupt contract](bluescsi-transport-contract.md#interrupt-cooperation-follow-up).

The final image SHA-256 is
`60150c60db8347b0ba9cf1a03c23b30aa4ec403a72c45a2fdc8b2c97b218d0b0`.
Its 1,333 code bytes occupy `000F:013E..0672`, physical `003D3E..004272`;
the 480-byte case table and 640-byte results area remain separate from the
guarded 4 KiB buffer. The first two fresh runs pass 16 cases; the final run
adds held-ACK timeout, absence, poll exhaustion and a successful command afterward.

All **20 final cases pass**, with 1,800 service points, 169 timer interrupts,
123 normal timer-0 rearms and six ordinary MIDI bytes handled and consumed.
The sequence lasts 2.550933 seconds, with a conservative observed masked-span
bracket of 5.018625 ms. This measured bound includes extra enabled time and
applies only to the tested muted Save System workload. TIMER1 sampling gaps
remain below one wrap (17.291125 ms maximum, including buffer preparation).
The held-ACK timeout exits at 5,016 ticks while servicing an interrupt;
the eight-poll exit takes 178 ticks and absence 23 ticks. Exact CDB/payloads,
original error/sense, guards, scratch media and caller transport state pass.

The final run observes every stack write and measures 180 bytes including the
hook; an earlier instrumented run measures 184, and the first run samples a
186-byte path. Full worst-case stack and ISR bounds remain open. Original OS
timer counters and MIDI state legitimately change; they are not incorrectly
restored to entry values. Four final snapshots retain code/table and complete
post-probe candidate contents. Ordinary HDD Load/playback afterward preserves
13 samples / 119,808 exact bytes, silent release and byte-identical exported
HD0 content. This is not concurrent audio, dense MIDI, responsive UI,
cancellation, physical interrupt routing or complete memory-ownership acceptance.

### Ordinary panel cancellation follow-up

The private helper now reads the normal four-row `F00A` panel scan while masked,
using row 1's active-low Exit bit. The original `003B:4320..4366` scan bytes and
native input mapping support this model-only path. It writes no native event
queue or button-history fields. The first press latches in extension-owned
state; the current command drains with existing deadlines, then the probe skips
all later commands. Invocation entry clears the latch. This establishes a
limited cancellation primitive, not the final browser input dispatcher.

The standard private image has SHA-256
`fc082180227d8d891039a0e3defc6f4f4f8bbef661e4d4386f27800febf2dc70`.
Its 1,571 bytes / 530 instructions occupy `000F:013E..0760`, physical
`003D3E..004360`; context extends to data `5FF0..6009`. The diagnostic stall
variant has 1,596 bytes / 538 instructions. Both remain separate from the
guarded 4 KiB buffer and case/result tables. This does not establish the
browser/importer's full memory budget.

The old helper ignores Exit and continues all 20 commands, as expected in the
negative control. With the new helper, read and held-Exit write cancellation
latch at 629 bytes, finish the current 4 KiB transaction, and return cancelled
308.312/309.462 ms later. The successful scratch WRITE remains committed;
cancellation cannot mean write rollback. Panel Up does not cancel. Re-entering
through the ordinary menu after cancellation runs all 20 cases with a cleared
latch. A separate guest-held ACK after real Exit returns the timeout error in
5.050 ms rather than hiding it behind a cancelled result. This is an initiator
test stall, not an independent target fault.

All five fresh processes subsequently load/play 13 HD0 samples / 119,808 exact
PCM bytes, release to silence and export unchanged HDD bytes. Full captured
buffers/media, guards, transmitted CDB/DATA OUT bytes, service scratch and caller
banks/IC4 mask pass. The failed read has one in-flight buffer byte beyond its
608 completed handshakes; failed/cancelled payloads must not be published.
Importer publication and rollback remain unimplemented. Native model cleanup
passes; stuck-target BSY, physical ABORT/reset, other controller modes and
simultaneous target-error/cancel need further qualification.
[Detailed cancellation contract](bluescsi-transport-contract.md#ordinary-exit-cancellation).

## BS1.4: observed native stereo object and persistence

The retained 44.1 kHz stereo run produced **56,719 frames per channel**. Each channel occupies 13 allocation blocks of 9,216 bytes: 119,808 bytes per channel, 239,616 total. Known, distinct signed PCM patterns match exactly between recorded wave memory, the exported floppy and wave memory after a fresh boot and Load. Allocation padding is zero. Original input images remain unchanged.

RAM snapshots add the following object-level evidence:

- Public sample slots 0 and 1 hold separate 48-byte descriptors, at physical `0D2800` and `0D2830`. Their block bases are 0 and 13; both block counts are 13. The allocation cursor `3616` advances from 0 to 26.
- The 16-byte names end with marker `7F` at byte 14 and `L`/`R` at byte 15. This agrees with the [static partner search](../firmware/os/os-selection-refresh.md).
- Five 32-bit RAM address fields at descriptor offsets `10/14/18/1C/20` use eight fractional bits. The right-channel values are higher by `0x00EA0000`, corresponding to 13 blocks of `0x1200` words shifted left eight bits.
- On disk those fields are channel-relative; native RAM records are relocated on Load. Both reloaded RAM descriptors match their recorded counterparts byte-for-byte. The disk's allocation references must not be copied directly into RAM as if they were wave-memory block bases.
- After recording, reserved partial 255 references sample 0 at `+10` and sample 1 at `+20`; its corresponding `+14/+24` bytes are `E0/20`, agreeing with the existing opposite-channel routing interpretation. This records the bytes, not a new calibration of pan units.
- After cold Sample Load, that preview partial still has `FFFF` references until a selection workflow establishes them. Successful storage/reload therefore does not by itself demonstrate playable assignment or stereo re-selection.

### Cold-load selection and playback follow-up

A fresh stock instance loads the saved stereo floppy through ordinary Disk controls, then enters Sample → Loop/Smoothing. Read-only snapshots and MIDI note 60 establish:

- Sample Load alone leaves preview partial 255 unassigned. Entering Loop/Smoothing builds preview descriptors 512/513 and assigns both to partial 255; source slots 0/1 and their allocation cursor remain unchanged.
- With the left member selected, preview block bases are 0/13 and partial bytes `+14/+24` are `E0/20`. Selecting the right member reverses the preview block bases to 13/0 and those routing bytes to `20/E0`. Output channel order remains left/right.
- In both selection states, output L matches the recorded 257-frame pattern and output R matches the 509-frame pattern. The analysis fits a common source-frame position for both channels in each 25,000-frame comparison window. Relative RMS fit error is at most `4.02e-8`, consistent with floating-point rendering; this is implementation agreement, not a physical fidelity measurement.
- Mono audition centers the selected left or right sample with bit-identical output channels. Returning to Stereo restores the distinct pair. All five audio cases end with a full silent second after release.
- Both complete 119,808-byte channel allocations, including zero padding, still match the saved fixture. All 12 snapshots preserve the original public sample descriptors and allocation cursor 26. No guest state was forced.

This qualifies the **44.1 kHz fixture's native preview selection/routing** after cold Load. At that checkpoint the sample-rate byte was only an observed fixture value; the [later sample contract](bluescsi-sample-contract.md) now qualifies eight rate codes with separate mono controls. There is no 48 kHz import claim, permanent partial/patch-assignment qualification or rollback/exhaustion result. Arbitrary-length descriptor construction and atomic reservation/publication/rollback for both channels remain open. [Raw contexts, audio fits and reproduction sources](../condensed/validation/bluescsi-stereo-ui-followup-2026-10-18.json).

## Compatibility baseline

The separate native HDD workflow loads the existing 13-sample floppy, initializes a private 10 MiB HD0 test copy, saves the performance, exports that test image, cold boots and loads it again. It preserves **119,808 exact sample bytes**, matches the original audition's spectral peak and level, and releases to silence. Repeated exports agree; existing-output protection rejects overwriting an export. Original HDD/floppy/OS/ROM hashes remain unchanged.

This initial baseline is the existing HD0/512-byte-sector development profile. It does not cover the user's historical HDD collection, imported WAVs or physical BlueSCSI behavior.

The fourth checkpoint additionally loads that saved 13-sample HD0 fixture after each private OS probe, verifies all 119,808 PCM bytes, auditions note 60 and reaches a silent final second. Exported HDD bytes remain identical to the source. On the final emulator build, a stock-OS CD1 regression loads all 79 K4 samples / 6,054,912 allocation bytes from the full JMD image, auditions four notes, reproduces 65,536 stereo frames exactly in two cold processes and rejects a changed-CD restore. Standard native boot, pointer, MIDI, release and clean shutdown checks also pass. CD qualification uses stock OS; it does not claim that the patched probe was followed by a CD transaction.

BUG-113 initially exposed a boot-ROM dependency on the old catch-all GOOD status: `1B 00 00 00 01 00` requests START UNIT before reading the system header. The final dispatcher explicitly accepts START for already-loaded native images and rejects unmodeled stop/eject/power transitions with invalid-field sense. The supported START/IMMED fields follow the [T10 command layout](https://t10.org/ftp/t10/document.05/05-344r0.pdf); this is limited image-model behavior, not spindle or removable-media modeling. Unsupported opcodes now return per-target invalid-operation-code sense. The final regression totals and retained failed trial are in the fourth validation record.

## Reproduction and evidence limits

Run from the repository root with Python, Pillow, NumPy, pypcode, the identified native executable, and user-supplied original firmware/media. The retained probe source is in the validation JSON's `probe_source`; the analyzer is `analyzer_source`; each native instance retains its exact `observer_source`. Local drafts used a directory four levels below the repository root. Use a new output directory for each run.

```powershell
python -B docs/ic20-hle-findings/chatGPT-work/bluescsi-feasibility-2026-10-18/probe.py --workflow stereo --output docs/ic20-hle-findings/chatGPT-work/bluescsi-feasibility-2026-10-18/stereo-04
python -B docs/ic20-hle-findings/chatGPT-work/bluescsi-feasibility-2026-10-18/probe.py --workflow scsi-save --output docs/ic20-hle-findings/chatGPT-work/bluescsi-feasibility-2026-10-18/scsi-03
python -B docs/ic20-hle-findings/chatGPT-work/bluescsi-feasibility-2026-10-18/analyze.py
```

These are the recorded commands, not instructions to overwrite their existing outputs. The stereo prerequisite is a previously firmware-formatted empty 720 KiB floppy with SHA-256 `f9fce7624a8ce5c68575c52994a3f3702a43cd4f19d30e8ec8c60ad4b9b9510b`. HDD/FDD fixture identities and exact harness paths are in the validation record. Local socket permission is required by NativeRuntime. Recording duration can vary slightly with ordinary input delivery; acceptance checks the actual descriptor length and exact input pattern, rather than requiring a fixed frame count across runs.

Exploratory runs exposed an observer-handle lifetime issue and an incorrect return-attribution offset. Their affected traces are excluded. The retained stereo RAM/PCM evidence and corrected SCSI contexts are explicitly identified in the sidecar. No complete-call coverage or absence-of-access claim is inferred from capped trace examples.

The second record embeds `native_explore.py`, `probe_base.py`, `observer.lua`, the ordered command-file contents and `analyze_followup.py`. Its retained output is `stereo-selection-02`; create a fresh output directory when replaying. Native pointer coordinates are 320 by 120, while captured CRT images are 640 by 480. The first exploratory instance stopped on an invalid host pointer-Y request and is excluded. Snapshot/audio names are historical labels: the retained `stereo-enabled` snapshot and `stereo-left-selected` audio actually show the mono control, as verified by RAM and pixels. Reported acceptance uses observed state rather than those labels.

The third record embeds `native_save_system.py`, `native_cold_verify.py`, both observer/base variants, `deadline_model.py` and `analyze_memory_transport.py`. The marker formula and file range reproduce the private input from the original; the blank format destination is 1,474,560 zero bytes. Save-run commands are retained in order. Its exploratory `save-system-screen` snapshot is actually a closed menu following an outside click; `save-system-entry` and `after-format-save` identify the real workflow. Replay the recorded pointer coordinates rather than inferring a scale from screenshot dimensions. The cold harness consumes the saved-system export and earlier captured-stereo fixture; preserve those identities and use fresh output paths. No guest register, RAM or PC was forced.

The fourth record embeds the v3/v4 builders, guest harness variants, read-only Lua observer, analyzer and final device test. The final probe uses `run_probe_fixed.py --system probe-v4.img --layout probe-v4.json --output <fresh-output>` from its private directory, with paths resolved from the repository root. `build_probe.py` generates the v4 copy from the original OS. The builder's byte-diff manifest and decoded instructions make the patch reviewable without distributing original firmware. Recorded commands use `docs/ic20-hle-findings/chatGPT-work/bluescsi-guest-probe-2026-10-18`; extract sources into the same relative depth when replaying, then choose new output names. The earlier saved 13-sample HD0 fixture is an explicit prerequisite. The baseline and intermediate executables are archived privately for historical hash verification; those captures are not attributed to the final build.

Final Release/x64 native driver/link builds succeed with serial MSBuild and `/Z7`; the driver emits two existing warnings, the link none. The final full backend suite passes **561 tests, zero skips**. Four targeted device/boot/fallback checks and 27 baseline legacy checks also pass. Fifteen legacy PNGs match byte-for-byte and parsed Lua outputs agree. The initial full run's ten failures are retained: eight arose from a private runner snapshot-path mistake and two exposed START UNIT compatibility. Neither failed trial nor synthetic register fixture is counted as firmware UI acceptance.

The fifth record embeds `build_transfer.py`, its retained red variant,
`run_transfer.py`, `probe_base.py`, `observer.lua` and `analyze_transfer.py`.
Run the builder with `--output <fresh-image>`, then the harness with `--system`,
`--layout` and `--output <fresh-run>`. The recorded private directory is
`bluescsi-transfer-probe-2026-10-18` at the same four-level depth. The harness
generates deterministic scratch HD2/CD1 inputs and copies the earlier saved HD0
fixture; observers only read guest/media backing state. The analyzer verifies
every transmitted CDB/DATA OUT byte, complete captured buffers/media, caller
state, timer arithmetic, patch bytes, decoded instructions and source hashes.
No emulator/source rebuild or repeat of its already-passing full suite was
needed for this private-firmware experiment.

The sixth record embeds `build_transfer.py`, `build_interrupt20.py`, the input
harness/read-only observer and analyzers. The final builder takes
`--output <fresh-image>`; the harness takes `--system`, `--layout` and
`--output <fresh-run>`. Its private directory is
`bluescsi-interrupt-probe-2026-10-18` at the same four-level depth. The record
retains earlier passing run identities and an observer-only setup failure
(misaligned tap range, corrected before guest testing). No vectors, guest
registers or guest events were forced. Screenshots confirm return to Save System
and subsequent normal Perform Play; the same exact HDD/audio checks pass in
all three fresh processes. The existing 561-test result remains historical.

The seventh record embeds the standard/diagnostic builders, read-only observer,
`run_cancel.py`, timeout/re-entry variants and independent `analyze_cancel.py`.
The private directory is `bluescsi-cancel-probe-2026-10-18` at the same depth.
The observer signals a host file after 256 guest data handshakes; the host then
sends ordinary panel input through NativeRuntime. An initial host notification
race is excluded and corrected with atomic rename. No guest state is forced.
Recorded commands require fresh outputs and the same HD0 fixture; scratch
HD2/CD1 media are generated by the harness. Existing runtime/source hashes and
the earlier 561-test build remain unchanged.

## Next checkpoint

1. Close code/RAM ownership beyond the qualified sampling/session/seeded-initialization workflows: indirect users, nested UI/LCD/GB-6 and the complete code/UI footprint. Validate the proposed shared-buffer relocation against the 4,928-byte local budget and bound the separate native stack allowance.
2. Extend idle interrupt cooperation and Exit/drain behavior to relevant workload/input/stack bounds, then qualify independently injected transport faults against the [contract](bluescsi-transport-contract.md). Qualify recovery and ordinary HDD/CD operations after each relevant exit. Physical abort/reset and importer publication remain separate from the successful native cancellation primitive.
3. Extend qualified Load/Save, active-owner menu and manufacturer41 session interoperation to remaining entry/cancel boundaries; decode the local mouse-cancel dispatch; BUG-125 now preserves early receive rollback ownership, while remaining local preparation/cancel timing still needs qualification after the experimental BUG-123 remote recovery and BUG-124 local ownership repairs, then implement a bounded writer with a qualified WAV endpoint/padding policy. BUG-118/119 now have tested private OS header guards through cancellation, publication and invalid-slot error cleanup; BUG-120 also rejects outgoing requests during receive ownership while preserving idle sends. BUG-121 adds active-sender exclusion, exact completion/explicit cancellation, and stale-handshake rejection during a subsequent receive. BUG-122 repairs local completion/cancellation cleanup, with bank preservation after the UI call. BUG-123 now adds a foreground remote owner and native-qualified header/data timeout and Exit recovery. BUG-124 guards local entry and holds ownership through UI cleanup; the final-packet/header race no longer leaks an allocation. These guards remain narrower than the importer's complete owner. The native SDS writer exceeds its reservation and is not directly reusable. Complete importer-driven initialized/named object creation and transactional stereo allocation/cleanup, including pre-supervisor cancellation, timeouts and resource exhaustion. Metadata, ordinary permanent assignment and native mono header admission have scoped evidence; the SDS single saved cursor cannot supply pair-wide rollback through two independent calls.
4. Complete CRT/LCD entry bounds and controller integration, then issue the BS1 PASS/REVISE/BLOCKED decision against the full gate.

No final feasibility decision has been issued at this checkpoint. The remaining work is concrete research, and BS2–BS6 remain unstarted.


### Combined diagnostic placement (checkpoint25, 2026-10-18)

The twenty-fifth checkpoint qualifies a combined diagnostic layout in the native emulator. The old 4 KiB transport buffer overlapped the SDS helpers by703 bytes. Relocating the buffer to physical004940, the480-byte case table to0046C0 and640-byte records to005944 removes that collision. All20 transport cases pass, including expected status/sense errors and timeout recovery. A separate panel Exit run latches cancellation after629 bytes, drains the current4096-byte read and starts no later command. Both runs subsequently load13 HDD samples with all119808 PCM bytes exact and pass playback/silent release. Eight RAM snapshots preserve all code, SDS patch spans, the case table and354 seeded gap bytes. This qualifies coexistence for these workflows; SDS cancellation/retry execution after transport remains to be tested. Retained code is2402 bytes; the production budget still leaves only672 arithmetic bytes, with browser UI, WAV parsing, stereo transactions and full stack bounds unmeasured. BS1 remains OPEN. [Evidence](../condensed/validation/bluescsi-combined-layout-2026-10-18.json).


### Post-transport receive rollback (checkpoint26, 2026-10-18)

Checkpoint26 qualifies SDS receive cancellation and retry in the same native session after the combined transport diagnostic and HDD Load. One run executes all20 transport cases; another cancels the first read after629 bytes and drains it safely. A third run uses the prior SDS-only image without the diagnostic as a comparison. All three load13 samples, then show actual header admission (cursor13 to14), receive cancellation stateFE, rollback at0166:8B6B to13, and idle before retry. Cancellation-to-idle spans1.995390�1.996954 seconds in these runs. Retry reserves block13 and publishes the fourteenth live sample with160 exact received PCM bytes. All119808 existing HDD PCM bytes and13 descriptors remain exact; preceding playback/release and unchanged HDD export pass. The16 combined-image snapshots preserve all patch spans, code, case table and354 seeded gap bytes; the comparison adds seven snapshots. An initial exploratory two-second assertion caught FE after rollback but before cleanup ended; it is not an acceptance pass or evidence of a leaked allocation. The repeated traced runs establish cleanup and retry; the final cancellation run allows four seconds. No firmware repair was needed for this timing assertion. BS1 remains OPEN for full code/UI/WAV sizing, stack bounds, bounded sample writing and atomic stereo publication/rollback. [Evidence](../condensed/validation/bluescsi-combined-lifecycle-2026-10-18.json).


### WAV reference and native-loader reuse (checkpoint27, 2026-10-18)

Checkpoint27 adds an executable host reference for the WAV-specific contract, with39 passing tests. It validates little-endian RIFF/WAVE, one fmt and one nonempty data chunk in either order, PCM16 mono/stereo, rate codes, block alignment, byte rate, chunk extents and odd-byte padding. Unknown chunks are skipped without reading their payloads; optional root/loop metadata is not interpreted. Duplicate fmt/data chunks, partial frames, unsupported encodings and truncation reject. Bytes outside the RIFF extent are ignored; extra PCM fmt bytes are ignored after validating the first16. The candidate rate list follows all eight decoded native codes; this does not qualify stereo playback at every rate. Metadata reads are at most16 bytes and streamed PCM reads at most4096, always complete frames. Short reads, cancellation and transport exceptions stop processing. Sparse near-4GiB arithmetic and a failure between PCM blocks pass without allocating large files. This is a host specification, not firmware implementation, native allocation or a measured code fit. The existing672-byte residual budget remains unproved.

The next reuse investigation must follow the ordinary SCSI disk Load path: identify callable allocation/descriptor and wave-transfer services, their register/bank inputs, write bounds and error cleanup. Reuse qualified native services where possible rather than duplicating them. The separate remote SCSI sample-transfer handler is not evidence for an ordinary disk-loader ABI. The SDS fixed-packet/zero-fill writer remains excluded because its writes can exceed reservation. WAV parsing and interleaved stereo conversion remain format-specific; publication still requires a pair-wide ownership contract.

[Reference](../../scripts/bluescsi_wav_contract.py), [tests](../../tests/test_bluescsi_wav_contract.py), [evidence](../condensed/validation/bluescsi-wav-contract-2026-10-18.json).


### Ordinary SCSI loader reuse (checkpoint28, 2026-10-18)

Stock HDD loading now supplies thirteen observed native DMA transfers and allocation updates, with119808 exact PCM bytes and playback intact. The destination/count setup and descriptor relocation are concrete reuse candidates; direct-call ABI, caller ownership, RAM-to-wave support and bounded failure handling remain open. Stereo WAV still needs deinterleaving. [Reuse contract and next steps](bluescsi-loader-reuse.md).


### RAM-to-wave reuse boundary (checkpoint29, 2026-10-18)

Seventy byte-checked instructions establish fixed-source/full-block wrappers and an unbounded inner DMA wait. Reuse the native DMA mechanism with a validated, bounded adapter; unchanged wrappers do not meet the4096-byte buffer contract. Stereo deinterleaving and atomic publication remain separate. Next: private guest adapter and exact write-extent/sentinel qualification. [Helper contract](bluescsi-loader-reuse.md#ram-to-wave-helper-boundary). BS1 remains OPEN.


### Native bounded-write diagnostic (checkpoint30, 2026-10-18)

Checkpoint30 runs a private guest RAM-to-wave adapter through the ordinary Save System callback after HDD Load. Three successful copies of2,4094 and4096 bytes match exactly. Six cases reject zero, odd and oversized lengths, source overrun, destination overrun and cancellation before launch. Each case checks its complete8192-byte destination/sentinel region:73728 exact bytes total. The DMA log matches18 initialization writes plus exactly three accepted payload writes; rejected cases perform no payload DMA. All119808 existing HDD sample bytes remain exact, the disk export is unchanged, and playback/release before the diagnostic passes.

The adapter occupies145 bytes for validation and80 for setup/polling, inside a1305-byte diagnostic harness. It uses the4096-byte RAM workspace at physical004940, explicit byte counts and word destinations in a fixed high-word1 test arena. Count polling is capped at256 iterations. These are prototype sizes, not a production32-bit API or combined browser fit. Interrupts remain masked during this diagnostic; no realtime responsiveness is claimed. Timeout return does not prove DMA abort/quiescence, and this run exercises neither stalled DMA nor cancellation after launch. Allocation ownership and atomic stereo publication remain open.

BUG-126 affected the first diagnostic image: results at005900 overlapped the source tail and were overwritten by later pattern fills. The observed first result64028 fails acceptance. V2 places results at005A00 and the marker at005AF0; all nine cases then pass. This fixes a private harness layout error, not original firmware. The accepted image SHA256 is89bccdd29734d10dd1e3fa80c0144e848c7bc21f9cdb880f06f5b1043843c0ac. Original firmware is unchanged. Next: generalize channel-address bounds, perform deinterleaving with distinct L/R fixtures, and qualify ownership/abort before integrating this adapter. BS1 remains OPEN. [Evidence](../condensed/validation/bluescsi-wave-adapter-2026-10-18.json).


### Native menu reuse (checkpoint31, 2026-10-18)

Seven native UI captures identify screen descriptors and callback resources. The CRT menu shows nine rows and reuses existing panel navigation. Its local resource span is268 bytes plus a4-byte index entry; this is not the full transitive cost or a browser estimate. Reuse native presentation/input with browser-owned bindings; native Disk action dispatch must remain separate. [Contract and next tests](bluescsi-ui-reuse.md). BS1 remains OPEN.


### Relocated native menu clone (checkpoint32, 2026-10-18)

Checkpoint32 qualifies an isolated relocation of the native Disk menu resource. The private image redirects index00F4 to000F:8150 (physical003D50), copies268 bytes and relocates ten internal resource pointers. Callback target/page pairs and labels remain native and unchanged. No rendering or input code is added. The image SHA256 is8c8fb7acadbfcb7e70bed86ead11b16869439cfb29abf14ed62012ce80a18e56. This placement is diagnostic only and overlaps the separately tested transport code; it is not a combined-image placement.

Two ordinary-input runs enter the relocated menu three times each, navigate with Panel Down/Exit, open Disk Load and Save System, and return to Perform. Seven snapshots in the traced run preserve both16-byte guards and the original268-byte resource. Its initial menu crop matches stock pixels exactly. A held0.2-second Down advances to Save in the first run and Copy in the repeat; differences in the repeat crop are confined to the changed selection rows. This is navigation evidence, not one-step key-repeat or full input-parity qualification.

The initial expectation that the clone would remain byte-identical was false: native exit copies six state bytes into geometry offsets10..15 (clone logical816B..8170). Eighteen masked stores from0000:DC6C account for three such copies. Replaying those stores reconstructs every traced snapshot exactly. This is expected native resource mutation, not a confirmed firmware defect. Browser geometry/state must therefore have private writable storage; sharing all resource tables as immutable would be unsafe.

The result demonstrates native menu rendering/input reuse with268 resource bytes and a changed index entry, not a completed browser or a full code-size saving. Existing Disk actions were intentionally retained for this clone; new browser rows still require dedicated callbacks. LCD/GB-6,100-entry scrolling, callback register/bank restoration and integration into the shared memory budget remain open. Next: replace a diagnostic binding with a harmless browser-owned callback and qualify dispatch/return before adding file-list behavior. BS1 remains OPEN. [Evidence](../condensed/validation/bluescsi-ui-clone-2026-10-18.json).


### Private callback dispatch (checkpoint33, 2026-10-18)

Checkpoint33 replaces only the first binding of the private relocated Disk menu with a36-byte diagnostic callback at000F:8300. Its only application effect is incrementing an owned word at physical005AF0. The callback saves/restores flags viaPUSHA/POPA, RW44 and data selector010A, and returns normally; all12 instructions round-trip decode. The accepted image SHA256 iscb2610f13f4d8376b78ac87530c05fe861486b18051b6712e9d44dd672621b54. Existing labels remain unchanged solely for this isolated diagnostic.

Two ordinary mouse selections produce counter sequence0,0,1,1,2,2,2 across seven captures. No00F6 Disk Load screen is entered; the menu remains active after the harmless callback. Exit, unchanged Save System selection and return to Perform work. Entry-after-save and return observations match all228 working register bytes (RW1C..FE), WSR and all eight bank selectors for both calls, including restored010A=02FA. The entry tap occurs afterPUSHA, so itsPSW is already masked: exact pre-call flags are not a dynamic claim. The observed10FA/1104 stack pointers reflect memory-access phases, not a complete frame-depth proof.

All seven snapshots preserve callback code, menu resources outside the six known mutable geometry bytes, original menu resources and sentinel guards. This demonstrates custom action dispatch through reused native menu rendering/input without invoking the old Load operation. It does not yet qualify safe browser state ownership, panel activation, LCD/GB-6,100-entry scrolling or a combined memory layout. Next: a browser-owned menu label/state and native list/scroll contract, retaining separate callbacks and explicit cleanup. BS1 remains OPEN. [Evidence](../condensed/validation/bluescsi-ui-callback-2026-10-18.json).


### Bounded stereo writes (checkpoint34, 2026-10-18)

Checkpoint34 qualifies guest-side stereo deinterleaving and bounded planar writes in an isolated native diagnostic. One4096-byte workspace holds2048 interleaved input bytes at physical004940,1024 left-channel bytes at005140 and1024 right-channel bytes at005540. The guest generates distinct16-bit left/right sequences, splits at most512 frames, and uses the bounded DMA adapter for each channel. Cases1,511,512 and513 frames preserve channel identity and sequence;513 requires512+1-frame chunks. All6148 payload bytes match exactly, including the two-byte-per-channel final tail. Ten payload DMA events match the expected source, destination, order and lengths.

Eight complete8192-byte channel/sentinel arenas match (65536 bytes), including every byte outside each payload. The13 previously loaded HDD samples retain all119808 PCM bytes, the HDD export is unchanged, and pre-diagnostic playback/release passes. No original firmware changed. Image SHA256:23a53f004a929af9120671464d05138ec40577947a41bd89e5ef58e7edf76e57.

The splitter measures32 code bytes, validation145 and DMA setup/polling80, totaling257 for these prototype pieces; the full diagnostic harness is1503 bytes. A conditional addition to the earlier2402-byte retained-code budget leaves415 of the3074-byte ceiling before parser, production ownership, publication and UI costs. This is a warning about the tight budget, not a linked fit measurement: the transport diagnostic still includes removable test code and these images are separate. The splitter assumes1..512 frames from its diagnostic caller; a production caller must validate that precondition. This design reads at most2048 PCM bytes per refill, within the reference parser's4096-byte maximum.

This closes only the bounded stereo write-path subcheck. Input is guest-generated, not read from WAV/BlueSCSI; destinations are test arenas, not native reserved/public samples. It does not prove stereo playback, pair-wide allocation, publication, rollback or cancellation between channels. Interrupts are masked, and physical DMA abort/quiescence remains unqualified. Next BS1 work is pair-wide ownership/reservation and right-channel failure rollback with descriptor publication held until both channels succeed. UI/code-reuse exploration remains deferred. BS1 stays OPEN. [Evidence](../condensed/validation/bluescsi-stereo-write-2026-10-18.json).


### Pair reservation and pre-publication rollback (checkpoint35, 2026-10-18)

Checkpoint35 qualifies pair-wide reservation and rollback before publication in a private native guest diagnostic. After ordinary HDD Load supplies13 samples, each attempt captures the original cursor and mirrors once, checks native free block capacity, and advances3616 plus the used-block mirror by two. Three attempts produce the observed sequence13->15->13, repeated three times. A65535-block request rejects without changing the native capacity or reserving storage. The retry therefore reuses blocks13/14 without a leaked allocation.

The left channel writes1024 bytes. Case1 then rejects an odd1025-byte right write; case2 cancels before the right write; case3 completes both1024-byte writes but deliberately rolls back without publication. Four read-only case captures verify the expected18432-byte pair region, all512 public48-byte descriptors unchanged, both allocation mirrors restored, native SDS backup1FA0 unchanged and all119808 existing PCM bytes exact. Unwritten right-channel bytes retain the sentinel. HDD export is unchanged and pre-diagnostic playback/release passes. The guest, not the host observer, performs the reservation and restoration.

The scoped reserve helper is43 bytes and rollback16 bytes inside a1450-byte harness. It checks a known13-block fixture and writes dedicated one-block channel extents; this is not a general slot allocator or complete32-bit address API. Interrupts are masked for the entire callback, so ownership is synchronous. Keeping an importer owner across interrupt/input service remains unqualified. No descriptor is constructed or published, and no in-flight DMA is aborted. The result establishes rollback before publication after right-channel rejection/cancellation, not atomic stereo import. Next: qualify safe staging/publication of the pair and its native object relationships, then interrupt-serviced ownership and combined size. UI reuse remains deferred; BS1 stays OPEN. [Evidence](../condensed/validation/bluescsi-pair-rollback-2026-10-18.json).


### Staged stereo-pair publication (checkpoint36, 2026-10-18)

Checkpoint36 qualifies staged descriptor publication for a known native stereo template in an isolated guest diagnostic. It checks that public slots13/14 are empty, reserves26 blocks together (cursor13->39), copies the recorded pair into a private96-byte staging area, and rebases all ten32-bit fixed-point addresses by13 blocks. Allocation bases become13/26, counts remain13 each, and names retain the native7F,L/R suffix. All five points of each descriptor fall inside its reserved channel extent. This uses the recorded44.1kHz/root60 descriptor defaults; it does not construct arbitrary WAV metadata.

The guest writes239616 bytes of distinct deterministic channel data before copying either descriptor into public sample memory. Four read-only captures prove: staging alone leaves public descriptors and wave data unchanged; completed PCM still leaves both public slots empty; publication changes exactly the two intended48-byte records; a repeat rejects occupied slots without allocating or rewriting PCM. The cursor has one diagnostic write,39. All other510 descriptors,119808 existing PCM bytes, the SDS backup and the untouched allocation mirror remain exact. Template/staging guards pass in the corrected image. The original HDD export and pre-diagnostic playback/release also pass. Ordinary native Loop/Smoothing selection then recognizes the newly published pair through the usual partner-name mechanism; this is selection evidence, not an audition or persistence test of the new pair.

BUG-127 records and fixes a private diagnostic guard incorrectly placed inside the DMA source interval. V2 moves the template/guards to physical005A0E..005A72; staging is005B00..005B60. The final fresh run uses corrected ordinary UI coordinates and checks the full public descriptor table after selection. The accepted image SHA256 is d5df8827994664cf766d61eedd204c62817f49aad210091bd23f5e8cf08ce152; its complete diagnostic harness is1167 bytes, not a measured production publication footprint.

Interrupts remain masked across reservation, writes and publication. This protects the two sequential descriptor copies from ordinary CPU interrupt readers in this experiment; it does not establish a resumable importer owner, arbitrary reader exclusion or real-time behavior. Fixed slots and template-sized allocations leave free-slot scanning, general metadata construction, cancellation ownership, new-pair playback/Save/cold Load and complete code/RAM/stack fit open. Next BS1 work is interrupt-serviced transaction ownership and general descriptor construction with the bounded WAV writer, followed by integrated fit. UI reuse remains deferred; BS1 stays OPEN. [Evidence](../condensed/validation/bluescsi-pair-publication-2026-10-18.json).


### Interrupt-serviced pair ownership (checkpoint37, 2026-10-18)

Checkpoint37 adds explicit interrupt service to the isolated stereo publication diagnostic. Its helper saves working registers and the current data selector, restores native data banks and the caller's interrupt masks from the saved PUSHA frame, permits interrupts only when the caller originally enabled them, then masks again and restores the diagnostic context. The final native run records 493 timer IOS reads at0000:CAD2 and 34 MIDI data reads at0000:CD1F during a 6.683714-second owned interval. These counts establish service activity, not worst-case latency, stack bounds or physical timing.

A separate private owner word at physical005BF0 protects the tested SDS entry. The five-byte hook at001F:6CDD calls a low-window gate and branches to the existing CANCEL response path when owned. With System Exclusive enabled through the native System menu, incoming commands01(header),03(request) and7D(CANCEL) reach that gate while cursor3616 is39. They do not change receive state2BBA, sender stateB1AE, the saved SDS allocation cursor, the reserved pair or existing samples. All239616 generated pair PCM bytes, all119808 existing PCM bytes, guards and the complete expected public descriptor table remain exact. Ordinary selection still builds stereo preview references512/513 using block bases13/26 and opposite pan bytes.

After publication the owner word clears. A normal header then passes through the same gate, reserves one block (39->40), and ordinary SDS cancellation rolls it back (40->39); all public descriptors, including the pair, remain exact. This positive control distinguishes actual command exclusion from disabled reception. Earlier runs received MIDI bytes but had System Exclusive disabled and never exercised admission; they are excluded from the exclusion claim. Initial instruction-fetch observation attempts were also inadequate for the native fetch path; final evidence uses data/register taps.

BUG-128 fixes an error path found in the private prototype: latching ownership before a failed reservation could leave the flag set. V2 reserves while masked and latches ownership only on success, before the first service window. A guest65535-block claim rejects with cursor13 and owner0, followed by the successful26-block claim and publication. The final harness is1601 bytes, including test delays, generated PCM, capacity rejection, template publication and unused diagnostic helpers; this is not an integrated production footprint. Accepted image SHA256:62b196966a95cfa6790a871e090ea8a2c5f0c578e4fb99e6b6a2f2025ffe000b.

The result qualifies this successful publication plus these three incoming SDS commands. It does not qualify every SysEx family (including manufacturer41), all SDS commands, user Exit/cancellation during the pair transaction, DMA timeout quiescence/release, arbitrary free-slot/metadata construction or general allocation exclusion. No native foreground dispatcher runs inside the helper. Broader register/stack/interrupt bounds, physical hardware and combined transport/parser/publication code fit remain open. Next: combine owner-preserving user cancellation with pair-wide rollback, extend competing-command coverage, then integrate and measure the full implementation. UI reuse stays deferred; BS1 remains OPEN. [Evidence](../condensed/validation/bluescsi-pair-owner-2026-10-18.json).


### Panel cancellation and pair rollback (checkpoint38, 2026-10-18)

Checkpoint38 adds ordinary panel Exit cancellation to the interrupt-serviced pair diagnostic. Three fresh native runs cancel at explicit service boundaries: before any PCM write, after the complete left channel, and after both channels but before publication. The raw four-row panel scan follows the previously qualified native Exit mapping; it latches an extension-owned cancellation word without forcing the native event queue. The callback unwinds its service/hold calls normally before cleanup.

Cleanup runs masked, checks DMA count0118 is zero and the expected allocation cursor is still39, restores the original cursor13 and both allocation mirrors, and zeroes the private96-byte descriptor staging area. A read-only capture sees owner1 after rollback and invalidation; a subsequent capture sees owner0. In all three runs, all512 public descriptors remain unchanged at cancellation, the SDS backup remains intact and all119808 existing PCM bytes are exact. Completed unpublished PCM remains in released storage; cancellation does not promise erasure. Whole368656-byte wave captures match the expected untouched/left-only/both-channel states, including every byte outside those payloads.

Each run then repeats the ordinary callback with Exit released. The cancellation latch resets, the same26 blocks are reserved again, and all239616 pair PCM bytes plus both rebased descriptors match exactly. Observed cursor writes are39,13,39 in each run. Native Loop/Smoothing again creates preview references512/513 with allocation bases13/26 and opposite pan values; the complete expected public table remains exact. Original HDD export and pre-diagnostic playback/release pass in each process. No production backend or original firmware changed, and no new defect was found.

The guest latch-to-owner-release interval is about223 microseconds in these runs. This is a native-model observation after input detection, not a bound on button-to-response latency, worst-case ISR cost or physical hardware. Timer IOS reads continue while owned. The full private harness is1882 bytes, including delays, generated PCM, fixed metadata and diagnostic helpers; it is not an integrated production size measurement. Image SHA256:be59793b78c7593e6df2cb87f5f2326dd9588e6158f55a853ec2456649cdaafc.

This closes only the tested cancellation boundaries before publication. It does not abort a DMA in flight, qualify a stalled transfer, or release ownership after an unknown DMA timeout. It does not establish cancellation after publication, simultaneous competing-SysEx/cancellation timing, every command family, arbitrary sample metadata/free-slot selection, new-pair playback/persistence, physical fidelity or complete code/RAM/stack fit. The existing ownership check is fixture-specific and cannot substitute for a general allocation lock. Next BS1 work is broader command exclusion and integration sizing, alongside the remaining WAV metadata and playback/persistence gates. UI reuse remains deferred; BS1 stays OPEN. [Evidence](../condensed/validation/bluescsi-pair-cancel-2026-10-18.json).

## BS1 decision — REVISE (2026-10-18)

The current single-region plan does not support a go to full implementation.
Its 8,002-byte candidate assigns 4,928 bytes to local data, leaving 3,074 bytes
for code, constants and UI. Measured reusable components total 2,408 bytes;
the diagnostic entry/exit wrapper adds 224 and a statically assembled RIFF
validator plus rate table adds 655: **3,287 bytes, 213 over the ceiling**.
General metadata/slot handling, file streaming, Toolbox command orchestration,
browser behavior and independent fault recovery still need code.

This is a component census, not a linked production image or minimum possible
implementation. The parser has decoded instruction/branch checks only; it has
not run against WAV fixtures. Optimization, native reuse, a smaller working
set or separately proved placement could change the result. Mono and stereo,
the 100-entry directory limit and required error/ownership repairs remain in scope.

Checkpoint 39 passes the existing stereo cancel/retry diagnostic with sustained
note/controller input: existing PCM and all descriptors survive cancellation,
staging clears before owner release, and retry publishes exact left/right PCM.
The observed stack low-water mark is 0x1022 versus post-PUSHA entry 0x10DA
(184 bytes); this is not a worst-case stack bound. Audio during ownership and
the number of sounding voices were not measured.

Checkpoint 40 establishes the sizing decision above. Checkpoint 41 audits the
recovery evidence: the emulator's Bus Release clears its own phase/PSNS directly,
so current successful cleanup cannot qualify an independently stuck target.
Physical controller/reset recovery remains open.

**Reopen BS1 for a revised design in this order:**

1. Produce an optimized integrated map and byte-counted build, accounting for
   all retained fixes and shared code/data lifetimes. Investigate native reuse
   and streaming workspace reductions before relying on another RAM region.
2. Validate the guest parser and general mono/stereo metadata construction,
   including arbitrary lengths, capacity failures and atomic publication.
3. Qualify independent target faults, cancellation/retry and stack/interrupt
   bounds; assign the physical-device checks explicitly.
4. Reissue PASS only when the complete design fits and the ownership/recovery
   contracts are justified. BS2–BS6 integration remains unstarted.

The decision is **revise the memory/implementation plan**, not abandon the feature.
See [reproducible evidence](../condensed/validation/bluescsi-feasibility-decision-2026-10-18.json).

