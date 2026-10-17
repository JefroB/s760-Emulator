# OS decoding: scope and current evidence

Latest functional-scope baseline: **OS36/96=37.50%, ROM46/60=76.67%, combined82/156=52.56%** under the [published scopes](../firmware-completion-matrix.md). These count acceptance gates, not effort or byte coverage.

Latest independently accepted inventory: **OS77,680/1,032,192 bytes (7.53%; +1.45 points),126 regions**. ROM26,277/32,768 (80.19%; unchanged). See the reconciled-frontier section below; earlier counts are historical checkpoints. Overall decoding completion: not yet quantifiable.

The objective is systematic OS decoding, independently of whether each discovery helps the filter. The filter-focused manifest remains a focused fixture. `scripts/firmware_manifests/os_exploration.json` is the broader, independently maintained exploration manifest; it includes a snapshot of the earlier regions plus startup, interrupts and resident services. Changes to one manifest do not automatically propagate to the other.

## Reproduce the exploration

```powershell
python scripts/analyze_firmware_routines.py S760224.IMG scripts/firmware_manifests/os_exploration.json --output temp/os-exploration
python scripts/firmware_coverage.py temp/os-exploration/analysis.json --output temp/os-exploration/coverage.json
```

The original input is read-only and hash checked. Generated assembly stays local. The [coverage inventory](../../condensed/validation/os-exploration-coverage-2026-10-16.json) records distinct file-byte coverage, remaining unclassified intervals, unresolved edges and selector-write review candidates. It counts aliases once. Decoding coverage is not semantic understanding, and unclassified bytes may be code, data or padding.

## Broadening beyond the filter

| Area | Evidence and new coverage |
| --- | --- |
| OS handoff/startup | Page 0:C000 initializes separate fetch/data selectors and stack. Recursive exploration includes startup and directly reachable same-window services. |
| Interrupts | Page 0:CD5D is independently identified by existing native FDC evidence. Stop at CDD4, which writes the current window's fetch selector 0106; subsequent instructions need a new mapping. |
| Resident MIDI parsing | Page 000F:213A consumes a byte ring whose read pointer wraps from 1B6C to 196C. Status parsing separates channel and message class and handles F0/F7/FE comparisons. Nine annotated dispatch stubs at 21DE + 4*index expose further message handlers. |
| Pitch control | Page 001F:480C follows additional parameter/mapping paths and ends in hardware writes at 4B0D/4B14. Exact musical semantics require further annotation. |
| Voice housekeeping | Page 001F:4B1B and 4C86 are direct service-call targets; provisional functional grouping, not complete semantic recovery. |
| Other modulation services | Page 002D:87DB decodes additional bounded service code. The dispatcher at 84C7 remains deliberately unresolved pending index evidence. |

The resident 000F mapping is established by startup C00A/C00E. Applying it to other invocations requires the selector to remain unchanged. The MIDI dispatch annotation uses the observed instruction pattern that extracts status-class bits or selects special index 8; an unknown-value edge remains because other writers and invocation states have not been exhaustively proved.

## Current result and limits

This inventory decodes 18,488 distinct instruction encodings spanning 59,244 unique bytes of the loaded OS payload, with 3,405 separately classified data bytes. There are no decoder warnings. It leaves 761 unresolved raw edge records and 969,543 payload bytes unclassified. These figures describe this tool's present inventory, not a percentage of OS understanding. Forty-seven targeted tests pass, including mirrored ROM mapping, alias counting and automatic stopping at direct current-window fetch-selector writes.

The current analyzer uses declared mapping windows. It does not automatically propagate selector writes, prove callee preservation, identify all code/data boundaries, or recover source types. A successful decode does not remove those qualifications. Explicitly stopping at CDD4 prevents one known stale-page continuation; other selector writes remain review candidates.

## Next decoding priorities

1. Explain the newly exposed resident message handlers and their data tables, including outgoing banked calls.
2. Resolve startup/UI/storage call-site mappings from selector setup and existing native traces.
3. Add supported data annotations and inspect referenced tables without treating all gaps as executable instructions.
4. Expand the interrupt handlers across evidenced bank transitions.
5. Continue toward source projects and rebuild tools once instruction and layout contracts support them.

No original image, ROM, guest state or emulator behavior changes in this pass. Milestone 7's complete recursive analysis and decompiler gates remain open.

Resident MIDI follow-up: [status-class and controller dispatch](os-midi-decoding.md) now names the message-family paths and verifies 26 jump stubs across three tables. BUG-077 corrects signed displayed direct destinations; unknown destination banks remain explicit.

Controller/routing follow-up: [assigned controllers, parameter state and routing refresh](os-controller-and-routing-decoding.md) documents the 33-byte channel-list stride, controller amount destinations, registered-parameter flags, and 195 newly decoded instructions in B247/B299/B489. Two bounded tag tables are recorded from the original image; runtime values still need confirmation.

System-message follow-up: [header validation and transfer dispatch](os-system-message-decoding.md) adds 1,874 decoded instructions, checks 43 jump stubs and records the seven-entry lookup table. The original source language remains unknown; assembly-level decoding and calling-convention recovery do not depend on identifying it.

Transfer-field follow-up: [packed fields and length gates](os-transfer-fields.md) resolves F874/F8A6 under the timer context, distinguishes four-byte most-significant-first fields from three-byte least-significant-first fields, and checks the register arithmetic on 8,203 cases. This is algebra validation, not a hardware transfer test.

Addressing follow-up: [transfer address map, slot search and response builder](os-transfer-addressing.md) identifies nibble-addressed readback, a 21-record address table (126 separately classified data bytes), and six-byte response construction. Code/data inventory now rejects classification overlaps.

Lifecycle follow-up: [allocation, packet ordering and retransmission](os-transfer-lifecycle.md) explains reservation before descriptor publication, receive conversion counts, send-tail zero padding and response transitions. It checks 596 existing instruction anchors against the image. A subsequent selector audit establishes entry 0166:87B5 and adds 298 instructions (988 bytes), including rollback 8B5F. Cross-window callee preservation remains unproved. Native transfer acceptance remains open; the coverage increase comes from the new supervisor region, not reinterpretation of old instructions.


Callee and initialization follow-up: [transfer lifecycle](os-transfer-lifecycle.md) corrects the initial staged-descriptor interpretation (BUG-078), resolves the final48-byte publication destination, and documents two bank-call wrappers. [Controller state](os-controller-and-routing-decoding.md) now includes a startup-qualified reset of all16 channels' selection flags. [EEPROM services](os-eeprom-services.md) describes the full64-word read/write/verify loops and serial pin operations. These add581 instructions/1644 bytes beyond the supervisor checkpoint.

`scripts/firmware_bank_frontier.py` reports adjacent, decoded LD/ST/CALL sequences with explicit fallthrough edges. It rejects data selectors, wrong-window calls, self-window remaps and out-of-payload destinations. Its output is a conditional candidate list, not automatic reachability or bank propagation. The current fixture suite has47 passing tests; no runtime source changed.

Boot-ROM work now has a separate [IC15 decoding inventory](../boot-rom/ic15-decoding-progress.md):4,720 instruction encodings,13,870 code bytes and185 data bytes under the explicit mirrored-ROM contract. These figures are separate from the OS payload counts. Original reset defaults on physical hardware remain unqualified.


Storage follow-up: [SCSI session and object notifications](os-scsi-session-decoding.md) qualifies the CDED wrapper, session request fields and three manufacturer41 message formats with588 byte-checked instruction anchors. Native SCSI behavior and request producers remain open.


[SCSI transfer, deletion and reset templates](os-scsi-transfer-and-delete.md) now document command dispatch,48-byte descriptor staging,9216-byte waveform blocks, shared-reference marking and memory compaction. Seven bounded reset templates expand to32/256/128/256/128/128/48 bytes. Incoming MIDI request producers link to the session through1FA4/1FA5/1FA6; all new results remain static-only.


[Selection and stereo pairing](os-selection-refresh.md) qualifies the name-based partner search and copy-progress display hook. [Startup audio control](os-startup-audio-control.md) adds bounded command/routing tables and port-control sequences. Outgoing universal7E request03 now links through resident voice-stop helpers; static qualification remains distinct from native execution.


[Screen descriptor loading](os-screen-descriptor-loading.md) follows actual pointer/geometry consumers and one startup-qualified mutable descriptor. [Floppy initialization](os-fdc-startup.md) connects seek/recalibration waits to the resident ISR completion flag. Current classified byte coverage is4.05% of the OS payload and42.89% of the separate boot ROM; these are classification metrics, not semantic completion percentages.


[Resident UI event dispatch](os-ui-event-dispatch.md) connects000F:2080 producers to0000:F468 consumers, qualifies page0 CDC6 wrapper targets, and explains cached callback target/page ordering. Current generated inventory isos-resident-init-2026-10-16/closure; ROM display resource classification adds2,048 data bytes without new code. Current coverage counts supersede earlier snapshot percentages; neither target is fully decoded.


Latest field/menu continuation qualifies seven-byte OS field records and the initial empty field list, plus boot-ROM setup menu labels and signed LCD contrast updates. OS coverage is regenerated atos-resident-init-2026-10-16/fields; ROM coverage atrom-display-2026-10-16/setup. Historical percentages above are superseded by the generated byte inventory.


[Fixed screen selection and status rows](os-ui-selection-callbacks.md) qualifies initial011E/011F callbacks, submenu event production, numeric metadata loads and four transfer-error messages. Current OS analysis isos-pointer-producers-2026-10-16/final; boot-ROM analysis isos-pointer-producers-2026-10-16/rom-final. [Completion metrics](../../condensed/validation/decoding-completion-2026-10-16.json) preserve prior-run baselines and the conditional native-model resource qualification.


## Current completion percentages (2026-10-16)

| Target | Classified-byte coverage | Classified / total bytes | Change from prior run |
| --- | --- | --- | --- |
| OS loaded payload | 5.20% | 53,664 / 1,032,192 | +0.18 percentage points |
| IC15 boot ROM | 75.68% | 24,799 / 32,768 | +12.60 percentage points |

These are generated classified-byte metrics, not overall semantic completion. The ROM total includes4,096 upload bytes qualified conditionally against the native VDP device model; ordinary execution and physical counter behavior are unvalidated. Overall decoding completion: not yet quantifiable. Complete region/root inventory, mutable dispatch and native end-to-end acceptance remain open; assembler/rebuild gates are separate. Input hashes, exact denominators and previous-run baselines are in[completion validation](../../condensed/validation/decoding-completion-2026-10-16.json).


[Device probe and numeric fields](os-device-probe-and-numeric-fields.md) adds the eight-target startup scan, bounded identification signatures/commands, object template copies and six concrete type3 metadata contracts. Boot-ROM TV-system setup is statically qualified; the existing VDP upload now has4,096 byte-matched native write observations. Current analysisos-menu-init-2026-10-16/final androm; all original identities remain unchanged.


## Current run completion metrics

| Target | Classified-byte coverage | Classified /total bytes | Change |
| --- | --- | --- | --- |
| OS loaded payload | 5.99% | 61,813 /1,032,192 | +0.79 percentage points |
| Boot ROM | 75.75% | 24,821 /32,768 | +0.07 percentage points |

Overall decoding completion: not yet quantifiable. Full root/region inventory,mutableinvocationbounds andnativeend-to-end acceptance remainopen; rebuildgates areseparate. Prior-run baselines53,664 OS/24,799 ROMbytes andinputidentities arestoredin[completion evidence](../../condensed/validation/decoding-completion-device-probe-2026-10-16.json). The ROMupload's4,096 bytes nowhaveobservednativequalification, withoutphysicalparity.47 toolingtests passed.


[Postprocessing and all40 initial012F fields](os-postprocess-and-full-fields.md) now qualify bounded object propagation, type-dependent tuple widths, dynamic word limits and indexed byte editing. Four boot-ROM input-mode cases have native execution evidence. Current OS analysisos-postprocess-2026-10-16/final; ROM inventory unchanged.


Current classified-byte coverage: OS6.07% (62,649/1,032,192; +0.08 percentage points), ROM75.75% (24,821/32,768; +0.00 points). Overall decoding completion remains not yet quantifiable. Previous baselines, identities and exact denominators are in [completion evidence](../../condensed/validation/decoding-completion-postprocess-2026-10-16.json). Four native ROM mode cases add qualification without byte-count growth;47 tooling tests pass.


## Boot-ROM residual closure and native qualification (2026-10-16)

Current generated classified-byte coverage is **79.65% ROM (26,101/32,768; +2.87 percentage points)** and **6.07% OS (62,649/1,032,192; +0.00 points)**. ROM contains5,172 instruction encodings/15,060 code bytes and11,041 identified data bytes. There are6,667 unresolved bytes, including6,488 in uniformFF intervals and179 in nonuniform intervals. These are classification metrics, not overall completion. Overall decoding completion: not yet quantifiable. [Metrics and identities](../../condensed/validation/decoding-completion-rom-followup-2026-10-16.json) preserve the immediately preceding25,162-byte ROM baseline and regenerated OS denominator.

[Residual helper report](../boot-rom/ic15-residual-helpers.md) explains bounded fill, storage phase waits, command bodies, positioned counted text, geometry/frame helpers, single-word EEPROM read, delay loops and redundant transfer stubs. Invocation remains unresolved for structural-only roots. All instruction bytes match the original, zero decoder warnings,47 existing firmware tests pass. The16-byte hexadecimal table now has independently bounded nibble consumers.

Ordinary native evidence now qualifies original-media112*9216-byte payload transfer, invalid-signature rejection without handoff, and2,789 exact audio-initialization writes against original tables and indices. The short720KB-media experiment instead exposed repeated handoff/restart (BUG-079); it does not qualify retries. Original ROM/OS inputs remain unchanged. Physical timing and reset defaults remain open; assembler/rebuild gates are separate.

Boot-ROM continuation additionally qualifies64-word EEPROM persistence and the extended TV gate-bit update through ordinary menu inputs. Native SCSI command transfer is blocked at theB0 status wait by observed81 (BUG-080); no forced guest-state workaround was used. The [residual helper report](../boot-rom/ic15-residual-helpers.md) now includes all nine copied command records, twoFC000-byte SCSI loader variants, exact transfer widths and status/message failures. Current classified-byte metrics remain unchanged at ROM79.65%/OS6.07%; semantic/native qualifications do not increment byte coverage.


## Boot-ROM configuration, mapping and independent decoder audit (2026-10-16)

[Configuration and mapping report](../boot-rom/ic15-configuration-and-mapping-audit.md) closes the initial-image pointer-candidate audit under retained mappings, accounts for all14 direct selector writes/restores and46 indirect memory store sites, and separates EEPROM startup validation from valid-state menu limits. There are147 raw numeric matches into nonuniform unknowns; all originate in already classified code/data, with no newly justified pointer table. Reset/initial-vector reachability reaches4,720 encodings/13,870 code bytes;452 encodings/1,190 bytes remain structural-only under that root contract. IntelHEX independently matches every original BIN byte exactly once. This does not prove every erased byte unused or arbitrary runtime pointers bounded.

All five setup fields now have ordinary native input evidence at both limits with repeated attempted edits: ID0..7, BootDrive0..9, Controller0..2, signed contrast-50..50 and TV0..1. A matched Mode-only baseline isolates disabled encoder-profile aliasing (BUG-081); the normal runtime already enables the encoder model. Existing HD media does not match the ROM SCSI header shape, so transport repair alone would not demonstrate OS boot.

[Independent MAME disassembly](../../condensed/validation/ic15-independent-mame-decoder-2026-10-16.json) agrees with SLEIGH on all5,172 instruction lengths/mnemonics and1,365 direct targets. A private standalone host compiles unchanged decoder/utility sources; production emulator and firmware are unchanged. This qualifies decoding agreement, not all operand semantics or runtime invocation.

Freshly regenerated classified-byte coverage: boot ROM **79.65% (26,101/32,768; +0.00 percentage points)**; OS **6.07% (62,649/1,032,192; +0.00 points)**. [Metrics, baselines and identities](../../condensed/validation/decoding-completion-rom-reference-audit-2026-10-16.json). Overall decoding completion: not yet quantifiable. Remaining gates include SCSI transport, genuine retry execution, unresolved byte use and physical reset/interrupt/dormant-entry evidence; assembler/rebuild acceptance remains separate.


## Boot-ROM SCSI command transport repair (2026-10-16)

[SCSI transport report](../boot-rom/ic15-scsi-boot-transport.md) supersedes the command-phase blocker: BUG-080 is fixed with independently supported active/busy status, command-byte counter consumption and transfer completion. Original-ROM ordinary setup input now sends CDBs and completes status/message handshakes. The new native regression observes nine active/completed transfers with zero SPC counters;452 tests and native runtime verification pass. Original HD header rejection is expected.

A private synthetic valid-header fixture passes that gate, then stalls at269D with IC4 count0000 and SPC count080000. BUG-082 tracks the independently unresolved full-count and DMA interrupt/vector contract. Service Notes page18 confirms IC25 INT→INT1 and DREQ/DACK channel0 wiring; it does not supply IC4 internal DMA semantics. No event, vector or guest state was forced.

Fresh classified-byte coverage remains ROM79.65% (26,101/32,768; +0.00 points) and OS6.07% (62,649/1,032,192; +0.00 points). Overall decoding completion: not yet quantifiable. [Metrics](../../condensed/validation/decoding-completion-rom-scsi-contract-2026-10-16.json) and [build/test/schematic evidence](../../condensed/validation/ic15-scsi-transport-validation-2026-10-16.json) preserve identities and failed/corrected validation attempts. Source/rebuild and physical parity remain separate.


## Gemini round4 independent review and qualified promotion (2026-10-16)

Gemini's frozen round4 output contains89,016 code bytes/27,844 encodings plus3,405 data bytes:92,421/1,032,192 candidate classified bytes (8.95%). Its23-25% executable-code estimate depends on an unqualified360,000-400,000-code-byte denominator and is not overall project completion. [Independent review](../../condensed/validation/os-round4-independent-review-2026-10-16.json) verifies original bytes, page/CPU/file mapping, no instruction-boundary or code/data conflicts, zero warnings, all27,844 independent MAME length/mnemonic comparisons and7,282 direct targets. These are static checks, not all candidate entry provenance, callee selector preservation, semantic understanding or runtime invocation. The142 additional regions add no conditional bank links in that snapshot.

Two caller-qualified roots001F:4F28/4F5E are now promoted with explicit bank links and87 code bytes.166:8B9D/8BA1/8BA6 and166:8D87/8D8B/8D90 each form an uninterrupted LDpage/ST0102/LCALL chain. The routines saveR9D in1BA7, conditionally invoke known controller reset4F7F withR9D=0, later restore the saved value through that reset helper unlessFF, and invalidate the saved byte.4F28 saves/restores data010C around0299:8F9C; CE14 saves/restores fetch0102. Callee-return and interrupt/state qualifications remain explicit. [Promotion evidence](../../condensed/validation/os-controller-session-pair-2026-10-16.json).

Maintained classified-byte coverage is now **OS6.08% (62,736/1,032,192; +0.01 percentage points)** and **boot ROM79.65% (26,101/32,768; +0.00 points)**. Overall decoding completion: not yet quantifiable. [Metrics](../../condensed/validation/decoding-completion-ghidra-review-2026-10-16.json). The broader8.95% candidate total remains separate until its additional root/context claims are individually qualified.

[IC15 Ghidra export instructions](../../../scripts/ghidra/ic15-readme.md) provide three immutable contextual views, entry CSV and full manifest evidence. Five focused exporter tests pass. These are separate inspection programs, not a complete bank-aware decompiler loader or a claim that a Ghidra project has been run. Gemini's existing setup files were preserved.


## Boot-ROM stack/monitor and CPU frame closure (2026-10-16)

[Stack/monitor report](../boot-rom/ic15-stack-and-monitor.md) reconciles ordinary native ROM boot: observed low stack47D6;171 extra word writes exactly match real FDC interrupt return/SP logs; total writes minus reads leaves2 bytes at handoffSP47FE. The retained word4338 is the return afterSCALL4336, documenting the nonreturning loader frame. Setup sampled stack deltas also agree; these are observed cases, not universal worst-case bounds.212/222 local static roots balance only under explicit assumed-call-return rules; reset/handoff/continuation cases are retained, not treated as faulty functions.

The monitor's manual16-byte frame andg/G cleanup exposed BUG-083: reversedWSR/mask packing and unintendedWSR clearing in the native CPU. Intel documentation and original bytes support the repair. Valid-window isolated CPU tests fail before and pass after, including the original manual frame.457 full regressions and the new CPU pytest pass; native runtime boot/playback/release/shutdown passes. Installed Ghidra SLEIGH PUSHA lifting has a separate wrong-register/order issue (BUG-084); byte-disassembly checks do not certify p-code/decompiler semantics. No installed package or Gemini project was changed.

Fresh classified-byte coverage: **OS6.08% (62,736/1,032,192; +0.00 points)** and **boot ROM79.65% (26,101/32,768; +0.00 points)**. Overall decoding completion: not yet quantifiable. [Metrics](../../condensed/validation/decoding-completion-rom-stack-2026-10-16.json) and [exact before/after evidence](../../condensed/validation/ic15-stack-cpu-validation-2026-10-16.json). Physical IC4 DMA/vector behavior, native monitor invocation and unresolved byte use remain open.


Gemini batchL independent review (2026-10-16): [review and acceptance limits](os-gemini-batch-l-review.md). Raw candidate coverage36.88%; zero original-byte/mapping or direct-target disagreements, but1,360 boundary-conflict pairs and25,858 length/mnemonic mismatches. Intel-supportedSKIP/IDLPD decoder defects account for25,837;21 need variant/support review. Triage flags1,504 regions;5,653 pass those checks only. BUG-086/087 logged. MaintainedOS62,736/1,032,192=6.08% (+0.00 points),ROM26,277/32,768=80.19% (+0.00); overall not yet quantifiable. Next operation: controlled KB decoder correction and regeneration, then reference-qualified/global-conflict-filtered candidate promotion. No Gemini-owned files or installed libraries changed.


## Independently accepted reconciled frontier (2026-10-16)

Gemini's65 ->119 ->126 region progression is independently reproduced:92 call sites/54 new destinations, then9 sites/7 destinations, then0 new destinations. All23,134 instruction locations and6,089 direct targets agree with the independent MAME decoder; original bytes/mapping match, warnings and global boundary conflicts are zero. The maintained manifest now includes61 new conditional roots plus101 explicit contextual links recording the original adjacent LD/ST/CALL evidence. Existing links and unknown control edges remain.57 focused tests pass; initial3 sandbox temp-directory errors disappear with workspace --basetemp.

Current OS classified-byte coverage: **77,680/1,032,192 =7.53% (+1.45 percentage points)**, including74,275 code bytes and3,405 data bytes. Boot ROM: **26,277/32,768 =80.19% (+0.00 points)**. Overall decoding completion: not yet quantifiable. [Promotion/evidence](../../condensed/validation/os-reconciled-frontier-promotion-2026-10-16.json), [independent checks](../../condensed/validation/os-reconciled-independent-review-2026-10-16.json), [metrics/baseline](../../condensed/validation/decoding-completion-reconciled-frontier-2026-10-16.json).

Convergence applies only to the strict adjacent-selector/direct-call frontier, not all OS control flow. Callee preservation/return context, interrupt clobbers, indirect/trampoline/nonadjacent setup and physical invocation remain separate gates. The discovery script does not itself enforce global code ownership or explicitly reject warning lists; those checks were supplied independently and pass for this final result. The installed SLEIGH length defect remains upstream; the analyzer's documented workaround is independently checked for this inventory. Candidate batchL's broader36.88% is not promoted wholesale. Next work: annotate new callee selector effects and return contexts, then expand justified nonadjacent/trampoline/indirect paths rather than rescan arbitraryRET bytes.


## Quantified boot-ROM functional scope (2026-10-16)

[Boot-ROM completion matrix](../boot-rom/ic15-completion-matrix.md) establishes rubric `ic15-native-decoding-v1`:15 named paths, four equal binary gates each (entry/context, layout, behavior, native execution). Initial acceptance is **46/60 =76.67%**:context11/15,layout15/15,behavior12/15,execution8/15. This is completion against the published scope, not a percentage of effort, full hardware fidelity or OS-plus-ROM completion. No partial credit; failed/blocked paths remain in the denominator. Scope changes require a versioned amendment and a comparable old/new denominator.

Unfinished gates cover genuine floppy recovery, SCSI DMA delivery/completion, original diagnostic/monitor invocation, auxiliary interrupt routing, structural-only helpers and unreferenced resource ownership. The user-accepted6,490FF bytes do not block this scope; the final08 byte remains provisional. Physical parity and Milestone7 source/rebuild acceptance are separate unscored requirements. All gate criteria and citations are in the machine-readable scope; a generator verifies evidence-file existence/JSON, input identity, byte accounting and arithmetic rather than pretending to re-prove semantics automatically. Three guard tests pass; deterministic --check passes.

Byte coverage unchanged this scoring pass:ROM26,277/32,768=80.19% (+0.00 points),OS77,680/1,032,192=7.53% (+0.00 points). Combined overall decoding completion remains not yet quantifiable until an OS subsystem scope is published. Reproduce with `python scripts/report_ic15_completion.py --check`. Next evidence work should target one named open gate and update it only against its criterion; retain this initial score as baseline.


## OS and combined functional-scope acceptance (2026-10-16)

[Published firmware matrix](../firmware-completion-matrix.md) addsOS rubric `s760-os-decoding-v1`:24 contracts/families and96 binary gates. InitialOS acceptance is **36/96 =37.50%**. Combined with ROM46/60, the explicit gate checklist is **82/156 =52.56%**; this sums gates rather than averaging percentages. It is not a source-understanding, effort-remaining or physical-fidelity estimate.

Unmapped scheduler/interrupt-wide behavior, voice lifecycle, filesystem/persistence, synthesis, remaining screens/inputs, object hierarchy and sampling/editing remain open. The remaining-payload family explicitly covers all unclassified bytes, overlays and unassigned functions; it cannot receive completion credit while unexplained bytes remain. Historical81/33-row catalogues were not used as verified addresses/status. Every scope row has criteria and evidence, with conditional contexts preserved. OS-side execution is credited only to the narrow original-ROM-to-running-OS handoff; unrelated native tests and ROM EEPROM tests do not count as OS routine execution.

Six scope/arithmetic guard tests pass. Both generators' deterministic --check passes. Scope changes require a versioned denominator amendment; initial scope/score snapshots are retained. Reproduce with `python scripts/report_firmware_completion.py --check`. Combined overall semantic decoding completion remains unquantifiable; **published functional-scope acceptance** is now measurable and reproducible. Physical parity and Milestone7 source/rebuild gates remain separate.

Byte coverage unchanged:OS77,680/1,032,192=7.53% (+0.00 points);ROM26,277/32,768=80.19% (+0.00). Next quantitative update must change a named gate against its acceptance criterion, not convert candidate-byte growth into semantic credit. Near-term targets include native parser/event-ring contracts and remaining callee preservation, alongside still-open boot-ROM SCSI/retry/diagnostic gates.


OS source toolchain review2026-10-16: [findings and next acceptance steps](os-source-toolchain-review.md). Fresh no-change byte reconstruction independently passes, but instruction text is ignored, aliases overwrite and offsets are not bounded. BUG-088/089/090 logged;4 original tests pass plus4 strict expected failures. No source-assembler or modified-firmware gate closed. Existing decoding scores/byte coverage unchanged. Next toolchain operation is a real instruction encoder with text-only edit/invalid-syntax acceptance, canonical alias ownership and strict layout validation; do not edit hex comments and label it assembly.
