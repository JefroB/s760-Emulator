# S-760 completion roadmap

Updated 2026-10-10. This is the active roadmap for delivering a standalone sampler and VST3 instrument with the React interface displaying authentic MAME CRT/LCD output. Update checkboxes only with recorded evidence; compilation and mock tests do not establish a working product.

## Definition of complete

A packaged Windows application and VST3 plugin boot the original firmware, load and edit sample programs, respond to MIDI and panel/mouse input, produce audio, sample external input, save media and restore sessions. React supplies the chassis and controls; MAME supplies the actual CRT/LCD pixels. Both products use the same tested engine. A release must document supported hardware behavior and remaining fidelity limits.

VST2, CLAP and other platforms are follow-on compatibility targets unless explicitly promoted into release scope. New OS features, including granular playback, are separate from completing the original sampler.

## Current checkpoint

- [x] Native MAME boots original IC15 ROM/system disk to the colour Perform Play screen; mouse and MIDI paths work in the tested native configuration.
- [x] Native sample floppy loading, measured playback/envelope/loop work and save-state checks have recorded evidence.
- [x] Full 88-note playback fixture validated. Measured interpolation agrees within 1% normalized RMS for the documented signals and settings.
- [x] Native build, core/plugin build and local regression checkpoint passed: 152 Python tests, plus core/plugin executables.
- [ ] Live native MAME engine integrated into the React/plugin host.
- [ ] Packaged standalone and VST3 verified end to end.

See the [native runbook](condensed/11-native-boot-and-audio-runbook.md), [audio scope](condensed/06-audio-dsp-and-hardware-parity.md) and [measurement summary](condensed/validation/audio-pitch-2026-10-10.json). Sub-1% agreement is a practical acceptance threshold within the stated measurement domain, not proof of all ASIC behavior. The analog recording chain contributes uncertainty.

## Milestone 1 — One live engine

- [ ] Select and document the runtime boundary: embedded engine or isolated runtime with bounded transport. Prove lifecycle, licensing/build compatibility and independent instances before committing to the architecture.
- [ ] Replace `core/src/s760_mame_host.cpp` scaffolding with the current native machine, including original boot ROM, memory banking and devices.
- [ ] Expose explicit boot/running/error state, stepping, audio, CRT/LCD frames, controls, MIDI, media and snapshots through one interface.
- [ ] Route plugin display, MIDI, audio, recording and state through that same instance; remove the separate-host behavior in `s760_vst3_plugin.cpp`.
- [ ] Make missing firmware and failed initialization visible; no successful-running status from an image-only initialization.

Acceptance: an automated harness boots, loads a known disk, sends MIDI, receives nonblank authentic frames and nonzero expected audio, then shuts down and repeats without leaked state. Compare against the native executable.

## Milestone 2 — Live React displays and controls

Depends on milestone 1.

- [ ] Deliver native CRT and LCD frames to the existing React canvas consumers, with correct geometry, palette and scaling.
- [ ] Connect mouse movement/buttons, panel buttons, dial, keyboard and disk actions to the live machine; preserve Mouse+CRT defaults for new profiles.
- [ ] Implement the actual WebView2 environment/controller, lifetime, resize and message/frame transport. The current gated implementation is also an outline, not a working host.
- [ ] Implement matching embedded transport in the React bridge client, which currently uses WebSocket.
- [ ] Replace demonstration disk metadata/actions with real media selection and backend results; connection indicators must reflect machine readiness.
- [ ] Ensure closing/reopening the UI leaves audio and the emulated machine running correctly.

Acceptance: from React, observe firmware boot, insert/load a sample disk, navigate and edit via real controls, then play MIDI and hear audio. Screens must agree with native MAME, including cursor and highlight behavior.

## Milestone 3 — Packaged standalone

Depends on milestones 1–2.

- [ ] Add the standalone executable and audio/MIDI device host, including device configuration, sample-rate conversion, buffering and reported latency.
- [ ] Package built React assets locally; launch without Vite, a terminal or a manually started bridge service.
- [ ] Provide firmware/media location setup, persistent settings, clean shutdown and actionable error messages.
- [ ] Support safe disk insertion/ejection and writeback, missing media and read-only files.
- [ ] Verify external audio input reaches the firmware sampling workflow and saved samples reload correctly.

Acceptance: install on a clean Windows environment with user-supplied firmware, boot, load, play, sample, save, quit and reopen successfully. Record device settings and dropout/latency results.

## Milestone 4 — Production VST3 host behavior

Depends on milestone 1; editor delivery also requires milestone 2.

- [ ] Connect processing and state to the unified engine rather than the old core host.
- [ ] Honor MIDI event sample offsets, note-off, sustain, pitch bend and other supported controllers; verify channel handling and panic/reset behavior.
- [ ] Support negotiated sample rates and varying block sizes with bounded audio buffers. Keep UI, disk access and avoidable allocations/blocking off the realtime callback.
- [ ] Validate instrument output and external sampling input, latency/tail reporting, suspend/resume and offline rendering.
- [ ] Implement versioned project state covering machine/sample state, settings and media references, with relocation and missing-media recovery.
- [ ] Verify two independent instances, editor resize/reopen, plugin removal and host shutdown.

Acceptance: scan and load in a real DAW; play and record MIDI, sample input, save/reopen a project, run multiple instances and compare offline bounce with realtime playback. Record host/version, rates and block sizes. No cross-instance media or machine state.

## Milestone 5 — Hardware coverage and supported defaults

Can proceed alongside integration; required for the completion claim.

- [ ] Audit actual firmware workflows for perform/patch/partial/sample editing, voice allocation/polyphony, MIDI and output routing.
- [ ] Validate interpolation beyond the current 44.1kHz forward-loop quarter-to-double-speed domain: other clocks, one-shots, reverse/alternate loops and pitch transitions.
- [ ] Validate combined envelope, filter, stereo and interpolation behavior; resolve unsupported resonant/moving filter cases with evidence.
- [ ] Audit floppy/SCSI load/save and sample editing/sampling through the native machine. Parser or host-manager tests alone do not demonstrate firmware peripheral behavior.
- [ ] Promote supported diagnostic monitor paths to normal configuration only after the combined path passes; document explicit unsupported cases.
- [ ] Record acceptance metrics per domain and distinguish model error from measurement-chain uncertainty. Request hardware captures only for specific unresolved behavior.

Acceptance: maintain a firmware-workflow and audio-domain matrix with reproducible tests. Every advertised feature has native-runtime evidence; remaining exclusions are explicit rather than silently approximated.

## Milestone 6 — Release qualification

Depends on milestones 3–5.

- [ ] Add end-to-end standalone and real-plugin smoke tests alongside existing unit/seam/property tests.
- [ ] Run sustained playback, repeated boot/load/save, malformed/missing media and recovery checks.
- [ ] Package reproducible release artifacts and runtime dependencies; exclude proprietary firmware, raw recordings and private research.
- [ ] Reconcile historical README coverage claims with actual product evidence and publish setup, troubleshooting and supported-feature documentation.
- [ ] Record the tested source revision, artifact hashes, host/device matrix and known limitations before tagging a release.

Acceptance: another user can follow the published instructions to run both products and complete the load/play/edit/sample/save/restore workflow without development tools.

## Working order and evidence

Start with milestone 1, then demonstrate the milestone 2 live-screen/audio workflow before expanding packaging or plugin formats. Share engine/runtime fixes between standalone and VST3. Hardware work can proceed independently when it does not alter the runtime contract.

Keep live coordination and evidence requests in the local shared findings folder; keep scratch in the assigned private work folder. Publish durable conclusions in `docs/condensed` and link release-relevant evidence here. The native checkpoint is commit-ready development work; it is not a completed standalone/VST release.
