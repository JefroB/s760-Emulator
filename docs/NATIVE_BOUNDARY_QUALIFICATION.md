# Native runtime boundary qualification

Historical qualification date: 2026-10-11. That decision was **GO for local development of
the VST3 adapter; NO-GO for public binary distribution**. This records the
historical boundary assessment. The Windows standalone distribution profile has
subsequently passed its [separate qualification](DISTRIBUTION_QUALIFICATION.md),
and bounded full-state/SCSI snapshots are complete. Native input and actual
DAW/editor acceptance remain open.

License update, 2026-10-11: the owner clarified that unrestricted downstream
reuse is welcome and warranty/liability protection is desired. Original
project-owned code now has a standard [BSD-3-Clause license](../LICENSE).
This resolves the missing license choice/file, not contributor provenance,
dependency compatibility or corresponding-source delivery. See
[scope and limitations](LICENSING.md). Historical observations below describe
the pre-license package audit; its recorded artifacts are not retrospectively
relabeled as qualified releases.

## Decision and scope

| Area | Decision | Evidence and limits |
| --- | --- | --- |
| Process ownership | Pass for Windows native adapter | Abrupt parent exit kills its owned MAME child; the same state directory can reopen and boot/load/play. Independent instances and shared-directory rejection are covered by the adapter harness. |
| Crash recovery | Pass for explicit standalone saved floppy sessions | Recovery starts a new child, restores the saved patch, plays/releases it and retains the archive. No recovery of edits after the last save; plugin project recall is still a separate objective. |
| Host-clocked audio | Pass for the documented development profile | Exported native module at 44.1/48/96 kHz, varied 64–1024-frame callbacks, exact offline-reference PCM and measured deadlines. Approximately 279 ms software latency; no actual DAW/device latency or complete MIDI-controller claim. |
| Project-owned licensing | Complete | BSD-3-Clause selected, standard text installed, firmware exclusions and third-party scope documented. |
| Binary distribution | Qualified for the exact Windows standalone artifact | See [source rebuild, component review and integrity gate](DISTRIBUTION_QUALIFICATION.md). Historical observations below are preserved; future builds require fresh review. |

See the [machine-readable qualification record](condensed/validation/native-boundary-2026-10-11.json)
for commands, hashes and measured results. This is a repository module harness
using the project's current VST3 definitions, not certification against an
external SDK or a real DAW. The process boundary is an engineering choice; it
does not itself establish license compatibility.

## Historical source and package audit (before distribution qualification)

The owner's distribution policy is now explicit: publish the project on GitHub,
exclude Roland binaries from both source and executable packages, and document
user-supplied firmware paths. Independently authored working replacements may
be included after provenance/licensing checks. This does not clear third-party
packaging obligations. See
[firmware setup and policy](FIRMWARE_SETUP.md).

Observed directly in this checkout:

- `mame-source/COPYING` identifies MAME as a whole as GPL version 2 and points
  to full texts in `docs/legal`. The S-760 driver header separately identifies
  BSD-3-Clause. The driver header does not license the whole bundled engine.
- No root `LICENSE` exists. The former README badge and blanket BSD claim
  incorrectly implied a project-wide license file. They have been corrected;
  this work does not choose a license or change contributors' grants.
- The old desktop builder copied `COPYING` but omitted all eight full MAME
  license texts. It now copies both the attribution and complete legal directory.
- The package includes Python/pywebview/pythonnet and other components, React
  assets, native DLLs, MAME plugins and the native executable. The audit collects
  available Python and npm notices and versions as a **build-environment
  inventory**, not a complete attribution or compatibility analysis of embedded
  DLLs. Windows/WebView2 and redistributable terms still need release review.
- A binary hash plus a Git revision is not verified corresponding-source
  delivery. Modified MAME and build inputs must be captured, rebuilt and made
  available through the chosen release process before that gate can pass.

Public release remains blocked until the owner establishes project license
scope, the actual bundled components and redistribution terms are reviewed,
and corresponding source/build delivery is verified. These are release tasks;
no license was assigned automatically and nothing was published by this work.

## Historical development gate (superseded for the reviewed artifact)

`scripts/build_standalone.ps1` invokes `scripts/s760_package_audit.py` after
assembly. It copies notices, writes `DEPENDENCY-INVENTORY.json`, marks the output
`DEVELOPMENT-ONLY.txt`, and emits `PACKAGE-AUDIT.json` with SHA-256 and size for
each file. Missing/changed MAME attribution, full licenses, native binary or Lua
adapter fail the development audit. Forbidden media/session extensions and
byte-identical copies of local ROM/media fixtures also fail, including a renamed
fixture. This is not a general detector for transformed private content.

The PowerShell `-Release` option fails before building. The audit CLI's
`--require-release` also fails; an edited JSON result cannot authorize a release.
These gates deliberately remain closed pending the release review above.
Passing unit tests or a development audit does not unlock them.

```powershell
# Existing assembled development package: retain notices and audit it.
python scripts/s760_package_audit.py --package <package-directory> --prepare

# Fresh private output directory required; crashes only its own test parent.
python scripts/verify_native_boundary.py --work docs/ic20-hle-findings/chatGPT-work/boundary-check
python scripts/verify_native_checkpoint.py --standalone-session --state-dir docs/ic20-hle-findings/chatGPT-work/session-check
```

The native verifier requires local original firmware, ROBOFULL and built Release
executables. It checks parent-crash cleanup and reopening, then runs the actual
exported module for 60 seconds at each supported host rate. Do not run competing
heavy workloads during the paced timing measurement.
