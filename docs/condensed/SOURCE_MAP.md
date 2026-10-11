# Source Map & Evidence Policy

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
| [01-overview.md](../01-overview.md) | 05 |
| [02-disk-layout.md](../02-disk-layout.md) | 05 |
| [03-cpu-investigation.md](../03-cpu-investigation.md) | 01, 05 |
| [04-findings-log.md](../04-findings-log.md) | 04, 05 |
| [05-manuals.md](../05-manuals.md) | 01, 05 |
| [06-ui-string-map.txt](../06-ui-string-map.txt) | 05, 09 |
| [07-emulation-spec.md](../07-emulation-spec.md) | 01, 02, 04, 10 |
| [front-panel-button-mapping.md](../front-panel-button-mapping.md) | 07 |
| [HARDWARE_RECORDING_PARITY_METHODOLOGY.md](../HARDWARE_RECORDING_PARITY_METHODOLOGY.md) | 06, 10 |
| [hil-deployment.md](../hil-deployment.md) | 10 |
| ic20-hle-findings (multi-agent boot/display/audio findings, numbered log) | 01–08 — see note below |
| [LLE_ROADMAP_AND_FIDELITY_ASSESSMENT.md](../LLE_ROADMAP_AND_FIDELITY_ASSESSMENT.md) | 04, 06, 10 |
| [MANUAL_FUNCTION_TEST_COVERAGE.md](../MANUAL_FUNCTION_TEST_COVERAGE.md) | 08 |
| [NEXTGEN_OS_FEATURES_AND_FEASIBILITY.md](../NEXTGEN_OS_FEATURES_AND_FEASIBILITY.md) | 10 |
| [OS_EXHAUSTIVE_CODE_MATRIX.md](../OS_EXHAUSTIVE_CODE_MATRIX.md) | 08 |
| [OS_FORENSICS_DEEP_DIVE.md](../OS_FORENSICS_DEEP_DIVE.md) | 05 |
| [OS_STRING_CATALOG.md](../OS_STRING_CATALOG.md) | 05, 09 |
| [OS_TEST_COVERAGE_MATRIX.md](../OS_TEST_COVERAGE_MATRIX.md) | 08 |
| [README.md](../README.md) | 05 |
| [real-hardware-ui-analysis/00-ui-architecture-and-palette.md](../real-hardware-ui-analysis/00-ui-architecture-and-palette.md) | 09 |
| [real-hardware-ui-analysis/01-disk-screens.md](../real-hardware-ui-analysis/01-disk-screens.md) | 09 |
| [real-hardware-ui-analysis/02-perform-screens.md](../real-hardware-ui-analysis/02-perform-screens.md) | 09 |
| [real-hardware-ui-analysis/03-patch-screens.md](../real-hardware-ui-analysis/03-patch-screens.md) | 09 |
| [real-hardware-ui-analysis/04-partial-screens.md](../real-hardware-ui-analysis/04-partial-screens.md) | 09 |
| [real-hardware-ui-analysis/05-sample-screens.md](../real-hardware-ui-analysis/05-sample-screens.md) | 09 |
| [real-hardware-ui-analysis/06-system-screens.md](../real-hardware-ui-analysis/06-system-screens.md) | 09 |
| [real-hardware-ui-analysis/INDEX.md](../real-hardware-ui-analysis/INDEX.md) | 09 |
| [real-hardware-ui-analysis/INFERRED_SCREEN_LAYOUTS.md](../real-hardware-ui-analysis/INFERRED_SCREEN_LAYOUTS.md) | 09 |
| [real-hardware-ui-analysis/SCREEN_INVENTORY_AND_CAPTURE_LIST.md](../real-hardware-ui-analysis/SCREEN_INVENTORY_AND_CAPTURE_LIST.md) | 09 |
| [ROLAND_DSP_ASIC_AND_TVF_ARCHITECTURE.md](../ROLAND_DSP_ASIC_AND_TVF_ARCHITECTURE.md) | 01, 06 |
| [ROLAND_RFSC16A_VDP_AND_DISPLAY_ARCHITECTURE.md](../ROLAND_RFSC16A_VDP_AND_DISPLAY_ARCHITECTURE.md) | 03, 09 |
| [ROLAND_SED1335_LCD_ARCHITECTURE.md](../ROLAND_SED1335_LCD_ARCHITECTURE.md) | 03, 07 |
| [service-notes-ocr.txt](../service-notes-ocr.txt) | 01, 05, 06 |
| [TESTING.md](../TESTING.md) | 08 |
| [UI_CONSOLIDATION_ASSESSMENT_AND_RECOMMENDATIONS.md](../UI_CONSOLIDATION_ASSESSMENT_AND_RECOMMENDATIONS.md) | 07, 08 |
| [UI_CONSOLIDATION_PLAN.md](../UI_CONSOLIDATION_PLAN.md) | 07, 08 |
| [UI_TEST_COVERAGE_MATRIX.md](../UI_TEST_COVERAGE_MATRIX.md) | 08 |
| [VDP_LAYOUT_DESCRIPTORS.json](../VDP_LAYOUT_DESCRIPTORS.json) | 09 |

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
