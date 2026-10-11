# Native plugin state contract

The native instrument now implements suspended `getState`/`setState` for the
bounded native checkpoint profile. A single archive contains native
machine/Lua state, unread stereo PCM, queued host blocks and note events, host
clock, native scheduling origin, and sample-rate converter phase and FIR history.
It never serializes the historical core as a substitute.

## Supported lifecycle

Configure the same sample rate (44100, 48000 or 96000 Hz) and maximum block size
before recall. Stop audio callbacks and call `setProcessing(false)` before either
state operation. Save/restore performs allocation and disk/transport I/O outside
the audio callback. Resume explicitly after success. A fresh exported component
can restore without loading the sample floppy again.

The current format is a four-byte little-endian archive length followed by
`S760NPS1`, SHA-256 of the payload, and versioned little-endian fields. Counts,
clock consistency, finite decoded PCM, converter history, queue continuity and
section sizes are validated. The archive is bounded to 260 MiB. Identity pins
native executable, boot ROM, system disk, Lua protocol, host module bytes and
external SCSI filenames/content. The media identity is folded into the module
identity slot.
Rebuilding either executable invalidates older archives intentionally. The hash
detects corruption; it is not an authenticity signature.

Malformed outer archives reject before machine application. A failure after
worker shutdown blocks processing and further saves until a valid restore
completes. A failed host stream write reports failure and retains resumability.
The caller must discard a partially written output stream. Partial successful
IBStream reads/writes are supported.

## Verified acceptance — 2026-10-11

The exported-module harness boots original firmware and loads ROBOFULL through
firmware controls. At all three rates it saves a host note-on still queued in a
64-frame block, restores in a fresh child, and compares one second of PCM. It
then saves an active voice with note-off, compares two seconds in a fresh child,
and repeats recall for another two seconds. Every stereo float frame matches
exactly: 220500 at 44100 Hz, 240000 at 48000 Hz, 480000 at 96000 Hz. Release ends
in silence. Corrupt archives, invalid native payloads and failing host writes
exercise rejection/recovery. Separate converter unit tests cover FIR history and
phase reconstruction. 25 C++ executables and 227 Python regressions pass.

```powershell
cmake --build build --config Release
./build/Release/s760_native_factory_tests.exe . docs/ic20-hle-findings/chatGPT-work/state-check --state 48000
```

Use a fresh private state directory. See the
[evidence record](condensed/validation/native-plugin-state-2026-10-11.json).
This is the repository's exported-module harness, not real DAW/SDK ABI acceptance
or evidence of hardware audio parity.

## SCSI state acceptance

The driver now saves device presence/type, all startup-sized media buffers,
controller/CDB state and a stable transfer shadow covering the largest existing
READ/WRITE(10) transfer: 65535 times 2048 bytes. Registration stays valid while the
live transfer vector resizes. This adds approximately 128 MiB of resident save
storage per machine, and native snapshots are correspondingly larger.

The host profile permits up to 64 MiB of external files under the private
`roms/SCSI` directory. Stage the same original files before starting each cold
runtime. Their filenames/content are pinned at startup; changed/missing files
reject before recall. Restore changes emulated memory, not the original host
images. This includes the driver's existing default blank targets.

Partial CDB, DATA_IN and DATA_OUT restore tests pass. A cold device test restores
media bytes after replacing the generated host fixture; the public client is
stricter and rejects changed backing files. Native scheduled playback with SCSI
present replays 131072 stereo frames and refreshed CRT/LCD exactly. All-rate
exported-plugin recall still passes. See [current evidence](condensed/validation/native-scsi-state-2026-10-11.json).

## Remaining scope

SCSI WRITE currently acknowledges data without updating disk contents (BUG-015).
Snapshot preservation does not qualify firmware disk Save or hardware SCSI
fidelity. Larger media configurations are outside this initial snapshot profile.

Actual DAW state-call ordering, differing host block sizes/rates, simultaneous
editor controls, native ADC, autosave and cross-build migration remain unqualified.
The Milestone 1 snapshot objective is complete for this quiescent, same-build,
same-rate/block-size profile. Actual DAW/editor and sampling objectives remain open.
