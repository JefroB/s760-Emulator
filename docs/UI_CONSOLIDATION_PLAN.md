# UI Consolidation Plan — One Canonical React UI, MAME as Display Backend

Status: PROPOSED (for review)
Author: prepared for Gemini review
Scope: `google-ui/` (React), `mame-source/src/mame/roland/s760.cpp` (MAME driver), `tests/`, docs

---

## Problem Statement

The project currently has **two separate, divergent user interfaces** for the same
Roland S-760 front panel, built in two different technology stacks:

1. **MAME driver GUI** — `mame-source/src/mame/roland/s760.cpp` hand-draws a complete
   "sampler GUI" in C++: `crt_update`, `lcd_update`, and
   `render_perform_mode / render_patch_mode / render_partial_mode / render_sample_mode /
   render_disk_mode / render_system_mode / render_rack_panel`, plus `draw_string`, a
   10-pen palette, a drawn 1U rack chassis, drawn knobs/buttons, a mouse cursor, and a
   drawn Gotek drive bay. This is what the root `README.md` screenshot (`Main.png`) shows.

2. **React web UI** — `google-ui/` (Vite + TypeScript) renders the same physical device:
   `OP760Monitor`, `S760FrontPanel`, `RolandLCD`, `GotekBay`, `AuditionKeyboard`, and an
   `EmulatorBridgePanel` that already sketches an intended `s760_input` event bridge to a
   C++/MAME core.

Having two UIs is the defect. They duplicate the same device chrome, drift independently,
and create false coverage claims (see below). **The React UI is the canonical UI design.**
MAME should **not** draw its own competing GUI; it should render **only the authentic pixel
content of the real displays** and hand those buffers to the React UI, which owns all shell
and chrome.

### Secondary problem: false test provenance

The doc generators `scripts/generate_ui_coverage_matrix.py` and
`scripts/generate_exhaustive_matrix.py` attribute ~170 UI elements to
`google-ui/src/components/OP760Monitor.tsx:<line>` and mark them "✅ Tested" by
`tests/test_interactive_ui.py`. But `tests/test_interactive_ui.py` actually boots
`mames760.exe` via `tests/mame_harness.py` and asserts on **MAME-rendered screenshots** — it
never loads or exercises the React components. So the React UI is effectively untested, and
the generated matrices (`docs/UI_TEST_COVERAGE_MATRIX.md`,
`docs/OS_EXHAUSTIVE_CODE_MATRIX.md`) claim coverage that does not exist. This must be
corrected as part of consolidation.

---

## Target Architecture

Clean split of responsibility:

- **React (`google-ui/`) = canonical UI / physical shell.** Owns everything the user sees
  as "the hardware": OP-760 CRT monitor bezel + tube effects, the 1U rack chassis, all
  knobs/buttons/meters, the front-panel LCD *housing*, and the Gotek drive-bay *housing*
  and backlight tint. Single source of UI-design truth.

- **MAME = emulation backend that renders only the three real display surfaces** (the
  "pixels behind the glass"), which React composites into its shell:
  1. **CRT frame content** — the OP-760 RFSC16A VDP RGB output.
  2. **Front-panel LCD content** — the Epson SED1335 160×64 monochrome framebuffer.
  3. **Gotek OLED content** — the drive's small image-name / track readout.

  MAME draws **no invented GUI**: no `render_*_mode`, no drawn rack panel, no drawn front
  panel, no drawn knobs/cursor/palette chrome. It emits only authentic emulated display
  buffers plus audio.

```
┌──────────────────────────────────────────────────────────────┐
│  React UI (google-ui)  — CANONICAL SHELL                        │
│                                                                 │
│   ┌───────────────────────────┐   OP-760 CRT bezel (React)      │
│   │   [ CRT pixel content ]   │ ◄── MAME VDP framebuffer         │
│   └───────────────────────────┘                                 │
│   ┌───────────┐  1U rack chassis + knobs/buttons (React)         │
│   │ [LCD px]  │ ◄── MAME SED1335 framebuffer                     │
│   └───────────┘                                                  │
│   ┌───────┐    Gotek bay housing (React)                         │
│   │[OLED] │ ◄── MAME Gotek OLED readout                          │
│   └───────┘                                                      │
│        ▲  input events (s760_input)   ▼ framebuffers + audio     │
└────────┼───────────────────────────────┼──────────────────────┘
         │                               │
         └────────────  BRIDGE  ─────────┘
                   (transport TBD)
                          │
         ┌────────────────▼─────────────────┐
         │  MAME s760 driver — EMULATION ONLY │
         │  CPU (MCS-96), SED1335, RFSC16A    │
         │  VDP, FDC, SCSI, sound. No GUI.    │
         └────────────────────────────────────┘
```

### Open design decision: the bridge/transport

React needs MAME's three framebuffers (and audio) live, and must send input back. Candidate
transports (pick one during review):

- **A. MAME Lua plugin → local WebSocket.** MAME has a Lua interface; a plugin streams the
  CRT + LCD + OLED buffers over `ws://localhost:<port>` and receives `s760_input` events.
  React `EmulatorBridgePanel` connects to it. Matches the design already stubbed in
  `EmulatorBridgePanel.tsx`. **Recommended.**
- **B. Sidecar process** reading MAME snapshots/shared memory and serving HTTP/WebSocket.
- **C. Use the existing `core/` libretro host for the live path instead of MAME.** The C++
  `core/` already exposes audio/video/state via `s760_libretro_host` and `s760_cpp` pybind.
  React could pair with that for the interactive path and keep MAME for accuracy/headless.

Recommendation: **A** for the MAME display path. (Decision needed from reviewer.)

---

## Phased Plan

### Phase 1 — Deduplicate (low risk, reversible, do first)
Goal: remove the second UI so only the React design remains; MAME emits only authentic
display buffers.

1. In `mame-source/src/mame/roland/s760.cpp`, remove the invented-GUI rendering:
   - Delete `render_perform_mode`, `render_patch_mode`, `render_partial_mode`,
     `render_sample_mode`, `render_disk_mode`, `render_system_mode`, `render_rack_panel`
     and their call sites.
   - Reduce `crt_update` to output only the genuine RFSC16A VDP framebuffer (no drawn tabs,
     tables, cursor chrome, or fake content).
   - Keep `lcd_update` but have it reflect only the real SED1335 VRAM contents (drop the
     "render active front panel page" fallback that invents text when VRAM is empty).
   - Remove the drawn rack-panel/Gotek/knob chrome and the palette pens that exist only to
     paint that chrome (keep pens the real VDP/LCD need).
2. Keep all genuine hardware emulation intact (CPU, SED1335 controller, RFSC16A VDP, FDC,
   SCSI, sound, EEPROM, inputs).
3. Mark `google-ui/` as the canonical UI in `README.md`; stop presenting the MAME-drawn
   `Main.png` as the product UI.
4. **Acceptance:** MAME still boots and runs the OS; CRT/LCD show only what the OS actually
   draws; no invented GUI remains in the driver.

### Phase 2 — Fix false coverage / provenance
5. Update `scripts/generate_ui_coverage_matrix.py`, `scripts/generate_exhaustive_matrix.py`,
   and `scripts/generate_coverage_matrix.py` so UI-element rows point at the real owning
   source (React component for shell elements; `s760.cpp` only for the three display
   surfaces) and reference a **real** test for each claim (do not mark React elements
   "Tested" by a MAME screenshot test).
6. Regenerate `docs/UI_TEST_COVERAGE_MATRIX.md` and `docs/OS_EXHAUSTIVE_CODE_MATRIX.md` from
   the corrected generators. Downgrade any element with no real test to "⚪ Untested" rather
   than falsely "✅ Tested".
7. **Acceptance:** no generated doc claims coverage that no test provides; `grep google-ui`
   in `scripts/` and `docs/` reflects real ownership only.

### Phase 3 — Define and build the bridge
8. Decide transport (A/B/C above).
9. Specify the contract:
   - **Inbound to core:** `s760_input` events — `{ type, payload }` for buttons, dial deltas,
     mode selects, mouse, note on/off (already emitted by `App.tsx` /
     `EmulatorBridgePanel.tsx`).
   - **Outbound to React:** three framebuffers (CRT RGB, LCD 160×64 mono, Gotek OLED) at a
     defined rate, plus stereo audio.
10. Implement the transport (e.g. MAME Lua plugin WebSocket server) and a React client that
    replaces the stubbed `<pre>` sample in `EmulatorBridgePanel.tsx` with a live connection.
11. React composites the three live buffers into the CRT bezel, LCD cutout, and Gotek OLED
    cutout.
12. **Acceptance:** input in React drives the emulated core; the three real display buffers
    appear inside the React shell; audio plays.

### Phase 4 — Test migration
13. Split `tests/test_interactive_ui.py`:
    - **Keep in MAME harness:** only assertions about authentic display output (CRT/LCD
      content renders, correct geometry) — not drawn chrome.
    - **Move to React tests** (Playwright or Vitest): shell/chrome/navigation (mode tabs,
      rack panel, Gotek bay, knobs, backlight), since those are now React's responsibility.
14. Remove the two obsolete `google-ui` string-grep tests in `tests/test_adversarial_review.py`
    (`test_finding_16`, `test_finding_21`) or convert them into real React tests.
15. Add CI wiring for the React test runner.
16. **Acceptance:** `pytest tests` is green with honest assertions; React UI has its own
    passing test suite.

---

## Files Expected to Change

| Area | File(s) | Change |
| :--- | :--- | :--- |
| MAME driver | `mame-source/src/mame/roland/s760.cpp` | Remove invented GUI renderers; keep only authentic CRT/LCD/OLED buffer output + emulation |
| React UI | `google-ui/src/components/*`, `App.tsx`, `EmulatorBridgePanel.tsx` | Confirm as canonical shell; add live bridge client; composite real buffers |
| Bridge | new MAME Lua plugin (or sidecar), React client | Transport for framebuffers + input |
| Doc gens | `scripts/generate_ui_coverage_matrix.py`, `generate_exhaustive_matrix.py`, `generate_coverage_matrix.py` | Correct source/test provenance |
| Docs | `docs/UI_TEST_COVERAGE_MATRIX.md`, `docs/OS_EXHAUSTIVE_CODE_MATRIX.md`, `README.md` | Regenerate / rewrite UI section |
| Tests | `tests/test_interactive_ui.py`, `tests/test_adversarial_review.py`, new React tests | Split MAME-display vs React-shell assertions |

---

## Risks & Notes

- **Reversibility:** Phase 1 is a pure deletion of invented rendering in one C++ file and is
  fully reversible via git. Do it first and land it green before the bridge work.
- **MAME has no S-760 driver upstream + boot ROM is not dumped.** Per the project steering,
  full emulation is blocked on the IC20 BOOT ROM dump; the interactive display path may need
  to rely on the `core/` libretro host (option C) until the ROM is available. The reviewer
  should confirm whether the live bridge targets MAME or the `core/` host first.
- **Do not** regress the genuine SED1335 / RFSC16A emulation when removing chrome — only the
  invented GUI drawing should be removed, not the hardware controllers.
- **Non-goal:** this plan does not change the audio engine, disk formats, or DSP; it is a UI
  ownership/architecture change only.

---

## Decisions Needed From Reviewer

1. Bridge transport: **A (MAME Lua WebSocket)**, B (sidecar), or C (core/libretro host first)?
2. Confirm Phase 1 (deduplicate now) can land independently before the bridge exists.
3. React test framework for Phase 4: Playwright (end-to-end) vs Vitest (component) — or both?
4. Should the live interactive path target MAME directly, or the `core/` libretro host while
   the IC20 BOOT ROM remains undumped?
