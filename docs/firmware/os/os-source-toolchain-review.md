# Independent OS source-project/toolchain review

**The byte-exact reconstruction succeeds. An editable instruction assembler has not yet been implemented.** This distinction preserves the useful export/reconstruction achievement without closing unsupported Milestone7 gates.

Two fresh exports from the independently reviewed126-region analysis are deterministic except for destination-specific README paths. A fresh rebuilt1,474,560-byte image matches every original byte and SHA2563827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd. The saved project has126 ASM files,304 preserved data blocks and673 layout entries. The count25,808 is annotated instruction writes including duplicates/aliases, not25,808 independently assembled unique instructions. The exporter console's data-block count subtracts126 routines from673 entries and is misleading; actual304 data entries were counted directly.

## Source and layout experiments

| Private-copy edit | Observed result |
| --- | --- |
| No change | Exact original image |
| PUSHA ->NOP, originalF4 comment retained | Exact original image; source edit ignored |
| F4 ->FD comment, PUSHA text retained | One changed byte at52D1; comment controls output |
| Invalid mnemonic, original comment retained | Accepted; exact original image |
| .orgCAD1 ->CB00 | Ignored; exact original image |
| Replace instruction with.file_offset52D1 and.byteFD | Directive ignored; resulting52D1 is00, notFD |
| Conflicting edit at01574E in first source alias | Later alias overwrites it; reports exact success |
| Byte annotation offset168010 outside disk extent | Writes1,474,561-byte output instead of rejecting |

`build_image` scans byte comments directly, ignores.include/.equ/.page/.org directives and does not encode instruction operands or labels. The standaloneparse_asm_file helper supports some.byte syntax, butbuild_image does not use it. Existing modification tests change both the mnemonic and comment, so they do not distinguish an assembler from a hex-comment writer.

The generated include also misidentifiesWSR14 asWDT and labels nativeFDC E000/E002 asLCD. Header symbols need native mapping verification before use by a real assembler. These do not affect the current comment-based rebuild because theinclude is ignored.

## Acceptance and evidence

Four existing source-project tests pass. Four additional strict expected-failure tests reproduce the missing acceptance conditions (BUG-088/089); **4passed +4xfailed is not8passed**. BUG-090 records the architectural include issue. [Independent evidence](../../condensed/validation/os-source-toolchain-independent-review-2026-10-16.json) retains hashes, exact probes, output sizes/differences, fresh-export evidence and limitations. Original firmware, Gemini's source project/exporter/builder and installed tools were preserved. No modified firmware was executed; removingPUSHA is not a qualified functional patch.

Required next steps: implement an explicit supported MCS-96 instruction encoder with symbol/equate/label resolution and range diagnostics; define canonical physical-byte ownership across aliases; enforce fixed image extent, complete nonconflicting coverage and declared segment sizes; reject unsupported directives/encodings. Then demonstrate a text-only source edit with expected bytes, independently decode those bytes and qualify a named safe behavior change under native execution. Both OS and boot-ROM toolchains remain required by Milestone7.

The no-change **byte reconstruction subcheck passes**. The assembler/editable-code/rebuild and modified-firmware acceptance gates remain open. Functional decoding scope staysROM46/60=76.67%,OS36/96=37.50%,combined82/156=52.56%; this toolchain review is separate. Classified bytes remainROM26,277/32,768=80.19%,OS77,680/1,032,192=7.53%,both+0.00 points. Overall semantic decoding completion remains not yet quantifiable.
