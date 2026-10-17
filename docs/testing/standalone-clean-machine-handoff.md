# Standalone clean-machine acceptance handoff

This kit tests one frozen **standalone candidate**, including the layered
WebView2 configuration interface. Extraction does not establish installation
acceptance. The package's manifest and distribution profile identify whether
its source/dependency contents have separately qualified for redistribution. The
workstation workflow record and package manifest identify the exact bytes under
test. Clean-machine acceptance remains pending until a separate Windows machine
completes this procedure and its evidence is reviewed.

## What to provide

Download the [complete standalone acceptance kit](https://github.com/JefroB/s760-Emulator/releases/download/standalone-acceptance-2026-10-17/s760-standalone-acceptance-2026-10-17.zip)
from the [qualification prerelease](https://github.com/JefroB/s760-Emulator/releases/tag/standalone-acceptance-2026-10-17).
The [artifact directory](../../artifacts/standalone/README.md) records its checksum
and local download location. No findings-folder access or source checkout is
needed. This is the same frozen archive used for workstation qualification.

Use a fresh Windows x64 installation or disposable VM without the source checkout,
Python, Node, CMake or Visual Studio. Record the original machine/prerequisite
state before installing anything. Extract the kit into a writable folder whose
name contains spaces. Keep the complete `S760Studio` folder together.

The package requires Microsoft Visual C++ v14 x64, .NET Framework4.8 and WebView2 runtimes, plus the
selected audio device's driver. The kit's package README,
`SYSTEM-PREREQUISITES.json`, dependency inventory and notices are authoritative
for this candidate. Record whether these runtimes were already present or had
to be installed. They are not downloaded or installed by the acceptance scripts.
Windows and the device driver own audio-format conversion.

Supply your own IC15 v1.11 boot ROM, OS 2.24 image, ROBOFULL sample disk and an
empty firmware-formatted 720KB disk. Keep them outside the extracted kit. The
manifest and package contain no proprietary firmware, media, saved sessions or
recordings. Use private working copies of sample disks. The documented recording
profile is 44.1 kHz stereo; record the actual output/input device names and driver
versions. The workstation's physical fixture uses MOTU outputs 3/4 connected to
inputs 1/2, carrying low-level 440/880 Hz tones. A different device/profile needs
its own recorded result.

## Start without development tools

Open Windows PowerShell in the extracted kit and substitute your own paths:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-Acceptance.ps1 -BootRom 'C:\My S760\boot.bin' -SystemDisk 'C:\My S760\S760224.IMG' -MediaDirectory 'C:\My S760\disks' -ReportDirectory 'C:\S760 acceptance evidence\trial-1'
```

This invocation changes execution policy only for that PowerShell process. The
script verifies every packaged file's SHA-256, rejects missing/extra files,
checks the documented firmware identities and creates a fresh evidence folder.
It records Windows, detected runtime versions and development tools on PATH.
It launches the frozen executable from the evidence directory with Python/Node/
S760 environment overrides removed and only Windows directories on the child
PATH. Your environment is restored immediately afterward. The app uses a private
profile outside the package. `-VerifyOnly` verifies inputs without launching and
cannot produce a completed acceptance result.

If a runtime or device is missing, retain a screenshot and its exact error text,
record the remediation, and repeat with a fresh evidence folder. A test on the
development workstation cannot be relabelled as clean-machine acceptance merely
by stripping PATH.

## Complete the workflow twice

Use two fresh evidence folders/profiles and the same package manifest. Do not
replace application files between repetitions. In each run:

1. **Launch:** Wait for original-firmware Perform Play. Open Configuration and
   visit all four categories. Confirm the footer fits the display and dialogs
   close one layer at a time. Record display resolution, Windows scaling and a
   screenshot. In Audio, choose the intended output and recording input, enable
   output and apply with the restart confirmation. In MIDI & display, show the
   keyboard. Record any startup/runtime/device error rather than bypassing it.
2. **Load:** Insert the private ROBOFULL copy using Gotek, then perform firmware
   Disk → Load of its volume/performance. Capture the resulting Perform screen.
3. **Play:** Hold C4 on the on-screen keyboard for about three seconds, release
   it and confirm the note stops. Retain an independent device recording where
   available; otherwise record that this was listening-only acceptance. Document
   the output routing. A native offline render does not establish device output.
4. **Edit:** Point at part 1 Level and use VALUE to change 127 to 64. Repeat the
   same note: pitch should remain stable and level should decrease. Record the
   field and result. The workstation test measures an approximately 64/127 peak
   ratio, not just an active MIDI indicator.
5. **Firmware save/export:** Execute firmware Disk → Save for the edited volume,
   including its confirmations. Wait for completion and use Configuration →
   Session & disks → Export disk. Retain the export separately as `EDITED.IMG`.
   The library input must remain unchanged.
6. **Sample:** Keep the edited program in memory. In firmware Sampling, choose
   **New** before **Ready** to allocate a new sample rather than resample the
   currently selected existing one. Create
   a new stereo recording of a known external signal for about one second; stop
   and choose End. Record the L/R sample names, waveform, source signal and input
   status. Keep output muted while recording if the physical routing could feed
   output back to input; restore its former level afterward.
7. **Sample save/export:** Insert the private blank formatted disk. In firmware
   Disk → Save select Sample, mark all samples and execute the confirmations.
   Wait for completion and export it as `CAPTURED.IMG`. This image holds the
   original and newly recorded samples; the edited program is also preserved in
   its separate volume export and the combined session.
8. **Session restore:** Return to Perform Play, verify Level 64, and Save session.
   Restart the sampler with explicit discard confirmation, then Restore saved
   session with replacement confirmation. Confirm Level 64, playback/release
   and the recorded sample waveforms/names. Save the restored session again.
9. **Cold reopen:** Close the application normally. Relaunch the same executable
   with `--state-dir` pointing to this evidence folder's `profile`; saved settings
   supply the firmware/media paths. Restore the saved session again and repeat
   the edited-note and recorded-waveform checks. In an independent fresh profile,
   cold-load the exported edited volume and recorded samples through firmware
   Disk → Load, selecting the corresponding target. Retain screenshots and audio.

Do not force through a dirty-media or busy-disk rejection. Finish/export the
operation and record the rejection and subsequent recovery. Sample-only exports
and full sessions serve different purposes; the steps intentionally retain both.

## Return reviewable evidence

In each evidence folder, edit `results.json`. Every step starts as `not_run`;
set it to `passed` or `failed`, identify a real evidence file relative to that
folder and describe observations/errors in `notes`. Preserve screenshots,
device recordings and the application's logs. Record who ran the test, machine
origin, prerequisite installation steps and both repetitions in a text file.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Complete-Acceptance.ps1 -ReportDirectory 'C:\S760 acceptance evidence\trial-1' -CleanMachineConfirmed
```

Use `-CleanMachineConfirmed` only when that environment was actually used. The
collector checks that claimed passes have evidence files and hashes media,
recordings and sessions without embedding them in the report. Missing steps
remain incomplete. A verify-only run remains `NOT_RUN`. Its output is a manual
acceptance report, not an automatic release approval or roadmap change.

Review `environment.json`, `results.json`, `acceptance-summary.json`, notes and
the corresponding evidence together. Keep firmware-derived saved sessions and
private recordings outside the distributable kit. Acceptance of this standalone
candidate does not qualify the VST3 host matrix or public distribution of a
changed artifact; source/notices review and the final release identity remain
separate gates.
