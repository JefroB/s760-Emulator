# S-760 completion roadmap

**Milestone 1 complete (2026-10-11):** One native engine now serves standalone and exported-module displays, MIDI, audio and bounded same-build state. Lifecycle, recovery, timing and the exact Windows standalone distribution profile have acceptance evidence. The remaining mixed objective is split below: configuration/editor delivery belongs to Milestones 2/4, native sampling to 3/4, and real DAW acceptance to 4. These remain open. [Closure and evidence](MILESTONE_1_COMPLETION.md).

Updated 2026-10-12. This is the active roadmap for delivering a standalone sampler and VST3 instrument with the React interface displaying authentic MAME CRT/LCD output. Update checkboxes only with recorded evidence; compilation and mock tests do not establish a working product.

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
- [ ] Complete production native ADC/input qualification beyond the supported Windows MME 44.1 kHz stereo profile: alternate clocks, driver-level loss measurement and hardware register/meter semantics remain open. The experimental profile remains disabled unless an input device is explicitly selected.
- [x] Deliver standalone recording-device selection and bounded live transport for Windows MME 44100 Hz stereo PCM16; source and packaged browser apply/restart/reconnect, unsupported/missing/stalled-device errors, checkpoint discontinuities and physical firmware capture pass. Windows interface negotiation is qualified; physical converter clocks and conversion are not inferred. [Evidence](condensed/validation/native-physical-sampling-2026-10-12.json).
- [x] Offer ASIO in standalone Configuration with persistent driver, stereo input/output pairs and buffer selection. Native callback uses preallocated lock-free rings; actual MOTU128/512/1024-frame duplex tests, native ROBOFULL playback/release, exact ASIO firmware capture/Save/fresh Load, source/package browser settings and actual WebView boot/close pass.341 backend/121 React plus native core/plugin/ASIO queue tests pass. Driver-reported latency is shown separately from transport; broader clocks, hotplug and sustained physical latency/dropout qualification remain open. [Evidence](condensed/validation/standalone-asio-2026-10-12.json).
- [x] Enable and qualify the standalone rack Input Level with the native ADC path: independent0–100% recording gain, acknowledged UI readback and same-build session recall. Original firmware records exact unity/half-gain/muted L/R PCM after cold restore, with Output Level muted, zero input underruns and exact Sample Save/export/fresh Load.322 backend/119 React tests, source and packaged browser gain/reconnect/restore and actual WebView boot pass. Service Notes p20 places recording gain before conversion; physical pot taper/headroom remain uncalibrated. VST host input routing and physical capture devices remain separate. [Evidence](condensed/validation/native-input-level-2026-10-12.json).
- [x] Verify external audio input reaches firmware sampling and saved samples reload correctly for the supported 44.1 kHz stereo profile. MOTU ASIO outputs 3/4 physically looped to Windows MME inputs 1/2: original firmware records 65,514 frames/channel, exactly matching a contiguous captured device PCM interval; all 276,480 allocated sample bytes survive Save/export/fresh Load. Normal-speed capture reports zero native input underruns; 18,432 discarded frames across the full workflow are reported explicitly. Missing/unsupported/stalled inputs fail visibly. Production ADC semantics, alternate rates, physical driver loss accounting and measured latency remain separate. [Evidence](condensed/validation/native-physical-sampling-2026-10-12.json).
- [x] Implement bounded same-build standalone saved-session recall through the native engine; cold PCM/display replay and explicit recovery of the last save pass. [Contract](NATIVE_SESSIONS.md).
- [x] Complete standalone session handling for the supported same-build floppy profile: relocated firmware paths and absent source libraries/private insertion files recover from embedded media; version/build/firmware/integrity failures explain repair and reject before changing the live machine. Explicit confirmation states that edits after the last save are lost; no autosave is claimed. Native cold replay reproduces 131072 stereo frames and both displays, and real-browser recovery/mismatch workflows pass. External SCSI files still require matching names/content; changed-package and clean-machine release qualification remain separate. [Session contract](NATIVE_SESSIONS.md).

Acceptance: install on a clean Windows environment with user-supplied firmware, boot, load, play, sample, save, quit and reopen successfully. Record device settings and dropout/latency results.

## Milestone 4 — Production VST3 host behavior

Depends on milestone 1; editor delivery also requires milestone 2.

- [x] Connect exported-module processing and bounded suspended state to the unified native engine, with no fallback to the historical core. Completed in Milestone 1; real host/ABI acceptance remains below.
- [x] Deliver graphical plugin configuration and host-visible startup errors, including persistent firmware/media settings and recovery from invalid paths; use the shared Milestone 2 interface. SoundCheck verifies a silent missing-firmware instance, visible errors, rejected-change preservation, UTF-8 media paths, editor reopen and successful host reload. Applying settings requires reload; damaged installations without editor assets require repair. [Configuration contract/evidence](NATIVE_VST3_CONFIGURATION.md).
- [x] Qualify the actual VST3 SDK/ABI, discovery/metadata/bus descriptions and scan/load in a named real DAW or native QA host. Independent Steinberg-header probe and SoundCheck 1.0.0 Windows x64 native host pass on the current module; stereo output and 16-channel MIDI input are described, and unqualified ADC input stays hidden. Basic factory metadata is covered; extended version/subcategory reporting and other DAWs are not inferred. [Qualification](condensed/validation/milestone-4-sdk-host-2026-10-12.json).
- [x] Honor note-on/off sample offsets and release through the native processor at all three supported host rates. Paced varying-block renders match the independent native reference exactly; SoundCheck loaded-sample release is silent. [Processing evidence](condensed/validation/milestone-4-processing-lifecycle-2026-10-12.json).
- [x] Deliver bounded native VST3 MIDI controller transport: actual SDK mapping/parameter queues, CC0–127 and14-bit bend on16 channels, exact varying-block native reference replay, and SoundCheck automation with measured volume, sustain and CC123 release. Independent channel15 CC123 leaves channel0 playback intact. [Controller contract/evidence](NATIVE_VST3_MIDI.md).
- [ ] Complete configured audible pitch bend, other controller effects and panic/reset qualification. Bend/expression remain unchanged on ROBOFULL, CC120 does not silence it, and reset-sustain effect is not established. Transport delivery and demonstrated CC7/64/123 behavior are the completed subset above; do not infer all controller semantics from byte delivery.
- [x] Support negotiated sample rates and varying block sizes with bounded audio buffers. Native processor qualification passes at 44.1/48/96 kHz with 64/127/256/511/1024-frame callbacks, exact independent-reference PCM and no missed callback deadlines in each 12-second paced profile. Fixed queues keep rendering/runtime I/O off the callback; unsupported rate/block/sample-size configurations are rejected. A started stream rejects rate changes to preserve queued state. [Processing evidence](condensed/validation/milestone-4-processing-lifecycle-2026-10-12.json).
- [x] Qualify native instrument output buses, latency/tail reporting, suspend/resume and offline rendering in the Windows native QA host. SoundCheck realtime playback with held-note suspension and unpaced offline bounce match exactly; independent native renders agree at all three supported rates. SDK latency reporting and infinite-tail reporting pass. [Rendering contract and limits](NATIVE_VST3_RENDERING.md).
- [ ] Route host sampling input through the same native ADC path delivered in Milestone 3 and qualify actual host input buses and recording. Do not advertise the Live Sampler FX class until its native input path passes; the completed output-rendering subset above does not establish sampling-input acceptance.
- [x] Implement versioned bounded native/host project snapshots with integrity/identity checks and exact cold replay at all three supported rates. [State contract](NATIVE_PLUGIN_STATE.md).
- [ ] Complete host project portability: persist product settings and media references, handle relocation/missing media, and verify actual DAW save/reopen. Preserve explicit same-build/format limitations until migration is implemented.
- [x] Verify two independent instances, editor resize/reopen, plugin removal and host shutdown for the Windows x64 native QA profile. SoundCheck verifies separate gain/media, removal of one instance preserving the other and reopened settings; the independent Steinberg SDK host verifies attached editor resize/readback at three sizes. Loaded SoundCheck audio survives editor reopen. Explicit removal followed by host exit leaves no native children. Shutdown with active instances/crash recovery and other DAWs are not inferred. [Lifecycle evidence](condensed/validation/milestone-4-processing-lifecycle-2026-10-12.json).

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

**Milestones 1 and 2 are closed for their qualified development profiles. Next: Milestone 3
standalone product acceptance.** Native processing, selection, bounded state,
recovery and the reviewed distribution artifact have evidence. Keep the
approximately279ms software delay and same-build snapshot limits explicit.
Actual device/DAW/editor, sampling and full product-release gates remain open
in their assigned milestones; no requirement was dropped by the scope split.

1. Deliver native ADC/input transport, recording-device selection and the dependent physical firmware sampling workflow. Offline recording gain and Sample Save/reload are qualified. Standalone media now has empty-drive/Eject, dirty protection, protected Save,720KB formatting, Save/export/reload and bounded periodic/normal-close recovery. Physical device qualification and broader formatting profiles remain open; changes since the last successful recovery are still at risk.
2. Preserve the completed same-build floppy session recovery contract: relocated firmware and missing source libraries restore from embedded media, with actionable version/identity errors and explicit loss of edits since the last save. External SCSI files remain matching-content prerequisites; qualify these flows in release/clean-machine testing.
3. Add audio device/input configuration and prove the firmware sampling → save → reload workflow; qualify physical MIDI and latency.
4. Qualify physical capture and recording timing; standalone Input Level, recovery flows and packaged settings acceptance are qualified for their documented development profiles.
5. Run sustained and clean-machine standalone acceptance, then qualify the already connected C++ VST3 client against the actual SDK/host/editor. Use the available SoundCheck native host for automated acceptance; compatibility with other DAWs remains separately scoped.

For each item, add a failing regression or acceptance test, implement the behavior, verify it against the native machine and refine it before marking completion. Keep blocking transport, UI and disk operations outside future realtime callbacks. Hardware work can proceed independently when it does not alter the runtime contract.

The standalone checkpoint is documented in local shared finding127. Reproduction entry points are [the native runtime regression](../scripts/verify_native_runtime.py), [the browser smoke test](../google-ui/e2e/native-runtime.spec.ts), [the player runbook](STANDALONE_PLAYER.md) and [the runtime contract](NATIVE_RUNTIME_PROTOCOL.md). Packaged and audio evidence are distinct checks; neither yet covers the full release workflow.

Keep live coordination and evidence requests in the local shared findings folder; keep scratch in the assigned private work folder. Publish durable conclusions in `docs/condensed` and link release-relevant evidence here. The native checkpoint is commit-ready development work; it is not a completed standalone/VST release.
