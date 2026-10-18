# Sony GB-6 firmware patches (Boot ROM v1.11 + OS 2.24)

> **Hardware testing status:** The selectable 4th controller option (`GB-6 +CRT`, mode `3`) across the modified IC15 Boot ROM v1.11 and OS 2.24 System Disk has been verified end-to-end in the native MAME emulator, **but has not been tested yet on real S-760 hardware.** Always keep your original IC15 Boot EPROM and original OS 2.24 floppy/Gotek image untouched as a rollback baseline.

The repository includes reproducible Python patchers, not Roland firmware or patched
disk/ROM binaries. Supply your own original S-760 firmware files:

- **IC15 Boot ROM v1.11 (`Roland_S-760_v1.11.BIN`)**: 32,768 bytes (`0x8000`), SHA-256 `ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6`.
- **OS 2.24 System Disk (`S760224.IMG`)**: 1,474,560 bytes (`0x168000`), SHA-256 `3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd`.

## 1. Selectable 4th Controller (`GB-6 +CRT`, Mode `3`) — Boot ROM + OS 2.24

Preserves `Panel+LCD` (`0`), `Mouse+CRT` (`1`) and `RC100+CRT` (`2`), and adds `GB-6 +CRT` (`3`) as a selectable 4th option in both the IC15 Power-On `Mode` Setup Menu and the OS 2.24 `System -> System PRM -> Page 2` menu:

```powershell
# Build and verify both modified files at once (v9 = X*4/Y*4 default; v8 = X*8/Y*4)
python scripts/build_gb6_combo.py --boot-input roms/BOOT/Roland_S-760_v1.11.BIN --os-input S760224.IMG --out-dir temp/work/gb6_combo --profile v9

# Or patch the Boot ROM and OS Disk individually:
python scripts/patch_gb6_boot_rom.py --input roms/BOOT/Roland_S-760_v1.11.BIN --output temp/work/gb6_combo/Roland_S-760_v1.11.GB6.BIN
python scripts/patch_gb6_os_disk.py --input S760224.IMG --output temp/work/gb6_combo/S760224.GB6-SELECTABLE-v9.IMG --profile v9
```

| Artifact | Profile / Role | Output SHA-256 | Status |
| --- | --- | --- | --- |
| `Roland_S-760_v1.11.GB6.BIN` | IC15 Boot ROM v1.11 (`GB-6 +CRT`, mode `3`, 13 bytes changed) | `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb` | Verified in emulator; **not yet tested on real hardware** |
| `S760224.GB6-SELECTABLE-v9.IMG` | OS 2.24 4-option selectable (`X*4, Y*4`, 220 bytes changed) | `0a15c81ad6747803160815393f2c2c207f15861bd5671d349ebde4aa3929af15` | Verified in emulator; **not yet tested on real hardware** |
| `S760224.GB6-SELECTABLE-v8.IMG` | OS 2.24 4-option selectable (`X*8, Y*4`, 220 bytes changed) | `6e32e3143dd06b2d93bdacaf765fd2ba68edeb2b64916dbf0d528262573b7403` | Verified in emulator; **not yet tested on real hardware** |

To test the Sony GB-6 trackball in the native emulator without Lua bus taps, pass a config file via `S760_CONFIG=s760_config.json` (`{"pointing_device": "gb6"}` or `"auto"`) or set `S760_POINTING_DEVICE=gb6`. Run `python -m pytest tests/test_gb6_combo.py` to run the automated disassembly and emulator verification suite.

---

## 2. Legacy OS-Only `Mouse+CRT` Replacement Patch (`scripts/patch_gb6_os.py`)

The standalone OS-only patcher needs only Python's standard library. It verifies the entire input,
keeps the original untouched, refuses existing output files, and checks the
generated image against the recorded experiment hash.

```powershell
New-Item -ItemType Directory -Force temp/work/gb6
python scripts/patch_gb6_os.py --input roms/System/S760224.IMG --output temp/work/gb6/S760224.GB6-v9.IMG --profile v9
```

| Profile | Gain before stock scaling | Output SHA-256 | Evidence |
| --- | --- | --- | --- |
| v8 | X8/Y4 | `cf29f7fdf75a3a672eefdd34d52f66aa25a6624632a85d52c0500d84223afead` | User confirmed vertical row selection after mechanical repair |
| v9 (default) | X4/Y4 | `c611e7156c9069dc632bcfd8e4d20a52da70ed2528112f29fe87258803f42deb` | Balanced sensitivity requested by user; hardware acceptance pending |

Use `--profile v8` and a distinct output filename to reproduce the preceding
experiment. Generated images and firmware backups stay local and ignored. Do not
force-add them or publish archives containing them. Keep the original disk and
boot EPROM as recovery copies. This legacy patch does not modify the boot EPROM.

The legacy replacement occupies file `[0x18BB5,0x18C11)` and writes `RET` at `0x18C2D`
to bypass the disconnected-mouse heuristic. It replaces the Mouse+CRT movement
decoder; select Mouse+CRT on the device. Original button and short settling
helpers remain. See the [controller plan](../../project/gb6-controller-plan.md) for background.

The experimental protocol reads X with pin8 low and Y with pin8 high, before
the edge clearing the respective counter. It subtracts8 from offset-binary
nibbles and leaves selection low between polls. The patch preserves the earlier
negative-endpoint clamp without claiming it was necessary. Starting with select
high can discard Y once; buttons and broader hardware behavior need retesting.
The user's earlier sticking problem was resolved by reseating an internal wheel,
not established as a firmware defect.

Protocol research used the independently implemented
[openMSX trackball model](https://github.com/openMSX/openMSX/blob/master/src/input/Trackball.cc),
which cites related Sony GB-7 material and discloses incomplete hardware
verification. The decoded-instruction/peripheral tests cover all X/Y nibble
combinations, button bits and initial selection states; they do not establish
physical fidelity. Run `python -m pytest tests/test_gb6_os_patch.py`; optional
`pypcode` enables the decoded-instruction matrix, and local firmware enables
byte-exact image reproduction checks. No firmware is required for guard tests.

[Tooling validation and image-exclusion review](../../condensed/validation/gb6-patch-tooling-2026-10-14.json).
