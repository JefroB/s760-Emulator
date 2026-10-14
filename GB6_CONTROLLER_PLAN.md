# Sony GB-6 controller option — deferred plan

**Owner intent:** Add GB-6 as a selectable controller alongside the original mouse and RC-100. Investigate and implement later; this document does not authorize implementation now.

**Recorded:** 2026-10-13. **Status:** feasibility investigated; combined-controller implementation not started. Original ROM and OS image remain the recovery baseline.

**Reproduction update (2026-10-14):** The v8/v9 experiment patcher is now retained
as `scripts/patch_gb6_os.py`, with [usage and limits](docs/GB6_OS_PATCH.md).
It requires a user-supplied original OS2.24 and reproduces the recorded hashes.
Original/patched images stay ignored; the combined-controller plan remains deferred.

## Desired result

One system disk supporting these visible choices:

1. Panel+LCD
2. Mouse+CRT
3. RC-100+CRT
4. GB-6+CRT

Mouse and RC-100 must retain their original handlers. GB-6 should use the existing CRT interface with its own movement decoder. The selection should survive power cycling. Independent horizontal/vertical sensitivity is desirable, but a settings menu for sensitivity is not yet designed. Current experimental disks replace mouse decoding; they do not provide the combined choices above.

## Established firmware constraints

- Boot EPROM is **IC15, AM27C256-15D, 32 KB**, with a socket. The 28-pin chip is reported installed in a 32-pin socket; preserve its actual placement and orientation.
- Controller preference is EEPROM byte8, loaded into boot RAM `0x4CB2`. Boot ROM v1.11 at `0x5194` loads that byte, compares with2, and clears values greater than2 at `0x519E`. The no-option-board path clears the controller byte at `0x51C4`.
- Existing values are0=Panel+LCD,1=Mouse+CRT,2=RC-100+CRT. The settings EEPROM is separate from the boot EPROM.
- OS runtime controller byte is `0x2476`. Original mouse routine at file `0x18BA9` accepts mode1; RC-100 routines check mode2. Many display/UI routines distinguish zero from nonzero. A raw signature scan found868 direct zero-compare sequences referencing this byte; this is not a verified control-flow inventory.
- OS initialization copies a saved configuration byte at CPU address `0x8F7C` to `0x2476` (file `0x4995` onward). Settings code around file `0x7704E..0x7718F` references the same saved setting and runtime byte. These accesses are banked; CPU addresses alone are insufficient identifiers.
- Controller labels exist in multiple places, including file `0xBCEFA` onward, the LCD strings near `0xBD358`, and strings near `0xBEE11`. Menu descriptors, range checks, labels and persistence all need tracing; these offsets are investigation leads, not a finished patch specification.

## Two implementation approaches

### A. OS-only visible fourth choice, internally Mouse+CRT

Keep runtime/controller EEPROM value1 for both mouse and GB-6, with a separate persisted preference selecting the decoder. The OS menu could still display four choices by combining the original controller value with that preference.

Advantages: preserves existing UI/display mode assumptions and avoids changing the boot ROM. Remaining prerequisite: identify storage that is genuinely unused and survives ROM validation, EEPROM saves and resets. Do not assume an apparently spare bit or byte is safe. The boot-ROM-owned startup menu may still show Mouse+CRT unless separately addressed; a fourth option in every menu is not yet proved possible without a ROM patch.

### B. Patch boot ROM and OS for a real fourth value

Use value3 for GB-6 and update boot validation, selection menus, labels and save behavior. Also audit every relevant OS mode comparison/table so mode3 follows CRT/mouse interface behavior while dispatching to GB-6 input. Retain mode1 mouse and mode2 RC-100 behavior.

The boot validation change alone is insufficient. The startup menu's selector range and tables also need investigation, as do any ROM services used after OS loading. User has a programmer and is considering inexpensive replacement EPROMs. This makes approachB practical to explore, but no approach has been selected or implemented.

## GB-6 experiment results and protocol

Hardware trial initially gave slow/asymmetric motion and later resistance moving left/up. Direct finger rotation of the tracking shafts produced smooth cursor motion. User found a small internal wheel incorrectly seated, reseated it, and reported that it now works. **The remaining sticking was mechanical.** No missing rubber sleeves were established. BUG-058 records the history and was closed after the repair.

The exact disk revision installed during the successful repaired-device trial was not explicitly identified. Preserve that disk and identify its hash before choosing an implementation baseline; do not declare v7 specifically hardware-qualified.

Independent protocol evidence from [openMSX Trackball.cc](https://github.com/openMSX/openMSX/blob/master/src/input/Trackball.cc), based partly on Sony GB-7 service information:

- Pin8 low selectsX; high selectsY.
- Rising edge clearsX; falling edge clearsY. Read each axis before the edge that clears it.
- Motion is offset binary: nibble8 is neutral; subtract8 to obtain a signed delta. Pass signs through for this model.
- S-760 selection is driven at `F008` bit6; movement uses its low nibble. Buttons are active-low bits4/5; preserve the original helper at runtime `0x4476`.
- Leave selection low between polls: select low/readX, select high/readY, return low. Use the original short settling helper `0x446F`; long accumulation waits did not establish a working protocol.

The independent source warns that hardware behavior is not completely verified and cites a related Sony model, not a direct GB-6 capture. Earlier wiki evidence gave opposite axis polarity and led to swapped-axis patches. Hardware success after mechanical repair is stronger evidence for the user's installed configuration, not blanket proof of all GB-6 units or all earlier images.

### Experimental artifacts

All are under `temp/work/sony-gb6-20261013/`; that directory is scratch and may not be retained by version control. The essential plan is self-contained here. Keep recovery copies outside scratch before implementation.

| Artifact | Role / SHA256 |
| --- | --- |
| `S760224.original-copy.IMG` | Original recovery copy; same hash as root original below |
| `S760224.GB6-v6-lowX-highY-X8-Y8.IMG` | Corrected axis model, X8/Y8; `b8ea69e840d38701f16bed091c1e1950c2eca8f1371bd46bcf2cb88744d9e3fd` |
| `S760224.GB6-v7-negative-endpoint-X8-Y8.IMG` | Same mapping/gain, caps -64 to-63 before stock2x scaling; `b438cc9d0a2157113aa0f71974cfa51e5d176ef84cd9449f965cc53c93ae1ea4` |
| `build_gb6_v6.py`, `build_gb6_v7.py` | Reproducible experimental builders; validation JSON and disassemblies accompany them |

Root original `S760224.IMG`: SHA256 `3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd`, size1,474,560 bytes (`0x168000`). Boot binary is `roms/BOOT/Roland_S-760_v1.11.BIN`, size32,768 bytes.

V6/v7 patch movement at file `[0x18BB5,0x18C11)` and replace file `0x18C2D` withRET to bypass the original disconnected-mouse heuristic. The polling code is bank `0x50`, runtime `0x43B5..0x4411`; mapping is `file = 0x4800 + (bank << 10) + (address & 0x3FFF)`. Both ran2,048 decoded instruction/peripheral-model cases, including select-driven reads and reset edges. These are software checks, not full hardware acceptance. Original button handling remained; buttons were not explicitly qualified by the user.

V7's negative-endpoint adjustment was a diagnostic hypothesis. -128 is valid signed-byte data; no defect at that endpoint was established. The wheel repair does not prove that clamp necessary. Earlier patches, especially v3, must not be used as the baseline: v3's lookup tables incorrectly assumed instruction and data banks matched. Separate fetch/data selectors must be respected in future work.

## Replacement ROM hardware

### AT27C256R — simplest replacement

The **28-pin PDIP AT27C256R-45PU or -70PU** matches the original read pinout, 32KB capacity and5V operation. Its access time is faster than the original150ns device. It is also specifically listed as an S-760 replacement by the firmware reference below.

Program the32KB boot binary once, with no repetition, using the programmer's exact device profile. Blank-check, program and verify. Install in the original chip's same socket position/orientation; do not infer placement just from the socket notch. Keep the original chip untouched for recovery.

**AT27C256R is one-time programmable:** each changed firmware build needs another blank chip. Avoid confusing PDIP parts with PLCC/SOIC packages. Prefer emulator/software validation before burning iterative builds.

### SST39SF040 — available chips, unresolved socket adaptation

User has SST39SF040 chips and a burner. DIP39SF040 is a32-pin,512KB,5V flash device. A32KB boot image repeated16 times fills512KB and makes upper-address banks identical.

However, repetition does not establish electrical compatibility. Critical flash pins are1=A18,2=A16,3=A15,30=A17,31=/WE,32=VDD. /WE must stay inactive for read-only use and upper address inputs need defined levels. The original27C256 has pin1=VPP,14=GND,20=/CE,22=/OE,27=A14,28=VCC. Service schematic shows original VPP andVCC tied toVCC, /OE toXBRD, /CE toCS_BOOT, with A0..A14 andBD0..BD7 connected.

**Socket verification outcome:** original28-pin device connections were established from the schematic and the board drawing was inspected. All extra socket contacts, their numbering relative to the original chip placement, and their wiring were NOT conclusively resolved. Do not treat39SF040 as a drop-in replacement. A physical power-off continuity check and a complete pin-by-pin adapter map are required before installation. An adapter may be needed; no adapter design has been verified.

## Work sequence when resumed

**Balanced sensitivity follow-up, 2026-10-13:** User confirms v8's vertical gain4 works perfectly for adjacent-row selection and requested the same gain on both axes. New image: `temp/work/sony-gb6-20261013/S760224.GB6-v9-balanced-X4-Y4.IMG`, SHA256 `c611e7156c9069dc632bcfd8e4d20a52da70ed2528112f29fe87258803f42deb`. Only file0x18BD0 differs from v8, changing horizontal shift3 to2. Both axes now use gain4;2,048 model cases pass. V8 vertical behavior is user-confirmed; v9 hardware testing remains pending. BUG-059 resolved for the reported vertical row-skipping issue. The combined-controller/ROM plan remains deferred.

**Sensitivity follow-up, 2026-10-13:** User reports that vertical movement skips adjacent Perform Play part rows after the mechanical repair. A separate single-decoder candidate `temp/work/sony-gb6-20261013/S760224.GB6-v8-fine-vertical-X8-Y4.IMG` halves vertical gain from8 to4 while retaining horizontal8. SHA256 `cf29f7fdf75a3a672eefdd34d52f66aa25a6624632a85d52c0500d84223afead`. Only one byte differs fromv7: file0x18BEB, vertical shift count3 becomes2. All2,048 model cases pass; hardware row selection is pending (BUG-059). This sensitivity experiment does not implement or resume the deferred combined-controller/boot-ROM work.

1. Identify/hash the user's successful installed GB-6 disk. Preserve it, the original system disk and boot EPROM dump as recovery artifacts.
2. Trace both boot and OS controller menus, descriptors, edit ranges, persistence, and initialization. Audit candidate spare EEPROM storage and boot validation if considering approachA.
3. Choose approachA orB against the desired experience, especially whether GB-6 must appear in the power-on MODE setup menu as well as the running OS menu.
4. Implement on new copies only. Preserve original mouse and RC-100 code, add GB-6 decoder dispatch, and account for code/data banking, registers, timing and pointer/button state when switching modes.
5. Test boot and runtime switching, save/reboot persistence, no-option-board fallback, menu labels, invalid settings and recovery. Include all four directions, diagonals, slow/fast motion, both buttons, idle drift, screen edges and longer use. Verify Mouse+CRT, Panel+LCD and RC-100 paths; lack of RC-100 hardware is an explicit remaining acceptance limit.
6. If approachB, build and validate a separate32KB ROM, then program a compatible spare EPROM and verify it before installation. Recover by reinstalling the unchanged original ROM and using the original disk if needed.
7. Record exact image/ROM hashes and scoped hardware results. Only then name a combined image as a working release. Sensitivity tuning follows correct mode selection and tracking.

## References

- Local service notes: `manuals/ROLAND_S-760_SERVICE_NOTES.pdf`, parts list and main-board schematic/layout; local firmware documentation: `docs/condensed/01-hardware-and-memory-map.md`, `docs/condensed/07-ui-architecture-and-front-panel.md`.
- [Microchip AT27C256R datasheet](https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/doc0014.pdf).
- [SST39SF010A/020A/040 datasheet, including PDIP pinout](https://ww1.microchip.com/downloads/en/DeviceDoc/S71147.pdf).
- [S-760 firmware/replacement-chip reference and 32-pin socket note](https://llamamusic.com/docs/synth_binaries/synth_binaries.html).
- [Independent openMSX trackball implementation](https://github.com/openMSX/openMSX/blob/master/src/input/Trackball.cc).

No boot-ROM patch, combined-controller image, hardware adapter or persistent fourth-mode implementation has been made as part of this deferred plan.
