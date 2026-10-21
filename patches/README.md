# S-760 firmware patches

These folders contain patch builders and instructions. Supply your own original
Roland firmware. Generated ROMs and disk images stay local under the ignored
`temp/work/` directory. Run commands from the repository root.

| Folder | Purpose | Status |
| --- | --- | --- |
| [boot-rom/](boot-rom/README.md) | IC15 v1.11 patch adding the selectable `GB-6 +CRT` controller mode and saved selection. Shared by both OS variants. | Native emulator verified; limited hardware confirmation described in its README. |
| [gb6/](gb6/README.md) | OS 2.24 selectable Sony GB-6 support, retaining Panel+LCD, Mouse+CRT and RC100+CRT. Includes a builder for the paired Boot ROM and OS. | Native emulator verified; limited hardware confirmation described in its README. |
| [gb6-scsi/](gb6-scsi/README.md) | GB-6 v9 plus BlueSCSI Image Library and SCSI/SDS repairs. | **Hardware testing pending; IM1 qualification incomplete.** |
| [bluescsi-v2/filename-fixes/](bluescsi-v2/filename-fixes/README.md) | Image filename fixes for BlueSCSI device firmware itself. | Separate device firmware patch; follow its own build instructions. |

## Requirements

Use Python with the firmware disassembler:

```powershell
python -m pip install pypcode
```

The S-760 builders require unmodified originals and verify their sizes and hashes:

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `roms/BOOT/Roland_S-760_v1.11.BIN` | 32,768 | `ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6` |
| `S760224.IMG` | 1,474,560 | `3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd` |

Change the input arguments if your originals are elsewhere, for example
`--os-input roms/System/S760224.IMG`. Keep originals as recovery copies and use
fresh output paths for each build.

## Boot ROM only

```powershell
python patches/boot-rom/patch_gb6_boot_rom.py --input roms/BOOT/Roland_S-760_v1.11.BIN --output temp/work/patches/boot-rom/Roland_S-760_v1.11.GB6.BIN
```

This needs only the original Boot ROM and produces the shared GB-6 Boot ROM.
Use a matching selectable GB-6 OS below for runtime controller support.
The command builds a file; it does not program an EPROM.

## GB-6 Boot ROM and OS together

```powershell
python patches/gb6/build.py --boot-input roms/BOOT/Roland_S-760_v1.11.BIN --os-input S760224.IMG --out-dir temp/work/patches/gb6 --profile v9
```

Outputs: `Roland_S-760_v1.11.GB6.BIN` and `S760224.GB6-SELECTABLE-v9.IMG`.
Profile v9 uses X4/Y4 movement gain. The bundle also documents the earlier v8
profile and legacy OS-only experiments.

## GB-6 + SCSI hardware-test candidate

```powershell
python patches/gb6-scsi/build.py --boot-input roms/BOOT/Roland_S-760_v1.11.BIN --os-input S760224.IMG --out-dir temp/work/patches/gb6-scsi
```

The output directory must not already exist. Outputs include
`S760224-BS-IM1.IMG`, the same `Roland_S-760_v1.11.GB6.BIN`, checksums,
a manifest and an example BlueSCSI configuration.

If the GB-6 Boot ROM is already installed, keep it when switching between these
two OS variants. Follow the [hardware test guide](../docs/project/bluescsi-hardware-test-guide.md)
for the combined candidate; emulator validation does not complete hardware
qualification. Each bundle README records its expected output hashes.

The old `scripts/build_gb6_combo.py` and corresponding `scripts/patch_*.py`
commands remain compatibility entry points to these implementations.
