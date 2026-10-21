# S760Studio — Roland S-760 emulator

S760Studio emulates the Roland S-760 sampler on Windows, using the original boot ROM and operating system. Load sample disks, play sounds over MIDI, and operate the sampler through its original screen and front-panel controls. It can also run as a VST3 instrument with a matching plugin build.

![S760Studio emulator with its original sampler display and on-screen keyboard](docs/images/standalone-keyboard.png)

You must supply your own IC15 boot ROM, S-760 OS disk image and sample media. These are not included in the download.

## Downloads

- **[Download the Windows standalone ZIP](https://github.com/JefroB/s760-Emulator/releases/download/standalone-acceptance-2026-10-17-v4/s760-standalone-acceptance-2026-10-17-v4.zip)**
- **[Download the PowerShell installer helper](https://github.com/JefroB/s760-Emulator/releases/download/standalone-acceptance-2026-10-17-v4/install-acceptance-v4.ps1)**
- [Release page and checksums](https://github.com/JefroB/s760-Emulator/releases/tag/standalone-acceptance-2026-10-17-v4)

The current download is a development prerelease. You do not need the source code, Python or Node to run it. The ZIP contains the standalone application; it does not include the VST3 plugin.

## Install the standalone

Use Windows 10 or 11, 64-bit, with the [Microsoft Visual C++ v14 Redistributable (x64)](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) and [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) installed. The desktop host also uses [.NET Framework](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48).

1. Download the ZIP above. In File Explorer, right-click it, choose **Properties → Unblock → Apply**, then extract it into a writable folder.
2. Find the `S760Studio` folder inside the extraction. Keep all its files and subfolders together.
3. Add your firmware and media as described below, then run **`S760Studio.exe`**.

Alternatively, download the ZIP and installer helper into the same folder. Open PowerShell there and run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-acceptance-v4.ps1 -Destination "$env:USERPROFILE\S760"
```

Choose a new destination folder. The helper verifies the download, unblocks it and extracts the application; it does not install Windows prerequisites or firmware. It prints the path to `S760Studio.exe` when finished.

## Add your boot ROM, OS and sample disks

The following paths are relative to the folder containing **`S760Studio.exe`**. The download includes empty `roms` folders ready for your files.

| What you supply | Where to put it |
| --- | --- |
| **IC15 boot ROM v1.11**, raw 32 KB binary (32,768 bytes) | `roms/BOOT/Roland_S-760_v1.11.BIN` |
| **S-760 OS 2.24 system disk**, raw 1.44 MB image (1,474,560 bytes) | `roms/System/S760224.IMG` |
| Sample floppy images, raw 720 KB or 1.44 MB `.IMG` / `.DSK` files | `roms/FDD/` — keep your own filenames |
| SCSI hard-disk image, raw `.IMG` with 512-byte sectors, at SCSI ID 0 | `roms/SCSI/HD0.img` |
| SCSI CD-ROM image, `.ISO` with 2,048-byte sectors, at SCSI ID 1 | `roms/SCSI/CD1.iso` |

The boot ROM must be a raw binary, not an Intel HEX file. The OS can also be named `S760224.OUT`; a raw Roland `.OUT` system disk needs no conversion. The boot ROM and OS disk are both required to start the sampler.

You can keep your firmware elsewhere and select its paths using the **Configuration gear → Firmware & media**. Saved settings take precedence over automatic folder discovery.

For SCSI media, use the filenames above and add the images **before starting the application**. Load their contents through the sampler's **Disk → Load** screen, selecting the appropriate SCSI device. Images must contain media the S-760 understands; renaming an arbitrary file to `.IMG` or `.ISO` does not convert it. Existing profiles retain private SCSI copies, so replacing a library image does not overwrite a profile's existing disk.

## Load a sound and play

1. Run `S760Studio.exe` and wait for the sampler to boot. If Configuration opens, select your boot ROM and system disk, then apply the settings.
2. Open the **Configuration gear**, enable audio output, choose your output device and select your MIDI input. You can also enable the on-screen keyboard.
3. For a sample floppy, use the **Gotek Up/Down** controls to choose an image and **Select** to insert it.
4. On the sampler screen, open **Disk → Load**, select a volume or performance and execute **Load**. Wait for loading to finish.
5. Return to **Perform → Perform Play**, then play your MIDI keyboard or the on-screen keys. Disk and Sampling screens can mute playback.

Use the mouse on the CRT and the rack buttons to operate the original menus. The **VALUE** control changes the selected field; **OUTPUT LEVEL** controls playback volume.

Use the sampler's **Disk → Save** to save edits to its private disk, then **Export disk** in Configuration to create an image you can keep. **Save session** saves a machine checkpoint separately. Export disks before updating the application; session checkpoints require the same build. Settings, recovery and private runtime files normally live under `%LOCALAPPDATA%\S760Studio\default`.

## Install and use the VST3

There is **no prebuilt VST3 download in the current release**. These instructions apply if you have a matching Windows VST3 development build.

1. Place **`Roland_S760.vst3`** and its matching runtime/editor files in `C:\Program Files\Common Files\VST3\S760\`. Keep the `mame-source`, `scripts` and `google-ui` folders beside the plugin, with their original contents. The `.vst3` file alone is not a complete installation.
2. Restart or rescan plugins in your 64-bit DAW, then add the S-760 instrument to a track.
3. Open the plugin editor's **Configuration gear**. Select the installation folder, a writable runtime-state folder, your IC15 boot ROM, OS disk and sample-media folder. Choose **Save plugin settings**, then remove and reload the plugin to apply them. A new, unconfigured instance opens this setup screen automatically.
4. Route MIDI to the instrument track and enable its stereo audio output. Audio and MIDI device selection is handled by your DAW.

The plugin needs the same user-supplied firmware as the standalone. Its settings are stored separately in `%LOCALAPPDATA%\S760\plugin-settings.json`.
