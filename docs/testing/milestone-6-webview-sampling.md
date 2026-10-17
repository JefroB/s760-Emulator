# Packaged WebView2 physical sampling

This acceptance exercises normal-speed stereo recording through the actual
Windows development package's WebView2 window, firmware Sample Save, exported
floppy media and session restart/restore. Independent native processes compare
the recorded wave RAM with the exported disk after both session restore and
cold firmware Sample Load.

[Dated results and exact identities](../condensed/validation/milestone-6-webview-sampling-2026-10-17.json).

Completed 2026-10-17 with WebView2 155.0.4283.60: the final run retains
46,387 frames per channel (1.052 seconds), measuring 440.085 Hz left and
879.833 Hz right. Each 101,376-byte sample allocation is exactly identical
across the exported disk and all three independent native readbacks. Peaks
are 2,287/2,297 PCM16 units, without clipping. The recording-status snapshot
reports 2,048 discarded input frames across the workflow and no native
recording underruns. The packaged case, 93 focused backend regressions and
TypeScript checking pass. Two earlier exploratory UI runs retained shorter
clips; only the final run uses the fresh post-restore checkpoint assertion.

## Test contract

The test source sends low-level 440 Hz left and 880 Hz right tones through
MOTU Pro Audio v2 ASIO outputs 3/4, physically connected to inputs 1/2. The
sampler selects the corresponding Windows MME stereo input at 44.1 kHz PCM16.
The generator uses amplitude 256 in PCM16 units; analog/interface gain can
change the measured input amplitude. Sampler output is disabled to avoid feedback.

The frozen application starts its own WebView2 window. Playwright attaches to
that existing page via a temporary loopback debugging port and verifies its
package-owned session URL. All sampler operations use real rack controls, CRT
pointer events and firmware dialogs. The application runs without `--fast`.
No guest memory, firmware bytes or control-socket commands are injected into
the packaged workflow.

The test mounts a private copy of an empty firmware-formatted 720KB disk,
records stereo audio, stops with the firmware right-button action and executes
Sample Save with its confirmations. It exports the disk, saves a session,
restarts the sampler, restores the saved session and waits for a newly written
checkpoint before retaining the restored state. Original firmware and the
formatted source disk stay byte-identical.

Independent verification uses the exact package's MAME in three new processes:
the recorded checkpoint, the checkpoint saved after UI restore, and a cold
firmware Sample Load from the exported disk. Both sample allocations must agree
byte-for-byte with disk in every process, including zero padding. Sample names,
L/R identities, frame counts, unclipped nonzero levels and the two known
frequencies are checked. These accelerated readbacks are separate from the
normal-speed physical recording.

## Reproduction

Requires installed WebView2, the documented physical MOTU loopback, Python with
NumPy/sounddevice, Node/Playwright, private IC15 v1.11 and OS 2.24, and an empty
firmware-formatted disk matching the validation hash. Run from `google-ui`,
setting absolute paths and a fresh work folder:

```powershell
$env:S760_SAMPLE_PACKAGE='<package containing S760Studio.exe>'
$env:S760_SAMPLE_WORK='<fresh private work folder>'
$env:S760_SAMPLE_BLANK='<private firmware-formatted 720KB disk>'
$env:S760_SAMPLE_DEVICE='<exact Windows MME recording device id>'
node node_modules/@playwright/test/cli.js test packaged-sampling.spec.ts --config=playwright.packaged.config.ts --output=<private-test-results>
```

Then, from the repository root:

```powershell
python scripts/verify_packaged_sampling.py verify --package <same-package> --work <same-work-folder>
```

The opt-in test skips without its four environment variables. It starts and
terminates only its own tone generator and application process tree. Readback
requires fresh `native-recorded`, `native-restored` and `native-cold` directories.

## Limits

This is one bounded physical-input workflow on a dated development artifact
and installed device/renderer. Windows MME does not expose physical driver loss
or measured latency. Reported discarded input frames cover the broader workflow;
they do not establish where a physical driver might have lost frames. Frequency
and exact persistence checks do not prove an uninterrupted original ADC stream.
Other rates/devices, disconnects, long-term drift, output-device playback,
clean-machine installation and final standalone/VST3 release artifacts remain
outside this result. Final combined load/play/edit/sample/save/restore release
acceptance remains open.
