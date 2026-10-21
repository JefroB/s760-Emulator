# IC15 Boot ROM: selectable GB-6 controller

This patches the original S-760 IC15 Boot ROM v1.11 to add `GB-6 +CRT` as
controller mode 3 in the power-on setup menu, including selection persistence.
It retains the existing three controller choices. Use it with either the
[GB-6 OS](../gb6/README.md) or the [GB-6 + SCSI OS](../gb6-scsi/README.md).
Both use this exact same Boot ROM.

Run from the repository root:

```powershell
python patches/boot-rom/patch_gb6_boot_rom.py --input roms/BOOT/Roland_S-760_v1.11.BIN --output temp/work/patches/boot-rom/Roland_S-760_v1.11.GB6.BIN
```

The input must be the original 32,768-byte ROM, SHA-256
`ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6`.
The output also has 32,768 bytes, with 13 changed bytes, SHA-256
`a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb`.
Use a fresh output path and keep the original EPROM and ROM file for recovery.
The command builds the patched file; it does not program hardware.

The shared patch implementation is in `../gb6/build_gb6_combo.py`, which also
builds and disassembles the paired Boot ROM and OS. The standalone ROM command
checks the original hash and reports changed offsets and the output hash.
The old `scripts/patch_gb6_boot_rom.py` command remains compatible.

Native emulator tests cover setup, saved selection and reboot persistence.
The user confirmed front-panel GB-6 selection and persistence on hardware on
2026-10-19; broader controller and trackball hardware qualification remains
limited as described in the GB-6 bundle. See the [patch overview](../README.md)
for dependencies and the complete build commands.
