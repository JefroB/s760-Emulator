# Historical standalone and VST3 static artifact audit

Audit date: 2026-10-17. Scope corrected for BUG-104.

This is a retained static inspection of dated local standalone and VST3 files.
It does **not** qualify clean-machine installation, a final release, or execution
in any of the proposed DAW hosts. The [machine-readable record](../condensed/validation/final-release-artifacts-qualification-2026-10-17.json)
preserves the inspected identities and incomplete acceptance flags.

## What was inspected

The historical standalone tree contained 572 files. The checker inspected
Windows x64 PE headers, package filenames/extensions, selected notices and
configuration contracts. It also inspected the local `Roland_S760.vst3` PE
artifact. Passing these checks establishes only their stated static properties.

Filename/extension checks and literal hash-reference checks do not establish
that compiled binaries contain no embedded proprietary assets. The static
checker does not establish that accompanying source rebuilds those binaries.
Source correspondence and private-asset exclusion need their own evidence.

The historical standalone is superseded by the source/dependency-qualified
611-file archive described in [standalone release promotion](standalone-release-promotion.md).
That report records the rebuilt ASIO GPLv3 dependency, corresponding source,
exact artifact identities and repeated workstation workflows. Its qualification
does not transfer to this older package or to a VST3 release.

## Proposed prerequisites and host matrix

The proposed Windows x64 prerequisites include the Microsoft VC++ runtime,
WebView2 runtime and suitable audio/MIDI drivers. The acceptance handoff records
discovery, installation/remediation and workflow observations separately.
Removing development-tool paths on this workstation does not establish a clean
Windows installation.

The static checker lists SoundCheck, REAPER, Ableton Live, Cubase and Bitwig as
proposed host rows. Every observation in this audit remains `NOT_RUN`; no row is
qualified by file inspection. Existing real SoundCheck acceptance has its own
[project evidence](soundcheck-projects.md) and does not qualify the other hosts.

Distribution uses an extracted standalone folder or a VST3 copied to an
appropriate host search path. These installation instructions remain proposals
until exercised on the supported target environment. No release tag or broader
compatibility claim follows from this audit.

## Remaining acceptance

The [clean-machine handoff](standalone-clean-machine-handoff.md) remains
incomplete because no separate Windows machine or VM is available. Final VST3
artifact/source/prerequisite qualification and observations in additional DAW
hosts remain separate work. Keep the roadmap's release gates open until actual
observations are recorded.

## Reproduction

Run the static checker into a new output record to preserve historical evidence:

```powershell
python scripts/verify_release_artifacts.py --out temp/release-artifact-static-audit.json
python -m pytest tests/test_release_artifacts.py tests/test_package_audit.py tests/test_vst3_configuration.py
```

A passing static check is not product or clean-machine acceptance.
