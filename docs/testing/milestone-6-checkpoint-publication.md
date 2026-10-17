# Packaged checkpoint-publication fault recovery

Completed 2026-10-17 for the same frozen Windows development package qualified
by the [completed-checkpoint crash test](milestone-6-crash-recovery.md).
Three interruptions of incomplete publication, a real Windows replacement denial
and a successful retry pass through the packaged browser interface. Ten fresh
native processes verify the resulting state. All 519 backend tests pass,
including 21 checkpoint tests.

[Source/artifact identities, commands and measured results](../condensed/validation/milestone-6-checkpoint-publication-2026-10-17.json).

## Qualified failure points

The private starting fixture is the hash-identified Level 64 recovery archive
from the preceding qualification, with dirty firmware Save data. Each cycle
restores it through the UI, changes the live performance Level to 63, and presses
Save recovery now. No firmware, guest memory or writer code is patched.

| Failure point | Observation and required result |
| --- | --- |
| Temporary replacement opened, before payload write | The external QA watcher observes the new `.tmp` file and terminates only the spawned service and its descendants through bound Windows process handles. All three observed and retained temporary files contain **zero bytes**. The published recovery archive must remain byte-identical. |
| Cold restart after that interruption | The packaged UI preserves and restores the previous Level 64 checkpoint, not the unsaved Level 63 state. The actual level-field pixels must return to their previous hash. Dirty-media Eject protection and exact edited-disk export must return. |
| Windows denies destination replacement | A separate QA process opens the existing archive without delete sharing. The real writer stages its new archive but Windows rejects replacement. The UI must report access denied; the previous archive and live Level 63 field must remain intact, and the failed writer must remove its temporary output. |
| Retry after releasing the handle | A second UI Save recovery now must succeed. Restoring that new archive must retain Level 63, proving the retry publishes new work rather than silently keeping the previous checkpoint. |

The interruption helper is `scripts/interrupt_checkpoint_publication.py`.
It identifies descendants before watching, binds handles to those exact
processes and rejects an interruption if the staged archive is already complete.
The retained incomplete files are moved to the private evidence directory before
the next cycle. No user library files are changed.

## Independent state and playback checks

`scripts/verify_packaged_crash_recovery.py` cold-restores each of the three
recovered sessions, and the successful retry, using the package's MAME and a
byte-identical runtime protocol. Every restore reinstates dirty, idle media and
exports the same 737,280-byte disk. All 119,808 bytes across 13 sample allocations
remain exact in each 33,554,432-byte wave dump. Full wave-RAM equality is not
claimed.

Separate PCM processes verify unchanged 20,004 Hz pitch and exactly silent
note-off tails. The restored old checkpoint has peak 0.008537158; the successful
Level 63 replacement has peak 0.008404436. This distinguishes old-state recovery
from successful publication of the newer edit. The original disk and private
library input remain unchanged.

Two host-side regressions additionally inject `fsync` and replacement errors
into the archive publisher. Each preserves the previous destination and removes
its own temporary file. These are unit checks; the Windows sharing-denial case
above exercises the actual packaged writer without monkeypatching it.

## Reproduction

Use the exact package and seed identities in the validation record. From
`google-ui`, set `S760_MEDIA_PACKAGE`, a fresh `S760_MEDIA_WORK`,
`S760_INTERRUPT_SEED` to the qualified recovery archive, and `S760_QA_PYTHON` to
the QA Python executable:

```powershell
node node_modules/@playwright/test/cli.js test packaged-media.spec.ts --grep 'incomplete checkpoint' --config=playwright.packaged.config.ts --output=<private-results>
```

Then run from the repository root:

```powershell
python scripts/verify_packaged_crash_recovery.py --package <package> --browser-work <private-work>/publication --state-dir <fresh-native-work>
```

The browser harness observes successful save completion through the UI before
reading the archive. An earlier probe repeatedly opened the destination while
the retry was being published and encountered another access-denied failure;
the final test avoids that file-observer interference.

Prerequisites are the existing Windows development workstation, its desktop
runtimes, private IC15 v1.11/OS 2.24/ROBOFULL, the qualified checkpoint, Chromium,
Python for QA, and loopback access. Product-side writer and emulator code are
unchanged.

## Limits

The forced interruptions were observed at the **opened, zero-byte temporary
file** stage. They do not qualify arbitrary offsets within payload writes,
interruption during flush, `fsync` or atomic rename, physical power loss, storage
hardware failures, or recovery of work newer than the last completed checkpoint.
Windows replacement denial is a separate observed error case, not a simulated
power failure. Device audio, final WebView input, installers, clean-machine and
final release qualification remain open.
