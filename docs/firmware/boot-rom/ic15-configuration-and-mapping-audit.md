# IC15 configuration, references and mapping audit

This continues the [boot-ROM residual audit](ic15-residual-helpers.md) against unchanged v1.11 input SHA256 `ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6`. Classified-byte coverage remains26,101/32,768 (79.65%). New behavior/reference evidence does not add classified bytes. Original OS and ROM, emulator implementation and user media remain unchanged.

## Root closure and complete input identity

[Independent HEX parsing and root reachability](../../condensed/validation/ic15-root-and-hex-audit-2026-10-16.json) verifies2,048 data records, one extended-linear-address record and one EOF record. Every record checksum is correct, all32,768 addresses occur exactly once, and every byte matches the BIN. The HEX hash is `509a4b6571212cd62500d406fc3919b26cf3756a29cb095757735e8675a4d420`. The unresolvedFF ranges are explicit dump contents, not missing records or conversion fill. This does not establish unused padding.

Starting only from reset2080 and initial vector targets0120/013E/02A0, the declared control-flow graph reaches4,720 instruction encodings/13,870 code bytes. Another452 encodings/1,190 bytes come from structural-only entries. All raw cross-region edges except external4755→C000 have conditional bank links. This graph uses assumed call-return edges and declared contexts; it does not prove physical vector delivery, immutable invocation, or that unreached bodies can never execute.

[The raw reference audit](../../condensed/validation/ic15-reference-and-selector-audit-2026-10-16.json) scans both alignments and byte orders of every16-bit word in the entire ROM, using retained data mappings0108=0780 and010C=0798. It finds147 numeric matches into the nonuniform gaps:85 little-endian matches (75 in code, eight in glyph data and two in bitmap data), and62 big-endian matches (53 in code, eight in glyph data and one in bitmap data). No source is an otherwise unexplained pointer-table entry. Big-endian matching is an extra conservative check, not evidence of a big-endian pointer consumer. This is stronger than searching immediate operands, but not proof against computed addresses, alternate contexts or externally supplied pointers. The fourth ten-byte controller-label-shaped placeholder at63CC can be addressed mathematically as83AE+10*3; startup excludes controller index3, so it remains an unqualified dormant candidate and is not counted as an active resource.

## Fetch/data selector and indirect-store contracts

[The store audit](../../condensed/validation/ic15-indirect-store-contracts-2026-10-16.json) accounts for14 direct selector writes/restores and46 indirect ST/STB memory stores. Register/SFR stores are excluded from that46; implicit stack stores and hardware DMA remain separate. Three POP restorations at40BA/40D3/40D9 complement the11 ST/STB candidates in the older coverage inventory. They were not decoder failures: that inventory deliberately listed only ST/STB candidates.

The three representative ROM selectors each have four byte-identical aliases over a16KB window:

| Representative | Equivalent selectors within the declared ROM aperture |
| --- | --- |
| 0780 | 0780,07A0,07C0,07E0 |
| 0790 | 0790,07B0,07D0,07F0 |
| 0798 | 0798,07B8,07D8,07F8 |

These equivalences follow from the32KB mirror and are checked against every mapped byte. They reduce dependence on a particular representative value; they do not identify the physical power-on selectors or prove fetch and data defaults equal.

Diagnostic4028 tests63 pages with selector values0000,0010,..03E0, covering physical000000..0FBFFF and excluding03F0's work-RAM page. Each page gets5555,AAAA and its page number written and verified, then a second pass verifies page numbers across all pages. Successful completion entails1,548,288 word stores and2,064,384 word comparisons.40A4 saves data010C, fills8000..BFFF and restores it.40BF restores010C on both mismatch and successful word comparison before returning to progress rendering. Success and failure terminate in separate infinite loops40A2/4104. This is static behavior; the native diagnostic-gate input remains unavailable and no physical RAM test is claimed.

Indirect store bounds are explicit rather than globally inferred.23F6 copies at most256 bytes to4C26..4D25 from its byte-sized length, with initial records using six or ten bytes.27DE's arbitrary byte index bounds the destination to4C52..4D51; valid target0..7 restricts it to4C52..4C59. That broad bound avoids selector registers but can overwrite configuration if the caller supplies an invalid index.3032 writes exactly four format bytes4F36..4F39; negative-number sign insertion2FFF stops at a leading space within4F36..4F38 because the negated magnitude is1..127.34ED reads exactly32 LCD bytes into4F3E..4F5D.

Generic PIO read25D4 has no universal selector-preservation guarantee for arbitrary16-bit buffer/count states. The audit accounts for all six declared256B transfer sites: counted CDB at4C26,16-byte sense data,36-byte inquiry,12/36/44-byte mode data, eight-byte capacity data and a512-byte header. The sole declared28C5 caller4600 setsRWC4=1 and4C46=4826, bounding that header read to4826..4A25. Initial command-record lengths remain separate from their fixed CDB field patches. These bounds are conditional call contracts; the unbounded FDC FIFO loop and arbitrary monitor memory commands remain explicit qualifications.

The SCSI header comparison4605..462A requires the same15 signature bytes as floppy boot, followed by40 rather than floppy50. The existing HD00_512.img fixture starts directly with `S770 MR25A` and fails the four-leading-zero header contract. Thus repairing BUG-080 alone would not establish successful SCSI OS boot with that fixture. No post-blocker native rejection is claimed; a supported bootable SCSI image or a separately validated image-construction contract is still needed.

## Configuration validation versus menu validity

5140 reads/verifies64 EEPROM words and initially applies contrast output `(2*4CB1+80hex) mod256`. It checks format byte4CAA=2 and all16 identity bytes4CBA..4CC9, invoking51E6 defaults on either failure. Defaults clear4CAA..4D29, set format2, self-ID7, contrast0/IOS2=80, boot drive0 and4CB4=1, copy the16-byte identity and save all64 words.

| Field | Startup contract | Menu contract for valid starting states |
| --- | --- | --- |
| 4CAB self SCSI ID | No general startup clamp established; bus-selection helper separately rejects IDs>=8. |0..7. |
| 4CAE display-presence state | Absent display forces0; present display changes0 to1 but preserves other nonzero values. | No direct field editor identified. |
| 4CAF Boot Drive | Main boot selection falls back for values>9; valid2..9 display IDs0..7. |0..9. |
| 4CB1 signed contrast | Applied before identity/default handling; no general startup-50..50 clamp. |Signed-50..50. |
| 4CB2 controller | Unsigned values>2 reset to0; absent display forces0. |0..2, stores gated by display presence. |
| 4CB3 last boot source | Successful floppy stores8; successful SCSI stores target&7. | No direct field editor identified. |
| 4CB4 | Defaults store1; bulk persistence preserves it. | No additional ROM-specific meaning established. |
| 4CB5 TV system | No general startup0..1 clamp; any nonzero value sets the TV gate bit when display is present. |0..1 in extended setup. |

Other bytes in the128-byte configuration block are preserved/read/written by the bulk EEPROM services. This does not establish unused/reserved status or recover their OS-specific interpretation. The16 identity bytes have an independently bounded comparison/copy contract.

TV label5AB6 multiplies the raw byte4CB5 by5 and adds9303. Valid0/1 values select the two known labels. Values2..255 would start in the unclassifiedFF tail and can continue through the ROM mirror into low code bytes until a NUL. That static consequence is not an ordinary invocation claim, a reason to count erased/code bytes as intended text resources, or evidence that malformed persisted values are normalized.

## Ordinary native menu bounds and encoder-profile correction

With the existing Value encoder model enabled, all five visible field limits now have ordinary input evidence:

| Field | Observed range | Repeated minimum / maximum stores | Evidence |
| --- | --- | --- | --- |
| Self SCSI ID |0..7 |33 /33 |[Three-field bounds](../../condensed/validation/ic15-native-menu-bounds-2026-10-16.json) |
| Boot Drive |0..9 |33 /33 |Same run |
| Controller |0..2 |33 /33 |Same run, display present |
| LCD contrast |Signed-50..50 |32 /33 |[Contrast bounds](../../condensed/validation/ic15-native-contrast-bounds-encoder-2026-10-16.json) |
| TV system |0..1 |28 /28 |[Extended bounds](../../condensed/validation/ic15-native-tv-bounds-2026-10-16.json) |

The tests use Mode, Panel Up/Down and S1/S2 input fields, fresh private NVRAM and immutable media copies. Each endpoint remains held for120 further emulated frames; repeated firmware stores demonstrate clamping. All observed values remain inside their ranges. No arbitrary corrupt RAM states, physical repeat rates, LCD contrast response or television timing are qualified.

[A matched encoder baseline](../../condensed/validation/ic15-native-encoder-baseline-2026-10-16.json) explains the earlier unsolicited contrast decrement. With only Mode held and the encoder model disabled, F012 returnsDC from the backend's aliased m_mmio[2], firmware clears it and writes contrastFF. Enabling the existing S760_NATIVE_VALUE_ENCODER profile produces idle0 and no edit. The normal runtime already enables that profile. BUG-081 records the disabled-profile artifact; the ROM's logical-code4 interpretation is explained by bits3/2 ofDC. Earlier setup/save evidence still establishes the observed words and persistence, but the entire contrast change must not be attributed to deliberate S1 input.

## Tools available online

[Independent MAME decoding](../../condensed/validation/ic15-independent-mame-decoder-2026-10-16.json) checks all5,172 declared instruction encodings against the unchanged MAME i8x9x/mcs96 disassembler source compiled as a private standalone utility. All lengths and mnemonics agree with SLEIGH; all1,365 direct call/branch targets agree after16-bit normalization. Original utility interfaces and formatting code are retained, with a minimal host header instead of the emulator header. No emulator binary or firmware was changed. This does not qualify all operand semantics, execution reachability or physical behavior; the generated table and source hashes, harness and build command are preserved in the evidence.

The official [Ghidra MCS-96 language](https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/Processors/MCS96/data/languages/MCS96.ldefs) supports the CPU family; our current pypcode decoder already uses it. A full Ghidra project would add interactive references, function analysis and decompiler views. [IDA documents80196 support](https://docs.hex-rays.com/9.1/user-guide/disassembler/disassembly-gallery/80196-processor), making it a possible independent decoder check. [MAME's debugger](https://docs.mamedev.org/debugger/index.html) supplies tracing and watchpoints for real execution under the model.

A flat ROM import is insufficient for trustworthy decompilation: fetch4000..7FFF is ROM while the same logical data addresses use work RAM through data010A=03F0; data8000..BFFF uses the0798 mirror, including its wrap. A useful loader/project must preserve those separate mappings and conditional call contexts. No full Ghidra installation or IDA executable was found on PATH in this run; no software was downloaded or installed. These tools do not themselves establish physical reset defaults or repair BUG-080.
