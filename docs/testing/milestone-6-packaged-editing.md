# Packaged standalone editing acceptance

The dated2026-10-15 Windows development package passes all four named browser
workflows below and five invalid-size rejection cases. Backend regression:
397 passed. TypeScript checking and packaged WebView2 CRT readback also pass
(640×480, OS ready). These are scoped development results, not a final release.

Independent cold disk/session PCM checks also pass: performance peak falls from
0.01694745 to0.00853716 without changing20004Hz pitch; patch centre/up/down
measure20004/4107/10002Hz in this fixture; partial tuning changes248Hz to495Hz
at1Hz FFT resolution. The erased note is exactly silent. All note-off tails are
silent, and cold disk/session frequencies and peaks agree within the stated
assertions. These results cover ten fresh native instances, not physical audio.

[Commands, hashes, individual case results and limits](../condensed/validation/milestone-6-packaged-editing-2026-10-15.json).

The automated workflow uses the frozen Windows standalone service, its packaged
React assets and its packaged native MAME executable. Chromium drives the real
CRT mouse surface, rack Value knob, Gotek and Configuration actions. The browser
does not send direct runtime controls or modify guest memory.

Four named cases cover performance part1 Level127→64, patch Bend Up/Down0→12,
partial Coarse Tune0→12 and sample1 whole-range Area Erase. Each starts from a
private ROBOFULL copy, performs firmware Save, exports a new disk, saves and
restores a session after restarting MAME, and loads the exported disk in a second
standalone process with a fresh state directory. Field comparisons select the
same parameter before comparing pixels, because firmware selection changes ink.
The erase comparison uses the waveform region rather than dynamic header values.

Export assertions check the named serialized parameter bytes and all119808
sample-allocation bytes for non-destructive edits. Erase checks the8192-byte
source body is zero and110592 neighboring allocation bytes remain unchanged.
Both the original library and its working library copy must stay byte-identical.
The performance case also rejects empty, one-byte-short and one-byte-long720KB
images and one-byte-short/long1.44MB images while preserving loaded field pixels.

`verify_packaged_edit_audio.py` independently cold-loads those exact exported
images into the package's MAME executable and measures pitch, gain and release.
It compares with two fresh original-media baselines, checks octave tuning and
bend frequencies, and requires silent erased-sample playback and note-off tails.
This native PCM check uses the source Python controller with byte-identical
package/source Lua; it is separate from browser-controls evidence.

## Reproduce

Prerequisites: Windows x64 development dependencies, a working native build,
WebView2 for desktop checks, Playwright Chromium, and locally supplied IC15v1.11,
OS2.24 and hash-identified ROBOFULL media. Build dependencies must be available to
the Python interpreter used by the package script. Use fresh private directories;
the test refuses to reuse case directories. Local loopback access must be allowed.

```powershell
./scripts/build_standalone.ps1 -OutputDirectory docs/ic20-hle-findings/chatGPT-work/m6-package
$env:S760_EDIT_PACKAGE = (Resolve-Path docs/ic20-hle-findings/chatGPT-work/m6-package/dist/S760Studio).Path
$env:S760_EDIT_WORK = "$PWD/docs/ic20-hle-findings/chatGPT-work/m6-browser"
Push-Location google-ui
node node_modules/@playwright/test/cli.js test --config=playwright.packaged.config.ts --output=../docs/ic20-hle-findings/chatGPT-work/m6-browser-results
Pop-Location
python scripts/verify_packaged_edit_audio.py --package $env:S760_EDIT_PACKAGE --browser-work $env:S760_EDIT_WORK --state-dir docs/ic20-hle-findings/chatGPT-work/m6-audio
```

The dedicated Playwright config starts no Vite server: every tested page and
asset comes from the frozen package. Each case owns and cleans up its processes.
Set `PLAYWRIGHT_BROWSERS_PATH` only if Chromium is installed outside the current
account's default cache. No firmware is bundled in the package.

## Physical screen references

The local `screenshots/` folder contains37 actual-hardware CRT photographs.
`perform-1.jpeg`, `patch-3.jpeg`, `partial-1.jpeg` and `sample-11.jpeg` show the
four relevant screen structures. Visual inspection confirms the corresponding
titles, Level/Pan/Out columns, Bend Up/Down and modulation matrix, Coarse/Fine Tune
and keyboard, and Area Erase From/To/Fade, waveform and Exec controls. The
white selection row visible in the Patch Control photo is firmware behavior.

These photos use a piano library with different values, durations and sampling
rates from ROBOFULL. Camera perspective, CRT scan/optics and those state differences
prevent treating this review as exact pixel/color parity or as evidence of audio
agreement. Photos remain private and are excluded from packages. See the
[screen evidence reference](../condensed/09-hardware-screens-and-layout-evidence.md).

This acceptance profile is silent, unthrottled and browser-driven on the
development workstation. It does not qualify normal-speed physical recording,
audio-device reliability, WebView input for every edit, all firmware commands,
installers, a clean machine or final release artifacts.
