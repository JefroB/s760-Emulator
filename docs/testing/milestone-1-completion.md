# Milestone 1 completion — one live engine

Closed 2026-10-11 for the documented Windows native-engine integration profile.
The standalone and exported VST3 module use the native MAME runtime for real
firmware execution, displays, MIDI, audio and supported state. The user requested
that the last mixed objective be separated into the appropriate later milestones
before closing this engine milestone.

## Scope split

| Former mixed requirement | Disposition | Acceptance still required |
| --- | --- | --- |
| Production engine selection | Complete in Milestone 1 | Exported factory is native-only; startup failure cannot fall back to the old core. |
| Project state through the same instance | Complete within the Milestone 1 bounded profile | Native machine, MIDI/PCM queues, converter history and SCSI transfer/media state restore together. |
| Graphical configuration | Open in Milestones 2, 3 and 4 | Shared React configuration/error presentation; standalone first-run persistence; plugin host-facing configuration. |
| Native sampling input | Open in Milestones 3 and 4 | Implement ADC/input transport and device capture; prove firmware sampling/save/reload; route actual host input into that same engine. |
| Actual DAW/editor operation | Open in Milestones 2 and 4 | Deliver editor transport/lifetime and qualify the SDK/ABI, scan/load, buses, rendering, multiple instances and project reopen in a named host. |
| Portable product sessions | Open in Milestones 3 and 4 | Relocated/missing-media recovery, product settings and recovery policy beyond an explicit same-build save. |

Nothing in the split claims those open features are implemented. Native input
continues to reject explicitly and the unimplemented Live Sampler FX class stays
unavailable. The [roadmap](../project/completion-roadmap.md) retains their checkboxes and
product-level acceptance criteria.

## Closure evidence

| Engine gate | Evidence |
| --- | --- |
| Native factory and single-instance routing | Fresh exported-module acceptance: native-only factory, requested interfaces, independent children, firmware boot/load/display, MIDI offsets, suspend/resume and shutdown. 480,000 stereo frames at 48 kHz match the offline reference exactly; release is silent, zero missed deadlines. |
| Timing profile | Existing 60-second runs at 44.1/48/96 kHz with varied blocks and exact PCM; approximately 279 ms software latency remains explicit. [Timing contract](../emulator/runtime/native-audio-timing.md). |
| Native and host state | Existing all-rate cold plugin replay and 131,072-frame native replay; partial SCSI command/data phases and media restoration. Every source/binary/fixture hash in the latest SCSI state record was rechecked and matches the current checkout. [State contract](../emulator/runtime/native-plugin-state.md). |
| Lifecycle and recovery | Isolated instances, owned-child cleanup, directory reopening and explicit last-save standalone recovery. [Boundary evidence](../condensed/validation/native-boundary-2026-10-11.json), [session contract](../emulator/guides/native-sessions.md). |
| Real standalone UI and readiness | Packaged desktop reaches Perform Play at 640×480 with 225,776 nonzero pixels; real runtime/browser recovery and control evidence is recorded. [Readiness contract](../emulator/runtime/native-firmware-status.md). |
| Licensing and distribution | BSD project license, preserved third-party terms, user-supplied firmware policy, clean source rebuild, dependency notices and exact 601-file Windows standalone artifact qualification. [Distribution review](distribution-qualification.md). |

The [closure record](../condensed/validation/milestone-1-completion-2026-10-11.json)
contains current hashes, the fresh command/result, and references to the existing
acceptance records. The latest full Python regression checkpoint is 241 passes;
this closure changed documentation only and did not rerun or relabel those tests.
The fresh exported-module acceptance uses this repository's interface definitions,
not an external DAW or SDK validator.

## Boundaries and next work

Snapshots require the same build, rate and block profile, quiescent controls and
matching startup media; external SCSI media is bounded to 64 MiB. SCSI writeback,
autosave, cross-build migration, native ADC, complete hardware fidelity and
low-latency device/DAW behavior are not closed by this milestone. Separate
acceptance binaries and historical records retain their original identities;
the source-rebuilt distribution executable has its own recorded hash.

Next work is Milestone 2 interface delivery, followed by Milestone 3 standalone
workflows. Milestones 4–6 retain actual plugin host, hardware coverage and final
release acceptance. The qualified distribution ZIP is unchanged by this roadmap
revision and still represents its dated, reviewed artifact.
