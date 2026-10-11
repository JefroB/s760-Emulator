# S-760 completion roadmap

**Milestone 1 complete (2026-10-11):** One native engine now serves standalone and exported-module displays, MIDI, audio and bounded same-build state. Lifecycle, recovery, timing and the exact Windows standalone distribution profile have acceptance evidence. The remaining mixed objective is split below: configuration/editor delivery belongs to Milestones 2/4, native sampling to 3/4, and real DAW acceptance to 4. These remain open. [Closure and evidence](MILESTONE_1_COMPLETION.md).

Updated 2026-10-11. This is the active roadmap for delivering a standalone sampler and VST3 instrument with the React interface displaying authentic MAME CRT/LCD output. Update checkboxes only with recorded evidence; compilation and mock tests do not establish a working product.

## Definition of complete

A packaged Windows application and VST3 plugin boot the original firmware, load and edit sample programs, respond to MIDI and panel/mouse input, produce audio, sample external input, save media and restore sessions. React supplies the chassis and controls; MAME supplies the actual CRT/LCD pixels. Both products use the same tested engine. A release must document supported hardware behavior and remaining fidelity limits.

VST2, CLAP and other platforms are follow-on compatibility targets unless explicitly promoted into release scope. New OS features, including granular playback, are separate from completing the original sampler.

## Current checkpoint

**Licensing decision (2026-10-11):** original project-owned code now uses
[BSD-3-Clause](../LICENSE), with standard warranty/liability provisions and
[explicit scope and hardware-use guidance](LICENSING.md). Roland binaries remain
excluded. Contributor provenance, corresponding-source delivery and actual
bundled-component review remain release gates; no compound objective is closed
solely by adding a license.

**Milestone 1 boundary assessment (2026-10-11):** current exported-module audio
passes 60 seconds each at 44.1/48/96 kHz with exact reference PCM and zero missed
deadlines. Parent-crash cleanup, directory reuse and explicit saved-session
recovery pass. Packaging now retains full MAME license texts and rejects release
labelling. At that historical checkpoint, distribution was blocked by missing project licensing,
unqualified source delivery and bundled-dependency review. These are now resolved
for the exact Windows standalone profile below. At that checkpoint, three objectives remained open; see current checkboxes below.
[Assessment](NATIVE_BOUNDARY_QUALIFICATION.md) and
[evidence](condensed/validation/native-boundary-2026-10-11.json).

**Milestone1 standalone session recovery delivered (2026-10-11):** Save session
and confirmed Restore saved session now recover the loaded patch after restart
or native-child failure. Native replay matches131072 stereo frames and both
displays; the real browser restores the original patch table after a reboot.
A checkpoint callback-boundary defect exposed by that test is corrected.
At that checkpoint, distribution qualification, full plugin/SCSI state and native
input/DAW integration remained open. Snapshot state is now delivered below.
[Session contract](NATIVE_SESSIONS.md) and
[evidence](condensed/validation/native-session-2026-10-11.json).

**Milestone1 production-backend retirement completed (2026-10-11):** the exported
VST3 factory now creates the native MAME engine exclusively, with independent
instance directories and explicit configuration/startup failure. The actual
module passes firmware boot/load, display and exact PCM acceptance; native
input still rejects; floppy-profile state now works. At that checkpoint, three objectives remained open; see current checkboxes below. The former ADC/FX class
is unavailable until implemented. [Selection contract](NATIVE_PLUGIN_SELECTION.md)
and [evidence](condensed/validation/native-factory-2026-10-11.json).

**Milestone1 audio timing objective completed (2026-10-11):** the native processor
passes60-second wall-clock runs at44.1/48/96kHz with varied callback sizes, exact
offline-reference PCM and no missed callback deadlines or stream faults. The
supported profile and approximately279ms software budget are explicit; actual
DAW/device and low-latency product qualification remain separate. Four objectives
remained open at that checkpoint. [Contract](NATIVE_AUDIO_TIMING.md) and
[evidence](condensed/validation/native-audio-timing-2026-10-11.json).

**Milestone1 readiness completed (2026-10-11):** firmware boot/load observations
and UI recovery now pass real native, browser and packaged desktop acceptance.
Reconnect preserves the loaded patch; confirmed restart reboots safely, and the
UI service survives a native-child failure. Five objectives remained open at that checkpoint.
[Contract](NATIVE_FIRMWARE_STATUS.md) and [evidence](condensed/validation/native-readiness-2026-10-11.json).

**Milestone1 state progress (2026-10-11):** Version2 checkpoints now restore future MIDI note-on/off in a fresh
process with131072 stereo float frames reproduced exactly. C++ queue snapshot
primitives preserve unread PCM and pending host events in unit tests; their
integration into complete plugin state is still required.204 Python regressions,
24 C++ executables and a ten-second native varied-block processor run pass.
See [checkpoint evidence](condensed/validation/native-scheduled-checkpoint-2026-10-11.json).

**Media progress (2026-10-11):** firmware Disk/Save now completes the observed
RAM and wave-memory DMA write paths. Export disk publishes a new image without
overwriting library media. Fresh-machine reload preserves all13 generated
ROBOFULL payloads (119808 bytes) exactly and passes note60 playback/release.
Disk replacement now rejects busy or unexported controller media; export clears
only the published revision. Native Save/export/eject/reinsert/reload passes.
Regression checkpoint:184 Python,88 React and10 browser tests, plus core/plugin
executables and packaged desktop pixel readback. Full session recall and other
FDC/SCSI workflows remain open; see [media evidence](condensed/validation/native-media-2026-10-11.json).

**Standalone progress (2026-10-10):** an isolated native runtime now feeds real
CRT/LCD pixels to a React player in a WebView2 desktop window. Firmware disk
loading and live MIDI audition pass a native regression, including silent
note-off. A packaged executable has returned live canvas pixels without Vite.
Independent processes and duplicate-state-directory rejection were tested.
This is a development player, not completion of the milestones below: the
VST3 routing, realtime audio qualification, sampling and full
session recall remain open. See the [player runbook](STANDALONE_PLAYER.md) and
[runtime contract](NATIVE_RUNTIME_PROTOCOL.md).

- [x] Native MAME boots original IC15 ROM/system disk to the colour Perform Play screen; mouse and MIDI paths work in the tested native configuration.
- [x] Native sample floppy loading, measured playback/envelope/loop work and save-state checks have recorded evidence.
- [x] Full 88-note playback fixture validated. Measured interpolation agrees within 1% normalized RMS for the documented signals and settings.
- [x] Native build, core/plugin build and local regression checkpoints passed. Standalone checkpoint: 172 Python tests, 87 React tests and 10 browser tests including the native runtime; core/plugin executables also pass.
- [x] Live native MAME engine connected to the standalone React/WebView2 player; actual CRT/LCD frames and firmware inputs verified.
- [x] Connect the native runtime to the C++ VST3 module, including audio and bounded same-build state. Actual DAW/editor qualification remains separate.
- [ ] Packaged standalone and VST3 verified end to end.

See the [native runbook](condensed/11-native-boot-and-audio-runbook.md), [audio scope](condensed/06-audio-dsp-and-hardware-parity.md) and [measurement summary](condensed/validation/audio-pitch-2026-10-10.json). Sub-1% agreement is a practical acceptance threshold within the stated measurement domain, not proof of all ASIC behavior. The analog recording chain contributes uncertainty.

## Milestone 1 — One live engine

**Status: complete for the documented Windows native-engine integration profile.**
The engine milestone establishes one functioning runtime shared by both clients;
user-facing sampling, configuration and external host compatibility are product
acceptance gates in later milestones. [Closure review](MILESTONE_1_COMPLETION.md).

Current implementation: [native C++ adapter](NATIVE_CPP_RUNTIME.md).
[Scheduled MIDI and C++ evidence](condensed/validation/native-cpp-runtime-2026-10-11.json).

- [x] Implement and document an isolated runtime boundary independent of React, with bounded display queues, authenticated local transport and serialized controls.
- [x] Verify startup/shutdown, startup-failure lock release, two independent processes and rejection of shared state directories.
- [x] Choose and document the license for original project-owned code: BSD-3-Clause, with standard warranty/liability disclaimers. Preserve third-party licenses; exclude Roland firmware and document user-supplied files. [License scope](LICENSING.md) and [firmware setup](FIRMWARE_SETUP.md).
- [x] Qualify the Windows standalone distribution profile: reviewed contributor/third-party provenance, actual bundled dependencies and corresponding-source delivery. The delivered MAME source rebuilt cleanly; that rebuilt binary passes native and packaged desktop acceptance. Exact artifact hashes gate redistribution; changed builds require review. VST3, signing and clean-machine product acceptance remain separate. [Distribution qualification](DISTRIBUTION_QUALIFICATION.md).
- [x] Qualify native crash recovery: owned-child cleanup, state-directory reopening and explicit last-save standalone recovery pass. Plugin autosave is not claimed.
- [x] Qualify host-clocked native audio for the documented profile: 60 seconds at each supported rate with varied callbacks, exact reference PCM and no missed deadlines. [Timing contract](NATIVE_AUDIO_TIMING.md).
- [x] Add demand-driven PCM block rendering with retained surplus samples; verify1–8192-frame blocks against a continuous native WAV. [Evidence](condensed/validation/native-pull-render-2026-10-11.json).
- [x] Schedule bounded MIDI batches in emulated time through the real serial transmitter; verify enqueue timestamps and native audio.
- [x] Implement preallocated C++ PCM queue and render worker; verify concurrent ordering, backpressure, underrun reporting and exact native PCM preservation.
- [x] Qualify realtime deadlines, host event offsets/latency and sample-clock behavior beyond video-frame stepping and fixed44100Hz output. Qualified explicit native processor profile:44.1/48/96kHz, varied64–1024-frame callbacks,60seconds per rate, exact offline PCM and no missed deadlines. Software latency is approximately279ms; total audible/device latency and real DAW acceptance remain separate. [Contract and limits](NATIVE_AUDIO_TIMING.md).
- [x] Add an explicitly configured native mode to `S760MameHost` using the original boot ROM, banking and devices; verify real displays, media, MIDI and worker PCM.
- [x] Retire the historical buffer-only production selection path when plugin-wide routing is complete. The exported VST3 instrument factory exclusively creates native MAME; bridge, MIDI and PCM share that instance, while unsupported native ADC explicitly rejects; floppy-profile state is supported. Historical direct constructors remain diagnostic-only. Actual module acceptance passes; full SDK/DAW/editor qualification remains separate. [Contract](NATIVE_PLUGIN_SELECTION.md).
- [x] Bind the C++ native child to a Windows lifetime job; verify abnormal parent exit kills the owned child and the state directory can reopen. Explicit standalone last-save recovery is now supported; changes after that save and plugin recovery remain open.
- [x] Expose native pause/resume/single-frame stepping and bounded live stereo PCM through the same runtime as CRT/LCD frames, controls, MIDI and media. Verify both PCM channels against MAME WAV and report overflow.
- [x] Add versioned native floppy-runtime checkpoints with identity/integrity validation; cold restore active PCM, refreshed displays, in-flight serial MIDI and dirty media. [Contract and evidence](NATIVE_CHECKPOINTS.md).
- [x] Expose standalone session save/restore and recovery of the last saved floppy-runtime checkpoint after native-child failure. Exact native PCM/displays, recovered patch playback/release and real browser save/restart/restore pass. [Contract](NATIVE_SESSIONS.md).
- [x] Complete full snapshots including integration of host/plugin queues and SCSI. Same-build suspended recall preserves native state, host queues/converter history, SCSI CDB/transfers and media. External SCSI images are bounded to 64 MiB total with matching startup files. Partial-phase/cold-media tests, 131072 exact native stereo frames/refreshed displays and all-rate plugin replay pass. No autosave, cross-build migration or SCSI writeback qualification is claimed. [State contract](NATIVE_PLUGIN_STATE.md).
- [x] Add an explicit native VST3 processor path: bridge displays, host note offsets and worker PCM use the same machine. Verify boot/load/play/release, suspension, termination and ten-second fixed/varied callback runs. [Evidence](condensed/validation/native-plugin-stream-2026-10-11.json).
- [x] Prevent selected-MAME processing and state from falling through to the legacy core. Native recording input rejects; supported state recall uses the same native instance.
- [x] Complete native-only exported-module selection and route supported project snapshots through that same instance. Factory startup/failure and independent-instance tests pass; bounded native/host/SCSI state restores with exact PCM. Unsupported ADC rejects explicitly. Graphical configuration/editor delivery is tracked in Milestones 2/4; native sampling in 3/4; actual SDK/DAW acceptance in 4. [Selection](NATIVE_PLUGIN_SELECTION.md), [state](NATIVE_PLUGIN_STATE.md) and [closure](MILESTONE_1_COMPLETION.md).
- [x] Report missing firmware, process startup failure and handshake failure in the standalone launcher; report MIDI discovery failure while preserving audition.
- [x] Expose explicit firmware boot/load readiness and recovery in the UI. OS 2.24 screen observations distinguish booting, Perform Play ready, disk activity/idle, unknown, timeout/stall and process failure. Reconnect preserves the patch; confirmed restart protects live dirty/busy media and recovers a failed child to a fresh boot. [Acceptance and limits](NATIVE_FIRMWARE_STATUS.md).

Acceptance met: native and exported-module harnesses boot, load ROBOFULL through firmware controls, deliver authentic frames and exact reference PCM, schedule/release MIDI, restore supported state and shut down/reopen isolated instances. The packaged desktop independently returns live firmware pixels. Evidence and profile limits are collected in the [closure review](MILESTONE_1_COMPLETION.md).

## Milestone 2 — Live React displays and controls

Depends on milestone 1.

- [x] Deliver native CRT and LCD frames to the existing React canvas consumers, with correct geometry, palette and scaling. Native player and conversion tests; remaining hardware display-mode fidelity is tracked separately.
- [x] Connect mouse movement/buttons, 13 panel buttons, raw floppy insertion and MIDI audition to the live native machine; preserve Mouse+CRT defaults for new profiles.
- [ ] Complete dial and keyboard controls and integrate the native transport into the full existing rack shell. The development player currently uses a smaller React control surface.
- [x] Host the standalone React player in WebView2 with live frames and controls; closing its window shuts down its machine.
- [ ] Implement the plugin WebView2 environment/controller, lifetime, resize and message/frame transport. The existing C++ gated implementation remains an outline. The standalone now uses a working pywebview/WebView2 host with local WebSocket transport; that does not complete the plugin host.
- [ ] Implement matching embedded transport in the React bridge client, which currently uses WebSocket.
- [ ] Deliver shared graphical firmware/media/runtime configuration and actionable startup errors in the React interface. Standalone first-run persistence is accepted in Milestone 3; plugin host/editor delivery in Milestone 4. This is the configuration work split from Milestone 1.
- [x] Populate the native player's floppy selector from the configured media folder and insert a private working copy; load through firmware Disk/Load.
- [x] Report acknowledged insertion/export results and rejected media changes in the native player.
- [ ] Replace demonstration media actions in the full rack shell.
- [ ] Ensure closing/reopening the plugin editor leaves audio and the emulated machine running correctly. Standalone window closure intentionally ends its session.

Acceptance: from React, observe firmware boot, insert/load a sample disk, navigate and edit via real controls, then play MIDI and hear audio. Screens must agree with native MAME, including cursor and highlight behavior.

## Milestone 3 — Packaged standalone

Depends on milestones 1–2.

- [x] Build a Windows standalone executable using MAME system audio; expose on-screen audition and enumerated MIDI input selection.
- [ ] Verify physical MIDI playing and device disconnect/reconnect; add audio device configuration, sample-rate conversion, buffering and reported latency.
- [x] Package built React assets locally; launch without Vite, a terminal or a manually started bridge service. Development Windows package verified through WebView canvas readback; clean-machine release qualification remains open.
- [x] Accept explicit firmware/media/state paths, stage selected system firmware per instance and verify clean desktop shutdown. Firmware and samples are excluded from the package.
- [ ] Add first-run firmware/media location setup and persistent settings, with recovery from missing paths and actionable UI errors.
- [x] Complete the observed firmware floppy Save path and explicit export to a new image; verify fresh-machine sample reload and audio while preserving library originals.
- [x] Reject busy/dirty controller media replacement and ejection; clear dirty state only after publication of the captured revision. Verify native Save/export/reinsert and fresh reload.
- [ ] Qualify firmware empty-drive behavior before exposing ejection in the UI; implement shutdown/crash recovery, formatting and firmware write-protection/error behavior.
- [ ] Implement native ADC/input transport into the existing machine, with negotiated capture format/rate and bounded buffering; expose standalone recording-device selection. Unsupported native input currently rejects. This is the sampling implementation split from Milestone 1.
- [ ] Verify external audio input reaches the firmware sampling workflow and saved samples reload correctly, using that native ADC path; record device, rate, timing and overflow/error behavior.
- [x] Implement bounded same-build standalone saved-session recall through the native engine; cold PCM/display replay and explicit recovery of the last save pass. [Contract](NATIVE_SESSIONS.md).
- [ ] Complete product session handling: relocated/missing-media recovery, clear identity/version mismatch UX and recovery policy for edits after the last explicit save. The bounded engine snapshot does not complete these workflows.

Acceptance: install on a clean Windows environment with user-supplied firmware, boot, load, play, sample, save, quit and reopen successfully. Record device settings and dropout/latency results.

## Milestone 4 — Production VST3 host behavior

Depends on milestone 1; editor delivery also requires milestone 2.

- [x] Connect exported-module processing and bounded suspended state to the unified native engine, with no fallback to the historical core. Completed in Milestone 1; real host/ABI acceptance remains below.
- [ ] Deliver graphical plugin configuration and host-visible startup errors, including persistent firmware/media settings and recovery from invalid paths; use the shared Milestone 2 interface.
- [ ] Qualify the actual VST3 SDK/ABI, discovery/metadata/bus descriptions and scan/load in a named real DAW or native QA host. Repository-interface module tests do not satisfy this gate.
- [ ] Honor MIDI event sample offsets, note-off, sustain, pitch bend and other supported controllers; verify channel handling and panic/reset behavior.
- [ ] Support negotiated sample rates and varying block sizes with bounded audio buffers. Keep UI, disk access and avoidable allocations/blocking off the realtime callback.
- [ ] Route host sampling input through the same native ADC path delivered in Milestone 3 and qualify instrument output/input buses, latency/tail reporting, suspend/resume and offline rendering in the actual host. Do not advertise the Live Sampler FX class until its native input path passes.
- [x] Implement versioned bounded native/host project snapshots with integrity/identity checks and exact cold replay at all three supported rates. [State contract](NATIVE_PLUGIN_STATE.md).
- [ ] Complete host project portability: persist product settings and media references, handle relocation/missing media, and verify actual DAW save/reopen. Preserve explicit same-build/format limitations until migration is implemented.
- [ ] Verify two independent instances, editor resize/reopen, plugin removal and host shutdown.

Acceptance: scan and load in a real DAW; play and record MIDI, sample input, save/reopen a project, run multiple instances and compare offline bounce with realtime playback. Record host/version, rates and block sizes. No cross-instance media or machine state.

## Milestone 5 — Hardware coverage and supported defaults

Can proceed alongside integration; required for the completion claim.

- [ ] Inventory CPU compatibility behavior by execution mode: distinguish legacy flat/HLE shims from native 80C196KB semantics. Audit BMOVI applicability, SFR/window behavior and remaining timer/serial/DMA peripherals against primary specifications and isolated instruction/device tests.
- [ ] Validate IC4 interrupt arbitration under simultaneous FDC, MIDI and voice-completion requests: priority, vector latching, masking, acknowledgement and return. Add MIDI burst/overrun tests; successful single-source firmware playback does not establish these rules.
- [ ] Audit actual firmware workflows for perform/patch/partial/sample editing, voice allocation/polyphony, MIDI and output routing.
- [ ] Validate interpolation beyond the current 44.1kHz forward-loop quarter-to-double-speed domain: other clocks, one-shots, reverse/alternate loops and pitch transitions.
- [ ] Validate combined envelope, filter, stereo and interpolation behavior; resolve unsupported resonant/moving filter cases with evidence.
- [ ] Audit floppy/SCSI load/save and sample editing/sampling through the native machine. Parser or host-manager tests alone do not demonstrate firmware peripheral behavior.
- [ ] Promote supported diagnostic monitor paths to normal configuration only after the combined path passes; document explicit unsupported cases.
- [ ] Record acceptance metrics per domain and distinguish model error from measurement-chain uncertainty. Request hardware captures only for specific unresolved behavior.

Acceptance: maintain a firmware-workflow and audio-domain matrix with reproducible tests. Every advertised feature has native-runtime evidence; remaining exclusions are explicit rather than silently approximated.

## Milestone 6 — Release qualification

Depends on milestones 3–5.

- [x] Add native boot/load/MIDI/audio regression, real-runtime browser smoke and packaged WebView pixel-readback checks alongside unit tests.
- [ ] Extend standalone acceptance to edit/sample/save/restore and add real-plugin smoke tests using the user's VST framework when available.
- [ ] Run sustained playback, repeated boot/load/save, malformed/missing media and recovery checks.
- [ ] Qualify final standalone and VST3 release artifacts, installers and runtime prerequisites on the supported clean-machine/host matrix. The exact development-stage Windows standalone artifact already has [source/dependency distribution qualification](DISTRIBUTION_QUALIFICATION.md); requalify changed builds and plugin-specific components. Preserve notices/source delivery and exclude proprietary firmware, recordings and private research.
- [ ] Reconcile historical README coverage claims with actual product evidence and publish setup, troubleshooting and supported-feature documentation.
- [ ] Record the tested source revision, artifact hashes, host/device matrix and known limitations before tagging a release.

Acceptance: another user can follow the published instructions to run both products and complete the load/play/edit/sample/save/restore workflow without development tools.

## Evidence required for review

| Concern | Completion evidence | Gate |
| --- | --- | --- |
| CPU/peripherals | Mode-specific shim inventory, specification-backed semantics and isolated tests; native workflow regression after corrections | 5 |
| MIDI arbitration | Concurrent-source traces/tests, mask/acknowledgement behavior, burst handling; inferred priority explicitly identified until verified | 5 |
| Audio DSP | Held-out physical captures for claimed domains, plus combined-path native tests; dynamic resonance remains open | 5 |
| Live integration | Actual native machine driving React frames and host audio/MIDI/state together | 1–4 |
| Testing | Label each result as model/unit, native runtime, physical hardware comparison or packaged-product validation | 6 |
| Documentation | Current status precedes dated history; superseded experiments never serve as current acceptance evidence | 6 |

The latest distribution checkpoint has 241 Python passes; the recorded React/browser checkpoints are separate evidence, not an equivalent number of hardware-parity tests. Native agreement with an independent mathematical reference verifies implementation of that model; only hardware comparisons assess the measured hardware behavior. Neither establishes complete product readiness.
## Working order and evidence

Prioritize the standalone while preserving the runtime boundary for VST3. The initial boot/load/play and live-screen path is working; the next implementation order is:

**Milestone 1 is closed. Next: Milestone 2 interface delivery, then Milestone 3
standalone product acceptance.** Native processing, selection, bounded state,
recovery and the reviewed distribution artifact have evidence. Keep the
approximately279ms software delay and same-build snapshot limits explicit.
Actual device/DAW/editor, sampling and full product-release gates remain open
in their assigned milestones; no requirement was dropped by the scope split.

1. Finish media lifecycle handling: firmware empty-drive behavior and shutdown/crash recovery. Controller-level dirty protection and acknowledged insertion/export are verified. The observed firmware Save/export/fresh-reload path now passes; formatting and write-protection remain unqualified.
2. Extend the completed bounded session recall with missing/relocated-media handling and user-facing recovery of saved sessions; define treatment of unsaved edits.
3. Add audio device/input configuration and prove the firmware sampling → save → reload workflow; qualify physical MIDI and latency.
4. Finish the full React rack controls, first-run setup, persistent settings and recovery flows.
5. Run sustained and clean-machine standalone acceptance, then qualify the already connected C++ VST3 client against the actual SDK/host/editor. Defer actual DAW/framework validation until that framework is available; standalone work need not wait for it.

For each item, add a failing regression or acceptance test, implement the behavior, verify it against the native machine and refine it before marking completion. Keep blocking transport, UI and disk operations outside future realtime callbacks. Hardware work can proceed independently when it does not alter the runtime contract.

The standalone checkpoint is documented in local shared finding127. Reproduction entry points are [the native runtime regression](../scripts/verify_native_runtime.py), [the browser smoke test](../google-ui/e2e/native-runtime.spec.ts), [the player runbook](STANDALONE_PLAYER.md) and [the runtime contract](NATIVE_RUNTIME_PROTOCOL.md). Packaged and audio evidence are distinct checks; neither yet covers the full release workflow.

Keep live coordination and evidence requests in the local shared findings folder; keep scratch in the assigned private work folder. Publish durable conclusions in `docs/condensed` and link release-relevant evidence here. The native checkpoint is commit-ready development work; it is not a completed standalone/VST release.
