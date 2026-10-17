# Source Map & Evidence Policy

Current project qualification (2026-10-14): `docs/testing/soundcheck-projects.md`,
`scripts/soundcheck_project.py`, `scripts/verify_soundcheck_project.py` and
`tests/test_soundcheck_project.py` define the accepted SoundCheck SDK adapter/
project-runner scope. Source/binary hashes,221184 exact-frame comparisons and
compatibility limits are recorded in
[validation](validation/milestone-4-soundcheck-project-2026-10-14.json).
This does not establish stock-GUI project integration, other DAW containers or
cross-build/rate/negotiated-maximum migration.355 backend regressions pass.

Updated 2026-10-10. Every public Markdown/text/JSON source under `docs/` is
mapped below; private agent work folders and condensed outputs are excluded.
Source documents remain intact as historical evidence. Raw catalogs/OCR/JSON
retain their full data; condensation replaces repeated explanation, not raw records.

## How conflicts were resolved

Use visually checked primary hardware specifications for physical identity;
current executable source/build configuration for implemented behavior; dated
trace/hardware results for observed outcomes. A newer prose claim does not
override those forms of evidence. Unproved hardware details are excluded from
the specification and requested in the shared evidence note.

Important reconciliations: CPU IC1 / EPROM IC15 / I/O gate IC20; 24 physical
voices versus 32 software slots; CS5339 ADC; four individual analog outputs;
narrow LCD map; one 17-bit modeled VDP pointer; byte DSP latches; existing
React/bridge tests; separate DSP implementations; latest stable run has no
D010 enable write. Document 08 explains why old coverage totals are unsupported.

## Original-to-condensed mapping

| Original source | Condensed document numbers |
| --- | --- |
| [native-vst3-sampling.md](../emulator/runtime/native-vst3-sampling.md) | 06, 10 |
| [01-overview.md](../project/history/01-overview.md) | 05 |
| [02-disk-layout.md](../project/history/02-disk-layout.md) | 05 |
| [03-cpu-investigation.md](../project/history/03-cpu-investigation.md) | 01, 05 |
| [04-findings-log.md](../project/history/04-findings-log.md) | 04, 05 |
| [05-manuals.md](../project/history/05-manuals.md) | 01, 05 |
| [06-ui-string-map.txt](../firmware/os/06-ui-string-map.txt) | 05, 09 |
| [07-emulation-spec.md](../emulator/07-emulation-spec.md) | 01, 02, 04, 10 |
| [front-panel-button-mapping.md](../hardware/front-panel-button-mapping.md) | 07 |
| [hardware-recording-parity-methodology.md](../hardware/captures/hardware-recording-parity-methodology.md) | 06, 10 |
| [hil-deployment.md](../hardware/captures/hil-deployment.md) | 10 |
| ic20-hle-findings (multi-agent boot/display/audio findings, numbered log) | 01–08 — see note below |
| [lle-roadmap-and-fidelity-assessment.md](../project/lle-roadmap-and-fidelity-assessment.md) | 04, 06, 10 |
| [manual-function-test-coverage.md](../testing/manual-function-test-coverage.md) | 08 |
| [nextgen-os-features-and-feasibility.md](../firmware/os/nextgen-os-features-and-feasibility.md) | 10 |
| [os-exhaustive-code-matrix.md](../firmware/os/os-exhaustive-code-matrix.md) | 08 |
| [os-forensics-deep-dive.md](../firmware/os/os-forensics-deep-dive.md) | 05 |
| [os-string-catalog.md](../firmware/os/os-string-catalog.md) | 05, 09 |
| [os-test-coverage-matrix.md](../firmware/os/os-test-coverage-matrix.md) | 08 |
| [README.md](../README.md) | 05 |
| [real-hardware-ui-analysis/00-ui-architecture-and-palette.md](../hardware/screens/00-ui-architecture-and-palette.md) | 09 |
| [real-hardware-ui-analysis/01-disk-screens.md](../hardware/screens/01-disk-screens.md) | 09 |
| [real-hardware-ui-analysis/02-perform-screens.md](../hardware/screens/02-perform-screens.md) | 09 |
| [real-hardware-ui-analysis/03-patch-screens.md](../hardware/screens/03-patch-screens.md) | 09 |
| [real-hardware-ui-analysis/04-partial-screens.md](../hardware/screens/04-partial-screens.md) | 09 |
| [real-hardware-ui-analysis/05-sample-screens.md](../hardware/screens/05-sample-screens.md) | 09 |
| [real-hardware-ui-analysis/06-system-screens.md](../hardware/screens/06-system-screens.md) | 09 |
| [real-hardware-ui-analysis/index.md](../hardware/screens/index.md) | 09 |
| [real-hardware-ui-analysis/inferred-screen-layouts.md](../hardware/screens/inferred-screen-layouts.md) | 09 |
| [real-hardware-ui-analysis/screen-inventory-and-capture-list.md](../hardware/screens/screen-inventory-and-capture-list.md) | 09 |
| [roland-dsp-asic-and-tvf-architecture.md](../hardware/roland-dsp-asic-and-tvf-architecture.md) | 01, 06 |
| [roland-rfsc16a-vdp-and-display-architecture.md](../hardware/roland-rfsc16a-vdp-and-display-architecture.md) | 03, 09 |
| [roland-sed1335-lcd-architecture.md](../hardware/roland-sed1335-lcd-architecture.md) | 03, 07 |
| [service-notes-ocr.txt](../hardware/service-notes-ocr.txt) | 01, 05, 06 |
| [testing.md](../testing/testing.md) | 08 |
| [ui-consolidation-assessment-and-recommendations.md](../emulator/ui/ui-consolidation-assessment-and-recommendations.md) | 07, 08 |
| [ui-consolidation-plan.md](../emulator/ui/ui-consolidation-plan.md) | 07, 08 |
| [ui-test-coverage-matrix.md](../testing/ui-test-coverage-matrix.md) | 08 |
| [VDP_LAYOUT_DESCRIPTORS.json](../firmware/os/vdp-layout-descriptors.json) | 09 |

## Primary references and code used to resolve disagreements

- [Service Notes](../../Manuals/ROLAND_S-760_SERVICE_NOTES.pdf), printed p.1 and p.5, visually reviewed.
- [MAME driver](../../mame-source/src/mame/roland/s760.cpp): installed handlers, HLE, VDP/LCD, palette, sound and geometry.
- [Opcode implementation](../../mame-source/src/devices/cpu/mcs96/mcs96ops.lst): current stack-neutral workarounds.
- [CMake source list](../../core/CMakeLists.txt) and [standalone DSP source](../../core/src/s760_core.cpp): distinguish existing source from linked engine.
- [Bridge contract](../../core/include/s760/s760_bridge_protocol.hpp) and [React client](../../google-ui/src/bridge/S760BridgeClient.ts).
- [Frontend package scripts](../../google-ui/package.json), actual Python/React test bodies, and CMake test targets.
- [Layout extractor](../../.agents/scripts/extract_screen_layout.py): heuristic implementation, not claimed full field parser.
- Calibration builder/extractor/analyzer scripts: current capability versus proposed measurement plan.

## Note on the ic20-hle-findings log

The multi-agent reverse-engineering log in `docs/ic20-hle-findings/shared/` is a
numbered, append-mostly working record (Kiro / Gemini / ChatGPT). Its CONFIRMED
results are consolidated into condensed documents 01–08 as they land, and the
superseded numbered entries are pruned once consolidated — so only the current
head of each active thread normally remains in `shared/` (plus `archive/` for the
earliest batch). The condensed documents are therefore the standalone source of
truth; the shared log is the live scratch/evidence trail, not a stable citation
target. Finding numbers referenced in the condensed prose (e.g. "finding 73") are
historical labels for that evidence, not links.

- finding58 - interactive ROM boot, grounded option-board identification, live VDP pointer, native LCD and requested EEPROM default.

- finding59 - native mouse handshake and guest movement/button verification.

- finding60 - uploaded font raster, matrix-page selection and cursor coordinate evidence.

- finding61 - original-ROM mouse hover trace, provisional crosshair rendering and unresolved label attribute semantics.

- finding62 - guest RGB graphics/text composition, option inversion, pink keyboard border and bounded display-model evidence.

- finding63 - hardware-observation correction to text RGB bits4/5/6; final colour and keyboard-border checks.

- finding64 - BMOV decode correction, observed RAM-to-wave DMA, host floppy swap and original-ROM sample-load validation.

- finding65 - native keyboard voice-register trace, pitch interval comparison, CMPL decode/VT fix and continued boot/sample validation.

- finding66 - native wave write-bank implementation, independent runtime replay and original-image pitch/rate-table analysis.

- finding67 - internal audio clock selection and opt-in raw-wave monitor, measured two-note capture and explicit synthesis limitations.

- finding69 - original OS product arithmetic and quadratic release verified against316 product writes and68 release updates; hardware gain semantics remain open.

- finding70 - write-side envelope/companion storage verified against902 updates; static state-clear evidence for high command bit; DSP semantics unresolved.

- finding71 - optional provisional Q15 coefficient audition;311 waveform intervals verified and raw-mode output unchanged; hardware semantics explicitly unresolved.

- finding72 - six rapid/short/long auditions with audio/register replay; establishes channel0 reuse and the limit of mouse testing for polyphony.

- finding73 - schematic correction to MIDI routing; IC4 byte port0116, transmit-ready polling and unresolved receive interrupt dispatch.

- finding74 - opt-in inferred IC4 vector response; serialized MIDI reaches the firmware allocator and produces three overlapping voices; peripheral fidelity limits explicit.

- finding76 - original pan tables and MIDI left/centre/right transactions;814 updates replayed, optional provisional Q11 stereo audition validated, and unsupported mixer claims corrected.

- finding77 -646 cutoff updates verified from upstream guest inputs and original tables;101008 resonance candidate narrowed, hardware filter law still unresolved.

- finding78 - isolated visible resonance and LPF/BPF/HPF/Off edits establish control-register labels and Off sequence; transfer-function emulation remains unfinished.

- finding79 - write-side filter state implemented;518 updates independently replayed across five channels, stereo PCM unchanged, build/regression evidence and DSP limits recorded.

- finding80 - global packed filter bitmap implemented;24 simultaneous firmware voices and full release verified with independent mask/wave/envelope replay; stereo PCM unchanged.
