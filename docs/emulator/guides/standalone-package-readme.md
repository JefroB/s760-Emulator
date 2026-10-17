# S760Studio Windows development package

Keep the entire extracted folder together. Run `S760Studio.exe` from a writable
folder. Python, Node, CMake and the source checkout are not needed to run this
package. This is a development artifact; final installation and clean-machine
release qualification remain open.

For a browser-downloaded ZIP, verify its published checksum, right-click the ZIP
→ Properties → Unblock → Apply **before extracting with File Explorer**. If the
desktop fails with `Failed to resolve Python.Runtime.Loader.Initialize`, keep
the failed extraction as evidence, unblock the original ZIP and extract into a
fresh folder. Windows may otherwise block the packaged .NET assemblies. Python
does not need to be installed separately.

## Prerequisites and your files

Use Windows x64 with the Microsoft Visual C++ v14 x64 runtime and Microsoft Edge
WebView2 Runtime installed. Audio devices and
ASIO drivers, if selected, must be installed separately. The dependency inventory
and [system prerequisites](SYSTEM-PREREQUISITES.json) identify this particular
build. The package contains no Roland firmware, sample libraries or recordings
and does not download them.

Supply these local files using paths in Configuration:

| Setting | Tested input |
| --- | --- |
| Boot ROM (32KB) | Raw IC15 boot EPROM version1.11,32768 bytes |
| System disk (1.44MB) | Raw OS2.24 floppy image,1474560 bytes |
| Media directory | An existing folder containing your raw720KB or1.44MB sample floppy images (`.img` or `.dsk`) |

The CPU is IC1 and the boot EPROM is IC15. Tested SHA-256 identities:

```text
IC15v1.11: ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6
OS2.24:    3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd
```

Hashes identify the tested files; users supply appropriately authorized copies.
Keep firmware and writable session data outside the package so replacing the
application folder does not replace your files.

## First launch

For a persistent private profile, open PowerShell in the extracted folder and run
the following command, substituting your actual paths. No development tools are
required; PowerShell is included with Windows.

```powershell
.\S760Studio.exe --state-dir "$env:LOCALAPPDATA/S760Studio/MySampler" --boot-rom "D:/My S760/boot.bin" --system-disk "D:/My S760/S760224.IMG" --media-dir "D:/My S760/disks"
```

Use a distinct writable state directory for each simultaneous instance. To reuse
saved settings, launch with the same `--state-dir`; explicit firmware/media
arguments override saved paths. Double-clicking uses a package-relative default
profile, so the application folder must be writable for that launch method.

If paths are missing, Configuration remains available. Enter **Boot ROM (32KB)**,
**System disk (1.44MB)** and **Media directory**. Choose Wave memory8,16 or32MB
(default32MB). Confirm that applying replaces current sampler memory, then apply
settings. The sampler reboots. On later launches the same profile remembers its
settings. The gear opens Configuration; Cancel settings returns to the rack.

## Load and play

1. Use Gotek Up/Down to select a sample image, then Gotek Select to insert it.
2. On the original CRT, open Disk → Load. Select the performance row, execute
   Load and wait for the Now Working dialog to finish.
3. Return to Perform → Perform Play. Select MIDI input in Configuration, or enable
   the optional on-screen keyboard. Firmware Disk/Load and Sampling screens mute
   ordinary performance playback; return to Perform Play to audition.
4. Enable audio output in Configuration and select the output backend/device.
   Output Level controls software output gain; it is independent of Input Level.

The CRT mouse and rack buttons control the original firmware. Move over a field
and turn VALUE (drag, wheel or arrow keys) to edit it. Save before applying runtime
settings: applying them reboots and loses unsaved memory.

## Recording

Input defaults to No audio input. The qualified recording profile is44.1kHz
stereo; enable an explicitly selected Windows MME input or ASIO input pair in
Configuration, confirm restart and apply. ASIO also requires its installed driver,
output pair and buffer size. Recording device refresh rediscovers changed devices.
Use the firmware Sampling screen to record, then return to Perform Play to play
the sample. Input Level changes recording gain; Output Level changes playback.
Alternate input clocks and device combinations are not qualified by this guide.

## Save disks and sessions

Firmware Disk → Save writes the private inserted disk. **Export disk** in
Configuration publishes a new image under `STATE_DIR/exports`; it does not overwrite
your library file. Copy that exported file into your media folder to select it on
a later launch. Wait for disk activity to finish before export, eject or restart.

**Save session** stores sampler memory and supported native state in
`STATE_DIR/sessions/latest.s760state`. **Restore saved session** requires the
explicit Replace current sampler memory confirmation. Save sessions separately
from saving/exporting a floppy; firmware media Save does not represent the full
machine. Checkpoints require the same build, audio profile and wave-memory size.
Migration between builds is unsupported. Keep session archives private because
they contain firmware-derived memory and samples.

Automatic recovery runs periodically and on normal close. If a prior recovery is
offered, restore it or explicitly start a new recovery history. Recovery is bounded
by its last save; changes since that save can be lost. Export disks and save a
session before deliberately restarting or replacing settings.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Window cannot open | Check WebView2 installation and keep all extracted package files together. From PowerShell, add `--browser` to use your installed browser and distinguish desktop-host failure. |
| Missing VCRUNTIME DLL at launch | Install the Microsoft Visual C++ v14 x64 runtime required by SYSTEM-PREREQUISITES.json, then launch again. |
| Sampler needs configuration | Correct existing local paths in Configuration. A boot ROM must be a raw32KB binary, not an Intel HEX text file. |
| No images in Gotek | Point Media directory at an existing folder of raw `.img`/`.dsk` files; selecting a directory does not load its contents into the sampler. |
| Unsupported image size | Use a737280- or1474560-byte raw floppy. Recognized size alone does not establish a valid Roland filesystem. |
| No sound | Finish loading and return to Perform Play, enable audio output, choose a connected output, raise Output Level and check MIDI input/channel. Check the optional keyboard first if MIDI discovery fails. |
| Audio device fails | Reconnect it, refresh the device list and use Reopen audio when offered. Export/save before a settings change that reboots the sampler. |
| Restart/eject blocked | Finish the disk operation and export unexported writes. Restart also requires the unsaved-memory confirmation. |
| Session identity/version rejected | Use the matching application build and wave-memory size. Rejection preserves the current machine; archives are not automatically migrated. |
| State directory already in use | Close the instance owning that directory or choose a different private state directory. |

For reproducible reports, retain the error text, chosen device/backend, Windows
version and hashes of this package's manifests. Do not attach firmware, sample
libraries or session archives to public reports. `--no-sound` starts muted;
`--fast` is for unthrottled testing and should not be used for musical playback.

## Package identity and scope

[Package audit](PACKAGE-AUDIT.json), [bundled inputs](BUNDLED-INPUTS.json) and
[dependency inventory](DEPENDENCY-INVENTORY.json) record this build. A successful
development audit does not grant release status. Retain the [project license](LICENSE.txt),
[MAME notices](MAME-COPYING.txt) and all `notices/` files when copying the package.
Original project code and third-party components have separate license scopes.

This guide covers the standalone floppy workflow. VST3 is a separate artifact;
native SCSI research profiles, arbitrary firmware edits, every audio device,
physical hardware fidelity and final clean-machine installation are outside this
package's qualified scope. Development packages must not be labelled final releases.
