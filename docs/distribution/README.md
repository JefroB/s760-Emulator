# Distribution review inputs

This directory retains verbatim upstream notices, byte-identity provenance and
the exact reviewed Windows standalone file manifest. See
[the qualification](../testing/distribution-qualification.md) for the component decisions,
source rebuild, runtime acceptance and limits.

The [2026-10-17 source-built standalone review](../testing/standalone-release-promotion.md)
adds a second exact dated tree, GPLv3 ASIO source delivery and a clean rebuild of
the engine and audio bridge. Historical manifests continue to identify only
their own bytes. Clean-machine acceptance remains a separate gate.

Downloadable frozen candidates live in [GitHub prerelease assets](https://github.com/JefroB/s760-Emulator/releases/tag/standalone-acceptance-2026-10-17).
The tracked [artifact index and checksum](../../artifacts/standalone/README.md)
identify the clean-machine kit; local ZIPs belong in `artifacts/standalone/`,
outside private research/findings directories.

For a new candidate:

1. Build into a fresh output directory with `scripts/build_standalone.ps1`.
   Preserve its PyInstaller COLLECT/PYZ/PKG records. The input inventory rejects
   binary drift and flags changed reviewed vendor binaries.
2. Create a fresh native source snapshot:
   `python scripts/s760_native_source_bundle.py --output <new-source.zip> --extract <new-source-directory>`.
   Rebuild the extracted Visual Studio project using the qualification's recipe.
3. Package that rebuilt engine. Verify it using
   `python scripts/verify_native_runtime.py --executable <rebuilt-mames760.exe> --state-dir <fresh-state-directory> --pull-render --scheduled-midi`
   with authorized local firmware/test media, then run packaged desktop acceptance.
4. Review actual frozen, bootstrap, native and Vite module inputs and notices.
   Retain full upstream text and resolve nested vendor obligations. A package
   metadata license string alone is insufficient. Recheck any changed versions.
5. Deliver the tested native source archive and project host sources alongside
   the binary, with firmware setup and prerequisites. Scan the archives themselves,
   not just the outer directory. Do not include firmware or test recordings.
6. Record evidence and deliberately review a new exact file manifest. The current
   dated manifest qualifies one artifact only; copying its `decision` field into
   a new package report has no effect. Run `s760_package_audit.py --require-release`
   against the completed tree before archiving or publishing it.

The artifact manifest lives in the repository, not inside the package it
authorizes. It records SHA-256 and byte count for each file except the root
generated PACKAGE-AUDIT.json report. That report is regenerated from actual
files. Preserve source/notices when distributing the package; publication itself
is a separate action.
