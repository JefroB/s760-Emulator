# S-760 completion roadmap

**Milestone 1 complete (2026-10-11):** One native engine now serves standalone and exported-module displays, MIDI, audio and bounded same-build state. Lifecycle, recovery, timing and the exact Windows standalone distribution profile have acceptance evidence. The remaining mixed objective is split below: configuration/editor delivery belongs to Milestones 2/4, native sampling to 3/4, and real DAW acceptance to 4. These remain open. [Closure and evidence](MILESTONE_1_COMPLETION.md).

Updated 2026-10-14. This is the active roadmap for delivering a standalone sampler and VST3 instrument with the React interface displaying authentic MAME CRT/LCD output. Update checkboxes only with recorded evidence; compilation and mock tests do not establish a working product.

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
- [x] Complete native-only exported-module selection and route supported project snapshots through that same instance. Factory startup/failure and independent-instance tests pass; bounded native/host/SCSI state restores with exact PCM. Unsupported input clocks reject explicitly. Graphical configuration/editor delivery is tracked in Milestones 2/4; native sampling in 3/4; actual SDK/DAW acceptance in 4. [Selection](NATIVE_PLUGIN_SELECTION.md), [state](NATIVE_PLUGIN_STATE.md) and [closure](MILESTONE_1_COMPLETION.md).
- [x] Report missing firmware, process startup failure and handshake failure in the standalone launcher; report MIDI discovery failure while preserving audition.
- [x] Expose explicit firmware boot/load readiness and recovery in the UI. OS 2.24 screen observations distinguish booting, Perform Play ready, disk activity/idle, unknown, timeout/stall and process failure. Reconnect preserves the patch; confirmed restart protects live dirty/busy media and recovers a failed child to a fresh boot. [Acceptance and limits](NATIVE_FIRMWARE_STATUS.md).

Acceptance met: native and exported-module harnesses boot, load ROBOFULL through firmware controls, deliver authentic frames and exact reference PCM, schedule/release MIDI, restore supported state and shut down/reopen isolated instances. The packaged desktop independently returns live firmware pixels. Evidence and profile limits are collected in the [closure review](MILESTONE_1_COMPLETION.md).

## Milestone 2 — Live React displays and controls

**Complete for the qualified Windows development profile (2026-10-11).** Native controls, original firmware displays, media loading, audio and editor reopening pass in SoundCheck. The Input Level control is explicitly assigned to the existing native recording dependency in Milestone 3 below; standalone Input Level is now qualified below, while VST host input routing remains open. Analog knob taper/full IC20 fidelity, packaged release and broader DAW acceptance are not claimed. [Rack contract and evidence](NATIVE_RACK_CONTROLS.md).

Depends on milestone 1.

- [x] Deliver native CRT and LCD frames to the existing React canvas consumers, with correct geometry, palette and scaling. Native player and conversion tests; remaining hardware display-mode fidelity is tracked separately.
- [x] Connect mouse movement/buttons, 13 panel buttons, raw floppy insertion and MIDI audition to the live native machine; preserve Mouse+CRT defaults for new profiles.
- [x] Connect native panel keyboard shortcuts, suppress repeat/text-field/dialog input and release held controls on blur. Real MAME Mode-menu navigation passes.
- [x] Wire the separate Menu button to the schematic-confirmed encoder push switch (SC0/SP4). Original firmware Perform menu opens in native MAME and through the SoundCheck React editor; releases on blur. Mixed panel/mouse positioning is now verified after the BUG-030 correction.
- [x] Complete Value and Output controls in the approved rack shell. Value rotation reaches the IC20 register and edits the original firmware in both directions, without S1/S2 substitution; the separate Menu push, navigation/F1–F6/Shift controls, LCD and Gotek remain intact. Output has exact software attenuation/mute, confirmed readback across editor reopen and native checkpoint recall. SoundCheck verifies the real controls and expected PCM. Input recording gain is explicitly retained in Milestone 3; physical pot taper and full quadrature timing remain fidelity work. [Contract and qualification](NATIVE_RACK_CONTROLS.md).
- [x] Host the standalone React player in WebView2 with live frames and controls; closing its window shuts down its machine.
- [x] Implement the concrete C++ WebView2 environment/controller, lifetime, resize and message/frame transport. Real runtime harness passes text/frame round trips, resize, pending-create cancellation and reopen. Opt-in Windows x64 build; [evidence and limitations](MILESTONE_2_PROGRESS.md).
- [x] Qualify Windows x64 plugin discovery and concrete React editor boot, screenshot capture, close/reopen and removal in SoundCheck 1.0.0 using its native SDK host. Independent SDK interface tests also pass; see [host evidence](MILESTONE_2_PROGRESS.md).
- [x] Qualify loaded-sample audio alongside editor operation in SoundCheck and deliver actionable plugin configuration/failure reporting. Actual firmware Disk/Load, expected 20,004Hz fixture playback/level, editor reopening during the held note and silent release pass at 44.1 kHz. Persistent settings, setup/check/diagnose commands, malformed/missing-path diagnostics and successful repair pass without runtime/UI environment overrides. [Configuration workflow](NATIVE_PLUGIN_CONFIGURATION.md). In-plugin graphical setup remains the existing Milestone 4 gate; this is development-host qualification.
- [x] Implement matching embedded transport in the React bridge client: detect WebView2, canonical control JSON, bounded frame envelope, shared decoder and listener cleanup. Mock-channel tests complement the real C++ runtime harness; integrated plugin acceptance remains above.
- [x] Deliver a transport-independent React firmware/media/runtime settings form and actionable startup errors, connected to the standalone host. Missing firmware can be corrected without exiting; paths validate before replacing a machine, dirty/busy media blocks replacement, and successful settings persist. Real native setup/relaunch tests pass. The plugin adapter and host-visible errors remain part of plugin integration above and Milestone 4.
- [x] Schedule concrete embedded-editor frames on the UI thread and remove the timer on close. Real WebView2 automatic-frame/reopen acceptance passes; native audio continuity remains below.
- [x] Populate the native player's floppy selector from the configured media folder and insert a private working copy; load through firmware Disk/Load.
- [x] Report acknowledged insertion/export results and rejected media changes in the native player.
- [x] Discover the embedded host's default floppy inventory and retain confirmed media across editor recreation. Bounded startup scan of `roms/FDD/*.IMG`, host-owned list and confirmed full path, Gotek controls, rejected insertion and SoundCheck close/reopen checks pass.
- [x] Complete configurable/recursive full-rack media libraries and session serialization. The existing Select dialog configures recursive folders; the host preserves independent browse/inserted identities across editor reopening and version-2 plugin-state recall. SoundCheck UI acceptance and native cold restore with relocated source files and exact PCM pass. Explicit scan limits and v1 compatibility are documented in [Native media library](NATIVE_MEDIA_LIBRARY.md).
- [x] Verify concrete editor-controller close/reopen with built React and the native plugin engine: same MAME process, advancing displays and exact reference PCM at 44.1/48/96 kHz. This is a native harness, not actual SDK/DAW hosting; that gate remains above. Standalone window closure intentionally ends its session.
- [x] Route supported C++ embedded panel/pointer commands to the native machine and reject unsupported legacy clicks and unknown dial IDs; bounded Value/Output commands use the native path. Firmware Mode-menu navigation passes through the bridge; complete rack controls and host-visible error UX remain above.

Acceptance: from React, observe firmware boot, insert/load a sample disk, navigate and edit via real controls, then play MIDI and hear audio. Screens must agree with native MAME, including cursor and highlight behavior.

## Milestone 3 — Packaged standalone

**Complete for the qualified Windows development profile (2026-10-13).** All
standalone objectives below have recorded evidence. By user direction, production
ADC alternate clocks, driver-level loss measurement and hardware register/meter
qualification now belong to Milestone 5. The supported 44.1 kHz MME/ASIO sampling
profiles remain opt-in. Clean-machine installation and final artifact acceptance
remain Milestone 6 release gates.

Depends on milestones 1–2.

- [x] Build a Windows standalone executable using MAME system audio; expose on-screen audition and enumerated MIDI input selection.
- [x] Expose persistent standalone Windows audio backend and buffer-target settings, with bounded validation and restart confirmation. Normal-speed WASAPI/60 ms target passes firmware load/play/release and clean shutdown; native PCM remains 44.1 kHz. The requested target is explicitly distinct from measured device latency. [Configuration and limits](STANDALONE_PLAYER.md).
- [x] Qualify normal audio device reopening/error recovery, Windows non-ASIO output endpoint selection, negotiated output conversion, bounded sustained playback and reported measured latency. Native44100Hz output reaches the selected Windows48000Hz endpoint with expected pitch and silent note-off; packaged selection/reconnect persists. Injected closed-stream failure pauses the sampler; reopening the actual MOTU driver preserves the same native process and media. Five-minute/150-note physical MIDI playback reports zero output underruns/discards/native drops/driver flags, with2048 input frames discarded. The16384-frame transport target (371.52ms) is shown separately from driver latency. Physical bridge arrival upper bounds10.45–88.43ms exclude MAME/MIDI transport. These are supported-profile measurements, not indefinite continuity or full instrument latency claims. Physical unplug/replug tests were removed by user direction. [Device qualification](condensed/validation/standalone-audio-devices-2026-10-12.json).
- [x] Verify physical standalone MIDI playing through micro lite Port 5 out-to-in: original firmware ROBOFULL responds to note-on, note-off returns to silence, software input detach ignores physical notes and reselect restores playback. A 180-second/90-note-cycle run produces all 90 native note pulses with a silent release tail and finite PCM. MOTU physical audio loopback confirms output. Sustained ASIO output underruns are reported separately as BUG-047; this is MIDI acceptance, not zero-loss audio or physical hotplug acceptance.
- [x] Package built React assets locally; launch without Vite, a terminal or a manually started bridge service. Development Windows package verified through WebView canvas readback; clean-machine release qualification remains open.
- [x] Accept explicit firmware/media/state paths, stage selected system firmware per instance and verify clean desktop shutdown. Firmware and samples are excluded from the package.
- [x] Add first-run firmware/media location setup and persistent settings, with recovery from missing paths and actionable UI errors. The source standalone recovers from a missing ROM through React and relaunches from saved settings; changed packaged-build and clean-machine acceptance remain release gates.
- [x] Complete the observed firmware floppy Save path and explicit export to a new image; verify fresh-machine sample reload and audio while preserving library originals.
- [x] Reject busy/dirty controller media replacement and ejection; clear dirty state only after publication of the captured revision. Verify native Save/export/reinsert and fresh reload.
- [x] Qualify OS 2.24 empty-drive behavior and expose acknowledged Eject in standalone. Firmware requests a disk, clock/controller remain responsive, empty export rejects, reinsertion loads ROBOFULL, and loaded playback/release survives ejection. Native and real-browser workflows pass; busy/dirty protection remains enforced. [Media/session evidence](condensed/validation/standalone-media-session-2026-10-12.json).
- [x] Add acknowledged standalone floppy write protection and preserve it in same-build session recall. OS 2.24 Save displays Write Protected, leaves the image byte-exact and clean, and succeeds after unprotecting; fresh reload reproduces all 13 sample payloads and native playback/release. [Evidence](condensed/validation/standalone-write-protection-2026-10-12.json).
- [x] Qualify OS 2.24 native 720KB floppy formatting through Disk Utility. Validated IC4 CHRN DMA fills all 160 tracks, firmware writes its formatted-disk header, protected Format preserves all bytes, and dirty formatted state recalls in a fresh process. Subsequent Save/export/fresh reload preserves all 13 sample payloads and playback/release. The packaged browser Format/export workflow passes. BUG-041 fixed for this profile; HD/foreign-format and physical FDC timing are not qualified. [Evidence](condensed/validation/standalone-formatting-2026-10-12.json).
- [x] Add bounded automatic and normal-close recovery for the supported standalone floppy profile. A separate checkpoint runs every60 host seconds after firmware boot, defers while the controller is busy, preserves dirty media and never overwrites manual saves. Normal desktop close saves recovery or cancels on failure; explicit Quit without recovery requires confirmation. Startup/restart/settings/manual restore preserve existing recovery until the user restores it or starts a new history. Native dirty child-failure/close replay, real production-timer/browser recovery and packaged WebView close pass. Changes after the last successful recovery can still be lost; connected physical MIDI blocks checkpointing, audio briefly pauses, and power-loss/filesystem durability or zero-loss journaling are not claimed. [Evidence](condensed/validation/standalone-auto-recovery-2026-10-12.json).
- [x] Implement the observed OS 2.24 A7 wave-to-RAM DMA used by sampling postprocessing. Firmware Start now exhausts the DMA count and reaches waveform review instead of hanging; the preserved previous binary fails the same regression. Bounded read-only bus diagnostics preserve exact 131072-frame native PCM/display replay. BUG-043 fixed for this synchronous transfer profile; this does not qualify recorded input. [Sampling implementation and limits](NATIVE_SAMPLING.md).
- [x] Add a standalone-only Configuration screen for acknowledged MIDI selection, existing audio output/backend/buffer settings and firmware/media paths, plus a 61-key on-screen keyboard hidden by default with persistent opt-in visibility. Held notes release on pointer/keyboard release, hide/blur and teardown.312 backend/117 React tests, packaged browser preference/audio-restart workflow and actual WebView boot pass. The VST editor continues to receive MIDI/audio from its host. Output endpoint/capture device and physical acceptance remain in the open objectives. [Configuration evidence](condensed/validation/standalone-configuration-2026-10-12.json).
- [x] Restore standalone/VST visual parity (BUG-044, user-assigned S1): shared rack and CRT housing/crop, working Gotek browsing/select, aligned 61-key keyboard, gear configuration containing session/media utilities. [Visual parity evidence](condensed/validation/standalone-visual-parity-2026-10-12.json).
- [x] Implement and qualify an opt-in offline native ADC transport profile: bounded44.1kHz stereo PCM16 queue, atomic format/overflow rejection, firmware recording and exact L/R Sample Save/export/cold Load.56,661 frames/channel match the known input;239,616 allocation bytes survive reload with zero recording underruns. This is not device capture or hardware parity. [Sampling evidence](condensed/validation/native-sampling-input-2026-10-12.json).
- [x] Deliver standalone recording-device selection and bounded live transport for Windows MME 44100 Hz stereo PCM16; source and packaged browser apply/restart/reconnect, unsupported/missing/stalled-device errors, checkpoint discontinuities and physical firmware capture pass. Windows interface negotiation is qualified; physical converter clocks and conversion are not inferred. [Evidence](condensed/validation/native-physical-sampling-2026-10-12.json).
- [x] Offer ASIO in standalone Configuration with persistent driver, stereo input/output pairs and buffer selection. Native callback uses preallocated lock-free rings; actual MOTU128/512/1024-frame duplex tests, native ROBOFULL playback/release, exact ASIO firmware capture/Save/fresh Load, source/package browser settings and actual WebView boot/close pass.341 backend/121 React plus native core/plugin/ASIO queue tests pass. Driver-reported latency is shown separately from transport; broader clocks, hotplug and sustained physical latency/dropout qualification remain open. [Evidence](condensed/validation/standalone-asio-2026-10-12.json).
- [x] Enable and qualify the standalone rack Input Level with the native ADC path: independent0–100% recording gain, acknowledged UI readback and same-build session recall. Original firmware records exact unity/half-gain/muted L/R PCM after cold restore, with Output Level muted, zero input underruns and exact Sample Save/export/fresh Load.322 backend/119 React tests, source and packaged browser gain/reconnect/restore and actual WebView boot pass. Service Notes p20 places recording gain before conversion; physical pot taper/headroom remain uncalibrated. VST host input routing and physical capture devices remain separate. [Evidence](condensed/validation/native-input-level-2026-10-12.json).
- [x] Verify external audio input reaches firmware sampling and saved samples reload correctly for the supported 44.1 kHz stereo profile. MOTU ASIO outputs 3/4 physically looped to Windows MME inputs 1/2: original firmware records 65,514 frames/channel, exactly matching a contiguous captured device PCM interval; all 276,480 allocated sample bytes survive Save/export/fresh Load. Normal-speed capture reports zero native input underruns; 18,432 discarded frames across the full workflow are reported explicitly. Missing/unsupported/stalled inputs fail visibly. Production ADC semantics, alternate rates, physical driver loss accounting and measured latency remain separate. [Evidence](condensed/validation/native-physical-sampling-2026-10-12.json).
- [x] Implement bounded same-build standalone saved-session recall through the native engine; cold PCM/display replay and explicit recovery of the last save pass. [Contract](NATIVE_SESSIONS.md).
- [x] Complete standalone session handling for the supported same-build floppy profile: relocated firmware paths and absent source libraries/private insertion files recover from embedded media; version/build/firmware/integrity failures explain repair and reject before changing the live machine. Explicit confirmation states that edits after the last save are lost; no autosave is claimed. Native cold replay reproduces 131072 stereo frames and both displays, and real-browser recovery/mismatch workflows pass. External SCSI files still require matching names/content; changed-package and clean-machine release qualification remain separate. [Session contract](NATIVE_SESSIONS.md).

Acceptance for this development milestone: the packaged Windows standalone boots, loads, plays, samples, saves, quits and reopens with user-supplied firmware in the qualified local environment; device settings and dropout/latency limits are recorded above. Repeat the full workflow on a clean Windows environment for Milestone 6 release acceptance.

## Milestone 4 — Supported VST3 host workflows

**Complete for the documented Windows x64 SoundCheck development profile.**
SoundCheck is the accepted automated DAW/host framework. This milestone covers
plugin integration: configuration, MIDI/audio processing, recording, editor
lifecycle and same-build project recall. Firmware editing/loading coverage belongs
to Milestone 5; final shipped artifacts and installation belong to Milestone 6.
Other DAWs, stock SoundCheck GUI project containers, Live Sampler FX and project
migration across builds/rates/negotiated maxima are follow-on work. Existing
44.1/48/96 kHz output qualification remains valid; recording stays within the
qualified opt-in 44.1 kHz stereo input profile. No new execution evidence is
claimed by this scope rewrite (2026-10-14).

Controller follow-up (2026-10-13): the current WebView module and native QA host
pass the unchanged55-case matrix. A preceding intermittent audio-block rejection
during controller-assignment UI editing was tracked as BUG-060. The2026-10-14 functional-QA correction explicitly negotiates offline processing;64 unpaced blocks and55 measured controller cases pass. This fixes the verifier contract rather than suppressing realtime deadline faults. [QA correction](condensed/validation/bug-060-qa-processing-contract-2026-10-14.json).
[Current-artifact requalification](condensed/validation/milestone-4-controller-requalification-2026-10-13.json).

Depends on milestone 1; editor delivery also requires milestone 2.

- [x] Connect exported-module processing and bounded suspended state to the unified native engine, with no fallback to the historical core. Completed in Milestone 1; real host/ABI acceptance remains below.
- [x] Deliver graphical plugin configuration and host-visible startup errors, including persistent firmware/media settings and recovery from invalid paths; use the shared Milestone 2 interface. SoundCheck verifies a silent missing-firmware instance, visible errors, rejected-change preservation, UTF-8 media paths, editor reopen and successful host reload. Applying settings requires reload; damaged installations without editor assets require repair. [Configuration contract/evidence](NATIVE_VST3_CONFIGURATION.md).
- [x] Qualify the actual VST3 SDK/ABI, discovery/metadata/bus descriptions and scan/load in a named real DAW or native QA host. Independent Steinberg-header probe and SoundCheck 1.0.0 Windows x64 native host pass on the current module; stereo output and 16-channel MIDI input are described, and optional stereo input is now qualified below. Factory2 vendor/version and Instrument|Sampler metadata pass independent SDK and SoundCheck discovery; other DAWs are not inferred. [Qualification](condensed/validation/milestone-4-sdk-host-2026-10-12.json).
- [x] Honor note-on/off sample offsets and release through the native processor at all three supported host rates. Paced varying-block renders match the independent native reference exactly; SoundCheck loaded-sample release is silent. [Processing evidence](condensed/validation/milestone-4-processing-lifecycle-2026-10-12.json).
- [x] Deliver bounded native VST3 MIDI controller transport: actual SDK mapping/parameter queues, CC0–127 and14-bit bend on16 channels, exact varying-block native reference replay, and SoundCheck automation with measured volume, sustain and CC123 release. Independent channel15 CC123 leaves channel0 playback intact. [Controller contract/evidence](NATIVE_VST3_MIDI.md).
- [x] Complete configured audible pitch bend, other controller effects and panic/reset qualification. Completed for the original-firmware Windows native QA profile on 2026-10-13: configured Bend Up/Down12, CC11 expression, assigned CC1 modulation, stereo CC10 pan (BUG-056 fixed), CC7 scaling, ordered RPN bend-range/null handling, sustain-aware CC123–127 release, and explicit bounded all-channel panic/neutral-reset sequences pass.55 measured SoundCheck cases, three-rate exact native PCM and cold state replay provide acceptance evidence. Raw CC120/121 remain explicitly unsupported by this firmware profile; the tested supported-message sequences provide panic/reset. Hardware fidelity and other DAWs remain separate. [Controller contract and evidence](NATIVE_VST3_MIDI.md).
- [x] Support negotiated sample rates and varying block sizes with bounded audio buffers. Native processor qualification passes at 44.1/48/96 kHz with 64/127/256/511/1024-frame callbacks, exact independent-reference PCM and no missed callback deadlines in each 12-second paced profile. Fixed queues keep rendering/runtime I/O off the callback; unsupported rate/block/sample-size configurations are rejected. A started stream rejects rate changes to preserve queued state. [Processing evidence](condensed/validation/milestone-4-processing-lifecycle-2026-10-12.json).
- [x] Qualify native instrument output buses, latency/tail reporting, suspend/resume and offline rendering in the Windows native QA host. SoundCheck realtime playback with held-note suspension and unpaced offline bounce match exactly; independent native renders agree at all three supported rates. SDK latency reporting and infinite-tail reporting pass. [Rendering contract and limits](NATIVE_VST3_RENDERING.md).
- [x] Route host sampling input through the same native ADC path delivered in Milestone 3 and qualify actual host input buses and recording. Completed for the Windows native instrument QA profile on 2026-10-13: optional 44.1 kHz stereo float32 input, inactive by default, passes actual SDK/SoundCheck buses, varying 64–1024-frame callbacks and aliased input/output buffers. Original firmware records 45,649 exact frames/channel with zero ADC underruns; all 184,320 allocation bytes survive Sample Save/export/fresh native Load. Strict paced active-input and three-rate output replay pass with zero missed deadlines. Unsupported input clocks/disconnections reject explicitly; Live Sampler FX remains unadvertised. Other DAWs and hardware fidelity remain separate. [Input contract and evidence](NATIVE_VST3_SAMPLING.md).
- [x] Implement versioned bounded native/host project snapshots with integrity/identity checks and exact cold replay at all three supported rates. [State contract](NATIVE_PLUGIN_STATE.md).
- [x] Qualify disk-backed same-build project save/cold host reopen in SoundCheck1.0.0 Windows x64 at44.1kHz/512 frames. Persisted local product settings select relocated matching firmware/media; embedded floppy state and captured media references restore with the original library and private runtime paths absent. Full-rate host L/R-average PCM matches221184 frames exactly with silent release; corrupt-file rejection preserves exact replay. [State contract and evidence](NATIVE_PLUGIN_STATE.md).
- [x] Verify project save/reopen and portability across the supported SoundCheck host matrix (SoundCheck accepted as the DAW by user direction). The versioned project-document runner selects project-local configuration and saved host settings, validates module/runtime/firmware/state identities and restores actual SDK component state in a cold native host. At44.1kHz/maximum512, relocated firmware/library and removed old runtime paths preserve221184 exact L/R-average PCM frames and a silent release tail. Actual callback sizes64/127/256/511/512 also replay exactly; corrupt state preserves the live timeline. A different module build,48kHz recall and a different negotiated maximum reject explicitly; migration is unsupported, not silently approximated. This qualifies the private SDK adapter/project runner, not the stock SoundCheck GUI or another DAW's container. [Project contract and evidence](NATIVE_PLUGIN_STATE.md#soundcheck-project-document--2026-10-14).
- [x] Verify two independent instances, editor resize/reopen, plugin removal and host shutdown for the Windows x64 native QA profile. SoundCheck verifies separate gain/media, removal of one instance preserving the other and reopened settings; the independent Steinberg SDK host verifies attached editor resize/readback at three sizes. Loaded SoundCheck audio survives editor reopen. Explicit removal followed by host exit leaves no native children. Shutdown with active instances/crash recovery and other DAWs are not inferred. [Lifecycle evidence](condensed/validation/milestone-4-processing-lifecycle-2026-10-12.json).

Acceptance: the actual VST3 module scans and loads in the accepted SoundCheck SDK host; host MIDI plays/releases notes and controls the firmware, optional input records through the firmware, same-build projects cold-reopen, independent instances remain isolated, and offline bounce agrees with realtime playback. Record host/version, rates, blocks, artifact identities and limitations. MIDI event transport is qualified; this does not claim a DAW MIDI-track recording workflow. BUG-060 is corrected as a functional-QA processing-contract defect; final-artifact realtime reliability still requires the separate release checks.

## Milestone 5 — Supported sampler workflows and defaults

**Complete for the documented Windows development profiles as of2026-10-14.**
The last concurrency gate is resolved against the original firmware's documented mute/recovery behavior below. Final shipped-interface, changed-artifact and clean-machine acceptance remains Milestone6.

Required for the product completion claim; can proceed alongside integration.
The goal is a reliable original-firmware sampler within the documented Windows
profile, rather than complete hardware equivalence. Firmware Load remains in
scope, including SCSI Load. Recording uses the qualified opt-in 44.1 kHz stereo
MME/ASIO standalone and SoundCheck host-input profiles. VST3 output remains
qualified at 44.1/48/96 kHz; host output conversion does not expand ADC scope.

Scope revised by user direction on 2026-10-14. Completed subsets below retain
their dated evidence; scope changes alone do not establish qualification.
See the [workflow acceptance matrix](MILESTONE_5_ACCEPTANCE.md) for supported
profiles, commands, expected results, evidence classes and pending coverage.

- [x] Qualify supported MIDI/controller and stereo-routing workflows: configured bend/expression/assigned modulation, CC7/10/64, RPN range/null handling, channel-mode release and documented panic/reset sequences. Fresh-note pan reaches the expected channel. Raw CC120/121 remain unsupported. [Controller evidence](condensed/validation/milestone-4-controller-semantics-2026-10-13.json) and [current-artifact repeat](condensed/validation/milestone-4-controller-requalification-2026-10-13.json).
- [x] Qualify standard 720 KB floppy Load/Save/export, write protection, Format and supported stereo recording Save/cold Load. Recorded sample bytes survive fresh original-firmware Load. [Formatting](condensed/validation/standalone-formatting-2026-10-12.json), [write protection](condensed/validation/standalone-write-protection-2026-10-12.json), [physical recording](condensed/validation/native-physical-sampling-2026-10-12.json) and [SoundCheck recording](condensed/validation/milestone-4-host-sampling-2026-10-13.json).
- [x] Correct and qualify the native SCSI register/selection prerequisites: even-byte register stride2 through TEMP/transfer-counter ports, native SELECT/interrupt write acknowledgement and true absent-target behavior. BUG-062/063/064 are fixed; isolated native regression, preserved legacy fixtures, native audio/MIDI and131072-frame cold state pass. This is device-level evidence, not firmware SCSI Load acceptance. [Prerequisite evidence](condensed/validation/milestone-5-scsi-prerequisites-2026-10-14.json).
- [x] Correct native SCSI idle/counter/reset status (BUG-065): failing-before/passing-after device regression, original-firmware audio/MIDI and exact cold state pass. Firmware discovery still reports No Drive; transfer/IRQ and media qualification remain open. [Status evidence](condensed/validation/milestone-5-scsi-status-2026-10-14.json).
- [x] Qualify original-firmware SCSI discovery and unsupported-media recovery for the native HD0/512-byte-sector development profile: absent target shows No Drive; private blank10MiB and truncated1024-byte images show Unformatted and report Not Formatted when selected. Each case recovers to exact119808-byte floppy sample Load, playback and silent release with unchanged media. BUG-066/068/069 correct native initiator masks, command ACK/REQ and observed bounded input DMA47; isolated native fixtures, legacy state,131072 exact cold stereo frames and363 backend tests pass. Bounded trace drops and synchronous DMA timing limits are explicit. [Discovery evidence](condensed/validation/milestone-5-scsi-discovery-2026-10-14.json).
- [x] Provide8/16/32 MB native wave-memory configurations, default32 MB, through standalone and VST3 settings and setup tools. Original firmware reports the selected capacity and90.8/181.8/363.8 seconds; native capacities, same-size checkpoint round trips and different-size restore rejection pass. Backend388/UI126 regressions and actual VST3 default-profile playback pass. Successful Akai/SCSI Load remains a separate gate below. [Memory evidence](condensed/validation/milestone-5-wave-memory-2026-10-14.json).
- [x] Qualify genuine Akai S1000 CD1/2048-sector Convert Load through original firmware: first String.Ensembles volume imports VI LONG FF and30 samples/13,568,196 PCM bytes into32 MB RAM. Every PCM word matches source data or a specifically observed original-firmware loop-tail rewrite; raw source values precede each rewrite. Assign the imported patch to a performance part, play three keys with silent release, preserve the source/backing CD and replay65536 exact stereo frames from two cold processes. This is the named foreign-format native Load subset, not SCSI Save or final shipped-interface qualification. [Akai Load evidence](condensed/validation/milestone-5-akai-scsi-load-2026-10-14.json).
- [x] Qualify the named native Roland-format SCSI performance/sample Load subset: full606,709,760-byte JMD CD1 is Formatted, lists10 volumes and loads K4 :KAWAI K4 with its native patch/partial/sample hierarchy. All79 sample allocations/6,054,912 bytes match source FAT chains exactly; three mapped drum notes and a channel2 melodic note play/release silently. Two fresh processes reproduce65536 exact stereo frames; changed-CD recall rejects. BUG-070 separates external immutable CD identity from bounded writable checkpoint data; BUG-071 supplies observed DMA84/full SPC counts.389 backend tests, native C++ host, writable SCSI state and prior native register/PIO/DMA checks pass. Other libraries, SCSI Save and final shipped-interface repetition remain separate. [Native Roland Load evidence](condensed/validation/milestone-5-roland-scsi-load-2026-10-14.json).
- [x] Qualify the named patch-edit/Save/fresh Load subset through native firmware controls: ROBOFULL Patch Control Bend Up/Down0 to12 via Value increments, observable audible bend, firmware performance Save/export and separate-process cold Load with fresh runtime/NVRAM. Centre/up/down frequencies and peaks match the edited result after reload; all auditions release silently and original library/input images remain unchanged. This is native control acceptance, not final shipped-interface qualification. [Patch-edit evidence](condensed/validation/milestone-5-patch-edit-2026-10-14.json).
- [x] Qualify the named performance-edit/Save/fresh Load subset: Perform Play1 part1 Level127 to64 through firmware Value input, measured attenuation to0.503743 of the original peak with unchanged pitch, firmware performance Save/export and fresh-process Load reproducing edited frequency/peak and silent release. Original library/input images remain unchanged. This qualifies the part-level operation, not every performance parameter or master-level persistence. [Performance-edit evidence](condensed/validation/milestone-5-perform-edit-2026-10-14.json).
- [x] Qualify the named partial-edit/Save/fresh Load subset: Partial Common Coarse Tune0 to12 through firmware Value input raises ROBOFULL note21 from248Hz to495Hz (1Hz FFT resolution). Original-firmware performance Save/export and separate-process Load reproduce edited frequency/peak; all auditions release silently, and original library/input images remain unchanged. This qualifies coarse tuning, not all partial parameters. [Partial-edit evidence](condensed/validation/milestone-5-partial-edit-2026-10-14.json).
- [x] Qualify the named destructive sample-edit subset: whole-range Area Erase, zero fade, on ROBOFULL sample1 through firmware controls. The4096-frame body is zeroed, playback becomes exactly silent, firmware Save/export/fresh Load preserves all9216 allocation bytes and twelve neighboring samples/110592 bytes remain unchanged despite native memory compaction. Named patch bend, performance part-level and partial coarse-tune workflows above are also complete. This minimal editing matrix does not qualify other sample commands, arbitrary subranges/fades or broader editing combinations; final shipped-interface repetition remains Milestone6. [Area Erase evidence](condensed/validation/milestone-5-sample-erase-2026-10-14.json).
- [x] Qualify bounded allocator/polyphony behavior for the named native fixtures: ROBOFULL allocates 24 simultaneous voices; eight excess notes each recycle a slot (24 to 23 to 24), original-note release preserves eight replacements, and replacement release clears the pool. Eight retriggers and sustain hold/release pass with counted enable slots and silent tails. Short-sample mixed-mode completion/retrigger is covered by the loop evidence below; documented panic/reset is covered by the controller gate above. No exact steal-order, arbitrary layered-patch allocation or disk-overlap claim is made. [Allocation traces and PCM evidence](condensed/validation/milestone-5-polyphony-2026-10-14.json).
- [x] Qualify bounded original-firmware floppy Load under dense scheduled MIDI: ten twelve-note bursts (240 serial events) overlap observed FDC commands; all 13 sample payloads/119,808 bytes remain exact, media ends idle/clean and post-load playback releases to a full second of silence after explicit cleanup. Partial read-only trace observes 152 overlapping FDC writes; its dropped rows preclude exhaustive arbitration claims. Serial delivery does not establish guest event handling during Load. [Native evidence](condensed/validation/milestone-5-disk-midi-2026-10-14.json).
- [x] Qualify the bounded Disk/Load directory restriction and recovery subset: Perform control exposes12 source2 completion-status slots, while three directory/MIDI trials clear playable voices before FDC commands and allocate no new notes despite24 serial events per trial. Complete narrow traces show no source2/FDC overlap. Return-to-Perform playback/releases pass; media is idle/clean and exports byte-exact. Do not rely on note preservation or musical continuity in this Disk/Load workflow. [Restriction/control evidence](condensed/validation/milestone-5-disk-voice-restriction-2026-10-14.json).
- [x] Complete the supported disk/MIDI/voice restriction and recovery contract. Owner's manual Advanced1-3 (PDF page11) explicitly excludes sound in Disk, Quick Load and Sampling displays, and during commands such as Copy. This corrects the former unsupported requirement to find a disk operation permitting ongoing voices; no three-source overlap is qualified. Native performance Save clears four active notes, completes under240 scheduled MIDI events with166 observed overlapping disk writes, stays silent for1543500 captured frames, returns without stuck voices and preserves13 allocations/119808 exact bytes through fresh Load. Three repeated Disk/Load trials retain12 source2 control requests and zero restricted overlap. Original images remain unchanged. Partial Save trace supports positive overlap only; exact IC4 timing remains research. [Restriction/recovery evidence](condensed/validation/milestone-5-concurrent-recovery-2026-10-14.json).
- [x] Qualify all seven firmware playback modes at native 44.1 kHz/unity pitch through original-firmware Load: five repeating modes match expected sign/direction sequences, both one-shots finish while held, and all modes release to silence. Eight mixed-mode retrigger cycles (112 note-ons) replay 1,058,400 stereo frames exactly from a same-process checkpoint with silent release tails. This does not establish voice-stealing counts, disk overlap or hardware parity. [Current native evidence](condensed/validation/milestone-5-loop-modes-2026-10-14.json).
- [x] Extend playback-mode acceptance to named practical octave changes and transitions: all seven modes at -12/0/+12 semitones pass expected firmware pitch writes, repeating-loop recurrence (>0.99 correlation), scaled one-shot durations and silent release. A 42-note overlapping transition sequence is finite/bounded and ends with a full second of silence. This qualifies the named key/partial pitch changes, not arbitrary pitch ratios, continuous glide or click-free transitions. Existing configured bend has separate controller evidence. Physical interpolation fidelity remains limited to its measured domain. [Native pitch/loop evidence](condensed/validation/milestone-5-loop-pitch-2026-10-14.json).
- [x] Qualify the explicit diagnostic combined envelope/filter/stereo/interpolation path on72 named cases: bypass, three static LP cutoffs, static resonant LP and nonresonant LP/BP/HP sweeps, each at MIDI57/60/63 and left/center/right pan. Finite bounded output, expected cutoff/sweep effects, forward-loop playback and a full silent release second pass. This is native diagnostic functional acceptance, not promotion into normal defaults or physical moving/resonant parity; BUG-005 remains open. [Combined-path evidence](condensed/validation/milestone-5-combined-audio-2026-10-14.json).
- [x] Establish the normal standalone stereo/interpolation/envelope subset and preserve explicit opt-ins: BUG-061 corrected by always enabling the existing stereo mixer, matching the plugin launch policy. Six normal-profile pan cases, native boot/load/release, variable-block PCM and scheduled MIDI pass; cold scheduled recall reproduces131072 stereo frames and refreshed displays exactly. Recording remains opt-in and inherited flags cannot change the selected profile; this dated stereo record precedes the filter-default qualification below. Its changed audio-profile identity rejects old mono-path checkpoints explicitly. [Normal-default evidence](condensed/validation/milestone-5-normal-stereo-2026-10-14.json).
- [x] Qualify original-firmware HD0/512-sector writes on a private10 MiB HD00_512.img: quick initialization, performance Save, explicit Python HD0 export and fresh firmware Load without a sample floppy. All13 allocations/119808 bytes match the source exactly; playback level/spectrum and silent release survive. Original library/firmware hashes remain unchanged. BUG-072 adds bounded RAM78/waveA0 output DMA and SPC completion. Interrupted-command/bounds/read-only checks, missing-HD0 rejection, existing-output refusal, concurrent-instance isolation and392 backend tests pass. No automatic library overwrite or GUI/VST export claim. [SCSI write evidence](condensed/validation/milestone-5-scsi-save-2026-10-14.json).

- [x] Complete normal filter-default selection and requalification for standalone and VST3: both launchers enable the existing native filter renderer. Normal72-case filter/pitch/pan acceptance and nine actual SoundCheck LP/bypass/pan cases pass, with silent releases and220500 exact fresh-instance/variable-block stereo frames. Active-filter cold recall matches65536 frames; scheduled/SCSI recall, seven-mode stress, firmware edit/Save/fresh Load,48/96kHz host conversion and363 backend tests pass. Supported coefficient words and raw-path exclusions are documented; physical moving/resonant accuracy (BUG-005) remains open. BUG-060 functional-QA processing-contract correction is recorded separately. Changed standalone audio identity and rebuilt-module hashes reject older bypass-profile states. [Normal filter evidence](condensed/validation/milestone-5-normal-filter-2026-10-14.json).
- [x] Publish a reproducible workflow/audio acceptance matrix with commands, source/artifact/fixture identities, expected results and limitations. Distinguish unit/model, native runtime, SoundCheck and physical comparison evidence. Link unresolved product defects and state the supported input/output/media profiles. [Acceptance matrix](MILESTONE_5_ACCEPTANCE.md) links dated identities and commands; pending workflows remain explicit and unqualified.

Acceptance: a user can load through the original firmware, edit, play polyphonically,
record within the supported input profile, Save/fresh Load and restore a session.
Concurrent supported activity must not hang, corrupt media or leave stuck notes.
Every advertised workflow has native evidence; physical parity claims remain
limited to their measured domains. Milestone 6 repeats the complete workflow
against final shipped artifacts.

### Follow-on research and explicit scope decisions

These items no longer block Milestone 5 merely because hardware equivalence is
unproven. A defect that breaks a supported workflow still requires a fix:

- Alternate ADC/sample clocks, additional input-driver profiles, driver-level loss characterization and hardware-exact ADC register/meter semantics. Preserve existing recording evidence and underrun/error checks.
- Exhaustive CPU instruction/cycle, BMOVI applicability, SFR/window, timer, serial and DMA specification audits. Legacy flat/HLE behavior remains diagnostic; supported workflows must continue using the native engine.
- Hardware-exact IC4 priority, vector latching, masking, acknowledgement and interrupt-return timing. Practical concurrent-source stress remains required above.
- Hardware-exact interpolation across other clocks and all pitch transitions, and exact resonant/moving-filter transfer functions. Functional coverage of advertised playback modes remains required above.
- Broader floppy formats beyond the qualified standard 720 KB profile.

**SCSI writes were explicitly authorized on2026-10-14.** The named HD0 workflow above is qualified; other media profiles and packaged-interface export remain separate. The minimal destructive editing subset is the qualified whole-range Area Erase operation above.

## Milestone 6 — Release qualification

Depends on milestones 3–5.

- [x] Add native boot/load/MIDI/audio regression, real-runtime browser smoke and packaged WebView pixel-readback checks alongside unit tests.
- [x] Extend development-profile acceptance to native standalone sampling/Save/cold Load/session restore and real-plugin SoundCheck tests. Physical recording preserves65514 exact frames/channel through firmware Save/fresh Load; standalone cold session replay preserves131072 stereo frames and both displays. SoundCheck covers actual SDK load/audio/MIDI/input/editor/state and cold projects. SoundCheck is the accepted automated DAW framework. [Standalone sampling](condensed/validation/native-physical-sampling-2026-10-12.json), [session restore](condensed/validation/standalone-media-session-2026-10-12.json) and [SoundCheck projects](condensed/validation/milestone-4-soundcheck-project-2026-10-14.json).
- [ ] Complete the remaining standalone edit/sample/save/restore acceptance: a reproducible perform/patch/partial/destructive-sample editing workflow through the final shipped interface. Existing recording, media and session tests are the completed subsets above.
- [x] Run bounded development-profile sustained playback, repeated startup and missing-media/recovery checks. Five-minute/150-note ASIO playback,80 fresh native launches, empty-drive/reinsert, missing library/source recovery, mismatched/corrupt state rejection and periodic/normal-close dirty-media recovery have dated evidence. [Playback](condensed/validation/standalone-audio-devices-2026-10-12.json), [startup](condensed/validation/s2-startup-lcd-2026-10-11.json), [media/session](condensed/validation/standalone-media-session-2026-10-12.json) and [automatic recovery](condensed/validation/standalone-auto-recovery-2026-10-12.json). These are bounded tests of recorded builds, not an indefinite soak or final-artifact reliability claim. BUG-060 is corrected as a functional-QA processing-contract defect.
- [ ] Complete final-artifact sustained and repeated full boot/load/edit/sample/save/reopen cycles, broader malformed-media cases and release recovery stress. The bounded development playback/startup/media/recovery subset above is complete.
- [x] Qualify source/dependency distribution for the exact dated Windows standalone development artifact: accompanying buildable source, notices, dependency identities and firmware/private-capture exclusions are reviewed. [Distribution review](DISTRIBUTION_QUALIFICATION.md). Changed builds, the VST3 package and clean-machine installation require separate qualification.
- [ ] Qualify final standalone and VST3 release artifacts, installers and runtime prerequisites on the supported clean-machine/host matrix. The exact development-stage Windows standalone artifact already has [source/dependency distribution qualification](DISTRIBUTION_QUALIFICATION.md); requalify changed builds and plugin-specific components. Preserve notices/source delivery and exclude proprietary firmware, recordings and private research.
- [x] Publish development-profile setup, troubleshooting and supported-feature contracts, and align current README status with qualified evidence. Standalone configuration/recovery and native plugin MIDI/input/state/project documentation identify supported profiles and explicit exclusions. [Standalone guide](STANDALONE_PLAYER.md), [plugin setup](NATIVE_PLUGIN_CONFIGURATION.md), [controller contract](NATIVE_VST3_MIDI.md), [sampling contract](NATIVE_VST3_SAMPLING.md) and [SoundCheck projects](SOUNDCHECK_PROJECTS.md).
- [ ] Finish the historical coverage-claim audit and verify release setup/troubleshooting instructions against the final clean-machine artifacts. Current development documentation is published; this does not establish another user's installation/workflow acceptance.
- [x] Record tested development source revisions, artifact hashes, host/device profiles, commands and limitations in the dated validation records. [Current SoundCheck project record](condensed/validation/milestone-4-soundcheck-project-2026-10-14.json) and [standalone device record](condensed/validation/standalone-audio-devices-2026-10-12.json). These identify the tested snapshots rather than implicitly qualifying later working-tree changes.
- [ ] Freeze and record the final release revision/artifact hashes, supported host/device matrix and outstanding limitations before tagging. Development-stage records above are complete; no final release/tag is qualified by them.

Acceptance: another user can follow the published instructions to run both products and complete the load/play/edit/sample/save/restore workflow without development tools.

## Milestone 7 — Editable OS and boot-ROM toolchain

Added by user direction on 2026-10-14. Deliver a practical decompiler/compiler
workflow for **both the disk OS image and the IC15 boot ROM**, so firmware changes
can be maintained as code and rebuilt instead of hand-patching binary offsets.
This is a parallel firmware-development track; it does not reopen the scoped
sampler integration milestones or become a Milestone 6 release prerequisite.

The first editable source target is labelled MCS-96/80C196KB assembly with explicit
data declarations and layout metadata. Disassembly and decompilation must preserve
uncertainty: original high-level source, names and types cannot be assumed to be
recoverable. Structured pseudocode aids understanding; an eventual compilable
higher-level representation must prove its semantics before replacing assembly.
An assembler/image builder satisfies the initial rebuild gate; a pseudocode-only
viewer or an offset-patch generator does not satisfy source-level editing.

- [ ] Define separate versioned import/build manifests for the OS disk and boot ROM: input hashes, CPU variant, entry points, reset/vector locations, bank/load-address mappings, code/data regions, image layout and derived fields. Preserve unknown regions explicitly; keep original user-supplied inputs immutable.
- [ ] Implement bank-aware recursive disassembly and analysis for both targets, with instruction boundaries, labels, cross-references, vector/call/jump targets and code/data annotations. Resolve overlay and fetch/data address mappings from evidence; report unresolved indirect targets and ambiguous regions rather than silently treating every byte as code.
- [ ] Produce editable source projects for both targets: assembly, labelled data/resources, symbols and layout/link metadata. Retain unknown bytes in explicit data sections. Permit incremental annotation without changing a no-op build; separate generated source from maintained edits.
- [ ] Deliver and test the matching assembler/compiler and linker/layout stage for the actual instruction subset and addressing modes used by both inputs. Diagnose unsupported encodings, branch-range errors, overlaps and unresolved symbols; never substitute guessed opcode encodings. Initially preserve fixed-address boundaries and reserved space; qualify relocation separately before moving firmware routines or tables.
- [ ] Build the OS image from source while preserving its disk/container structure, boot/loading records, bank placement, padding and any verified checksums/length fields. Build the IC15 ROM from source while preserving its reset/vector placement, mapped layout, size and any verified integrity fields. Derive these rules from the actual inputs; do not assume a shared OS/ROM container format.
- [ ] Establish independent **byte-exact no-change round trips for both targets**: import the hash-identified original, generate source, rebuild, then compare every byte and report changed ranges. Include deterministic repeated builds and negative tests for malformed manifests, invalid instructions and layout violations. Opaque byte preservation alone does not qualify meaningful code regions as disassembled or editable.
- [ ] Demonstrate one named source-level behavior change in each target, with a reviewable source diff and reproducible build. Start with bounded, reversible changes and explain all resulting binary differences. For each modified target, verify original-firmware boot/load, displays, controls and sample playback/release in native MAME; preserve the unchanged counterpart's identity. OS-only success does not qualify the boot-ROM toolchain or vice versa.
- [ ] Add a structured decompiler view for identified routines: control-flow graphs, readable expressions and evidence-backed variable/type annotations, linked back to assembly and bytes. If adding a higher-level compiler, define the supported language/ABI and test generated code against instruction-level behavior and native firmware workflows. Keep non-compilable pseudocode clearly labelled.
- [ ] Document one-command import/build/compare/test workflows for both targets, tool versions, fixture/artifact identities and remaining unsupported code/relocation cases. Keep user-supplied firmware and generated proprietary source/resources outside public source distributions; ship project-owned tooling, manifests that do not embed firmware, and validation procedures.

Acceptance: from locally supplied OS and boot-ROM inputs, a developer can generate
editable code, reproduce each original byte-for-byte, make a named code change in
each source project and rebuild independently bootable artifacts with recorded
native acceptance. No manual hex edits are needed for the demonstrated changes.
Physical-hardware validation is required before claiming modified firmware works
on a real S-760; native MAME acceptance alone does not establish that claim.

## Evidence required for review

| Concern | Completion evidence | Gate |
| --- | --- | --- |
| CPU/peripherals | Native supported-workflow regressions; isolated tests for fixes. Exhaustive specification/cycle audits are follow-on research | 5 |
| Concurrent activity | Deterministic firmware disk/MIDI/voice stress, correct loaded bytes, documented MIDI restrictions and no hangs/stuck notes; exact arbitration is follow-on | 5 |
| Audio DSP | Combined-path native functional tests for supported modes; physical claims limited to held-out measured domains; exact dynamic resonance is follow-on | 5 |
| Live integration | Actual native machine driving React frames and host audio/MIDI/state together | 1–4 |
| Testing | Label each result as model/unit, native runtime, physical hardware comparison or packaged-product validation | 6 |
| Documentation | Current status precedes dated history; superseded experiments never serve as current acceptance evidence | 6 |
| Firmware toolchain | Separate OS/IC15 source projects, byte-exact round trips, deterministic builds and one native-tested source change per target; higher-level decompilation claims scoped explicitly | 7 |

The latest distribution checkpoint has 241 Python passes; the recorded React/browser checkpoints are separate evidence, not an equivalent number of hardware-parity tests. Native agreement with an independent mathematical reference verifies implementation of that model; only hardware comparisons assess the measured hardware behavior. Neither establishes complete product readiness.
## Working order and evidence

Prioritize the standalone while preserving the runtime boundary for VST3. The initial boot/load/play and live-screen path is working; the next implementation order is:

**Milestones 1–5 are closed for their qualified Windows development profiles,
with SoundCheck as the accepted Milestone4 DAW/host matrix.** Native
processing, configuration, bounded state, standalone recovery, device selection
and supported 44.1 kHz physical sampling have evidence. Keep the documented
software/transport latency, same-build state and finite device-test limits explicit.

1. Preserve the qualified SoundCheck project contract and track remaining reliability defects and preserve the BUG-060 functional-QA processing contract. Other DAW containers, stock-GUI project integration, cross-build/cross-rate migration and a changed negotiated maximum remain unsupported extensions; they are not inferred from the scoped Milestone4 closure.
2. Preserve the completed Milestone5 development-profile acceptance matrix: named firmware edits, floppy/SCSI media, polyphony, disk-mode mute/recovery and combined audio defaults. Recording stays opt-in at the qualified44.1kHz stereo profile; repeat the complete workflows against final shipped artifacts in Milestone6.
3. Run Milestone 6 sustained, changed-package and clean-machine release acceptance, including the complete standalone load/play/edit/sample/save/restore workflow and final VST3 artifacts.
4. Advance Milestone 7 as a parallel firmware-development track: establish editable assembly and exact rebuilds of both the OS image and IC15 ROM before introducing source-level behavior changes or higher-level compilation.

For each item, add a failing regression or acceptance test, implement the behavior, verify it against the native machine and refine it before marking completion. Keep blocking transport, UI and disk operations outside future realtime callbacks. Hardware work can proceed independently when it does not alter the runtime contract.

The standalone checkpoint is documented in local shared finding127. Reproduction entry points are [the native runtime regression](../scripts/verify_native_runtime.py), [the browser smoke test](../google-ui/e2e/native-runtime.spec.ts), [the player runbook](STANDALONE_PLAYER.md) and [the runtime contract](NATIVE_RUNTIME_PROTOCOL.md). Packaged and audio evidence are distinct checks; neither yet covers the full release workflow.

Keep live coordination and evidence requests in the local shared findings folder; keep scratch in the assigned private work folder. Publish durable conclusions in `docs/condensed` and link release-relevant evidence here. The native checkpoint is commit-ready development work; it is not a completed standalone/VST release.
