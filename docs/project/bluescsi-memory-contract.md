# BlueSCSI extension memory contract

**Current IM1 footprint (2026-10-20):** 6452/8002 bytes,1550 free/1332 code-adjacent. BUG-165 saves35 code bytes. Exact rebuild and366-snapshot resource census pass; all custom stack paths balance with166-byte maximum including80-byte frame. Native caller/callee/ISR depth, service time and remaining indirect aliases are not bounded by this result. [Closeout results](bluescsi-im1-closeout-results-2026-10-20.md).

**Previous fresh-entry IM1 footprint (2026-10-19):** 5408/8002 bytes,2594 free/2106 code-adjacent. A15-byte init loop invalidates76 operation-context bytes while preserving16 callback-save bytes. Native stale-reentry baseline, fresh recovery, Save System export/cold boot/exact Load/playback and retained cancellation/SDS pass. Full stack/ISR and external checkpoint/reset qualification remain open. [Entry-state results](bluescsi-im1-entry-state-results-2026-10-19.md).

**Previous help/identity IM1 footprint (2026-10-19):** 5393/8002 bytes,2609 free with2121 immediately after code. Contextual CRT help and collection/target titles add131 code+280 string bytes to the owned-footer candidate, including the3-byte cold-entry render fix. Two final-hash native workflows and exact rebuild pass. Full feature/stack/ISR fit and remaining controller/media/hardware gates are open. [Help/identity results](bluescsi-im1-help-identity-results-2026-10-19.md).

**Previous page-window IM1 footprint (2026-10-19):** 4,982/8,002 bytes,3,020 free with3,004 directly after code. A224-byte visible-page buffer replaces the3200-byte full catalog for40 added code bytes; all100 names/indices remain supported through fresh page reads. Nine native workflows on one hash, model checks and exact rebuild pass. Full UI/policy/repair and stack/ISR fit remain open. [Page-window results](bluescsi-im1-page-window-results-2026-10-19.md). The BS1 WAV-import measurements below are historical and separate.

**Latest integrated measurement (checkpoints67-79):** 4,507 code bytes; conservative partial census6,009, exceeding5,634 by375. It retains potentially duplicate helpers and is not a minimum/full production footprint. Static extension stack268 bytes excludes native ISR/caller depth. [Integrated evidence](../condensed/validation/bluescsi-integrated-client-2026-10-19.json).

**Latest directory measurement (checkpoints62-66):** 3,346 diagnostic code bytes, 4,848-byte partial census and786-byte residual. Static extension stack266 bytes excludes native ISR/caller depth. [Directory contract](bluescsi-toolbox-fixture.md).

**Previous combined measurement (checkpoints53-56):** 2,783 diagnostic code bytes; 4,285-byte conservative census leaves1,349 bytes before unfinished required code. Static extension stack is264 bytes including the hook return; native ISR/caller depth remains unbounded here. See [block-window evidence](../condensed/validation/bluescsi-block-windows-2026-10-19.json).

**2026-10-19 update:** the [workaround evaluation](bluescsi-workaround-evaluation.md) proposes a 1,536-byte workspace and 5,634-byte code ceiling backed by scoped native tests. Earlier 4 KiB workspace arithmetic below is historical; complete integrated fit remains open.

**2026-10-18 — BS1 research; proposed placement, not an allocation reservation.**

The lower physical CPU-RAM interval `003D3E..005C80` contains 8,002 bytes.
All ranges in this document are end-exclusive. Native lifetime tests support
this candidate through the workflows below, but complete alias/reader/writer
ownership and the complete browser/importer footprint remain open.
[Feature roadmap](bluescsi-files-roadmap.md),
[validation](../condensed/validation/bluescsi-memory-lifecycle-2026-10-18.json).

## Address and lifetime boundaries

| Item | Byte-checked or observed boundary | Consequence |
| --- | --- | --- |
| Original OS payload | File `004800..100800` loads to physical `000000..0FC000` | The candidate is loaded from file `00853E..00A480` |
| Preceding interrupt stubs | Physical `003D20..003D3E`; last two instructions are `POPA; RET` | Start extension bytes at `003D3E`, without modifying the stubs |
| Following resident code | Begins at physical `005C80`, fixed-low fetch `000F:2080` | End extension bytes before `005C80` |
| OS entry | Sets fetch selector `0100=000F` and data selector `0108=0204` | Low fetch and low data addresses refer to different physical locations |
| Native initialization and stack | Clears logical data `0120..1120`, physical `081120..082120`; sets SP to logical `1120`, physical `082120` | This startup clear does not initialize the candidate; the native stack is outside it |
| Save System | Earlier native marker test retains the full candidate in the exported system image | Treat saved mutable bytes as uninitialized on boot/entry |
| Same-build emulator checkpoint | Restores all 8,002 candidate bytes in a fresh process, then native sampling and Save succeed | This establishes modeled RAM persistence, not synchronization with an external BlueSCSI device |

For loaded OS bytes, `file = 4800 + physical`. With fetch page `000F`, the
candidate corresponds to logical `013E..2080`. With data page `000F` in window
1, it corresponds to logical `413E..6080`. Address translation uses addition:
`physical = (selector << 10) + (logical & 3FFF)`.

The arithmetic audit enumerates 96 overlapping window/page views: selectors
`0000..0017` can each expose some candidate bytes in each of four windows.
These are address views, not evidence that native code uses them. Low data
addresses below `0120` have register/selector behavior and cannot be treated as
ordinary mapped RAM. The proposed window-1 view avoids that special region.
Read-only CPU taps translate every observed data address through the active
selector; opcode fetch and direct DMA require separate evidence.

## Corrected budget and proposed placement

The earlier 5,440-byte working allowance combines **4,928 local data bytes**
with **512 bytes of additional native stack allowance**. The latter is outside
this candidate and is not a reserved or proved stack bound. Separating the two
leaves a **3,074-byte ceiling for all code, constants and UI resources** in the
candidate. The diagnostic code uses 1,571 bytes and the remote SDS recovery
helper adds 640; the local owner adds another 160 and early-cancel ownership adds31. Their total is 2,402, leaving
**672 bytes** of that ceiling. At the current separate placements, 31 bytes lie
between the diagnostic's end 0761 and the remote helper at 0780; **641 contiguous
bytes** remain after the early-cancel helper's end 0ABF
before 0D40 (all end-exclusive). The diagnostic stall variant ends 077A, leaving
six bytes before 0780. Checkpoint25 qualifies a combined diagnostic/recovery
layout after relocating the case table and working data (see below). These
diagnostic resources are not the production browser state. This arithmetic
does not establish that a complete client fits.

The recovery helper is native-qualified at physical 004380..004600, file 008B80..008E00,
fetch 000F:0780..0A00 (end-exclusive). It adds no persistent RAM. Its observed
main-loop stack low-water mark is 106A versus caller 1120, a 182-byte depth across
seven remote workloads. This is not a complete interrupt/callee stack bound or
validation of the proposed 512-byte allowance. [Recovery evidence](../condensed/validation/bluescsi-remote-recovery-2026-10-18.json).

The local-owner helper occupies physical 004600..0046A0, file 008E00..008EA0,
fetch 000F:0A00..0AA0 (end-exclusive), with no new persistent RAM. Its entry
explicitly saves 10 stack bytes, excluding call returns and native callees;
release saves 6 and the setup wrapper adds a 2-byte return. These static frame
sizes do not establish complete nested stack use. The combined SDS image passes
native local/remote ownership cases; checkpoint25 additionally combines those
patches with the relocated transport diagnostic.
[Local owner evidence](../condensed/validation/bluescsi-local-owner-2026-10-18.json).

| Proposed resource | Bytes | Physical interval | Data page `000F`, window 1 |
| --- | ---: | --- | --- |
| Code, constants and UI ceiling | 3,074 | `003D3E..004940` | `413E..4D40` (code fetch uses low `013E..0D40`) |
| Shared listing/read workspace | 4,096 | `004940..005940` | `4D40..5D40` |
| Current and pending paths | 128 | `005940..0059C0` | `5D40..5DC0` |
| Browser/transport state | 256 | `0059C0..005AC0` | `5DC0..5EC0` |
| CDB scratch | 32 | `005AC0..005AE0` | `5EC0..5EE0` |
| Sense/discovery scratch | 64 | `005AE0..005B20` | `5EE0..5F20` |
| Two staged sample descriptors | 96 | `005B20..005B80` | `5F20..5F80` |
| RIFF/deinterleave carry and scratch | 256 | `005B80..005C80` | `5F80..6080` |

The listing allowance follows the current BlueSCSI limit of 100 entries,
requiring 4,000 bytes. A possible S-760 list limit of 126 is a separate user
lead, not a reason to increase the advertised count: use the lower verified
limit. A hypothetical 126-record wire list would occupy 5,040 bytes and would
not fit this 4,096-byte workspace. Revisit the layout only if protocol and
native UI qualification establish a different supported count.

This proposed layout is **not installed by the current diagnostic**. That
probe retains its buffer at physical `004400`, its 480-byte case table, 640-byte
result records and 26-byte context. Those test resources are not a measured
production browser footprint. Relocation, full code/UI sizing, native-call
scratch and guards still require implementation and validation. No spare local
bytes remain if every proposed allowance is consumed.

The separate stack allowance must be checked against the lowest native SP,
existing native frames and all reachable interrupt/callback nesting. The
earlier observed requirement of at least 186 bytes including the diagnostic
hook remains valid; it is not a maximum and does not justify the 512-byte
allowance by itself. Do not clear or reserve the existing native stack range.

## Shared-buffer ownership proposal

Only one operation may own the 4 KiB workspace at a time:

1. A successful listing may expose up to 100 complete 40-byte records. Store
   count and validity separately; unused bytes do not represent entries.
2. Before reusing the workspace for discovery or import, retain the selected
   original index/name and current path in separate browser state. Invalidate
   the listing before overwriting any byte.
3. A file read publishes only its successfully received, semantically valid
   length to the parser. The transport's byte count after an error or cancel
   does not authorize sample publication.
4. Streaming PCM conversion consumes the current block before the next read.
   Both stereo channels share one transaction: staged descriptors, allocation
   reservations and rollback state must outlive buffer reuse.
5. Returning to browsing requires a fresh listing. Errors/cancellation must
   reconcile directory/open-file state; a command may have completed before
   the cancel return. Buffer contents alone never establish validity.

Boot/entry must initialize all control fields, lengths, validity flags and
resource ownership before interpreting saved workspace bytes. A future session
restore must reconcile external directory/open-file state before another
Toolbox transaction. The native RAM checkpoint cannot prove that a physical
device retained matching state. The parser, publication/rollback mechanism
and these browser state transitions remain unimplemented.

## Native lifetime evidence

The private image preserves the earlier 1,571-byte helper and 480-byte case
table, and seeds every other byte of the candidate with a nonzero pattern
(5,951 bytes). Only the candidate and the already qualified eight-byte Save
System diagnostic hook differ from the immutable original. The 530 helper
instructions round-trip decode unchanged.

Three fresh processes exercise ordinary sampling controls, armed same-build
session save/restore, stereo recording, native Sample Save and cold Sample
Load. All **24 initialized RAM snapshots** retain the complete 8,002 bytes.
A separate pre-restore snapshot has zero candidate RAM at 16.667 ms; restoring
the saved session recovers the exact code/table/pattern without boot-loading
the system disk in that process. Candidate CPU data-read/write observations
remain zero during this sampling workflow; the helper is present but not
executed there.

Both recorded channels contain **56,737 exact PCM16 frames**, each allocated
119,808 bytes. All 239,616 allocation bytes, including zero padding, agree
between recorded RAM, the saved floppy and cold-loaded RAM. The test reports
zero input underruns. This uses the opt-in offline 44.1 kHz ADC model; it does
not qualify physical input, other sample rates or real-time timing.

Completed modeled DMA copies provide evidence beyond CPU taps: the retained
logs contain 305 floppy reads, 370 wave/RAM copies and 91 floppy writes. Four
read intervals overlap the candidate, all from the two normal system boots
and all with `disk_offset - RAM_address = 4800`. The armed-restore process has
no such boot copy. No later logged DMA copy overlaps the candidate. This does
not establish all possible physical DMA modes or all native workflows.

The host wrapper's final report initially failed on a relative-path conversion
after native acceptance completed. A separate read-only validator checked the
retained outputs and explicitly separated the pre-restore zero snapshot from
the 24 initialized snapshots. The effective patched-image identity is recorded
by the wrapper and confirmed by RAM bytes; the inherited sampling result also
retains its original requested configuration identity. No guest evidence was
changed to repair reporting.

A fourth fresh process enters the same helper with seeded mutable bytes. All
20 cases pass, including deliberate errors/sense and timeout/poll exits, with
1,800 interrupt service points and restored caller scratch/banks. The prefilled
cancel word resets to zero. Only physical `0043FE..005402` (buffer and guards),
`005600..005880` (records) and `005BF0..005C0A` (context) change; code, table and
all remaining seeded bytes retain their initial values. All candidate bytes
then remain stable through native HDD Load/playback, retaining 13 samples and
119,808 exact allocation bytes, unchanged HDD export and a silent final second.
The four additional snapshots bring this checkpoint to 29 snapshots in four
processes. This qualifies initialization of the existing probe; the future
browser's full control/ownership state still needs its own initialization test.

## Remaining ownership gate

Complete static users and indirect aliases; qualify nested dialogs, LCD and
GB-6 paths; size the full code/UI footprint; validate the relocated shared
workspace and initialization; and bound native stack use. Existing HDD/CD
transitions, Save System, sampling and session restore remain distinct test
cases. The observations support a candidate and a concrete budget, not a
complete reservation or a BS1 PASS decision.


### Additional session-caller stack observation (2026-10-18)

Four manufacturer41 session remote-owner runs reach a read-only observed stack
low-water mark196 bytes below the0166:8C68 continuation stack pointer. Remote
entry is18 bytes below that continuation because of the banked wrapper/return
frame. Scratch RW1C..6A, selectors and WSR restore across that path; timer-service
gaps stay below42.780 ms in these runs. This extends observed workload coverage,
not the complete stack/interrupt proof or approval of the proposed512-byte
allowance. [Evidence](../condensed/validation/bluescsi-session-2026-10-18.json).


The BUG-125 helper occupies physical0046A0..0046BF, file008EA0..008EBF, fetch000F:0AA0..0ABF. Its tail-jump implementation adds31 code bytes, no call frame and no persistent RAM. [Evidence](../condensed/validation/bluescsi-early-cancel-2026-10-18.json).


### Combined diagnostic placement (checkpoint25, 2026-10-18)

The twenty-fifth checkpoint qualifies a combined diagnostic layout in the native emulator. The old 4 KiB transport buffer overlapped the SDS helpers by703 bytes. Relocating the buffer to physical004940, the480-byte case table to0046C0 and640-byte records to005944 removes that collision. All20 transport cases pass, including expected status/sense errors and timeout recovery. A separate panel Exit run latches cancellation after629 bytes, drains the current4096-byte read and starts no later command. Both runs subsequently load13 HDD samples with all119808 PCM bytes exact and pass playback/silent release. Eight RAM snapshots preserve all code, SDS patch spans, the case table and354 seeded gap bytes. This qualifies coexistence for these workflows; SDS cancellation/retry execution after transport remains to be tested. Retained code is2402 bytes; the production budget still leaves only672 arithmetic bytes, with browser UI, WAV parsing, stereo transactions and full stack bounds unmeasured. BS1 remains OPEN. [Evidence](../condensed/validation/bluescsi-combined-layout-2026-10-18.json).


### Post-transport receive rollback (checkpoint26, 2026-10-18)

Checkpoint26 qualifies SDS receive cancellation and retry in the same native session after the combined transport diagnostic and HDD Load. One run executes all20 transport cases; another cancels the first read after629 bytes and drains it safely. A third run uses the prior SDS-only image without the diagnostic as a comparison. All three load13 samples, then show actual header admission (cursor13 to14), receive cancellation stateFE, rollback at0166:8B6B to13, and idle before retry. Cancellation-to-idle spans1.995390�1.996954 seconds in these runs. Retry reserves block13 and publishes the fourteenth live sample with160 exact received PCM bytes. All119808 existing HDD PCM bytes and13 descriptors remain exact; preceding playback/release and unchanged HDD export pass. The16 combined-image snapshots preserve all patch spans, code, case table and354 seeded gap bytes; the comparison adds seven snapshots. An initial exploratory two-second assertion caught FE after rollback but before cleanup ended; it is not an acceptance pass or evidence of a leaked allocation. The repeated traced runs establish cleanup and retry; the final cancellation run allows four seconds. No firmware repair was needed for this timing assertion. BS1 remains OPEN for full code/UI/WAV sizing, stack bounds, bounded sample writing and atomic stereo publication/rollback. [Evidence](../condensed/validation/bluescsi-combined-lifecycle-2026-10-18.json).


### Bounded stereo writes (checkpoint34, 2026-10-18)

Checkpoint34 qualifies guest-side stereo deinterleaving and bounded planar writes in an isolated native diagnostic. One4096-byte workspace holds2048 interleaved input bytes at physical004940,1024 left-channel bytes at005140 and1024 right-channel bytes at005540. The guest generates distinct16-bit left/right sequences, splits at most512 frames, and uses the bounded DMA adapter for each channel. Cases1,511,512 and513 frames preserve channel identity and sequence;513 requires512+1-frame chunks. All6148 payload bytes match exactly, including the two-byte-per-channel final tail. Ten payload DMA events match the expected source, destination, order and lengths.

Eight complete8192-byte channel/sentinel arenas match (65536 bytes), including every byte outside each payload. The13 previously loaded HDD samples retain all119808 PCM bytes, the HDD export is unchanged, and pre-diagnostic playback/release passes. No original firmware changed. Image SHA256:23a53f004a929af9120671464d05138ec40577947a41bd89e5ef58e7edf76e57.

The splitter measures32 code bytes, validation145 and DMA setup/polling80, totaling257 for these prototype pieces; the full diagnostic harness is1503 bytes. A conditional addition to the earlier2402-byte retained-code budget leaves415 of the3074-byte ceiling before parser, production ownership, publication and UI costs. This is a warning about the tight budget, not a linked fit measurement: the transport diagnostic still includes removable test code and these images are separate. The splitter assumes1..512 frames from its diagnostic caller; a production caller must validate that precondition. This design reads at most2048 PCM bytes per refill, within the reference parser's4096-byte maximum.

This closes only the bounded stereo write-path subcheck. Input is guest-generated, not read from WAV/BlueSCSI; destinations are test arenas, not native reserved/public samples. It does not prove stereo playback, pair-wide allocation, publication, rollback or cancellation between channels. Interrupts are masked, and physical DMA abort/quiescence remains unqualified. Next BS1 work is pair-wide ownership/reservation and right-channel failure rollback with descriptor publication held until both channels succeed. UI/code-reuse exploration remains deferred. BS1 stays OPEN. [Evidence](../condensed/validation/bluescsi-stereo-write-2026-10-18.json).


### Pair reservation and pre-publication rollback (checkpoint35, 2026-10-18)

Checkpoint35 qualifies pair-wide reservation and rollback before publication in a private native guest diagnostic. After ordinary HDD Load supplies13 samples, each attempt captures the original cursor and mirrors once, checks native free block capacity, and advances3616 plus the used-block mirror by two. Three attempts produce the observed sequence13->15->13, repeated three times. A65535-block request rejects without changing the native capacity or reserving storage. The retry therefore reuses blocks13/14 without a leaked allocation.

The left channel writes1024 bytes. Case1 then rejects an odd1025-byte right write; case2 cancels before the right write; case3 completes both1024-byte writes but deliberately rolls back without publication. Four read-only case captures verify the expected18432-byte pair region, all512 public48-byte descriptors unchanged, both allocation mirrors restored, native SDS backup1FA0 unchanged and all119808 existing PCM bytes exact. Unwritten right-channel bytes retain the sentinel. HDD export is unchanged and pre-diagnostic playback/release passes. The guest, not the host observer, performs the reservation and restoration.

The scoped reserve helper is43 bytes and rollback16 bytes inside a1450-byte harness. It checks a known13-block fixture and writes dedicated one-block channel extents; this is not a general slot allocator or complete32-bit address API. Interrupts are masked for the entire callback, so ownership is synchronous. Keeping an importer owner across interrupt/input service remains unqualified. No descriptor is constructed or published, and no in-flight DMA is aborted. The result establishes rollback before publication after right-channel rejection/cancellation, not atomic stereo import. Next: qualify safe staging/publication of the pair and its native object relationships, then interrupt-serviced ownership and combined size. UI reuse remains deferred; BS1 stays OPEN. [Evidence](../condensed/validation/bluescsi-pair-rollback-2026-10-18.json).

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



## Experimental LCD addition - 2026-10-19

Trial6141/8002,1861 free/1611 code-adjacent adds733 bytes to the5408-byte broader CRT baseline:495 code and238 LCD resource/temporary bytes. Native scoped LCD Load/playback and CRT cancellation/SDS pass; complete LCD UI, name identity, final-hash broad regression and full stack/ISR fit remain open. [LCD results](bluescsi-im1-lcd-results-2026-10-19.md). This is not a release or complete-fit GO.


## LCD full-name confirmation trial - 2026-10-19

Latest LCD candidate6487/8002,1515 free/1297 code-adjacent adds346 bytes to the6141-byte LCD trial (314 code+32 strings). Two native final-hash workflows,256 decoded guard cases and exact rebuild pass. Broader final-hash LCD/IRQ/session/stack/hardware qualification remains open. [Name-view results](bluescsi-im1-lcd-name-results-2026-10-19.md).


## Current native IRQ analysis - 2026-10-20

Current OS6297274d... remains6452/8002 bytes,1550 free/1332 code-adjacent. A152-function/9181-instruction native IRQ graph gives a conditional62-byte timer/control/wave contribution under the stated fetch-page, jump-table state and interrupt-owner assumptions. Complete native caller/callee composition and indirect ownership remain open. Parser000F:213A drains a live MIDI ring without an identified service quota, so stack closure does not establish bounded service time. Do not add62 to the166-byte custom contribution and call it a proven total. [Results and limitations](bluescsi-im1-final-gates-results-2026-10-20.md).


## IM1 dense-MIDI timing counterexample (2026-10-20)

Unchanged6297274d... preserves all7360 immutable/gap bytes across177 new native snapshots (642 mutable excluded). Allocation remains6452/8002,1550 free/1332 adjacent; complete indirect-alias and native caller/callee/ISR bounds remain open. Dense notes during D7 preserve769 MIDI bytes and188 matched service contexts; lowest observed SP1030 is not a worst-case bound. One service lasts479.111125ms: timer-read interval479039 ticks gives modulo delta20287, omitting458752 ticks/seven wraps. BUG-168 tracks bounded service and wrap-safe outer elapsed accounting. Correct modulo RW38 idle adjustment does not recover lost whole wraps in the total deadline. [Results](bluescsi-im1-safety-batch-results-2026-10-20.md), [validation](../condensed/validation/bluescsi-im1-safety-batch-2026-10-20.json).


### Browser parser admission and memory limits

Experimental OS367f067d... adds an89-byte native parser-admission helper at000F:1400 (physical005000, file009800), reached by the3-byte hook at000F:213A (file00A53A). Context word005BDA holds32 admissions while browser service is active;16000 timer ticks stop further admission, and masked continuation scheduling preserves pending MIDI. Outside service the original parser path is retained. Exact rebuild/disassembly and GB-6 v9/SDS checks pass. Allocation6580/8002 leaves1422 free; largest remaining code gap1191. This does not promote the experimental hash over established6297274d... .

Dense MIDI parses775 bytes exactly, has no observed overflow, preserves188 service contexts and releases notes; maximum28.006625ms and no lost whole timer wraps are observed. BUG168 remains IN-PROGRESS because the single-byte/control-ISR bound and total wall-time deadline are unproved. The helper adds8 local stack bytes; this and the earlier166-byte custom/conditional62-byte IRQ figures are not a composed native bound. All7360 immutable/gap bytes survive111 new snapshots (18 established,93 trial), with642 mutable bytes excluded; the trial hook is also preserved. Indirect aliases/DMA and native stack remain open. [Results](bluescsi-im1-timing-recovery-results-2026-10-20.md), [validation](../condensed/validation/bluescsi-im1-timing-recovery-2026-10-20.json).


## Synchronous native-callee composition, 2026-10-20

The trial367f067d... analysis resolves all10 native browser helpers through46
contextual functions/904 unique instructions and byte-audited CE14/CDED far
wrappers. Browser plus synchronous-callee maximum remains166 bytes including
the80-byte common frame. Dispatcher ancestry, IRQ nesting/state assumptions and
indirect DMA/resource ownership remain open;166+62 is not a total-stack proof.
Eleven native cases add91 unchanged7360-byte immutable/gap snapshots, excluding
642 mutable bytes. Wording successors ecdbd721.../79124692... preserve their
predecessor allocations6452/6580 of8002 bytes; four native warning resources
change without growth. Timing trial remains experimental.
[Results](bluescsi-im1-format-fdc-stack-results-2026-10-20.md).


## IM1 native bounds and unchanged allocation (2026-10-20)

The four immediate init/update/exit/action dispatcher frames each use12 bytes (five saved words plus synthetic return). Observed outer prefixes28/30/62 are route observations, not global maxima. The prior166-byte synchronous and conditional62-byte IRQ figures are not an additive total proof. Parser000F:25A6..25FC has at most32 comparisons per sentinel scan and528 total across32 insertions into16 records of33 bytes, assuming no concurrent external writer. Native MIDI TX-ready001F:68A2 and wave-port-ready7118/7344 still need completion bounds.

Same-size Verify Medium repair leaves established6452/8002 and trial6580/8002 allocations unchanged. Nine accepted native cases/93 snapshots preserve7360 immutable/gap bytes with642 mutable exclusions. Simultaneous stalled-target/MIDI fails the byte check; full native timing/ownership remains open. Evidence: [validation](../condensed/validation/bluescsi-im1-verify-stall-bounds-2026-10-20.json).


## IM1 repaired redraw and authored-image loading (2026-10-20)

Candidate5e5ec016... adds3 bytes to call the existing caller-qualified service between880 CRT character clears. Both actual simultaneous D7 stall/MIDI cases (byte1/3999) preserve775 reads,239616 stereo bytes and playback/release. Original dense D7, CRT/LCD cancellation/names, SDS and Remote Mode regressions pass:10 native cases/104 snapshots. BUG175 is fixed independently of BUG168, whose full service/deadline proof remains open. Allocation6583/8002 leaves1419 free; synchronous stack166 bytes unchanged, no total IRQ/ancestry proof. GB-6 v9/boot/SDS/Verify Medium/warnings retained. BUG174 fixes the minimal authored header and tests first real ROM handoff with112 tracks/all1032192 loaded bytes; no runnable-example-OS claim. Full suite1089 pass/3 skip, no failures. Physical qualification and upstream BlueSCSI defects remain separate. BUG140's abandoned descriptor experiment is WONTFIX, not repaired. [Evidence](../condensed/validation/bluescsi-im1-bug-fixes-2026-10-20.json).


BUG168 native policy successor (2026-10-20): e78750c2... uses6736/8002 named bytes (1266 free), main browser4111 bytes atphysical4080..508E, existing89-byte parser helper at5100..5158,935 contiguous bytes before5500. C+30 saves native performance mode; C+31 leases action suspension. Boot and GB-6 v9 unchanged. The earlier166-byte synchronous stack bound is not a current complete bound: include native001F:4F8D and its callees. See docs/project/bluescsi-bug168-native-policy-results-2026-10-20.md and docs/condensed/validation/bluescsi-bug168-native-policy-2026-10-20.json.


Current synchronous stack successor (2026-10-21): e78750c2... now includes001F:4F8D suspend/restore and its eight-function closure. Native11-root/54-function/1211-instruction graph has balanced returns and original-matching bytes. Callback maxima166/90/156/166 include80-byte common frame; transition path112. Immediate dispatcher12 bytes is outside these maxima. IRQ152-function/9212-instruction graph closes conditionally;62-byte IRQ contribution and outer/recursive dispatcher ancestry still need invariants. No complete total stack bound is claimed. Firmware/allocation unchanged. See docs/project/bluescsi-im1-current-stack-results-2026-10-21.md and docs/condensed/validation/bluescsi-im1-current-stack-2026-10-21.json.


Named CRT ancestry (2026-10-21): e78750c2... fresh native15309 callbacks all restore SP with zero nesting. Exact saved return chains match update28/action30/open62/exit62-byte entry prefixes; CF7F/D3A8 retries are tail jumps. Native/declared-domain IRQ graphs do not reach browser dispatchers/callbacks under normal return/state assumptions. Observed total248 bytes is not a worst-case bound. Additional modal/LCD ancestry, IRQ invariants and indirect ownership remain open. No firmware/allocation change. See docs/project/bluescsi-im1-ancestry-results-2026-10-21.md and docs/condensed/validation/bluescsi-im1-ancestry-2026-10-21.json.


Final owner-transition candidate (2026-10-21):606e277e... adds24 guard bytes,6760/8002 total,1242 free. Main4135 bytes physical4080..50A6,89-byte gap before parser5100..5158;935 contiguous bytes remain after that helper before5500. Synchronous maximum166 unchanged. Current CRT/LCD ancestry prefixes28/30/62 and20/20-mask IRQ56 give conditional284-byte named-route envelope; no universal native-state/stack-region/alias proof. Ten production cases/101 snapshots preserve main/parser/SDS bytes; six further native gate workflows and1123 backend passes/3skips. See docs/project/bluescsi-im1-owner-and-recovery-results-2026-10-21.md.
