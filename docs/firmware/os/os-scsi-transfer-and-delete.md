# SCSI sample transfer and deletion

Static analysis follows the explicit CDED invocation of0139:B418 from the [session service](os-scsi-session-decoding.md), then the explicitly selected005A:4A1A deletion service. [Evidence](../../condensed/validation/os-scsi-transfer-delete-2026-10-16.json) checks1,838 instruction anchors against the original image and records referenced reset-template extents. No deletion or SCSI transaction was executed.

## Target-side command processing

EntryB418 reads commands throughE416 with theE404 E4/C4 handshake andE40A bit6 polling. It saves command bytes in data02E9:70EA. The high three opcode bits select total command lengths6 for groups0..3,10 for groups4..6, and12 for group7. These are observed local choices, not a claim of standards compliance for every group. Opcode dispatch is bounded by explicit comparisons:

| Opcode | Handler | Observed behavior |
| --- | --- | --- |
| 00 | B5AB | Sends status0 and clears sense byte7156 |
| 03 | B5C6 | Returns up to3 bytes from7154, then zeros |
| 08 | B6DE | Sends sample descriptor or waveform block |
| 0A | BA40 | Receives sample descriptor or waveform block |
| 12 | B652 | Returns up to36 bytes from7130, then zeros |
| Other | B58C | Sends status2 and sets7156 to5 |

Handlers03/12 take their byte loop count directly from command byte4. The post-body DJNZ means an initial zero loops256 times; ordinary reachability and protocol consequences remain unvalidated. Do not silently rewrite this to a zero-byte transfer. Identification bytes in the original image contain `Roland  S-760 Ver. 2.24`; the36-byte table and3-byte initial sense buffer are classified data. Runtime sense byte7156 is mutable.

Status completionB50F drives phase3, sendsR30, drives phase7, sends zero, then releases throughE404=4. The register interpretation agrees with the existing project's two-byte-stride SPC mapping; physical bus timing remains unproved.

## Sample transfer state

All listed state fields use data page02E9. The selected sample index is a big-endian word from command bytes2/3, limited to0..511. Command byte4 must equal1. Command byte1's low5 bits select descriptor request1 or continuation0. Continuation also requires matching index and nonzero total block count.

| Field | Role in this closure |
| --- | --- |
| 70E8 | 0 idle,1 read continuation,2 write continuation |
| 70F6 | Selected index |
| 70F8 | Saved command byte4, required1 |
| 70FA | Source descriptor's original block base during reads |
| 70FC..712B | 48-byte staging descriptor |
| 712C | Current block cursor |
| 712E | Total block count copied from descriptor+2A |
| 7158..715F | Eight-byte transfer header |
| 7160 | Refresh request for session display |

Descriptor reads copy48 bytes from the type5 lookup destination. Five32-bit address fields at offsets10/14/18/1C/20 are converted to relative values by subtracting `((block_base*0x1200)+wave_base)<<8`. The staging descriptor's block base at+28 is zeroed. An8-byte header precedes the48-byte descriptor.

Read continuation sends an8-byte header followed by0x1200 words (9216 bytes), low byte first, through the wave-memory read portC00A. It advances the cursor and keeps state1 only while more blocks remain. Write continuation receives the same fixed byte count and writes words throughC008; it advances the cursor and keeps state2 while more blocks remain. Received headers are stored locally; these loops do not derive their transfer length from the header.

Before accepting a descriptor write, free blocks plus the old descriptor's+2A count must cover the incoming+2A count. The code then calls the deletion service, acknowledges and enters state2. It does not publish the new descriptor at this stage. After the last block,BD82 adds the new absolute base back to all five address fields, sets descriptor+28, copies48 staged bytes into the type5 destination, advances3616 by the total block count, and mirrors allocation bounds into0299:8F9E/8FA0. Cleanup on interruption and zero-block write behavior need separate validation; no atomic-replacement guarantee is claimed.

## Deletion and shared references

Entry005A:4A1A accepts a bank selector0/1 orFF (resolve from0299:8F9D), an object type and an index. Invalid explicit selectors return. It records these in2233/2232/2230. The known SCSI callers pass type5 and RW48=FFFF, and display the referenced `Delete Sample` label before the call.

For an individual deletion,4ACB clears the working mark area03B0:8180..9337. Type2 walks32 child bytes at descriptor+10; type3 walks88 child bytes at+20; type4 walks four16-bit sample references at+10/+20/+30/+40. A child is marked only when no retained parent references it. Type5 directly marks its sample. The tables hold128 type3 flags,256 reserved type4 positions (the traversal uses255),512 sample flags, and3640 block flags. The remaining resource count differences must stay explicit.

Marked samples contribute their block ranges using descriptor+28/+2A. Descriptor reset calls go through535D;52A6 also clears matching partial subrecord state. Freed trailing blocks shrink the used bound; internal runs are removed by moving later0x1200-word blocks and adjusting sample block bases and five fixed-point address fields. The block mover6F52/6FD7 uses DMA staging and additional wrappers; its remaining callees and runtime overlap/timing behavior remain unresolved.

RW48's low byte controls a final reference-removal pass: only zero invokes50E8. The known SCSI callers'FFFF therefore skip that pass. The separate52A6 pass still clears matching type4 per-sample state. Do not collapse these into a claim that all references are always removed.

## Descriptor reset templates

Interpreter5584 selects data0299. A00 byte terminates. Counts01..FE consume one value byte and repeat it; they are **not literal spans**. FF consumes a subcommand:0 emits16 bytes of channel-map defaults;1 emits index&7F;2 copies the11-byte length-prefixed subrecord at80DB;3 copies20 bytes at8100;4 copies the word at8114;5 emits16 FF bytes followed by16 7F bytes. The input template extents are bounded by this interpreter and their explicit callers.

| Type | Template interval, end exclusive | Expanded bytes |
| --- | --- | --- |
| 1 | 8020..802B | 32 |
| 2 | 802B..804C | 256 |
| 11 | 804C..8055 | 128 |
| 3 | 8055..808C | 256 |
| 4 | 808C..80DB | 128 |
| 12 | 80E8..80EB | 128 |
| 5 | 80EB..8100 | 48 |

Type numbers are hexadecimal. These are observed reset writes, not automatically the complete storage record sizes. Auxiliary source bytes80DB..80E6,8100..8115 are separately referenced. Byte80E7 remains unclassified because these consumers do not use it. Runtime mutation of the template sources is not excluded.

Remaining work includes request-field producers, DMA helper73C1, wrapperCEC8, page007F refresh services, exhaustive cancellation paths and ordinary native transaction validation.


## Block-copy helper closure

The explicitly requested73C1 helper programs DMA address0ED712 and controlBC, waits for0118 to become zero, then reads011D. The paired read-side7113 uses controlA7.6FD7 doubles the0x1200-word count for DMA byte length and uses the staging area between wave reads and writes. Control meanings follow the surrounding source/destination sequence; native timing and all DMA modes are not thereby validated.

Wrapper0000:CEC8 saves fetch0102/0104 plus15 working words, installsRW1C into0104, and callsRW1E through an explicitly pushedCEF8 continuation. It restores both selectors on return. Its page010A:8000 display/progress callee remains a separate dependency. The [request/DMA anchor record](../../condensed/validation/os-scsi-request-dma-2026-10-16.json) covers this closure.
