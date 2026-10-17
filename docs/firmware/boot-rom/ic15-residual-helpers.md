# IC15 residual helpers and completion audit

Input is the unchanged 32,768-byte v1.11 ROM, SHA256 `ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6`. This report extends the [boot-ROM inventory](ic15-decoding-progress.md). All locations below are CPU addresses in the retained native ROM mapping: low fetch page0780, boot-service fetch0790, data010C=0798 for8000..BFFF. Physical reset defaults and arbitrary selector preservation remain unproved.

## Structural code versus reachable code

The new roots are explicitly structural. Bounded routines immediately adjoin independently decoded routines, call established helpers, use consistent RAM/device interfaces and terminate at established boundaries. This justifies decoding their encodings, but supplies no caller or ordinary execution evidence. Redundant branches and returns after unconditional transfers are likewise retained as residual encodings; they are not new reachable paths. The manifest records each rationale. [Byte-matched anchors](../../condensed/validation/ic15-residual-helpers-2026-10-16.json) preserve the first797 added bytes; the final generated inventory adds a further126 code bytes and16 referenced data bytes.

| Root | Static contract | Qualification |
| --- | --- | --- |
| 2274 | Calls2278 to fill4826..4A25 with byteR48, then falls through2282 to fill4A26..4C25. Both use228A advancing store, end-pointer comparison and RET2292. | 1,024 total stores when entered2274; entering2278 alone fills only the first512 bytes. No invocation proved. |
| 245E | Calls249E, polls E40A&7, returns carry clear for phase0, returns RBB=9/carry set for phase3, otherwise repeats. | Phase0 counterpart to243C phase1 wait. 2480/248F poll for phase3/7 and return carry clear; no local timeout. |
| 25F8 | Saves flags, selects RF0=RF1=0, RF2=90, copies error byteRBB intoRF3 and calls38AB while preserving RW20/22/24/26/40. | Diagnostic display wrapper; visual meaning of90 remains qualified. |
| 280A | Validates type through22D2, selects bus through2302, sends copied record4C77/4C7E/4C85 for type00/80/other accepted type, sets RWBC=0C/24/2C, waits through243C, then transfers via2410/256B and finishes24AD. | Propagates carry failures. Stores RBC at4826 then sends data starting4827. No new physical SCSI acceptance. |
| 2871 | Uses copied command4C8C, phase helper243C, RWBC=8, stores RBC at4826, transfers starting4826, then24AD. | Distinct buffer start from280A is preserved. Command names not inferred solely from position. |
| 2F98 | Reads RF0/RF1/RF2 from three advancing bytes atRWE2, then emits exactlyRF4 text bytes using2D64; RF4=0 emits none. | Counted positioned text, distinct from NUL-terminated2F73. |
| 317C | Rejects x>=192 or y>=64. Equal-coordinate cases branch to pixel30B0 or axis helpers327A/32D6. General case orders both coordinate pairs separately, uses a four-bit shifted multiply/divide interpolation and calls30B0 once per major-axis step. | Endpoint pairing, rounding and original intended geometry must not be replaced with a conventional signed-slope line algorithm. No caller proved. |
| 3496 | Rejects out-of-range192x64 coordinates, orders y endpoints and calls32D6 for every inclusive row with retained x pair. | Static rectangle-row behavior; no invocation or physical pixels proved. |
| 35BC | Uses byte coordinates fromRW48 and byte dimensions fromRW4A; emits character codesC0..C7 through2D64, preserving local work registers. | Frame-like glyph sequence. Byte DJNZ loops execute256 times when initialized0; no positive-size precondition is proved. |
| 3AAE | If4D2F nonzero, writes4A toE816 and80 toE814. | Body follows immediate return3AAD; invocation unresolved. |
| 3C38 | Writes0 toF00A; masks read value with38; returns1/2/3 for28/10/00, otherwise0 inRDA. | Related to rooted panel-interface3C68; source identity unresolved. |
| 52D1 | Requires4CAA<=RW48<4D2A; aligns pointer down, computes EEPROM index `(RW48-4CAA)>>1`, calls53EC,53C5, stores returnedRW4A to aligned RAM word, then53F6. | Single-word EEPROM read counterpart to52FE write. Bound is64 words; no local read verification. Invocation unresolved. |
| 580A / 5BDB | Identical delay bodies:50 outer iterations,255 inner PUSH/POP pairs. | 12,750 pairs, not a calibrated time. Invocation unresolved. |

3088..309D independently bounds both hexadecimal-digit indices to0..15 by high/low nibble extraction fromRF3. Data0798:8907..8916 is therefore the16-byte ASCII table `0123456789ABCDEF`. Its followingFF remains unresolved.

## Ordinary native qualification

The main boot decision chain is also statically connected.4140 derives display/setup flags from the first inverted panel group, reads/validates EEPROM through5140, applies F002 bit5 only when both display4D2F and TV-system4CB5 are nonzero, initializes audio54A2, contrast5554, peripheral3C96, CRT3684 and LCD29BC, then draws startup resources4758/4875. Calls3AC5/3AAD return immediately; the adjacent residual bodies are bypassed. Panel group1 bit0 selects5574 setup and a return to4140. Group0 bit5 qualifies diagnostic/alternate paths through4917/4000/4028; physical button names remain unqualified.

Normal startup copies71 command bytes through219A, enables interrupts and retries4A00 while carry is set. Saved Boot Drive4CAF=0 selects4486,1 skips that initial boot attempt, values2..9 use44C0 unless the raw saved value equals4CAB; values>9 fall back4486. Preserve the actual comparison with4CAB, without silently translating the displayed drive number.4486 tests4DA3 twice before trying the storage scan44C8/4645. The main loop432B repeatedly probes panel shortcuts and calls433B.433B runs4DA3, selects media density through4E1A, validates the header4E4E, displays loading state, calls4FBF, and on success writes4CB3=8 through single-word EEPROM writer52FE before474F handoff. Failure branches use4906 messages and4451's media/input wait. These are static control contracts; the saved-device boot and diagnostic cases do not yet have ordinary execution qualification.

[Invalid-media evidence](../../condensed/validation/ic15-native-invalid-media-2026-10-16.json) uses a private all-zero1.44MB disk and fresh state. The observer records postinstruction4E5D storing4C61=FF,4E69 storingFE after the read succeeds, followed by the ROM error/input loop without handoff during30 emulated seconds. This qualifies signature rejection, not FDC transport retries. The first setup attempt exited before execution because required ROM-audit media was missing; staging an unchanged original separately from selected test media resolved that setup failure.

[Original-media DMA evidence](../../condensed/validation/ic15-native-loader-dma-2026-10-16.json) enables existing read-only FDC logging. It records a512-byte header read from disk0 into physicalRAM0FC826, then112 rows each of2400 hex bytes. Row indexi=0..111 has disk offset4800+i*2400 and RAM destinationi*2400. This covers exactlyRAM000000..0FBFFF and disk004800..1007FF, with no gaps or overlaps, followed by handoff4755 and OS PCs. Logging was initially disabled, producing no DMA rows; enabling MAME `-log` supplied the113 matched rows. This is model execution, not physical DMA timing/parity.

[Short-media evidence](../../condensed/validation/ic15-native-short-media-2026-10-16.json) deliberately truncates a private OS copy to720KB. Signature status reaches50, but five handoffs4755 interleave with reset initialization2095 during30 emulated seconds. It supplies no accepted retry-chain evidence. BUG-079 tracks the unexpected native behavior; original full-media boot remains the qualified baseline. No original firmware, guest state or emulator implementation was changed.

## Remaining completion gates

### Command records and SCSI transfer widths

[The71-byte copy](../../condensed/validation/ic15-scsi-records-and-transfer-2026-10-16.json) contains exactly nine variable-length records, each a length byte followed by a six- or ten-byte CDB.23EA copies the counted CDB to4C26 before programming the SPC transfer. The table below preserves opcode bytes without importing unsupported device semantics; command-name associations in the existing native controller are model interpretation.

| RAM record | File record | CDB length | Initial CDB bytes |
| --- | --- | --- | --- |
| 4C62 | 6312 | 6 | 00 00 00 00 00 00 |
| 4C69 | 6319 | 6 | 03 00 00 00 10 00 |
| 4C70 | 6320 | 6 | 12 00 00 00 24 00 |
| 4C77 | 6327 | 6 | 1A 00 3F 00 0C 00 |
| 4C7E | 632E | 6 | 1A 10 3F 00 24 00 |
| 4C85 | 6335 | 6 | 1A 00 3F 00 2C 00 |
| 4C8C | 633C | 10 | 25 00 00 00 00 00 00 00 00 00 |
| 4C97 | 6347 | 6 | 1B 00 00 00 01 00 |
| 4C9E | 634E | 10 | 28 00 00 00 00 00 00 00 00 00 |

26AE rejects type85 and otherwise patches4C9E record offsets3..6 fromRD9/RD8/RD7/RD6, and offsets8..9 fromRC5/RC4. These are most-significant-first32-bit block-address and16-bit block-count fields. It multiplies the count by512, sends the low24 bits asRBE/RBD/RBC toE418/E41A/E41C and enters261C DMA. The observed caller counts fit that24-bit width.2705 requests blocks0400 at LBA4 intoRAM0, then03E0 at LBA15AC intoRAM080000, totalingFC000 bytes.273A instead requests07E0 blocks at LBA4 intoRAM0, alsoFC000 bytes. These variants must not be collapsed into one disk layout.

261C writes onlyRWBC to the16-bit IC4 count0118, twice; it does not copyRBE there. It programs physical destination from4C4A/4C4C, preserves0115/flags around interrupt-enabled transfer, selects011D control47 or78 from phase bit0 and waits forRB3 bit0 followed byE408 bit4.2671 repeats the same high-nibbleB0 SSTS gate as25A3. A large request such as0400 blocks leavesRWBC=0 while the SPC count is080000; current native47 handling requires a nonzero16-bit count. This is an additional qualification dependency, not proof of physical zero-count semantics or an accepted large-transfer implementation.24AD then performs two REQ/ACK handshakes, stores status/message bytes4C4E/4C4F, waits for disconnect, and returnsRBB=0A/0B/0C for masked status02/08/other-nonzero or0D for a nonzero message; success clears F010 bit7 and returnsRBB=0/carry clear.

### EEPROM, menus and the native SCSI blocker

[Native configuration read](../../condensed/validation/ic15-native-eeprom-2026-10-16.json) observes exactly64 stores5344 to4CAA..4D28 and64 comparison reads538C. [Ordinary setup/save/reboot evidence](../../condensed/validation/ic15-native-setup-eeprom-2026-10-16.json) qualifies5350 without writing guest state: Mode enters setup, S1/Exit use normal input fields, the firmware saves64 words, verifies all64, restarts and rereads all64. A second native process rereads/verifies the identical saved words from private persisted EEPROM. The sole changed word is4CB0 from0000 toFD00, corresponding to signed contrast-3 at4CB1. Entry5574 selects field3 (contrast), not field0; the first short input attempt released Mode before startup sampling and provided no save evidence. Input repeat timing is not inferred from the aggregate contrast change.

[The extended-menu run](../../condensed/validation/ic15-native-tv-menu-2026-10-16.json) uses existing virtual board straps40, which select4D34=2. Ordinary Panel Down moves selection3→4; S2 changes4CB5 from0 to1; Exit saves and verifies it. Subsequent startup F002 writes changeDC→FC, exactly bit5. This qualifies the saved TV-system/gate-bit path, not physical NTSC/PAL pixel geometry or timing.

[SCSI boot selection](../../condensed/validation/ic15-native-scsi-boot-2026-10-16.json) uses copies of existing HD/CD images and ordinary setup inputs to select Boot Drive2. It reaches target0 selection and six-byte command transfer programming, then stalls in25A3..25BE. [Persisted-state polling](../../condensed/validation/ic15-native-scsi-poll-2026-10-16.json) observesE408=00 andE40C=81 about five million times each; the ROM requiresE40C&F0=B0. The model sets transfer-active30 bits only for internal data phases4/5, excluding command phase3. BUG-080 records this concrete qualification blocker. No firmware patch, invented event or forced status was used to bypass it. Fixing/validating the native SPC transfer contract is independent implementation work before SCSI end-to-end ROM acceptance can advance.

The short-media path now has a [density/DMA qualification](../../condensed/validation/ic15-native-short-density-2026-10-16.json). At4E2C, F002 readsDB (bit1 set), so4E2F setsRCF bit1. Loader4FBF first initializesRF2=A0, then4FD6 branches over4FD9..4FE3 when that bit is set.4FE7 compares the unchangedA0 marker and returns carry clear; caller4409 therefore takes442A and eventually handoff474F. The12-second trace has exactly two512-byte header DMAs, no payload DMA and two handoffs. This is a statically connected explanation for the earlier observed loop, not an eight-retry qualification or a physical-density claim. The existing driver synthesizes F002 bit1 from disk-image length below1.44MB; do not infer that its encoding or firmware behavior has physical acceptance.

[Audio-initialization evidence](../../condensed/validation/ic15-native-audio-init-2026-10-16.json) matches2,789 native word writes: three initial clears,128 groups of three slot-clear writes,400 groups of command low/high/index,400 groups of coefficient/zero/index and two control-word writes. Every table word matches the immutable ROM, every commit index is in the observed sequence and every write mask isFFFF. This qualifies loading/order/values under native execution, not the physical meaning of the programmed DSP words.

[The static frontier](../../condensed/validation/ic15-final-static-frontier-2026-10-16.json) has98 raw cross-region edges. Every edge except the deliberate external4755→C000 handoff has a context-qualified bank link. Retaining these raw edges preserves selector/callee uncertainty. There are no indirect branch edges in this declared ROM decode; that does not prove arbitrary invocation states or writable instruction mappings safe.

[Remaining intervals](../../condensed/validation/ic15-remaining-range-audit-2026-10-16.json) total6,667 bytes:6,488 in uniformFF intervals and179 in nonuniform intervals. The latter comprise four apparent self-check strings2918..29BB plus precedingFF, bytes6004..6005,6369,63CC..63D5 and6903. No decoded pointer candidate establishes these as active resources. The one remaining numeric operand match8359 is the exclusive-end comparison for a copy, not a consumed byte. Content appearance alone does not justify classifying these regions as padding or active resource data.

Full decoding remains open: establish residual invocation or noninvocation, exhaust mutable/computed addressing and interrupt contexts, explain all peripheral semantics at the appropriate confidence level, qualify retry/recovery and serial-monitor behavior, and obtain physical reset/mapping evidence where claimed. Assembler/rebuild/source-edit acceptance is a separate Milestone7 gate. This static audit and native success/signature-failure evidence do not satisfy those gates.
