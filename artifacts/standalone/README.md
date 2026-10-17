# Standalone acceptance artifacts

Download the [2026-10-17 qualification prerelease](https://github.com/JefroB/s760-Emulator/releases/tag/standalone-acceptance-2026-10-17)
or its [complete acceptance ZIP](https://github.com/JefroB/s760-Emulator/releases/download/standalone-acceptance-2026-10-17/s760-standalone-acceptance-2026-10-17.zip).
Keep downloaded ZIPs in this directory; binaries are git-ignored because GitHub
release assets deliver them independently of the source checkout.

The ZIP is 287,210,283 bytes. Verify it against [SHA256SUMS](SHA256SUMS):

```powershell
Get-FileHash .\s760-standalone-acceptance-2026-10-17.zip -Algorithm SHA256
```

It contains the frozen standalone, complete corresponding-source archives,
notices, package manifest and PowerShell acceptance scripts. It excludes Roland
firmware and test media; supply your own private copies. Renaming/relocating the
outer ZIP has not changed its bytes or the frozen package inside.

Extract into a writable folder with spaces and follow the
[clean-machine handoff](../../docs/testing/standalone-clean-machine-handoff.md).
Two full workstation runs passed. Separate Windows installation/prerequisite
and workflow acceptance remains pending. This prerelease is a qualification
candidate, not a completed clean-machine or VST3 release qualification.
