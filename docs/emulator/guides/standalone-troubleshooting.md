# Standalone troubleshooting

| Problem | Action |
| --- | --- |
| `Failed to resolve Python.Runtime.Loader.Initialize` | Verify the ZIP checksum, unblock the original downloaded ZIP in Properties, and extract again into a fresh folder. Keep the original failure evidence. Python does not need to be installed. |
| Missing VC runtime DLL | Install the Windows x64 VC++ runtime listed in `SYSTEM-PREREQUISITES.json`. |
| No desktop window | Check WebView2 is installed. Keep the extracted files together. `--browser` uses your browser to help distinguish a desktop-host problem. |
| Firmware not found | Check Configuration or the default `roms/BOOT/` and `roms/System/` folders. Boot ROM must be raw 32KB; OS must be raw 1.44MB IMG or OUT. If several alternate files are present, select the intended one explicitly. |
| Empty Gotek list | Put your sample `.img`/`.dsk` files in `roms/FDD/` or change Media directory. No sample media is bundled. |
| No sound | Select and enable output audio, check OUTPUT LEVEL and MIDI selection, load a performance, and return from Disk/Sampling to Perform Play. |
| Cannot quit normally | Use Quit application or X. A recovery failure keeps the app open. Keep working to save/export, or acknowledge the loss warning and choose Quit without saving. |
| Old findings folder appears in an older package | Earlier versions used it as a private runtime profile and staged your supplied OS there. New versions use Local AppData. Preserve any old sessions/recovery before removing the old installation. |
| State directory in use | Close the instance using it, or launch another instance with a different `--state-dir`. |
| Session cannot restore | Match the recorded build, firmware, audio/wave-memory profile and external SCSI backing files. Read the error before replacing anything. |

Default private state is `%LOCALAPPDATA%\S760Studio\default`. For another profile:

```powershell
.\S760Studio.exe --state-dir 'C:\My S760 profile'
```

When reporting a problem, include the package version/checksum, Windows and
device details, exact error, reproduction steps and relevant logs from the
profile. Keep firmware, sample media and session archives private.

[Quick Start](quick-start.md) · [User guide](user-guide.md) · [Controls](controls.md)
