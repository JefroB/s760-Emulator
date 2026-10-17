# SCSI session and object notifications

This is static analysis of the original OS image. [588 instruction anchors](../../condensed/validation/os-scsi-session-2026-10-16.json) are checked against its bytes. No native SCSI transaction or physical MIDI capture validates these paths yet.

## Invocation and ownership

Startup 0000:C87C/C880 selects fetch page0166 before C885 calls8B91. This session service configures the E4xx SCSI register aperture, polls status, invokes storage processing, and sends manufacturer41 messages. It is distinct from the universal7E sample packet sender.

Page0:CDED saves fetch0104 and RW30/32/34/36/44, installs RW1C into0104, pushes return addressCE05, and branches throughRW1E. CE05 restores those words and the original selector. That explicit continuation justifies its analysis root. This establishes conditional mappings for the following calls; arbitrary invocation states remain unproved.

| Caller on0166 | Requested target | Local role |
| --- | --- | --- |
| 8C65 | 0166:87B5 | Existing transfer owner |
| 8CB0 | 01C7:8339 | Refresh selected object state and display |
| 8CD9 | 0139:B418 | SCSI status-triggered processing, semantics pending |
| 8CFD | 01C7:8000 | Object enumeration notification |
| 8D1B | 01C7:81AB | Conditional object operation and identifier notification |

The session loop polls1FA4 for exit. Byte1FA5 requests enumeration unlessFF; the caller resets it toFF after return. Word1FA6 requests the object operation unlessFFFF and is reset toFFFF afterward. The writers of these request fields and the SCSI transaction state machine still need tracing.

## Message formats

All three formats write serial data0116 and poll status0114 bit1 after each byte. Device ID comes from data page0299:8F9A. The checksum is the negative sum of bytes following command12, masked to7 bits. Names are transmitted directly by this routine; their upstream seven-bit validity is not established here.

| Producer | Bytes before checksum andF7 |
| --- | --- |
| 0166:8E1F | `F0 41 device 34 12 01 00 00 08 00 mode` |
| 01C7:80F2 | `F0 41 device 34 12 01 00 00 18 records...` |
| 01C7:81E1 | `F0 41 device 34 12 01 00 00 20 index_nibbles...` |

The session sends mode1 on entry and mode0 on exit. Its checksum is `(-9-mode)&127`. This interpretation names the observed entry/exit usage, not an independently verified protocol specification.

Enumeration accepts request0 for all five types, or1..5 for one type. Counts are1,64,128,255,512, respectively, with the last count reduced by two when2460 equals2, by one for another nonzero value, and unchanged for zero. Unsupported requests return without sending. For each index it calls004B:6A26 to locate the descriptor and skips descriptors whose first byte is7F.

Each record contains four nibbles (type, index bits8..11, bits4..7, bits0..3) followed by16 name bytes. Up to16 records share a message. A final message contains two zero bytes after the01/00/00/18 prefix, including when no records qualified. After each enumeration message the local delay loop decrements a counter initialized to15000; elapsed time is not inferred.

The identifier response sends four nibbles of the16-bit requested index, most significant first, after01/00/00/20. Entry81AB compares the request against0200 and conditionally calls005A:4A1A with type5, the requested index, RW48=FFFF and R4B from1BB9. Its operation semantics and callee preservation remain open; the response itself follows either branch.

## Selection and display

Entry8339 selects data02E9 and acts only when7160 is nonzero, then clears that flag. It copies RW48 toRWFE, preserves bytes2A30/295D around a refresh chain, and prints16 descriptor bytes on LCD or CRT. The refresh chain calls001F:4F7F with modes0 and4 around four page007F helpers. This connects an additional caller to the previously decoded controller-state reset; it does not establish all reset writers or the meaning of every mode.

Unfinished dependencies include page0139:B418,005A:4A1A, the page007F refresh helpers, request-field producers, resource strings, interrupt effects and native transactions. Original OS bytes remain unchanged.


## Request producers linked to the session

The normal manufacturer41 parser supplies the request fields. Under its established timer mapping,001F:6261 computes payload length, callsF874 to unpack the four-byte address, and dispatches:

| Wire address bytes | Internal address | Required payload | Effect |
| --- | --- | --- | --- |
| 01 00 00 08 | 00200008 | 2 nibbles | Decode a byte, mask bit0, write1FA4 |
| 01 00 00 18 | 00200018 | 2 nibbles | While1FA4 is nonzero, decode and write1FA5 |
| 01 00 00 20 | 00200020 | 4 nibbles | While1FA4 is nonzero, decode high/low bytes into1FA7/1FA6 |

This connects incoming requests to the outgoing session, enumeration and deletion messages. Initialization0000:C7F4..C802 sets1FA4=0,1FA5=FF,1FA6=FFFF. The main loop checks1FA4 before entering0166:8B91; the session polls it for exit. All requests still pass the existing manufacturer/device/model, receive-enable and additive checksum gates. Two-nibble helpers have an earlyF7 error return that callers do not check locally; valid-frame behavior is qualified, malformed reachability remains open.

The [request/DMA evidence](../../condensed/validation/os-scsi-request-dma-2026-10-16.json) anchors this connection. This is an end-to-end static chain, not an executed command test.
