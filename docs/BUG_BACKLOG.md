# S-760 Bug Backlog

Single source of truth for known defects. One row per bug in the table; detailed
entries below. Managed via the `s760-bug-logging` skill — do not hand-reformat;
follow the schema so entries stay machine-greppable.

## Conventions

- **ID:** `BUG-NNN`, zero-padded, monotonically increasing. Never reuse a number.
- **Status:** `OPEN` · `IN-PROGRESS` · `FIXED` · `WONTFIX` · `DUPLICATE` · `CANNOT-REPRODUCE`
- **Severity:** `S1` critical (crash/data loss/boot broken) · `S2` major (feature
  broken, no workaround) · `S3` minor (feature degraded, workaround exists) ·
  `S4` trivial (cosmetic/polish)
- **Area:** one of `ui` · `bridge` · `core` · `mame-driver` · `cpu` · `dsp-audio` ·
  `disk` · `midi` · `build` · `tests` · `docs` · `hardware` (extend as needed).
- **Dates:** ISO `YYYY-MM-DD`.
- Keep the summary table and the per-bug detail section in sync (every table row
  has a matching `### BUG-NNN` entry).
- Fixed/closed bugs stay in the file (do not delete) for history; set their
  Status and `Resolved` date.

## Summary

| ID | Status | Sev | Area | Summary | Opened | Resolved |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| BUG-001 | OPEN | S2 | cpu | MCS-96 PUSHA/POPA/PUSHF/POPF are stack-neutral no-ops (don't save PSW/regs) — boot workaround, not real semantics | 2026-10-11 | |
| BUG-002 | OPEN | S2 | cpu | BMOVI (0xCD) still has the duplicate operand-fetch bug (same class as fixed BMOV/CMPL); unaudited | 2026-10-11 | |
| BUG-003 | OPEN | S2 | dsp-audio | Unrecognized sample loop/direction mode flags are silently dropped → valid patches can play silent | 2026-10-11 | |
| BUG-004 | OPEN | S2 | midi | IC4 MIDI vector response is an inferred/forced model; no real arbitration/FIFO, overrun bytes dropped | 2026-10-11 | |
| BUG-005 | OPEN | S3 | dsp-audio | Static HP filter fails the 1% accuracy target (1.59%); moving/sweep filter response unmatched | 2026-10-11 | |
| BUG-006 | OPEN | S3 | disk | Native floppy save/export: whole-wave-RAM compare differs by 347 name/high-mem bytes | 2026-10-11 | |
| BUG-007 | OPEN | S2 | tests | Generated coverage matrices claim OS/UI coverage from tests that don't exercise that layer (false provenance) | 2026-10-11 | |
| BUG-008 | OPEN | S3 | build | core/CMakeLists.txt omits s760_core.cpp — the "shared DSP engine" is not actually compiled/linked | 2026-10-11 | |
| BUG-009 | FIXED | S2 | core | Checkpoint save/load executed inside an emulated-timer callback → restored empty patch table | 2026-10-11 | 2026-10-11 |
| BUG-010 | FIXED | S3 | build | Desktop package omitted MAME full license texts and had no development/release audit gate | 2026-10-11 | 2026-10-11 |
| BUG-011 | FIXED | S3 | docs | README claimed a project-wide BSD license and linked to a nonexistent LICENSE | 2026-10-11 | 2026-10-11 |
| BUG-012 | FIXED | S3 | docs | Boot-ROM setup asserted unsupported download permissions and described verified boot as unqualified | 2026-10-11 | 2026-10-11 |
| BUG-013 | FIXED | S2 | core | Failed native plugin restore allowed a fresh instance to resume an uncertain timeline | 2026-10-11 | 2026-10-11 |
| BUG-014 | FIXED | S2 | mame-driver | SCSI checkpoint omits transfer buffer and media state | 2026-10-11 | 2026-10-11 |
| BUG-015 | OPEN | S2 | disk | SCSI WRITE accepts payload but does not modify target media | 2026-10-11 | |
| BUG-016 | FIXED | S3 | build | Package notice inventory omits actual frozen dependencies and nested vendor DLL attribution | 2026-10-11 | 2026-10-11 |
| BUG-017 | FIXED | S3 | build | Native source archive filter misses forbidden upstream test-media extensions | 2026-10-11 | 2026-10-11 |
| BUG-018 | FIXED | S3 | build | Package audit skips nested files named PACKAGE-AUDIT.json | 2026-10-11 | 2026-10-11 |

<!-- NEXT-ID: BUG-019 -->

## Details

<!-- Add one "### BUG-NNN" block per bug, newest at the top of this section. -->

### BUG-018 — Audit report exclusion applies to nested files

- **Status:** FIXED
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** distribution gate review

**Summary:** The package scan skipped every file named PACKAGE-AUDIT.json, allowing a nested added file to escape the complete-tree check.
**Repro:** Add scripts/PACKAGE-AUDIT.json to a reviewed package.
**Expected:** The changed tree must fail qualification.
**Actual:** The old basename-only exclusion omitted the file from the manifest.
**Evidence:** Parameterized exact-tree regression includes this nested path.
**Resolution:** Exclude only the root generated report; nested names are hashed and checked like every other file. Release status is still recomputed from actual files, never read from a package-supplied report.

### BUG-017 — Native source media filter misses AIFF

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-11
- **Reported by:** final distribution source archive scan

**Summary:** Native source selection excludes WAV but did not apply the complete private-media suffix policy. An upstream FLAC AIFF test fixture was included in the candidate archive.

**Repro:** Scan native-source-145.zip with the package PRIVATE_SUFFIXES policy; 3rdparty/flac/test/foreign-metadata-test-files/AIFF-ID3.aiff fails.
**Expected:** The source candidate excludes every prohibited media suffix.
**Actual:** Final qualification correctly stops before authoring an approved manifest.
**Evidence:** Finding 145; final archive validation assertion. No Roland leak was identified.
**Notes:** Regenerate the archive with the full suffix policy and repeat clean-source validation.

**Resolution:** The source filter now covers every prohibited media suffix. All 27323 final source entries passed integrity/media scans, and that exact extracted archive rebuilt from scratch successfully. Final native boot/audio and desktop tests pass; 241 backend regressions pass.

### BUG-016 — Build-environment inventory misses actual bundled components

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-11
- **Reported by:** distribution qualification audit

**Summary:** The fixed Python notice list omits dependencies actually frozen into the desktop executable, including Jinja2 and MarkupSafe. Parent pywebview attribution also does not describe the separate Microsoft WebView2 DLL license.

**Repro:** Compare the fresh standalone build's PYZ-00.toc and COLLECT-00.toc against DEPENDENCY-INVENTORY.json. Observe jinja2 modules and WebView2 binaries without corresponding complete component-level notice accounting.

**Expected:** Identify the actual bundled inputs and copy available notices; retain explicit unresolved vendor obligations.
**Actual:** Inventory describes the build environment and can pass development checks with omitted bundled-component notices.

**Evidence:** Finding 145; private distribution-145 build records. New distribution inventory tests exercise notice discovery, binary drift, unknown binaries and unsafe output paths.

**Notes:** Public release remains blocked while missing third-party rights/source evidence is unresolved.

**Resolution:** Actual COLLECT/PYZ inventory and Vite module inventory identify shipped components. Exact upstream WebView2/Python checks, proxy_tools source/license correction and supplemental vendor notices close the omissions. Runtime DLL copies with unresolved package provenance are excluded. 241 backend regressions, frontend build/type checks, clean-source MAME rebuild and final desktop/native acceptance pass.

### BUG-015 — SCSI WRITE discards completed payload

- **Status:** OPEN
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-11
- **Reported by:** SCSI device checkpoint acceptance

**Summary:** Existing WRITE(6)/WRITE(10) paths allocate a data buffer and acknowledge completion without copying it into the target disk image.

**Repro:** `python scripts/verify_scsi_checkpoint.py --state-dir <fresh-private-dir>` writes a generated 512-byte payload to LBA 0, then READ(6) observes the previous disk bytes. The device probe reports `writeback_supported: false`. It does not use or alter user media.

**Expected:** A supported successful disk WRITE changes the target sector, or reports a supported failure.
**Actual:** DATA_OUT completion moves to STATUS, but target contents remain unchanged.

**Evidence:** [SCSI state validation](condensed/validation/native-scsi-state-2026-10-11.json); finding 144. Source: `scsi_w` DATA_OUT completion and `scsi_execute_cdb` WRITE cases.

**Notes:** Separate media-writeback objective; snapshot tests establish restoration of implemented state, not working firmware SCSI Save or hardware protocol fidelity. Needs range/read-only/sense handling and firmware save/reload acceptance.

### BUG-014 — SCSI checkpoint loses in-flight response

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** mame-driver
- **Opened:** 2026-10-11
- **Reported by:** isolated SCSI checkpoint test

**Summary:** Controller registers restore, but dynamic transfer bytes and media were omitted.

**Repro:** `python scripts/verify_scsi_checkpoint.py --state-dir <private-dir>` issues INQUIRY, consumes 8 bytes, saves, replaces the buffer using REQUEST SENSE, then restores and reads the remaining 28 bytes. This is a device-level test, not firmware workflow acceptance.

**Expected:** Remaining response is byte-exact after restore.
**Actual:** Red test reports `SCSI response bytes changed after restore`.

**Evidence:** Private scsi-red2-144/result.json; finding 144.

**Resolution:** Registered stable maximum-transfer storage, device metadata and startup-sized media buffers. Partial CDB/data-in/data-out and cold media tests pass; native cold scheduled audio/displays and all-rate plugin replay pass. [Evidence](condensed/validation/native-scsi-state-2026-10-11.json).

### BUG-013 — Failed native plugin restore allowed processing

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** core
- **Opened:** 2026-10-11
- **Reported by:** native exported-factory state acceptance

**Summary:** The new plugin state implementation only faulted an existing stream after a native apply failure. A fresh instance had no stream and could start processing after rejection.

**Repro:** Run `s760_native_factory_tests.exe . <private-state-dir> --state 44100`. The test wraps an invalid one-byte native checkpoint in a valid archive and loads it into a fresh native instance.

**Expected:** Processing remains rejected until a complete valid restore succeeds.
**Actual:** The red regression failed with `Failed native restore allowed processing`.

**Evidence:** Finding 143; private `state-failure-red-143.log`.

**Resolution:** Explicit failure latch set before worker shutdown and cleared only after a complete valid restore. Exported native-module tests pass at 44100/48000/96000 Hz, including rejection after invalid native payload and successful recovery with a valid archive. See [state evidence](condensed/validation/native-plugin-state-2026-10-11.json).

### BUG-012 — Boot-ROM setup guidance had unsupported permissions and stale status

- **Status:** FIXED
- **Severity:** S3
- **Area:** docs
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT firmware setup audit

**Summary:** The boot README described third-party downloads as lawful for
hardware owners without evidence of that permission. Its version note also
called IC15 IC20 and said the now-tested v1.11/v2.24 boot pair was unverified.

**Repro:** Inspect the previous `roms/BOOT/README.md` sections “Where to obtain
it” and “Version note”; compare with the native boundary acceptance record.
This is a documentation audit, not a new hardware test.

**Expected:** State project distribution policy and verified firmware identity
without granting rights to third-party firmware or contradicting native tests.
**Actual:** Unsupported permission claims, obsolete qualification status and
incorrect chip labels remained in the setup instructions.

**Evidence:** [Firmware setup](FIRMWARE_SETUP.md),
[native acceptance](condensed/validation/native-boundary-2026-10-11.json).
Finding 141. Local SHA-256 checks match both documented firmware identities.

**Resolution:** Replaced download recommendations with user-supplied firmware
instructions, removed blanket permission claims, corrected IC15 labels and
linked current native evidence. Working-tree documentation change only.

**Notes:** No license grant was created and no Roland binary was distributed.

### BUG-011 — README implied a nonexistent project-wide license

- **Status:** FIXED
- **Severity:** S3
- **Area:** docs
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT native-boundary source/package audit

**Summary:** The README BSD badge linked to a nonexistent root LICENSE and the
footer described the whole project as BSD-3-Clause, despite MAME's separate
whole-engine license and no explicit project-wide license file.

**Repro:** Inspect the old README license badge/footer, `Test-Path LICENSE`,
`mame-source/COPYING`, and the header of `mame-source/src/mame/roland/s760.cpp`.
This is a source-documentation audit, not a runtime or hardware test.

**Expected:** Preserve per-file notices and identify the actual distribution
status without implying a nonexistent project-wide grant.
**Actual:** Badge link was broken and the blanket license statement overstated
the license scope established by the checkout.

**Evidence:** [Boundary assessment](NATIVE_BOUNDARY_QUALIFICATION.md), finding 140.

**Resolution:** Replaced the badge with distribution status and rewrote the
footer to distinguish driver, complete MAME engine and missing project license.
No new license grant was created. Changes remain in the working tree.

**Notes:** Public distribution remains blocked; correcting prose does not resolve
project licensing or dependency/source delivery review.

### BUG-010 — Desktop package omitted full MAME licenses

- **Status:** FIXED
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT inspection of the finding 139 desktop package

**Summary:** The builder retained COPYING but omitted its referenced full
`docs/legal` texts. It also had no artifact identity/private-media audit or
enforced distinction between development builds and qualified releases.

**Repro:** Inspect the original `scripts/build_standalone.ps1` and the package's
`mame-source/docs/legal` directory; the latter was absent. No native execution
is required to reproduce this packaging defect.

**Expected:** Preserve all upstream MAME legal texts, report package identity,
exclude private media, and avoid presenting unqualified artifacts as releases.
**Actual:** Only COPYING was included; no post-assembly audit ran.

**Evidence:** `tests/test_package_audit.py` (7 tests),
`docs/ic20-hle-findings/chatGPT-work/package-audit-140.log` (private log), and
[boundary assessment](NATIVE_BOUNDARY_QUALIFICATION.md). Finding 140.

**Resolution:** Added notice collection and a post-assembly audit, exact runtime
and legal-text identity checks, private-fixture checks and development-only
labels. Release requests fail explicitly. All seven regressions pass, including
missing/changed licenses and binary, renamed firmware, session leakage and a
forged release report. Changes remain in the working tree.

**Notes:** Build-environment dependency inventory is not complete embedded-DLL
attribution or a license-compatibility decision; release review remains required.

### BUG-009 — Checkpoint save/load ran inside an emulated-timer callback (restored empty patch table)

- **Status:** FIXED
- **Severity:** S2
- **Area:** core
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** native-runtime browser regression (finding 139)

**Summary:** The native runtime's buffer checkpoint (`machine:buffer_save/load`)
could execute inside an emulated timer callback, which MAME's Lua binding warns
is a synchronization/timer hazard. Result: a real browser-visible defect — session
restore produced an **empty patch table** or failed to advance.

**Repro:** Native Studio, real Chromium, normal speed: firmware load → Save
session → Restore saved session; the restored CRT patch-table region did not
match the saved hash (3384624565).

**Expected:** restored patch table pixels identical to the saved session.
**Actual:** empty/partial patch table after restore.

**Resolution:** Runtime now handles checkpoint commands only from a **paused
periodic callback** and skips the first periodic callback after each pause (a
"pause grace" so the old timer returns before save/load). Deferring to the
periodic hook alone was insufficient. Fixed in finding 139; browser + native
PCM/display + MIDI-replay regressions pass. Caveat: the grace is a workaround
around MAME's frame-vs-periodic hook ordering, not a redesign.

**Evidence:** `chatGPT-work/session-grace-139.log`, `browser-test4-139.log`,
`regression-complete-139.log` (findings area, git-ignored).

**Notes:** Lua identity changed, so pre-139 checkpoint archives are deliberately
rejected (no migration). Related: findings 134/135 (checkpoint design), BUG-004.

### BUG-008 — Shared DSP engine source (`s760_core.cpp`) is not compiled into the library

- **Status:** OPEN
- **Severity:** S3
- **Area:** build
- **Reported by:** condensed docs 06/10 (code audit)

**Summary:** `core/include/s760/s760_core.hpp` + `core/src/s760_core.cpp` exist,
but `core/CMakeLists.txt`'s library source list **omits `s760_core.cpp`**, and
MAME defines its own separate `s760_sound_device`. So the "MAME and plugins share
one DSP engine" claim is false — the standalone core is not actually linked.

**Repro:** inspect `core/CMakeLists.txt` source list; `s760_core.cpp` absent.
**Expected:** either the shared engine is compiled/linked end-to-end, or docs/
claims stop asserting a shared engine.
**Actual:** reference model exists but is dead code; two DSP implementations.

**Notes:** fixing means explicit integration + compiled end-to-end verification,
not just adding another reference model. Low user impact today; it is a
correctness/architecture-claim defect.

### BUG-007 — Generated coverage matrices claim coverage from tests that don't exercise that layer

- **Status:** OPEN
- **Severity:** S2
- **Area:** tests
- **Reported by:** UI consolidation plan/assessment (condensed 07/08)

**Summary:** `docs/*_MATRIX.md` generators attribute UI elements to React
components and mark them "✅ Tested" by `tests/test_interactive_ui.py`, which
actually boots MAME and asserts on MAME-rendered screenshots — it never loads or
exercises the React components. The matrices (and README badges) therefore claim
coverage that no test provides. Symmetric risk: OS behaviour "verified" by
React-only or screenshot tests.

**Repro:** compare `scripts/generate_ui_coverage_matrix.py` /
`generate_exhaustive_matrix.py` outputs against the referenced test bodies.
**Expected:** each matrix row names a test that actually exercises that layer;
untested elements marked "⚪ Untested."
**Actual:** false "✅ Tested" provenance; 100% badges unsupported.

**Notes:** This is the project's recurring "honesty about layers" hazard; the UI
test automation roadmap (`docs/UI_TEST_AUTOMATION_ROADMAP.md`) is designed to fix
it by asserting per-layer. Fix the generators + regenerate, downgrade false rows.

### BUG-006 — Native floppy save/export: whole-wave-RAM compare differs by 347 bytes

- **Status:** OPEN
- **Severity:** S3
- **Area:** disk
- **Reported by:** finding 128

**Summary:** The decoded native OS Save/export path writes the sample payloads
correctly (all 13 sample payloads, 119,808 bytes for the 88-key patch, match
source exactly), but a whole-wave-RAM comparison still differs by **347 bytes**
around 0x1FA410 (name / high-memory records). The finding records
`whole_wave_ram_equal=false` and makes no session-equivalence claim.

**Repro:** native runtime, load patch → firmware Save/export → fresh machine
reload → compare entire wave RAM to source.
**Expected:** byte-exact whole-wave-RAM session equivalence.
**Actual:** sample bytes identical; 347 name/high-mem record bytes differ.

**Notes:** bus-cycle arbitration unimplemented; no library writeback/formatting.
"Dirty" tracking is controller-write based, not firmware Save completion. Related:
findings 128/129.

### BUG-005 — Static HP filter fails the 1% accuracy target; moving/sweep filter unmatched

- **Status:** OPEN
- **Severity:** S3
- **Area:** dsp-audio
- **Reported by:** findings 87–95, 108

**Summary:** The fitted filter model matches static LP (−45/−58 dB) and static
BP (−60.84 dB, <1% RMS), but static **HP residual is 1.59%** — it does NOT pass
the 1% RMS threshold. Separately, the **moving/sweep** resonant response does not
yet match hardware; the filter topology is not uniquely identified.

**Repro:** compare the opt-in filter audition against the RoboSampler static HP
capture (cutoff 428, damping 85) and the moving-sweep captures.
**Expected:** HP within ~1% RMS; moving sweep matches hardware.
**Actual:** HP 1.59%; moving-sweep mismatch unresolved.

**Notes:** opt-in/diagnostic path only (`S760_NATIVE_LPF_MONITOR` etc.), not the
default audio. Fixed-point width, saturation, resonance feedback law and update
timing remain open. This is a fidelity gap in an experimental feature, hence S3.

### BUG-004 — Experimental IC4 MIDI vector response is inferred/forced; no real arbitration or FIFO

- **Status:** OPEN
- **Severity:** S2
- **Area:** midi
- **Reported by:** findings 73/74

**Summary:** MIDI receive works only under the opt-in `S760_IC4_MIDI_EXPERIMENT`
path, which **substitutes the external-interrupt vector low byte** (source6 →
0138) based on an inferred model of IC4 behaviour — not measured hardware. A
one-byte latch stands in for the real receiver: a second byte arriving before
consumption is logged as an **overrun and dropped**. Source priority, latching,
reassertion under concurrent sources, FIFO depth and MIDI-out are unestablished.

**Repro:** `S760_IC4_MIDI_EXPERIMENT=1`, send MIDI faster than the firmware
consumes it → dropped bytes; concurrent FDC + MIDI interrupts → unverified
arbitration.
**Expected:** faithful IC4 receive/interrupt behaviour (proper FIFO/overrun,
real vector/arbitration).
**Actual:** inferred vector substitution + single-byte latch with silent overrun
drop; disabled by default so default build cannot receive MIDI at all.

**Notes:** three-voice and 24-voice polyphony were demonstrated through this
experimental path. Do NOT promote to default emulation until real IC4
arbitration/buffering is resolved. Related: BUG-009.

### BUG-003 — Unrecognized sample loop/direction mode flags are silently dropped

- **Status:** OPEN
- **Severity:** S2
- **Area:** dsp-audio
- **Reported by:** findings 101/102/104

**Summary:** The native wave monitor explicitly accepts only control high-nibble
4 and forward inclusive looping, and **rejects/ignores other loop & direction
mode flags** (e.g. reverse, alternate, one-shot variants, flags like E000). A
valid patch using an unsupported mode can therefore play **silent** even though
the filter/pitch paths match well — a silent-failure that can hide behind
apparent success.

**Repro:** native audio audition with a patch whose sample mode byte selects a
non-forward loop/direction; the voice produces no output.
**Expected:** all seven documented loop/direction modes render (finding 103/104
decoded them: Forward End, Forward Release, One Shot, Forward One Shot, Alternate,
Reverse One Shot, Reverse Loop; boundaries end-exclusive, reverse −4 offset).
**Actual:** unrecognized modes skipped → silent voice.

**Notes:** finding 104 implements the seven modes behind `S760_NATIVE_LOOP_MONITOR`
(opt-in); the default monitor still skips them. Physical interrupt timing/ack and
fractional-pitch coverage remain provisional.

### BUG-002 — BMOVI (0xCD) retains the duplicate operand-fetch bug; unaudited

- **Status:** OPEN
- **Severity:** S2
- **Area:** cpu
- **Reported by:** findings 64/65 (BMOV/CMPL audit)

**Summary:** The generated MCS-96 core double-fetched operand bytes for block ops
(after `direct_2w` already fetched them), consuming the following instruction.
This was fixed for **BMOV (0xC1)** and **CMPL (0xC5)**, but **BMOVI (0xCD) still
has the same duplicate-fetch pattern** and is explicitly unaudited; its KB
applicability / interrupt semantics must not be assumed from later 196 variants.

**Repro:** execute a BMOVI instruction path (not covered by the current TX81Z
load path) → operand over-fetch corrupts the following instruction.
**Expected:** BMOVI fetches operands once, per the 80C196KB User's Guide.
**Actual:** duplicate fetch (latent; not yet hit by exercised firmware paths).

**Notes:** audit separately with an isolated CPU fixture before any path uses it.
Fixed siblings: BMOV, CMPL (verified by fixtures).

### BUG-001 — MCS-96 PUSHA/POPA/PUSHF/POPF are stack-neutral no-ops

- **Status:** OPEN
- **Severity:** S2
- **Area:** cpu
- **Reported by:** findings 23/25 (boot bring-up)

**Summary:** In `mcs96ops.lst`, PUSHA/POPA are stack-neutral and PUSHF clears
PSW + checks IRQ while POPF leaves PSW/SP — i.e. the flag/register save-restore
instructions **do not actually save/restore** PSW or the register set. This is a
deliberate boot-compatibility workaround (a real two-word PUSHA/PUSHF derails the
OS at 0xB93A / 0xE080 because routines PUSH at entry and plain-RET at exit with no
matching POP), NOT correct Intel architectural behaviour.

**Repro:** replace the stubs with real PUSHA/PUSHF semantics → OS derails during
boot (RET returns to a PSW-as-address). Current workaround = net-zero stack.
**Expected:** architecturally correct PUSHA/POPA/PUSHF/POPF.
**Actual:** stack-neutral no-ops; PSW/INT_MASK1 not preserved across the pair.

**Notes:** confined to the flat baseline per the native-mode notes; native 196KB
interrupt work added INT_MASK1/INT_PEND1 but the stack-op stubs remain. Do NOT
"correct" without re-proving the 0xB93A / 0xE080 paths. Any instruction audit
(see BUG-002) should cover these.
