# Packaged WebView2 editing and persistence

Completed 2026-10-17 on the hash-identified Windows development package with
Microsoft WebView2 **155.0.4283.60**. All four named editing workflows pass through
the package's actual desktop window, including firmware Save, session restore
and a fresh-process cold Load. Independent verification passes in ten native
processes; all 519 backend tests and TypeScript checking pass.

[Exact identities, commands, case results and audio measurements](../condensed/validation/milestone-6-webview-editing-2026-10-17.json).

## Interface actually exercised

The frozen executable launches normally, without `--no-browser`. It creates its
own WebView2 window and navigates it to the package's native session. QA supplies
a temporary loopback debugging port through the WebView2 environment and attaches
Playwright to that existing page. The test does **not** navigate an external
Chromium page to the application in desktop mode.

Both edit and cold-launch pages must have the package's own session URL. Their
renderer identities are recorded, and process inspection independently identifies
the test-owned `msedgewebview2.exe` and its installed version. Four cases use
eight fresh frozen-application launches. The debugging argument is QA-only;
product startup and sampler behavior are unchanged.

Mouse and keyboard events drive the actual rack controls, CRT pointer and firmware
dialogs. No direct MAME control socket, guest-memory writes, mocked bridge,
patched firmware or synthetic readiness result substitutes for those actions.

## Passed workflows

| Workflow | Serialized and visual result | Independent playback |
| --- | --- | --- |
| Performance part 1 Level 127→64 | Disk byte `0x4E40=C0`; edited field pixels return after restore and cold Load | 20,004 Hz remains unchanged; peak changes from 0.01694745 to 0.00853716 |
| Patch Bend Up/Down 0→12 | Bytes `0x8EE0..0x8EE1=0C 0C`; both field pixels persist | Centre/up/down measure 20,004 / 4,107 / 10,002 Hz |
| Partial Coarse Tune 0→12 | Byte `0x10E2D=0C`; field pixels persist | Named note 21 changes from 248 to 495 Hz, approximately one octave |
| Whole-range sample Area Erase, zero fade | The 8,192-byte sample body becomes zero and the waveform persists | Held output and note-off tails are exactly silent |

Each workflow loads a private ROBOFULL copy, edits through firmware controls,
executes the firmware Save confirmations and exports a 737,280-byte disk. It then
saves a session, restarts the sampler, restores that session and compares the
relevant field/waveform pixels. A second frozen process cold-loads the exported
disk and must reproduce those pixels again.

All 119,808 sample-allocation bytes remain unchanged for the three parameter
edits. Erase preserves all 110,592 neighboring allocation bytes. The original
disk and private library input stay byte-identical. Five invalid floppy sizes
also reject inside the WebView2 performance case without altering field pixels.

`scripts/verify_packaged_edit_audio.py --require-webview` independently checks
the exported disks and WebView-created sessions using the package's MAME and
byte-identical runtime protocol. The flag rejects external-browser evidence and
requires both renderer identities for every case. Disk and session playback
agree in pitch and peak; every note releases to exact silence.

## Reproduction

Use the exact development package recorded in the validation. From `google-ui`,
set `S760_EDIT_PACKAGE` to the package, `S760_EDIT_WORK` to a fresh private folder,
and `S760_EDIT_WEBVIEW=1`:

```powershell
node node_modules/@playwright/test/cli.js test packaged-editing.spec.ts --config=playwright.packaged.config.ts --output=<private-results>
```

Then run from the repository root:

```powershell
python scripts/verify_packaged_edit_audio.py --package <package> --browser-work <private-work> --state-dir <fresh-native-work> --require-webview
```

QA requires installed WebView2, desktop runtimes, private IC15 v1.11/OS 2.24 and
ROBOFULL, Node/Playwright, Python for independent checks, and loopback access.
The harness terminates only its own application tree, including native and
WebView children. No tested child process remains after acceptance.

## Limits

This closes the actual-WebView input and persistence gap for these four named
workflows on this dated development artifact and installed renderer. The window
runs silently and unthrottled; PCM verification is separate from device audio.
It does not qualify normal-speed device sampling through WebView2, arbitrary
editing combinations, every WebView2 version, clean-machine installation,
installers or final standalone/VST3 release artifacts. The complete
load/play/edit/sample/save/restore release workflow remains open.
