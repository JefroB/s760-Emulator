# Testing, Coverage & Verification

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

`OS_TEST_COVERAGE_MATRIX.md`, `OS_EXHAUSTIVE_CODE_MATRIX.md`, and
`UI_TEST_COVERAGE_MATRIX.md` are generated ownership/coverage inventories.
Their totals are snapshots, and old no-React-tests statements are superseded by
the existing suites. `MANUAL_FUNCTION_TEST_COVERAGE.md`'s 63/63 claim is not
supported by its broad/reused citations; it even assigns modern Gotek workflows
to original manual pages. Do not use its page ranges or percentages as verified
manual coverage without checking the scanned pages and actual assertions.

For any promoted coverage claim record owner, specific test, assertion,
execution result, and scope. Separate identified feature, implemented model,
tested behavior, and physical parity. Keep generated tables reproducible through
`scripts/generate_{coverage,exhaustive,ui_coverage,manual_coverage}_matrix.py`;
repair their inputs before publishing stronger claims.

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
