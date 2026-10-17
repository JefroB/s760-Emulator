# Browser UI Test Automation Roadmap

Status: PROPOSED
Scope: `google-ui/` (React shell + composed studio), the S-760 bridge, and the
native MAME runtime driven through the on-screen emulated CRT/mouse.
Goal: one automated UI test suite that runs **headed or headless on demand**,
exercises **all major React UI functions AND the OS functions through the
emulated monitor/mouse**, and is structured so the **same test set can later be
re-created in SoundCheck** (DAW/VST acceptance) with minimal rework.

---

## 1. Why this plan (what already exists)

The harness is already real; this roadmap extends it rather than starting over.

- **Playwright** (`google-ui/playwright.config.ts`, `e2e/`): Chromium project, a
  `webServer` that builds + `vite preview`s the production app, visual snapshots.
  Run `npm run test:e2e`.
- **Vitest** (`src/**/*.test.tsx`, `vitest.config.ts`): component/unit +
  property tests (fast-check). Run `npm run test`.
- **Two backends already wired:**
  - **Mock bridge** — `e2e/fakeBridge.ts` installs a fake `window.WebSocket`
    before load and pushes deterministic CRT/LCD/OLED frames + telemetry through
    the real `S760BridgeClient` decode/blit path. No C++ needed.
  - **Native runtime** — `e2e/native-runtime.spec.ts` connects to a real MAME
    process via `S760_NATIVE_URL`, **clicks the CRT at logical coordinates** and
    verifies OS screens by **pixel-region SHA-256 / FNV hashes**. This is already
    the "drive the OS via the emulated monitor+mouse" pattern.

**Key existing idioms to standardize on:**
- CRT interaction via a normalized logical click: `click(x,y)` maps a 0..160 ×
  0..120 logical grid onto the live CRT canvas bounding box, with settle delays.
- OS-screen assertions via canvas `getImageData` over a fixed region → hash,
  because status text and pixels arrive in separate packets (poll, don't assume).
- Status via `getByRole('status')` text (e.g. `OS ready — Perform Play.`).

---

## 2. Architecture: a backend-swappable test model (the SoundCheck lever)

The single most important design decision is to **separate WHAT each test does
from HOW it reaches the device**, so the SoundCheck port is a backend swap, not a
rewrite.

```
         ┌──────────────────────────────────────────────┐
         │  Test specs (scenarios) — backend-agnostic     │
         │  "load TX81Z, open Patch > TVF, set BPF, play  │
         │   C4, assert screen + audio"                   │
         └───────────────┬───────────────────────────────┘
                         │ uses
         ┌───────────────▼───────────────────────────────┐
         │  S760Driver interface (Page Object + device)   │
         │  boot() loadSample() clickCrt(x,y) press(id)   │
         │  note(n) readScreenRegion(r) readStatus()      │
         │  captureAudio(ms) snapshot()                   │
         └──────┬───────────────────────┬─────────────────┘
                │ impl A                 │ impl B (later)
     ┌──────────▼─────────┐   ┌──────────▼───────────────┐
     │ PlaywrightDriver   │   │ SoundCheckDriver          │
     │ (browser: mock OR  │   │ (DAW/VST host automation) │
     │  native runtime)   │   │                           │
     └────────────────────┘   └───────────────────────────┘
```

- **Scenarios** import only the `S760Driver` interface and a shared **scenario
  library** (ordered steps + expected results as data, not Playwright calls).
- **PlaywrightDriver** implements the interface for the browser, with two modes
  (mock bridge / native runtime) chosen by env.
- **SoundCheckDriver** (Phase 5) implements the same interface against the VST3
  plugin under a DAW/host; the scenario library is reused unchanged.
- Expected OS-screen hashes and audio fingerprints live in a shared
  **golden/fixtures** store keyed by scenario id, so both drivers compare against
  the same ground truth.

Deliverables this creates (new, under `google-ui/e2e/`):
- `driver/S760Driver.ts` — the interface + shared types (logical CRT coords,
  screen regions, button ids, audio capture handle).
- `driver/PlaywrightDriver.ts` — browser implementation (mock + native).
- `scenarios/*.ts` — backend-agnostic scenario definitions (the reusable set).
- `fixtures/` — golden screen hashes, telemetry expectations, audio references.

---

## 3. Headed / headless mechanics (both on demand)

Playwright is headless by default and headed with `--headed`; no code change is
needed. Standardize via npm scripts and an env switch, and make the native URL
and mode explicit:

```jsonc
// package.json scripts (add)
"test:e2e":          "playwright test",                       // headless (default)
"test:e2e:headed":   "playwright test --headed",              // headed window
"test:e2e:debug":    "playwright test --debug",               // inspector, step
"test:e2e:ui":       "playwright test --ui",                  // watch/timeline
"test:e2e:native":   "cross-env S760_TEST_MODE=native playwright test",
"test:e2e:mock":     "cross-env S760_TEST_MODE=mock playwright test"
```

Conventions:
- **Mode selection by env** (`S760_TEST_MODE=mock|native`), read in a Playwright
  fixture that constructs the right `S760Driver`. Default `mock` (no backend
  needed → always runnable in CI).
- **`--headed` / `--debug` / `--ui`** choose the viewing experience for ANY mode;
  they are orthogonal to the backend. A developer debugging an OS-screen click
  runs `test:e2e:native -- --headed --debug`.
- **Slow-mo & tracing** for headed OS debugging: `use: { launchOptions: { slowMo
  } , trace, video }` gated on an env flag so headless CI stays fast.
- **Determinism in headless**: keep the existing "disable all CSS
  animations/transitions + caret" style injection before snapshots; it matters
  more headless where timing is tighter.

---

## 4. Coverage: what "all major functions" means here

Two surfaces, tested at the layer that actually owns each behavior.

### A. React UI / shell functions (own layer = React; backend mocked)
Run against the **mock bridge** so these are fast, deterministic, backend-free.

| Area | Components | What to assert |
| :-- | :-- | :-- |
| Shell composition | OP760Monitor, RolandLCD, GotekBay, RackEars | chrome mounts; 3 live canvases at 640×480 / 160×64 / 128×32 |
| Live surface blit | BridgeContext / useSurfaceCanvas | pushed CRT color reaches pixels (read-back); LCD/OLED mono frames blit |
| Front panel | S760FrontPanel, ShiftButton, ShiftRow | every primary button emits the correct `onEventEmit(type,payload)`; SHIFT buttons emit the mapped chord event; keyboard focus order; tooltips/aria |
| Audition keyboard | AuditionKeyboard | note on/off events emitted; pointer + keyboard activation |
| Bridge panel | EmulatorBridgePanel | connection indicator reflects telemetry; input forwarded to socket |
| Mode navigation | shell nav | mode tabs/panels switch; migration behavior (existing ShellNavigationMigration test) |
| Visual regression | full shell | deterministic full-page snapshot (animations disabled) |

Input→event assertions use the fake socket's `window.__fakeBridge.received`
array (already records control messages the client sends back).

### B. OS functions via the emulated monitor/mouse (own layer = firmware; native runtime)
Run against the **native runtime** (`S760_NATIVE_URL`), driving the real OS by
CRT pixel clicks and verifying by screen-region hashes + status + telemetry.
These are `test.skip` unless the native service is present, so CI stays green.

| OS flow | Steps (via emulated monitor/mouse) | Assertions |
| :-- | :-- | :-- |
| Boot | connect | status `OS ready — Perform Play.`; Perform-Play screen hash |
| Mode switch | Command/Mode menu clicks → each of Perform/Patch/Partial/Sample/Disk/System | each mode's title region hash; menu open/close |
| Disk load | insert sample floppy → Disk > Load → select → Load → return | "Disk Load ready" status; populated patch table hash |
| Patch/Partial edit | open Patch > TVF; set Filter Mode LPF/BPF/HPF/Off; set Resonance | displayed-field region hashes per setting |
| Play / voices | note-on (keyboard area or MIDI), chord | telemetry activeVoices; audio capture non-silent (Phase 3) |
| Save / export | Save session; Export disk | status messages; reconnect retains table hash |
| Restart / restore | Restart (discard) then Restore saved session | reset loses patch; restore matches saved hash |

Screen hashes are **fixtures** (regenerate deliberately when the firmware/render
legitimately changes), not inline magic numbers scattered across specs.

---

## 5. Audio verification (shared with the eventual SoundCheck suite)

The OS-function tests should assert **what the device produced**, not just that a
screen changed. The native runtime already exposes PCM (findings 130–135: demand
render, native stereo PCM 44.1 kHz float). Add to the `S760Driver`:

- `captureAudio(ms)` → returns PCM frames (browser: via the runtime's PCM/render
  endpoint or a WAV the host writes; SoundCheck: the host's render buffer).
- Assertions as **fingerprints**, matching the project's existing discipline:
  non-silence RMS, dominant-frequency / FFT-bin checks for a played note,
  silence in idle windows — NOT bit-exact unless explicitly intended.
- Store expected fingerprints per scenario id in `fixtures/audio/`. The
  SoundCheck port compares the SAME fingerprints, so audio expectations transfer.

This is the main thing that makes the SoundCheck re-creation cheap: scenario +
screen-hash + audio-fingerprint are all backend-neutral data.

---

## 6. Phased delivery

**Phase 0 — Foundation (no new coverage, enables everything)**
- Add the `S760Driver` interface + `PlaywrightDriver` (mock + native) + a
  Playwright fixture that selects the backend from `S760_TEST_MODE`.
- Add the headed/headless/debug npm scripts (Section 3). Add `cross-env`.
- Move the existing `native-runtime.spec.ts` CRT-click + hash helpers into
  `PlaywrightDriver` (clickCrt, readScreenRegion, readStatus) so they are shared.
- Create `fixtures/` with the current known-good hashes migrated out of specs.
- Exit criteria: existing composed-shell + native specs pass through the driver;
  `test:e2e:mock` green with no backend.

**Phase 1 — React UI coverage (mock backend, headless-first)**
- Implement Section 4.A as scenarios: shell composition, surface blit, full front
  panel + SHIFT emission, audition keyboard, bridge panel, mode nav, visual
  snapshot. Property-test the front-panel event emission (reuse fast-check).
- Exit: every major React control has an input→emitted-event (or →pixel) assert;
  runs headless in CI with the mock bridge; visual baseline committed.

**Phase 2 — OS functions via emulated monitor (native backend)**
- Implement Section 4.B scenarios against `S760_NATIVE_URL`. Build the mode-nav
  CRT click map (logical coords per menu target) once, in the driver.
- Capture golden screen-region hashes for each OS screen/field state as fixtures.
- Exit: boot, all six modes, disk load, patch/partial filter edits, save/export,
  restart/restore all pass headed and headless when the native service is up;
  skip cleanly when it is not.

**Phase 3 — Audio assertions**
- Add `captureAudio` + audio fingerprints to the play/voice scenarios (Section 5).
- Exit: played notes assert non-silence + expected pitch; idle asserts silence.

**Phase 4 — CI integration & stability**
- Two CI jobs: `ui-mock` (always, headless, no backend) gates PRs; `ui-native`
  (self-hosted/opt-in, provisions MAME + firmware + `S760_NATIVE_URL`) runs
  nightly / on demand. Mirror the existing backend/frontend split in `ci.yml`.
- Flake controls: retries on native only, trace/video on first retry, per-test
  timeouts sized for firmware latency, deterministic animation disabling.
- Exit: green mock job required on PRs; native job reporting with artifacts.

**Phase 5 — SoundCheck re-creation (the payoff)**
- Implement `SoundCheckDriver` against the VST3 plugin (see
  `s760-soundcheck-testing` skill) satisfying the SAME `S760Driver` interface:
  transport/notes, parameter/UI automation, `captureAudio` from the host render.
- Re-point the Phase 1–3 **scenario library** at the SoundCheck driver; reuse the
  audio fingerprints; screen-hash asserts become plugin-editor equivalents where
  a visual surface exists (or are skipped where the host has no CRT).
- Exit: the agreed scenario set runs under SoundCheck with shared fixtures;
  divergences are documented per scenario, not forked into a second suite.

---

## 7. Conventions & guardrails

- **One source of truth for scenarios.** Specs orchestrate; the step/expectation
  data lives in `scenarios/` so Playwright and SoundCheck consume the same list.
- **Fixtures are deliberate.** Screen hashes and audio fingerprints are
  regenerated via an explicit `--update-*` path and reviewed, never auto-healed.
- **Honesty about layers (project rule).** A React test must not claim to verify
  OS behavior, and an OS test must not pass by asserting React chrome. Each
  assertion names the layer it proves. (This repo has a history of coverage
  matrices claiming OS coverage from React-only or MAME-screenshot tests —
  do not repeat that.)
- **Native tests skip, never fail, when the backend is absent** (as the current
  native spec does), so the default developer/CI run is always green.
- **Keep CRT interaction in the driver.** Specs never compute canvas bounding
  boxes or hashes inline; they call `driver.clickCrt` / `driver.readScreenRegion`.
- **Determinism:** disable animations before snapshots; poll for pixels (status
  and pixels are separate packets); seed any randomness.

---

## 8. First concrete tasks

1. `google-ui/e2e/driver/S760Driver.ts` — interface + types.
2. `google-ui/e2e/driver/PlaywrightDriver.ts` — extract CRT-click/hash/status
   helpers from `native-runtime.spec.ts`; add mock-vs-native construction.
3. `google-ui/e2e/driver/backend.fixture.ts` — Playwright fixture selecting mode
   from `S760_TEST_MODE`.
4. Add npm scripts in Section 3 + `cross-env` devDependency.
5. `google-ui/e2e/fixtures/screens.json` — migrate current native hashes.
6. Port `composed-shell.spec.ts` and `native-runtime.spec.ts` onto the driver as
   the first two scenario files; confirm headed + headless both pass.
