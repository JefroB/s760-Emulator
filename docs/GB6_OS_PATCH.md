# Sony GB-6 experimental OS patch

The repository includes a reproducible patcher, not Roland firmware or patched
disk images. Supply your own original S-760 OS2.24 image:

- Size: 1,474,560 bytes (`0x168000`).
- SHA-256: `3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd`.

The patcher needs only Python's standard library. It verifies the entire input,
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
boot EPROM as recovery copies. This patch does not modify the boot EPROM.

The replacement occupies file `[0x18BB5,0x18C11)` and writes `RET` at `0x18C2D`
to bypass the disconnected-mouse heuristic. It replaces the Mouse+CRT movement
decoder; select Mouse+CRT on the device. Original button and short settling
helpers remain. Mouse and GB-6 are not simultaneously selectable. A persistent
fourth controller option and preserved mouse dispatch are deferred in the
[controller plan](../GB6_CONTROLLER_PLAN.md).

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

[Tooling validation and image-exclusion review](condensed/validation/gb6-patch-tooling-2026-10-14.json).
