# Testing, Coverage & Verification

## Final source-built standalone archive — 2026-10-17

The611-file source/dependency-qualified archive now passes two complete
normal-speed workflows from its final extracted bytes, with the layered
WebView2 UI, measured Windows playback and physical MOTU recording. Four app
launches, eight output captures and twelve fresh native readbacks preserve
the Level64 program, all119,808 original sample bytes and both new allocations.
Recorded markers are32,429/36,871 frames/channel; allocations are73,728/82,944
bytes/channel. Native and device playback retain pitch, expected attenuation and
silent release. All611 files remain unchanged.

MAME and the audio bridge rebuild from delivered source; PortAudio19.7.0 uses
ASIO SDK2.3.4's GPLv3 option with its source/notices. Python and native dependency
sources accompany the host.532 backend regressions pass. The final extracted
PowerShell handoff boots without child development-tool paths; its clean-machine
collector remains INCOMPLETE because no separate clean machine/VM is available.
Static PE/matrix checks cannot close that gate (BUG-104). This is bounded
workstation acceptance, not analog parity, a duration guarantee or a release tag.
[Current promotion and exact evidence](../testing/standalone-release-promotion.md).

## Earlier572-file candidate workflow — 2026-10-17

Two complete normal-speed workstation cycles pass through one unchanged572-file
candidate and its actual layered WebView2 interface: load ROBOFULL, measure
Windows-device play/release, edit Level127→64, firmware Save/export, create a new
physical stereo recording while retaining the edited program, save all samples,
save/restart/restore the combined session and cold-reopen/restore/play again.
Four frozen-app launches and eight Windows output captures pass; the measured
edited/baseline peak ratio is0.502703 with unchanged20,004.272Hz pitch and a
released tail below1e-7. Twelve independent native processes preserve119,808
original sample bytes and both new allocations exactly through session/cold
Sample Load, and reproduce the edited program's pitch/level and native silence.
New allocations are138,240 and175,104 bytes/channel in the two cycles, with
440.085/879.833Hz tones. The second clip retains seven nonzero frames after its
default loop-start marker but before serialized sample end; these bytes are
preserved, rather than assumed to be padding.

The re-extracted PowerShell handoff verifies all candidate files and boots the
actual WebView2 UI from an unrelated directory with child development-tool paths
removed; BUG-101 fixes default kit paths under Windows PowerShell5.1. This boot
smoke remains an incomplete manual workflow report. The user has no clean Windows
machine/VM available, so clean-machine acceptance remains open. Source-built
artifact promotion is recorded above. Windows output measurements are digital endpoint loopback, not
analog parity/latency or lossless-driver evidence. [Results and reproduction](../testing/milestone-6-complete-standalone-workflow.md),
[handoff procedure](../testing/standalone-clean-machine-handoff.md).

## WebView2 physical sampling — 2026-10-17

The actual frozen WebView2 window passes a bounded normal-speed MOTU stereo
recording, firmware Sample Save/export and session restart/restore. The final
run retains 46,387 frames/channel (1.052 seconds), with 440.085/879.833 Hz tones
and unclipped peaks of 2,287/2,297 PCM16 units. Both 101,376-byte allocations
match disk exactly in three independent native processes: recorded checkpoint,
fresh checkpoint after UI restore, and cold firmware Sample Load. The final UI
case, 93 focused backend tests and TypeScript pass. The input-status snapshot
reports 2,048 discarded frames across the workflow and no native recording
underruns; physical driver loss, latency and continuous-stream integrity are
not measured. This is short physical-input acceptance on the dated development
package, with output disabled; final-artifact and clean-machine acceptance remain
open. [Evidence and reproduction](../testing/milestone-6-webview-sampling.md).

## Actual WebView2 editing — 2026-10-17

The frozen package's real WebView2 window (155.0.4283.60) passes performance
Level, patch bend, partial coarse-tune and whole-range sample Area Erase,
including firmware Save/export, session restore and cold Load. Eight frozen
launches preserve the relevant field/wave pixels and serialized edits. Ten
independent native processes verify level, bend/tuning, erased-sample silence
and note release; 519 backend tests and TypeScript pass. This closes the named
WebView editing input/persistence subset. Physical sampling is separately
qualified above; final artifact/clean-machine acceptance remains open.
[Scope and reproduction](../testing/milestone-6-webview-editing.md).

## Checkpoint-publication failures — 2026-10-17

Three forced process-tree exits at the opened zero-byte temporary-file stage
preserve the preceding recovery archive and Level 64 state. A real Windows
replacement-denied error also preserves the archive and live Level 63 edit;
retry after releasing the handle publishes and restores that new edit. Ten
fresh native processes verify dirty exports, exact sample bytes and the expected
pitch/level/release behavior; 519 backend tests pass. Later write/flush/rename
interruption points and physical power loss remain unqualified.
[Exact scope and evidence](../testing/milestone-6-checkpoint-publication.md).

## Packaged crash-recovery checkpoint — 2026-10-17

Three forced Windows process-tree exits and cold launches of the dated frozen
development package pass recovery after a completed production-timer checkpoint.
The first startup preserves that archive for 61 seconds. All three restores
reinstate dirty-media protection and the Level 64 edit, export an identical
737,280-byte disk and retain all 119,808 sample bytes. Eight independent native
processes verify sample RAM, dirty exports, unchanged pitch, expected attenuation
and silent note release; 515 backend regressions pass. This does not qualify
physical power loss, interruption during archive publication, device audio or
clean-machine/final release acceptance. [Reproduction and evidence](../testing/milestone-6-crash-recovery.md).

## Current status — 2026-10-15 review

Milestones1–5 have scoped Windows development-profile acceptance in the [current roadmap](../project/completion-roadmap.md) and [Milestone5 matrix](../testing/milestone-5-acceptance.md). SoundCheck is the accepted automated DAW framework. Final-artifact, final-interface and clean-machine qualification remains open. The [historical claim audit](../testing/milestone-6-coverage-audit.md) separates research inventories from execution evidence.

## Historical 2026-10-10 checkpoint

The finding124 checkpoint passed native/core/plugin builds, core/plugin executable checks and 152 Python tests. React was not retested for that checkpoint. Model and source-contract assertions are not hardware parity, and native executable validation is not packaged standalone/DAW validation. No tests were rerun for this documentation review.

See the [completion roadmap](../project/completion-roadmap.md) and [native runbook](11-native-boot-and-audio-runbook.md).

## Technical reference and dated milestone history

Milestone labels below apply to their cited finding, not to the present project status.


Input checkpoint: finding59. Native F008 now supplies the four-nibble
mouse movement packet and active-low buttons. A ROM-boot integration test
verifies firmware coordinate changes in both directions and left-button press/
release. The launcher enables host mouse input. Hardware cursor rendering,
encoder, RC-100 and complete IC20 behavior remain unfinished.


At that checkpoint: finding58. The experimental IC15 ROM boot now loads all112 OS tracks
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


Condensed from TESTING and the four coverage matrices; checked against current
test bodies, frontend package scripts, and CMake targets on 2026-10-09.
Historical pass totals and blanket “100% covered” statements are not current
results. This documentation pass did not run the regression suites.

## What each layer establishes

| Layer | Current entry points | Evidence provided |
| --- | --- | --- |
| Disk/image | `test_image_invariants.py`, `test_disk_conversion.py`, `test_cpp_parity.py` | Signatures, layouts, parsers/builders, selected C++/Python consistency |
| Offline DSP | `test_dsp_tools.py` | Numerical properties of software transforms, not Roland hardware equivalence |
| Peripheral models | `test_{vdp,lcd,dsp,gate_array,fdc,scsi}_mame.py` | Inspect individual tests: several exercise Python mirrors and source strings rather than compiled MAME |
| Live MAME | `mame_harness.py`, `test_interactive_ui.py`, integration/verification tests | Bounded process, controller probes, snapshots, result schema |
| C++ hosts/plugins | CMake core/plugin/bridge/editor/host/backend and property targets | Host lifecycle, serialization, protocol/surface/input contracts according to actual assertions |
| React unit/component | `google-ui` Vitest suites | Shell, SHIFT mapping/emission, rack, bridge decode/input/pointer behavior |
| Browser E2E | Playwright smoke, shell navigation, composed-shell suites | Browser interactions and visual shell output |
| Hardware captures | Recording/parity workflow | Physical reference; requires actual matched recordings and analysis |

The file name or test docstring does not determine coverage. Examples from the
current source:

- `test_mame_boot_and_palette_rendering` asserts clean exit, a frame callback,
  and a snapshot path; it does **not** assert the named palette or full OS UI.
- `test_keyboard_arrow_navigation_moves_cursor` injects keys and checks a Lua
  completion flag; it does **not** measure cursor displacement.
- `test_vdp_mame.py`'s Python mirror still treats D024 as mouse control and
  enable as bit0, unlike the current driver's pointer mapping / `data & 0x19`.
  Passing mirror tests cannot validate those newer driver semantics.
- Disk-byte parity does not establish velocity crossfades or real-time TVF
  envelopes. Static source checks do not establish runtime behavior.

## Correct treatment of the matrices

All four generated reports (`os-test-coverage-matrix.md`,
`os-exhaustive-code-matrix.md`, `ui-test-coverage-matrix.md`, and
`manual-function-test-coverage.md`) now publish **unverified historical
inventories**, not measured coverage (BUG-007). Broad feature claims, binary
addresses, manual page ranges and ownership mappings in the old inputs were
not individually validated. They must not become coverage merely because a
related test file exists. No whole-project coverage percentage is asserted.

The shared generator policy separates reviewed test selectors and their actual
assertions from the inventory: image-byte checks, static source checks and React
controls with mocked transport have different scopes. React Vitest/Playwright
suites exist; native acceptance and hardware parity require their own dated
validation. Five regression checks enforce reproducible committed output and
prevent unsupported badges from returning. See
[S2 validation](validation/s2-bugs-2026-10-11.json).

For any promoted coverage claim record owner, specific test, assertion,
execution result and scope. Separate identified feature, implemented model,
tested behavior and physical parity. Regenerate tables through
`scripts/generate_{coverage,exhaustive,ui_coverage,manual_coverage}_matrix.py`.

## Functional inventory and gaps

The software test inventory includes disk conversion/persistence, crossfade,
time stretch, offline filtering, rate/bit conversion, truncate/normalize,
wave editing, defragmentation, FAT12 exchange, SDS parsing, live recorder,
plugin I/O/state, and bridge input/display contracts. The original matrices
are useful for finding tests, not proof that every firmware mode works.

Features needing dedicated hardware/behavior evidence include performance/patch
internal resampling, compression/expansion matching the sampler, reverse-loop
smoothing, emphasis curves, Analog Feel, SMT ring/cascade behavior, SDS retries,
and sequential SCSI tape backup. Old proposed parameter values and tolerances
are test ideas, not confirmed Roland specifications.

For meaningful checks: compare rendered resampling PCM, dynamics input/output
levels and timing, reverse-loop discontinuities, emphasis transfer response,
pitch drift statistics, ring-modulation sidebands, protocol retry ordering,
and tape restore bytes. Do not promote tests that only inspect labels.

## Running checks

Current native audio checkpoint (2026-10-10, finding124): MAME driver/link and
core/plugin builds pass, both C++ test executables pass, and all152 Python tests
pass locally with no skips. The six earlier failures were stale MAME paths,
static-map assertions and a removed static Lua-file expectation; current checks
verify the generated Lua handoff, native CPU selection and narrow dynamic ports.
Five new analytic measurement tests cover reconstruction fidelity and image
rejection. The88-note native run additionally verifies the interpolation output
against an independent frequency-domain reference and confirms bit-identical
output with the option disabled. See document11 for scope and limitations.

Use the repository build/test skill for C++/backend changes and UI skill for
frontend changes. Common entry points are `python -m pytest tests -v`, CMake
test executables, `npm test`, and `npm run test:e2e` from `google-ui/`.
Use configured build directories/runtimes; do not assume old executable paths.
Regenerate MCS-96 decoder tables after opcode/generator/header edits.

For boot verification retain separate observations: EI/main-entry PCs,
interrupt acceptance/vector/return, controller writes, VRAM-active,
enabled-ever, and authentic frame content. Preserve run configuration and trace
identity. Never infer firmware completion solely from process survival,
a screenshot existing, or a nonblack fallback/background pixel.
