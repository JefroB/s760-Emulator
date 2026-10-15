# Hardware Deployment & Development Roadmap

Current product status (2026-10-14): Milestones1–5 are complete within their documented Windows development profiles; final shipped-artifact/clean-machine qualification remains Milestone6. [Current roadmap](../COMPLETION_ROADMAP.md). Dated reconciliation below predates the subsequent native editing/SCSI/concurrency results.

Milestones5/6 evidence reconciliation (2026-10-14): the roadmap now exposes
completed native controller/stereo-routing and720KB floppy/sampling workflows,
plus development standalone sampling/session restore, SoundCheck acceptance,
bounded playback/startup/media recovery, the dated standalone distribution
review, current setup/contracts and recorded development identities. Compound
objectives retain unchecked entries for the remaining work. This is a review of
existing dated evidence, with no new execution or hardware measurements. CPU/IC4
audits, full editing/SCSI workflows, physical DSP/ADC fidelity, longer release
stress, final artifacts and clean-machine acceptance remain open. Neither
Milestone5 nor Milestone6 is closed. See the
[updated objectives](../COMPLETION_ROADMAP.md#milestone-5--hardware-coverage-and-supported-defaults).

Condensed from HIL deployment, LLE fidelity assessment, and next-generation OS
proposal, reconciled with current source and hardware specifications.

Current closure (2026-10-14): Milestones1–4 are qualified for their documented
Windows development profiles. By user direction, the Milestone4 DAW matrix is
SoundCheck1.0.0 with the private SDK adapter/project-document runner. Cold reopen,
project-local configuration and relative fixture references preserve221184 exact
L/R-average frames; variable callback sizes also match. Changed builds, host
rates or negotiated maxima reject explicitly; migration and stock-GUI/other-DAW
containers remain unsupported. Dated statements below about the remaining
project gate are superseded for this scope. BUG-060 remains an open intermittent
controller-QA reliability defect. See the [project contract](../SOUNDCHECK_PROJECTS.md)
and [validation](validation/milestone-4-soundcheck-project-2026-10-14.json).

Milestone 1 is complete for the Windows native-engine integration profile.
The final compound objective was split: native-only selection and bounded
project state have acceptance evidence; graphical configuration/editor delivery,
native sampling and actual DAW qualification remain open in Milestones 2–4.
The fresh module test passes 480000 exact stereo frames at48kHz with no missed
deadlines, and current identities match the accepted SCSI/host-state record.
See the [closure review](../MILESTONE_1_COMPLETION.md) and
[closure evidence](validation/milestone-1-completion-2026-10-11.json).

## Physical deployment

The native VST3 output-rendering profile now supports unpaced offline processing
through its worker, with bounded waits and packet backpressure. SoundCheck's
offline bounce exactly matches realtime playback with held-note suspend/resume;
independent native reference replay passes at44.1/48/96kHz. Actual SDK latency
reports and potentially infinite voice-tail reporting are qualified. This closes
the scoped Milestone4 output-rendering gate; host sampling input, graphical
plugin configuration, broader controller semantics and DAW project portability
remain separately scoped. See the [rendering contract](../NATIVE_VST3_RENDERING.md).

Graphical native VST3 configuration now shares the firmware/media form and shows
startup errors in a silent native recovery instance. SoundCheck verifies invalid
change preservation, UTF-8 media paths, editor reopen, corrected host reload and
loaded playback/release. Saving settings does not replace a processing machine;
the host must reload to apply. Installed editor assets are required for recovery.
This closes the scoped Milestone4 configuration gate; full MIDI semantics, host
sampling input and DAW project portability remain open. See the
[configuration contract](../NATIVE_VST3_CONFIGURATION.md).

The Windows native boundary passes crash cleanup/reopen, saved-session recovery
and host-clocked module audio acceptance. The exact Windows standalone package
now has a [distribution qualification](../DISTRIBUTION_QUALIFICATION.md): actual
frozen dependencies and vendor DLLs are attributed, notices retained, copied
Windows runtime DLLs excluded, and the delivered MAME source snapshot rebuilt
cleanly. That rebuilt engine passes native boot/audio and packaged desktop
readback. Original project-owned code remains BSD-3-Clause; MAME retains GPL
and its individual component terms. No Roland firmware or sample media ships.

The release gate recomputes the complete package tree against a reviewed
manifest; changed artifacts require a new review. This completes the separated
Milestone 1 standalone distribution objective, not clean-machine installation,
finished sampler workflows or actual VST3/DAW/editor qualification. See the
[distribution evidence](validation/distribution-2026-10-11.json) and
[remaining roadmap](../COMPLETION_ROADMAP.md).

The project has a proven raw-IMG → Gotek → physical S-760 boot loop. Use copies
of `S760224.IMG`, keep total size `0x168000`, verify patch bytes/diffs, and retain
a known-good image. Generated media and recordings belong in the author's work
folder until finalized. Never overwrite the original disk or infer target media
letters from an old example.

The HIL source records a FlashFloppy setup using Shugart/native navigation and
raw 80×2×18×512 geometry. Its FF.CFG snippet is a historical setup record,
not a verified universal FlashFloppy configuration. Inspect the actual working
device configuration and current firmware documentation before changing it.

SCSI workflows use a Roland-format volume image and an appropriate target ID.
Naming such as `HD00_512.hda` is adapter-specific. Confirm adapter naming, sector
size, termination, and host/target IDs against the actual device. A sector-image
builder's success does not itself prove real hardware filesystem compatibility.

The old deployment example for `build_dump_chunk.py` is inconsistent with the
recorded builder interface. Inspect the actual script CLI before executing it;
do not reuse the obsolete payload/--off example. See document 05 for proven
patch milestones and document 06 for audio capture isolation.

## Current implementation versus fidelity

MAME has a local S-760 driver, resident disk preload/HLE, peripheral handlers,
CRT/LCD models, and its own sound device. The opt-in **banked native path now
cold-loads the real IC15 v1.11 ROM, boots OS v2.24 to colour Perform Play,
scans the panel, loads samples, and produces diagnostic audio** (documents 02–07)
— so the earlier blanket "native IC15 boot remains unfinished" is superseded for
the opt-in path. What is still NOT finished: full physical bus semantics
(IC4/DMA arbitration, exact interrupt vectoring), hardware-exact DSP (filter
moving/BP-HP precision, DI, MEQ gain), and a single shipped product (the live
runtime integration is "Milestone 1", in progress — see above). "Step 1 100%
complete," "cycle accurate," and "bit accurate across all frontends" remain
unsupported and are not claimed; numerical replay is implementation agreement,
not hardware equivalence.

Architecture correction (2026-10-14, BUG-008): the native standalone and VST3 share the modified MAME machine implementation through isolated runtime processes. MAME owns the product renderer; the VST3 worker transports PCM/MIDI and host-rate conversion. `S760HardwareCore` is a separate, deliberately unlinked reference model, not a missing product dependency. The former shared-reference-DSP completion claim is withdrawn; see the current architecture in document06.

## Native runtime integration (findings 100, 125–135) — "Milestone 1", in progress

A live-engine integration effort is building one product around the native MAME
instance. Confirmed, but all explicitly **opt-in / dev-checkpoint, not a finished
release**:

- **Save/load state (finding100):** handler-backed banked RAM, bank regs, wave
  memory and wave regs were unregistered with MAME's save manager (caused an
  `Unhandled 1e` load crash); now registered. An active BP-sweep save→load is
  byte-exact (57,330 PCM16 samples, corr 1). No machine-wide save flag yet;
  display/media/other-peripheral/fresh-process restore are separate work.
- **Native floppy Save/export/reload (findings128/129):** the OS Save path is
  decoded (bank005A:6C41 programs C00E/C00C, count 0x1200, control **E2** copies
  wave RAM → floppy). A fresh machine reloads the export; all 13 sample payloads
  (119,808 bytes for the 88-key patch) match exactly. The controller tracks
  media generation/write-revision and **rejects dirty/busy insert or eject**
  until an atomic no-clobber export. LIMITS: whole-wave-RAM compare still differs
  by 347 name/high-mem bytes (sample bytes unchanged); no library writeback,
  SCSI-save; "dirty" = controller writes, not
  firmware Save completion.
  Findings163/164 extend this with acknowledged floppy protection, protected
  firmware Save, and OS2.24 standard720KB Format/Save/export/reload qualification.
  HD/foreign formatting and physical FDC timing remain unqualified. See
  [format evidence](validation/standalone-formatting-2026-10-12.json).
- **Standalone dev player (finding127, supersedes finding125's "no working host"):**
  a desktop player boots an isolated native MAME process, shows the real CRT/LCD
  in React, accepts mouse/panel, inserts a private floppy copy, and plays MIDI
  through the serial receiver (note60 peak 1459 PCM16, zero release tail). Two
  independent runtime processes work; duplicate state dir rejected.
  Finding165 adds separate60-host-second and normal-close recovery for this
  standalone floppy profile. Dirty media and sampler RAM survive the last
  successful recovery; manual saves stay separate. Restart/startup preserve an
  existing recovery until explicit restore/replacement. Save failure cancels
  desktop close, with confirmed quit-without-recovery available. Native exact
  replay and packaged timer/restore/close pass. Later edits, physical-MIDI/busy
  delays and power-loss guarantees remain limits. [Evidence](validation/standalone-auto-recovery-2026-10-12.json).
- **Native C++ runtime + VST3 (findings130–133):** the shared runtime exposes
  pause/resume/step, demand-driven PCM render (1–8192 frames, exact block sizes,
  ≤0.9999 PCM16 vs MAME WAV), a direct Windows C++ client (no Python/React,
  authenticated loopback + kill-on-close job), emulated-time MIDI scheduling
  (absolute 44.1 kHz timestamps via MAME coroutine timers + the 31250-baud
  transmitter, <0.001-sample error), and the real MAME instance driven **through
  the VST3 processor** with a ~12,288-sample (~279 ms, conservative) delay budget
  and alloc-free callbacks. LIMITS: a "class-level processor harness", not a DAW
  plugin-scan/load; not calibrated low-latency/sample-exact onset; 44.1 kHz
  float stereo + note on/off only; native sampling rejects; suspended bounded native plugin state now works.
- **Cold checkpoints (findings134/135):** state registration was extended to the
  handler-backed VDP/LCD+VRAM, EEPROM, gate/IRQ, floppy-controller and MIDI
  transmit ring; **Version2** checkpoints also preserve future scheduled MIDI
  events (and cancel stale ones on reload). Active-note and serial-boundary cold
  restores are byte-exact (65,536–131,072 frames). LIMITS: paused isolated-runtime
  checkpoints, NOT complete project recall; VST3 getState/setState still reject;
  Version1 archives deliberately rejected; all six Milestone-1 gates remain open.

Validation JSON for these lives under `docs/condensed/validation/` (e.g.
`native-cpp-runtime-2026-10-11.json`, `native-plugin-stream-2026-10-11.json`,
`native-checkpoint-2026-10-11.json`); design notes in `docs/NATIVE_CPP_RUNTIME.md`
and `docs/NATIVE_CHECKPOINTS.md`.

## Ordered development work

1. Establish the natural D010 enable path (task 26), then verify authentic
   text/UI output and matching controller state.
2. Decode real IC15 mapping/handoff and service contracts; remove synthetic
   record validity and correct disk bounds/error behavior with evidence.
3. Validate display layout, font transfer, timing/status and input paths against
   firmware traces and hardware captures.
4. Characterize DI interpolation, TVF/MEQ and analog stages with measurements;
   integrate a common DSP engine only when its ownership/build path is explicit.
5. Maintain honest layer-specific tests and coverage while implementing features.

The old dated Gantt charts were planning estimates, not measured schedules or
commitments. They are omitted from the current reference.

## Future OS ideas (proposals, not implemented firmware)

| Candidate | Concrete dependency / constraint |
| --- | --- |
| Non-destructive slicing | Proven sample-address/object allocation and key mapping |
| WAV/AIFF/FAT import | Actual filesystem/parser/memory-transfer implementation; an SD-backed SCSI target does not expose host folders automatically |
| Unison/voice stacking | Correct allocator and **24-voice hardware** budget |
| CC/NRPN routing, arp, Scala tuning | Proven MIDI/timer/pitch contracts and bounded CPU load |
| Extended envelopes/step modulation | Verified update cadence and DSP control interface |
| Moving loops/granular scrub | Safe live pointer changes and measured voice behavior |
| Themes and analysis displays | Verified video/palette protocol; FFT performance measurements |

The 16 MHz MCS-96 is a control CPU with dedicated sound ASICs. “100% feasible,”
real-time FFT, arbitrary new synthesis, and MIDI 2.0 compatibility are not
established by the proposal. Evaluate CPU cycles, memory, I/O, format changes,
and backward compatibility separately for emulator extensions and physical OS
patches. Modern software features need not be assumed executable on vintage
hardware.

Native plugin state now archives machine state, pending host MIDI/PCM, timing
and FIR converter history together. Cold and repeated replay matches exactly at
44.1/48/96 kHz; invalid native apply blocks processing until valid reload. This
now includes the bounded SCSI snapshot profile: device metadata, partial
commands/transfers and startup-sized media buffers. External SCSI files are
limited to 64 MiB total and pinned to startup identities. Native cold audio and
refreshed displays match; all-rate plugin replay passes. SCSI writeback remains
broken (BUG-015), and actual DAW compatibility remains unqualified.
See the [state contract](../NATIVE_PLUGIN_STATE.md) and
[validation](validation/native-plugin-state-2026-10-11.json).


## Native sampling postprocessing checkpoint (2026-10-12)

BUG-043 is fixed for the observed OS2.24 synchronous IC4 A7 wave-to-RAM
transfer. Start now exhausts the count and reaches waveform review; the preserved
previous executable fails the same native regression. The inverse BC transfer
validates both full byte ranges and even count, copies, advances addresses and
clears count. Read-only diagnostic taps preserve exact131072-frame native PCM
and both displays; independent load/play/release and307 backend tests pass.
ADC capture remains open: input meter0x10001C and recording-position0x100010/12
return unmapped values. Arming observes slots4/20 with mode8, which is a constraint
rather than a qualified input model. No captured signal, recorded PCM integrity,
physical timing, packaged acceptance or full sampling workflow is claimed.
See [sampling contract](../NATIVE_SAMPLING.md) and
[validation](validation/native-sampling-dma-2026-10-12.json).


The standalone native entry point now has a Configuration screen for live MIDI
selection and existing output/backend/buffer settings, with firmware/media
configuration below. Its 61-key keyboard is hidden by default and persists its
visibility per instance; note holds release on blur/hide/teardown.312 backend,
117 React, packaged native browser preference/audio-restart and actual WebView
boot checks pass. The VST editor remains host-driven. Subsequent physical sampling
qualification below leaves two Milestone3 objectives: device qualification and
production ADC semantics/rates. See [standalone configuration](../STANDALONE_PLAYER.md) and
[validation](validation/standalone-configuration-2026-10-12.json).


Standalone Input Level is now qualified for the experimental native44.1kHz
recording profile: unity/half/mute PCM after cold session recall, independent of
Output Level, survives firmware Sample Save/fresh Load exactly.322 backend,
119 React, source/packaged browser gain/restore/reconnect and actual WebView boot
checks pass. The gain objective is complete; physical capture-device selection,
negotiated capture and realtime external sampling remain open. See
[qualification](validation/native-input-level-2026-10-12.json).

Physical external sampling is now complete for the supported MOTU Windows MME
44.1 kHz stereo profile: outputs 3/4 to inputs 1/2, exact captured PCM through
original firmware Sampling, zero native underruns and exact Sample Save/fresh
Load. Recording selection, restart/readback and reconnect pass in source and
packaged browsers;329 backend/120 React tests pass. Two Milestone3 objectives
remain: broader playback/MIDI device qualification and production ADC
semantics/rate/driver qualification. [Physical sampling evidence](validation/native-physical-sampling-2026-10-12.json).
## Standalone ASIO delivery

ASIO is now a selectable standalone backend, with persistent driver, stereo
input/output pairs and buffer controls. MOTU128/512/1024-frame duplex, native
patch playback/release and physical-input firmware Sampling/Save/fresh Load
pass.341 backend/121 React tests, native core/plugin/ASIO queues, source and
packaged browser configuration and actual desktop boot/close pass. The two
broader Milestone3 qualification gates remain open; measured physical latency,
indefinite clock drift, other rates/drivers and hotplug are not inferred from
this supported profile. [Evidence](validation/standalone-asio-2026-10-12.json).

The standalone device objective is now complete for the documented finite
profiles: selected Windows48kHz output conversion from native44.1kHz PCM,
packaged settings persistence, actual MOTU software reopen after a closed-stream
error, five-minute/150-note playback without reported output losses, and measured
physical bridge arrival upper bounds with explicit limits. Larger transport
buffering trades latency for scheduling headroom; its371.52ms target is visible
separately from driver latency.354 backend/123 React tests and native queue tests
pass. Production ADC alternate clocks, driver-level loss coverage and hardware
register/meter semantics moved to Milestone5 by user direction on2026-10-13.
Milestone3 is complete for the qualified Windows development profile;
clean-machine/final-artifact acceptance remains Milestone6. Physical
unplug/replug tests were removed by user direction.
[Device evidence](validation/standalone-audio-devices-2026-10-12.json).

Milestone4 SDK/discovery/bus/scan-load acceptance is complete for SoundCheck1.0.0
Windows x64 native QA hosting. The current concrete WebView2 module passes an
independent Steinberg-header ABI probe, including stereo output,16-channel MIDI
input and rejection of nonexistent buses; native ADC input remains hidden.
SoundCheck loads the current instrument. Its response leaves extended version
and subcategory fields empty. The extended playback rerun was stopped at an
obsolete disk-name UI selector, so earlier loaded-sample qualification is retained
without claiming a new playback pass. Other DAWs, lifecycle isolation, project
portability, full MIDI control, variable rates/blocks and host input remain open.
[SDK/host evidence](validation/milestone-4-sdk-host-2026-10-12.json).

Milestone4 processing and lifecycle qualification now passes for the documented
Windows x64 native QA profile. At44.1/48/96kHz,12-second paced processor runs
with64/127/256/511/1024-frame callbacks reproduce independent native checkpoint
renders exactly, with silent release and zero missed callback deadlines. Callback
queues are bounded; unsupported rates, block limits and float64 buffers reject.
Started streams reject rate changes rather than discarding queued state.
SoundCheck1.0.0 at44.1kHz/512 frames loads ROBOFULL through original firmware,
plays the expected20,004Hz fixture, preserves held audio through editor reopen,
and verifies separate media/gain for two instances and survivor behavior after
removal. Actual SDK editor attachment verifies size readback at1200x900,
1600x1200 and1440x1100. Removal followed by host exit leaves no native children.
The earlier stale-selector playback limitation is superseded by this passing run.
Sustain/bend/controllers/panic, host sampling input/offline acceptance, graphical
setup and project portability remain open. Other DAWs, indefinite soak, hardware
parity and shutdown with active instances/crash recovery are not inferred.
[Processing/lifecycle evidence](validation/milestone-4-processing-lifecycle-2026-10-12.json).

Native VST3 controller transport now implements actual SDK MIDI mapping and
bounded parameter queues for16-channel CC0–127 and14-bit bend. A12-second paced
varying-block render matches independently scheduled native MIDI exactly,
including effective channel15 CC123 while channel0 plays. SoundCheck automation
measures CC7 scaling, CC64 held/released notes and CC123 silence on original
OS2.24/ROBOFULL.354 backend tests, C++ core/plugin and actual SDK queue/metadata/
overflow checks pass. The private SoundCheck QA adapter was repaired to forward
stored automation through real SDK queues; its independent checkout is unchanged.
Configured audible bend now passes with firmware Bend Up/Down set to12:
centre20004Hz, folded upward4108Hz, downward10002Hz, restored centre20004Hz
and silent release. The supported original-firmware controller gate is now qualified below.
Raw CC120/121 are unsupported; explicit supported-message macros provide panic
and neutral-controller reset. CC123 retains held-pedal audio until CC64 up. Firmware
bytes are unchanged. See the [controller contract](../NATIVE_VST3_MIDI.md),
[text/audio report](validation/milestone-4-midi-automation-2026-10-12.txt) and
[source/binary evidence](validation/milestone-4-midi-2026-10-12.json).


SoundCheck1.0.0 native QA project-file save/cold reopen now passes at44.1kHz/512
frames. The same module recalls embedded floppy state with original library and
private runtime paths absent, using relocated matching firmware and persisted
local product settings. The full-rate host L/R-average waveform matches221184
frames exactly, including a silent release tail; corrupted-file rejection
preserves another exact replay. This is same-build native QA component-state
file acceptance; actual DAW project containers, per-project firmware overrides,
other hosts and cross-build/rate/block migration remain open. No proprietary
state/media is committed. [State contract](../NATIVE_PLUGIN_STATE.md) and
[project evidence](validation/milestone-4-project-portability-2026-10-13.json).


The remaining Milestone4 controller objective is complete for the Windows native
QA profile. BUG-056 enabled the existing stereo mixer in the C++ native launcher;
CC10 now produces left-only/right-only/equal-centre output on fresh notes.
Configured CC11 expression and assigned CC1 modulation control TVA gain; ordered
RPN0 sets a measured two-semitone bend range and null selection prevents further
Data Entry changes. CC123–127 release with pedal up.32-message all-channel
panic and64-message neutral-controller reset macros release sustain-held audio
and permit fresh notes. Original-firmware CC120/121 remain explicitly unsupported,
consistent with the1993 MIDI implementation and observed native behavior.

The55-case SoundCheck1.0.0 matrix passes at44.1kHz/512 frames. Three-rate paced
native runs match independent reference PCM with zero missed callback deadlines;
fresh48kHz state recall reproduces240000 stereo frames. Core/plugin tests,
354 backend regressions and the default native verifier pass. This qualifies the
software/controller profile, not hardware gain/LFO/filter/alias fidelity or other
DAWs. Existing same-build constraints reject older-module snapshots after rebuild.
Host ADC/input is qualified below; actual DAW project portability is the remaining
Milestone4 objective. [Controller contract](../NATIVE_VST3_MIDI.md) and
[complete evidence](validation/milestone-4-controller-semantics-2026-10-13.json).


## Native VST3 host sampling — 2026-10-13

Milestone 4 host input now passes the Windows SoundCheck 1.0.0 native instrument
profile. Its optional inactive stereo bus accepts float32 at 44.1 kHz. Callback
buffers are copied before output clearing, preserving aliased input/output and
channel silence flags. A bounded worker queue carries PCM alongside MIDI;
worker conversion feeds the existing native ADC peripheral in the same render
transaction, using validated 2,048-frame ingress chunks. Firmware performs the
recording; no guest/sample RAM writes or substitute recorder are used.

Original OS 2.24 records 45,649 exact host frames/channel with varying
64/127/256/511/1024-frame callbacks and shared input/output buffers. Native
recording underruns are zero. All 184,320 allocated sample bytes match recorded
wave RAM, firmware Sample Save/export and fresh native Sample Load. The source
floppy is unchanged. Actual SDK getState captures the machine for diagnostic
wave/FIFO inspection; this is separate from third-party DAW project containers.

A strict 12-second active-input clock produces 529,200 exact output frames with
36.9 µs maximum callback and zero missed deadlines. Output-only 48/96 kHz runs and
240,000-frame cold state also pass.354 backend tests and independent SDK metadata,
input-clock rejection, silence flags and disconnection checks pass. State v3
preserves pending input PCM; older formats remain decodable with zero input.

Live Sampler FX remains unadvertised. Other input clocks, physical ADC fidelity,
other DAWs and release qualification remain open. Actual DAW project portability
is the sole remaining Milestone 4 checkbox. See the
[host sampling contract](../NATIVE_VST3_SAMPLING.md) and
[exact source/binary validation](validation/milestone-4-host-sampling-2026-10-13.json).
