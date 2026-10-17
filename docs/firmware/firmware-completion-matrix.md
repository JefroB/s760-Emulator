# Firmware functional-scope acceptance

**Combined checklist: 82/156 = 52.56%.**
Boot ROM: 46/60 = 76.67%. OS: 36/96 = 37.50%.

These are binary acceptance gates against versioned scopes, not estimates of effort remaining or percentage of source understood. The combination counts gates directly; it does not average byte coverage or give every subsystem an assumed share of engineering cost.

The OS scope has24 bounded contracts/families, including broad unmapped families and an explicit catch-all for every unclassified region or unassigned function. Passing a local MIDI parser does not pass the whole MIDI/voice system. Native playback, UI tests, physical captures and ROM tests do not automatically qualify unrelated OS routines. The historical81/33-row catalogues remain unverified; their addresses and badges were not credited.

| OS contract/family | Context | Layout | Behavior | Execution |
| --- | --- | --- | --- | --- |
| [OS handoff and initial selectors](../condensed/validation/os-reconciled-independent-review-2026-10-16.json) | Pass | Pass | Open | Pass |
| [Scheduler and interrupt-wide control](../condensed/validation/os-reconciled-frontier-promotion-2026-10-16.json) | Open | Open | Open | Open |
| [Resident MIDI status parser](../condensed/validation/os-midi-decoding-2026-10-16.json) | Pass | Pass | Pass | Open |
| [Note processing and voice lifecycle](../condensed/validation/os-controller-routing-2026-10-16.json) | Open | Open | Open | Open |
| [Controller/RPN routing](../condensed/validation/os-controller-routing-2026-10-16.json) | Pass | Pass | Open | Open |
| [System-message framing/checksum](../condensed/validation/os-system-message-decoding-2026-10-16.json) | Pass | Pass | Pass | Open |
| [Transfer allocation and rollback](../condensed/validation/os-transfer-lifecycle-2026-10-16.json) | Pass | Pass | Open | Open |
| [Known transfer field packing](../condensed/validation/os-transfer-fields-2026-10-16.json) | Pass | Pass | Pass | Open |
| [Known sample-send/copy helpers](../condensed/validation/os-send-and-copy-helpers-2026-10-16.json) | Pass | Pass | Open | Open |
| [SCSI session/request ownership](../condensed/validation/os-scsi-session-2026-10-16.json) | Pass | Pass | Open | Open |
| [SCSI target commands and deletion](../condensed/validation/os-scsi-transfer-delete-2026-10-16.json) | Pass | Pass | Pass | Open |
| [OS FDC startup and result IRQ](../condensed/validation/os-panel-fdc-startup-2026-10-16.json) | Pass | Pass | Pass | Open |
| [OS filesystem and media persistence](../condensed/validation/os-reconciled-frontier-promotion-2026-10-16.json) | Open | Open | Open | Open |
| [OS EEPROM services](../condensed/validation/os-eeprom-services-2026-10-16.json) | Pass | Pass | Pass | Open |
| [OS audio initialization/routing](../condensed/validation/os-startup-audio-2026-10-16.json) | Pass | Open | Open | Open |
| [Remaining synthesis and modulation](../condensed/validation/os-controller-routing-2026-10-16.json) | Open | Open | Open | Open |
| [Resident UI event ring](../condensed/validation/os-ui-event-ring-2026-10-16.json) | Pass | Pass | Open | Open |
| [Known screen-descriptor loader](../condensed/validation/os-screen-descriptor-loader-2026-10-16.json) | Pass | Pass | Open | Open |
| [Known selection/refresh callbacks](../condensed/validation/os-selection-refresh-2026-10-16.json) | Pass | Pass | Open | Open |
| [Remaining UI screens and rendering](../condensed/validation/os-screen-descriptor-loader-2026-10-16.json) | Open | Open | Open | Open |
| [Remaining panel/mouse/input ownership](../condensed/validation/os-panel-fdc-startup-2026-10-16.json) | Open | Open | Open | Open |
| [Performance/patch/partial/sample management](../condensed/validation/os-scsi-transfer-delete-2026-10-16.json) | Open | Open | Open | Open |
| [Sampling and waveform editing](../condensed/validation/os-reconciled-frontier-promotion-2026-10-16.json) | Open | Open | Open | Open |
| [Remaining payload, overlays and resources](../condensed/validation/os-exploration-coverage-2026-10-16.json) | Open | Open | Open | Open |

## Open acceptance work

- **OS handoff and initial selectors:** Explain complete startup ordering, dependency failures and mutable configuration branches.
- **Scheduler and interrupt-wide control:** Map all scheduler/IRQ owners, bound indirect dispatch, qualify context restoration and ordinary invocation.
- **Resident MIDI status parser:** Exercise parser wrap, status classes and malformed/system transitions with native captured input.
- **Note processing and voice lifecycle:** Recover caller graph, voice ownership and allocation/release failures; validate supported musical workflows.
- **Controller/RPN routing:** Resolve destination parameter meanings and runtime list termination/preservation; exercise controller contracts.
- **System-message framing/checksum:** Native valid/invalid header, checksum and length cases; account for remaining protocol families in unknown-payload row.
- **Transfer allocation and rollback:** Prove intervening callee preservation, overflow/failure cleanup and runtime allocation/cancellation.
- **Known transfer field packing:** Native boundary/malformed inputs and response capture; algebra tests are not execution.
- **Known sample-send/copy helpers:** Close owner/callee context, complete send/receive state transitions and native end-to-end transfer.
- **SCSI session/request ownership:** Resolve producers and mutable ownership; validate session success/failure/status under ordinary input.
- **SCSI target commands and deletion:** Exercise target commands, error status, deletion and cleanup without forcing guest state.
- **OS FDC startup and result IRQ:** Ordinary native seek/recalibration/result lengths and IRQ wait qualification.
- **OS filesystem and media persistence:** Map file/media workflows and failure/cleanup behavior, then exercise persistence/reload.
- **OS EEPROM services:** Ordinary OS configuration persistence and retry cases; ROM EEPROM execution does not qualify OS routines.
- **OS audio initialization/routing:** Bound remaining configuration-indexed coefficient tables and explain routing meanings; validate OS-side transactions.
- **Remaining synthesis and modulation:** Recover remaining parameter/voice paths, layout and state transitions, then validate representative boundaries.
- **Resident UI event ring:** Resolve concurrency, capacity and cursor ownership; native producer/consumer event traces.
- **Known screen-descriptor loader:** Explain all descriptor-pointer roles and mutable callbacks; native cache/state validation.
- **Known selection/refresh callbacks:** Close mutable descriptor/callback assumptions and full caller preservation; native selection/cancel assertions.
- **Remaining UI screens and rendering:** Establish actual screen inventory and bounds, explain renderer/field behavior and exercise screens.
- **Remaining panel/mouse/input ownership:** Identify all input producers and dispatch ownership, recover side effects and native boundary cases.
- **Performance/patch/partial/sample management:** Decode object layouts and full lifecycle/failure paths; validate representative ordinary workflows.
- **Sampling and waveform editing:** Recover entry/caller graph, sample buffer contracts and edit/failure semantics; validate workflows.
- **Remaining payload, overlays and resources:** Classify remaining payload with evidence; account for overlays/indirect control and assign newly discovered functionality via versioned scope amendments. This row cannot pass while unexplained regions remain.

## Interpretation and stable updates

Never remove unfinished families to improve score. New independent functionality requires a versioned amendment, retained previous snapshot and explicit old/new denominator. Refinements retain gates and stated scope.

The unknown-payload family cannot earn credit while unclassified bytes remain. Newly discovered behavior is assigned explicitly; it is never silently omitted to preserve a high score. The current scope is a reviewable v1 functional plan, not a proven exhaustive feature taxonomy. A fuller feature inventory can require a versioned amendment. Hardware parity and source/rebuild acceptance stay separate.

**Overall semantic decoding completion or effort remaining: not yet quantifiable.** The checklists now give a reproducible, narrower acceptance measure; they do not supply defensible effort weights or establish that all runtime roots are known.

[Boot-ROM matrix](boot-rom/ic15-completion-matrix.md) · [OS criteria and evidence](../condensed/validation/os-completion-scope-v1.json) · [Generated scores](../condensed/validation/firmware-completion-score-v1-2026-10-16.json)

Reproduce: `python scripts/report_firmware_completion.py --check`. The script verifies scope shape, input identities, inventory/evidence files and arithmetic; evidence judgments remain explicit manual assessments.

OS classified-byte coverage: **77,680/1,032,192 = 7.53%** (+0.00 percentage points in this scoring pass).
ROM classified-byte coverage: **26,277/32,768 = 80.19%** (+0.00 percentage points in this scoring pass).
