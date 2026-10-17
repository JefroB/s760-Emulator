# User-supplied firmware and distribution policy

## What the project distributes

The project is intended to be open source on GitHub. Source releases and any
future executable packages must exclude Roland boot ROMs, Roland system disks,
third-party sample libraries, and saved sessions containing those bytes.
Users supply their own appropriately authorized firmware and media. The project
does not download or bundle them automatically.

GB-6 experiments follow the same rule: use the [source-only patcher](../../firmware/os/gb6-os-patch.md)
with an original user-supplied OS2.24. Original and patched OS images, including
compressed images/backups, remain local and must not be force-added to Git.

An independently authored replacement may be distributed with the project once
it works and its source provenance, license and distribution rights are
established. Patching, renaming, converting or embedding a Roland binary does
not make it an original replacement. No working replacement is currently
qualified by this document; the tested native boot still uses original firmware.

This policy excludes Roland binaries, not future builds of our emulator.
MAME and other dependencies retain their existing licenses and notices.
Original project-owned code now uses [BSD-3-Clause](../../../LICENSE). See
[license scope and hardware-use guidance](../../project/licensing.md) and the
[runtime distribution assessment](../runtime/native-boundary-qualification.md).

## Files needed for the tested native player

Place these files relative to the repository root, or beside `S760Studio.exe`
in a development desktop package:

| File | Purpose | Tested size |
| --- | --- | --- |
| `roms/BOOT/Roland_S-760_v1.11.BIN` | IC15 boot EPROM, version 1.11; raw binary, not Intel HEX | 32,768 bytes |
| `roms/System/S760224.IMG` | OS 2.24 raw system floppy image | 1,474,560 bytes |
| `roms/FDD/<your-sample-disk>.IMG` | Optional raw sample floppy for loading sounds | 737,280 or 1,474,560 bytes |

The boot EPROM is **IC15**; IC20 is the CPU. Firmware is not supplied by this
repository. Obtain it separately with the necessary rights; this guide does not
assert that hardware ownership or availability on a download site establishes
permission. No specific download source is endorsed here.

The currently tested firmware SHA-256 values are:

```text
Roland_S-760_v1.11.BIN
ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6

S760224.IMG
3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd
```

Verify local identity in PowerShell:

```powershell
Get-FileHash ./roms/BOOT/Roland_S-760_v1.11.BIN -Algorithm SHA256
Get-FileHash ./roms/System/S760224.IMG -Algorithm SHA256
```

Hashes identify the tested files; they are not redistribution permission. Other
versions are not established as compatible by these checks.

## Use files outside the project

The standalone accepts explicit paths, so firmware need not be copied into the
checkout or package:

```powershell
python scripts/s760_standalone.py --boot-rom "D:/My S760/boot.bin" --system-disk "D:/My S760/S760224.IMG" --media-dir "D:/My S760/disks" --state-dir "D:/My S760/session"
```

For a packaged development build, replace `python scripts/s760_standalone.py`
with `./S760Studio.exe`. Use a separate writable state directory for each running
instance. The state directory can contain firmware-derived machine checkpoints
and sample data; keep it private. See the [standalone instructions](standalone-player.md)
for building, selecting a sample disk and using the firmware Disk/Load menu.

Native VST3 development currently uses explicit environment variables rather
than these CLI options; see [plugin configuration](native-plugin-selection.md).
The standalone floppy picker does not imply working native SCSI mounting or
complete SCSI session recall.

For the native Windows VST3, use the [persistent plugin configuration and startup diagnostic workflow](native-plugin-configuration.md). Settings contain paths, not firmware bytes.
