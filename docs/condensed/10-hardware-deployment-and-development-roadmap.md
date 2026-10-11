# Hardware Deployment & Development Roadmap

Condensed from HIL deployment, LLE fidelity assessment, and next-generation OS
proposal, reconciled with current source and hardware specifications.

Milestone 1 is complete for the Windows native-engine integration profile.
The final compound objective was split: native-only selection and bounded
project state have acceptance evidence; graphical configuration/editor delivery,
native sampling and actual DAW qualification remain open in Milestones 2–4.
The fresh module test passes 480000 exact stereo frames at48kHz with no missed
deadlines, and current identities match the accepted SCSI/host-state record.
See the [closure review](../MILESTONE_1_COMPLETION.md) and
[closure evidence](validation/milestone-1-completion-2026-10-11.json).

## Physical deployment

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

In particular, `S760HardwareCore` exists but its implementation file is omitted
from the CMake library source list, and MAME defines a separate sound engine.
Completing a genuinely shared DSP implementation requires explicit integration
and compiled end-to-end verification, not just adding another reference model.

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
  formatting, write-protect/error, or SCSI-save; "dirty" = controller writes, not
  firmware Save completion.
- **Standalone dev player (finding127, supersedes finding125's "no working host"):**
  a desktop player boots an isolated native MAME process, shows the real CRT/LCD
  in React, accepts mouse/panel, inserts a private floppy copy, and plays MIDI
  through the serial receiver (note60 peak 1459 PCM16, zero release tail). Two
  independent runtime processes work; duplicate state dir rejected.
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
