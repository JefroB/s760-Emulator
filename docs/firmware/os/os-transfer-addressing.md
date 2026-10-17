# Transfer address mapping, slot search and responses

## Nibble-addressed readback

001F:610B searches a six-byte-record table at data page 02BE:AFB6. Each record contains a little-endian 32-bit base and 16-bit extent. Bases descend from 218000 to zero across 21 entries. The index selects a memory-source path; gaps and unsupported source indices can emit zero. This is a protocol address map, not the CPU's physical memory map.

The valid-bank paths subtract the selected base, shift the offset right once, and read a byte. An even original protocol address selects the high nibble; an odd address selects the low nibble. 6236 masks the result to four bits before emitting it and increments the protocol address by one. Consequently, the 256-unit chunk at 6700 represents up to 256 nibble values on this path, not 256 source bytes.

| Table index | Base | Extent | Selected data page |
| --- | --- | --- | --- |
| 1 | 210000 | 7F00 | 037B |
| 2 | 208000 | 8000 | 036B |
| 12 | 036000 | 6000 | 0356 |
| 13 | 030000 | 6000 | 034A |
| 14 | 028000 | 7F00 | 033A |
| 15 | 020000 | 8000 | 032A |
| 16 | 018000 | 8000 | 031A |
| 17 | 010000 | 8000 | 030A |
| 18 | 00C000 | 4000 | 0363 |
| 19 | 004000 | 8000 | 02FA |
| 20 | 000000 | 0020 | Special read at 1CCE + half-offset |

Other indices return zero in this particular read helper; that does not establish that the corresponding addresses are unsupported by all write or transfer paths. The full initial table, including those entries, is retained in validation. Runtime modifications to the table remain unqualified.

## Sample-slot search and descriptor preparation

6FBF initializes B180 to FFFF, increments it, and searches up to index 511; reaching 512 takes an error-state path. Helper 6C2E maps indices 0..255 to data page 034A, and 256..511 to 0356 after subtracting 256. Descriptor address is `4000 + 48 * local_index`. The search accepts a descriptor whose word at offset 2A is zero. This establishes a free-slot criterion used here, not a complete allocation contract.

The following code copies a 13-byte template, appends decimal index-derived characters, and fills descriptor fields using transfer values shifted left eight bits. It derives further addresses by adding A00 and 400. The [lifecycle follow-up](os-transfer-lifecycle.md) explains reservation and publication; higher-level failure cleanup remains unresolved. After successful reservation and descriptor setup, 6D1A calls 4F05, which loops over 24 voices and invokes resident 30E0 for flagged voices after clearing associated flags; it is included as a separate decoded region.

## Response and transmit path

7481/748B/7495 select response bytes 7D/7E/7F. Shared code at 749F builds six bytes:

`F0 7E configured_device selected_response (B1A0 & 7F) F7`

It sets the transmit pointer B036 and count B038=6, then calls the transmit loop. 6872 reads bytes through that pointer. 689D writes each byte to CPU register 0116 and polls bit 1 of 0114 before returning. These are the actual byte-building and output operations; acknowledgment/error names and retry timing still need full state-machine qualification.

## Verification

The analyzer now accepts evidenced data ranges separately from code and rejects overlap with decoded instructions. The coverage inventory counts those bytes separately. The 126-byte range table is the first such declaration in this broader inventory; prior documented data structures are not retroactively claimed as inventoried.

Thirty targeted tests pass. [Validation](../../condensed/validation/os-transfer-addressing-2026-10-16.json) records the initial range table, decoded instruction anchors, file identities and qualifications. No firmware, emulator behavior or hardware state changed.
