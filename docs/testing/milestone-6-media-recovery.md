# Packaged unformatted-media and dirty-session recovery

Completed2026-10-15 for the named development profile: eight browser
unformatted-media/reload cycles and the separate dirty-session guard/restore case
pass. Independent inspection passes in21 fresh native processes;404 backend
regressions and TypeScript checking pass.

All119808 sample-allocation bytes remain exact. The eight unformatted-session
readbacks also match the baseline's full33554432 wave bytes. The dirty session
differs in13 nonsample bytes following edit/Save; those ranges are recorded,
while all sample bytes remain exact. Baseline playback is20004Hz at peak
0.01694745; both edited-disk and dirty-session recall give20004Hz at peak
0.00853716, with silent release tails. The two737280-byte dirty exports match
exactly.

[Source/package identities, commands and individual results](../condensed/validation/milestone-6-media-recovery-2026-10-15.json).

This acceptance profile uses the dated Windows development package from
[packaged setup qualification](milestone-6-package-setup.md), actual OS2.24,
IC15v1.11 and the hash-identified ROBOFULL sample fixture. No emulator behavior,
guest memory or firmware binary is patched to obtain a result.

## Correct-size unformatted profiles

Four private raw images contain only00 orFF bytes, at737280 and1474560 bytes.
They pass the host's raw geometry check but contain no valid Roland filesystem.
Independently inspected native frames show `xxxxxfiles`, unknown Disk/Marked
statistics and no valid file rows. Pressing the firmware Load action leaves that
sentinel unchanged. This is an observed firmware directory outcome, not a host
size rejection or a generic success/readiness label.

The real packaged browser test exercises each profile twice. Every cycle:

1. Mounts the image through Gotek, opens firmware Disk/Load and checks the
   independently established sentinel pixels before and after pressing Load.
2. Exports controller media and compares every byte with the original fixture.
3. Returns to Perform Play, checks the loaded patch table and saves a retained
   session for independent native inspection.
4. Reinserts ROBOFULL and executes Load. The original firmware's **Clear Internal
   Memory Before Loading** prompt is identified by its own label pixels before
   selecting Yes. Completion and the original loaded patch table must return.
5. Reopens Disk/Load and checks the known-bad sentinel is absent from the valid
   directory, then returns to Perform Play for the next cycle.

A disk-ready transport observation alone cannot satisfy these assertions. The
first trial omitted the firmware's clear-memory confirmation and timed out;
native screen inspection established the required user action. No emulator fix
or deadline suppression was applied to bypass that prompt.

## Dirty-session guard sequence

A separate fresh packaged instance loads ROBOFULL, changes performance part1
Level127→64 and performs firmware Save. Before export, Gotek replacement, Eject
disk and confirmed Restart sampler must reject the operation while retaining
unexported writes. Save session captures that dirty controller state.

Export produces the edited disk, with the expected level byte and all119808
sample-allocation bytes unchanged. After a clean restart, restoring the earlier
session must reinstate the dirty-media guard. A second export must equal the
first737280-byte image exactly. Both original and private library inputs must
remain unchanged throughout.

## Independent native inspection

`scripts/verify_packaged_media_recovery.py` cold-restores the baseline, eight
retained sessions and dirty session into the package's actual MAME executable,
using the source controller with byte-identical package/source Lua. It compares
all13 independently identified sample allocations against the original disk.
Full32MB wave-memory differences are recorded separately: firmware catalog
records can change during media operations, so those differences are not silently
treated as lost sample data or whole-session equality.

Native PCM checks require the baseline fixture's pitch/level and silent note-off
tails after every retained session. The dirty session and a fresh Load of its
exported disk must agree in pitch/peak and show the expected approximately half
level. This is native functional evidence, not physical audio or device latency.

## Reproduction and limits

From `google-ui`, set `S760_MEDIA_PACKAGE` to the complete frozen package,
`S760_MEDIA_WORK` to a fresh private directory, then run:

```powershell
node node_modules/@playwright/test/cli.js test packaged-media.spec.ts --config=playwright.packaged.config.ts --output=../docs/ic20-hle-findings/chatGPT-work/media-results
```

From the repository root:

```powershell
python scripts/verify_packaged_media_recovery.py --package <package> --browser-work <browser-work> --state-dir <fresh-native-work>
```

If the unformatted case was rerun independently, `--unformatted-work` accepts
that case's directory while the dirty result remains under `--browser-work`.
Local firmware, Chromium, loopback access and fresh private directories are QA
prerequisites. No firmware, generated disks or sessions belong in distributions.

The profile is bounded, silent and unthrottled on the development workstation.
It does not establish arbitrary corrupt FAT-chain handling, physical damaged
floppies, power-loss durability, normal-speed device stress, an indefinite soak,
clean-machine installation or final-release artifact acceptance.
