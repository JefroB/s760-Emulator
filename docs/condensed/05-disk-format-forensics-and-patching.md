# Disk Format, Forensics & Patching

## BlueSCSI feasibility baseline — 2026-10-18

The stock OS now independently qualifies sample-rate codes `0..7` as
48/44.1/24/22.05/30/15/32/16 kHz. Mono preview frequencies agree within
0.050861% for identical 40-cycle/4,096-word sine fixtures; all rate labels
match. Descriptor `+24` selects Forward=0 or OneShot=2, while `+2C` holds the
rate code and `+2D` the root key. Five fixed-point addresses at
`+10/+14/+18/+1C/+20` represent Start, Loop start/end and Release-loop
start/end, confirmed by distinct native screen values and RAM. BUG-114/115
correct the sample builder's mislabeled controls with explicit fields while
preserving both historical preset images byte-for-byte. Ten allocations load
92,160 bytes exactly; 28 focused tests and 588 backend tests pass with zero
skips. This does not qualify arbitrary WAV padding or stereo at every rate.
[Sample contract](../project/bluescsi-sample-contract.md),
[native/byte evidence](validation/bluescsi-sample-contract-2026-10-18.json).

The SDS allocator has a single cursor backup at `1FA0`, captures `3616`,
stages one 48-byte descriptor at `1F6E`, and publishes only in its successful
supervisor path. Two independent calls would overwrite that backup; the
proposed stereo importer needs one reservation/rollback owner and two staged
descriptors. Atomic publication, exclusive ownership, importer-driven object
creation and failure during the second channel remain unimplemented.

Native SDS length probes now bound this reuse risk. For 16-bit/44.1 kHz
OneShot headers with loop start0/endN-1, reservation is ceil((N+13)/4608)
blocks, descriptor points are0/0/N-2/N+8/N+12, zero-fill writes4608 words from
B+N+12, and packets write40*ceil(N/40) words. Eighteen lengths plus settled
cancel/retry retain249,760 transmitted bytes and3143 exact acknowledgments
across54 snapshots. The9203-word case writes24 packet words beyond its reserved
9216; zero-fill exceeds its reservation by up to4607 words in this matrix.
These loops are excluded from direct bounded-WAV reuse. Native mono cancellation
restores the cursor without publication; safe retry waits for UI/state cleanup.
Early retry can retain an unpublished allocation in the stock OS (BUG-118).
The opt-in guard below repairs the observed cancellation case. BUG-116/117
fix missing native MIDI output and sequential C00A wave writes; both regressions
first failed, and590 backend tests plus ordinary runtime/audio checks pass.
[Length/ownership contract](../project/bluescsi-sample-contract.md#sds-length-boundaries-and-cancellation),
[native and byte evidence](validation/bluescsi-length-contract-2026-10-18.json).

The cancellation trace identifies the old supervisor's `0166:8905` state clear
after rollback and a newly accepted header. The experimental OS guard rejects
headers when `2BBA` is nonzero before decoding/allocation, emitting the existing
CANCEL response. Its 36 changed bytes repack the existing 51-byte dispatcher at
file `00F0DD..00F10F`; no additional RAM or unqualified free space is used.
BUG-118 is fixed for this native cancellation case. Three timings preserve
staging, existing allocations and all unrelated public descriptors, then publish
nine exact samples/28,800 PCM bytes through settled retries and follow-on work.
The four SDS runs retain 63 snapshots, including the stock negative control;
375 ACKs and six CANCEL responses match. Three focused tests cover 65,536
command/state combinations and image safety; ordinary patched-OS playback,
scheduled MIDI and audio rendering pass. Original firmware and native driver
remain unchanged. This cancellation-only guard leaves success/error admission
windows, repaired for incoming headers below; complete transaction ownership,
stereo transactions, bounded WAV writing and physical/controller acceptance
remain open.
[Guard and reproduction](../firmware/os/os-transfer-lifecycle.md#native-cancellation-overlap-and-private-os-guard),
[validation](validation/bluescsi-cancel-ownership-2026-10-18.json).

The extended private firmware repairs two further header-admission windows
(BUG-119): a new header could replace a descriptor awaiting publication or
reserve unpublished memory during error cleanup. Completion state FF now stays
busy until publication/UI cleanup, while allocation errors retain their state
until the common final clear. Six existing code spans total 123 bytes, with 96
bytes changed and no new RAM/free-space assumption. Two prior-image failures
and four final native runs retain 78 snapshots. Eleven samples match 10,800
transmitted PCM bytes; all 148 ACKs and five CANCEL responses match. The short
burst case observes FF at supervisor entry and then exact publication; ordinary
cancellation remains valid. Seven focused tests and patched-OS playback/MIDI/
audio checks pass. An intermediate marker-80/JGT failure is retained and
excluded. Original firmware and emulator remain unchanged. This is header-only
exclusion: other SDS/disk operations, pre-supervisor cancellation, native resource
exhaustion, atomic stereo publication and physical/controller behavior remain
open. The bounded WAV writer is still required.
[Header lifecycle contract](../firmware/os/os-transfer-lifecycle.md#header-admission-through-publication-and-error-cleanup),
[evidence](validation/bluescsi-header-lifecycle-2026-10-18.json).

The request guard additionally repairs BUG-120: command03 could enter sender
setup at `001F:6990`, clear active/completed receive state and discard pending
publication. Busy requests now return CANCEL before slot decoding or voice
stop. Two existing spans add19 changed bytes to the header patch, for115 total
changed bytes across167 bytes of existing code; no extra RAM/stack is used.
Seven final native runs publish18 exact samples/2,880 transmitted PCM bytes
with56 ACKs and five CANCEL replies. An idle dump sends9,216 exact sample bytes
through116 packets plus one exact retransmission, then accepts another receive.
Two prior-image failures and one prior ACK control retain118 snapshots in total.
Ten focused tests and ordinary patched-OS playback/MIDI/audio pass. This is
receive-owned request exclusion; already-active sender ownership, disk work,
stereo transactions, bounded WAV writing and hardware/controller qualification
remain open. Original firmware and native sources remain unchanged.
[Request contract](../firmware/os/os-transfer-lifecycle.md#receive-owner-exclusion-for-outgoing-requests),
[evidence](validation/bluescsi-command-exclusion-2026-10-18.json).

The shared admission guard repairs BUG-121's opposite-direction overlap:
while B1AE is1 (waiting for ACK) or0 (data), 2BBA remains0, allowing another
header/request to overwrite the sender. Commands01/03 now require 2BBA=0 and
B1AE=FF. A helper in the existing header span computes `(B1AE+1)|2BBA` modulo
256 and returns flags; busy callers emit CANCEL without decoding. Reusing the
original6AA5 counter initializer frees the code space. There is no new RAM or
code region, but admission/counter calls use temporary two-byte stack frames.
The combined image changes146 bytes in204 bytes of existing spans;89 replacement
instructions decode. Ten final native runs preserve28 received samples/4,480
PCM bytes and four complete dumps/36,864 bytes, with exact retransmission,
completion/cancellation and later stale-handshake rejection. All86 ACKs, nine
CANCEL replies and469 data packets match. Two prior failures bring the total
to182 snapshots. Thirteen focused tests include131,072 admission cases; ordinary
patched-OS playback/MIDI/audio pass. Disk exclusion, abandoned-sender recovery,
full stack/interrupt bounds, stereo atomicity, bounded WAV writing and hardware
qualification remain open. Sender fixtures occupy one allocation block.
[Shared admission](../firmware/os/os-transfer-lifecycle.md#shared-admission-for-active-senders-and-receivers),
[evidence](validation/bluescsi-sender-ownership-2026-10-18.json).

Local Sample Dump has a distinct UI owner and no-ACK fallback. Its stock
cleanup writes B1AE=0, which conflicts with the experimental FF-idle guard
(BUG-122). Three existing 28-byte tails now converge on parser/display cleanup
and a final bank-preserving FF release. The helper saves one two-byte selector
word; the complete stack bound is still open. An initial repair failed Exit
because display cleanup changed the data bank; that candidate is excluded.
Four final local completion/cancellation runs and one remote-stall/recovery
run preserve15 received samples/2,400 PCM bytes, two full dumps/18,432 bytes,
45 ACKs, two CANCEL replies and251 data packets. Twenty-four focused tests
and ordinary runtime/audio checks pass. The third error tail has decoded/unit
coverage only. Its remote no-ACK counterexample remains busy after60 seconds
and panel Exit; MIDI CANCEL releases it. [Cleanup contract](../firmware/os/os-transfer-lifecycle.md#local-sample-dump-cleanup-and-remote-stalls),
[evidence](validation/bluescsi-local-sender-lifecycle-2026-10-18.json).

BUG-123 is now fixed in experimental firmware with a foreground remote owner.
Successful command 03 setup claims 2BBA=7; the original 87B5 supervisor dispatches
that state into a 640-byte helper at 000F:0780..0A00 (end-exclusive). Five seconds
without packet-counter progress or panel Exit marks sender idle, emits CANCEL
and releases ownership without modifying samples or rolling back allocation.
Completion and peer cancellation release without an extra CANCEL. A separate
1,048,576-poll budget has decoded/model exhaustion coverage. Seven native remote
cases and four local compatibility cases preserve 33 received samples/5,280 PCM
bytes, three complete dumps/27,648 bytes, all 99 ACKs, seven CANCEL replies and 371
data packets. A negative control brings the total to 180 snapshots. Thirty
focused tests and ordinary runtime/audio pass. Caller scratch, selectors,
WSR/PSW and SP restore in the observed main-loop calls. Maximum timer-read gap
is 42.710 ms; observed stack depth is 182 bytes, not a worst-case bound. Native
callee waits, other caller contexts, local UI races, Disk exclusion, complete
code/stack fit, stereo atomicity and bounded WAV writing remain open. No physical
acceptance or released OS is claimed. [Recovery contract](../firmware/os/os-transfer-lifecycle.md#foreground-remote-sender-recovery),
[evidence](validation/bluescsi-remote-recovery-2026-10-18.json).

BUG-124 closes the observed local completion gap: final ACK plus an immediate
header previously reserved a block before local cleanup cleared the new owner;
final ACK plus a request similarly discarded remote ownership. A160-byte helper
at 000F:0A00..0AA0 now checks local admission, claims state 8 before shared setup,
retains nonzero ownership through completion/error display, and releases only
after parser cleanup under PUSHA/POPA. Nine accepted native cases preserve 27
samples/4,320 received PCM bytes and five dumps/46,080 bytes, with 81 exact ACKs,
six CANCEL replies and 601 data packets. Two prior-image controls bring the total
to 175 snapshots. All 96 focused tests and runtime/audio checks pass. Busy local
entry and setup-failure cases have decoded/model coverage; remaining input
timing, native Disk exclusion, complete code/stack fit and atomic stereo import
remain open. [Local owner contract](../firmware/os/os-transfer-lifecycle.md#local-ownership-through-setup-and-cleanup),
[evidence](validation/bluescsi-local-owner-2026-10-18.json).

The current browser profile retains100 total directory entries from BlueSCSI's
protocol limit (4,000 bytes in the4,096-byte shared workspace). A possible
S-760 limit of126 is an unverified, separate native-list constraint; effective
capacity is the lower verified limit. It does not authorize a126-entry wire
list, which would require5,040 bytes. [Memory contract](../project/bluescsi-memory-contract.md).

Ordinary native permanent stereo assignment is now qualified separately:
Partial SMT assigns public sample references0/1 with E0/20 pan; Patch Split
maps88 keys to partial0; Perform part1 selects patch0. Naming the three objects
changes their initial7F marker to space and makes them eligible for Disk Save.
Two stock-OS processes,25 snapshots and238 replayed CPU stores preserve all736
record bytes through Save/cold Load. The disk contains1 performance,1 patch,
1 partial and2 samples; all239,616 PCM allocation bytes remain exact. Cold
Perform Play succeeds while preview partial255 is unassigned. Seven audio
cases retain L/R at a common source position with relative RMS fit error below
4.016e-8 and silent final release seconds. Eleven byte-checked store anchors
identify construction points, not callable ABIs. No importer, other-rate
stereo or physical acceptance is inferred.
[Permanent assignment contract](../project/bluescsi-sample-contract.md#permanent-playable-hierarchy-and-persistence),
[evidence](validation/bluescsi-permanent-assignment-2026-10-18.json).

Original-OS native stereo capture/Save/cold Load retains 56,719 frames per
channel, two 13-block allocations, exact PCM and matching reloaded RAM sample
descriptors. Recorded preview partial255 references slots0/1 with bytesE0/20;
cold Sample Load alone leaves that preview partial unassigned. The follow-up
enters Loop/Smoothing through ordinary controls and reconstructs preview slots
512/513. Selecting either L or R preserves output channel order by reversing
the preview records and E0/20 routing bytes together. Both outputs match their
distinct source patterns at a common source position; relative RMS fit error
is at most 4.02e-8. Mono audition centers either selected member, Stereo restores
the pair, and all five cases release to silence. The public descriptors and
exact PCM allocations remain unchanged. This qualifies this 44.1 kHz fixture's
preview behavior, not importer construction, permanent patch assignment,
other rates or physical fidelity. [Follow-up evidence](validation/bluescsi-stereo-ui-followup-2026-10-18.json).
The separate HDD baseline retains13 samples and119,808 exact bytes through Save
and cold Load. Native caller observations also confirm six-/ten-byte command
templates at003B:7592 and a matched10-byte PIO sense read at003B:7B14. The sender's
fixed02CC operand page, class-dependent CDB byte1 mutation and unbounded inner
polls prevent treating it as a ready Toolbox client. [Contracts, fixtures and
limitations](../project/bluescsi-feasibility.md).

Native Save System also preserves the lower-candidate data marker exactly;
cold boot from that export still loads and auditions the stereo fixture with
239,616 exact PCM allocation bytes and silent release. Native initializer
`004B:794A` clears `RW2E`, skips its conditional bus reset on that entry, and
updates shared drive state. It is not transparent cleanup. TIMER1 provides
the nominal microsecond counter for a bounded client; full recovery remains
unqualified.
[Memory/timer evidence](validation/bluescsi-memory-transport-2026-10-18.json),
[proposed transport contract](../project/bluescsi-transport-contract.md).

A private patched OS now enters a limited guest transport diagnostic through
ordinary Disk → Save System (CRT index `0112`, descriptor `023F:B22A`, callback
`0181:9040`). It preserves all ten CDB bytes, observes three-byte short DATA IN
and zero-data completion, distinguishes transport failure from CHECK CONDITION,
and reads sense separately. A guest-held ACK exits on a 5,000-tick inactivity
limit at 5,010–5,011 ticks, including an observed TIMER1 wrap; a separate finite
poll guard exits at 165 ticks. Caller registers/banks are restored and ordinary
HDD Load/playback then retains 119,808 exact PCM bytes with silent release.
The final 14-case diagnostic masks interrupts for 20.32825 ms. At that checkpoint,
DATA OUT, cancellation, full buffers, independently stuck targets and controller/bus
reset were not qualified. Reserved-field CDBs prove byte preservation only.

BUG-113 changes native unsupported opcodes from false GOOD to CHECK CONDITION
with per-target sense `05/20/00`. The boot ROM's `1B 00 00 00 01 00` START UNIT
request is explicitly supported for already-ready image targets; unmodeled
stop/eject/power transitions return invalid-field sense. The native SCSI boot
and fallback regressions pass. Final build `b5036f4de04d0eb1007730a9120efb85278e219663bb73026ab32e4f0ec24524`
passes all 561 backend tests (zero skips), the guest probe/HDD workflow, stock-OS
full-CD Load/playback/two-process cold recall and standard native runtime checks.
Fifteen legacy screenshots and their parsed Lua outputs match the pre-change
build exactly across 27 legacy tests. This is scoped regression evidence, not
physical BlueSCSI or complete Toolbox/browser acceptance.
[Fourth checkpoint and reproduction](validation/bluescsi-guest-transport-2026-10-18.json).

On that unchanged build, the 16-case guest follow-up verifies exact 4 KiB
DATA IN/OUT and independent command status/sense. Unsupported opcode, invalid
START fields, out-of-range WRITE and protected-CD WRITE return CHECK CONDITION
with sense `05/20/00`, `05/24/00`, `05/21/00` and `07/27/00`; successful sense
retrieval does not overwrite the original failure. Complete 16 KiB scratch-image
captures after every case isolate one successful 4 KiB write and prove no
additional mutation after rejected/incomplete writes. Incomplete-WRITE atomicity
is emulator staging behavior, not a physical-device guarantee. Guard words and
unread buffer contents remain correct. Subsequent native HDD Load/playback
retains 119,808 exact sample bytes and releases to silence.

Six long transfers cross 28 TIMER1 wraps; elapsed counts agree with machine
time within one tick. The old 20 ms prototype failed after 258 read bytes and
rejected DATA OUT; the extension uses a bounded diagnostic total budget of
1,048,576 ticks. Full transfers take about 295–297 ms and the complete sequence
masks interrupts for 1.897658 seconds. Interrupt servicing, cancellation and
independent target-fault/reset qualification remain required before a usable
client; no actual Toolbox or physical acceptance is claimed. No new emulator
change or repeat full-suite result is implied.
[Transfer/error contract](../project/bluescsi-transport-contract.md#full-buffer-and-deliberate-error-matrix),
[fifth checkpoint](validation/bluescsi-transfer-errors-2026-10-18.json).

The next private OS probe adds explicit interrupt service points while retaining
the full buffer/error matrix. The final 20 cases also qualify held-ACK timeout
at 5,016 ticks, absent target at 23 ticks, eight-poll exhaustion at 178 ticks,
and successful TUR afterward. Across 1,800 service points, the original firmware
handles 169 timer interrupts and six ordinary MIDI bytes. All transport scratch
and bank mappings restore; native timer/MIDI state advances. The IC4 SCSI/DMA
source is masked while the helper owns the bus, and the original mask restores.
No SPC register writes occur inside the observed ISR service periods.

The 2.550933-second sequence has a conservative 5.018625 ms observed bracket
for masked spans; this includes extra enabled time and is not a worst-case
latency bound. Guest TIMER1 sample gaps remain below a wrap. Exact command/data
bytes, original status/sense, complete scratch-media captures, guards and
subsequent native HDD Load/playback pass. The tested Save System screen is muted;
concurrent audio, dense MIDI, browser input dispatch/cancel, broader ISR/stack
bounds and physical interrupt routing remain open. In particular, the current
native model does not route raw SPC command/status IRQs to the CPU. This advances
BS1 without closing it or implying a new emulator build/full regression run.
[Interrupt contract](../project/bluescsi-transport-contract.md#interrupt-cooperation-follow-up),
[sixth checkpoint](validation/bluescsi-interrupt-cooperation-2026-10-18.json).

The following cancellation probe uses ordinary panel Exit, latches the request
in its own workspace and drains the current bounded command before stopping
later transactions. Read and held-Exit WRITE tests latch at 629 bytes and finish
the 4 KiB command before returning cancelled about 308–309 ms later. A WRITE
therefore still commits its intended range. Panel Up does not cancel; ordinary
re-entry resets the latch and completes the 20-case matrix. The original helper
fails the cancellation check as expected, continuing all 20 commands.

A diagnostic initiator stall after real Exit preserves timeout outcome `3`
instead of masking it as cancellation, and returns in 5.050 ms after the latch.
Its buffer contains one in-flight byte beyond the 608 completed handshakes;
failed/cancelled buffers must not be published as samples. This is not an
independent target-stall or physical ABORT/reset result. All five fresh passing
processes retain exact payload/media and state-restoration checks and then load
13 HD0 samples / 119,808 exact bytes, audition/release and export unchanged HDD
content. Six invocations cover 45 executed cases. The native emulator build and
original ROM/OS remain unchanged; full browser input handling, independent
fault recovery and importer publication/rollback are still open.
[Cancellation contract](../project/bluescsi-transport-contract.md#ordinary-exit-cancellation),
[seventh checkpoint](validation/bluescsi-cancellation-2026-10-18.json).

The seeded-memory follow-up preserves the entire 8,002-byte lower candidate
through an armed same-build checkpoint restore, native stereo capture, Sample
Save and cold Load. Both channels contain 56,737 exact frames, with all 239,616
allocation bytes matching between recorded RAM, disk and cold-loaded RAM.
This is another 44.1 kHz offline-ADC fixture, not a new rate/importer claim.
A separate fresh process executes all 20 transport cases from seeded workspace
and then loads/auditions the unchanged 13-sample HDD fixture. The native build
and original ROM/OS remain unchanged. Save System persistence and emulator
checkpoint restoration do not synchronize a physical device's open file or
directory state; future browser entry/restore must reconcile that state.
[Memory lifetime contract](../project/bluescsi-memory-contract.md),
[eighth checkpoint](validation/bluescsi-memory-lifecycle-2026-10-18.json).

## Full native Roland SCSI performance Load — 2026-10-14

The complete606,709,760-byte JMD S760 freeware CD now boots as an external CD1
profile, reports Formatted, lists all10 volumes and loads K4 :KAWAI K4 through
normal Disk/Load. The firmware restores its native performance/patch/partial
hierarchy; no Akai conversion or host-generated sample injection is involved.
All79 K4 sample allocations/6,054,912 bytes match independent source FAT-chain
reads exactly. Three channel1 drum notes and channel2 note60 produce bounded
finite audio and release to a full silent second. Two cold processes replay
65536 stereo frames exactly; changed-CD preflight rejects before native restore.

BUG-070 separated immutable CD identity from mutable state: both managed
launchers stream-hash recognized CD filenames, allowing1 GiB aggregate read-only
CD content, while writable SCSI media retain64 MiB aggregate checkpoint storage.
CD contents are excluded from native machine state; the imported session is
171,072,219 bytes. Mounted CD writes still fail before DATA OUT. External CD
filename/content are required on recall; this guard belongs to managed launchers.
Older-build checkpoints reject by build identity; no migration is qualified.

BUG-071 implements observed SCSI-to-wave DMA84. Native code page003B:7CD0..7D29
programs wave address and gate count then waits for SPC completion. The gate
carries the low16 bits of the full24-bit SPC length; treating a118,784-byte
request as53,248 leaves65,536 bytes pending and freezes firmware controls.
Bounded36/65,536/118,784-byte regressions, counter/address advancement, invalid
bounds and CD write rejection pass. Prior RAM47/PIO/register contracts remain
qualified;389 backend tests, core/plugin units, full-CD C++ host playback and
writable-SCSI checkpoint recall pass. All changed artifacts build successfully.

The qualified scope is this CD1/2048-sector image and first K4 performance at
32 MB RAM. Other volumes/libraries, SCSI Save, hot-plug, physical arbitration and
final packaged interface repetition remain separate work.
[Exact identities, commands, source samples and limits](validation/milestone-5-roland-scsi-load-2026-10-14.json).

## Genuine Akai S1000 SCSI Convert Load — 2026-10-14

Original IC15/OS2.24 imports the first volume of the supplied String.Ensembles CD
through CD1,2048-byte sectors and32 MB wave RAM. Convert Load produces the
VI LONG FF patch and30 samples, totaling13,568,196 PCM bytes. The imported patch
is then assigned to performance part1 through the firmware's Value control.

A bounded independent reader follows the fingerprinted volume directory/FAT and
150-byte S1000 sample headers. Every source PCM word matches native wave RAM
except107 words in the four-word regions after aligned loop boundaries.
A read-only native wave-port observer records240 writes without drops: source
values are first transferred correctly, then the original firmware rewrites
those regions. Converted values match those writes exactly. The complete32 MiB
wave dump is byte-identical to an unobserved fresh conversion. This is observed
firmware conversion behavior, not proof of physical loop/DSP equivalence.

MIDI55/72/96 produce finite bounded output and release to a full silent second.
The source and private CD backing hashes remain unchanged. Two fresh processes
restore the imported session and produce65536 identical stereo frames, then
release silently. Backend388 regressions pass. Failed exploratory probes
included an insufficient45-second conversion wait, audition before assigning
an imported patch, and overbroad diagnostic capture; these are not product fixes.

This qualifies one genuine Akai CD/volume/program through native firmware;
at that checkpoint native Roland-format Load was still pending. The later full
Roland qualification is above. Other Akai CDs/device profiles, SCSI Save/writeback,
hot-plug and final packaged media selection remain unqualified.
[Exact fixture/artifact identities, command and results](validation/milestone-5-akai-scsi-load-2026-10-14.json).

## Native SCSI prerequisite correction — 2026-10-14

Original IC15 initialization accesses the SPC registers at E400/E402/E404/E408,
physical102400/02/04/08. Native decoding now uses a two-byte stride through the
16-register address window; TEMP and transfer-counter ports are accessible.
Native SELECT uses command20 and reports command-done10 or absent-target timeout04;
INTS reads preserve pending status until explicit write acknowledgement. Controller
reset uses SCTL40, bus reset SCMD10. These definitions agree with the
[original NetBSD MB89352 register header](https://raw.githubusercontent.com/NetBSD/src/trunk/sys/dev/ic/mb89352reg.h)
and the isolated native register fixture. Synthetic blank targets0/1 are retained
only for the legacy flat/HLE device fixture; native targets require supplied files.

Native SSTS now reports idle empty-data/zero-counter as 0x05 rather than the
incorrect constant 0x28 (busy/reset). TC-zero follows the programmed counter;
reset follows SCMD assertion/deassertion. The failing-before/passing-after native
fixture also checks idle recovery after absent selection. BUG-065 is fixed for
this direct-data status contract; this does not add an asynchronous FIFO engine.
[Status regression and native/state evidence](validation/milestone-5-scsi-status-2026-10-14.json).

## Native SCSI discovery and unsupported-media recovery — 2026-10-14

Native BDID reads now expose1<<ID and ignore upper write bits. SELECT uses TEMP,
excludes the initiator bit, and times out on empty/initiator-only masks without
reusing an old target. Original firmware page003B:75FE..7634 writes command bytes
through TEMP and handshakes SET ACK E4 / RESET ACK C4; the native controller now
drops/reasserts REQ accordingly. Programmed-input reads decrease the SPC counter,
and status/message ACKs release the bus.

Observed firmware DMA47 (page003B:7724..778C) now transfers bounded SPC input into
RAM, advances destination and exhausts gate/SPC counters. Oversized and out-of-RAM
fixture requests leave data/counters unchanged. This implementation is synchronous;
other controls, output DMA, zero-count conventions, native IRQ priority and exact
hardware timing remain unqualified. Legacy flat behavior stays separate.

Original IC15/OS2.24 now identifies a private HD0/512-byte-sector target rather
than listing every supplied device as No Drive. Three fresh-machine cases qualify
absence, a zero-filled10MiB image and a truncated1024-byte image. Absent target
shows No Drive; both unsupported images show Unformatted and emit Not Formatted
on selection. Each case returns to a real floppy Load, verifies all119808 sample
bytes, plays/releases to a full silent second, and preserves both source/backing
images with idle/clean media. Firmware-issued512-byte DMA completions are logged
for present targets. Command traces are bounded and drop rows in present cases;
no exhaustive bus/arbitration claim is made. Late absent-case trace has no commands,
so no claim is made that every absent ID is actively reselected by that UI action.

Isolated before/after regressions cover eight initiator IDs, seven present-target
INQUIRY selections, command/PIO and DMA/bounds. Original-firmware native audio/MIDI,
131072 exact cold stereo frames/refreshed displays, legacy transfer/state and363
backend tests pass on the complete fix. Intermediate BDID-only and PIO-only builds
exposed two firmware stalls; both are resolved rather than accepted as regressions.
BUG-066/068/069 are fixed for this bounded contract.

At this discovery checkpoint, genuine formatted SCSI sample Load was unqualified.
The later Akai Convert Load subset is qualified above; native Roland performance
Load and SCSI Save remain separate pending work.
[Exact identities, commands, failures, firmware cases and limits](validation/milestone-5-scsi-discovery-2026-10-14.json).

The owner manual Advanced3-104 (PDF page128) states that System LoadPRM/SavePRM
transfer settings between internal and System Backup memory. This is not a disk
operation and cannot establish concurrent disk/MIDI/voice coverage. Earlier local
screen notes incorrectly described disk storage; BUG-067 corrects those notes.
Advanced5-15 (PDF page153) describes the drive Scan action. The firmware verifier
uses the actual Scan widget and panel action; screenshots identify reviewed OS2.24
labels, not generalized OCR.

## Native persistence checkpoint — 2026-10-11

Firmware Save now completes observed IC4 DMA modes FA (RAM to floppy) and E2
(wave memory to floppy). Original OS bytes at file01DC41 onward program the
wave address at C00C/C00E, count1200 and controlE2; the runtime trace confirms
the subsequent WRITE DATA45. These are bounded synchronous transfers, not proof
of exact controller timing or complete FDC behavior.

The standalone exports actual controller media to a new image after firmware
Save. A fresh-machine reload preserves all13 generated sample payloads used by
the88-key ROBOFULL fixture:119808 bytes, with note60 playback and silent release
verified. High wave-memory records differ across save/reload, so full session
state equivalence is not claimed. Library originals remain unchanged.
See [reproducible evidence](validation/native-media-2026-10-11.json) and
[the player runbook](../emulator/guides/standalone-player.md). Busy or dirty controller media
now rejects replacement/ejection. Export acknowledges only its captured revision
after host publication; subsequent writes remain dirty. Native regression covers
134 writes, rejected changes, export, ejection/reinsertion and fresh reload.
OS 2.24 empty-drive behavior is now qualified: Disk/Load requests insertion,
emulated time advances, empty export fails, and reinsertion loads ROBOFULL.
Standalone Eject waits for controller acknowledgement and preserves busy/dirty
protection. Loaded sample playback/release survives ejection. The supported
same-build standalone session profile restores embedded floppy/sample memory
after source-library removal and firmware-path relocation, with 131072 exact
stereo frames and refreshed CRT/LCD bytes. Browser version/build diagnostics
preserve the live patch on rejection. See
[current media/session evidence](validation/standalone-media-session-2026-10-12.json).
Standalone now also maintains a separate automatic recovery checkpoint every60
host seconds after observed boot, plus a checkpoint on normal desktop close.
Dirty media and sampler RAM are retained independently of manual saves/exports.
Startup/restart hold existing recovery until explicit restore or replacement;
save failure cancels normal close and retains the old archive. Native dirty
revision134 child-failure/close replay reproduces131072 stereo frames/both
displays and exact disk bytes. Production timer/restore/explicit quit and desktop
close pass in the updated package. Recovery ends at the last successful
checkpoint; later edits, forced termination, physical-MIDI/busy/error delays,
broader formatting profiles and firmware SCSI saves remain limitations. See
[automatic recovery evidence](validation/standalone-auto-recovery-2026-10-12.json).
External SCSI backing filenames/content remain prerequisites.

Floppy write protection is now controller state: ST3 WP is reported, protected
WRITE DATA/FORMAT returns ST0 abnormal termination with ST1 not-writable, and
absent-media writes return not-ready. Host protection changes reject busy/empty
controllers; insert/eject resets protection. The bit is serialized in native
checkpoints. OS 2.24 Save visibly reports Write Protected, with an exact unchanged
export and revision zero. Cold process recall preserves protection. Turning it
off permits 134 write revisions, export, fresh reload of all 119808 sample bytes
and native note60 playback/release. The actual packaged browser verifies control
acknowledgement, reconnect, reset and recalled protection. This is a Windows
development/OS 2.24 qualification, not physical FDC timing or a clean-machine
release. See [write-protection evidence](validation/standalone-write-protection-2026-10-12.json).
BUG-041 is now fixed for OS 2.24 standard 720KB native formatting. Firmware at
physical0188E4 supplies 4D with SC09, fill0F and FA RAM DMA count0024 from083E0E.
The driver validates a complete CHRN descriptor set (cylinder/head, unique sector
IDs, size, source/count and media bounds) before filling a track and advancing
DMA. Unsupported transfers return an error without mutation; PIO and nonstandard
sector layouts are unsupported. All160 tracks plus the firmware header write
produce revision161. Protected Format leaves the original bytes unchanged;
dirty formatted bytes/revision recall exactly in a fresh process. The exported
formatted image contains the firmware's S-760 Formatted Disk Ver. 2.24 header
and733184 verified fill bytes beyond the first4096 bytes. Save afterward reaches
revision295, then export/fresh reload preserves all13 sample payloads and audio.
The actual packaged browser verifies Format/export fill and retained sampler
memory before reconnect/restart/recall. HD/foreign media and physical FDC timing
remain unqualified. See [format evidence](validation/standalone-formatting-2026-10-12.json).

## SCSI device write contract

WRITE(6)/WRITE(10) commit a complete payload to private target memory at the
requested LBA. The original library image is unchanged. Incomplete or reset
transfers leave sectors unchanged. CD-ROM writes reject with DATA PROTECT
(7/27); out-of-range reads/writes reject with ILLEGAL REQUEST (5/21). Sense is
per-target and included in checkpoints. Zero count in a ten-byte command
completes immediately; WRITE(6) count zero transfers 256 blocks.

The generated-media device probe verifies readback, neighboring sectors,
protection, range failures, reset interruption, and warm/cold recovery of a
partial nonzero-LBA write. This fixes BUG-015's discarded-payload defect, not
firmware SCSI Save/reload or host-file export qualification. Those workflows
remain open. See [validation](validation/s2-scsi-and-stack-2026-10-11.json).

## Earlier format research

Updated mapping evidence (findings53/54): ROM loader copies file4800..1007FF
to physical0..FBFFF and jumps CPUC000. Banked fetch/data addresses use separate
selector sets. The runtime+2780 relation below applies only to the old flat
preload; it does not describe the real loader handoff or prove banking unnecessary.

Condensed 2026-10-09 from the original overview, disk map, CPU investigation,
manuals guide, emulation specification, findings log, and string/forensics catalogs.
See [source map](source-map.md) for the complete input list. Offsets below are
**disk file offsets** unless explicitly marked runtime.

## Artifact and layout

`S760224.IMG` is 1,474,560 bytes (`0x168000`): 80 cylinders × 2 heads ×
18 sectors × 512 bytes. Sector 0 contains `S770 MR25A`,
`S-760 System Disk    Ver. 2.24`, and the Roland copyright banner. It is a
proprietary Roland system disk, not a FAT boot volume. An embedded x86 DOS
formatting template is data used for interchange; it does not identify the CPU.

| File range | Interpretation | Confidence / limitation |
| --- | --- | --- |
| `0x000000–0x0001FF` | Volume/banner sector | Directly identified |
| `0x000200–0x0047FF` | Solid `0x0F` fill | Allocation/free sentinel interpretation remains provisional |
| `0x004800–~0x085FFF` | Executable payload and data | Not one contiguous runtime address window |
| `~0x086000–0x0AFFFF` | UI/resources mixed with other data | Text and descriptor locations overlap this broad classification |
| `~0x087000–0x089000` | UI/MIDI text and DOS template area | Original region boundaries are approximate |
| `~0x0C3000–0x0DDFFF` | Repeating `0x100`-byte records | Preset/parameter role is inferred |
| `0x0DE000–0x0EFFFF` | Zero fill | Reserved/unused interpretation |
| `0x0F0000–0x0F9FFF` | Sparse tables | Directory/secondary-table role unresolved |
| `0x0FA000–0x0FFFFF` | Zero fill | — |
| `0x100000–0x167FFF` | Solid `0x0F` tail | Apparently unallocated |

For resident runtime addresses `0x2080–0xFFFF`, use **file = runtime + `0x2780`**.
The resident slice is file `0x4800–0x1277F`. Later disk content needs its own
loading/mapping evidence; do not apply the formula to arbitrary resources or
interpret file offsets above 64 KB as resident PCs. No resident code banking is
needed to execute the upper `0xE000–0xFFFF` routines.

## CPU identification and inspection

The service notes and coherent reset disassembly establish Intel **S80C196KB**,
16-bit little-endian MCS-96. Earlier i960, 68000, and x86 interpretations are
superseded. Payload entropy around 6.3–6.8 bits/byte supports structured,
uncompressed code/data, but does not classify every byte as executable.

Use the existing pypcode/Ghidra SLEIGH wrapper:

```powershell
python .agents/scripts/mcs96_disasm.py S760224.IMG --off 0x4800 --len 0x200 --base 0x2080
```

Older notes use the `.kiro/scripts/` mirror. Confirm instruction boundaries,
relative-target math, and callers before treating a raw opcode-pattern match as
code. Low register operands belong to `AS_DATA`; external buffers use
`AS_PROGRAM` in the emulator. This established emulator distinction does not
by itself prove the historical hypothesis about physical low-ROM fetch decoding.

## Hardware patch experiments worth retaining

| Experiment | Recorded result | What it establishes |
| --- | --- | --- |
| M1/M1b version-string edits | Modified disks booted; main display eventually showed `9.99` | Gotek round trip and these patches accepted; not a universal proof that no checksum exists anywhere |
| B0 reset-tail delay | Delay then normal hardware boot | Injected code executed and rejoined initialization |
| B1 repeated calls to `0x218E` | Delay then normal boot | Resident call/return from injected code worked |
| Save System output comparison | 344/360 4 KB blocks identical; 993 bytes differed | SaveSys includes live resident patches and some configuration differences |
| Four 8-byte sentinel markers | Survived SaveSys | Those markers/locations survived that experiment; not proof every larger write is safe |
| Low-memory copy probes | Some froze; later probes saved zero-filled captures | Data-copy approach did not recover firmware; physical code/data split remained an interpretation |

The reset-tail hook was runtime `0x218B` / file `0x490B`; original bytes
`E7 A3 06` jump to `0x2831`. Historical scratch entry `0x5DBE` / file `0x853E`
lies in an approximately 8 KB gap ending at runtime `0x7D00`. Later copy
destination `0x5E00` corresponds to file `0x8580`. These are experiment anchors,
not standing permission to overwrite them: current HLE uses other former gaps,
including the `0x9B42/51/71` delay entries.

Always patch a copy, retain exact size and sector alignment, check original hook
bytes, round-trip assembled code through the decoder, record the diff, and retain
a known-good hardware boot image. Keep this team's scratch in the author's work
folder. Never alter `S760224.IMG` in place.

## Resource catalogs and limits

`os-string-catalog.md` and `06-ui-string-map.txt` preserve exact strings and file
offsets. Useful anchors include Patch Common `0x09446A`, Partial TVF `0x09A1DC`,
TVA `0x09A872`, and LFO `0x09ACA0`. These locate labels/descriptors; they are not
automatically executable function entries or C++ structure offsets.

The short forensics deep dive also lists SCSI tape, foreign-format conversion,
and RC-100-related labels. Its raw `F0 41` byte matches include ASCII strings
such as `Auto Trun/Norm`; they do **not** establish SysEx messages or a complete
protocol. Use the MIDI implementation manual for protocol confirmation.

Manual sources are `ROLAND_S-760_SERVICE_NOTES.pdf` (24 scanned pages),
`S-760_OM.pdf`, and `S-760_MI.pdf` (14 pages). Service-note OCR is retained in
`service-notes-ocr.txt`; schematic wiring and noisy IC labels need visual
confirmation. Visually checked parts list p.5 establishes **IC15 = BOOT EPROM,
IC1 = CPU, IC20 = I/O gate array**; finding 22's CPU designation was incorrect.
Directory/catalog structure, allocation units, full record semantics, and checks
outside the tested boot patches remain open.


### Native HD0 writes (2026-10-14)

Original firmware quick initialization and performance Save now use bounded RAM78/waveA0 output DMA with native SPC counter completion. Writes modify the instance's controller image; source files remain unchanged. Python `NativeRuntime.export_scsi_hd0(new_path)` requests an idle HD0 snapshot through the native media port, validates its byte count and publishes a new output without replacing an existing destination. Busy/missing/read-only targets reject; export failures preserve controller data. The emulator must be running for the input callback. This export is a Python QA operation; the packaged GUI/VST export action has not been qualified for SCSI.

`verify_native_scsi_save.py` qualifies the private10 MiB HD00_512.img / HD0 /512-byte-sector profile: initialize, Save ROBOFULL performance, export and fresh firmware Load without a sample floppy. All13 sample allocations/119808 bytes are exact; playback level/spectrum and release survive. No low-level physical format/timing or arbitrary-media acceptance is claimed. [Validation](validation/milestone-5-scsi-save-2026-10-14.json).


### Supported disk/MIDI/voice contract (2026-10-14)

Owner's manual Advanced1-3 (S-760_OM.pdf page11) explicitly excludes sound output in Disk, Quick Load and Sampling displays and while commands such as Copy execute. Searching for a supported ongoing-voice disk operation was an incorrect roadmap requirement. This resolves the remaining Milestone5 gate through documented restriction/recovery, without claiming three-source arbitration.

Current native ROBOFULL Save clears four active notes, completes under240 incoming scheduled MIDI events (166 observed overlapping FDC writes), remains exactly silent over1543500 frames, and returns to Perform without stuck notes. Fresh Load preserves13 allocations/119808 bytes and matching recovered peak/release; original media/firmware hashes remain unchanged. The positive Save trace drops378 rows and cannot prove exhaustive handling or absence of every event. Three current Load-directory trials have complete traces and zero restricted completion overlap; their Perform control observes12 source2 requests. [Evidence and commands](validation/milestone-5-concurrent-recovery-2026-10-14.json).


### Disk Load versus full-session identity (BUG-006,2026-10-14)

The historical347-byte wave-RAM mismatch reproduces in the32MiB profile at high-memory metadata/name/ID/directory records, while13 sample allocations/119808 bytes remain exact through Save/export/fresh firmware Load. A separate cold checkpoint preserves all33554432 wave-RAM bytes exactly. Disk Load reconstructs records and must not be required to reproduce an entire session. BUG-006 is closed WONTFIX for its erroneous whole-session expectation; no guest metadata was patched. `verify_native_media.py --checkpoint --state-dir <fresh-private-directory>` now records every changed range and asserts full-wave identity specifically for checkpoint recall. [Evidence](validation/remaining-bug-investigation-2026-10-14.json).


### Explicit TVF envelope fields corrected (BUG-073,2026-10-14)

The original firmware TVF screen confirms partial+0x52..0x55 holds the four Level values and+0x56..0x59 the four Time values. The historical local builder labelled/wrote these in reverse for explicit specs. The canonical tracked scripts/build_sample_disk.py corrects explicit JSON levels/rates(time); the local .agents entry point delegates to it. Implicit legacy preset bytes remain unchanged. The controlled TVFSTEP capture disk is737280 bytes, loads64512 sample bytes exactly and produces the measured up/down steps and static endpoints through unmodified firmware. [Capture instructions](../hardware/captures/tvf-transition-capture.md), [native evidence](validation/tvf-transition-capture-2026-10-14.json). Generated images and their proprietary template stay outside source distributions.


### OS transfer supervisor (static, 2026-10-16)

OS 2.24 reserves sample space in units of 0x1200 before searching its 512 descriptor slots. Startup C869/C86D/C872 explicitly maps fetch page 0166 and calls 87B5; recursive analysis reaches higher-level rollback at 8B5F. That helper restores cursor 3616 from saved 1FA0 and refreshes page 0299 allocation mirrors. The supervisor's receive loop resets a 16-bit stall counter when the packet counter changes; cancellation or counter wrap takes an error path through rollback, while success takes a staged 0x30-byte copy path. External callee preservation, descriptor ownership and native cleanup acceptance remain open. These are static original-byte observations, not a measured timeout or physical transfer validation. [Lifecycle analysis](../firmware/os/os-transfer-lifecycle.md) and [byte evidence](validation/os-transfer-lifecycle-2026-10-16.json).


### Original OS startup device identification

[Static device-probe decoding](../firmware/os/os-device-probe-and-numeric-fields.md) followsstartup0129:8000 overeight targets0..7. Commandrecordsunder02CC:5F4E/5F55 are count6 plus03/12 commandbytes withrequested0A/23-byte responses. Counted comparisons identifyvendor/productprefixes,includingJVC/OMTI,CD-ROMfamilies,SonySMO-C,SyQuestandIomega. [Original-byte evidence](validation/os-device-probe-and-numeric-2026-10-16.json) preserves boundedresources;these firmwarebranchesdo notestablishnewphysicaldevicecompatibility.


### SDS traffic during ordinary Disk Load (2026-10-18)

With the experimental local-owner firmware, four Mouse+CRT native processes
cross floppy/HDD Load with ten receive headers or ten remote dump requests.
Every process preserves 13 allocations/119,808 PCM bytes, passes playback and
release, and then receives/publishes another 160 exact PCM bytes. Both HDD
exports match the saved input image. The schedules span the first nine seconds;
153/152 FDC and 98/98 SCSI command writes overlap their serial-delivery windows.
No SDS state/saved-cursor writes or MIDI replies occur during the measured Load
intervals. Serial delivery does not establish parser handling or a busy reply.
Save, all payload-phase boundaries, entry while SDS already owns the foreground,
and hardware/controller variants remain unqualified. Manufacturer41 session
0166:8B91 (including its 8C65 call to 87B5) is a distinct path, not ordinary
Disk Load/Save. No firmware/runtime changes were made for this qualification.
[Evidence with source/build identities and raw rows](validation/bluescsi-disk-load-2026-10-18.json).


### Floppy Save under SDS traffic and stock reload (2026-10-18)

Two experimental-image processes save a private ROBOFULL copy while receiving
ten SDS headers or ten remote dump requests across 27 seconds. Each clears four
active notes on Disk entry, remains silent for 1,543,500 frames, and recovers
playback/release afterward. Partial traces retain 166 overlapping FDC writes
per case. No SDS state/saved-cursor writes or transmitted replies occur in the
measured Save intervals. Separate stock-OS cold Loads recover all 13 allocations
and 119,808 PCM bytes exactly, with matching playback peak and silent release.
Both experimental processes subsequently receive/publish another 160 exact PCM
bytes. The original media/firmware remain unchanged. This qualifies the named
floppy Save workflow, not HDD Save, every phase boundary, parser acceptance,
an explicit busy reply, active-owner Disk entry or hardware/controller parity.
[Raw evidence, source and binary identities](validation/bluescsi-disk-save-2026-10-18.json).


### HDD overwrite Save under SDS traffic (2026-10-18)

The twenty-first checkpoint adds two HDD overwrite Save cases on copies of the previously native-saved 10 MiB image: ten SDS headers or ten remote dump requests over 27 seconds, followed by separate stock-OS cold Loads. Both exported images change, while independent Roland allocation extraction and cold Load preserve all 13 samples/119,808 PCM bytes. Playback/release match before and after cold Load; each experimental process also receives/publishes another 160 exact PCM bytes after Save. Partial traces show 209/209 SCSI command writes overlapping serial delivery, with no SDS state/saved-cursor writes or MIDI replies during the measured Save interval. Four active notes are cleared on Disk entry and 1,543,500 captured Disk-mode frames remain silent in each case. Originals remain unchanged. The excluded trials failed to activate the HDD-specific Yes button or encountered a host snapshot-file sharing conflict; neither is firmware-defect evidence. Active-owner Disk entry, manufacturer41 sessions, remaining phase boundaries and hardware/controller qualification remain open. [HDD Save evidence](validation/bluescsi-hd-save-2026-10-18.json).


### Disk menu attempts during active SDS ownership (2026-10-18)

The twenty-second checkpoint tests Disk-menu entry during active SDS ownership. Receive (state1) and remote send (state7) retain ownership across both Load/Save menu attempts when ordinary packet progress prevents timeout; no allocation/backup/owner writes occur between the measured active snapshots. Peer cancellation then restores idle and Disk Load entry. Local send behaves differently: separate Load/Save click attempts trigger cancellation and release state8 while remaining on System MIDI; a matched no-click ACK-stream control stays active. These cases qualify cancellation/recovery, not local ownership retention. Five native processes/79 snapshots preserve the two existing descriptors and full allocations, finish with three samples/480 exact received PCM bytes each, and byte-check 47 transmitted packets in total. Disk Load screens after release show the expected system-floppy rejection; no media Load/Save is executed in these menu-entry tests. Exact mouse-cancel dispatch, manufacturer41 sessions, pre-supervisor timing and hardware/controller cases remain open. No firmware/runtime change or confirmed new defect. [Active-owner evidence](validation/bluescsi-active-disk-2026-10-18.json).


### Manufacturer41 session and SDS ownership (2026-10-18)

The twenty-third checkpoint qualifies the separate manufacturer41 Remote Mode (MIDI/SCSI) session using ordinary MIDI requests. Five native cases cover remote-send timeout, peer cancellation, full completion, session exit requested during a stalled send, and receive publication. All return through the session caller at0166:8C68 and exit cleanly where applicable; remote scratch RW1C..6A, bank selectors and WSR match entry, with the expected18-byte wrapper/return stack difference. The two timeouts measure5,000,069 and5,000,056 timer microseconds. An exit request clears1FA4 while state7 remains owned, then the session exits after timeout recovery; it is not an immediate transfer abort. Across76 snapshots,16 received samples/2,560 PCM bytes and118 sent packets match exactly, including a full9,216-byte allocation and wire padding. All ten manufacturer entry/exit notifications match their bytes and checksum. Observed stack use reaches196 bytes relative to the session continuation, and the largest observed clock-service gap is42.780 ms; these are not complete stack/ISR bounds. No firmware/runtime changes or new confirmed defect. External SCSI initiator operations, enumeration/deletion, remaining entry/cancel boundaries and hardware/controller cases remain open. [Session evidence](validation/bluescsi-session-2026-10-18.json).


### Early SDS cancellation rollback repair (2026-10-18)

The twenty-fourth checkpoint fixes BUG-125 in experimental firmware. A receive header immediately followed by CANCEL previously left one reserved block unreachable: idle cursor3 with only two samples, then retry at block3/cursor4. Two of three prior-image controls reproduce it; the session-start burst does not admit the receive and therefore does not test rollback. The new31-byte helper retains receive cancellation as stateFE for active1, completed-but-unpublishedFF and already-cancelledFE, while other owners keep generic0A. FE follows the existing receive rollback path; duplicate CANCEL cannot erase its ownership. Ten native cases cover ordinary/session entry bursts, duplicate cancellation, a one-packet completion/CANCEL boundary, active receive cancellation, remote cancellation/timeout and local cancellation/full completion. All end with three samples/cursor3 and exact480 received PCM bytes each; 118 sent packets match. Including controls, 181 snapshots preserve both seed descriptors and allocations. All113 focused tests and ordinary native playback/MIDI/audio pass. The helper adds no RAM or call frame; total proposed code use becomes2,402 bytes, leaving672 arithmetic bytes (641 contiguous after0ABF). Exact pre-supervisor instruction ordering remains unproved because an exploratory read tap targeted the replaced entry instruction; ownership writes prove the defect and rollback. Complete memory/stack fit, remaining timing and transactional stereo/bounded WAV writing remain open. [Early cancellation evidence](validation/bluescsi-early-cancel-2026-10-18.json).


### Ordinary HDD Load transfer and allocation anchors

A fresh original-OS HDD Load identifies actual native reuse candidates. Thirteen DMA launches at003B:7A1E use control84 with9216-byte gate counts and wave-word destinations8+i*4608 for i=0..12. Their119808 PCM bytes match independent disk extraction exactly, and subsequent playback/silent release pass. The HDD export and original firmware remain unchanged. Three additional8192-byte launches use wave address00FFCC08; their purpose is not established here and they are excluded from the sample-transfer total.

Thirteen actual cursor increments at0119:9110 advance3616 from0 to13. Byte-checked code at0119:90F3 masks descriptor rate+2C to three bits, copies the prior cursor to descriptor+28, adds the global block count1C5C to3616, and derives the address relocation base from the old cursor times1200 plus361A/361C. These stores establish inputs and side effects, not a complete allocator entry point: free-space checks, descriptor search, caller state and rollback still require closure.

The observed DMA tail at003B:79F3..7A5C takes RWBC for0118, saves/restores flags and the115 mask, enables interrupts, writes84 to011D, polls SPC statusE408 and returns carry/RBB status. Its repeated wait path is not a qualified bounded Toolbox operation. The separately decoded003B:7CD0 helper reads the destination globals3644/3646, sets C00E/C00C, clears011A/011C and sets0118 fromRWBC; this run does not establish that helper as the observed caller. All three instruction spans match the original image and decode exactly to their stated boundaries.

Reuse direction: retain native wave-DMA and descriptor relocation mechanisms where a complete calling contract can be proved; do not reimplement Roland disk loading. A direct SCSI-to-wave transfer does not deinterleave stereo WAV, and the observed disk path assumes native block/state preparation. The next investigation is the RAM-to-wave helper and its caller, followed by a bounded private invocation with exact write extents. No callable service has been approved for importer use yet, no firmware bytes changed, and no code-size savings are claimed. Full WAV/stereo sizing and BS1 remain open.

[Evidence](validation/bluescsi-loader-reuse-2026-10-18.json).


### RAM-to-wave helper boundary

Checkpoint29 byte-checks70 instructions across five original-OS spans (213 bytes), clarifying the RAM-to-wave reuse boundary. All ranges are end-exclusive and use page005A; file=4800+(page<<10)+(logical&3FFF).

| Routine | Established static behavior | Importer consequence |
| --- | --- | --- |
| 6A31..6A7C | Destination words come from RW2C/RW2E; source is fixed physical0EC002; count is fixed2400 hex bytes; controlBC; waits for0118=0 | Copies9216 bytes, so cannot directly consume the proposed4096-byte buffer |
| 70DF..7113 | Sets1200 wave words, advances destination globals, doubles count to2400 bytes and calls005A:73C1 throughCE14 | Native block mover prepares state outside the helper; not a general WAV writer |
| 7113..7132 | Doubles RW42 into byte count, writes R48 as DMA control and waits for0118=0 | Paired read-side caller suppliesA7; no deadline in this wait |
| 73C1..73E1 | Saves RWDA/RWB0, sets controlBC and fixed source0ED712, invokes7401, restores saved words; RW58 is overwritten | Destination and count must already be prepared; source is not parameterized |
| 7401..7418 | Reads011D, writes RB0 to011D, loops on0118 until zero, reads011D and returns | Small mechanism but no bounds validation, timeout or cancellation path |

Current emulator code implementsBC as contiguous CPU-RAM-to-wave copy andA7 as its inverse, preserving byte order. It accepts positive even lengths within both modeled memories, advances both addresses and clears the count synchronously. This is a driver implementation fact, not a physical timing guarantee; rejected bounds leave the count pending and therefore cannot make the native wait safe. No new guest execution is claimed by this static checkpoint.

Reuse decision: use the established DMA mechanism through a bounded importer adapter, not unchanged fixed-source/block wrappers. The adapter must validate a positive even count no larger than4096, source ownership, destination within the reserved channel, exclusive DMA ownership, caller state restoration, and failure cleanup. Timeout alone does not prove a physical DMA has stopped; abort/quiescence must be qualified before freeing its reservation. Stereo data needs deinterleaving before contiguous per-channel DMA. Do not borrow0EC002 or0ED712 without separate lifetime proof, and do not count their native allocations as free importer memory. Next is a private guest adapter and exact source/destination sentinel tests, including final partial chunks, failure and cancellation. Full code fit, native adapter ABI, physical DMA behavior and atomic stereo publication remain open.

[Evidence](validation/bluescsi-ram-wave-reuse-2026-10-18.json).


### Bounded RAM-to-wave diagnostic

Checkpoint30 runs a private guest RAM-to-wave adapter through the ordinary Save System callback after HDD Load. Three successful copies of2,4094 and4096 bytes match exactly. Six cases reject zero, odd and oversized lengths, source overrun, destination overrun and cancellation before launch. Each case checks its complete8192-byte destination/sentinel region:73728 exact bytes total. The DMA log matches18 initialization writes plus exactly three accepted payload writes; rejected cases perform no payload DMA. All119808 existing HDD sample bytes remain exact, the disk export is unchanged, and playback/release before the diagnostic passes.

The adapter occupies145 bytes for validation and80 for setup/polling, inside a1305-byte diagnostic harness. It uses the4096-byte RAM workspace at physical004940, explicit byte counts and word destinations in a fixed high-word1 test arena. Count polling is capped at256 iterations. These are prototype sizes, not a production32-bit API or combined browser fit. Interrupts remain masked during this diagnostic; no realtime responsiveness is claimed. Timeout return does not prove DMA abort/quiescence, and this run exercises neither stalled DMA nor cancellation after launch. Allocation ownership and atomic stereo publication remain open.

BUG-126 affected the first diagnostic image: results at005900 overlapped the source tail and were overwritten by later pattern fills. The observed first result64028 fails acceptance. V2 places results at005A00 and the marker at005AF0; all nine cases then pass. This fixes a private harness layout error, not original firmware. The accepted image SHA256 is89bccdd29734d10dd1e3fa80c0144e848c7bc21f9cdb880f06f5b1043843c0ac. Original firmware is unchanged. Next: generalize channel-address bounds, perform deinterleaving with distinct L/R fixtures, and qualify ownership/abort before integrating this adapter. BS1 remains OPEN. [Evidence](validation/bluescsi-wave-adapter-2026-10-18.json).


## BlueSCSI IM1 library preflight — 2026-10-19

The read-only scripts/bluescsi_image_preflight.py enforces the first32-byte ASCII image-leaf policy: homogeneous ISO/IMG collections, distinct visible names, at most100 total entries, no nested/link entries and nonempty sector-aligned images. It also rejects numeric first-underscore block-size overrides. Eighteen tests and810 pinned-upstream host assertions verify400 displayed-name/index mount matches across IDs1/2/3/6, with fixture hashes unchanged. This avoids reviewed enumeration hazards within the supported policy; it is not firmware enforcement, image-format validation or physical acceptance. Firmware allocation remains4982/8002. [Validation](validation/bluescsi-im1-preflight-2026-10-19.json). Finding281.


### BlueSCSI native Delete — 2026-10-20

Unchanged19448d85... passes native GB6 Disk options Delete/private HD0 selected performance with related hierarchy. Preconfirmation export equals source; confirmed export counters0x116/118/11A/11C change1/22/88/13→0/0/0/0 and independent sample reader finds0 allocations. Fresh-process native Load scan shows empty performance list; Perform allocation count0. Source/golden media and captured browser/SDS code preserved. Named10MiB512-sector hierarchy-deletion scope only, not secure erase, arbitrary types, interruption/concurrency or hardware acceptance.6487/8002,1515 free. RC100 remains assumed under user waiver; other IM1 gates open. [Validation](validation/bluescsi-im1-native-delete-2026-10-20.json).


### BlueSCSI native Optimize no-change roundtrip — 2026-10-20

Unchanged19448d85... passes scoped native Optimize warning/Yes/return on private already-packed10MiB512-sector HD0, byte-identical export, fresh Load13 allocations/119808 exact bytes and playback/release. All captured browser/SDS code and original media remain intact. No fragmented relocation/free-space recovery/interruption/physical claim. High-volume observer timeout is excluded; accepted run removes broad read-only register logging without changing firmware/emulator.6487/8002,1515 free. Other IM1 gates remain open; RC100 remains assumed under user waiver. [Validation](validation/bluescsi-im1-optimize-roundtrip-2026-10-20.json).


### BlueSCSI native Copy — 2026-10-20

Unchanged19448d85... passes private10MiB512-sector HD2→HD0 selected performance/hierarchy Copy: counts0/0/0/0→1/22/88/13; exported samples119808 exact bytes; fresh native Load13 allocations and playback/release. Separate same-name overwrite Cancel leaves destination export byte-identical. Source backing/golden inputs and all observed browser/SDS code preserved. No physical write-protection/arbitrary geometry/type/interruption/concurrency or overwrite Yes/No claim.6487/8002,1515 free. RC100 remains user-waived; other IM1 gates open. [Validation](validation/bluescsi-im1-native-copy-2026-10-20.json).


## IM1 multi-gate batch and nested-mode defect — 2026-10-20

Unchanged19448d85... candidate passes browser-mounted native Akai Convert Load with30 samples/13,568,196 exact converted PCM bytes,15 distinct L/R pairs and stereo playback/release; same-process checkpoint stale-load refusal and explicit119808-byte image reselection; and current Mouse+CRT D7/D8 cancellation/Load/SDS160-byte retry. A26-cycle/13-screen GB-6 matrix preserves screen IDs, browser/SDS code and loaded PCM with final playback, but full parent acceptance is OPEN: matched original/current Mouse evidence proves BUG-165. Native System mode ancestor8120 survives original depth3→4→3; browser Exit collapses it to depth2/page0121 and highlights Perform. Native Mode selection is a workaround. Private Volume Dump FD initialization/export reaches an empty4-slot directory; populated save/reload remains unqualified. No firmware growth:6487/8002,1515 free/1297 contiguous. Stack/resource lifetime, general concurrency, broader media/reset/cold recall and physical qualification remain open; RC100 stays assumed under the user waiver. [Results](../project/bluescsi-im1-multi-gates-results-2026-10-20.md), [validation](validation/bluescsi-im1-multi-gates-2026-10-20.json).


## IM1 full-CD and checkpoint qualification (2026-10-20)

Combined OS6297274d... retains GB-6 v9 and SDS repairs. Fixing the opt-in emulator fixture's64MiB ceiling (BUG-166) permits a full606709760-byte JMD CD browser mount; native Load reproduces79 allocations/6054912 exact bytes, with four notes on two MIDI channels and silent release. The1GiB fixture ceiling is a host-memory policy, not a BlueSCSI or sampler limit. Synthetic first/last-sector/capacity and invalid-geometry/oversize controls pass;769 backend tests and fixture-disabled native acceptance pass on emulator5720c78b... . Cold checkpoint stale Load allocates nothing, explicit B reselection restores119808 exact bytes. Three active-D7 recalls drain without automaticD8, then explicit index99/B loads exactly. Host catalog is unchanged; D8 replay, external mutation and physical reset remain unqualified. Current LCD IMG/error, D7/D8 cancellation and MIDI/SDS/Remote Mode race regressions pass. [Results](../project/bluescsi-im1-closeout-results-2026-10-20.md), [validation](validation/bluescsi-im1-closeout-2026-10-20.json).

The user's writable-media policy supersedes the earlier all-library-read-only fixture: FDD and SCSI IMG remain writable; optical ISO remains read-only. BUG-167 corrects only the opt-in image-switch model. Completed writable HD2 IMG writes persist to the selected file; incomplete DATA OUT does not commit. Protected/optical media reject writes; missing/resized backing returns WRITE ERROR03/0C and invalidates cached media. Native Save, verified index0/1 reselection, fresh-process Load and playback preserve119808 exact sample bytes. Ten synthetic controls and773 backend tests pass on7c994e86... . Ordinary media still use explicit export; checkpoint recall does not undo completed fixture-file writes. No physical durability, competing-writer or crash-atomicity claim.

Current6297274d... also passes Copy overwrite No (byte-identical destination) and Yes (exact distinct source PCM), each with cold Load/playback. Both native Optimize options on scattered clusters reorder240 directory bytes and preserve all name/PCM associations; fresh Load/playback is exact. Optimize offers alphabetical sorting and time-indication correction, not sample compaction. Current Akai Convert Load matches30 samples/15 L/R pairs/13568196 bytes and playback. The first populated Volume Dump FD fixture saved/listed its slot but failed source-media restoration; the matching native-saved whole-Volume source now closes that gap as described below. [Latest results](../project/bluescsi-im1-final-gates-results-2026-10-20.md), [validation](validation/bluescsi-im1-final-gates-2026-10-20.json).


### Current IM1 Volume Dump, Roland stereo and mounted Delete (2026-10-20)

On unchanged OS6297274d.../emulator7c994e86..., native whole-Volume Save to10MiB HD2 creates counts1/1/22/88/13 at0x114. Native Volume reload then720KB Volume Dump Save and a new-process F3 Load/Continue with that matching HDD restore13 clusters/119808 exact bytes and playback/release. This supersedes the earlier incomplete source-fixture restore, not a claim that Volume Dump contains standalone sample data.

A native-recorded44.1kHz distinct L/R pair passes FDD Load, browser-mounted32MiB512-sector IMG Initialize/Save, independent disk PCM verification and fresh browser Sample Load:26 clusters/239616 exact bytes. Native stereo audition/release and browser Exit pass. Current mounted10MiB IMG Delete preserves the file before confirmation, then removes the selected performance/related hierarchy: counts1/22/88/13 to0/0/0/0; independent sample reader and fresh native directory are empty. Original fixtures remain unchanged. These are named native profiles, not arbitrary geometry or physical write guarantees. [Results](../project/bluescsi-im1-safety-batch-results-2026-10-20.md), [validation](validation/bluescsi-im1-safety-batch-2026-10-20.json).


### IM1 timing and partial-command recovery

Native input-exclusion checks on established OS6297274d... now cover Load (Disk-header click plus Mode), quick Initialize, Copy and Delete (Mode). Attempts overlap actual reads/writes and issue no Toolbox command; exact PCM, source preservation or valid empty hierarchy is independently checked. FDC, conversion and full-surface Format remain separate.

BUG170 is fixed in emulator4cf1cfab...: a recalled active COMMAND phase on an opt-in image target cannot complete a stale image selection against the current host catalog. It returns CHECK CONDITION/UNIT ATTENTION06/28; a new selection starts a new command. Before the fix, first-D8-byte recall loaded replacement A instead of selected B. Twelve SPC cases at0/1/5/9 bytes on optical/IMG/ordinary targets pass, plus three native recalls including catalog replacement, then explicit119808-byte exact Load/playback. Other phases/reset-during-write and physical behavior remain unqualified.959 backend tests and fixture-disabled native acceptance pass; all33554432 wave bytes match the prior executable. [Results](../project/bluescsi-im1-timing-recovery-results-2026-10-20.md), [validation](validation/bluescsi-im1-timing-recovery-2026-10-20.json).


### Native Format, conversion and FDD conflict coverage (2026-10-20)

The opt-in BlueSCSI image fixture accepts the observed native FORMAT UNIT CDB
04 00 00 00 00 00 as non-erasing success on writable IMG (BUG171 fixed), matching
pinned upstream disk.cpp commit5e64e3b4a09088c67a2a6728385600ea67ddbe0d. Nonzero
parameter fields are outside this implementation; ISO/protected media reject
the operation. Ordinary targets retain their previous behavior. The S-760 writes
its initialization structures separately. Native full Format option with Verify
No and Yes completes on private32MiB IMG; this is not surface erasure.

Read-only command census shows Verify Medium reads65535 single-sector READ(10)s,
descending LBA65534..0, before initialization. Last valid LBA65535 is not read.
BUG173 records this observed gap; original-OS comparison and cause remain open.
Do not claim complete surface verification from native Format success.

On timing candidate367f067d..., input overlapping native Akai Convert Load,
FDD Load/Save/Format and both IMG Format cases produces no Toolbox commands.
Conversion preserves13568196 exact bytes/30 samples; stereo FDD Save/export and
fresh-process Load preserve239616 exact bytes/26 clusters and L/R playback with
release. FDD Format performs160 track formats plus header revision161;733184
bytes after offset4096 have fill0F. These are named conflict cases, not universal
alias/DMA ownership proof. Native-write reset probes failed to isolate mid-DMA
because transfer execution is synchronous; they are excluded and the gate stays
open. All user media inputs remain unchanged.
[Evidence](validation/bluescsi-im1-format-fdc-stack-2026-10-20.json).


## IM1 Verify Medium and stalled-target qualification (2026-10-20)

BUG-173 is fixed by reordering the inherited48-byte loop at0129:B717/file052317: READ CAPACITY supplies an inclusive last LBA, so decrement now follows the zero/end check. Original bytes match OS2.24. Native complete65,536/65,537-sector censuses pass on established0be06d4d... and trial5581ee53..., with zero growth and GB-6 v9/SDS retained. Nine accepted native cases and93 memory snapshots pass. Immediate dispatcher frames are12 bytes; a conditional sentinel scan bound is32 comparisons per scan/528 total, not a complete native time/stack proof.

The default-disabled one-shot D7 REQ-withheld fixture passes first/last-byte recovery and explicit retry. The actual simultaneous-MIDI case fails:323 reads overlap the stall,585 of775 expected reads appear overall; release occurs after113.279125ms. BUG-168 remains open for this byte deficit, native hardware-poll bounds and total deadlines. Full suite:1,088 pass,3 skip,1 minimal authored-OS ROM-loader failure reproduced on the prior executable (BUG-174);44 focused tests pass. All32MiB wave bytes match with the fixture disabled. Physical parity, total stack/IRQ/ownership and other write-reset phases remain unqualified. See [results](../project/bluescsi-im1-verify-stall-bounds-results-2026-10-20.md) and [validation](validation/bluescsi-im1-verify-stall-bounds-2026-10-20.json).


## IM1 repaired redraw and authored-image loading (2026-10-20)

Candidate5e5ec016... adds3 bytes to call the existing caller-qualified service between880 CRT character clears. Both actual simultaneous D7 stall/MIDI cases (byte1/3999) preserve775 reads,239616 stereo bytes and playback/release. Original dense D7, CRT/LCD cancellation/names, SDS and Remote Mode regressions pass:10 native cases/104 snapshots. BUG175 is fixed independently of BUG168, whose full service/deadline proof remains open. Allocation6583/8002 leaves1419 free; synchronous stack166 bytes unchanged, no total IRQ/ancestry proof. GB-6 v9/boot/SDS/Verify Medium/warnings retained. BUG174 fixes the minimal authored header and tests first real ROM handoff with112 tracks/all1032192 loaded bytes; no runnable-example-OS claim. Full suite1089 pass/3 skip, no failures. Physical qualification and upstream BlueSCSI defects remain separate. BUG140's abandoned descriptor experiment is WONTFIX, not repaired. [Evidence](validation/bluescsi-im1-bug-fixes-2026-10-20.json).


## BlueSCSI filename source repair (2026-10-20)

Local patches fix BUG145/146 in reviewed BlueSCSI-v2 revisions5e64e3b4... and4d0f96fe.... Count/list/selection validate the same pre-display-truncation name;32-byte wire labels and100-entry cap stay unchanged. Explicit switch paths must fit63 bytes plus NUL; longer inputs are refused before old-medium/audio side effects. D8 rejects overlong constructed paths/invalid indices and propagates switch failure with CHECK CONDITION. Real backing-open failure retains upstream close-before-open behavior; no rollback claim. Both full-source patch applications and21 focused tests/10,002 host assertions pass; backend suite1110pass/3skip. This is a local source repair, not an RP2040/RP2350 cross-build, installed firmware or physical acceptance. Existing32-byte preflight profile, S-760/GB-6 v9 binaries, BUG168 and broader IM1 gates are unchanged. [Results](../project/bluescsi-filename-fixes-results-2026-10-20.md), [validation](validation/bluescsi-filename-fixes-2026-10-20.json).


## BlueSCSI failed-switch source contract (2026-10-20)

BUG137 is fixed in the same local BlueSCSI source patches as145/146; published patch bytes are unchanged. Dedicated short-name invalid-index, missing-directory and backing-open reproducers show original false GOOD status. Patched D8 returns CHECK CONDITION, STATUS phase, zero data and sense5/24/00. Host execution checks36 errors/36 explicit retries across four target IDs and three getName conventions (552 assertions); exact image contents and subsequent tray-close unit attention pass.33 focused tests and1122 backend passes/3skips. Invalid requests preserve old media; actual backing-open failure still closes the old backing before error, without rollback. Source-defect closure is distinct from installed-board build/flash and physical/native recovery qualification. BUG168 and full IM1 safety remain open. [Results](../project/bluescsi-switch-error-fix-results-2026-10-20.md), [validation](validation/bluescsi-switch-error-fix-2026-10-20.json).
