# Native boot and audio checkpoint — 2026-10-10

The native path boots the original IC15 ROM and system disk, reaches the colour
Perform Play screen, accepts mouse/MIDI input, and loads sample floppies through
the firmware. New EEPROM profiles default to Mouse+CRT; existing profiles retain
their settings. This is a development checkpoint, not complete ASIC emulation.

## Run from an existing local build

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
