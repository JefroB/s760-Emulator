# Resident MIDI parsing and controller dispatch

This static analysis names resident message paths from the status-class dispatch and checks their local behavior. It does not qualify hardware MIDI timing, every mode, or complete handler semantics. Instruction page 000F is established by OS startup; data selectors remain separate.

## Status-class dispatch

217E extracts the low channel nibble into R78. 2182–2186 extracts `(status & 0x70) >> 4` into R72. The data-byte path uses 21DE + 4*R72 as the address of a jump stub. Special handling can select index 8. Nine annotated stubs decode as follows:

| Index / status family | Destination | Interpretation |
| --- | --- | --- |
| 0 / 80–8F | 307A | Note off, shared note entry |
| 1 / 90–9F | 307A | Note on, shared note entry |
| 2 / A0–AF | 2203 | Polyphonic pressure path; matches channel and note against voice fields |
| 3 / B0–BF | 29F3 | Controller path |
| 4 / C0–CF | 23DA | Program-change path; mode/channel gates precede further work |
| 5 / D0–DF | 2255 | Channel-pressure path |
| 6 / E0–EF | 25FD | Pitch-bend path |
| 7 / F0–FF class | 5EB2 | Outside current resident mapping window; destination bank unresolved |
| 8 / special parser state | 2202 | Return |

At 307A the shared note entry returns if the saved note byte R76 is zero. Otherwise it copies the current data byte into R79, distinguishes class 0/1, and routes note-on with velocity zero to the same 3092 path as note-off; nonzero note-on routes to 3373. This is a decoded branch behavior, not yet a new physical test or a conclusion about every possible route for note zero.

At 2631–263F the pitch-bend handler combines saved low data byte R76 with current high data byte R73 into `(R73 << 7) | R76`, subtracts 8192, and stores the signed result at per-channel 8FC6 + 2*channel. Subsequent voice updates remain part of the larger handler.

## Controller tables

The controller entry first calls a more general per-voice mapping path at 2ACB. Therefore a no-op in the later fixed table does **not** prove that controller has no effect anywhere.

For controller numbers 0..10, range checks lead to eleven four-byte jump stubs at 2A5C:

| Controller | Fixed-table destination |
| --- | --- |
| 0, 2, 3, 4, 5, 8, 9 | 2A88 (return from this fixed path) |
| 1 | 2F55 |
| 6 | 2DB7 |
| 7 | 2C53 |
| 10 | 2CB2 |

Controller 38 branches directly to 2DD5. Controller 64 branches to 2D2B, which checks bit 6 of the value, matching the 64 threshold, and updates per-channel/per-voice hold-related fields. Controllers 96..101 use six stubs at 2AB2: 96/97 return at 2ACA, 98/99 share 2DA6, 100 selects 2DF3, and 101 selects 2E10. These destinations establish control flow, not full semantic qualification of parameter selection or value scaling.

The low table is bounded by an unsigned comparison against 10. The high table subtracts 96, rejects underflow, and rejects results above 5. Both multiply the index by four. These checks provide stronger target evidence than scanning arbitrary words for plausible addresses. Other invocation states remain explicitly unresolved by the generic analyzer.

## Tool correction and next unknowns

Four resident calls were previously listed as indirect because the decoder displayed negative hexadecimal destinations. BUG-077 corrects their representation: 2567/29EF target B299, 256A targets B247, and 256D targets B489. Their destination banks remain unresolved; the corrected numeric address alone does not establish a mapping.

Next work includes the general controller mapping path at 2ACB, parameter-selection handlers, and bank context for the system-message and B2xx/B4xx calls. No renderer or native MIDI implementation changed. The exploration manifest records the new dispatch annotations; the [validation record](../../condensed/validation/os-midi-decoding-2026-10-16.json) records the independently checked jump destinations and tool/input hashes.
