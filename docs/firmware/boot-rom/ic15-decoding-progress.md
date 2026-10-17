# IC15 boot-ROM decoding progress

Latest: **boot-ROM functional-scope acceptance46/60 =76.67%**, under [versioned criteria](ic15-completion-matrix.md). Byte classification:ROM26,277/32,768=80.19%;OS77,680/1,032,192=7.53%. Counts in earlier sections are historical; combined overall completion remains unquantified.

Current input is the immutable32,768-byte Roland S-760 v1.11 ROM, SHA256 `ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6`. The IntelHEX file independently covers every BIN address exactly once; SHA256 `509a4b6571212cd62500d406fc3919b26cf3756a29cb095757735e8675a4d420`. The OS image remains SHA256 `3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd`.

This index was restored from durable reports/validation after a Windows text-encoding failure during publication. Earlier detailed history remains in [condensed boot-ROM documentation](../../condensed/02-ic15-boot-eprom-and-handoff.md); underlying manifests and evidence were unaffected.

## Scope and measured coverage

Boot-ROM classified-byte coverage is **79.65% (26,101/32,768 bytes)**:5,172 instruction encodings,15,060 distinct code bytes and11,041 identified data bytes. The immediately preceding reference-audit baseline is26,101, so the current change is+0.00 percentage points. OS classified-byte coverage is now **6.08% (62,736/1,032,192; +0.01 points)** after the caller-qualified Gemini pair below. Overall decoding completion: not yet quantifiable. Physical parity and assembler/rebuild acceptance remain separate gates.

There are6,667 unclassified ROM bytes:6,488 in all-FF intervals and179 in nonuniform intervals. Neither erased contents nor an absent reference proves padding. The nonuniform intervals include2917..29BC,6004..6006,6369,63CC..63D6 and6903. The four apparent diagnostic strings and fourth controller placeholder remain unqualified candidates.

Stable manifest: `scripts/firmware_manifests/ic15_exploration.json`. [Generated ROM inventory](../../condensed/validation/ic15-exploration-coverage-2026-10-16.json), [OS inventory](../../condensed/validation/os-exploration-coverage-2026-10-16.json), [reference-audit baseline](../../condensed/validation/decoding-completion-rom-reference-audit-2026-10-16.json). The previous residual-closure run added939 classified bytes (+2.87 points from25,162); that is historical, not this run's delta.

## Mapping, roots and remaining invocation uncertainty

ROM mapping is `((page<<10)+(cpu_address&0x3fff))&0x7fff` within physical1E0000..1FFFFF. It differs from the OS loaded-payload formula. Native representative selectors are0780 low,0790 fetch4000,03F0 work RAM and0798 resource8000. Fetch/data selectors are separate. Four equivalent mirror aliases for each ROM representative were independently checked byte-for-byte. Physical reset values remain unqualified.

Reset2080 and initial vectors0120/013E/02A0 reach4,720 declared encodings/13,870 code bytes in the static graph. Another452 encodings/1,190 bytes are structural-only. Conditional bank links close all raw external edges except intentional4755->C000 OS handoff; assumed call returns and runtime mapping preservation remain qualifications. [Root/HEX audit](../../condensed/validation/ic15-root-and-hex-audit-2026-10-16.json).

[Configuration and mapping audit](ic15-configuration-and-mapping-audit.md) accounts for14 direct selector writes/restores and46 indirect memory store sites. Generic PIO buffer/count, monitor writes, FDC FIFO destinations, implicit stack writes and hardware DMA retain their stated conditional bounds. All147 raw16-bit numeric matches into nonuniform unknowns originate in already-classified code/data; none establishes a new pointer table. Computed/external pointers and alternate contexts are not excluded.

[Independent MAME decoding](../../condensed/validation/ic15-independent-mame-decoder-2026-10-16.json) agrees with SLEIGH on all5,172 lengths/mnemonics and1,365 direct call/branch targets. Decoder agreement does not prove all operand semantics or execution reachability.

## Reset, resources, interrupts and monitor

Reset selects the4000 ROM window, copies71 command-template bytes6312..6358 toRAM4C62, initializes hardware and chooses boot paths. Initial vector words2000..2013/2030..203F reference013E,02A0 and0120. Native FDC0120->013F drains FIFO to4800, sets4820 and restores registers/flags. The serial monitor and other low-address roots are decoded but not executed by these observations.

Structural0124..013D entries retain invocation uncertainty.0131 branches02E0, which setsRB3 bit0; bit7 gates a preserved-RW20 F000 read/OR3/write/clear-bit1/write sequence and011D read. Initial CPU vectors do not establish delivery to0130. No vectors or events were injected. [Original decoding evidence](../../condensed/validation/ic15-decoding-2026-10-16.json).

Display resources have bounded consumers: ROM1000..1FFF supplies2,048 VDP words, font glyphs have bounded address arithmetic, counted text/geometry helpers have explicit widths, and the sixteen hexadecimal lookup bytes6907..6916 have nibble indices0..15. [Display evidence](../../condensed/validation/ic15-display-resource-2026-10-16.json), [bitmaps](../../condensed/validation/ic15-boot-bitmaps-2026-10-16.json), [native upload](../../condensed/validation/ic15-native-upload-2026-10-16.json). Full physical display timing remains open.

## Loader, failure and startup behavior

Ordinary native original-media boot performs one512-byte header transfer and112 contiguous9,216-byte payload DMAs, disk4800..1007FF toRAM0..FBFFF, then reaches4755 handoff. [DMA evidence](../../condensed/validation/ic15-native-loader-dma-2026-10-16.json), [handoff](../../condensed/validation/ic15-native-handoff-2026-10-16.json). All-zero1.44MB media fails the signature gate and stays in ROM for30 emulated seconds. [Failure evidence](../../condensed/validation/ic15-native-invalid-media-2026-10-16.json).

A private720KB truncation instead sets the density-derived RCF bit1 and bypasses payload loading before success/handoff, causing repeated reset: BUG-079. This is not successful retry qualification. [Short-density evidence](../../condensed/validation/ic15-native-short-density-2026-10-16.json). A genuine retry requires a represented transport error or physical evidence; raw content corruption tests only signature rejection.

Startup audio54A2..5549 has2,789 observed writes matching the original indexed400-pair/400-coefficient tables and two control words. [Audio evidence](../../condensed/validation/ic15-native-audio-init-2026-10-16.json). This is exact transaction evidence under the model, not recovered audio-chip semantics or physical timing.

## EEPROM, setup and residual helpers

[Residual helper report](ic15-residual-helpers.md) covers bounded fill, storage phase waits, command records, positioned counted text, geometry/frame helpers, EEPROM single-word read, delays and transfer stubs. The diagnostic4028 RAM test covers63 pages/FC000 bytes and restores data010C around comparisons/progress; native invocation is unqualified.

Ordinary setup input qualifies64-word EEPROM save/verify/reread and a fresh-process reboot. [Round trip](../../condensed/validation/ic15-native-setup-eeprom-2026-10-16.json). A matched baseline identifies a disabled-encoder profile artifact (BUG-081); normal runtime enables the existing encoder model. Earlier aggregate contrast changes must not all be attributed to deliberate S1 input. [Encoder baseline](../../condensed/validation/ic15-native-encoder-baseline-2026-10-16.json).

Both endpoints and repeated attempted edits qualify all five valid-state fields: ID0..7, BootDrive0..9, Controller0..2, signed contrast-50..50 and TV0..1. [Menu bounds](../../condensed/validation/ic15-native-menu-bounds-2026-10-16.json), [contrast bounds](../../condensed/validation/ic15-native-contrast-bounds-encoder-2026-10-16.json), [TV bounds](../../condensed/validation/ic15-native-tv-bounds-2026-10-16.json). These do not prove malformed persisted values normalized or physical encoder repeat timing. Startup validation/default/preservation differences are retained in the configuration report.

## SCSI and exact resume point

Nine counted CDB templates have explicit widths and big-endian patched LBA/count fields.2705 requests0400 blocks atLBA4 and03E0 atLBA15AC;273A requests07E0 blocks atLBA4. Both totalFC000 bytes but represent distinct layouts. [Static command/transfer evidence](../../condensed/validation/ic15-scsi-records-and-transfer-2026-10-16.json).

The original command-phase stall is recorded in [ordinary menu evidence](../../condensed/validation/ic15-native-scsi-boot-2026-10-16.json) and [persisted-state polling](../../condensed/validation/ic15-native-scsi-poll-2026-10-16.json): native SSTS81 versus requiredB0. The current independent component repair and new qualification are documented in [SCSI transport report](ic15-scsi-boot-transport.md). Payload DMA, physical reset/interrupt/dormant delivery and unresolved byte use remain material completion gates.

Current queue and exact next operation are in [OS decoding queue](../os/os-decoding-queue.md). Ghidra outputs must retain page/CPU/file identity and separate fetch/data mappings; source-level readability alone is not byte classification or physical parity. No full-ROM completion is claimed.


## Boot-ROM SCSI command transport repair (2026-10-16)

[SCSI transport report](ic15-scsi-boot-transport.md) supersedes the command-phase blocker: BUG-080 is fixed with independently supported active/busy status, command-byte counter consumption and transfer completion. Original-ROM ordinary setup input now sends CDBs and completes status/message handshakes. The new native regression observes nine active/completed transfers with zero SPC counters;452 tests and native runtime verification pass. Original HD header rejection is expected.

A private synthetic valid-header fixture passes that gate, then stalls at269D with IC4 count0000 and SPC count080000. BUG-082 tracks the independently unresolved full-count and DMA interrupt/vector contract. Service Notes page18 confirms IC25 INT→INT1 and DREQ/DACK channel0 wiring; it does not supply IC4 internal DMA semantics. No event, vector or guest state was forced.

Fresh classified-byte coverage remains ROM79.65% (26,101/32,768; +0.00 points) and OS6.07% (62,649/1,032,192; +0.00 points). Overall decoding completion: not yet quantifiable. [Metrics](../../condensed/validation/decoding-completion-rom-scsi-contract-2026-10-16.json) and [build/test/schematic evidence](../../condensed/validation/ic15-scsi-transport-validation-2026-10-16.json) preserve identities and failed/corrected validation attempts. Source/rebuild and physical parity remain separate.


## Gemini round4 independent review and qualified promotion (2026-10-16)

Gemini's frozen round4 output contains89,016 code bytes/27,844 encodings plus3,405 data bytes:92,421/1,032,192 candidate classified bytes (8.95%). Its23-25% executable-code estimate depends on an unqualified360,000-400,000-code-byte denominator and is not overall project completion. [Independent review](../../condensed/validation/os-round4-independent-review-2026-10-16.json) verifies original bytes, page/CPU/file mapping, no instruction-boundary or code/data conflicts, zero warnings, all27,844 independent MAME length/mnemonic comparisons and7,282 direct targets. These are static checks, not all candidate entry provenance, callee selector preservation, semantic understanding or runtime invocation. The142 additional regions add no conditional bank links in that snapshot.

Two caller-qualified roots001F:4F28/4F5E are now promoted with explicit bank links and87 code bytes.166:8B9D/8BA1/8BA6 and166:8D87/8D8B/8D90 each form an uninterrupted LDpage/ST0102/LCALL chain. The routines saveR9D in1BA7, conditionally invoke known controller reset4F7F withR9D=0, later restore the saved value through that reset helper unlessFF, and invalidate the saved byte.4F28 saves/restores data010C around0299:8F9C; CE14 saves/restores fetch0102. Callee-return and interrupt/state qualifications remain explicit. [Promotion evidence](../../condensed/validation/os-controller-session-pair-2026-10-16.json).

Maintained classified-byte coverage is now **OS6.08% (62,736/1,032,192; +0.01 percentage points)** and **boot ROM79.65% (26,101/32,768; +0.00 points)**. Overall decoding completion: not yet quantifiable. [Metrics](../../condensed/validation/decoding-completion-ghidra-review-2026-10-16.json). The broader8.95% candidate total remains separate until its additional root/context claims are individually qualified.

[IC15 Ghidra export instructions](../../../scripts/ghidra/ic15-readme.md) provide three immutable contextual views, entry CSV and full manifest evidence. Five focused exporter tests pass. These are separate inspection programs, not a complete bank-aware decompiler loader or a claim that a Ghidra project has been run. Gemini's existing setup files were preserved.


## Boot-ROM stack/monitor and CPU frame closure (2026-10-16)

[Stack/monitor report](ic15-stack-and-monitor.md) reconciles ordinary native ROM boot: observed low stack47D6;171 extra word writes exactly match real FDC interrupt return/SP logs; total writes minus reads leaves2 bytes at handoffSP47FE. The retained word4338 is the return afterSCALL4336, documenting the nonreturning loader frame. Setup sampled stack deltas also agree; these are observed cases, not universal worst-case bounds.212/222 local static roots balance only under explicit assumed-call-return rules; reset/handoff/continuation cases are retained, not treated as faulty functions.

The monitor's manual16-byte frame andg/G cleanup exposed BUG-083: reversedWSR/mask packing and unintendedWSR clearing in the native CPU. Intel documentation and original bytes support the repair. Valid-window isolated CPU tests fail before and pass after, including the original manual frame.457 full regressions and the new CPU pytest pass; native runtime boot/playback/release/shutdown passes. Installed Ghidra SLEIGH PUSHA lifting has a separate wrong-register/order issue (BUG-084); byte-disassembly checks do not certify p-code/decompiler semantics. No installed package or Gemini project was changed.

Fresh classified-byte coverage: **OS6.08% (62,736/1,032,192; +0.00 points)** and **boot ROM79.65% (26,101/32,768; +0.00 points)**. Overall decoding completion: not yet quantifiable. [Metrics](../../condensed/validation/decoding-completion-rom-stack-2026-10-16.json) and [exact before/after evidence](../../condensed/validation/ic15-stack-cpu-validation-2026-10-16.json). Physical IC4 DMA/vector behavior, native monitor invocation and unresolved byte use remain open.


## User-directed unused-space assumption (2026-10-16)

For continued boot-ROM work, treat the 6,488 bytes in wholly FF unclassified intervals as **presumed unused space unless contrary evidence appears**, as explicitly directed by the user. This is an operational assumption, not a remaining prerequisite for boot-ROM decoding completion. The 179 other bytes remain unresolved. Reopen a presumed-unused interval if credible code/data references, copy or checksum requirements, or runtime evidence establish use. Preserve the original FF bytes in exports and rebuilds.

This accounts for **32,589/32,768 bytes (99.45%) including the assumption**; it does not measure semantic completion. Strict evidence-backed classified-byte coverage remains **26,101/32,768 (79.65%; +0.00 percentage points)**. OS classified coverage remains **62,736/1,032,192 (6.08%; +0.00 points)**. Overall decoding completion: not yet quantifiable; remaining behavioral questions include IC4 SCSI DMA/interrupt handling and dormant monitor invocation. [Assumption inventory](../../condensed/validation/ic15-presumed-unused-space-2026-10-16.json) records the hash-checked intervals and reopening rule.


## Residual text classification (2026-10-16)

Structural classification adds176 data bytes: four NUL-terminated self-check messages at file2918..29BB, nine-question-mark placeholder63CC..63D5, the -128 terminator6004 and leading Controller-label space6369. These are recognizable resource contents; no caller or diagnostic invocation is claimed. Regenerated analysis has zero decoder warnings.

Strict ROM classified-byte coverage is now **26,277/32,768 = 80.19% (+0.54 percentage points)**. Of the remaining6,491 bytes,6,490 are FF and presumed unused under the user's direction (including the newly separated2917/6005); the sole other byte is **file6903 = 08**, adjacent to the FDC SPECIFY template. Including presumed unused space accounts for **32,767/32,768 bytes = 99.997%**; rounded100.00% would conceal the remaining byte and is deliberately avoided. This is byte accounting, not behavioral completion. OS remains62,736/1,032,192 =6.08% (+0.00 points). Overall decoding completion: not yet quantifiable. [Exact inventory and qualifications](../../condensed/validation/ic15-residual-text-classification-2026-10-16.json).

Next operation: investigate file6903's possible template-prefix role without assigning meaning from adjacency alone, then qualify remaining diagnostic invocation and IC4 transport contracts. Original ROM remains unchanged.


The final08 byte is **not consumed by the established FDC SPECIFY loop**:4B09 starts8904,4B1A sets count3 and4B1D/4B32 read only8904..8906 (file6904..6906,03 BF02). Adjacency does not identify6903's role. Native diagnostic entry is separately constrained:4285 requires panel group0 bit5, but current nativePANEL0 marks that bit unused (maskE0). The subsequent gates areR4A bit0 ->4917, otherwiseR4B bit0 ->4000, otherwiseR4A bit1 ->4028. No physical service-button identity, synthetic input, guest-state mutation or invocation is claimed. Remaining boot-ROM paths need a justified reference/alternate-ROM comparison for6903, supported service-input mapping, or independent IC4 DMA/interrupt evidence; existing static reference searches and ordinary modeled-input paths do not resolve them.


Final-byte investigation: [file6903 assessment](ic15-final-residual-byte.md) identifies a plausible unused FDC Sense Interrupt Status08 constant next to SPECIFY. The active routine0197/019A uses immediate08, qualified during ordinary boot; read-only boot/setup probes never read resource8903. Both adjacent consumers exclude it. This supports a leftover constant hypothesis, not original-author intent or all dormant contexts. Preserve the byte; semantic status remains provisional. Coverage unchanged: ROM26,277/32,768=80.19% (+0.00 points this run), OS62,736/1,032,192=6.08% (+0.00); overall not yet quantifiable. Next decisive evidence would be an alternate original ROM/symbol listing or justified dormant consumer; repeated baseline probes cannot prove historical intent.


## Read-event watchpoint with history (2026-10-16)

A reusable observer in `scripts/trace_ic15_residual_byte.py` records exact read events, CURPC/post-PC, CPU state, all bank selectors and32 recent instruction addresses. A known-used neighboring FDC template is the positive control. Seven30-second native cases pass with **zero reads of file6903**: successful floppy boot, Mode setup, invalid floppy signature, short floppy (only through first handoff), absent SCSI target with floppy fallback, bad SCSI header with floppy fallback, and valid SCSI header reaching the known269D DMA stall. No unsupported diagnostic input or guest mutation was used.

The debugger's raw disassembly uses the wrong banked data view (BUG-085); all32 positive-control history addresses were matched to original-ROM encodings under the observed0790 fetch context. [Full observer source, events, identities and history](../../condensed/validation/ic15-residual-byte-history-2026-10-16.json). This demonstrates the event logger works and bounds the negative finding to exercised paths; it does not prove no possible caller exists. No target-read event occurred from which to infer a use. Classified coverage unchanged:ROM26,277/32,768=80.19% (+0.00 points),OS62,736/1,032,192=6.08% (+0.00); overall not yet quantifiable.


## Quantified boot-ROM functional scope (2026-10-16)

[Boot-ROM completion matrix](ic15-completion-matrix.md) establishes rubric `ic15-native-decoding-v1`:15 named paths, four equal binary gates each (entry/context, layout, behavior, native execution). Initial acceptance is **46/60 =76.67%**:context11/15,layout15/15,behavior12/15,execution8/15. This is completion against the published scope, not a percentage of effort, full hardware fidelity or OS-plus-ROM completion. No partial credit; failed/blocked paths remain in the denominator. Scope changes require a versioned amendment and a comparable old/new denominator.

Unfinished gates cover genuine floppy recovery, SCSI DMA delivery/completion, original diagnostic/monitor invocation, auxiliary interrupt routing, structural-only helpers and unreferenced resource ownership. The user-accepted6,490FF bytes do not block this scope; the final08 byte remains provisional. Physical parity and Milestone7 source/rebuild acceptance are separate unscored requirements. All gate criteria and citations are in the machine-readable scope; a generator verifies evidence-file existence/JSON, input identity, byte accounting and arithmetic rather than pretending to re-prove semantics automatically. Three guard tests pass; deterministic --check passes.

Byte coverage unchanged this scoring pass:ROM26,277/32,768=80.19% (+0.00 points),OS77,680/1,032,192=7.53% (+0.00 points). Combined overall decoding completion remains not yet quantifiable until an OS subsystem scope is published. Reproduce with `python scripts/report_ic15_completion.py --check`. Next evidence work should target one named open gate and update it only against its criterion; retain this initial score as baseline.


## OS and combined functional-scope acceptance (2026-10-16)

[Published firmware matrix](../firmware-completion-matrix.md) addsOS rubric `s760-os-decoding-v1`:24 contracts/families and96 binary gates. InitialOS acceptance is **36/96 =37.50%**. Combined with ROM46/60, the explicit gate checklist is **82/156 =52.56%**; this sums gates rather than averaging percentages. It is not a source-understanding, effort-remaining or physical-fidelity estimate.

Unmapped scheduler/interrupt-wide behavior, voice lifecycle, filesystem/persistence, synthesis, remaining screens/inputs, object hierarchy and sampling/editing remain open. The remaining-payload family explicitly covers all unclassified bytes, overlays and unassigned functions; it cannot receive completion credit while unexplained bytes remain. Historical81/33-row catalogues were not used as verified addresses/status. Every scope row has criteria and evidence, with conditional contexts preserved. OS-side execution is credited only to the narrow original-ROM-to-running-OS handoff; unrelated native tests and ROM EEPROM tests do not count as OS routine execution.

Six scope/arithmetic guard tests pass. Both generators' deterministic --check passes. Scope changes require a versioned denominator amendment; initial scope/score snapshots are retained. Reproduce with `python scripts/report_firmware_completion.py --check`. Combined overall semantic decoding completion remains unquantifiable; **published functional-scope acceptance** is now measurable and reproducible. Physical parity and Milestone7 source/rebuild gates remain separate.

Byte coverage unchanged:OS77,680/1,032,192=7.53% (+0.00 points);ROM26,277/32,768=80.19% (+0.00). Next quantitative update must change a named gate against its acceptance criterion, not convert candidate-byte growth into semantic credit. Near-term targets include native parser/event-ring contracts and remaining callee preservation, alongside still-open boot-ROM SCSI/retry/diagnostic gates.
