# IC15 stack, monitor and flag-frame audit

The native ordinary-ROM stack is now reconciled through floppy handoff. The audit also found and fixed a CPU frame-layout defect, BUG-083. No original ROM/media bytes, guest vectors or original-firmware CPU state were forced to obtain these findings.

## Ordinary boot and setup

[Passthrough observations](../../condensed/validation/ic15-native-stack-audit-2026-10-16.json) classify external stack reads/writes using declared original-ROM post-instruction PCs. Fresh boot and Mode-held setup each reach a lowest observed address47D6,42 bytes below initialSP4800. Setup enters the normal menu; its sampled net stack bytes equal4800-SP. These are observed paths, not a universal worst-case bound.

[Interrupt reconciliation](../../condensed/validation/ic15-native-stack-after-cpu-2026-10-16.json) matches every one of171 initially unclassified stack writes to the CPU's real interrupt log, including returnPC andSP. All use level13/vector203A/target0120. Classified stack stores total2,620,856 bytes; IRQ return-word stores add342 bytes; classified stack reads total2,621,196 bytes. The difference is2 bytes, matchingSP47FE at handoff.

The remaining word is4338, exactly the return address afterSCALL4336. The successful loader jumps to474F/4755 instead of returning through that frame; the OS then establishes its own stack. This is a documented nonreturning handoff, not evidence of an accumulating stack leak. Program-space observers stop accounting at4755. They do not observe internal register-file stacks or physical CPU bus timing.

## Local static balance and monitor continuation

[Local stack accounting](../../condensed/validation/ic15-local-stack-balance-2026-10-16.json) examines222 declared roots/direct-call targets.212 have only zero-depth returns under the explicit assumed-call-return contract. Calls are treated as net zero locally; their frames, interrupts, nontermination and selector preservation remain separate. The ten other results are retained individually, including SP reassignment, externalC000 handoff and continuation entries that require an existing frame. This is not a212/222 completion metric.

Reset208A setsSP4800. The monitor path401C disables gate sources,4021 setsSP0100 and4025 jumps to01A0. The CPU model routes accesses below0100 into its internal register space. No native invocation of this monitor path is claimed.

01A0 builds a16-byte frame: PUSHF, a manually packedWSR/mask word, five register words and data010C. Commandsr/R andw/W call the existing monitor read/write services and return to the input loop; slash is echoed. Commandg/G branches to01F7, restores010C and the five words, clears pending interrupt bytes, usesPOPA for the final four bytes and jumps to474F. It restores the manually built frame and transfers control; it is not an ordinary RET. Treating continuation01F3 as an independent zero-frame function produces an expected negative-depth result and must not drive a code correction.

## Independently supported CPU repair

The [Intel80C196KB User's Guide270651-003](https://www.syndex.org/kernels/196/27065103.pdf), printed pages30/32, describes the extra mask/window pair, push/pop order and mask clearing. The original ROM bytes at01A0..01AA independently placeWSR inR3E andINT_MASK1 inR3F beforePUSH RW3E. ThusWSR occupies the extension word's low byte. PUSHA's detailed description clears the mask while retainingWSR.

The native model formerly packed/restored the opposite byte order and clearedWSR. Its old component test round-tripped that layout and used reservedWSR03. The revised isolated CPU fixture uses validWSR0E andmask45, expects450E and includes the ROM's actual11-byte manual frame-building sequence. Before repair, that manual frame restoredWSR45/mask0E; after repair, it restoresWSR0E/mask45. SP, PSW and stack guards are checked. Synthetic fixture code/state initialization is explicitly component testing, not original-monitor execution evidence.

[Before/after validation](../../condensed/validation/ic15-stack-cpu-validation-2026-10-16.json) preserves all identities, fixtures, results and build commands. The CPU dependency and executable build successfully.457 full-suite tests pass, the newly added CPU regression passes separately, and ordinary native boot, pointer, MIDI playback/release and clean shutdown pass. A fresh original-ROM boot after repair reproduces the stack/IRQ/handoff observations above. Legacy flat-profile stubs remain outside this native repair.

## Ghidra lifting limitation

The installed pypcode4.0.0 MCS96 language emits incorrectPUSHA semantics: its extension usesINT_MASK fromRAM08 instead ofINT_MASK1 fromRAM13, and it pushes that extension before the flags word. ItsPOPA constructor reads the extension first. BUG-084 records the exact installed source and emitted operations; no installed language/package or Gemini project was modified. This does not invalidate the independently checked instruction bytes, lengths, mnemonics or direct targets. It means those checks cannot certify lifted stack semantics or pseudocode.

Current classified-byte coverage remains OS6.08% (62,736/1,032,192; +0.00 points this run) and ROM79.65% (26,101/32,768; +0.00 points). Overall decoding completion: not yet quantifiable. IC4 DMA extent/vector/acknowledgment behavior, genuine transport retry, physical reset/dormant invocation and unresolved byte use remain open. Assembler/rebuild acceptance is separate.
