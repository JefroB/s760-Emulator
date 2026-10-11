# Hardware Deployment & Development Roadmap

Condensed from HIL deployment, LLE fidelity assessment, and next-generation OS
proposal, reconciled with current source and hardware specifications.

## Physical deployment

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
CRT/LCD models, and its own sound device. C++ provides disk/DSP/recorder/host/
plugin/bridge infrastructure; React provides the shell and test suites. The
native IC15 boot, full physical bus semantics, faithful firmware services, and
hardware DSP equivalence remain unfinished. “Step 1 100% complete,” “cycle
accurate,” and “bit accurate across all frontends” were unsupported roadmap
claims and are not retained as completed milestones.

In particular, `S760HardwareCore` exists but its implementation file is omitted
from the CMake library source list, and MAME defines a separate sound engine.
Completing a genuinely shared DSP implementation requires explicit integration
and compiled end-to-end verification, not just adding another reference model.

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
