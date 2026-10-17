# Packaged abrupt-termination recovery

The [follow-on publication fault qualification](milestone-6-checkpoint-publication.md)
covers opened zero-byte temporary archives, Windows replacement denial and retry.
The evidence below remains scoped to exits after a completed checkpoint.

Completed 2026-10-17 for the hash-identified Windows development package:
three forced process-tree termination/relaunch cycles preserve a completed
automatic checkpoint, the firmware edit, dirty floppy state and sample data.
The browser acceptance passes, independent inspection passes in eight fresh
native processes, and all 515 backend regressions pass.

[Commands, identities and results](../condensed/validation/milestone-6-crash-recovery-2026-10-17.json).

## Qualified sequence

The frozen standalone service serves its packaged React assets and launches its
packaged MAME. Real browser controls drive OS 2.24 Load of a private ROBOFULL
copy, performance part 1 Level 127→64, and firmware Save. The original source
disk and private library copy remain unchanged.

The test observes dirty, idle media at revision 134 and waits for a new recovery
archive from the unchanged **60-second production timer**. It never presses
Save recovery now. Reconnect display requests a current media status after the
firmware write; media status is not continuously streamed.

Each cycle forcibly terminates only the test's frozen service PID and its
descendants with Windows `taskkill /T /F`, bypassing normal-close recovery.
A new process opens the same profile. On the first cold launch, the previous
checkpoint must survive another 61 seconds without replacement. The user-facing
Restore recovery confirmation then restores the sampler.

Every cycle checks the loaded patch-table pixels, the dirty-media Eject guard,
the unchanged manual-session slot before an explicit Save session, and an exact
737,280-byte export of the edited disk. Retained screenshots show Level 64 and
are identical across the three cycles. The exported level field is `C0` at
`0x4E40`; all 119,808 bytes across 13 sample allocations remain exact.

## Independent native readback

`scripts/verify_packaged_crash_recovery.py` uses the tested package's MAME and
byte-identical source/package Lua. Each retained session is cold-restored in a
fresh native process. It must restore dirty, idle media, export the exact edited
disk, and retain all sample allocations at their established wave-RAM location.
Each wave dump is 33,554,432 bytes; full wave-RAM equality is not claimed.

Separate fresh processes compare the original disk, the edited disk and all
three sessions. Pitch remains 20,004 Hz. Peak changes from 0.01694745 to
0.00853716, matching Level 127→64, and every note-off tail is exactly silent.
The three session measurements match the cold edited-disk playback.

## Reproduction

Build with `scripts/build_standalone.ps1` and the recorded desktop build
dependencies. From `google-ui`, set `S760_MEDIA_PACKAGE` to that complete package
and `S760_MEDIA_WORK` to a fresh private directory, then run:

```powershell
node node_modules/@playwright/test/cli.js test packaged-media.spec.ts --grep 'abrupt process-tree' --config=playwright.packaged.config.ts --output=<private-results>
```

From the repository root:

```powershell
python scripts/verify_packaged_crash_recovery.py --package <package> --browser-work <private-work>/crash --state-dir <fresh-native-work>
```

Private IC15 v1.11, OS 2.24 and ROBOFULL, Chromium and loopback access are QA
prerequisites. The workstation already has the Windows desktop runtimes.

Fresh package qualification also found and fixed BUG-098: six README template
links escaped the package after documentation relocation. The regression fails
before correction; all 20 package-audit tests and fresh package preparation pass
afterward. BUG-099 fixes the media harness's failed-trial cleanup to terminate
its native descendants. No sampler behavior was changed for these results.

## Limits

This qualifies abrupt process-tree termination **after a completed checkpoint**
on this development workstation. It does not qualify physical power loss,
interruption during checkpoint publication, later unsaved changes, normal-speed
device audio, final WebView input, an installer or a clean machine. The changed
package passes the development audit; its source/dependency release qualification
remains open. Milestone 6 as a whole remains open.
