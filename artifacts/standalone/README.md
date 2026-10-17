# Standalone acceptance artifacts

Download the [2026-10-17 qualification prerelease](https://github.com/JefroB/s760-Emulator/releases/tag/standalone-acceptance-2026-10-17-v2)
or its [complete acceptance ZIP](https://github.com/JefroB/s760-Emulator/releases/download/standalone-acceptance-2026-10-17-v2/s760-standalone-acceptance-2026-10-17-v2.zip).
Keep downloaded ZIPs in this directory; binaries are git-ignored because GitHub
release assets deliver them independently of the source checkout.

The ZIP is 287,293,134 bytes. Verify it against [v2 checksum](s760-standalone-acceptance-2026-10-17-v2.zip.sha256):

```powershell
Get-FileHash .\s760-standalone-acceptance-2026-10-17-v2.zip -Algorithm SHA256
```

It contains the frozen standalone, complete corresponding-source archives,
notices, package manifest and PowerShell acceptance scripts. It excludes Roland
firmware and test media; supply your own private copies. The original v1 ZIP remains available unchanged in the
[previous prerelease](https://github.com/JefroB/s760-Emulator/releases/tag/standalone-acceptance-2026-10-17).
V2 rebuilds the host and preserves empty BOOT/System/FDD/SCSI media directories.

Extract into a writable folder with spaces and follow the
[clean-machine handoff](../../docs/testing/standalone-clean-machine-handoff.md).
The user accepted the prior kit's clean-machine launch/setup and waived full
media workflows. The v2 host separately passes workstation OUT boot and native
regression. See [accepted scope](../../docs/testing/clean-machine-acceptance-2026-10-17.md)
and [v2 verification](../../docs/testing/standalone-media-defaults.md). VST3 and
final product release qualification remain separate.

## Before extracting a browser download

After verifying the ZIP checksum, right-click the ZIP in File Explorer, choose
Properties, check **Unblock**, and Apply. Then extract into a fresh folder.
Otherwise Windows may mark the extracted .NET assemblies as internet downloads,
causing `Failed to resolve Python.Runtime.Loader.Initialize` before the UI opens.
If already extracted, keep that failed folder as evidence and extract again
after unblocking the original ZIP. Installing Python is not required.

Alternatively, download [install-acceptance-v2.ps1](https://github.com/JefroB/s760-Emulator/releases/download/standalone-acceptance-2026-10-17-v2/install-acceptance-v2.ps1)
beside the ZIP and run this in Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-acceptance-v2.ps1 -Destination 'C:\S760 acceptance kit'
```

The helper verifies the exact frozen ZIP hash before unblocking/extracting it,
checks every packaged file against its manifest, and preserves existing folders.
Execution policy changes apply only to this PowerShell process. The helper does
not install runtimes, firmware or drivers, or establish workflow acceptance.
The helper's own checksum is recorded in
[install-acceptance-v2.ps1.sha256](install-acceptance-v2.ps1.sha256).
