# BlueSCSI Files/Folders roadmap

> **Direction changed 2026-10-19:** the [image mounting plan](bluescsi-image-mount-plan.md) is the active delivery plan. It requires multiple ISO collection folders and a dedicated IMG folder, with a fixed maximum of 100 entries per folder; mounting across many folders is the open feasibility question. Direct WAV import is deferred. The status, milestones and checkpoints below describe the earlier research and remain evidence references.

**Updated:** 2026-10-19  
**Status:** BS1 decision: REVISE the current memory/implementation plan; private integrated prototype qualified in the named scope; no released browser/importer.  
**Next work:** reconcile helper reuse and final RAM/state placement; integrate general ownership/allocation and qualify permanent assignment, Save/cold Load and the browser UI.  
**Hardware baseline:** the user confirms BlueSCSI V2 and reports current firmware.

This is the active roadmap for a native S-760 Files/Folders browser and WAV importer. It supersedes the architecture and implementation sequence in the [earlier SD library-image proposal](bluescsi-sd-browser-plan.md). Milestone IDs BS1–BS6 belong to this feature and are separate from the [sampler completion roadmap](completion-roadmap.md). Creating this roadmap does not complete any implementation or hardware gate.

## Navigation

- [Current BS1 decision](#current-bs1-decision--revise-2026-10-19)
- [Milestone tracker](#milestone-tracker)
- [BS1 feasibility requirements](#bs1--feasibility-gate)
- [Qualification fixtures](#qualification-fixtures)
- [Checkpoint history](#checkpoint-history)

## Current BS1 decision — REVISE (2026-10-19)

**The smaller-buffer workaround passes scoped native tests; the full client is
not yet qualified.** Checkpoints 42–48 establish guarded 1 KiB reception,
1,536-byte stereo processing, branch compaction, guest RIFF validation and
parser/SCSI integration. The old memory-plan rejection is superseded at component
level; it is not a feature-level no-go.

The revised proposal leaves **5,634 bytes for code/UI**. A conservative measured
assembly census is now **6,009 bytes**, **375 bytes over the proposed ceiling**.
The linked diagnostic is4,507 code bytes; its final menu additionally uses268 bytes
plus the4-byte index. The census retains1,502 bytes of separate helpers/resources,
including that menu once; it may double count functions now integrated.
This conservative tally retains diagnostic overhead and is not a complete linked build.
General allocation/metadata policy, browser behavior, competing-operation ownership
and fault recovery are still incomplete. No complete fit or minimum-size claim is made.

Checkpoints67-79 qualify100-entry mixed directories,32-bit file addressing,
discovery, WAV-derived public descriptors, rollback/retry, native preview audition
and combined menu dispatch. All745 backend tests pass.
[Latest integrated evidence](../condensed/validation/bluescsi-integrated-client-2026-10-19.json).

Checkpoints 62-66 add actual directory-to-WAV integration, cancellation/retry,
missing-directory rejection and an81-command trace. All744 backend tests pass;
guest code is3,346 bytes.
[Latest directory evidence](../condensed/validation/bluescsi-directory-native-2026-10-19.json).

Checkpoints 57-61 qualify actual guest D1 commands against the native read-only
fixture, short EOF/reopen, MIDI, cancellation/retry and missing-file errors.
743 backend tests pass; fixture-disabled wave RAM matches the prior executable.
[Latest D1 evidence](../condensed/validation/bluescsi-toolbox-native-2026-10-19.json).

Checkpoints 53-56 add fixed-block boundary assembly, shared helper reuse and a
264-byte static extension-stack bound (native ISR depth remains separate).
[Latest evidence](../condensed/validation/bluescsi-block-windows-2026-10-19.json).

Checkpoints 49-52 additionally pass the combined mono/stereo data path under MIDI,
cancellation before PCM, retained stall errors and same-session retry.
See [pipeline evidence](../condensed/validation/bluescsi-pipeline-2026-10-19.json).

**Next:** link and measure those remaining functions in the revised layout, then
qualify combined ownership, independent-target recovery and stack/interrupt bounds.
Use additional placement/overlays or a ROM fallback only if the complete design
still cannot fit. Mono/stereo, 100 entries and retained error repairs remain in scope.

[Workaround evaluation and acceptance boundaries](bluescsi-workaround-evaluation.md)
· [New evidence](../condensed/validation/bluescsi-workarounds-2026-10-19.json)
· [Previous decision evidence](../condensed/validation/bluescsi-feasibility-decision-2026-10-18.json)

## Agreed direction and completion criteria

Keep existing HDD/CD images at the SD root, with their names, SCSI IDs, geometry and normal configuration intact. Add an existing `/Files` directory containing ordinary files and subdirectories. The existing Disk interface continues to use mounted images; a separate Files/Folders interface uses BlueSCSI Toolbox commands. Imported samples enter ordinary sampler memory and can be saved through the existing Roland Disk workflow.

```text
SD root/
    Existing HDD/CD images
    bluescsi.ini
    Files/
        Drums/
        Keys/
        Synth/
```

The first importer includes **both mono and stereo 16-bit PCM WAV**. Mono-only completion is not sufficient. Stereo must preserve distinct left/right channels, their common timing, and the native relationships needed for selection, playback and persistence. A mono fixture may simplify early debugging without narrowing the delivery scope.

Directory capacity is the lower of the verified target response limit and the
chosen S-760 UI/data structure limit. The current BlueSCSI profile remains
**100 entries** (files and folders together), not 100 files plus folders. The
user's possible **126-entry S-760 limit** is a separate, unverified lead; its
specific list/format and reserved entries still need evidence. Do not enlarge
the 4 KiB listing buffer or advertise 126 entries on that basis. If a reused
native widget supports fewer than 100 entries, reduce the effective limit or
revise the widget design. [BlueSCSI protocol documentation](https://bluescsi.com/docs/Toolbox-Developer-Docs).

The feature is complete when the same patched OS can browse, import, play, save and reload the qualified mono/stereo fixtures on the native emulator and physical S-760/BlueSCSI setup, while previously machine-saved HDD images remain readable and writable. Hardware and emulator acceptance must be reported separately until both pass.

### Scope boundaries

- Pursue an OS-disk-only extension first. A boot-ROM change is a contingency requiring a specific demonstrated constraint and a revised design; it is not currently a prerequisite.
- Use stock BlueSCSI commands. No custom BlueSCSI firmware or SD filesystem parser in the S-760 is planned.
- Keep ordinary SCSI disk identity and save destination separate from browser target/path/file state. Restore shared transport state on success, cancellation and error.
- Initial browser operations read files. Directory selection uses SCSI DATA OUT but does not upload sample content. SD file writing/export, deletion and formatting are separate future features.
- Opening image files inside the browser, image switching and a virtual-disk loader adapter are deferred. Existing mounted HDD/CD access continues through the current interface.
- Initial WAV container scope is RIFF/WAVE, integer PCM format 1, 16 bits, one or two interleaved channels. Compressed audio, floating point, 24-bit conversion, more than two channels, RF64, AIFF and automatic resampling are deferred.
- Freeze the supported source-rate list and its native metadata encoding in BS1.4. Include 44.1 and 48 kHz in qualification; assess the other native rates there. Reject unsupported rates explicitly; do not silently change pitch, resample or downmix.
- Freeze naming, root-key, loop-metadata and patch-assignment behavior in BS1.4. Unsupported optional metadata must have a documented fallback; unsupported audio encoding must not be treated as PCM.
- Reuse native drawing/input services with dedicated browser descriptors and callbacks. Separate source modules are compiled into the OS image; loose UI files on the SD card are not an established firmware mechanism.

## Milestone tracker

| ID | Milestone | Status | Dependencies | Exit evidence |
| --- | --- | --- | --- | --- |
| BS1 | Feasibility gate | REVISE — smaller-buffer mechanisms pass; complete integrated fit and recovery remain open | None | Code/RAM ownership, callable contracts, UI entry and stereo import design support a concrete implementation |
| BS2 | BlueSCSI emulator target | IN PROGRESS - discovery and D0/D1/D2/D9 profile qualified; physical parity open | BS1 for final integration; fixture/spec work can proceed independently | Qualified command model and ordinary-SCSI regression results |
| BS3 | Native OS Toolbox client | IN PROGRESS - guest discovery/read/public prototype qualified; general client/physical open | BS1, BS2 | Real guest command traces and matching physical file bytes/recovery |
| BS4 | Native Files/Folders UI | IN PROGRESS - reused menu dispatch qualified; browser absent | BS3 | CRT/LCD browsing, input, cancellation and Disk-state restoration |
| BS5 | Mono and stereo WAV import | IN PROGRESS - scoped public samples/audition; general lifecycle open | BS1.4, BS3, BS4 | Correct PCM, native objects, playback and failure cleanup for both channel modes |
| BS6 | Compatibility and release qualification | NOT STARTED | BS2–BS5 | Existing-media and new-import workflows pass on emulator and hardware |

Ordinary-disk regression checks begin with the first transport change; they are not postponed until BS6. No calendar estimates are committed before BS1 passes.

## BS1 — Feasibility gate

**Purpose:** replace promising addresses with a bounded implementation design. A static disassembly lead, blank RAM region, or successful protocol mock alone cannot pass this gate.

### BS1.1 — Prove code and working-memory ownership

- [x] Record immutable OS/ROM hashes and the intended controller-patch baseline, including any GB-6 integration. Keep all experimental images separate from originals. — 2026-10-18: stock Mouse+CRT research baseline; selectable GB-6 v9 integration remains separately qualified. See [baseline identities and scope](bluescsi-feasibility.md#baseline-and-method).
- [x] Test initial fill-region assumptions against ordinary native workflows and record observed exclusions. — 2026-10-18: CPU writes and DMA-sensitive snapshots initially exclude six candidate ranges; follow-up UI ownership excludes the upper tail, leaving one unqualified lower candidate. See [memory evidence](bluescsi-feasibility.md#bs11-memory-exclusions-and-remaining-candidate).
- [x] Bound the existing upper-tail UI storage users. — 2026-10-18: three CRT backup slots, accepted LCD save extents and the conditional last-page clear are byte-checked; the tail is excluded as permanent extension storage. Maximum nesting is static evidence, not complete dynamic coverage. See [screen storage](../firmware/os/os-screen-backup-storage.md).
- [x] Test lower-candidate persistence through boot, native Save System and cold Load/playback using a private data marker. — 2026-10-18: all 8,002 bytes survive 11 snapshots and the saved-system export. This is a scoped lifetime result, not a free-space reservation; mutable bytes must be initialized after boot. See [marker evidence](bluescsi-feasibility.md#lower-candidate-marker-and-save-system-follow-up).
- [x] Execute a limited guest diagnostic from the lower candidate through an ordinary callback and measure stack/placement. — 2026-10-18: fixed-low page `000F`, 942 code bytes, 86 stack bytes with hook; code/table and post-probe candidate contents survive subsequent HDD Load/playback. This does not close complete ownership or full-client sizing. See [guest experiment](bluescsi-feasibility.md#guest-transport-experiment-and-executable-placement).
- [x] Qualify the seeded candidate through native sampling and same-build session restore, then execute the existing helper from seeded workspace. — 2026-10-18: three sampling/restore/cold-load processes and a fourth 20-case transport/HDD process pass; only declared probe data ranges change. Physical-device state synchronization is not covered. See [lifetime evidence](bluescsi-memory-contract.md#native-lifetime-evidence).
- [x] Separate local-data and native-stack accounting and enumerate a proposed address layout. — 2026-10-18: 4,928 local bytes plus an unproved 512-byte stack allowance; 3,074 bytes remain for code/UI/constants. The arithmetic map and shared-buffer ownership rules are proposals, not a reservation or implemented relocation. See [memory budget](bluescsi-memory-contract.md#corrected-budget-and-proposed-placement).
- [ ] Identify code, descriptors, constants and mutable-buffer locations with physical extents, fetch/data selectors, boot-loading coverage and lifetimes.
- [ ] Audit existing readers, writers, initialization, DMA, interrupt use and aliases for each proposed region. Verify critical ownership assumptions using native observations of ordinary workflows.
- [ ] Size the complete code/UI/constants, native-call scratch and stack against the proposed memory contract. Validate shared listing/read placement, staged mono/stereo resources and initialization; the 3,074-byte code/UI ceiling is not evidence that the complete client fits.
- [ ] Complete lifecycle ownership beyond the qualified boot, sampling, Disk, Save System and same-build session workflows: nested screen changes, LCD/GB-6 integration and external-device state recovery. If overlays are proposed, document how code stays executable across calls and interrupts.

**Known exclusion:** the initial `FF` run at OS file `0x0F1BF8..0x0F47FF` overlaps physical `0x0ED712`, used by transfer/display staging. It cannot be allocated as permanent code based on fill bytes. See [transfer staging](../firmware/os/os-scsi-transfer-and-delete.md) and the [banked memory map](../condensed/01-hardware-and-memory-map.md).

#### Required workaround evaluation before the final feasibility decision (2026-10-19)

The current **REVISE** result applies to the measured single-region component
mix. Evaluating alternatives is part of BS1, not work deferred until after the
gate. The 213-byte excess is not the total saving required: the revised budget
must include every missing function and retained error/ownership repair.

- [x] Qualify a guarded 1 KiB receive window while draining the full 4 KiB response; exact bytes, errors and subsequent HDD load/playback pass (checkpoints 42–43).
- [x] Qualify 1,536-byte in-place stereo processing on 1/511/512/513-frame fixtures (checkpoint 45).
- [x] Validate compact guest RIFF code on 88 cases and link it to bounded standard SCSI reads for ten representative cases (checkpoints 46/48).
- [x] Measure branch compaction and rerun stereo cancellation/retry under input workload (checkpoint 44).
- [x] Evaluate reopen-after-EOF and 100-entry page scheduling in a host reference; guest/physical qualification remains separate (checkpoint 47).
- [ ] **Smaller streaming buffers and shared lifetimes:** determine minimum legal Toolbox response/read buffers; measure smaller WAV chunks and reuse between browsing, parsing and import. Record peak simultaneous data use, directory-state preservation or refetch, chunk-boundary behavior, transfer cost and cancellation safety. Preserve mono/stereo support and the 100-entry limit.
- [ ] **Native routine reuse:** evaluate existing menu/drawing/input, copy, sample initialization and SCSI routines. Record verified entry points, bank/register/stack contracts, clobbers, error behavior and net byte savings including adapters. UI reuse is now explicitly part of feasibility; earlier checkpoint notes deferring it describe historical sequencing.
- [x] Qualify shared context-copy reuse and ABI-based register-save reduction in the combined fixed-block pipeline; native MIDI/cancel/retry/error checks pass (checkpoints54/56). Full production cleanup remains below.
- [ ] **Production compaction:** remove diagnostic-only delays, generators, probes and redundant wrappers; share helpers where their contracts permit. Measure emitted code and constants, retaining bounded waits, accurate errors, interrupt service and atomic stereo ownership/publication/rollback.
- [ ] **Alternative placement or overlays, if the first three approaches do not fit:** prove ownership, loading, initialization and lifetime of any additional region, including calls, interrupts, Disk operations and Save System/cold boot. Record why an overlay is safe or reject it with evidence. Evaluate a boot-ROM change only as a documented fallback if the OS-only options remain insufficient.
- [ ] **Compare and select:** record each option as accepted, rejected with evidence, or unnecessary because the selected design fits. Produce an integrated byte-counted build/map with code, constants, UI, buffers, scratch and stack accounted for; report remaining margin and unimplemented pieces explicitly. No fit claim may rely on omitted functions or unverified free RAM.

The selected workaround must pass the relevant native regression and lifecycle
checks before BS1 can become PASS. Retain the parser/metadata, interrupt/stack
and independent-target recovery requirements elsewhere in BS1. A feature-level
no-go requires evidence against the applicable alternatives; missing evidence
is BLOCKED or further REVISE work, not proof that the feature is impossible.

### BS1.2 — Establish the native SCSI client contract

- [x] Establish an ordinary native transport baseline and record count-prefixed six-/ten-byte command templates, a matched PIO sense read, and HDD Save/cold Load. — 2026-10-18: [transport evidence](bluescsi-feasibility.md#bs12-transport-observations-and-reuse-boundary); no vendor-command or exhaustive ABI claim.
- [x] Identify and observe a deadline clock that does not require interrupt-handler progress. — 2026-10-18: 512 ordinary guest TIMER1 reads follow nominal microsecond ticks, including 85 reads with interrupts masked; 1,024 periodic samples cover 260 rollovers. The diagnostic below adds scoped guest guard/restoration evidence; release deadlines and interrupt servicing remain open. See [timer and recovery design](bluescsi-transport-contract.md).
- [x] Qualify a limited exact-byte guest sender and DATA IN/error return. — 2026-10-18: ordinary-entry diagnostic retains ten bytes including byte 1, short/zero data, original CHECK CONDITION and separate sense; absence/capacity cases return and caller state is restored. Reserved-field test CDBs establish byte preservation only; real Toolbox semantics remain open.
- [x] Fix false success for commands the native emulator does not implement (BUG-113). — 2026-10-18: unsupported 6/10/12-byte commands return CHECK CONDITION (`02`) and per-target ILLEGAL REQUEST / invalid-operation-code sense (`05/20/00`), with no data or media mutation. Verify sense isolation/clearing and a successful command afterward; retain explicit boot-ROM START UNIT support. Device fixtures, the ordinary-entry guest error/sense case, boot/HDD/CD regressions and all 561 backend tests pass. This prerequisite prevents unsupported-command probes from being mistaken for successful zero-byte replies. [Fix and evidence](bug-backlog.md#bug-113--native-scsi-reports-success-for-unsupported-commands).
- [x] Exercise a guest timeout across TIMER1 wrap and an independent finite poll guard. — 2026-10-18: held initiator ACK exits at 5,010–5,011 ticks, eight-poll limit at 165 ticks, timer sample gaps below 201 microseconds. The final full diagnostic masks interrupts for 20.32825 ms; no physical timing or independently stuck-target acceptance. See [qualified subset](bluescsi-transport-contract.md#qualified-guest-diagnostic-subset).
- [x] Qualify full 4 KiB guest DATA IN/OUT and deliberately rejected writes on private emulator fixtures. — 2026-10-18: exact payload/readback, guarded shared buffer, 28 observed in-command timer wraps, distinct `05/20`, `05/24`, `05/21` and `07/27` sense, unchanged media after rejected/incomplete writes, restored caller and subsequent native HDD Load/playback. Partial-write atomicity is model behavior only. The 1.897658-second masked diagnostic cannot establish usable interrupt/UI servicing. See [transfer/error matrix](bluescsi-transport-contract.md#full-buffer-and-deliberate-error-matrix).
- [x] Qualify explicit interrupt service points for the idle native transport diagnostic. — 2026-10-18: 20 cases pass, including full transfers, deliberate failures, held-ACK timeout at 5,016 ticks, eight-poll exit at 178 ticks and absent target. Timer and MIDI ISR progress is observed with scratch/bank preservation; the caller's IC4 mask restores. Measured stack paths require at least 186 bytes including the hook; no worst-case stack or ISR bound is claimed. See [interrupt contract and limits](bluescsi-transport-contract.md#interrupt-cooperation-follow-up).
- [x] Qualify ordinary Exit cancellation during native DATA IN/OUT using bounded command completion. — 2026-10-18: pressed/released Exit, held Exit, unrelated-key control, timeout precedence after cancellation and clear-on-re-entry pass. The probe suppresses later commands, preserves actual completion/error status, restores caller state and returns to exact HDD Load/playback. This does not qualify importer publication/rollback or an independent target-fault abort. See [cancellation contract](bluescsi-transport-contract.md#ordinary-exit-cancellation).
- [ ] Bound service intervals and stack under relevant active-audio/dense-MIDI workloads; qualify cancellation before selection, simultaneous target error/cancel, full input dispatch and physical controller interrupt ownership. The scoped raw panel scan and timer/MIDI service do not prove that every ISR returns within one TIMER1 wrap.
- [ ] Trace ordinary native invocations of selection, command, DATA IN/OUT and completion routines. Record caller mappings, registers, clobbers, interrupts, buffers, counts and return status.
- [ ] Establish an explicit 10-byte CDB path that preserves every vendor-command byte. Audit the existing drive-class branch that modifies CDB byte 1 and the descriptor reader's fixed data-bank selection.
- [ ] Specify short transfers, zero-data/status-only responses, REQUEST SENSE, unsupported commands, target absence, EOF and cancellation.
- [ ] Identify unbounded polls and decide which routines can be reused, locally adapted or replaced. Specify timeout units, bus cleanup and interrupt/UI servicing; an outer timeout cannot bound a non-returning inner poll.
- [ ] Define ownership/restoration of target selection, native disk classification, CDB staging, buffers and shared Toolbox directory/open-file state. No concurrent browser and native-disk transaction may corrupt the other's state.
- [ ] Specify extended INQUIRY/vendor-page discovery. The existing OS identification helper requests only 35 bytes and cannot retrieve the extended BlueSCSI identity unchanged.

### BS1.3 — Establish UI entry and state isolation

- [ ] Trace the actual Disk Menu selection path and mutable screen-index/callback tables in CRT and LCD modes; choose the Files/Folders entry and screen IDs.
- [ ] Audit menu labels, scrolling limits, field tables and descriptor bounds. The qualified CRT Disk Menu displays all nine labels; scrolling capacity and other display modes remain open. Adding an item requires safe bindings, not just a text edit.
- [ ] Define browser-owned navigation/selection state and its enter/exit cleanup. Existing Load/Save/Copy/Delete/Format handlers must never interpret a browser row as a native disk object.
- [ ] Verify callback register/bank restoration, panel operation, Mouse+CRT and the intended GB-6 baseline. Include shared drawing services and screen-change teardown.

### BS1.4 — Establish mono/stereo import and lifecycle contracts

- [x] Fix native MIDI transmit-ready/output before using SDS boundary experiments (BUG-116). — 2026-10-18: serial output, ready/busy behavior and RX isolation pass; stock OS emits 3,143 exact acknowledgments in retained boundary/cancellation runs. [Evidence](../condensed/validation/bluescsi-length-contract-2026-10-18.json).
- [x] Fix native sequential wave writes before accepting SDS PCM evidence (BUG-117). — 2026-10-18: C00A commits/advances once per completed word, C008 behavior remains intact, bounds regressions pass, and 249,760 transmitted bytes match native wave memory across 19 cases. The complete 590-test suite passes with zero skips.
- [x] Bound the existing SDS writer at packet/allocation edges and qualify settled mono cancellation. — 2026-10-18: 18 length cases plus cancel/retry, 54 snapshots and 399 original-OS instruction decodes establish the scoped formulas. Fixed 40-word packets can exceed the reservation by 24 words; zero-fill exceeds it by up to 4,607 words in this matrix. This excludes direct SDS-writer reuse for bounded WAV import. [Length contract](bluescsi-sample-contract.md#sds-length-boundaries-and-cancellation).
- [x] Resolve the observed early-retry cancellation failure (BUG-118) in an isolated OS patch. — 2026-10-18: busy headers receive CANCEL before allocation; three cancellation timings preserve staged/public data and PCM, settle without leaks, and permit exact retry/follow-on publication. A stock-OS counterexample proves the old state clear. [Guard and limits](../firmware/os/os-transfer-lifecycle.md#native-cancellation-overlap-and-private-os-guard).
- [x] Repair header admission during success publication and error cleanup (BUG-119). — 2026-10-18: completion state FF persists through publication; error cleanup joins the final state clear. Back-to-back publication/header, invalid-slot/retry, early completion and cancellation pass with exact PCM and responses. This is an opt-in native firmware result. [Contract and limits](../firmware/os/os-transfer-lifecycle.md#header-admission-through-publication-and-error-cleanup).
- [x] Repair competing outgoing SDS requests before they overwrite receive metadata (BUG-120). — 2026-10-18: active receive, publication, cancellation/error cleanup and idle sending pass; busy requests return CANCEL before slot decoding or sender setup. [Contract and evidence](../firmware/os/os-transfer-lifecycle.md#receive-owner-exclusion-for-outgoing-requests).
- [x] Repair active-sender admission of receive headers and new dump requests (BUG-121). — 2026-10-18: both sender phases reject overlaps; exact completion, explicit cancellation and stale ACK/NAK during a subsequent receive pass. The shared guard requires 2BBA=0 and B1AE=FF. [Contract and limits](../firmware/os/os-transfer-lifecycle.md#shared-admission-for-active-senders-and-receivers).
- [x] Reconcile local Sample Dump completion/cancellation with the sender guard (BUG-122). — 2026-10-18: bank-preserving cleanup permits the next exact receive; third error tail has decoded/unit coverage only. [Local cleanup](../firmware/os/os-transfer-lifecycle.md#local-sample-dump-cleanup-and-remote-stalls).
- [x] Repair remote header/data stalls and panel Exit recovery (BUG-123). — 2026-10-18: foreground state 7, a five-second progress deadline and a separate poll budget pass seven remote cases; four local compatibility cases and ordinary runtime/audio also pass. Physical deadlines, stuck native callees and complete stack bounds remain unqualified. [Remote recovery](../firmware/os/os-transfer-lifecycle.md#foreground-remote-sender-recovery).
- [x] Guard local entry and retain ownership through final-packet/UI cleanup overlap (BUG-124). — 2026-10-18: native final-ACK/header and final-ACK/request races now reject without leaks or discarded new owners; peer cancellation and normal local/remote sends pass. Busy entry and setup-error cases have decoded/model coverage. [Local ownership](../firmware/os/os-transfer-lifecycle.md#local-ownership-through-setup-and-cleanup).
- [ ] Qualify remaining local preparation/cancel timing and native disk exclusion, receive cancellation before supervisor entry, resource exhaustion and atomic stereo publication/rollback; qualify physical behavior and intended controller modes. The SDS admission guards are scoped prerequisites, not the importer's complete owner.

- [x] Record native stereo capture, descriptor storage and Save/fresh Load as an importer comparison baseline. — 2026-10-18: 56,719 exact frames/channel, 13 blocks/channel, matching recorded/reloaded RAM descriptors, and observed capture-preview references. See [stereo evidence](bluescsi-feasibility.md#bs14-observed-native-stereo-object-and-persistence).
- [x] Qualify stereo preview selection and channel routing after cold Load. — 2026-10-18: ordinary Loop/Smoothing entry constructs preview slots 512/513; selecting either member preserves L/R, mono controls center the selected channel, and five audio cases release to silence. Public descriptors and PCM remain unchanged. This is one 44.1 kHz fixture, not permanent patch assignment or hardware acceptance. See [selection/playback evidence](bluescsi-feasibility.md#cold-load-selection-and-playback-follow-up).
- [x] Correct sample-fixture metadata before using it to qualify the importer (BUG-114/115). — 2026-10-18: explicit rate/loop/native-point fields, unchanged legacy preset images, 28 focused tests and 588 full backend tests pass. See [builder corrections](bluescsi-sample-contract.md#builder-corrections-and-reproduction).
- [x] Establish the five playback-address fields, rate codes and Forward/OneShot metadata in the stock OS. — 2026-10-18: ten exact allocations/92,160 bytes, all eight displayed rates and preview pitches, asymmetric-point control and silent release tails pass. [Sample contract](bluescsi-sample-contract.md).
- [x] Qualify the ordinary native path from public stereo samples to permanent playable and saveable objects. — 2026-10-18: Partial SMT search, Patch Split Set, Perform assignment, naming, Performance Save and cold Load pass for one 44.1 kHz pair. Cold Perform Play succeeds with preview partial255 still unassigned; all 736 object bytes and 239,616 PCM allocation bytes match. See [permanent hierarchy contract](bluescsi-sample-contract.md#permanent-playable-hierarchy-and-persistence).
- [ ] Complete importer-driven descriptor construction for arbitrary frame counts/padding and permanent partial/patch references. Qualify initialization, naming and native-call contracts; the observed manual route and store anchors are not callable ABIs.
- [ ] Determine the required sample slots, aligned wave-memory blocks and descriptor reservations for mono and stereo. Do not assume two independent mono allocations automatically form a native stereo sample. The [single SDS rollback cursor](bluescsi-sample-contract.md#stereo-transaction-requirements) requires a separate pair-wide transaction owner.
- [ ] Define staged publication and rollback for both channels together, including failure after one channel has been written and exhaustion of either slots or wave RAM. Preserve existing samples and objects.
- [ ] Define streaming deinterleaving, PCM representation conversion, exact frame count, allocation padding, final partial block and chunk-boundary handling without requiring the whole file in CPU RAM.
- [ ] Freeze rates, naming/collision behavior, root key, optional WAV metadata handling, loop behavior and the path to playable partial/patch assignment. Avoid destructive automatic replacement.

The existing [stereo-selection analysis](../firmware/os/os-selection-refresh.md) identifies a name-based partner lookup and matching block-count check. Its local static contract is a lead, not proof that naming alone establishes every stereo playback/save relationship. [Native stereo sampling evidence](../condensed/validation/native-sampling-input-2026-10-12.json) supplies a comparison workflow; it does not qualify a WAV importer. [Allocation/publication/rollback analysis](../firmware/os/os-transfer-lifecycle.md) supplies further tracing roots.

### BS1 decision record

- [ ] Publish the address/ownership map, memory budget, transport ABI, UI patch list, stereo object contract, supported-format policy and proposed binary-diff boundaries.
- [ ] Attach reproducible static checks and native observations to each critical claim; identify what still requires the new Toolbox client or physical device.
- [x] Record one result: **PASS**, **REVISE**, or **BLOCKED**, with the exact remaining condition and next action. Do not mark PASS with unresolved code ownership, an unbounded command path, or an unexplained stereo lifecycle.

**PASS** means there is an implementable, evidence-backed design with remaining end-to-end tests assigned to BS2–BS6. It does not claim hardware parity or a finished importer. **REVISE** means a specific architectural choice must change, such as memory placement or a demonstrated ROM dependency. **BLOCKED** names the exact missing evidence; independent work can continue. Record effort estimates only after this decision.

## BS2 — BlueSCSI emulator target

- [ ] Pin the modeled protocol to a source release and record the physical device's exact reported build/capabilities at first qualification. The user reports latest firmware; no update task is presumed. The source previously inspected is V2 `v2026.08.17`, not an independently read-back installed build.
- [x] Qualify opt-in target-scoped ten-byte D1 framing, fixture file reads and named negative cases; actual guest pipeline passes (checkpoints57-60). Full target coverage remains below.
- [x] Add target-scoped ten-byte D0/D1/D2/D9 framing and capability/path/list/read operations on an actual fixture directory tree (checkpoint62); keep ordinary image targets operational.
- [x] Add opt-in INQUIRY/API and current MODE SENSE page31 discovery, pinned to an inspected source commit (checkpoint70).
- [ ] Reconcile the fixture subset with the physical device protocol; qualified differences remain explicit in the fixture contract.
- [ ] Match the supported subset's phases, lengths, status/sense, index/type encoding, filename/path limits and directory/open-file lifecycle. Advertise only implemented capabilities; document any subset differences instead of copying unsupported capability bits.
- [ ] Require negative-command tests for each Toolbox operation: unsupported opcode/subcommand/capability, invalid parameters and lengths, invalid file/directory/index, and applicable media/range failures must return the pinned firmware's status/sense rather than false success. Assert no unintended file/media mutation, preserve the original failure across REQUEST SENSE, and verify a following valid command. Keep zero-byte success and EOF distinct from failure; BUG-113's ordinary-SCSI fix is the prerequisite, not full Toolbox coverage.
- [ ] Define missing-directory creation behavior, invalid paths, count overflow, empty directories/files, short reads, EOF/reopen, reset and cancellation. Keep test filesystem effects confined to fixture trees.
- [ ] Include target state in session recall or explicitly invalidate/reopen transient browser state safely. Never silently restore a stale host file handle/index.
- [ ] Pass ordinary READ/WRITE, capacity, discovery, existing-target state and writeback regressions with Toolbox disabled and enabled. Preserve source images except for intentional writes to test copies.

**Exit:** protocol tests and native regressions pass for the declared profile, with physical comparison assigned to BS3. A host UI browser or host-injected guest catalog/sample is not acceptance.

## BS3 — Native OS Toolbox client

- [ ] Implement the BS1 contract as an isolated OS client with bounded transfers and cleanup. Begin with one 4 KiB file block per command.
- [x] On a configured target, query capabilities, select an existing `/Files` subtree, count/list entries and derive file indices/sizes from actual SPC responses (checkpoint63).
- [x] Discover/select the qualified Toolbox target through INQUIRY/API and the full vendor page; targets2/6 and no-target rejection pass (checkpoint71).
- [ ] Generalize the fixed path/batch selection into browser state and qualify multiple device groups and physical reads.
- [ ] Preserve returned entry indices when sorting/filtering. Open at offset zero; manage the shared handle and final short block explicitly.
- [ ] Qualify absent targets, unsupported capabilities, short/empty responses, CHECK CONDITION, bus reset, timeout and cancellation. Return to working native Disk operations after every failure.
- [x] Retain original status02 on missing-directory failure before any per-file results or PCM changes; independent boot-baseline comparison passes (checkpoint64).
- [ ] Expose transport outcome, original SCSI status and bounded sense separately to the browser/importer. Deliberately send commands that must fail and assert that the guest reports the failure without publishing samples or treating a successful REQUEST SENSE as a successful original command.
- [ ] Compare command bytes, transfer lengths, status/sense and payload hashes between the native emulator and physical BlueSCSI. Record exact firmware/configuration and any unmeasured timing limitations.

**Exit:** guest-originated reads return the expected fixture bytes on both platforms and recovery preserves the native disk destination. No SD file-upload commands are part of this client.

## BS4 — Native Files/Folders screens

- [x] Link the integrated client to a relocated native menu callback and preserve the original Save System entry (checkpoints73/78).
- [ ] Add dedicated CRT and LCD descriptors/callbacks for the Files/Folders entry, current path, folder/file rows, selection, scrolling and errors.
- [ ] Implement Open/Parent/Refresh/Back, constrain navigation to `/Files`, and handle empty folders and the protocol's name/path/count limits visibly.
- [ ] Invalidate row indices and read state on refresh/directory changes. Handle ambiguous/truncated directory names without guessing the path.
- [ ] Support panel, Mouse+CRT and the selected GB-6 configuration through normal guest input. Disable unsupported file imports with an explanation.
- [ ] Exercise repeated entry/exit, missing targets, cancellation and return to existing Disk screens. Verify actual guest CRT/LCD frames and native state restoration.

**Exit:** browser acceptance passes in emulator and hardware. A listing demo does not close the importer milestone.

## BS5 — Mono and stereo PCM WAV import

- [ ] Parse RIFF chunk boundaries and odd-byte padding; find and validate `fmt ` and `data` without assuming a fixed 44-byte header. Validate sizes, frame alignment, channel count, rate and overflow before allocation/publication.
- [ ] Stream mono and stereo PCM16 through the verified memory path. Stereo deinterleaves left/right into the native representation and preserves frame alignment, channel identity and equal length.
- [x] Construct and publish the scoped WAV-derived mono/stereo descriptors with exact reserved PCM/padding; ordinary native preview selection/audition passes (checkpoints74/76).
- [ ] Generalize slot/block allocation, naming/rate/loop policy and permanent playable assignment; qualify native edit/save behavior.
- [ ] Publish a complete sample or stereo pair only after successful transfer. On cancellation, malformed input, I/O failure or insufficient resources, undo reservations and leave existing content intact.
- [ ] Verify sample data and frame counts against source fixtures after documented representation conversion; check allocation padding separately. Audition distinct left/right signals, note release and native stereo selection.
- [ ] Save mono and stereo imports to a Roland HDD test image, then cold boot/fresh Load and recheck both PCM channels, pairing, metadata and playback. Exercise the same workflow on hardware.

**Exit:** both mono and stereo import pass. A mono-only prototype, audible output alone, or two unpaired channel records cannot close BS5.

## BS6 — Backward compatibility and delivery

- [ ] Freeze patched OS, ROM/controller baseline, emulator build, BlueSCSI version/configuration and fixture identities.
- [ ] Use copies of authentic, previously machine-saved HDD images. Load, save, overwrite and cold reload through the existing Disk interface, including after browser errors and cancellations. Preserve CD loading and read-only behavior.
- [ ] Check that images intentionally saved by the patched OS remain loadable by the stock OS, including newly imported mono/stereo content represented in normal Roland structures.
- [ ] Verify that browsing/import alone leaves HDD/CD image bytes and existing SD files unchanged. Account explicitly for intentional test saves and any documented missing-directory creation.
- [ ] Exercise ordinary non-BlueSCSI targets and unsupported/disabled Toolbox profiles without breaking their normal disk workflows.
- [ ] Qualify repeated browsing/import/cancel cycles, resource exhaustion, supported RAM sizes, exact boundary cases, MIDI/UI servicing and playback recovery. Existing firmware can mute disk workflows; continuous music during import is not assumed.
- [ ] Qualify native session save/cold restore, including missing or changed browser source files. Loaded sample PCM must remain independent of a transient SD file handle after import.
- [ ] When exposed in standalone/VST3 products, verify configured filesystem access and the real packaged/plugin workflows. Keep host UI convenience distinct from guest-native acceptance.
- [ ] Publish supported formats/rates/limits, installation/recovery steps, original-media fallback and separate emulator/hardware results. Distribute project-owned patch tooling/manifests, not proprietary firmware binaries.

**Exit:** all required feature gates pass with evidence and residual limitations stated. Existing image readability/writability is a release requirement, not an architectural assumption.

## Qualification fixtures

| Area | Required cases |
| --- | --- |
| Directory protocol | 0/1/99/100/101 visible entries; separately qualify any reused S-760 list at 125/126/127; folders and files; reordered entries; long/truncated names; maximum path; missing directory; no target |
| File reads | 0/1/4095/4096/4097 bytes; multiple blocks; final short block; EOF/reopen; failed read; reset/cancel |
| WAV parsing | Mono/stereo PCM16 at every advertised rate; extra/unknown chunks; odd padding; chunk/header/data crossing 4 KiB boundaries; truncated/invalid chunks; unsupported format/rate |
| Stereo identity | Different L/R tones and impulses; left-only/right-only; known signed extremes and silence; exact channel/frame alignment and no downmix/swap |
| Native allocations | Reads crossing 9,216-byte allocation boundaries; nearly full RAM; enough RAM but too few sample slots; failure while writing the second channel; repeated abort/retry |
| Persistence | Mono/stereo Save and fresh Load; imported content with existing programs; unchanged historical HDDs; intentional writes to test copies; stock-OS compatibility; cold session recall |

## Research starting points and evidence discipline

The following are bank-aware static leads from the original OS, including the read-only 2026-10-18 review. They are not yet a qualified ABI or permission to overwrite those locations. For banked OS addresses, `file = 0x4800 + (selector << 10) + (address & 0x3FFF)`; instruction and operand selectors must be tracked independently.

| Area | Bank:logical address | Image file offset | Qualification needed |
| --- | --- | --- | --- |
| Banked-call wrapper | `0000:CE14` | `0x005614` | Caller/interrupt context and complete preservation |
| Target selection/retry | `003B:7482` | `0x016882` | Bounded recovery and target-state ownership |
| Count-prefixed command sender | `003B:7592` | `0x016992` | Descriptor bank, byte-1 mutation, buffer bounds |
| Programmed DATA IN | `003B:7647` | `0x016A47` | Actual/expected length, short response and waits |
| Programmed DATA OUT | `003B:76BC` | `0x016ABC` | Phase handling, bounded waits and cancellation |
| Status/message completion | `003B:7D2A` | `0x01712A` | Sense/retry policy and cleanup |
| Disk Menu descriptor, index `00F5` | data `0219:91DA` | `0x08BDDA` | Runtime descriptor/menu mutations |
| Disk Load CRT descriptor, index `00F6` | data `023F:928C` | `0x09568C` | Reusable drawing/input dependencies |
| Disk Load LCD descriptor, index `00F7` | data `023F:95B2` | `0x0959B2` | LCD-specific dispatch and field behavior |

Disk Menu initial callbacks include fetch `0196:968A` and `0171:8149`; selection reaches `0196:993C`, which reads data `02DB:47EA`. The screen-index table is data `0219:8000 + 4*index`. Re-derive initial descriptor values from the immutable image, then qualify runtime mutation and both control-mode paths.

Baseline identities:

- OS `S760224.IMG`: 1,474,560 bytes; SHA-256 `3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd`.
- IC15 v1.11 `roms/BOOT/Roland_S-760_v1.11.BIN`: 32,768 bytes; SHA-256 `ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6`.

Relevant maintained references:

- [Device probe and command records](../firmware/os/os-device-probe-and-numeric-fields.md), [screen descriptor loader](../firmware/os/os-screen-descriptor-loading.md), [UI event dispatch](../firmware/os/os-ui-event-dispatch.md).
- [Transfer allocation/publication](../firmware/os/os-transfer-lifecycle.md), [sample slots/addressing](../firmware/os/os-transfer-addressing.md), [stereo selection](../firmware/os/os-selection-refresh.md), [transfer staging](../firmware/os/os-scsi-transfer-and-delete.md).
- [Firmware toolchain](../firmware/tooling/firmware-toolchain.md), [native emulator SCSI implementation](../../mame-source/src/mame/roland/s760.cpp).
- [BlueSCSI Toolbox protocol](https://bluescsi.com/docs/Toolbox-Developer-Docs), [pinned implementation](https://github.com/BlueSCSI/BlueSCSI-v2/blob/v2026.08.17/src/BlueSCSI_Toolbox.cpp), [constants](https://github.com/BlueSCSI/BlueSCSI-v2/blob/v2026.08.17/src/BlueSCSI_Toolbox.h), [configuration](https://bluescsi.com/docs/bluescsi.ini).

For the inspected protocol, use source-accurate directory type 0/file type 1, 40-byte records, 32-byte returned names, a 100-entry limit with count overflow error, a conservative 63-byte path plus NUL, and a one-byte NUL to reset the directory override. Verify those behaviors against the pinned physical build. Preserve original indices, handle shared open-file state, and do not infer protocol behavior from file extensions.

Each completed checkbox needs a dated result recording the milestone/task ID, source/build/firmware hashes, fixture hashes, reproducible commands or hardware procedure, expected/observed result, evidence location and limitations. Distinguish static analysis, protocol/unit tests, native guest execution, physical hardware and packaged-product acceptance. Keep durable evidence in committed documentation/validation paths; ignored scratch directories are not stable citations. Update this tracker and its project-index status together. Do not convert research leads into completion percentages.

## Checkpoint history

Chronological research record. Status and next-action statements below describe
what was known at each checkpoint; the current decision and BS1 requirements
above govern ongoing work. Evidence links and qualification limits are retained.

### Checkpoints 1-18: baselines, transport and ownership

**2026-10-18 research checkpoint:** [feasibility evidence](bluescsi-feasibility.md) records exact native stereo capture/Save/cold Load, the 13-sample HDD Save/cold Load baseline, 22 RAM snapshots, 1,952 byte-checked assembly annotations, and real six-/ten-byte command call contexts. Several apparent free regions are occupied, and the existing transport has byte-1 mutation and unbounded-wait constraints. These results advance BS1 without passing it.

**Second checkpoint:** another fresh instance and 12 snapshots qualify the 44.1 kHz fixture's stereo preview selection from either member, mono controls, unchanged PCM and silent release. Byte-checked screen-backup bounds exclude the upper RAM tail. A proposed shared 4 KiB listing/read workspace reduces the provisional working budget from 9,440 to 5,440 bytes; code/UI placement and buffer lifetimes remain unqualified. [Follow-up evidence](../condensed/validation/bluescsi-stereo-ui-followup-2026-10-18.json).

**Third checkpoint:** an 8,002-byte data marker survives native Save System and a cold boot from that saved disk, followed by exact stereo Load/playback. Eleven snapshots preserve the marker. TIMER1 observations support the deadline source, while byte-checked initialization/sense side effects rule out treating native helpers as neutral cleanup. [Evidence](../condensed/validation/bluescsi-memory-transport-2026-10-18.json) and [proposed timeout/recovery contract](bluescsi-transport-contract.md). Complete memory ownership, executable size and guest recovery remain open; BS1 has not passed.

**Fourth checkpoint:** ordinary Disk controls enter a 942-byte private-OS diagnostic. The final 14 cases qualify exact CDB bytes, short/status-only DATA IN, error/sense, capacity limits, absence, finite timeout/poll exits and caller restoration; a baseline replay crosses TIMER1 wrap during the timeout. The helper uses 86 stack bytes including the hook and masks interrupts for 20.32825 ms, so interruption/cancellation and recovery remain open. BUG-113 corrects native unsupported-command status while preserving the boot ROM's START UNIT request. Subsequent patched-OS HDD Load and separate stock-OS CD/runtime regressions pass. [Evidence](../condensed/validation/bluescsi-guest-transport-2026-10-18.json). No Toolbox/browser/importer or physical acceptance is claimed.

**Fifth checkpoint:** a 16-case ordinary-entry guest probe transfers exact 4 KiB buffers through DATA IN/OUT. Unsupported opcode, invalid START fields, out-of-range WRITE and protected-CD WRITE return distinct expected sense; successful REQUEST SENSE leaves the original failure record intact. A capacity-limited 4,095-byte WRITE does not commit in this emulator, and complete scratch-media comparisons isolate the single successful write. Guards, caller state and subsequent ordinary HDD Load/playback pass. Full transfers take 294.729–296.777 ms; the entire diagnostic masks interrupts for 1.897658 seconds, making interrupt servicing the next design constraint. [Evidence](../condensed/validation/bluescsi-transfer-errors-2026-10-18.json). No emulator change or new full-suite run was needed; BUG-113's previously tested build is unchanged.

**Sixth checkpoint:** an ordinary-entry private OS probe now services interrupts while retaining exact 4 KiB IN/OUT, original error/sense results and bounded timeout/poll exits. The final 20 cases include 1,800 service points, 169 native timer interrupts and six ordinary MIDI bytes. A conservative measured bracket for interrupt-masked spans is 5.019 ms in this muted Save System workload, compared with the earlier continuously masked 1.898-second sequence. All transport scratch/banks and the native SCSI interrupt mask restore; ordinary HDD Load/playback remains exact. [Evidence](../condensed/validation/bluescsi-interrupt-cooperation-2026-10-18.json). This is scoped interrupt cooperation, not worst-case latency, responsive UI, cancellation or physical controller acceptance.

**Seventh checkpoint:** ordinary panel Exit now latches cancellation, drains the current bounded command and stops subsequent probe commands. Read and held-Exit WRITE cases return about 308–309 ms after the latch; a deliberate initiator stall retains the timeout error and returns in 5.050 ms. Panel Up does not cancel, and ordinary re-entry clears the previous latch and passes all 20 cases. Five fresh processes / six invocations cover 45 cases; all then load/play the unchanged 13-sample HD0 fixture. [Evidence](../condensed/validation/bluescsi-cancellation-2026-10-18.json). Completed writes are not rolled back. Independent target faults, physical abort/reset, full browser input handling and importer publication remain open.

**Eighth checkpoint:** the complete lower candidate, containing unchanged diagnostic code/table plus 5,951 seeded workspace bytes, survives native stereo recording, Save, cold Load and armed session restore. Twenty-four initialized snapshots retain all 8,002 bytes; a separate pre-restore snapshot proves recovery from zeroed RAM. Both channels retain 56,737 exact frames and 239,616 total allocation bytes. A fourth fresh process initializes the seeded workspace, passes all 20 transport cases and returns to exact HDD Load/playback. The [memory contract](bluescsi-memory-contract.md) separates 4,928 local data bytes from a provisional 512-byte native stack allowance, leaving a 3,074-byte code/UI ceiling. Complete ownership, stack bounds and full-client fit remain open. [Evidence](../condensed/validation/bluescsi-memory-lifecycle-2026-10-18.json).

**Ninth checkpoint:** native metadata controls establish all eight rate codes, loop modes and five playback-point fields. Ten allocations/92,160 bytes and twelve snapshots pass; BUG-114/115 correct the fixture builder while preserving legacy preset bytes. The 588-test backend suite passes. The SDS single-cursor backup requires a pair-wide transaction owner. [Sample contract](bluescsi-sample-contract.md).

**Tenth checkpoint:** two fresh stock-OS processes qualify permanent stereo partial/patch/performance assignment, naming, Save and cold Load. Twenty-five snapshots, 238 replayed object writes and seven audio cases retain exact records and 239,616 PCM allocation bytes. Cold Perform Play works before any preview setup. Eleven native store anchors identify construction points without claiming callable ABIs. [Evidence](../condensed/validation/bluescsi-permanent-assignment-2026-10-18.json). Importer-driven creation, arbitrary-length padding and atomic stereo allocation/publication/rollback remain open.

**Eleventh checkpoint:** 18 SDS length cases and one settled cancellation/retry establish packet, zero-fill and reservation bounds through 54 snapshots and 249,760 exact transmitted bytes. BUG-116/117 repair native MIDI output and sequential wave writes; 590 backend tests and ordinary runtime/audio checks pass. The existing SDS writer can exceed its reservation and is excluded from direct bounded-WAV reuse. Early retry during cancellation exposed BUG-118, addressed in the next checkpoint. [Evidence](../condensed/validation/bluescsi-length-contract-2026-10-18.json). No stereo transaction or physical acceptance is claimed.

**Twelfth checkpoint:** BUG-118 is fixed in an opt-in experimental OS patch. A stock negative control identifies the old supervisor's state clear after a new allocation; the guard rejects busy headers before decoding/allocation. Three fresh timing cases preserve existing content, publish nine exact samples/28,800 PCM bytes after settled retries and return six exact CANCEL responses plus 375 ACKs. The four SDS runs retain 63 snapshots. Three focused tests cover 65,536 command/state combinations; ordinary patched-OS playback, MIDI scheduling and audio rendering pass. Original firmware and native executable remain unchanged. Full completion/error ownership, stereo transactions and bounded WAV writing remain open. [Repair](../firmware/os/os-transfer-lifecycle.md#native-cancellation-overlap-and-private-os-guard), [evidence](../condensed/validation/bluescsi-cancel-ownership-2026-10-18.json).

**Thirteenth checkpoint:** BUG-119 extends header exclusion through successful publication and allocation-error cleanup in private firmware. Two negative controls expose descriptor replacement/unpublished reservations; four final native runs pass publication overlap, invalid-slot retry, completion before supervisor entry and cancellation compatibility. They publish eleven samples/10,800 exact PCM bytes and emit 148 ACKs plus five CANCEL responses. All six runs retain 78 snapshots. Seven focused tests and ordinary playback/MIDI/audio checks pass. An intermediate completion-marker failure is retained and excluded. Other-command/disk exclusion, resource exhaustion, atomic stereo publication and bounded WAV writing remain open. [Header contract](../firmware/os/os-transfer-lifecycle.md#header-admission-through-publication-and-error-cleanup), [evidence](../condensed/validation/bluescsi-header-lifecycle-2026-10-18.json).

**Fourteenth checkpoint:** BUG-120 is fixed in private firmware: outgoing sample requests are rejected before decoding or sender setup while a receive owns state. Two prior-image failures show active/completed receives being discarded; seven final native runs preserve 18 exact samples/2,880 PCM bytes and emit 56 ACKs plus five CANCEL responses. Idle send compatibility retains 9,216 exact bytes, 116 packets and one exact retransmission. With a prior ACK control, 118 snapshots are retained. Ten focused tests and ordinary playback/MIDI/audio checks pass. Already-active outgoing sessions, disk exclusion, stereo transactions and bounded WAV writing remain open. [Request guard](../firmware/os/os-transfer-lifecycle.md#receive-owner-exclusion-for-outgoing-requests), [evidence](../condensed/validation/bluescsi-command-exclusion-2026-10-18.json).

**Fifteenth checkpoint:** BUG-121 closes active-sender admission in private firmware. Headers and dump requests require both receive-idle and sender-idle state; overlapping transfers return CANCEL before mutation. Ten final native runs preserve 28 received samples/4,480 exact PCM bytes and four complete outgoing dumps/36,864 bytes, with 86 ACKs, nine CANCEL replies and 469 exact data packets. Two prior-image failures bring the total to 182 snapshots. Thirteen focused tests cover 131,072 state/entry cases; ordinary playback/MIDI/audio pass. Disk exclusion, abandoned-sender recovery, stereo transactions and bounded WAV writing remain open. [Shared admission](../firmware/os/os-transfer-lifecycle.md#shared-admission-for-active-senders-and-receivers), [evidence](../condensed/validation/bluescsi-sender-ownership-2026-10-18.json).

**Sixteenth checkpoint:** BUG-122 repairs a regression in the private sender guard: local Sample Dump exits left B1AE=0, blocking the next receive. Three existing cleanup tails now share a bank-preserving FF release after parser/display cleanup. Four local completion/cancellation cases and one remote-stall/recovery case preserve 15 received samples/2,400 exact PCM bytes and two complete outgoing dumps/18,432 bytes; all 45 ACKs, two CANCEL replies and 251 data packets match. Three negative controls bring the retained total to 115 snapshots. Twenty-four focused tests and ordinary playback/MIDI/audio pass. At this checkpoint BUG-123 was OPEN: a remotely requested dump stays busy after 60 seconds without ACK and panel Exit, while MIDI CANCEL restores admission. Third-tail error coverage is decoded/unit only; local UI races, disk exclusion, timeouts, stereo transactions and bounded WAV writing remain open. [Cleanup contract](../firmware/os/os-transfer-lifecycle.md#local-sample-dump-cleanup-and-remote-stalls), [evidence](../condensed/validation/bluescsi-local-sender-lifecycle-2026-10-18.json).

**Seventeenth checkpoint:** BUG-123 is fixed in experimental firmware: successful remote requests claim foreground state 7; five seconds without packet-counter progress or panel Exit cancels safely. Seven remote scenarios and four local compatibility cases preserve 33 received samples/5,280 exact PCM bytes anoperationd three complete dumps/27,648 bytes. All 99 ACKs, seven CANCEL replies and 371 data packets match; one prior-image negative control brings the total to 180 snapshots. Thirty focused tests and ordinary playback/MIDI/audio pass. The 640-byte helper leaves 863 bytes of the proposed code/UI budget, with combined placement and full fit still unqualified. Observed stack use is 182 bytes and maximum TIMER1 read gap 42.710 ms in these workloads. Local UI races, native Disk exclusion, full stack bounds, stereo transactions and bounded WAV writing remain open. [Recovery contract](../firmware/os/os-transfer-lifecycle.md#foreground-remote-sender-recovery), [evidence](../condensed/validation/bluescsi-remote-recovery-2026-10-18.json).

**Eighteenth checkpoint:** BUG-124 is fixed in experimental firmware. A final local-send ACK followed immediately by a receive header previously leaked a sample block; a queued remote request was also discarded by local cleanup. Local entry now checks shared admission and claims state 8, retaining ownership through display cleanup and releasing atomically. Nine accepted native cases preserve 27 samples/4,320 received PCM bytes and five complete dumps/46,080 bytes; all 81 ACKs, six CANCEL replies and 601 packets match. Two prior-image controls bring the total to 175 snapshots. All 96 focused tests and ordinary playback/MIDI/audio pass. The added 160 bytes leave 703 bytes of the proposed code/UI budget; complete fit and stack bounds remain open. Busy local entry and setup-failure handling have decoded/model coverage. Native Disk exclusion, remaining preparation/cancel timing, stereo transactions and bounded WAV writing are still unqualified. [Local owner contract](../firmware/os/os-transfer-lifecycle.md#local-ownership-through-setup-and-cleanup), [evidence](../condensed/validation/bluescsi-local-owner-2026-10-18.json).

### Checkpoints 19-24: historical handoff summary

Historical summary through the [twenty-fourth 2026-10-18 checkpoint](bluescsi-feasibility.md#next-checkpoint). Sampling/session restore and seeded transport initialization strengthen the lower candidate's lifetime evidence. Complete its indirect-user and nested UI/LCD/GB-6 ownership audit and size the full client against the [3,074-byte code/UI ceiling](bluescsi-memory-contract.md#corrected-budget-and-proposed-placement); local data and native stack are separate budgets. Extend interrupt/input/stack bounds to relevant workloads and qualify independently injected target faults, recovery and subsequent native HDD/CD use. Rate/loop/address metadata and ordinary permanent stereo assignment/Save/cold Load now have native evidence; BUG-114/115 are fixed. BUG-116/117 are fixed, and the native SDS writer is excluded from direct WAV reuse by measured write overruns. BUG-118/119 have qualified native header guards through cancellation, publication and invalid-slot error cleanup in private firmware. BUG-120 additionally rejects outgoing requests during receive ownership and preserves ordinary idle sending. BUG-121 now protects active senders through completion or explicit cancellation and ignores stale handshakes during a later receive. BUG-122 reconciles local Sample Dump completion/cancellation with that guard. BUG-123 now supplies native-qualified remote timeout/Exit recovery. BUG-124 now guards local entry and retains ownership through cleanup. Four ordinary floppy/HDD Load cases now preserve exact media/PCM and post-load reception under scheduled SDS headers/requests. Two floppy Save cases also preserve exact PCM through stock-OS cold Load and accept post-save reception. Two HDD overwrite Save cases now also preserve all sample allocations through independent extraction and stock-OS cold Load. Active receive/remote-send menu attempts now retain ownership; local-send click attempts cancel cleanly versus an active no-click control. Five manufacturer41 session cases now qualify remote recovery/completion, deferred session exit and receive publication through the second caller. BUG-125 now fixes immediate/duplicate/completion-boundary receive cancellation leaks using distinct rollback ownership. Qualify remaining entry boundaries and preparation/cancel timing, then complete bounded WAV padding, importer-driven object creation and two-channel allocation/publication/rollback against the [sample contract](bluescsi-sample-contract.md). The Save System callback is a diagnostic entry only; final browser entry remains open. BS1 ends with a written feasibility decision.



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

### Checkpoints 39-41: workload, sizing and recovery audit (2026-10-18)

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

[Decision evidence](../condensed/validation/bluescsi-feasibility-decision-2026-10-18.json).

### Checkpoints 42–48: measured memory workarounds (2026-10-19)

Bounded receive windows, actual 1 KiB buffer relocation, compacted stereo
cancellation/retry, 1,536-byte in-place stereo splitting, 88-case guest RIFF
validation, 128-case host file scheduling and ten-case guest parser/SCSI
integration pass within their stated scopes. The revised 5,634-byte code ceiling
and 3,749-byte component census replace the old component-level memory objection;
the remaining 1,885 bytes are an unallocated budget, not proof the full client fits.
BS1 remains REVISE pending complete integration and recovery qualification.
[Evaluation](bluescsi-workaround-evaluation.md) · [Evidence](../condensed/validation/bluescsi-workarounds-2026-10-19.json).

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
