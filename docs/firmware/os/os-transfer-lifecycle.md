# Transfer allocation and packet lifecycle

Static analysis of OS 2.24, primarily instruction pages 001F and 0166. CPU addresses below require the established fetch mapping; Bxxx fields require the caller's transfer data mapping. This explains local control flow, not a native or physical transfer test.

## Reservation and descriptor publication

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
