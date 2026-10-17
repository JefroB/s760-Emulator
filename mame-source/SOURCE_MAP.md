# Roland S-760 Condensed Reference

Reconciled documentation as of 2026-10-10, findings through 73. Two major
milestones now stand: the native OS **boots to a colour, mouse-interactive
Perform Play screen** (findings 53–63, documents 01–04/07), and it **loads real
samples and produces audible native-wave audio with a firmware-driven envelope**
(findings 64–72, document 06). The downstream TVF (IC29 MB87424A) and MEQ (IC30)
registers are now schematic-identified (finding68, Gemini), and MIDI is confirmed
on the CPU gate array IC4 (finding73). Both milestones are opt-in diagnostic
paths over unmodified firmware — not yet complete CPU/peripheral/ASIC fidelity,
and no simultaneous polyphony is demonstrated yet. Physical hardware facts,
implemented emulator behaviour, and observed results are labelled separately;
unproved details are tracked as evidence requests in `shared/`.

Latest functional milestone: finding64. Original-ROM boot plus a host floppy swap loads the TX81Z sample performance through Disk > Load. Perform Play shows populated patches;211,968 wave-memory bytes match the original sample disk. BMOV operand over-fetch and observed IC4 controlBC RAM-to-wave DMA were fixed. Native audio synthesis remains unverified.

Latest analysis and CPU fix: finding65. Native keyboard notes now have a verified write trace: wave slot selection, sample-address fields, pitch changes and note release. CMPL operand over-fetch and sticky-overflow handling are fixed and tested. The native path no longer starts the unrelated host audition. Boot and sample loading still pass; native audio output remains unfinished.

Latest implementation: finding66. Native Wave Custom selector/data writes now populate per-slot register state;1,080 updates pass independent replay. Pitch/rate tables are decoded with explicit inference limits. Native waveform output remains unfinished.

Latest audio milestone: finding67. The opt-in raw-wave monitor produces verified PCM from firmware notes and loaded wave RAM. CPU PORT1 selects the internal output clock. It bypasses TVF/MEQ/envelope and uses provisional loop/interpolation behavior; this is not full hardware audio emulation.

Current next step: decode downstream amplitude/filter and mixer commands, then validate loop and DI behavior. Separate pending work includes BMOVI applicability/implementation, SCSI, FDC save/errors, DMA timing, encoder/RC-100 and remaining display modes. Complete chip fidelity is not claimed.

Reproduction: run `docs/ic20-hle-findings/chatGPT-work/run-native-os.ps1`; after ROM/system-disk boot, F5 inserts the configured TX81Z sample disk, then use Disk > Load. The launcher defaults new EEPROM profiles to Mouse+CRT. Normal launch disables sound. Add `-RawWaveMonitor` for the diagnostic forward-loop PCM path; filtering, envelopes and mixing are not yet emulated there.

Latest display update: finding63, correcting finding62's text colours. Text RGB uses attribute bits4/5/6: the active Perform tab is red, B0/B1 labels yellow, E0 labels cyan. Native original-ROM boot now composes the guest graphics planes and uploaded text font. Perform hover reverses red/white text, keyboard hover turns its border pink, and Command/Exit remains functional. The colour/attribute model matches these observed transitions; exact output intensity, mask/alternate-font behavior, cursor pixels and other display modes remain provisional or unresolved.


Latest input update: finding59. Native F008 now supplies the four-nibble
mouse movement packet and active-low buttons. A ROM-boot integration test
verifies firmware coordinate changes in both directions and left-button press/
release. The launcher enables host mouse input. Hardware cursor rendering,
encoder, RC-100 and complete IC20 behavior remain unfinished.


Latest: finding58. The experimental IC15 ROM boot now loads all112 OS tracks
and reaches interactive Perform Play. Correct OP-760 identification and live VDP
pointer readback remove the video blockers. New native EEPROM profiles default
to Mouse+CRT at the user's request; existing profiles retain their setting.
Native LCD writes and its screen surface are restored. Rendering, hardware cursor,
complete chip behavior and power-on bank defaults still need work.


Previous result: finding57. Original IC15 now reads the system disk through the
native FDC/observed IC4 DMA mode, loads all112 tracks (disk4800..1007FF to
RAM0..FBFFF), and enters the disk OS without payload preloading. The ROM path
services timer interrupts and scans the panel, but its CRT remains blank.
Reset bank defaults are experimental; DMA is synchronous and CPU/peripheral
emulation remains partial. The older direct handoff still reaches Perform Play.


Current, reconciled documentation as of 2026-10-10 (findings through 60 folded
in — the opt-in banked native handoff boots the disk OS to Perform Play and runs
interactive front-panel menus, findings 53–56; MAME build/trace runbook in
`.kiro/steering/mame-build-and-trace.md`). Physical hardware facts,
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
