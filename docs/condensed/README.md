# Roland S-760 Condensed Reference

Current, reconciled documentation as of 2026-10-09. Physical hardware facts,
implemented emulator behavior, and observed boot results are labeled separately.
Unsupported claims are excluded from specifications and tracked as evidence
requests in the team's shared folder. Original docs remain as the evidence trail.

| Document | Contents |
| --- | --- |
| [01 Hardware and memory map](01-hardware-and-memory-map.md) | Primary-source chip identities/specs; current installed MAME windows |
| [02 IC15 EPROM and HLE](02-ic15-boot-eprom-and-handoff.md) | Available ROM, actual preload path, implemented selector behavior and limits |
| [03 VDP/display](03-rfsc16a-vdp-and-display-architecture.md) | Current register handling, pointer/layout defaults, palette, native/bridge geometry |
| [04 Execution and next work](04-execution-pipeline-and-emulator-action-plan.md) | Stable-run evidence, CPU compatibility shims, D010 task, verification gates |
| [05 Disk/forensics/patching](05-disk-format-forensics-and-patching.md) | Disk regions, address math, tools, patch results, catalogs/manuals |
| [06 Audio and capture parity](06-audio-dsp-and-hardware-parity.md) | Actual software DSP contract, hardware identities, capture plan/tooling limits |
| [07 UI and front panel](07-ui-architecture-and-front-panel.md) | Canonical shell, implemented bridge, SHIFT evidence rules, LCD commands |
| [08 Testing and coverage](08-testing-coverage-and-verification.md) | Real layer ownership, assertion limits, stale matrix claims, verification |
| [09 Hardware screens](09-hardware-screens-and-layout-evidence.md) | 37-photo catalog, visual patterns, candidate descriptors and capture priorities |
| [10 Deployment and roadmap](10-hardware-deployment-and-development-roadmap.md) | Gotek/SCSI workflow, unfinished fidelity work, proposed future features |
| [Source map](SOURCE_MAP.md) | Every public source document, resolution evidence, shared requests |

Read 01–04 for boot engineering; 07–09 for frontend/display work; 05–06 and 10
for disk/audio/hardware experiments. No fresh regression pass is claimed by this
documentation-only update.
