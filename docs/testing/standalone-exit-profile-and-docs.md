# Standalone exit, private profiles and user documentation — 2026-10-17

The v3 standalone addresses BUG-106, BUG-107 and BUG-108.

- **Quit:** a visible Quit application button and the native window X open the
  same layered save/discard dialog. Failed recovery saves keep the app open;
  discarding changes requires explicit acknowledgement. The WinForms callback
  returns before evaluating frontend JavaScript, avoiding a UI-thread deadlock.
- **Private data:** the default profile is `%LOCALAPPDATA%\S760Studio\default`.
  Runtime logs, recovery and privately staged firmware no longer go inside the
  installation. `--state-dir` remains available for explicit private profiles.
- **Documentation:** `docs/` includes an offline index, Quick Start, full user
  guide, controls reference and troubleshooting. All relative links are tested.
  The package audit rejects findings directories and executable content in docs.
  Build output defaults under `build/`; current QA output is under `temp/`.

## What the reported IMG was

The user confirmed the old application-relative path
`docs/ic20-hle-findings/chatGPT-work/standalone-state/roms/s760`.
The old runtime created that private profile after launch and staged the user's
selected OS image there. Inspection of the exact original and v2 ZIPs found no
outer firmware/findings entries and no such entries in their host-source ZIPs.
The corrected package has a separate manifest and archive scan.

Old profiles are left untouched because they may contain sessions and recovery.
Use an old profile explicitly with `--state-dir` if needed; the update does not
silently delete or migrate it. Do not remove an old installation until any work
you need has been preserved.

## Actual frozen-desktop checks

`scripts/verify_packaged_exit.mjs` launches fresh private copies of the frozen
application and controls its real WebView2 interface. It verifies:

1. Native window X with missing firmware opens Quit; accepting safe quit exits0.
2. Default-folder OUT boot reaches Perform Play; Save recovery and quit exits0
   and stops the owned MAME child.
3. Relaunch with existing recovery, native X, and failed safe quit keeps the app
   open. Explicit discard then exits0 and stops the owned MAME child.

All three cases use the default profile location, with Local AppData redirected
only in the test process. None writes findings/runtime data into package docs.
These are real packaged desktop tests; they do not add unobserved clean-machine
or additional DAW qualification. The prior user-approved clean-machine handoff
remains closed under its recorded scope.

[Exact artifact and validation record](../condensed/validation/standalone-exit-profile-and-docs-2026-10-17.json).
