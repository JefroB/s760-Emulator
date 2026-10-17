# Hardware-in-the-Loop (HIL) Deployment Guide — Roland S-760

This guide details the physical testing pipeline to execute modified Roland S-760 OS binaries on physical sampler hardware without burning physical EPROMs.

---

## 1. Gotek Floppy Emulator Setup (FlashFloppy)

Replace the physical 3.5" floppy drive with a **Gotek USB Floppy Drive Emulator** flashed with **FlashFloppy** firmware.

### FlashFloppy `FF.CFG` Configuration
Place the following setting in `FF.CFG` on the root of your USB flash drive:

```ini
interface = shugart
host = pc
nav-mode = native
display-type = lcd-1602
image-grid-select = no
autocont = yes
```

### Floppy Geometry (Roland S-760 1.44 MB)
* **Format:** High Density (HD) 3.5"
* **Tracks:** 80
* **Heads:** 2
* **Sectors per track:** 18
* **Sector size:** 512 bytes
* **Total size:** 1,474,560 bytes (0x168000)

---

## 2. SCSI Hardware Emulation (ZuluSCSI / PiSCSI)

Connect a **ZuluSCSI** or **PiSCSI** module to the external DB25 SCSI bus or internal 50-pin header.

* **Target SCSI ID:** ID 0 or 1.
* **Image Naming:** `HD00_512.hda`
* **Partition Layout:** Roland proprietary S-770/S-760 volume block layout.

---

## 3. Automated HIL Build & Export Pipeline

To generate and transfer a modified system disk image to your physical testing USB/SD media:

```powershell
# 1. Run automated static invariants test
python -m pytest tests/

# 2. Package custom OS binary chunk into target disk image
python .kiro/scripts/build_dump_chunk.py S760224.IMG target_payload.bin --off 0x4800 --out temp/S760_HIL.IMG

# 3. Copy target image to USB drive (replace E: with your USB drive letter)
Copy-Item temp/S760_HIL.IMG E:/S760224.IMG -Force
```

---

## 4. Hardware Verification Checklist
- [ ] USB drive formatted FAT32/exFAT with `FF.CFG` and `S760224.IMG`.
- [ ] S-760 powered on; display shows `Loading System...`.
- [ ] System initializes to main menu (Ver. 2.24 or custom modified version string displayed).
