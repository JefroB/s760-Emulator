# Boot-ROM completion scope and score

**Boot-ROM functional-scope acceptance: 46/60 gates = 76.67%.**

This measures acceptance against the published IC15 v1 functional scope. It is not a percentage of effort completed or time remaining. Each of15 paths has four binary gates; open or blocked gates earn zero. Evidence is assessed manually against explicit criteria, then totals are generated. A linked report alone does not mechanically prove a gate.

| Gate | Acceptance rule | Passed |
| --- | --- | --- |
| Context | Justified entry/caller/gate and explicit fetch/data context under recorded conditions; conditional proof can pass, physical invocation is not implied. | 11/15 |
| Layout | Instruction/data boundaries, relevant widths and extents independently checked for the path. | 15/15 |
| Behavior | Inputs, outputs/state transitions and error/terminal behavior explained within the declared path scope. | 12/15 |
| Execution | Ordinary unchanged-firmware native execution validates the path acceptance condition; isolated component tests alone are insufficient. | 8/15 |

| Functional path | Context | Layout | Behavior | Execution |
| --- | --- | --- | --- | --- |
| [Reset and startup selection](../../condensed/validation/ic15-root-and-hex-audit-2026-10-16.json) | Pass | Pass | Pass | Pass |
| [Successful floppy OS load](../../condensed/validation/ic15-byte6903-floppy-load-trace-2026-10-16.json) | Pass | Pass | Pass | Pass |
| [Floppy errors and recovery](../../condensed/validation/ic15-native-invalid-media-2026-10-16.json) | Pass | Pass | Open | Open |
| [SCSI command/header and fallback](../../condensed/validation/ic15-native-scsi-command-contract-2026-10-16.json) | Pass | Pass | Pass | Pass |
| [SCSI payload DMA completion](../../condensed/validation/ic15-native-scsi-valid-header-2026-10-16.json) | Open | Pass | Open | Open |
| [Front-panel setup menu](../../condensed/validation/ic15-native-menu-bounds-2026-10-16.json) | Pass | Pass | Pass | Pass |
| [EEPROM persistence](../../condensed/validation/ic15-native-setup-eeprom-2026-10-16.json) | Pass | Pass | Pass | Pass |
| [Boot display and referenced resources](../../condensed/validation/ic15-display-resource-2026-10-16.json) | Pass | Pass | Pass | Pass |
| [Startup audio initialization](../../condensed/validation/ic15-native-audio-init-2026-10-16.json) | Pass | Pass | Pass | Pass |
| [RAM self-test](../../condensed/validation/ic15-indirect-store-contracts-2026-10-16.json) | Pass | Pass | Pass | Open |
| [Serial monitor and continuation](../../condensed/validation/ic15-local-stack-balance-2026-10-16.json) | Pass | Pass | Pass | Open |
| [FDC interrupt and boot stack](../../condensed/validation/ic15-native-stack-after-cpu-2026-10-16.json) | Pass | Pass | Pass | Pass |
| [Other low ROM interrupt stubs](../../condensed/validation/ic15-decoding-2026-10-16.json) | Open | Pass | Pass | Open |
| [Structural-only helper family](../../condensed/validation/ic15-residual-helpers-2026-10-16.json) | Open | Pass | Pass | Open |
| [Unreferenced resources and final byte](../../condensed/validation/ic15-residual-text-classification-2026-10-16.json) | Open | Pass | Open | Open |

## What remains

- **Floppy errors and recovery:** Each error cause, retry transition and cleanup distinguished; genuine transport retry contract completed. Represented transport error/retry and short-media behavior qualified without forcing guest state.
- **SCSI payload DMA completion:** DMA interrupt delivery, vector selection and acknowledgment context established. Full-count extent, completion/acknowledgment and failure handling explained independently. Original ROM loads full SCSI OS payload and reaches OS via ordinary input.
- **RAM self-test:** Supported ordinary diagnostic input reaches test and qualifies success/failure behavior.
- **Serial monitor and continuation:** Supported entry and serial input exercise original monitor commands and continuation.
- **Other low ROM interrupt stubs:** Real source-to-vector delivery and mapping contracts established. Independent ordinary invocation validates delivery/acknowledgment for these sources.
- **Structural-only helper family:** Justified callers or supported alternate invocation contexts established for structural-only entries. Original firmware invokes representative remaining helper contracts via supported inputs.
- **Unreferenced resources and final byte:** Consumers/ownership or an explicitly accepted unused classification established for remaining resources. Role or non-use established beyond observed-path absence; author intent not invented. Relevant dormant consumer or accepted non-use contract validated; current negative traces alone do not close this.

## Byte accounting and separate acceptance gates

Boot ROM evidence-backed classified-byte coverage: **26,277/32,768 = 80.19%**. This scoring pass adds no bytes (+0.00 percentage points).

OS evidence-backed classified-byte coverage: **77,680/1,032,192 = 7.53%**. This scoring pass adds no bytes (+0.00 percentage points).

User-accepted presumed unused FF space: 6,490 bytes. Including that assumption accounts for 32,767/32,768 bytes; 1 other byte remains provisional. The FF assumption does not prove padding, and preserving those bytes remains required.

**Overall OS-plus-ROM decoding completion: not yet quantifiable.** The OS needs its own subsystem scope before a combined measure is defensible. No averaging the ROM score with OS byte coverage.

The following are outside this score and remain independently required for their respective claims:

- Physical power-on selector defaults, bus/interrupt timing and real hardware parity
- Assembler/source generation, byte-exact rebuild and modified-firmware acceptance (Milestone7)
- Full OS behavioral completion; its inventory/denominator is not yet established

## Stable updates

Freeze v1 paths and acceptance criteria. New independent functionality requires a versioned scope amendment and an explicit old/new denominator and baseline; new details within a path refine evidence without silently changing its gates. Never drop a failed path to improve score.

A gate changes to Pass only when its stated acceptance criterion is met with evidence and limitations recorded. Regressions can reopen passed gates. Preserve previous score snapshots and report deltas against the same rubric version. At100% this means all60 v1 gates passed, not that physical parity or the editable toolchain is complete.

[Machine-readable criteria, statuses and evidence](../../condensed/validation/ic15-completion-scope-v1.json) · [Generated score and evidence hashes](../../condensed/validation/ic15-completion-score-v1-2026-10-16.json)

Reproduce: `python scripts/report_ic15_completion.py`. It verifies input identity, current byte inventories, scope shape and evidence-file existence/JSON before generating totals. It does not independently re-prove the semantic conclusions in those evidence files.
