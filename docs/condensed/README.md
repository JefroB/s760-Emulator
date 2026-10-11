# Roland S-760 Condensed Reference

Current checkpoint: 2026-10-10, findings through124. Native original-ROM boot
reaches the colour, mouse-interactive Perform Play screen, loads sample disks,
and plays firmware-driven MIDI voices. Measured loop, envelope, filter and
pitch audition paths are available; complete CPU/peripheral/ASIC fidelity is
not claimed.

The full88-key hardware capture resolves a measurement-resampling bug. With
fixed coefficients,28 pulse rates match within0.697–0.926% normalized RMS error
and four independent noise cases within0.380–0.538%, in100Hz–18kHz. The new
opt-in native interpolator passes all88 fixture notes; disabled output remains
bit-identical. Hardware limits and distinctions between models and facts remain
explicit in document06.

Start with [the native boot/audio runbook](11-native-boot-and-audio-runbook.md)
for current launch flags, validation, limits and commit scope. MAME and core/plugin
builds pass; both C++ suites and all152 Python tests pass locally. Original
firmware, captures and private research remain local; committed references
contain the supported conclusions.

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
| [11 Native boot/audio runbook](11-native-boot-and-audio-runbook.md) | Current launch, supported pitch domain, validation and commit scope |
| [Source map](SOURCE_MAP.md) | Every public source document, resolution evidence, shared requests |
