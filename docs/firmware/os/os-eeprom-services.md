# EEPROM configuration services

Static OS2.24 analysis under fetch page003B, reached through explicit selector/call sequences in page0 startup. The257-instruction closure has no unresolved outgoing calls or fetch-selector writes. This is firmware behavior recovered from original bytes, not a new hardware test.

## Configuration buffer and verification

Data page0299:8F74..8FF3 is a64-word configuration buffer. Entry5886 enables serial writes/commands, reads all64 words into that buffer through5A43, disables writes, then calls58F0 to reread and compare every word. A mismatch retries the whole read. Entry58BA erases/writes all64 words from the same buffer, then rereads and compares; mismatch retries the entire write. There is no local retry-count bound.

5845 accepts a byte address from8F74 inclusive to8FF4 exclusive, aligns it down to an even address, computes word index `(address-8F74)>>1`, and erases/writes that one word. Unlike the full-buffer routines, this helper does not locally reread and compare the value. It returns carry clear, including for out-of-range addresses that skip the operation.

## Serial operations

The existing hardware map identifies EEPROM wiring as P1.0=CS, P1.1=clock, P1.2=data-in, P2.7=data-out. These routines match that wiring:

| Helper | Operation visible in firmware |
| --- | --- |
| 5A43 | Command index OR80; shift in16 bits through P2.7 and return RW4A |
| 5A1E | Command index OR40; shift out16 bits from RW4A, then wait for ready |
| 5A57 | Command index ORC0; then wait for ready |
| 5A6A /5A74 | Send command30 /00 |
| 5A7E | Clear P1 low three bits, toggle select/clock, emit a start bit and8 command bits |
| 5A98 |16-bit input, most-significant bit first |
| 5AB1 /5AC8 |16-bit data /8-bit command output, most-significant bit first |
| 5ADF /5AE9 | Set/clear P1.2 |
| 5AF3 /5B05 | Toggle P1.1 /P1.0 |
| 5B17 | Toggle clock and poll P2.7 until high |

The command patterns support read/write/erase and write-enable/disable semantics of the documented64x16 serial EEPROM. Interrupt masking uses PUSHA/POPA around the serial operations. The ready poll has no local timeout; elapsed timings and behavior on missing hardware remain unmeasured.

## Defaults and startup checks

The default-copy helper5968 uses a source base8FF4, exactly80 hex bytes above the live buffer. If R4A is nonzero, it copies five words from8FF4 to8F74. In either case it copies48 words from9014 to8F94. It deliberately does not copy the entire128-byte block. Helper59C0 compares four bytes at8F80..8F83 against9000..9003;59F3 copies those four source bytes back into the live buffer. The precise field meanings require separate evidence.

Startup C12F calls the full read. C148 checks the four-byte comparison, and the following branch also inspects8F7E. The failure/reset branch sets R4A=1 when8F7E is zero and R4A=0 when it is nonzero, copies the selected default subsets, restores the four-byte field, clears8F7E and invokes the full write. The four default bytes in this image are ASCII `1.00`; their presence is established, but they must not be confused with the OS2.24 release number. Other startup branches update individual configuration fields and can invoke58BA or5845. This is not a checksum algorithm over the entire configuration buffer.

## Evidence and limits

[Byte validation](../../condensed/validation/os-eeprom-services-2026-10-16.json) contains every decoded instruction, explicit entry roots and input/tool hashes. Hardware pin attribution comes from the project's [hardware map](../../condensed/01-hardware-and-memory-map.md). No original image, EEPROM state or emulator behavior was changed. Field names, native failure/retry behavior and physical timing remain separate acceptance work.


## Boot-ROM counterpart

IC15 v1.11 independently uses64-word read/write/verify loops at532D/5350/5375 over RAM4CAA..4D29 and command helpers53C5/53A0/53D9. Its single-word helper52FE aligns a byte address within that buffer. Buffer bases, signature/default handling and helper addresses differ from OS2.24; this is semantic correspondence, not byte-identical firmware. See [boot-ROM analysis](../boot-rom/ic15-decoding-progress.md) and its EEPROM/audio validation for original-byte evidence. Neither set of unbounded retry loops has new runtime failure qualification.
