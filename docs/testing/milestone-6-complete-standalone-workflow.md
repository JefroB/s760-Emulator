# Complete frozen standalone workflow

This qualification joins load, device playback, firmware editing, physical
sampling, firmware Save/export and session restore in the same sampler workflow.
It uses one hash-frozen development candidate with the layered configuration
interface. The later [source-built final archive](standalone-release-promotion.md)
has completed distribution promotion and repeated workstation acceptance from
its extracted bytes. This page retains the earlier572-file candidate record.
A separate Windows clean-machine run remains required. The user confirmed that
no clean machine or VM is available; an updated final-archive handoff is prepared.

[Dated results and identities](../condensed/validation/milestone-6-complete-standalone-workflow-2026-10-17.json).
[Clean-machine handoff procedure](standalone-clean-machine-handoff.md).

Completed workstation qualification on **2026-10-17**: both complete UI cycles
pass in 9.9 minutes, using four frozen-application launches. Twelve fresh native
processes pass independent readback. All 572 candidate files remain unchanged.
The separately extracted handoff also passes Windows PowerShell 5.1 default-path
launch, original-firmware boot and actual WebView2 configuration readback with
development-tool paths removed from the child process. It is still a workstation
test; the collector correctly leaves the nine manual workflow steps incomplete.

| Measurement | Cycle 1 | Cycle 2 |
| --- | --- | --- |
| Windows playback frequency | 20,004.272 Hz | 20,004.272 Hz |
| Edited/baseline Windows peak ratio | 0.502703 | 0.502703 |
| Recorded L/R tones | 440.085 / 879.833 Hz | 440.085 / 879.833 Hz |
| New allocation bytes, each channel | 138,240 | 175,104 |
| Default recorded-marker frame count | 66,223 | 87,535 |
| Nonzero PCM extent, frames | 66,223 | 87,542 |
| Original sample bytes retained | 119,808 | 119,808 |

The second recording contains seven nonzero frames after its default loop-start
marker but before the serialized sample end. Those bytes are retained and match
exactly, rather than being discarded as presumed padding. Frame markers are not
a guarantee of requested wall-clock recording duration. Padding is checked beyond
serialized sample end; full allocation bytes are compared in all three sample
readbacks per cycle. Native program playback remains 20,004 Hz, with baseline
peak 0.0169474501 and edited/restored peak 0.0085371584; all releases are silent.

The v2 handoff archive is 21,562,136 bytes; SHA-256:
`8f2905876c5818bad15d671e813c1e4a4457e4edb338d1c63f3d6fc9d956c482`.
The committed [candidate manifest](../condensed/validation/milestone-6-standalone-candidate-manifest-2026-10-17.json)
identifies every packaged file. BUG-101 records the corrected kit default-path
startup; no application bytes changed during this qualification.

## Observable acceptance

`packaged-workflow.spec.ts` defines two fresh-profile repetitions against the
same package manifest. The frozen executable opens its actual WebView2 window;
Playwright attaches to that app-owned URL without navigating an external browser.
The package runs from a separate working directory whose path contains spaces.
Every manifest file is checked before and after the workflow. No runtime rebuild
or application-file replacement occurs between repetitions.

All firmware operations run at normal speed. Initial startup is muted; the test
then uses Configuration → Audio to select WASAPI, the actual Realtek digital
endpoint, a 60 ms buffer target and enabled output, and confirms the restart.
The selected MOTU Windows MME recording input is active at 44.1 kHz stereo PCM16.
The optional keyboard is enabled through MIDI & display, with acknowledgement
awaited before leaving Configuration.

Each repetition performs the following operations:

1. Firmware-load the private ROBOFULL volume through Gotek and Disk → Load.
2. Hold and release C4 through the actual on-screen keyboard. Independently
   capture eight seconds from the selected Windows endpoint with the QA-only
   WASAPI loopback observer. Check finite unclipped output, stable pitch,
   sustained note activity and a released tail below `1e-7` float amplitude.
3. Change part 1 Level 127→64 using the CRT field and VALUE knob. Return to the
   normal Perform view before comparing pixels, so an active edit highlight is
   not confused with changed parameter data. Repeat device playback and verify
   the expected attenuation without a pitch change.
4. Execute firmware Volume Save and its confirmations, then export `EDITED.IMG`.
   Require serialized byte `0x4E40=C0`. The library source remains unchanged.
5. Keep that edited program loaded. In Sampling choose **New** before Ready,
   preserving the 13 existing sample allocations. Record known low-level
   440/880 Hz tones through the physical MOTU outputs 3/4 → inputs 1/2 route,
   stop through the firmware right-button action and choose End. Sampler output
   is reduced to zero for recording and returned to its original level afterward.
6. Mount a private firmware-formatted blank disk. Firmware-save all samples and
   export `CAPTURED.IMG`, retaining both the original samples and the new L/R pair.
   Sample-only media and the separately saved program volume serve different
   purposes; the combined session retains both together.
7. Return to Perform, require the edited field pixels and Save session. Restart
   the sampler with explicit confirmation, restore the saved session, require
   the same edited field and repeat measured device playback/release. Save a
   fresh post-restore checkpoint and wait for its completed publication.
8. Terminate the completed test-owned app tree, launch the same frozen executable
   again with its saved profile, restore the saved session and repeat the field,
   Windows-device playback and release checks. This bounded fresh-process
   reopen is not a new power-loss/recovery qualification.

## Independent native readback

`verify_packaged_workflow.py verify` uses the same package's MAME and matching
runtime protocol. Three fresh native processes read the combined recorded
checkpoint, the checkpoint saved after UI restore, and a cold firmware Sample
Load of the exported sample disk. All 119,808 original sample bytes must match
ROBOFULL. Both new allocations must match disk byte-for-byte, including padding,
   with the known L/R tones, valid frame markers and no clipping. Sample records use
the documented ten-records-per-sector layout; serialized clusters locate PCM.
Firmware New derives a fresh name from the selected sample in a loaded library,
rather than necessarily naming it `NEW:Unnamed`.

Three additional fresh native processes render the original volume, edited
volume export and combined restored session. Pitch must agree; the edited peak
must approximate 64/127 of baseline; restored output must match the edited
export. All notes must release to exact native silence. These accelerated
readbacks are distinct from the normal-speed UI/device measurements.

## Reproduction

Build the Windows endpoint observer separately; it observes output and never
supplies sampler audio:

```powershell
cmake -S scripts/qa -B <private-loopback-build> -A x64
cmake --build <private-loopback-build> --config Release
```

From `google-ui`, set absolute paths for `S760_WORKFLOW_PACKAGE`,
`S760_WORKFLOW_MANIFEST`, `S760_WORKFLOW_WORK` (fresh parent),
`S760_WORKFLOW_BLANK`, `S760_WORKFLOW_INPUT` (exact Windows MME ID) and
`S760_WORKFLOW_LOOPBACK` (the observer executable), then run:

```powershell
node node_modules/@playwright/test/cli.js test packaged-workflow.spec.ts --config=playwright.packaged.config.ts --output=<private-results>
```

From the repository root, independently verify both case directories:

```powershell
python scripts/verify_packaged_workflow.py verify --package <same-package> --work <work-parent>/cycle-1
python scripts/verify_packaged_workflow.py verify --package <same-package> --work <work-parent>/cycle-2
```

The test skips without its explicit prerequisites. It requires the documented
private firmware/media, physical MOTU route, Realtek Windows endpoint,
WebView2, Python/NumPy/sounddevice for QA, and Node/Playwright. Those QA tools
are not application runtime dependencies. The clean-machine handoff uses only
the frozen package and Windows PowerShell, with user-supplied firmware/media.

## Remaining qualification

This is bounded workstation acceptance of a frozen candidate, including real
Windows output and physical input. Windows loopback is a digital endpoint
measurement, not analog-output parity, measured physical latency or proof of
continuous lossless device operation. Input-status counters and Windows capture
discontinuity flags remain part of the evidence; short clips do not qualify
long-duration sampling or drift. Other devices/rates remain separate profiles.

The archive preserves `DEVELOPMENT-ONLY.txt` and its original audit status. It is
an internal acceptance handoff, not a public release or an installer. Final
source/notices distribution review, final release revision/artifact freeze,
clean-machine prerequisite/install/workflow evidence and VST3 host qualification
are not inferred from this run. The broad release objective stays open until
those applicable gates are met.
