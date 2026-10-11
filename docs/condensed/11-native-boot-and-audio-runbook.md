# Native boot and audio checkpoint — 2026-10-10

The native path boots the original IC15 ROM and system disk, reaches the colour
Perform Play screen, accepts mouse/MIDI input, and loads sample floppies through
the firmware. New EEPROM profiles default to Mouse+CRT; existing profiles retain
their settings. This is a development checkpoint, not complete ASIC emulation.

## Run from an existing local build

For the React/WebView2 desktop player, follow [Standalone player](../STANDALONE_PLAYER.md).
Its isolated MAME process supplies real CRT/LCD frames and accepts native inputs;
audio still belongs to MAME. The [runtime protocol](../NATIVE_RUNTIME_PROTOCOL.md)
now serves an explicit [native VST3 development path](../NATIVE_CPP_RUNTIME.md).
Its processor harness passes; production selection and DAW acceptance remain open.
The command below remains the direct MAME alternative.

From the repository root in PowerShell, using your own firmware and media:

```powershell
$env:S760_ROM_BOOT = (Resolve-Path 'roms/BOOT/Roland_S-760_v1.11.BIN').Path
$env:S760_FLOPPY = (Resolve-Path 'roms/System/S760224.IMG').Path
$env:S760_SAMPLE_FLOPPY = (Resolve-Path 'roms/FDD/ROBOFULL.IMG').Path
$env:S760_F00A = '00'
$env:S760_IC4_MIDI_EXPERIMENT = '1'
$env:S760_NATIVE_INTERPOLATION_MONITOR = '1'
Push-Location mame-source
try {
    ./mames760.exe s760 -rompath '../roms;../roms/System' -window -mouse -skip_gameinfo
} finally { Pop-Location }
```

`ROBOFULL.IMG` is the local calibration disk, not a required boot ROM. Substitute
another native sample disk as needed. F5 inserts the configured sample floppy;
then load it through the firmware's Disk/Load controls. To supply MIDI from a
file, append `-midiin` and its absolute path. Firmware, recordings and images
are intentionally not distributed in Git.

The interpolation option enables the measured loop and envelope monitors.
`S760_NATIVE_LPF_MONITOR=1` and `S760_NATIVE_STEREO_MONITOR=1` are separate
experimental filter/mixer options; their combination with every pitch and loop
mode is not covered by the pitch capture. Environment switches test presence,
so remove a variable to disable it; assigning `0` does not disable it.

## Implemented pitch domain

The new opt-in interpolation path covers pitch words0x1000–0x8000 (quarter to double
speed),44100Hz clock selection, control4, unflagged forward loops with integer
boundaries and at least two samples. Unity output is unchanged. Existing measured
half/quarter-speed kernels remain in use. Other supported rates use a fixed
128-phase cubic and a symmetric output equalizer relative to unity playback.
Unsupported configurations keep the preceding renderer.

Hardware validation uses fixed coefficients, fixed gain and held recording
windows in100Hz–18kHz:28 pulse rates have0.697–0.926% normalized RMS error;
four independent noise cases have0.380–0.538%. This supports practical sub1%
agreement for those signals and settings. It does not establish bit-exact ASIC
arithmetic, absolute phase rounding, full-band20kHz behavior, other clocks,
reverse/alternate/one-shot interpolation, or pitch/filter transitions.

The remaining apparent mismatch was substantially an analysis error: a short
polyphase reconstruction filter allowed images to alias into the comparison
band. `scripts/audio_capture_reference.py` supplies the corrected reconstruction;
its tests include a tone that reproduces the failure. Increasing only the
upsampling ratio does not fix that filter transition band.

## Validation and build

The full88-key image passes native boot/load/playback. All88 outputs agree with
an independent frequency-domain reference within1.378 16-bit PCM units. With the
new option absent, the complete recorded output is bit-identical to the previous
executable. Unity remains unchanged with it enabled; release tails are silent.
[Per-case hardware metrics, capture hash and tested executable hash](validation/audio-pitch-2026-10-10.json).

For the existing generated Visual Studio projects, compile `mame_s760.vcxproj`
then link `mames760.vcxproj` in
`mame-source/build/projects/windows/mames760/vs2022`. Use Release/x64,
`/nodeReuse:false /m:1`, and `/p:BuildProjectReferences=false` for the link step.
Do not link while MAME is running. Both steps passed for this checkpoint.

`cmake --build build --config Release`, the core and plugin test executables,
and `python -m pytest tests -q` passed locally: **152 Python tests**, no skips.
NumPy and SciPy are required for the new measurement tests and are included in
the CI dependency installation. This is local validation, not a claimed GitHub
Actions run. The unrelated React frontend was not changed or retested.

## Commit scope

Include the native MCS-96/driver/build-target changes, condensed references,
measurement helper and tests, CI dependencies, and ignore rules. Preserve the
already staged removal of private research files from version control if that
remains the intended repository policy; the local shared evidence is retained.
Do not add firmware, generated disks, recordings, executables, logs, private
agent folders, or the unrelated untracked root file `--search`.

This checkpoint is ready for review and a commit. No commit or push was made as
part of the analysis. Remaining hardware work is tracked separately from the
completed pitch checkpoint in document06 and the local shared roadmap.

## Native state update — 2026-10-11

Version2 floppy-runtime checkpoints preserve pending scheduled MIDI across cold
restart and repeated recall:131072 stereo float frames match exactly, including
release. An unrelated old scheduled event is cancelled during restore. C++
queue snapshots preserve unread PCM and pending host blocks in unit tests;
complete VST3 state, SCSI and UI/recovery are still open. See the
[checkpoint contract](../NATIVE_CHECKPOINTS.md) and
[acceptance record](validation/native-scheduled-checkpoint-2026-10-11.json).

## Firmware readiness and recovery — 2026-10-11

The standalone header observes known OS 2.24 CRT labels: Perform Play, Disk
Load, Load... and Now Working. It distinguishes booting/ready/loading/idle,
unknown screens, timeout, clock stall and process failure. Idle does not assert
sample-load success. Reconnect retains the live patch; confirmed restart checks
live dirty/busy media, releases the old process and boots a new child. The UI
service remains available after child failure. Unsaved-state restoration is
still separate work. [Contract](../NATIVE_FIRMWARE_STATUS.md) and
[acceptance evidence](validation/native-readiness-2026-10-11.json).

## Host audio timing — 2026-10-11

The explicit native C++ processor now supports44.1/48/96kHz using a continuous
worker-side converter; MAME stays at44.1kHz. Sixty-second varied-block runs at
all three rates reproduce offline PCM exactly without callback deadline misses
or stream faults. Initial padding, MIDI lead and conversion delay total about279ms;
this is not total analog/device latency. This closes the Milestone1 timing
objective for the stated profile. Production plugin selection, native input,
complete state and DAW/editor qualification remain open. In-process rewind of
a pre-capture checkpoint has an overflow limitation; cold restoration passes.
See the [contract](../NATIVE_AUDIO_TIMING.md) and
[evidence](validation/native-audio-timing-2026-10-11.json).

## Exported VST3 engine selection — 2026-10-11

The exported factory now creates native MAME exclusively. Missing configuration
fails explicitly, and each instance has its own state directory/child. Actual
module acceptance passes boot/load, real displays, exact offline PCM at48kHz,
note offsets/release and suspension/termination. Historical core construction
remains diagnostic-only; native ADC/state and real DAW/editor qualification are
still open. The former FX class is unavailable until native input exists. See
[selection/configuration](../NATIVE_PLUGIN_SELECTION.md) and
[evidence](validation/native-factory-2026-10-11.json).

## Standalone sessions and crash recovery — 2026-10-11

Native Studio now saves and restores a versioned floppy-runtime checkpoint.
Restoration validates identities, protects live dirty/busy media and requires
confirmation. It can restart a crashed child and recover the saved loaded patch.
Native131072-frame replay and displays are exact; the normal-speed browser
save/restart/restore path preserves the original patch-table pixels. Checkpoint
buffer operations defer past the first periodic callback after pause so an old
emulated timer cannot continue over restored state. No guest state is forced.
Full plugin/SCSI snapshots and recovery of changes after the last save remain
open. [Contract](../NATIVE_SESSIONS.md) and
[evidence](validation/native-session-2026-10-11.json).
