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
| BUG-001 | FIXED | S2 | cpu | Native flag-stack behavior verified; stack-neutral stubs are confined to legacy flat mode | 2026-10-11 | 2026-10-11 |
| BUG-002 | FIXED | S2 | cpu | BMOVI (0xCD) duplicate operand fetch fixed; interrupt semantics remain unaudited | 2026-10-11 | 2026-10-11 |
| BUG-003 | FIXED | S2 | dsp-audio | Seven loop modes verified in the supported 44.1 kHz native profile | 2026-10-11 | 2026-10-11 |
| BUG-004 | OPEN | S2 | midi | IC4 MIDI vector arbitration and buffering remain inferred; latch overruns drop bytes | 2026-10-11 | |
| BUG-005 | OPEN | S3 | dsp-audio | Static HP filter fails the 1% accuracy target (1.59%); moving/sweep filter response unmatched | 2026-10-11 | |
| BUG-006 | OPEN | S3 | disk | Native floppy save/export: whole-wave-RAM compare differs by 347 name/high-mem bytes | 2026-10-11 | |
| BUG-007 | FIXED | S2 | tests | Generated coverage matrices now separate unverified inventory from scoped test evidence | 2026-10-11 | 2026-10-11 |
| BUG-008 | OPEN | S3 | build | core/CMakeLists.txt omits s760_core.cpp — the "shared DSP engine" is not actually compiled/linked | 2026-10-11 | |
| BUG-009 | FIXED | S2 | core | Checkpoint save/load executed inside an emulated-timer callback → restored empty patch table | 2026-10-11 | 2026-10-11 |
| BUG-010 | FIXED | S3 | build | Desktop package omitted MAME full license texts and had no development/release audit gate | 2026-10-11 | 2026-10-11 |
| BUG-011 | FIXED | S3 | docs | README claimed a project-wide BSD license and linked to a nonexistent LICENSE | 2026-10-11 | 2026-10-11 |
| BUG-012 | FIXED | S3 | docs | Boot-ROM setup asserted unsupported download permissions and described verified boot as unqualified | 2026-10-11 | 2026-10-11 |
| BUG-013 | FIXED | S2 | core | Failed native plugin restore allowed a fresh instance to resume an uncertain timeline | 2026-10-11 | 2026-10-11 |
| BUG-014 | FIXED | S2 | mame-driver | SCSI checkpoint omits transfer buffer and media state | 2026-10-11 | 2026-10-11 |
| BUG-015 | FIXED | S2 | disk | SCSI WRITE now updates private media; protection, ranges and checkpoint recall tested | 2026-10-11 | 2026-10-11 |
| BUG-016 | FIXED | S3 | build | Package notice inventory omits actual frozen dependencies and nested vendor DLL attribution | 2026-10-11 | 2026-10-11 |
| BUG-017 | FIXED | S3 | build | Native source archive filter misses forbidden upstream test-media extensions | 2026-10-11 | 2026-10-11 |
| BUG-018 | FIXED | S3 | build | Package audit skips nested files named PACKAGE-AUDIT.json | 2026-10-11 | 2026-10-11 |
| BUG-019 | FIXED | S3 | ui | Malformed native session JSON escapes the display event handler | 2026-10-11 | 2026-10-11 |
| BUG-020 | FIXED | S2 | ui | Gated C++ WebView2 backend reports success without creating an editor | 2026-10-11 | 2026-10-11 |
| BUG-021 | FIXED | S2 | ui | VST3 view exposes a private tick but installs no UI frame timer | 2026-10-11 | 2026-10-11 |
| BUG-022 | FIXED | S2 | bridge | Live editor frame polling starves native plugin audio | 2026-10-11 | 2026-10-11 |
| BUG-023 | FIXED | S2 | bridge | C++ bridge accepts panel/pointer controls without routing them | 2026-10-11 | 2026-10-11 |
| BUG-024 | FIXED | S1 | bridge | VST3 local interfaces are ABI-incompatible with SDK hosts | 2026-10-11 | 2026-10-11 |
| BUG-025 | FIXED | S2 | ui | Embedded live CRT clicks hit demo handlers; native held mouse input missing | 2026-10-11 | 2026-10-11 |
| BUG-026 | FIXED | S2 | ui | SoundCheck editor clips the rack and shows unused native CRT rows | 2026-10-11 | 2026-10-11 |
| BUG-027 | FIXED | S2 | ui | Embedded rack uses demo controls and empty Gotek display; Shift chords inaccessible | 2026-10-11 | 2026-10-11 |
| BUG-028 | FIXED | S2 | mame-driver | Native LCD stays blank despite firmware status-message writes | 2026-10-11 | 2026-10-11 |
| BUG-029 | FIXED | S2 | bridge | Native plugin media pulse released before driver acknowledgement | 2026-10-11 | 2026-10-11 |
| BUG-030 | FIXED | S2 | bridge | Absolute mouse position drifts after firmware Menu/Exit interaction | 2026-10-11 | 2026-10-11 |
| BUG-031 | FIXED | S2 | bridge | Plugin checkpoints omit media browser state and retain stale insertion labels | 2026-10-11 | 2026-10-11 |
| BUG-032 | FIXED | S3 | ui | Plugin editor discovery ignores configured native root | 2026-10-11 | 2026-10-11 |
| BUG-033 | FIXED | S2 | bridge | Uninitialized LCD registers stall fresh runtime startup and cold restoration | 2026-10-11 | 2026-10-11 |
| BUG-034 | FIXED | S3 | tests | Shift synchronous-dispatch test incorrectly measures wall-clock host scheduling | 2026-10-11 | 2026-10-11 |
| BUG-035 | FIXED | S2 | bridge | Initial output knob used digital override API for a MAME adjuster | 2026-10-11 | 2026-10-11 |
| BUG-036 | FIXED | S3 | bridge | Worker display cache omits output-level metadata | 2026-10-11 | 2026-10-11 |
| BUG-037 | FIXED | S3 | tests | Rack recall test reused monotonic WAV offsets after guest-time rewind | 2026-10-11 | 2026-10-11 |
| BUG-038 | FIXED | S3 | tests | Native verifier gives normal-speed 35-second wait only 30 seconds | 2026-10-12 | 2026-10-12 |
| BUG-039 | FIXED | S3 | bridge | Missing source sample path or startup error blocks self-contained session recovery | 2026-10-12 | 2026-10-12 |
| BUG-040 | FIXED | S2 | disk | Floppy protection, firmware Save rejection and cold recall qualified | 2026-10-12 | 2026-10-12 |
| BUG-041 | FIXED | S2 | disk | Native 720KB firmware formatting, protected rejection and Save/reload qualified | 2026-10-12 | 2026-10-12 |
| BUG-042 | FIXED | S2 | bridge | Standalone periodic/normal-close recovery preserves dirty media and manual saves | 2026-10-12 | 2026-10-12 |
| BUG-043 | FIXED | S2 | mame-driver | Observed A7 wave-to-RAM DMA completes firmware sampling postprocessing | 2026-10-12 | 2026-10-12 |
| BUG-044 | FIXED | S1 | ui | Standalone shares approved rack/CRT, restores Gotek and removes UI clutter | 2026-10-12 | 2026-10-12 |
| BUG-045 | FIXED | S2 | dsp-audio | Bounded control ingress now sustains physical standalone stereo recording | 2026-10-12 | 2026-10-12 |
| BUG-046 | FIXED | S3 | dsp-audio | Output-only ASIO detects an active driver that stops consuming queued PCM | 2026-10-12 | 2026-10-12 |
| BUG-047 | FIXED | S3 | dsp-audio | Five-minute supported ASIO playback passes with explicit transport buffering | 2026-10-12 | 2026-10-12 |
| BUG-048 | FIXED | S2 | dsp-audio | ASIO counts all missing frames while waiting to re-prime output | 2026-10-12 | 2026-10-12 |
| BUG-049 | FIXED | S2 | dsp-audio | Audio errors pause native time; actual driver reopening preserves the machine | 2026-10-12 | 2026-10-12 |
| BUG-050 | FIXED | S2 | dsp-audio | Windows endpoint mappings require MAME's output-node prefix | 2026-10-12 | 2026-10-12 |
| BUG-051 | CANNOT-REPRODUCE | S3 | build | One initial windowed test-package launch failed before session publication | 2026-10-12 | 2026-10-12 |
| BUG-052 | FIXED | S2 | midi | Native VST3 lacks controller mapping and ignores host controller queues | 2026-10-12 | 2026-10-12 |
| BUG-053 | FIXED | S3 | tests | Private SoundCheck test processor drops pending parameter automation | 2026-10-12 | 2026-10-12 |
| BUG-054 | CANNOT-REPRODUCE | S3 | ui | Knob indicator visual defect; fix required before shipping, shared frontend impact suspected | 2026-10-12 | |
| BUG-055 | FIXED | S3 | bridge | Native VST3 now reports potentially infinite sustained-voice tail | 2026-10-12 | 2026-10-12 |

<!-- NEXT-ID: BUG-056 -->

## Details

### BUG-055 — Native sampler reports zero tail

- **Status:** FIXED
- **Severity:** S3
- **Area:** bridge
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Milestone 4 SDK host qualification

**Repro:** Run the independent Steinberg SDK probe with valid native configuration. The new `getTailSamples()==kInfiniteTail` assertion fails on the existing module.

**Expected:** Report a potentially infinite tail because looped or sustained voices may continue indefinitely.

**Actual:** Native `getTailSamples()` returns zero, potentially allowing a host to truncate active voices during tail rendering.

**Evidence:** SDK probe failure: `sampler must report potentially infinite voice tail`; core/src/s760_vst3_plugin.cpp returns zero unconditionally.

**Resolution:** Native instrument returns SDK kInfiniteTail. Independent SDK regression and actual SoundCheck report pass; sustained playback and note-off release remain functional. See [rendering qualification](NATIVE_VST3_RENDERING.md). The historical core's tail behavior is unchanged.

### BUG-054 — Knob indicator visual defect

- **Status:** CANNOT-REPRODUCE
- **Severity:** S3
- **Area:** ui
- **Opened:** 2026-10-12
- **Reported by:** User

**Summary:** User reports a visual defect in the knob indicators. Functionality is unaffected. A fix is required before shipping; impact on both VST3 and standalone is suspected, not yet verified.

**Repro:** Pending the exact visual symptom, affected knob(s), and position or interaction that reveals it. No independent reproduction yet.

**Expected:** Knob indicators render correctly throughout their travel in both applications.

**Actual:** Indicator appearance is incorrect according to the user report; precise appearance has not yet been described.

**Evidence:** User report on 2026-10-12; no screenshot or measured reproduction attached.

**Notes:** S3 per user classification. CANNOT-REPRODUCE records missing reproduction details, not dismissal or release acceptance. Keep this unresolved as a pre-shipping requirement; verify both frontends when fixing.

### BUG-053 — Private SoundCheck automation never reaches processor

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-12
- **Closed:** 2026-10-12
- **Reported by:** Native VST3 controller qualification

**Repro:** Send `set_param`, then `process_test_chunk` in the private native SDK QA backend. Pending changes were stored, but the test call supplied null `inputParameterChanges`.

**Expected:** Real SDK parameter queues reach the processor once, on the next block.

**Resolution:** Private host uses SDK ParameterChanges and consumes pending updates on block0. Original independent SoundCheck checkout unchanged. Measured CC7/64/123 audio effects pass. The [reproduction patch](condensed/validation/soundcheck-native-automation-2026-10-12.patch) and [evidence](condensed/validation/milestone-4-midi-2026-10-12.json) preserve the supported QA profile.

### BUG-052 — Native VST3 drops host MIDI controllers

- **Status:** FIXED
- **Severity:** S2
- **Area:** midi
- **Opened:** 2026-10-12
- **Closed:** 2026-10-12
- **Reported by:** Independent SDK MIDI mapping regression

**Summary:** Native VST3 exposes no IMidiMapping and ignores inputParameterChanges, so host sustain, pitch bend and panic cannot reach original firmware. Notes alone are delivered.

**Repro:** Build/run s760_vst3_sdk_tests against the concrete native module with valid firmware configuration. Query controller for the actual SDK IMidiMapping IID.

**Expected:** Stable channel-specific assignments and bounded sample-offset controller delivery.

**Actual:** Query fails at `native MIDI mapping interface`; process_native only handles note events.

**Evidence:** Independent Steinberg-header probe and core/src/s760_vst3_plugin.cpp inspection.

**Resolution:** Added actual SDK-compatible IMidiMapping, hidden channel-specific CC/bend aliases and bounded queue-point merging into the native worker clock. SDK ABI/queue/overflow checks pass; paced varying-block controller PCM matches independent MIDI bytes exactly; SoundCheck volume/sustain/CC123 release effects pass. Fixed for the documented nonzero-block transport profile. Configured audible bend, reset semantics and CC120 behavior are explicitly not inferred. [Contract and limits](NATIVE_VST3_MIDI.md).

### BUG-051 — Initial windowed package startup exception

- **Status:** CANNOT-REPRODUCE
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Packaged Windows endpoint acceptance

**Summary:** The first newly built windowed package run created native runtime files but never published `session.json`. Its test process displayed an unhandled-script exception; the original exception text was not captured. A diagnostic console build and subsequent instrumented windowed/browser and actual desktop starts succeeded.

**Repro:** Private `m3-device-final-package/dist/S760Studio/S760Studio.exe --no-browser --no-sound --seconds 95 --state-dir .../windows-output-package-browser` with explicit boot/system/media paths. Concurrent bounded ASIO test was running. No repeatable trigger established.

**Expected:** Publish the session URL or an actionable startup diagnostic.

**Actual:** Initial session publication was absent; an unhandled exception window remained after the native child exited.

**Evidence:** Private `windows-output-package-browser/`, `windows-output-console-debug.log`, `windows-output-package-e2e-final.log` (one passed) and `device-final-desktop/desktop-verification.json` (OS ready,225776 nonblack CRT pixels).

**Resolution:** Cannot reproduce on the subsequent console, instrumented windowed and final desktop starts; no root-cause fix claimed. Frozen launches with an explicit `--state-dir` now preserve exceptions in `startup-error.log` for a recurrence. This is not clean-machine or indefinite startup reliability qualification.

### BUG-050 — Explicit Windows output endpoint produces no audio

- **Status:** FIXED
- **Severity:** S2
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Native Windows endpoint qualification

**Summary:** The new Windows endpoint selector initially wrote a raw endpoint ID into MAME's sound mapping. MAME identifies output nodes as `o:` plus the endpoint ID and removed the unresolved mappings, leaving no stream on the selected endpoint.

**Repro:** Select Realtek Digital Output, boot original OS2.24, load ROBOFULL and hold a native note while capturing that endpoint's WASAPI loopback. The initial mapping produces zero captured packets despite nonzero native PCM.

**Expected:** Native left/right audio reaches the selected Windows endpoint.

**Actual:** The unprefixed mapping is removed and digital loopback is empty.

**Evidence:** Private `windows-output-48000.log` reproduces the failure. `windows-output-48000-fixed/result.json` reports575520 stereo frames at48000Hz, expected20004.5Hz fixture peak, finite output and silent note-off. The corrected mapping survives MAME shutdown. `tests/test_native_runtime.py` covers the required node prefix, stereo channel mapping, escaping and restoring default output.

**Resolution:** Prefix render endpoint IDs with `o:` when staging private MAME sound mappings. Persisted configuration keeps the original Windows endpoint ID. This is digital shared-mode output qualification, not analog converter parity.

### BUG-049 — Device loss leaves native sampling running without input

- **Status:** FIXED
- **Severity:** S2
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Standalone audio acceptance review

**Summary:** A failed or stalled recording stream previously closed the device and reported an error while native time continued. An active recording could consume missing input, and recovery required restarting the sampler.

**Repro:** In the standalone capture worker, make the device read/status operation report a driver failure while a native machine is running. See `tests/test_audio_recovery.py`.

**Expected:** Pause the same native machine, show an actionable failure, and reopen the device with input re-priming before resuming. Preserve RAM, media and controls.

**Actual:** Before the change, the device closed without a native pause or a reopen operation.

**Evidence:** Four backend recovery tests cover pause, same-machine resume, failed reopen and preserving existing queued input while re-priming. React acknowledgement/error handling has a focused regression. Actual MOTU stream reopening after an injected closed-stream failure preserves the native PID and media, freezes native time while failed and resumes successfully. Physical unplug testing is excluded by user direction.

**Notes:** Live MIDI unplug is excluded from Milestone3 acceptance by user direction. This defect concerns audio capture and output devices.

**Resolution:** Pause on stream failure, preserve reported loss counters, offer acknowledged Reopen audio, re-prime input without overwriting queued samples, and resume the existing native machine. See [qualification](condensed/validation/standalone-audio-devices-2026-10-12.json).

### BUG-048 — ASIO underrun counter omits refill-wait silence

- **Status:** FIXED
- **Severity:** S2
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Sustained audio acceptance review

**Summary:** After output underflow, the callback zero-fills until the ring reaches its prime watermark. The counter previously counted only the initial short read, omitting subsequent silent callbacks during refill.

**Repro:** Prime a real MOTU ASIO output with4096 silent frames, stop supplying PCM, allow initial consumption, then compare missing-frame counters over another0.2 seconds. The preserved package DLL reports zero additional missing frames despite continued callbacks.

**Expected:** Count every missing output frame after playback starts, including re-prime waits; exclude initial startup silence and explicitly disabled output.

**Actual:** Old counter freezes while the device continues receiving zeros.

**Resolution:** Track whether playback has started. Count silent refill callbacks after that point, preserving explicit zero-fill/re-prime policy. The real driver probe reports8704 additional missing frames with the corrected DLL versus0 with the preserved DLL. Native callback regression covers initial prime, short read and a subsequent refill-wait callback.

**Evidence:** Private `reprime-old.log` / `reprime-new.log` under `docs/ic20-hle-findings/chatGPT-work`; source regression in `core/tests/test_asio.cpp`. Earlier sustained records retain their original counters and therefore undercount total refill silence.

### BUG-047 — Sustained ASIO playback output underruns

- **Status:** FIXED
- **Severity:** S3
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Physical micro lite MIDI/MOTU ASIO sustained acceptance

**Summary:** Physical MIDI loopback playback exposes native ASIO output underruns after the short smoke-test window.

**Repro:** Original firmware ROBOFULL, normal-speed standalone, MOTU ASIO outputs 3/4 to inputs 1/2 at 44100 Hz/512 frames; micro lite Port 5 physical out-to-in note-on/off cycles, with display and capture workers active. Initial test overlaps backend tests and a package build; resource contention is not isolated as the cause.

**Expected:** Sustained playback without unreported loss; bounded explicit recovery if a queue underruns.

**Actual:** Counter reaches 826 missing output frames by 122 seconds, with zero native output drops or driver status flags. The existing callback zero-fills and reprimes, and the UI reports the loss. This does not establish a driver-level dropout.

**Evidence:** Private `docs/ic20-hle-findings/chatGPT-work/m3-midi-sustained.log` and adjacent raw native/physical PCM.

**Notes:** Earlier native output draining below the prime watermark passes its regression, but the full physical retest still reports 102 missing output frames and8192 discarded input frames. The baseline ends at1610 missing output frames and22528 discarded input frames. Both runs produce all90 native note pulses and a silent release tail. Concurrent host load differs, so the counter difference does not isolate causation. At that stage this bug remained open pending controlled native/device clock and scheduling qualification; the later resolution is recorded below. [Durable evidence](condensed/validation/standalone-midi-sustained-2026-10-12.json).

**Resolution:** Binary input transport, output delivery even when the input FIFO is full, bounded wall-clock feedback and an explicitly displayed16384-frame output target pass five minutes/150 physical MIDI note cycles with zero output underruns/discards/native drops/driver flags. All150 native pulses and silent release are independently checked.2048 input frames are discarded; no zero-loss recording claim. The target adds371.52ms transport buffering, separate from driver latency. Earlier counts omitted refill-wait silence (BUG-048); they are lower bounds. This closes the documented finite profile, not indefinite or arbitrary-load qualification. [Evidence](condensed/validation/standalone-audio-devices-2026-10-12.json).

### BUG-046 — Output-only ASIO can silently stall while reporting active

- **Status:** FIXED
- **Severity:** S3
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Roadmap device-failure regression test

**Summary:** ASIO progress monitoring checked captured input only. With input disabled, a driver that remained active but stopped consuming output could leave the standalone silent indefinitely.

**Repro:** `tests/test_asio.py::test_output_only_driver_stall_is_visible_even_if_driver_reports_active` models an active driver with 8192 queued frames, unchanged played counter and more than two seconds elapsed. This is a deterministic driver model, not a physical unplug test.

**Expected:** Report the stopped output stream and provide reconnect/apply guidance.

**Actual:** Before the fix, status continued to succeed; the regression failed with `DID NOT RAISE OSError`.

**Resolution:** Track the existing native played-frame counter. If enabled output remains primed with queued PCM but makes no progress for two seconds, raise an actionable error through the existing stream failure/close path. Empty queues and progressing output do not trigger the check. Six focused ASIO tests pass; physical unplug qualification remains separate.

**Evidence:** Regression tests in `tests/test_asio.py`; native counter implementation in `core/src/s760_asio.cpp` is unchanged.

### BUG-045 — Live capture delivery underruns during firmware recording

- **Status:** FIXED
- **Resolved:** 2026-10-12
- **Severity:** S2
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Reported by:** Native MOTU physical loopback acceptance

**Summary:** Initial standalone capture delivery shared the 15 Hz display polling schedule and failed to sustain firmware recording.

**Repro:** Normal-speed native S-760 v2.24, opt-in recording device Windows MME MOTU Stereo In 1-2 at 44100 Hz stereo PCM16; ASIO outputs 3/4 looped physically to inputs 1/2. Arm and start using the firmware sampling screen, then stop and save.

**Expected:** Bounded capture transport sustains recording without native input underruns.

**Actual:** 51587 underruns by the recording screenshot and 55428 after stopping; both physical tones reach saved sample PCM, but continuity is unqualified.

**Evidence:** Private `docs/ic20-hle-findings/chatGPT-work/motu-live-sampling-34.log` and its adjacent capture/session evidence directory.

**Resolution:** Root cause was 4KB/frame JSON ingress, below the bandwidth required by stereo PCM packets. Ingress now reads at most 64KB/frame and executes at most one command; live PCM bypasses pointer-settle waits. A separate 5ms capture worker primes a bounded 8192-frame buffer. Checkpoint save/restore reopens hardware buffers and reports a discontinuity. MOTU physical recording now has zero native underruns; both 65514-frame channels match captured device PCM exactly and all 276480 allocated bytes survive firmware Save/export/fresh Load.329 backend/120 React tests and native source/package browser recording settings pass. Alternate rates, driver-level loss counts and long-term drift remain separate. See [physical sampling evidence](condensed/validation/native-physical-sampling-2026-10-12.json).

### BUG-044 — Standalone diverges from approved native VST interface

- **Status:** FIXED
- **Severity:** S1
- **Area:** ui
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** User; S1 explicitly requested by user

**Summary:** Standalone uses a separate simplified rack instead of the approved native VST panel. It omits completed button groups, Shift functions, input/output knob layout and Gotek browse/select controls. Its CRT housing also differs and exposes unused black transport rows.

**Repro:** Compare the native standalone README screenshot with the native SoundCheck VST screenshot captured on 2026-10-11.

**Expected:** Both native entrypoints share the approved visual hardware layout, with standalone settings and optional keyboard.

**Actual:** Generic button rows and a disk-status box; instructional text and media controls separate rack and keyboard.

**Evidence:** `docs/images/standalone-keyboard.png`; private reference `docs/ic20-hle-findings/chatGPT-work/soundcheck/156-rack-dials-final/loaded.png`.

**Notes:** Separate `NativeRack` and `S760FrontPanel` render paths. Verify shared rendering and real firmware inputs before closure.

**Resolution:** Shared front-panel and CRT-housing renderers; restored native Gotek browse/select and Shift controls; matched VST crop; 61-key keyboard scales with rack. Removed header, dropdown, footer and empty content area; all utilities are in Configuration.118 React tests,5 unchanged shell/visual checks, real native load/reconnect/restart/session recall and packaged configuration/WebView checks pass. See [validation](condensed/validation/standalone-visual-parity-2026-10-12.json).

### BUG-043 — Sampling postprocessing stalls on A7 wave-to-RAM DMA

- **Status:** FIXED
- **Severity:** S2
- **Area:** mame-driver
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** ChatGPT native sampling bus probe

**Summary:** OS 2.24 Sampling → Ready → name confirmation → Start enters postprocessing and polls IC4 DMA count forever. BC RAM-to-wave is implemented; inverse A7 is missing.

**Repro:** Native IC15/OS 2.24, accelerated muted machine, Sample → Sampling → Ready → Yes → Start. Read-only trace observes wave word 8, RAM destination 0x0ED712, byte count 0x2400 and command A7 at CPU 740B. Reads at CPU 7410 retain count 0x2400.

**Expected:** Copy the bounded byte range, advance addresses and exhaust count.

**Actual:** Now Working remains; over 1.9 million reads retain count 0x2400 in the initial probe. ADC input and recording-position reads are independently unsupported; DMA completion alone does not qualify recording.

**Evidence:** Private m3-sampling-discovery/trace.json and started.png; native verifier accompanies closure.

**Resolution:** Implemented the observed synchronous A7 inverse of BC with complete range/even-count validation and pointer/count advancement. `verify_native_sampling_dma.py` fails on the preserved prior binary and passes on the rebuilt driver, reaching waveform review and End. Normal native playback/release, exact131072-frame/display traced replay and307 backend tests pass. This closes the DMA stall only; live ADC, recording-position reads and physical timing remain open. See [qualified sampling profile](NATIVE_SAMPLING.md).

### BUG-042 — Closing standalone discards dirty media without recovery

- **Status:** FIXED
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Codex Milestone 3 lifecycle audit

**Summary:** Closing the standalone after firmware Save but before export discards controller changes unless the user separately saved a session. Native child failure also recovers only the last explicit save.

**Repro:** Complete a firmware Save (dirty revision134), close/reopen the standalone without export or Save session. The prior close path only stopped transports and destroyed the runtime.

**Expected:** Periodic separate recovery and a close checkpoint retain sampler/dirty media; failures are visible and normal desktop close is cancelled rather than losing work silently.
**Actual:** Pre-change no periodic or close checkpoint existed.

**Evidence:** Five new lifecycle tests fail before implementation with missing recovery API. Final native dirty revision134 replay compares131072 stereo frames and both displays exactly; child-failure and normal-close/reopen exports match, and injected close-save failure retains the previous archive/running dirty state.307 backend/115 React tests pass. Two actual packaged browser workflows verify the production60-second timer, startup preservation for61 seconds, confirmed restore and explicit quit. Actual WebView close writes a recovery checkpoint and exits0. Durable evidence: `docs/condensed/validation/standalone-auto-recovery-2026-10-12.json`.

**Resolution:** Added separate recovery checkpoint scheduling and normal-close capture, visible timestamps/errors, preserved startup/restart/settings/manual-restore history, explicit restore/new-history/quit actions and close cancellation on save failure. Manual saves and library originals remain independent.

**Notes:** Recovery is bounded by its last successful checkpoint, not lossless recovery of a killed process. Busy disks/connected external MIDI can defer snapshots; audio pauses during capture. Power-loss/zero-loss journaling, plugin autosave and SCSI workflow qualification are not claimed.

### BUG-041 — Format Track success without media mutation

- **Status:** FIXED
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Codex Milestone 3 source audit

**Summary:** The native FDC FORMAT TRACK case prepares a successful result but consumes no track IDs, fills no sectors and changes no media revision.

**Repro:** Inspect `fdc_execute_command`, case `0x0D`, in `mame-source/src/mame/roland/s760.cpp`. The writable inserted-media path immediately calls `fdc_start_result_phase(7)`.

**Expected:** Validate and transfer format descriptors, format controller-owned media, and expose failures and dirty state.
**Actual:** Before the fix, success with no formatting. Write-protect/no-media rejection was fixed separately in BUG-040.

**Evidence:** `python scripts/verify_native_media.py --format --checkpoint` fails before implementation: Format did not fill every sample/data sector. Native OS 2.24 trace at physical0188E4 supplies command4D, FA RAM DMA count0024 from083E0E, SC09 and fill0F. Final native run `media-verification-20261012-065549` verifies protected Format leaves bytes unchanged; writable formatting reaches revision161 with 733184 exact fill bytes, formatted dirty cold recall is exact, and subsequent Save/export/fresh reload preserves 119808 sample bytes plus peak1459/silent release.

**Resolution:** Validate whole CHRN sets and DMA/media bounds before track fill; advance native DMA and dirty revision on success, reject malformed/unsupported transfers without mutation. 294 backend tests, native builds, lint/build, actual packaged Format/export/reconnect/restart/restore and desktop readback pass. Durable evidence: `docs/condensed/validation/standalone-formatting-2026-10-12.json`.

**Notes:** Closed for OS 2.24 standard720KB native DMA formatting. HD/foreign layouts, PIO and physical controller timing are not qualified. Recovery beyond explicit saved sessions remains open.

### BUG-040 — Native floppy write protection missing

- **Status:** FIXED
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Codex Milestone 3 media qualification

**Summary:** The native floppy controller had no write-protect state, ST3 always reported ready/writable, and WRITE DATA never rejected a protected disk.

**Repro:** Before this change, `test_write_protection_uses_acknowledged_native_controls` fails because the runtime has no protection API. Driver source had no write-protect member or status bit.

**Expected:** Protected firmware Save reports Write Protected without mutating controller bytes; protection survives cold session recall and standalone displays acknowledged state.
**Actual:** Pre-change there was no way to protect inserted media.

**Evidence:** Private native acceptance `media-verification-20261012-063112`: firmware error screenshot, unchanged protected export, cold protection recall, then unprotected Save/export/fresh reload with 119808 exact sample bytes and peak PCM16 1459.
**Resolution:** Added controller protection state, ST3 WP/ready reporting, protected/no-media WRITE DATA/FORMAT rejection, native acknowledged controls, checkpoint serialization and standalone checkbox/readback. Final native acceptance includes the exact firmware error-region hash; packaged browser verifies protect/reconnect/restart/recall/unprotect. 294 backend and 114 React tests pass, as do native compilation, lint/build, development package audit and WebView readback. Durable evidence: `docs/condensed/validation/standalone-write-protection-2026-10-12.json`.

**Notes:** Protection is logical media state for the private controller copy; source filesystem permissions are independent. Writable formatting remains BUG-041. No physical timing or clean-machine release claim.

<!-- Add one "### BUG-NNN" block per bug, newest at the top of this section. -->

### BUG-039 — Missing source sample blocks saved-session recovery

- **Status:** FIXED
- **Severity:** S3
- **Area:** bridge
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Codex, `test_restore_after_failed_start_does_not_require_source_sample_disk`

**Summary:** Restore is blocked by the generic startup-error guard and by native startup validating an obsolete sample source, despite the checkpoint containing the floppy bytes.

**Repro:** Save a standalone session, remove/relocate its configured sample image, let the child stop, then restore with that old sample path and a startup error.

**Expected:** Preflight firmware/build identity, launch without the source sample image, and restore embedded media.

**Actual:** Generic Runtime settings error or missing-file startup rejection prevents restore.

**Evidence:** Regression in `tests/test_standalone_sessions.py`; native relocated-session acceptance reproduces 131072 stereo frames and both displays exactly. Real browser restores from missing-library startup and rejects incompatible archives without changing the live patch.

**Resolution:** Restore bypasses the startup-error guard, clears the obsolete initial sample path after archive preflight, and clears startup error only after successful state load. Firmware and SCSI prerequisites remain validated. 287 backend and 113 React tests pass.

### BUG-038 — Normal-speed native acceptance deadline shorter than wait

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Codex, Milestone 3 system-audio acceptance

**Summary:** The verifier's accelerated-time helper always allowed 30 wall-clock seconds, including a 35-emulated-second load wait. Normal-speed output necessarily exhausted that deadline.

**Repro:** `python scripts/verify_native_runtime.py --system-audio --audio-backend wasapi --audio-latency-ms 60 --state-dir docs/ic20-hle-findings/chatGPT-work/m3-wasapi-60ms` with local OS 2.24, IC15 ROM and ROBOFULL fixture.

**Expected:** Normal-speed waits allow their requested duration plus bounded overhead.

**Actual:** `TimeoutError: Machine stopped advancing` during the 35-second wait, despite advancing emulated time.

**Evidence:** Private `m3-wasapi-60ms/runtime.log`; corrected run in `m3-wasapi-60ms-final`.

**Resolution:** Deadline includes requested duration for system-audio runs. Normal-speed WASAPI firmware load/play/release and clean shutdown pass; accelerated regression remains unchanged.

### BUG-037 — WAV timeline assertion after checkpoint rewind

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-11
- **Reported by:** Extended native rack recall acceptance

**Summary:** Adding repeated checkpoint recalls to the existing native smoke test invalidated its assumption that external WAV offsets equal guest emulated time.
**Repro:** Combine `--rack-dials --pull-render --scheduled-midi` in the extended test.
**Expected:** Test note-off at the actual captured interval.
**Actual:** Gain/recall checks pass, then a wrong WAV interval produces a false sounding-tail failure. The external writer continues forward across guest rewind.
**Evidence:** native156-final.log in private scratch; original native156-dials3.log passed with fewer rewinds, illustrating why that pass was insufficient.
**Progress:** Separate the recall qualification from monotonic WAV qualification. Dial test verifies note-off directly through native float PCM and rejects incompatible flags; final separate runs pass.

**Resolution:** Recall and monotonic-WAV qualification now run separately. The final dial test verifies direct PCM release, exact non-unity replay and restored encoder position; the independent baseline passes WAV alignment and scheduled MIDI.

### BUG-036 — Worker display cache omits output level

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S3
- **Area:** bridge
- **Opened:** 2026-10-11
- **Reported by:** SoundCheck rack-knob acceptance

**Summary:** Native gain changes reach MAME, but audio-streaming display snapshots only copy pixel buffers and time, leaving output level at its default 100.
**Repro:** Set Output to 50% in the actual plugin editor while audio is streaming.
**Expected:** Telemetry and knob indicator report 50%, including editor reopen.
**Actual:** SoundCheck readback assertion fails. Native C++ regression reproduces: `Worker display cache lost output level`.
**Evidence:** Finding 156; audio156-dials.log and native156-cache-before.log in private scratch.
**Progress:** Copy level into the worker-owned display snapshot; native and real-host regression now pass.

**Resolution:** Worker snapshots now retain output_level. The new native C++ regression passes, and SoundCheck confirms 50% telemetry/indicator before and after editor reopen.

### BUG-035 — Output adjuster used digital override

- **Status:** FIXED
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** Native rack-dial acceptance

**Summary:** Initial in-development output routing called `set_value` on PORT_ADJUSTER, which MAME treats as a digital override.
**Repro:** `verify_native_runtime.py --rack-dials` on the initial knob implementation.
**Expected:** 50% gives half amplitude; 0% is silent.
**Actual:** Peak 0.069033 at requested half level, 0.044538 at minimum; comparison failed.
**Evidence:** Finding 156; native156-dials2.log and dial-audio.npz in private scratch.
**Resolution:** Use `ioport_field.user_value` for adjusters; initialize from the actual saved setting and restore it explicitly. Native comparison now gives zero half-gain error and exact silence. This tests software gain, not analog potentiometer taper.

### BUG-034 — Synchronous UI test measured host scheduling

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** React regression during concurrent compilation

**Summary:** A test inferred synchronous emission from an asynchronous user-event gesture taking under 100ms wall time.
**Repro:** Full Vitest run while native/C++ builds execute.
**Expected:** Verify event emission happens inside the dispatch.
**Actual:** Gesture took 118ms and failed despite exactly one synchronous emission.
**Evidence:** ui156-tests.log in private scratch.
**Resolution:** Dispatch a click synchronously and require the event before dispatch returns, without advancing timers. This is a functional ordering test; it makes no measured latency claim.

### BUG-033 — Intermittent cold restoration connection failure

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Reported by:** Final native plugin state acceptance

**Summary:** Cold restore can fail before publishing its checkpoint file, despite earlier passing runs. Added exception diagnostics distinguish this from an identity or checksum rejection.
**Repro:** build/Release/s760_native_plugin_tests.exe D:/S-760 docs/ic20-hle-findings/chatGPT-work/native157-state-diagnostic --state 48000 3 (use a fresh state directory for each run).
**Expected:** Fresh pending-note and active-note instances restore and replay exact PCM.
**Actual:** First final run failed pending restore; instrumented repeat passed pending restore but failed active cold restore with Native runtime disconnected or timed out. No checkpoint file in the failing cold instance.
**Evidence:** chatGPT-work/native157-final-state.log; native157-state-diagnostic.log; associated private cold runtime.log files.
**Notes:** Earlier native157-state.log passed. Root cause remains under investigation; do not treat the timeout as proven hardware or firmware failure.


**Follow-up:** Diagnostic stage run and three consecutive repeats pass exact cold PCM at48kHz. Root cause of the two earlier failures is still unknown. Operation-specific exception diagnostics are retained.

**Investigation (finding 159):** Reproduced at the pause stage before checkpoint load, and then without any checkpoint in the smaller C++ `--startup-repeats` test. After 35 successful fresh instances, the next timed out with Winsock 10060 waiting for the four-byte response header. A second run with another instance active also timed out. The frozen instance's flushed diagnostic trace recorded no frame/pause callback; a different child continued servicing controls. This narrows the failure to fresh runtime/control startup, not archive decoding. Root cause remains unproven. Thirty immediate and eight delayed Python startup/pause cycles passed; several complete C++ cold-state repeats also passed. These passes do not close the failure. Socket errors now distinguish EOF from the Winsock code and remaining byte count. Temporary Lua traces were removed. New repro: `build/Release/s760_native_runtime_tests.exe D:/S-760 <fresh-private-dir> --startup-repeats`. See [validation](condensed/validation/s2-loops-and-restore-2026-10-11.json).

**Resolution (finding 160):** A read-only stack capture from the stalled test child identified `sed1330_device::draw_graphics_scanline`, called by `update_text` before the first frame hook. The device constructor initialized only its busy flag; display enable, dimensions and other register storage were indeterminate. All scalar register fields now have deterministic initial values, with display off and character pitch 1. These are safe pre-configuration storage values, not claims about measured power-on registers. No firmware, vector, timing or timeout changes. The old binary failed twice during this investigation; the corrected binary passed two 40-launch stress runs alongside a running instance (80 fresh children), exact 240000-frame cold replay at48kHz, original-firmware boot/display/controls/audio/MIDI acceptance, 266 Python tests and six C++ suites. Temporary tracing was removed. See [validation](condensed/validation/s2-startup-lcd-2026-10-11.json).

### BUG-032 — Plugin editor discovery ignores configured native root

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S3
- **Area:** ui
- **Opened:** 2026-10-11
- **Reported by:** Plugin configuration qualification

**Summary:** The native root locates the machine but editor discovery previously searched only four module ancestors and the host working directory. A plugin stored deeper in the tree required a separate S760_UI_URL override.
**Repro:** Load the concrete plugin from chatGPT-work/m2-webview-build/Release with an unrelated host CWD and no S760_UI_URL; set the native root to D:/S-760.
**Expected:** The editor loads from the configured runtime root.
**Actual:** The old resolver falls back to a relative file URL.
**Evidence:** resolve_frontend_url in core/src/s760_webview_host.cpp; existing SoundCheck runs supplied an explicit URL override.
**Implementation:** Per-instance percent-encoded editor URL follows the native configuration; existing explicit development override remains supported.

**Resolution:** The native constructor supplies a per-instance percent-encoded file URL from its configured root. Settings-only SoundCheck boot/editor/load/play/reopen passes with unrelated host CWD and no S760_UI_URL. See docs/condensed/validation/milestone-2-audio-config-2026-10-11.json.


### BUG-031 — Plugin recall loses media metadata

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Reported by:** Milestone 2 session serialization review

**Summary:** Version-1 native plugin state captures mounted bytes but omits library folder, inventory, browse selection and source-path label. Restoring into another machine leaves its startup labels unrelated to restored media.
**Repro:** Insert a sample, choose another browse item, save plugin state and restore into a fresh instance. Inspect the Gotek metadata.
**Expected:** Restored selection, configured library and insertion label correspond to the saved session; missing source files do not replace captured media bytes.
**Actual:** The old state contains no media metadata and the cold instance reports its own boot disk.
**Evidence:** NativePluginState v1 schema; new media-library round-trip and cold native replay regressions.
**Resolution:** Version-2 archive includes validated metadata; old states restore an explicitly unknown label. Native checkpoint bytes remain authoritative. Recursive scans and failed folder changes are transactional.


**Validation:** Recursive discovery, rejected scans without mutation, independent selection and old-state compatibility pass. Real SoundCheck retains uninserted selection across reopening. Cold native VST recall restores media metadata and 240,000 exact stereo frames at48kHz with private source/library relocated, including note-off and corruption rejection. Finding154 and docs/NATIVE_MEDIA_LIBRARY.md record scope. One pre-load timeout on the extended native test was followed by a fresh-directory passing retry; both logs are retained.

### BUG-030 — Absolute mouse coordinates drift after Menu/Exit

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Reported by:** Native Menu integration regression

**Summary:** Host pointer transport assumes fixed accumulated mouse motion. After firmware Menu/Exit, the requested screen position no longer agrees with the observed guest cursor. The new Menu switch exposed this limitation.
**Repro:** `python scripts/verify_native_runtime.py --panel-menu --state-dir docs/ic20-hle-findings/chatGPT-work/native155-menu-repro` with original firmware and current native binary.
**Expected:** Pointer request (150,60) reaches diagnostic CRT coordinate (300,120), as on fresh boot.
**Actual:** (237,160). Subsequent requests also drift; motion is delivered but the fixed absolute mapping is invalid after this panel interaction.
**Evidence:** chatGPT-work/native155-regression.log; probe155.log records five successive request/cursor pairs; fresh-boot baseline passes boot/load/MIDI/release.
**Notes:** Read-only guest diagnostics and physical input only. ROM disassembly establishes context-dependent sensitivity and cursor bounds; the adapter now observes these and current cursor position. Do not force guest coordinates to conceal this defect. Menu opening itself is verified in MAME and SoundCheck.


**Resolution:** Read-only OS 2.24 cursor/bounds/sensitivity translation sends normal bounded MU-1 input; no RAM/PC writes. Free-running and paused-render regressions, corner/reversal checks, loaded audio and native state replay pass. See docs/condensed/validation/milestone-2-audio-config-2026-10-11.json.


### BUG-029 — Native media input pulse too short

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Reported by:** SoundCheck native drive UI acceptance

**Summary:** NativeRuntimeClient released media controls immediately after the socket acknowledged setting an input, before MAME sampled the input on a frame.
**Repro:** Through the embedded drive dialog, insert valid ROBOFULL.IMG while SoundCheck processes audio.
**Expected:** Native driver acknowledges insertion and the drive displays its filename.
**Actual:** No media-status.json was produced; UI correctly reported failure, but the error was "Invalid native JSON response".
**Evidence:** Private soundcheck/152-rack/failed-ui.json includes exact requests and returned error.
**Resolution in progress:** Hold the input until driver acknowledgement, with bounded timeout and release. Never force emulated time or firmware state.

**Resolution:** Hold the media control until the driver writes its acknowledgement, then release, with a bounded timeout. Actual SoundCheck rejects a nonexistent path and confirms ROBOFULL.IMG insertion; no forced firmware state (finding 151).

### BUG-028 — Firmware-driven LCD status missing in CRT mode

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** mame-driver
- **Opened:** 2026-10-11
- **Reported by:** Hardware owner; read-only native bus trace

**Summary:** Owner confirms the real LCD retains content in Mouse+CRT mode. Earlier explanation that blankness was expected was incorrect.
**Repro:** Boot original ROM/system disk in native Mouse+CRT mode; inspect LCD frames.
**Expected:** Display firmware-authored LCD pixels, including the CRT-mode status.
**Actual:** Blank. Native F800/F802 trace records SYSTEM SET 31 85 07 1a 40 3f 20 00, SCROLL, external font writes, cursor-direction changes, DISP OFF parameter54, and final bare DISP ON59. Provisional handler loses display attributes and requires a new parameter on59; also wraps memory at4KB, assumes20-byte pitch, ignores cursor direction and external fonts.
**Evidence:** Private lcd152-trace.txt and lcd152/1.png; driver lcd_w/lcd_update; Epson SED1335 technical manual.

**Resolution:** Native LCD now uses the SED1330 device with matching data readback and corrected mixed-layer rendering. Original firmware boot LCD matches the independent bus replay pixel-for-pixel (zero differences); real SoundCheck shows Mouse+CRT status. This qualifies the observed boot path, not every LCD mode (finding 151).

### BUG-027 — Embedded rack controls and drive display

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** ui
- **Opened:** 2026-10-11
- **Reported by:** User

**Summary:** Embedded rack still exposes demonstration mode buttons and F1–F6; native matrix has Command, Mode, Exit, Shift, S1/S2, F1–F3 and arrows. Seeded Shift map is empty. Gotek receives blank placeholder pixels.
**Repro:** Open plugin in SoundCheck; inspect rack and attempt a Shift combination with a single pointer.
**Expected:** Native panel input, usable chord controls and truthful drive status.
**Actual:** Demo-only controls, no Shift shortcuts, blank OLED. LCD blankness is BUG-028; Mouse+CRT mode still has a firmware LCD status message.
**Evidence:** S760FrontPanel.tsx, shiftButtonMap.ts; native driver panel input definitions.

**Progress (2026-10-11):** Manual-verified native layout replaces demo controls. F1–F6 under LCD; original six-position navigation cluster; dedicated Home/Mark/Jump. Value and Output routing is qualified by native and actual SoundCheck acceptance in finding 156. Input remains disabled until the native ADC path in Milestone 3 exists. Menu now routes the schematic-confirmed SC0/SP4 switch and opens the real firmware menu; mixed panel/mouse coordinates are tracked separately as BUG-030. Gotek Up/Down/encoder browse session-entered paths; Select opens the prefilled insertion dialog. The bay is centered, and redundant Insert image text and rack-ear 1U labels are removed. Native SoundCheck validates F4 chord and rejected/accepted media requests; the later Value/Output qualification below completes the playback rack scope.

**Resolution:** The approved native playback rack now has functional Value/Output controls, Menu, F1–F6 and Shift actions, LCD and acknowledged Gotek media. Original-firmware edits, native gain/state and actual SoundCheck reopen/play/release pass. Input Level is retained explicitly as a Milestone 3 recording feature; it is disabled and not claimed implemented.

### BUG-026 — Embedded studio viewport and CRT active area

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** ui
- **Opened:** 2026-10-11
- **Reported by:** User, SoundCheck screenshot review

**Summary:** Default 1024x640 plugin client clips the 1440px rack below the fixed monitor. Native renderer draws200 rows in a240-row surface; doubling all240 exposes80 unused black display rows.
**Repro:** Open plugin in SoundCheck at default size; rack is below viewport and black band appears beneath firmware softkeys.
**Expected:** Full rack and monitor visible together; verified native active area fills the monitor.
**Actual:** Overflow requires scrolling and unused native rows fill the bottom of the CRT.
**Evidence:** User screenshot observation; crt_update native loop y<200 and screen size640x240 in mame-source/src/mame/roland/s760.cpp.
**Notes:** Preserve wire pixels and legacy240-line modes; qualify pointer mapping after presentation crop.


**Resolution:** 1480x900 embedded editor and fitted studio layout keep the full rack visible. CRT presentation crops the native unused rows while preserving wire pixels. Real SoundCheck screenshots before/after editor reopen confirm the result (finding 151).

### BUG-025 — Embedded live CRT mouse input missing

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** ui
- **Opened:** 2026-10-11
- **Reported by:** ChatGPT SoundCheck load-workflow audit

**Summary:** App's live CRT is pointer-transparent over demo click handlers; C++ accepts no explicit held native mouse message. Real frames therefore cannot be operated using the embedded CRT.
**Repro:** Open the plugin in SoundCheck, then inspect OP760Monitor and the C++ message enum; legacy MOUSE_CLICK is rejected in native mode.
**Expected:** Live CRT pointer movement and held left/right buttons operate the firmware, with release on blur/cancel/close.
**Actual:** Demo handlers receive clicks; firmware mouse button ports are not driven.
**Evidence:** Source audit; new frontend and bridge regressions plus native firmware load acceptance will verify the fix.


**Resolution:** Explicit native pointer/button handlers operate the real Disk/Load workflow in SoundCheck; loaded-sample playback, Menu/Exit handoff and editor reopening pass. Existing pointer-release unit coverage remains applicable. See docs/condensed/validation/milestone-2-audio-config-2026-10-11.json.


### BUG-024 — VST3 SDK ABI mismatch

- **Status:** FIXED
- **Severity:** S1
- **Area:** bridge
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT SoundCheck preparation

**Summary:** Local VST3 interfaces prepend a virtual destructor, use virtual inheritance and encode incorrect interface IDs. Factory queries claim unsupported interfaces, metadata and bus outputs are uninitialized, and the class category is not the SDK audio-effect category.
**Repro:** Compare core/include/s760/vst3_defs.h and the factory with the local Steinberg SDK; exercise exported factory from an independently SDK-compiled process.
**Expected:** SDK hosts can discover, instantiate and query the native plugin.
**Actual:** Repository tests share the faulty definitions and cannot establish SDK compatibility.
**Evidence:** Independent SDK probe under development; this is initially source evidence, not a SoundCheck runtime result.
**Notes:** Correct ABI before claiming real-host editor acceptance.


**Resolution:** Corrected Windows x64 GUID encoding, actual SDK interface IDs, nonvirtual inheritance and FUnknown method order; initialized factory/bus metadata and audio class category, rejected unsupported factory interfaces, and validated stereo negotiation. Independent SDK probe and SoundCheck native loading pass. Exported native factory/audio regression passes with exact 48kHz PCM. Full host playback/editor UX remains separately qualified; old malformed class IDs are not migrated. See [host checkpoint](MILESTONE_2_PROGRESS.md).

### BUG-023 — Accepted panel and pointer messages are no-ops

- **Status:** FIXED
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT editor integration audit

**Summary:** C++ `S760Bridge::apply_message` groups panel/dial/pointer commands into a no-op case, although the MAME adapter has native input methods.
**Repro:** Inspect the switch in `core/src/s760_bridge.cpp`; accepted BUTTON_PRESS does not call the host.
**Expected:** Supported native controls route to the live machine; unsupported controls are reported.
**Actual:** Parsing succeeds without performing the input.
**Evidence:** Source audit; standalone uses a separate working Python route.
**Notes:** Embedded editor control qualification remains open until corrected and exercised.

**Resolution:** Native panel and normalized pointer commands now route to the host; mount returns its actual result. Invalid IDs/coordinates and unsupported legacy click/dial reject. Real firmware Mode-menu change passes through the bridge; complete React controls and host-visible errors remain open. See [native editor evidence](condensed/validation/milestone-2-native-editor-2026-10-11.json).

### BUG-022 — Editor frame requests compete with native audio

- **Status:** FIXED
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT native editor acceptance

**Summary:** The concrete WebView2 editor polls native frames on the same serialized control connection as audio rendering.
**Repro:** `s760_native_editor_tests ROOT PRIVATE_STATE --paced-var 48000 12`, concrete WebView2 build, original firmware and ROBOFULL fixture.
**Expected:** PCM remains identical to the reference across editor open/close/reopen with no underrun.
**Actual:** Output underrun (fault 3) at block 374, started 142704 / completed 139698 frames.
**Evidence:** Local `chatGPT-work/editor-149-native.log`; real MAME, WebView2 and React, not a mock.
**Notes:** Investigating display snapshots delivered with worker render replies, avoiding separate UI control requests during processing. No delay increase or fabricated audio is proposed.

**Resolution:** Audio render replies optionally carry display snapshots; the UI reads a separate cached snapshot during processing instead of issuing competing frame requests. Native editor close/reopen passes at 44.1/48/96 kHz with exact reference PCM and zero drops. A run during a concurrent C++ build still underruns: arbitrary load robustness is not established. See [native editor evidence](condensed/validation/milestone-2-native-editor-2026-10-11.json).

### BUG-021 — VST3 editor does not schedule frame updates

- **Status:** FIXED
- **Severity:** S2
- **Area:** ui
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT Milestone 2 integration audit

**Summary:** `S760Vst3PlugView::attached` opens the editor and `tick()` can pump it, but the view installs no UI timer and tick is not part of IPlugView.
**Repro:** Inspect attached/removed/tick in `core/src/s760_vst3_plugin.cpp`; only initial bridge frames are requested by controller open.
**Expected:** Periodic UI-thread frame delivery for the lifetime of an attached view, detached without stopping audio.
**Actual:** A generic host using only IPlugView has no frame-pump entry point. Initial frames can also precede asynchronous page readiness.
**Evidence:** Source audit, not a DAW observation. The WebView2 harness explicitly posts test messages; it does not test plugin scheduling.
**Notes:** Native-plugin editor integration remains open in Milestone 2. Any fix must keep UI transport outside realtime callbacks and qualify close/reopen with continuing audio.

**Resolution:** The concrete Windows editor controller installs a UI-thread timer at about 15Hz, waits for page readiness, and removes its registration before closing. The real WebView2 harness receives multiple automatically scheduled CRT frames, verifies no callbacks after close, and repeats after reopen. Native audio/DAW continuity remains a separate qualification gate.

### BUG-020 — WebView2 backend is a success-reporting outline

- **Status:** FIXED
- **Severity:** S2
- **Area:** ui
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT source audit

**Summary:** The gated C++ backend sets `m_created=true` without creating a WebView environment/controller, and discards outbound frames/messages.
**Repro:** Inspect `WebView2WebViewHost::create` and `post_frame_to_js` in `core/src/s760_webview_host.cpp` under `S760_HAVE_WEBVIEW2`.
**Expected:** A functioning embedded page, or explicit creation failure.
**Actual:** Success with no page. The default stub is separately identified as a test backend.
**Evidence:** Source inspection; no real C++ editor acceptance claimed.
**Notes:** Milestone 2 tracks implementation. Standalone uses a separate working Python host; the React embedded channel alone does not fix this backend.

**Resolution:** Concrete environment/controller, local asset mapping, bounded messaging, resize and cancellation implemented. `s760_webview2_tests` passes against the installed runtime for two open/close cycles. Actual native VST3 editor/audio host acceptance remains a separate gate.

### BUG-019 — Malformed native session JSON escapes the event handler

- **Status:** FIXED
- **Severity:** S3
- **Area:** ui
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT NativeStudio regression

**Summary:** NativeStudio parsed incoming text without exception handling or checking the media list shape.
**Repro:** Deliver `{bad` to the NativeStudio WebSocket message handler (mock transport).
**Expected:** Actionable error while allowing subsequent valid messages.
**Actual:** Uncaught JSON parsing exception before the fix.
**Evidence:** `google-ui/src/NativeStudio.test.tsx`, malformed session regression.
**Resolution:** Guard JSON parsing and session media shape; report invalid response and retain the message handler. No firmware behavior changed.

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

- **Status:** FIXED
- **Resolved:** 2026-10-11
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

**Resolution:** Completed WRITE(6)/WRITE(10) payloads now update the private emulated image at the requested LBA. Range errors return CHECK CONDITION with per-target sense; CD-ROM writes are rejected. Zero-count 10-byte commands complete without a data phase; WRITE(6) zero means 256 blocks. Incomplete/reset writes leave media intact. Pending offsets, sense and written image bytes survive warm/cold checkpoints. Generated-media device tests pass, including unchanged source files. This fixes discarded device payloads, not firmware Save/export-to-host qualification; that remains in Milestone 3. See [validation](condensed/validation/s2-scsi-and-stack-2026-10-11.json), `scripts/verify_scsi_checkpoint.py`, and finding 158.

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

- **Status:** FIXED
- **Resolved:** 2026-10-11
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

**Resolution:** All four generators now use a shared evidence policy and were regenerated. Historical rows are explicitly unverified inventory, with no coverage percentage, invented owner/source-line claims or passing badges. Reviewed assertion examples distinguish image bytes, static source and mocked React controls; native/hardware qualification links to dated validation instead. Five report regressions check determinism, committed output freshness, removal of false claims and resolvable scoped selectors. The full Python suite passes 266 tests. Evidence: [S2 validation](condensed/validation/s2-bugs-2026-10-11.json); finding 157.

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
**Expected:** faithful IC4 receive/interrupt behaviour, including measured buffering,
overrun and vector/arbitration semantics. A FIFO must not be presumed without evidence.
**Actual:** inferred vector substitution + single-byte latch with logged overrun
drop. The raw driver flag is off by default; supported native launchers explicitly
enable this experimental profile, so standalone/plugin MIDI receive does work.
This does not establish hardware arbitration or FIFO depth.

**Notes:** three-voice and 24-voice polyphony were demonstrated through this
experimental path. Do NOT promote to default emulation until real IC4
arbitration/buffering is resolved. Related: BUG-009.

### BUG-003 — Unrecognized sample loop/direction mode flags are silently dropped

- **Status:** FIXED
- **Resolved:** 2026-10-11
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

**Resolution:** The supported Python and C++ runtime launchers already enable interpolation, which enables the existing loop implementation. Added a firmware-driven `--loop-modes` acceptance against the identified ROBOLOOP fixture. All seven modes produce PCM; five repeating modes match the expected forward/reverse/alternate sign sequence exactly, the two one-shots stop while held, and all modes end in silence after note-off. This closes the stale default-profile silence report at 44.1 kHz/unity pitch, not complete-chip parity or other clocks/flag combinations. No new DSP behavior was introduced. See [validation](condensed/validation/s2-loops-and-restore-2026-10-11.json); finding 159.

### BUG-002 — BMOVI (0xCD) retains the duplicate operand-fetch bug; unaudited

- **Status:** FIXED
- **Resolved:** 2026-10-11
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

**Resolution:** Removed the two opcode-body read_pc calls already performed by direct_2w. The rebuilt MAME passes the isolated zero/one/three-word fixture, bounds, pointers and following-instruction sentinel; the pre-fix binary aborts with Unhandled 10 (feb6). Original-firmware boot/load/audio/pull-render/scheduled-MIDI acceptance also passes. This closes the operand-fetch defect only: interrupt restart, timing, count semantics and physical KB applicability remain unaudited. Evidence: [S2 validation](condensed/validation/s2-bugs-2026-10-11.json); `scripts/verify_bmovi_fetch.py`; finding 157.

### BUG-001 — MCS-96 PUSHA/POPA/PUSHF/POPF are stack-neutral no-ops

- **Status:** FIXED
- **Resolved:** 2026-10-11
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

**Resolution:** Native mode already delegates to kb_push_flags/kb_pop_flags; the original report incorrectly generalized the legacy flat-mode workaround. Added an isolated I80C196KB execution test for PUSHF/POPF and PUSHA/POPA: exact SP deltas, saved PSW and INT_MASK1/WSR words, clearing/restoration, and stack guards pass. No CPU semantics changed in this closure. The unsupported flat bring-up profile retains its documented stubs; broader interrupt/timing fidelity remains unqualified. Native original-firmware acceptance passes. See [validation](condensed/validation/s2-scsi-and-stack-2026-10-11.json), `scripts/verify_native_cpu_flags.py`, and finding 158.
