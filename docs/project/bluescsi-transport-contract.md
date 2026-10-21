# BlueSCSI transport: timeout and recovery design

**2026-10-18 — BS1 research; a limited guest diagnostic is implemented, full client contract remains open.**

The client needs its own bounded phase handling. An outer deadline cannot make an existing non-returning SCSI helper safe. Private OS diagnostics demonstrate exact CDB transmission, short/status-only and full-buffer transfers, sense, timeout/poll limits and caller restoration in native emulation. Follow-ups add idle interrupt service points and ordinary Exit cancellation through bounded command completion. Physical BlueSCSI timing, wider input/ISR bounds and independent target-fault recovery remain unqualified.

[Feasibility report](bluescsi-feasibility.md) · [Roadmap](bluescsi-files-roadmap.md) · [Validation and reproduction sources](../condensed/validation/bluescsi-memory-transport-2026-10-18.json)

## Qualified guest diagnostic subset

Ordinary Disk → Save System reaches an eight-byte private-image hook at fetch `0181:9040`; actual CRT screen index is `0112`, descriptor data `023F:B22A`. The fixed-low page `000F` diagnostic occupies 942 bytes, of which transaction/helpers use 576. It saves/restores the caller, replays the two displaced instructions and returns to the original callback. Its final 14 cases exercise exact six-/ten-byte commands, three-byte short INQUIRY, zero-data completion, READ failure/sense, absent target, capacity refusal, two held-ACK guards and subsequent successful commands. The final unsupported-command case returns CHECK CONDITION and `05/20/00` sense after BUG-113's native-model correction. [Raw traces, builders and analysis](../condensed/validation/bluescsi-guest-transport-2026-10-18.json).

The manual TEMP/ACK path checks TIMER1 and a poll budget at each handshake wait. Experimental constants are 20,000 ticks total, 5,000 ticks without progress, and 65,535 polls (eight for the poll-limit fixture). A high elapsed-word check expires the attempt before 32-bit overflow. Cleanup has a separate finite 64-iteration limit; it releases ACK and the bus and clears count/PCTL/INTS. All observed exits reach model PSNS zero. These are test constants and model outcomes, not release deadlines or physical recovery bounds.

The held-ACK timeout exits at 5,010–5,011 ticks, including a replay crossing TIMER1 wrap inside that wait. The eight-poll case exits at 165 ticks. Maximum observed timer-sampling gap is below 201 microseconds. All 114 observed general-register words, native target bytes and unrelated selectors are unchanged; the original data bank and saved PSW/window/mask frame are restored. Stack growth is 84 bytes inside the helper, 86 with the hook call. Ordinary HDD Load/playback after the probe preserves 119,808 exact sample bytes and releases to silence.

The final sequence masks interrupts for 20.32825 ms. It has no cancellation, DATA OUT, 4 KiB transfer, independently faulted target, controller/bus reset or Toolbox implementation. The initiator itself holds ACK to create non-progress; the model releases immediately on cleanup. The sensitive READ CAPACITY includes nonzero reserved fields accepted by the model, so it establishes transmitted bytes only. These limitations prevent treating this diagnostic as a production transport or closing BS1.2.

## Full-buffer and deliberate-error matrix

A second private-image diagnostic uses the same ordinary callback and unchanged
BUG-113 emulator build. It adds a guarded 4,096-byte shared buffer, DATA OUT and
a 16-case sequence. The old 20,000-tick prototype times out after only 258 read
bytes and rejects DATA OUT as an unexpected phase; that red result is retained.
The extended experiment uses a finite 1,048,576-tick total budget, the same
5,000-tick inactivity bound and 65,535-poll limit. These are diagnostic values,
not release timing choices. [Validation and reproduction](../condensed/validation/bluescsi-transfer-errors-2026-10-18.json).

**Transport completion and command success are separate results.** A transport
outcome of zero means the status/message handshake completed. If the original
status is `02`, the command failed even when a later REQUEST SENSE returns GOOD.
The following matrix records both responses independently; all sense ASCQs are
zero in these fixtures.

| Deliberate request | Original status / transferred bytes | Separate sense key / ASC | Media result |
| --- | --- | --- | --- |
| Unsupported `3F A5 5A 12 34 56 78 9A BC DE` on HD2 | CHECK CONDITION / 0 | `05/20` — invalid operation code | Unchanged |
| Unmodeled load/eject START fields `1B 00 00 00 03 00` on HD2 | CHECK CONDITION / 0 | `05/24` — invalid CDB field | Unchanged |
| WRITE(10) to LBA `FFFFFFFF`, eight blocks on HD2 | CHECK CONDITION / 0 | `05/21` — LBA out of range | Unchanged |
| WRITE(10), two 2,048-byte blocks on CD1 | CHECK CONDITION / 0 | `07/27` — write protected | No DATA OUT bytes sent; subsequent 4 KiB read matches source |
| Eight-block WRITE with only 4,095 bytes of guest capacity | Transport capacity failure / 4,095 | Status/message not received (`FF` sentinel), no invented sense | Entire 16 KiB scratch image unchanged from before this command |
| Eight-block WRITE with 4,096 bytes available | GOOD / 4,096 | Not needed | Exactly bytes 4,096–8,191 changed; subsequent readback matches |

The sequence also verifies ordinary 4 KiB reads, sense clearing and successful
TUR after the errors. Read-only observers capture the entire scratch image after
every case; all bytes outside the single completed WRITE remain unchanged.
Both buffer guards survive, and unread buffer tails retain the expected pattern.
The incomplete-WRITE result reflects this emulator's staging/commit behavior.
A physical device may write earlier blocks before failure; future recovery and
import rollback must not assume physical command-level atomicity.

Four full DATA IN transfers, a full DATA OUT and the incomplete DATA OUT cross
28 TIMER1 wraps in total. Elapsed accumulation agrees with emulated time within
one tick for every case. Full commands take about 295–297 ms. Maximum timer
sampling gap is 7,030.5 microseconds, including bounded buffer preparation
between commands, below one timer wrap. All 114 observed general-register words,
native target state and caller bank mappings are restored; stack growth is 82
bytes inside the helper, 84 including the hook. Ordinary HDD Load afterward
retains 119,808 exact PCM bytes, auditions successfully and releases to silence.

**Constraint exposed by this checkpoint:** the complete diagnostic keeps interrupts
masked for 1.897658 seconds. Raising its total budget makes the full-buffer
experiment possible but does not make it a usable production client. Audit
interrupt handlers, shared bank/controller ownership and bounded service points
before enabling interrupts; do not assume an `EI` inside the transfer is safe.
Cancellation, independent target faults and controller/bus reset remain open.

## Interrupt cooperation follow-up

The next private image preserves the transfer implementation and adds explicit
service points during buffer preparation and every 64 budget polls. Its 1,333
bytes occupy fixed-low `000F:013E..0672`, physical `003D3E..004272`. The final
20-case table/results occupy 480/640 bytes; the guarded 4 KiB buffer is unchanged.
The ordinary Save System callback and original firmware inputs are preserved.
[Validation, complete byte manifest and sources](../condensed/validation/bluescsi-interrupt-cooperation-2026-10-18.json).

The timer ISR at `0000:CAD1` uses `RW5C/RW5E` and other scratch registers; its
control service changes fetch/data banks. `PUSHA` saves PSW/window/MASK1 and
clears interrupt masks, so inserting `EI` alone is insufficient. The experiment
saves its 35 working register words, restores the native `010A` data bank,
restores the caller's interrupt masks from its own saved frame, and permits
interrupts only if the original I bit was set. After eight NOPs it masks again,
returns `010A` to the workspace page, and restores its working registers. ISR
owned counters, MIDI ring pointers and parser state advance normally; restoring
all general registers to entry values would incorrectly erase that progress.

While it owns the manual PIO transaction, the helper clears IC4 mask `0115`
bit 4 and restores the caller's full byte on exit. The original timer handler
ORs `44` into that mask, leaving bit 4 clear. No interrupt handler writes SPC
registers in the captured run. This is a native-model ownership result: the
current native driver routes SCSI DMA completion through this source but does
not assert the CPU line for raw SPC command/status IRQ transitions. Physical
source routing, acknowledgement and handshake delays still require validation.

The final run passes all 20 cases, with **1,800 service points, 169 timer
interrupts, 123 normal timer-0 rearms and six MIDI bytes** received by the
original `CD1F` handler and consumed from its ring. All service points preserve
transport scratch, banks, window and stack balance. The complete sequence lasts
2.550933 seconds; it no longer masks interrupts continuously. The largest gap
between service entries is 4.906125 ms; the largest whole service call is
3.163250 ms. Bracketing each masked span with adjacent service entry/return
observations gives a conservative **5.018625 ms observed upper bound**, including
extra enabled time. This is not a worst-case or physical latency guarantee.

The guest's maximum TIMER1 sample gap is 17.291125 ms, including buffer
preparation between commands, below one 65.536 ms wrap. The six long commands
cross 33 wraps and every elapsed record matches emulated time within one tick.
The held-ACK case services an interrupt and exits at 5,016 ticks; the eight-poll
case exits at 178 ticks, absence at 23 ticks, and a following TUR succeeds.
Status/sense, all payloads, buffer guards and complete scratch-media comparisons
remain correct. Native HD0 Load/playback afterward retains 119,808 exact PCM
bytes, silent release and an unchanged exported HDD image.

Every stack-pointer write was observed in the final run (180 bytes including
the hook) and a preceding 16-case run (184 bytes). The first 16-case run sampled
a still deeper 186-byte path. These are workload-dependent observations, not
a maximum stack reservation. Three fresh processes pass the transfer/HDD
workflow; the first two exercise 16 cases, the final one 20. The caller entered
with interrupts enabled; the disabled-entry branch has static byte checks only.
The Save System screen is muted, so this does not establish concurrent audio,
dense MIDI, UI event dispatch, cancellation or bounds on every reachable ISR.

## Ordinary Exit cancellation

The next private helper latches Exit while polling the ordinary panel input.
It finishes the current bounded command, then stops scheduling further commands.
It does not treat cancellation as permission to return immediately with a live
SCSI transaction. Deadline and poll guards remain active during the drain. A
transport failure takes precedence over the normal cancelled outcome, and the
original SCSI status/message remain separate. The intended importer must discard
cancelled or failed payloads and withhold sample publication; that importer and
its allocation rollback are not implemented by this probe.
[Validation, negative control and reproduction](../condensed/validation/bluescsi-cancellation-2026-10-18.json).

Original `003B:4320..4366` restarts the panel scan through `F00A` and reads four
rows. The byte-checked access pattern and current native driver identify row 1
bit 1 as active-low Exit. The helper performs four reads while masked, without
calling the native event dispatcher or writing its queue/button-history fields.
It checks only during an active operation, records the first press in its own
workspace, and clears that latch at the next invocation. Physical scan timing,
other controller modes and complete browser input handling remain unqualified.

| Native experiment | Observed result |
| --- | --- |
| Earlier helper, Exit pressed during READ | Expected negative control: no cancellation; all 20 commands continue |
| Exit pressed/released during READ | Latches at 629 completed bytes; drains all 4,096 bytes with GOOD/status-message completion; returns cancelled after 308.312 ms; no following command |
| Exit held through WRITE return | Latches at 629 bytes; completes exactly the intended 4 KiB scratch write; returns cancelled after 309.462 ms; later probe commands suppressed |
| Panel Up during READ | No cancellation; all 20 transfer/error/timeout cases pass |
| Initiator deliberately holds ACK after Exit | Cancellation remains latched, but timeout outcome `3` takes precedence; returns 5.050 ms after the latch, with no fabricated status/message |
| Ordinary re-entry after cancellation | Latch resets and all 20 cases pass without another cancel input |

The stall is deliberately created by guest diagnostic code after a real Exit
press; it is not an independently stalled target. It leaves 608 fully completed
byte handshakes plus one in-flight byte already in the read buffer. The reported
completed-byte count is therefore not permission to publish that partial buffer.
Cleanup reaches model bus-free state and normal HDD operations resume; physical
reset/ABORT and a target that keeps BSY asserted remain unqualified.

Five fresh processes execute six invocations / 45 cases. Exact CDB/DATA OUT
bytes, whole buffers and scratch images, guard words, caller scratch/banks and
IC4 mask restoration pass. Every process subsequently loads 13 native HD0
samples / 119,808 exact PCM bytes, plays at the established level, releases to
silence and exports an unchanged HDD image. Re-entry changes only the expected
diagnostic state; post-operation RAM remains stable through HDD Load/playback.
The existing emulator build and original firmware files are unchanged.

The normal helper is 1,571 bytes at `000F:013E..0760`, physical
`003D3E..004360`; the stall variant is 1,596 bytes through `0779`. Context grows
to 26 bytes at data `5FF0..6009`; table/results and guarded 4 KiB buffer remain
separate. Observed stack use is 180 bytes with the hook, 182 for the stalled
path. The earlier 186-byte observation still applies; none is a worst-case
reservation. Maximum guest timer gap across these runs is 17.494250 ms, below
one wrap for this workload.

**Cancellation does not roll back completed commands.** A WRITE may finish;
similarly, a future Toolbox directory-selection DATA OUT may change the device's
directory before cancellation returns. Browser directory/open-file caches must
be invalidated or reconciled before further use. The production UI should expose
pending cancellation while the current bounded command finishes. Cancellation
before selection, simultaneous target CHECK CONDITION/cancel and importer
publication/rollback still require acceptance evidence.

## Established timer facts

TIMER1 is a 16-bit free-running counter, read at SFR `0A` in window 0; its write mapping is window 15. Intel specifies one increment per eight state times, each state taking two oscillator periods. At the S-760's 16 MHz clock this gives a nominal 1 microsecond tick and a 65.536 millisecond wrap. Writing TIMER1 can disrupt scheduled HSO events. IOS1 reads clear status and must not be used as a harmless clock read. [Intel 80C196KB User's Guide, sections 1.3, 7.1 and 7.4](https://www.syndex.org/kernels/196/27065103.pdf).

The identified native CPU source implements the same divider: `current_time / (8 * cycles_scaling)`, with KB `cycles_scaling = 2`. The stock timer handler reads TIMER1 at `0000:CB00` and `CB40`; its normal scheduling uses the earlier reading plus `4E20` ticks. The extension must preserve the window selector and existing timer setup. It must not depend on a software counter advanced only by an interrupt handler while it masks interrupts.

The third-checkpoint executable produced 512 ordinary guest TIMER1 reads at `CAE1/CB00/CB40`. Every value equals machine-time microseconds modulo 65,536; 85 readings occurred with the interrupt-enable bit clear. Separately, 1,024 periodic observations span 260 rollovers. Those callbacks show up to 45 microseconds of phase skew relative to machine time, so they are supporting continuity evidence, not a precision timing measurement. These observations do not bound every interrupt-disabled interval or establish physical hardware timing.

## Proposed deadline rules

Use TIMER1 without resetting it. Preserve the caller's register window and PSW under a short, audited access sequence; restore the prior interrupt state rather than unconditionally enabling interrupts. The service sequence above has scoped native evidence; its disabled-entry branch, wider ISR workloads and physical timing remain to be qualified.

For each bounded poll, accumulate `delta = (now - previous) & FFFF` into a saturating 32-bit total. Maintain a separate inactivity counter and a finite total poll budget. The total deadline and poll budget cover the whole command attempt, including phase changes and retries. Only actual accepted progress may reset inactivity; check expiry before applying that reset. REQUEST SENSE and recovery need explicit bounded budgets, with a finite overall operation limit as well.

This subtraction is valid only when the interval between samples is less than one complete wrap. A long ISR or native callee can make an entire wrap invisible. Therefore all reachable waits and callees need an execution bound; do not put UI drawing, native Disk calls or an unbounded transfer helper inside the handshake. The poll budget terminates the client's own loop even if the timer stops advancing, but cannot rescue a CPU stuck inside another routine. The maximum interval between timer reads and the maximum interrupt-masked duration are gate criteria, not assumptions.

Eight host-side design cases check wrap arithmetic, accumulation across repeated wraps, exact expiry, non-renewal by repeated progress, a stalled clock, saturation, and the known missed-wrap counterexample. These are arithmetic checks, **not transport acceptance tests**. Numerical command/inactivity/recovery deadlines and poll limits remain to be selected and measured against the guest implementation and physical target; no release values are implied by the test constants.

## Native helper boundaries

| Entry | Byte-checked behavior | Consequence |
| --- | --- | --- |
| `003B:7592` | Count-prefixed CDB source uses a fixed operand bank; a drive-class branch modifies byte 1; handshake polls are unbounded | Use an exact-byte sender with locally bounded waits. Calling this unchanged does not satisfy the Toolbox contract. |
| `003B:7647/76BC/7B14` | Existing PIO routes wait for transfer/FIFO conditions | A maximum allocation length must not become an obligation to receive that many bytes after the target changes phase. Short/status-only handling needs qualification. |
| `003B:7D2A` | Native completion includes unbounded waits and native status/sense policy | Do not hide these waits beneath an outer deadline. Return raw status and separate transport outcome. |
| `003B:7E31` | Sense classes 0/1 clear `RBB`; class 6 calls `7EC0`, then clears it | `RBB == 0` alone is not proof that the original Toolbox request completed successfully. Preserve original status and bounded sense details separately. |
| `003B:7EC0` | Calls page `010A:AAFB/AD64`, sets low-data `1BAC = FF` and `02CC:403E = FF` | Native cache/state invalidation is a shared-state change, not a neutral error decoder. |
| `004B:794A` | Clears `RW2E`, initializes the controller, updates native self-ID/configuration/failure bytes `3623/3622/3625` | Normal entry skips its conditional bus-reset branch. It cannot be used as transparent recovery. |
| `004B:7A18` | `CLR RW28; DEC RW28; JNE; RET` | Finite 65,536-iteration delay, not a calibrated wall-time deadline. |

The initializer saves/restores data selector `010C` around page `0299`. It writes SCTL `80`, configures BDID, clears PCTL/transfer counts/TEMP/SCMD, then writes SCTL `92` and `12`. The subsequent SCMD `10` bus-reset branch requires nonzero `RW2E`; entry `794A` has already cleared that register. A safe callable alternate entry and its complete clobber contract have not been established. Its success/failure result also changes `3625`, `RBB` and carry.

The MB89352 distinguishes controller reset in SCTL from bus reset in SCMD. NetBSD's definitions identify these bits and its driver implements a separate bus-reset pulse and settle delay. That driver is useful primary implementation evidence, not a qualified S-760 timing recipe. [Register definitions](https://ftp.netbsd.org/pub/NetBSD/NetBSD-release-10/src/sys/dev/ic/mb89352reg.h), [controller and bus reset implementation](https://ftp.netbsd.org/pub/NetBSD/NetBSD-release-10/src/sys/dev/ic/mb89352.c).

## Proposed transaction and cleanup contract

| Stage | Required behavior before BS1 can pass |
| --- | --- |
| Acquire | Enter only when native Disk owns no active transaction. Save the exact caller banks, window, PSW and registers in a measured frame. Record which native target/configuration fields the client may change. |
| Select / CDB | Bound bus-free and selection waits; transmit exactly the requested ten CDB bytes, with no drive-class rewrite. Avoid implicit retries that renew the total budget. |
| DATA IN / OUT | Check actual phase and remaining buffer capacity. Account for actual bytes transferred. Accept early STATUS only when command semantics allow that short result; reject overruns and unexpected direction. Zero-data responses must reach status without entering a mandatory FIFO-read loop. |
| Status / sense | Capture status and message completion independently from byte count. Preserve original CHECK CONDITION even if REQUEST SENSE succeeds. Unsupported commands, absence, EOF and malformed responses need distinct outcomes. |
| Cancellation | Latch cancellation and stop new commands. Drain the current command under its existing deadlines; preserve failure/status if draining fails and enter bounded cleanup. Do not return with ACK asserted or a live transfer. Reconcile completed directory-selection side effects and publish neither half of a stereo import. |
| Recovery | Bound each attempt and escalation. Prove bus-free/controller-idle or report transport unavailable. Controller reset and SCSI bus reset are separate operations with separately qualified effects. Never restore stale healthy/cache flags after a reset. |
| Return | Restore CPU calling state on every path. After destructive bus recovery, invalidate browser discovery/listing/open-file assumptions and coordinate native drive revalidation before allowing another Disk transaction. A stuck bus must not lead directly into another unbounded native call. |

A manually acknowledged byte path now has scoped native DATA IN/OUT, deliberate-error, interrupt-cooperation and Exit/drain evidence. Physical timing and full cancellation/recovery coverage remain unqualified. Do not infer hardware support merely because the emulator accepts it. The current `scsi_w` model also simplifies controller reset, bus release and bus-reset behavior; it cannot yet certify the recovery contract above.

## Remaining gate evidence

The next transport work is broader ISR/stack/input bounds, independently missing REQ/stuck BSY, unexpected phases, repeated non-progress phase changes and sense failure. Full-size DATA IN/OUT, unsupported commands, absence, zero-data success, short DATA IN, deliberate errors, idle interrupt cooperation and scoped Exit/drain behavior have model evidence; actual Toolbox EOF/discovery semantics remain open. Each new exit needs a finite measured bound, restored caller state and subsequent ordinary HDD/CD transactions. The post-probe HDD results and separate stock-OS CD regression do not cover every exit/target combination. Physical V2 traces must then qualify timing and recovery against the installed firmware build.

Until those results exist, this document closes the timer-source investigation and records recovery constraints; it does not close BS1.2.
