# Transfer allocation and packet lifecycle

Static analysis of OS 2.24, primarily instruction pages 001F and 0166. CPU addresses below require the established fetch mapping; Bxxx fields require the caller's transfer data mapping. This explains local control flow, not a native or physical transfer test.

## Reservation and descriptor publication

The later [native SDS boundary qualification](../../condensed/validation/bluescsi-length-contract-2026-10-18.json)
now exercises a scoped receive/publication/cancellation path through ordinary
System MIDI controls and external messages. For the retained 16-bit OneShot
headers, 18 lengths plus settled cancel/retry preserve 249,760 transmitted
bytes in 54 snapshots. It also identifies write extents outside the reservation
and an unsafe early-retry interval (BUG-118). See the
[length and cleanup contract](../../project/bluescsi-sample-contract.md#sds-length-boundaries-and-cancellation).
This qualifies that subset of the static discussion below; it does not establish
complete cleanup, every caller's ABI, physical timing or stereo transactions.
The [cancellation guard follow-up](#native-cancellation-overlap-and-private-os-guard)
identifies the offending stock writes and supplies an opt-in firmware repair.

6E69 saves allocation cursor 3616 to 1FA0 before validation. At 6F11..6F1E, available sample units are `(3618 - 3616) * 0x1200`. A requirement exceeding this capacity sets state byte 2BBA to 3 and returns carry set. For a positive requirement, 6F31..6F3A rounds it upward to units of 0x1200 by decrementing, dividing and incrementing. Zero/overflow input qualification remains open.

6F41 saves the old cursor in B192; 6F49 commits the increased cursor to 3616. The sample start is `old_cursor * 0x1200 + uint32(361A,361C)`, stored in B194/B196 and current-write fields B19C/B19E. B198/B19A receives start plus the requested count. State becomes 1, and page 0299:8F9E/8FA0 mirrors cursor/capacity.

Only after this reservation does caller 6D10 invoke descriptor search 6FBF. It scans 512 slots, with descriptor stride 0x30, selecting a slot whose word at +2A is zero. Exhaustion sets state 2 and returns carry set. After saving the chosen slot in 1F9E, **6FFF sets RW5C=1F6E**. Subsequent fields, including +28 at7150 and +2A at7161, therefore belong to a temporary 0x30-byte descriptor. They do not mark the selected table slot occupied. This corrects the initial publication interpretation (BUG-078). Final table publication occurs in the successful supervisor path.

Both reservation and slot-search failures reach 6D30, which sends response 7D and returns carry set. There is no cursor rollback in that local failure branch. This alone does not prove a leak: a higher-level owner may restore it.

An exact-load search found rollback at **file offset 0x5EB5F**. A subsequent selector audit establishes a supported mapping: 0000:C869 loads 0166, C86D writes fetch selector 0104, and C872 calls 87B5. Recursive decoding from that root reaches **0166:8B5F**, called by 88E2 and 8A51. It loads 1FA0, compares to 3616, restores 3616 when different, temporarily selects data page 0299, restores its cursor/capacity mirrors, restores the old data selector and returns. This supersedes the initial file-only candidate status; it does not prove that every intervening external callee preserves the mapping.

## Transfer supervisor and timeout

0166:87B5 returns immediately for state zero. It saves context and calls cross-window helpers before choosing 8810 for state 1 or 8998 for other states. These calls' register-preservation contracts remain to be checked, particularly R30 holding the state.

8810 selects transfer data page 02BE and clears word B1A8. Its polling loop observes state 0A as cancellation (error identifier 37) and state zero as success. Otherwise it compares the current packet counter B1A0/B1A2 against saved B1A4/B1A6. Progress copies the new counter and resets B1A8. No progress runs a short delay loop and increments B1A8; a 16-bit wrap exits with error identifier 6. This is a software stall counter, not a measured timeout duration.

The error exit at 88DB calls display/error helper 8A7A, rollback 8B5F, and delay 8A6D. Success instead calls 8ACA, which handles the staged name and copies 0x30 bytes from 1F6E to a destination obtained through page 004B:6A26. Both then restore the saved data selector, update the display through external calls, clear state 2BBA and set parser R72=8.

8998 clears the state and parser mode first, then handles state values through 5. Values 2/3/4/5 select error identifiers 5B/15/5C/5D; its common error path calls rollback at 8A51. Thus slot exhaustion and insufficient capacity have a higher-level restoration path in the declared static context. The rollback helper does not need to clear the selected table slot on the local pre-publication path: descriptor construction is staged at1F6E. External callee effects and native behavior still need qualification before declaring abort cleanup complete.

## Native cancellation overlap and private OS guard

BUG-118 is reproduced through ordinary MIDI input in the native emulator.
`001F:6D92` sets state `2BBA=0A`; `0166:8B6B` restores cursor `3616` from
`1FA0`. During the subsequent UI delay, another header reaches `001F:6E69`,
`6F49` and `6F90`, replacing the saved cursor, reservation and active state.
The old supervisor then writes zero at `0166:8905`, erasing that new active
state. The retained stock run ends with cursor 2 and all 24,576 public sample
table bytes unchanged. These are original instructions executing in the native
model; physical timing remains unmeasured.

[patch_sds_cancel_guard.py](../../../scripts/patch_sds_cancel_guard.py) builds
an opt-in private OS copy. It repacks the existing dispatcher span
`001F:6CDD..6D0F` (file `00F0DD..00F10F`) and checks `2BBA` before entering
header decoder `6E05`. A nonzero state branches to the existing `6D30` CANCEL
response and carry-set return, without decoding the header or reserving memory.
All seven original command destinations remain intact. The command-table
sentinel test uses bit 7 because all seven validated entries have it clear and
the terminator is FF; unknown commands use existing `6D33` SETC/RET.
The index expression becomes `2*RW5C + 0A48`, locating the relocated jump table
at `6CFA`. No new RAM, stack frame, bank switch or free-space claim is needed.

The image builder validates the original hash, exact hook bytes and command
table, disassembles the replacement, and exclusively creates a new `.IMG`.
Original OS/ROM inputs remain unchanged. Output SHA-256:
`0c24823eac6370ed9d9a382f499a602a2b8cb6593072c10f7fbf16ccb8cff59e`.
Reproduction from the repository root, using a fresh private output path:

```powershell
python scripts/patch_sds_cancel_guard.py --input roms/System/S760224.IMG --output temp/work/S760224.SDS-GUARD.IMG
```

Three fresh native processes test cancellation delays of 0.05, 1.0 and 1.5
emulated seconds. Each rejects an active-transfer header and a cancellation
header, ignores the rejected transfer's packet, settles without a leak, then
publishes a successful retry and a subsequent sample. Existing allocated PCM
and all unrelated public descriptors remain exact. Together they publish nine
samples/28,800 transmitted PCM bytes and emit 375 ACKs plus six exact CANCEL
responses. In the late case cleanup becomes idle before the ignored-packet
snapshot; cursor and content remain unchanged. The guard bytes are verified
in boot-loaded RAM at every snapshot. Three focused tests cover 65,536 decoded
command/state combinations and image safety; patched-OS ordinary playback,
scheduled MIDI and variable-block audio checks also pass.
[Validation](../../condensed/validation/bluescsi-cancel-ownership-2026-10-18.json).

This closes the observed cancellation defect in the experimental patched OS.
That first guard does **not** make `2BBA` a complete transaction lock: successful
packet completion clears it before publication, and `8998` clears it before
other error cleanup. The follow-up below repairs those header-admission paths.
The importer still requires one explicit owner spanning reservation, both
channels, publication or rollback, and final UI cleanup.

### Header admission through publication and error cleanup

BUG-119 reproduces both remaining header windows with the cancellation-only
image. A 41-word receive followed immediately by another header publishes a
descriptor for the second reservation (block 2/count 2) while abandoning the
completed PCM in block 1. Cursor settles at 4 rather than 2. An invalid slot-512
header followed by a valid receive during its error screen leaves cursor 2
rather than 1 and publishes nothing. Read-only taps identify the original
`001F:73A8` and `0166:8998` state clears that reopen admission prematurely.

[patch_sds_header_lifecycle.py](../../../scripts/patch_sds_header_lifecycle.py)
includes the cancellation guard and extends the private OS state contract:

| State | Header admission / supervisor action |
| --- | --- |
| 0 | Accept a new header |
| 1 | Receive packets; reject new headers |
| FF | Payload complete, publication pending; reject new headers |
| 2–5 | Allocation/validation error cleanup; reject new headers |
| 0A | Cancellation cleanup; reject new headers |

The rewritten `001F:738F` uses indirect word loads through scratch RW6A to fit
the FF store within the original 31 bytes. Its 32-bit unsigned completion
comparison is preserved; only `2BBA` is written. `0166:87E4` routes state 1 or
FF through the receive supervisor; `8848` recognizes FF as completion. The
error dispatcher no longer clears states 2–5 on entry. Its CRT/LCD return paths
share the CE62 call and join `8905`, which clears state and parser mode after
publication/rollback and UI teardown. Other high error values retain the old
clear-and-return behavior. No CPU implementation, RAM allocation, stack frame
or bank switch is added. Six existing spans total 123 bytes; 96 bytes change.

The first trial used marker 80. A short transfer completed before supervisor
entry, and modeled JGT misrouted `80-1` because it checks N/Z, not N XOR V.
That trial and its initially incorrect instruction model are retained as
excluded intermediate evidence. The final marker FF avoids that overflow
boundary; the corrected test fails the first trial and passes the final image.
Native read taps confirm supervisor entry with FF followed by exact publication.

Final native acceptance: four fresh processes exercise publication overlap,
invalid-slot error/retry, short burst completion before supervisor entry (8 MiB),
and cancellation compatibility (other cases 32 MiB). Together with two prior
image counterexamples they retain 78 snapshots. Eleven published samples match
10,800 transmitted PCM bytes; existing allocations and unrelated public slots
stay exact. All 148 ACKs and five CANCEL responses match. Seven focused tests
include 841 unsigned completion boundary pairs, state dispatch, both CRT/LCD
exit branches, image safety, and the prior 65,536 command/state matrix.
Ordinary patched-OS playback, scheduled MIDI and variable-block audio pass.
[Validation](../../condensed/validation/bluescsi-header-lifecycle-2026-10-18.json).

Build from the original image into a fresh private output path:

```powershell
python scripts/patch_sds_header_lifecycle.py --input roms/System/S760224.IMG --output temp/work/S760224.SDS-LIFECYCLE.IMG
```

Final SHA-256:
`54c7b7ecb36b16c0f17b06b8f0ab2a0cbab5f04fad407e46cebc78db0f3f81e2`.
Original inputs remain immutable. This qualifies **incoming header admission**,
not a general lock against other SDS commands or native disk operations. Only
invalid-slot state 2 is exercised as a native allocation error; resource
exhaustion, pre-supervisor cancellation, timeouts, controller combinations,
physical behavior and atomic stereo publication remain open. The SDS writer's
reservation overruns remain unchanged; it is still unsuitable for bounded WAV
import without replacement.

### Receive-owner exclusion for outgoing requests

BUG-120 shows that an incoming command 03 can bypass the header guard and call
`001F:6990`, which clears `2BBA` and replaces the shared transfer metadata.
With a 41-word seed and a second 41-word receive, a request after packet 0
changes state 1 to 0; after the last packet it changes completion FF to 0.
Both prior-image controls eventually roll the cursor from 2 back to 1 without
publishing the second sample. The existing seed remains intact.

[patch_sds_request_guard.py](../../../scripts/patch_sds_request_guard.py)
includes the BUG-118/119 patches and rejects command 03 whenever `2BBA` is
nonzero. The guard at `001F:6D81` runs before slot decoding, voice stop and
sender setup, using the existing `6D30` CANCEL/SETC return. The original
13-byte handler calls `7370` only when idle. That decoder retains the two
seven-bit slot bytes and B180 store, compares against 512, returns carry set
for invalid slots, and tail-jumps to the existing sender `695A` for valid
slots. Its return uses the existing decoder call frame. The only decoded
caller of `7370` in the source export is `6D81`; no new caller ABI is claimed.

Two existing spans, file `00F181..00F18D` and `00F770..00F78E`, add 19 changed
bytes to the header-lifecycle image. The combined patch changes 115 bytes in
eight spans totaling 167 bytes; 67 replacement instructions decode exactly.
It adds no RAM, bank switch, free-space dependency or stack frame. Build from
the immutable original into a fresh private output:

```powershell
python scripts/patch_sds_request_guard.py --input roms/System/S760224.IMG --output temp/work/S760224.SDS-REQUEST.IMG
```

Output SHA-256:
`cb5f65ef1ea15646ccee1ec3e20eddc801e1ccc80d6198dac5a3022524537e40`.

Seven final native runs cover request rejection during receive, publication,
invalid-slot error cleanup and cancellation; ACK/NAK during receive with sender
state FF; and normal idle sending. They publish 18 samples with 2,880 exact
transmitted PCM bytes, preserving earlier allocations and unrelated descriptors.
All 56 ACKs and five CANCEL replies match exactly. The idle sender exports all
9,216 allocated sample bytes through 116 packets plus one exact NAK retransmit,
then accepts a subsequent receive. Its last packet's 96 zero wire bytes are
outside the declared 4,608 words; they decode to 8000, not PCM silence.

Two failing prior-image controls and one passing prior ACK control bring the
retained total to 118 snapshots. Ten focused tests pass: the new tests cover
all 16,384 seven-bit slot values, all 255 busy states with five representative
slots, branch/call depth and image safeguards, alongside the previous seven
regressions. Ordinary patched-OS boot/playback, scheduled MIDI and variable
block audio pass with the unchanged native executable.
[Validation](../../condensed/validation/bluescsi-command-exclusion-2026-10-18.json).

This closes BUG-120's receive-owned request overlap in the experimental image.
It does not establish ownership of an already-active outgoing dump: overlapping
receive headers/new requests and stale ACK/NAK sender state remain unqualified.
Disk exclusion, cancellation before supervisor entry, native exhaustion,
timeouts, atomic stereo publication, bounded WAV writing and physical/controller
qualification remain open. Original firmware and runtime sources are unchanged.

### Shared admission for active senders and receivers

BUG-121 supplies the opposite-direction counterexample. After two distinct
41-word seeds, request a dump of slot 0. A receive header while the sender waits
for ACK changes `2BBA` from 0 to 1, reserves another block and replaces the
sender range; a subsequent ACK acts on the receive's shared counter. A second
dump request after packet 0 emits another header and switches the source to
slot 1. `B1AE` is 1 while waiting for the initial ACK and 0 during the dump;
checking `2BBA` alone misses both sender phases.

[patch_sds_sender_guard.py](../../../scripts/patch_sds_sender_guard.py)
extends the private image with one admission rule for commands 01 and 03:
accept only if `2BBA == 0` and `B1AE == FF`. The helper at `001F:6D20` computes
`((B1AE + 1) & FF) | 2BBA` in scratch R6A and returns its zero flag. Busy
headers/requests use the existing CANCEL/SETC return without decoding,
reservation, voice stop or sender reinitialization. Data, ACK, NAK and explicit
CANCEL retain their existing dispatch paths.

The helper fits in the existing dispatcher/header extent `001F:6CDD..6D34`,
file `00F0DD..00F134`. Header setup reuses the unchanged counter initializer at
`001F:6AA5..6AB4`: load FFFF into RW5C, store both B1A0/B1A2 words, CLRC, RET.
Its callee order and allocation/descriptor-error exits remain intact. Admission
and counter initialization use temporary two-byte call frames; no RAM storage
or new code region is allocated. Complete interrupt/stack bounds remain open.
The combined image changes 146 bytes in eight spans totaling 204 bytes; all
89 replacement instructions decode exactly.

```powershell
python scripts/patch_sds_sender_guard.py --input roms/System/S760224.IMG --output temp/work/S760224.SDS-SENDER.IMG
```

Output SHA-256:
`a5817b0f891242b3f8e40f5caa86b46861f8feed58089bf279b78ba4d5f38684`.

Ten final native runs include four overlapping sender/header or sender/request
cases (before initial ACK and during data), two explicit sender cancellations,
and four receive request/publication/error/cancel regressions. All 28 received
samples match 4,480 transmitted PCM bytes. Four complete outgoing dumps retain
36,864 sample bytes and exact retransmission; all 469 outgoing data packets,
86 ACKs and nine CANCEL replies match. The rejected message changes B1AC to
7D as response scratch; transfer counters/ranges, staged metadata, existing
allocations and unrelated public descriptors remain unchanged. Completion or
explicit cancellation restores B1AE=FF; stale ACK/NAK during the next receive
are ignored without changing its counters or PCM.

Two failing prior-image controls bring the retained total to 182 snapshots.
Thirteen focused tests pass, including 131,072 decoded admission cases (both
entries across every pair of state bytes), header callee ordering/error exits,
unchanged counter-helper bytes, and the prior ten regressions. Ordinary patched
OS boot/playback, scheduled MIDI and variable-block audio pass. Original
firmware and native sources remain immutable; no new full-suite run is claimed.
[Validation](../../condensed/validation/bluescsi-sender-ownership-2026-10-18.json).

This qualifies admission in both directions for the tested native SDS paths,
including explicit completion/cancellation. It does not establish a timeout
policy for an abandoned sender; completion or explicit MIDI CANCEL is required
to release it in this contract. Native disk exclusion, receive cancellation
before supervisor entry, exhaustion, packet-number-wrap retry, bounded WAV
writing and atomic stereo publication remain open. Sender fixtures occupy one
allocation block. Hardware timing and other controllers remain unqualified.

## Receive ordering and buffer bounds

6D35 accepts processing only while state 2BBA is 1. Helper 71F7 XORs 121 bytes B04F..B0C7 into B04C, then compares the received packet byte B04F to `(low8(counter) + 1) & 0x7F`. A mismatch returns carry set and leads to response 7E. A match increments the full 32-bit B1A0/B1A2 counter **before** conversion or sample-memory writes. Initial counter FFFFFFFF therefore expects packet zero.

7242 converts the 120-byte data portion starting at B050:

| B1AA range | Input bytes per word | Output words | Output buffer, inclusive |
| --- | --- | --- | --- |
| 0..14 | 2 | 60 | B1B0..B227 |
| 15..21 | 3 | 40 | B1B0..B1FF |
| 22..28 | 4 | 30 | B1B0..B1EB |

Values above 28 return carry set. Caller 6D44 does not branch on that carry; it continues through housekeeping to 72D0. The writer independently selects the same three counts or returns carry set for an invalid format. The caller also does not test that return before completion comparison and response 7F. Upstream format constraints must be established before treating this as reachable erroneous behavior.

72D0 writes converted words XOR 8000 through C00A, using C00C/C00E for the current address and polling C000 bit 1. It advances B19C/B19E by the selected word count. 738F clears transfer state when the current address reaches or exceeds B198/B19A. The fixed-size writer does not locally shorten the last receive block to the remaining count.

The XOR accumulator is updated but not tested by 71F7. The 7E end-of-message branch at 5F62..5F6C goes directly to dispatch 6CDD, bypassing the separate Roland-path additive checksum gate at 5F7A. Neither observation proves the complete absence of checksum qualification elsewhere; it identifies the exact path needing a native malformed-packet test and caller audit.

## Send, retry and cancellation

6BAE computes `start + 40 * uint32(B1A0,B1A2)` with 32-bit arithmetic. An address greater than end marks B1AE=FF and returns carry set. Otherwise it sets B1AD=40; if address+39 exceeds end, it changes the count to `end-address+1` and sets B1AE=FF. These comparisons treat this send path's end as inclusive. Do not silently merge that convention with the receive completion comparison.

6C29 calls 73F5, which builds `F0 7E device 02 (counter & 7F)`, invokes payload output 757E, and appends the accumulated XOR and F7. This differs from the six-byte 7D/7E/7F response builder at 749F.

757E programs the hardware address to current-address minus one, performs a priming read, and then reads **40 words** into B1B0 even when B1AD is smaller. The packing loop converts only B1AD words, XORing each with 8000 and producing three seven-bit bytes. 762D..7636 fills the remaining output bytes with zero up to B0C7; 7641 sets the output length to 120. Thus a partial final packet still has a full 120-byte data payload, with zero padding. The shorter count limits packing, not the hardware read loop. Whether the extra reads cross a meaningful hardware boundary remains a runtime question.

| Incoming dispatch | Local behavior |
| --- | --- |
| 7D / 6D8F | Set state 2BBA=0A, B1AE=FF, parser register R72=8. No local allocation restoration. |
| 7E / 6DA3 | Ignore when B1AE=FF. Otherwise compare B04F to the **unmasked low counter byte**; equal resends through 6BAE, unequal increments the full counter before sending. |
| 7F / 6DD5 | Ignore when B1AE=FF. Otherwise clear B1AE if it was 1, increment the full counter and send through 6BAE. |

Outgoing packet numbers mask to seven bits; the retry comparison does not. Behavior across counter 127/128 is therefore a specific validation target, not an assumed modulo-128 comparison. The supervisor supplies a static cancellation/timeout owner, but its real elapsed timeout and complete cleanup effects remain unresolved.

## Evidence and remaining work

[Validation](../../condensed/validation/os-transfer-lifecycle-2026-10-16.json) retains 596 packet/allocation anchors plus 301 supervisor/entry anchors, input and tool hashes, and explicit limitations. The manifest adds 298 instructions spanning 988 bytes under the evidenced supervisor entry mapping. No new code coverage is claimed for interpreting already decoded packet instructions. OS-001 and OS-002 remain active until callee contracts, complete cleanup and ordinary runtime behavior are qualified.


## Callee and publication follow-up

003B:6F90 is a leaf that writes 1BAA=1, clears F000 bit3 inside PUSHA/POPA, then writes 1BA8=1. It does not change R30 or a fetch selector. Its earlier provisional context-save name was misleading; the manifest calls it transfer_io_gate.

004B:675C selects a UI branch using 2476 and RDC. When RDC is nonzero, it invokes 003B:6244 or004B:4D38, then003B:4919 through CE14. CE14 saves/restores fetch0102 and RW28/2A/2C/2E/42; it does not itself protect R30 or0104. Those target routines remain dependencies of the preservation claim. In contrast, CE62 saves/restores0102/0104 and RW20..3E (even addresses) plus40/42/44/46, including R30. Both wrappers push an explicit return continuation before BR[RW1E]; those continuations are separately justified decode roots, not guessed indirect destinations.

004B:6A26 receives R4A=5 and RW4C=the selected slot in the success path. Its type5 arm computes RW4E=4000+0x30*low8(slot), selects data page034A for high8(slot)=0 or0356 otherwise, and adds3000 if high8(slot) bit1 is set. For this path's bounded slots0..511, that additional offset is never selected. The caller copies48 staged bytes from1F6E to this final destination at0166:8B55..8B5B. This establishes final publication separately from initial slot selection and memory reservation.

The helper also maps type2 to page02FA with256-byte stride, type11 to0363 with128-byte stride, type3 to030A/031A with256-byte stride and64 records per bank, type4 to032A/033A with128-byte stride and128 records per bank, and type12 to036B/037B with128-byte stride and128 records per bank. Type1 returns1CCE; unsupported types return pointer zero. These are observed numeric type tags, not inferred user-facing object names. Caller index bounds beyond the transfer path remain unproved.


### UI preservation closure

The explicit CE14 invocations from675C have now been followed into003B:6244/4919 and004B:4D38, then into the LCD/CRT text consumers003B:64FA and004B:4550. Their decoded local closures contain no explicit R30/R31/RW30 or fetch0104 writes. The only unresolved outgoing calls in this group are the already-decoded CE14 wrapper calls. This strengthens the supervisor's saved-state interpretation for these invocation chains; it does not prove arbitrary indirect memory effects or interrupt preservation.

Both text consumers terminate on NUL and treat01 as an escape followed by a token byte. They select data02E9 and locate the `(token-80)&FF` entry in a NUL-separated dictionary at42BA. Dictionary allocation bounds and runtime token validity remain unresolved, so the full apparent string pool is not classified merely because it looks readable. LCD character advance wraps32columns/8rows; CRT advance wraps40columns/25rows. Four fixed9-character labels plus terminators selected by4919 are bounded on data02DB at431B..4342. [UI evidence](../../condensed/validation/os-ui-preservation-2026-10-16.json) records472 instruction anchors, with overlap deduplicated in coverage.
## Outgoing request entry and voice stop

The universal7E lookup byte03 selects001F:6D81. Helper7370 decodes the requested slot from two seven-bit bytes and rejects indices above511. It then calls695A, which saves fetch0104, installs002D for dependent voice services, calls resident000F:2553, and restores0104. This uses the timer's retained000F window0 mapping; it does not infer the bank from the numeric call target alone.

2553 walks24 indices, invoking3C3B for each nonzero1F52 flag. That helper selects the hardware voice, writes zero control pairs, and pollsD006/D004 until both are zero before4BB1 clears the allocation/activity state and30E0 releases the resident bookkeeping. Direct calls to46C2 reach14 NOPs and RET; they are deliberate firmware delays but this analysis does not assign elapsed time. Hardware polls are unbounded locally. Native voice-stop timing and arbitrary interrupt contexts remain unvalidated.

6990 rejects an empty descriptor, derives the start/end word range and length from descriptor+28/+2A using0x1200-word allocation blocks, and limits total length to1FFFFF. It derives the two loop positions from fixed-point descriptor addresses, maps the local loop mode, and initializes the sequence counter toFFFFFFFF. Successful preparation invokes73AE/74F7 to send the header, then setsB1AE=1; failures setB1AE=FF. Acknowledgment handlers already described above drive subsequent packets. This establishes the static outgoing entry chain without treating neighboring0166 SCSI routines as its owner.

[Sender and display-helper anchors](../../condensed/validation/os-send-and-copy-helpers-2026-10-16.json) verify the newly decoded dependencies. Repeated code covered by existing regions is deduplicated in the coverage inventory.

## Local Sample Dump cleanup and remote stalls

Finding 236 qualifies BUG-122 in experimental firmware. The native System
MIDI / SmpDump UI enters sender setup at `0166:9A35..9A42` and waits on
`02BE:B1AE`. If no initial ACK arrives, its counted wait falls back through
`001F:6ABF` to a paced local send. The remotely requested `001F:6D81` path does
not enter this UI owner in the observed runs. This distinction corrects any
reading of the remote-only sender evidence as full local UI qualification.

Stock local exit tails `0166:9AA0`, `9B0B` and `9BA8` write B1AE=0. After
BUG-121's guard that idle value conflicts with active-send state 0. A prior
image completes all 116 outgoing packets but rejects the next receive with
CANCEL and leaves cursor 2. The repair consolidates the three existing
28-byte tails (file `05FAA0..05FABC`, `05FB0B..05FB27`, `05FBA8..05FBC4`,
end-exclusive). Common cleanup clears 2BBA, sets parser R72=8 and performs the
existing CRT cleanup when applicable. The final helper at `0166:9BAA` saves
010C, selects data 02BE, writes FF to B1AE and restores 010C before return.
It needs one temporary two-byte selector word, not a new code/RAM region.
Full nested stack bounds remain open. An earlier repair omitted this bank
selection and failed both Exit tests; those failures are retained and excluded.

The combined image changes 226 bytes in eleven spans totaling 288 bytes;
SHA-256 `472b656b5ab859d1c6eb9814e25a3d1ecad69785db47b50e72fe20d96649dbd3`.
[Builder](../../../scripts/patch_sds_local_cleanup.py),
[decoded tests](../../../tests/test_sds_local_cleanup.py),
[validation and reproduction sources](../../condensed/validation/bluescsi-local-sender-lifecycle-2026-10-18.json).
Twenty-four focused tests pass, including all three tails under three mocked
controller branches and a display call that clobbers the data selector.
The third error tail is **decoded/unit coverage only**: the native empty-slot
attempt was rejected before reaching it. LCD/GB-6 have no new native result.

Four final local runs cover acknowledged/unacknowledged completion and Exit
cancellation; a fifth covers a remotely requested no-ACK stall and explicit
MIDI cancellation. Fifteen received samples retain 2,400 exact transmitted PCM
bytes, and two full sends retain 18,432 bytes. All 45 ACKs, two CANCEL replies
and 251 data packets match; unrelated descriptors and prior allocations remain
unchanged. Five accepted runs plus three negative controls retain 115
snapshots. Ordinary playback, release, scheduled MIDI and variable-block audio
rendering pass. Original firmware/native source and executable are unchanged.

The checkpoint-16 BUG-123 counterexample remains valid: the remote header-wait state stays 1 after at least 60
emulated seconds and ordinary panel Exit. MIDI CANCEL clears it and the next
receive publishes successfully. This does not prove an infinite wait, qualify
an elapsed-time deadline, or test a stalled data-phase sender. The next section
qualifies a separate remote recovery patch before extending this owner to the importer.
Also qualify local UI entry/completion races and Disk operations: a local
caller still bypasses remote admission, and the sender's FF completion can
precede UI cleanup. This patch repairs quiescent exits, not all such races.

## Foreground remote sender recovery

Finding 237 fixes BUG-123 in an experimental OS image. A prior-image control
also remains busy in the data phase after six seconds and panel Exit; peer
CANCEL releases it. The new remote command 03 path retains the shared admission
guard, calls the existing slot decoder/sender setup, then claims **2BBA=7** only
on success. This keeps admission closed even if B1AE reaches FF before the
foreground owner runs. Failed setup leaves receive ownership unchanged.

The original receive supervisor's first instruction at `0166:87B5`, file
`05E7B5`, becomes a call to a dispatch helper. States other than 7 still return
the original state in R30. State 7 enters the remote owner; it returns R30=0 so
the original supervisor does not publish a receive descriptor or roll back
the allocation cursor. The main-loop caller at C872/C875 is native-qualified.
The shared hook also lies on a native SCSI-service call path; that caller and
Disk coexistence still need qualification.

The owner cancels after **5,000,000 TIMER1 ticks without a packet-counter
change**, or ordinary panel Exit. It accumulates unsigned 16-bit timer deltas
into a 32-bit elapsed value. Any change in B1A0/B1A2 resets the deadline and a
separate **1,048,576-poll budget**; same-packet NAK does not count as progress.
Completion or peer CANCEL takes precedence at the top of a poll. Timeout/Exit
first marks B1AE=FF, emits native CANCEL, clears 2BBA and leaves parser R72=8.
No sample allocation, descriptor or wave contents are changed by this owner.
Its raw four-row panel scan reads the Exit bit without manufacturing UI events.

PUSHA/POPA preserve PSW/window/masks. The helper saves selectors 0102/010A/010C
and forty register words 1C..6A. Each brief interrupt service window preserves
that scratch again while leaving parser/timer registers at 70 and above live.
Seven native remote runs restore all captured scratch words, all selectors,
WSR and PSW, and return to the caller's SP. The observed stack low-water mark
is 106A versus caller SP1120: **182 bytes**, not a complete nested stack bound.
The maximum observed TIMER1 read gap is 42.710 ms, below its 65.536 ms wrap in
these workloads. Timeout elapsed values are 5,000,046..5,000,070 microseconds;
the CANCEL helper returns 2.0705 ms after the abort write in the measured runs.
The deadline begins at foreground admission, not MIDI request arrival.

The helper occupies **640 bytes** at `000F:0780..0A00`, file`008B80..008E00`,
physical`004380..004600` (end-exclusive), inside the proposed lower code area.
It uses no new persistent RAM. The combined SDS image changes 842 bytes in 13
spans totaling 933 bytes, SHA-256
`46d2c6da3e35d2c6bfcc45e08820cebd40836343ed6de0f2cc3112f121a460b3`.
[Builder](../../../scripts/patch_sds_remote_owner.py),
[decoded tests](../../../tests/test_sds_remote_owner.py),
[validation and reproduction sources](../../condensed/validation/bluescsi-remote-recovery-2026-10-18.json).
The transport diagnostic and this owner have not yet run in one combined image.

Seven remote cases cover header/data timeout, header/data Exit, resumed
progress, peer CANCEL and complete send with exact NAK retransmission. Four
local UI cases retain acknowledged/unacknowledged completion and Exit.
All 11 accepted runs publish 33 samples with 5,280 exact received PCM bytes;
three complete sends retain 27,648 bytes. All 99 ACKs, seven CANCEL replies
and 371 data packets match, including padding. A negative control brings the
retained total to 180 snapshots. Late ACK/NAK after release and during the next
receive leave its packet counters, addresses and PCM unchanged; its ordinary
receive stall counter continues advancing. Thirty focused tests and ordinary
boot/playback/release, scheduled MIDI and variable-block audio checks pass.

This is a scoped native firmware fix, not a physical deadline guarantee.
Stopped-clock poll exhaustion has decoded/model coverage only. Native sender
setup, voice-stop and UART waits remain locally unbounded; this loop cannot
rescue a stuck callee or CPU. WAIT handling, counter 127/128 NAK comparison,
local UI entry/completion races, native Disk exclusion, complete stack/ISR
bounds, pre-supervisor cancellation and controller/hardware acceptance remain
open. Stereo allocation/publication/rollback and bounded WAV writing are
separate BS1 requirements. Original firmware and native source/executable
remain unchanged; no new full backend-suite result is claimed.

## Local ownership through setup and cleanup

Finding 238 fixes BUG-124 in experimental firmware. Two ordinary native MIDI
sequences reproduce the checkpoint-17 image's remaining local completion race:
queue final ACK114 and immediately append a receive header or remote request.
The sender marks B1AE=FF before its UI cleanup finishes. The header is admitted,
advancing the allocation cursor 2→3 and setting state 1; local cleanup at 9AA0 then
clears that owner. A settled retry advances to 4 and publishes the third sample
from block 3, leaving block 2 unpublished. Two zeroed bytes at wave offsets 27666/
27667 are also retained in this negative control; the existing samples remain
intact. In the request case the second outgoing header appears and remote
state 7 is claimed, then the old local cleanup discards that owner as well.

The repair replaces the entry span `0166:998E..99AC` (end-exclusive). Under
PUSHA it selects the shared sender page, requires 2BBA=0 and B1AE=FF, and checks
the selected descriptor using the original 004B:6B2E lookup. Empty or zero-block
samples are refused. A valid idle entry claims **2BBA=8** before shared local
setup or drawing. Rejected calls preserve owner state and restore the original
fetch/data selectors and RW6A. The selected-slot lookup's 125 decoded
instructions contain no calls or interrupt enable/restore instructions.
Busy entry and invalid-slot cases have decoded/model coverage; native runs
enter from idle and exercise the later competing commands.

The existing PUSHA/POPA at 9A35..9A42 still surrounds sender setup. A helper
called from 9A3F reclaims state 8 after successful 695A, which temporarily clears
2BBA while interrupts remain masked. Failure retains original state 6. The
early state clear at 9B85 is removed so its error message remains owned. The
three common exit tails also retain ownership through display cleanup. Final
release at 000F:0A7C selects data 02BE, writes B1AE=FF, resets parser R72=8 and
clears 2BBA while masked, then restores the bank and PSW/window/masks. Peer
CANCEL may change state 8 to 0A; that nonzero state still excludes new admission
until the same final release. No new persistent RAM is allocated.

The new helper occupies **160 bytes** at `000F:0A00..0AA0`, file`008E00..008EA0`,
physical`004600..0046A0` (end-exclusive). Its entry saves an explicit 10-byte
frame, excluding call returns/callees; release saves 6 bytes and the setup
wrapper adds one 2-byte return. Complete nested stack bounds remain open.
The combined SDS image changes 1,034 bytes in 17 spans totaling 1,131 bytes;
SHA-256 `248b94253c95069070d4625168f867fdfcf20c98a699b0e09dbddd1038908431`.
[Builder](../../../scripts/patch_sds_local_owner.py),
[decoded tests](../../../tests/test_sds_local_owner.py),
[validation and reproduction sources](../../condensed/validation/bluescsi-local-owner-2026-10-18.json).

Nine accepted native cases cover both completion races, peer CANCEL followed
by an overlapping header, four local completion/Exit controls, remote header
timeout and complete remote send with NAK retransmission. All 27 received
samples match 4,320 PCM bytes; five complete sends retain 46,080 bytes. All 81
ACKs, six CANCEL replies and 601 data packets match exactly. Existing samples,
full wave snapshots and allocation cursors remain unchanged during accepted
send/cleanup cases. Settled retries publish the third sample at cursor 3.
Two prior-image controls bring the total to 175 snapshots. All 96 focused tests
and ordinary boot/playback/release, scheduled MIDI, audio rendering and clean
shutdown checks pass. Original firmware and native sources/executable remain
unchanged; the historical 590-test backend run was not repeated.

This closes the reproduced local completion gap and installs a shared local
entry gate. It does not exhaust preparation/cancel timing, qualify the native
setup-failure tail or prove Disk-operation exclusion. Native Disk/service
coexistence, pre-supervisor receive cancellation, resource exhaustion, complete
stack/ISR bounds and physical/controller behavior remain open. The diagnostic,
remote and local helpers total 2,371 bytes of the proposed 3,074-byte code/UI
allowance, leaving 703 arithmetically and 672 contiguous bytes after 0AA0. They
have not run in one combined transport image; complete client fit is unproved.
Atomic stereo publication/rollback and bounded WAV writing remain separate
BS1 work.


## Early receive cancellation ownership (BUG-125)

The current experimental image distinguishes receive rollback from generic
cancellation. StateFE means an unpublished receive must roll back; states1,FF
andFE becomeFE on CANCEL. Other states retain0A. This supersedes the earlier
generic0A receive-cancellation contract above. FE remains busy for admission,
routes through the signed receive branch at0166:87E4, and is recognized by
the updated cancel comparison at883D. Existing8B5F rollback restores3616 and
allocation mirrors before UI cleanup releases2BBA. Repeated CANCEL preservesFE.

The31-byte helper at fetch000F:0AA0..0ABF (file008EA0..008EBF,
physical0046A0..0046BF, end-exclusive) replaces8 bytes at001F:6D8F with a
tail jump, then rejoins6D97 to idle B1AE and reset the parser. It uses existing
R6A scratch and adds no stack frame or persistent RAM. No ISR-side allocation
rollback is introduced. Existing sender cancellation and full local send pass.
The one-packet completion/CANCEL burst exercisesFF-to-FE before publication;
settled cancellation and retry reuse the released block.

[Builder](../../../scripts/patch_sds_early_cancel.py),
[decoded tests](../../../tests/test_sds_early_cancel.py),
[native and prior-image evidence](../../condensed/validation/bluescsi-early-cancel-2026-10-18.json).
