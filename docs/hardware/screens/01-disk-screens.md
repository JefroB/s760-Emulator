# Roland S-760 CRT Display — Disk Mode Screens

This document covers all screens within the **Disk** mode of the Roland S-760 hardware display (`DISK-1.jpeg` and `DISK-2.jpeg`).

---

## 1. Screen DISK-1: Disk Load

- **Image File:** `d:\S-760\screenshots\DISK-1.jpeg`
- **Active Mode Tab:** `Disk` (Highlighted white with red/orange text)
- **Screen Title:** `Disk Load`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | ---/---`
- **Subheader Right Buttons:** `[Disk]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | Sample | [ DISK ] | System                                        |
| Disk Load                                                     [Disk]  Mark  Jump  Com         |
+-----------------------------------------------------------------------------------------------+
| Target   : TG[Pfom]       ID[All]       Device : CD[FDD:-FloppyDisk-]                         |
+-----------------------------------------------------------------------------------------------+
|  No. Type Name                    Size   |  Internal    Disk         Marked                   |
| -----------------------------------------| ---------------------------------                  |
| [ 1] PNO  Acoustic Pno 1/ 1       2.1M   |  Pform:  0   Pform:  1    Pform:  0                |
| [ 2] EP   Rhodes Stage 73         1.4M   |  Patch:  0   Patch: 16    Patch:  0                |
| [ 3] STR  Stereo Strings 1        3.2M   |  Partl:  0   Partl: 32    Partl:  0                |
| [ 4] BAS  Acoustic Upright        0.9M   |  Smpl :  0   Smpl : 48    Smpl :  0                |
| [ 5] VOX  Choir Aahs Full         1.8M   |                                                    |
| [ 6] ---  -----------------       ----   |                                                    |
+-----------------------------------------------------------------------------------------------+
| [ ]AllOn      ---         Load         [ ]OW Off     VolInfo                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Top Target & Device Control Bar (Row 4):**
   - **Target Filter:** `Target : TG[Pfom]` (Target type selector: `Pfom` [Performance], `Patch`, `Partl`, `Sample`, `All`).
   - **Target ID:** `ID[All]` (Filter by MIDI or sound bank ID).
   - **Device Selector:** `Device : CD[FDD:-FloppyDisk-]` (Active source drive: floppy drive or SCSI CD/HD/MO unit).

2. **File Catalog Table (Left Panel):**
   - Columns:
     - `No.` : Item index in disk directory (`[ 1]` to `[ 6]`).
     - `Type` : Data category tag (`PNO`, `EP`, `STR`, `BAS`, `VOX`).
     - `Name` : File name string up to 16 characters (e.g. `Acoustic Pno 1/ 1`).
     - `Size` : Data memory footprint in Megabytes (`2.1M`, `1.4M`, etc.).

3. **Memory Allocation & Count Status Box (Right Panel):**
   - Three status columns:
     - `Internal`: Count of currently loaded objects in internal RAM (`Pform: 0`, `Patch: 0`, `Partl: 0`, `Smpl: 0`).
     - `Disk`: Total available objects present on disk (`Pform: 1`, `Patch: 16`, `Partl: 32`, `Smpl: 48`).
     - `Marked`: Total selected/checked objects ready for batch loading (`Pform: 0`, `Patch: 0`, `Partl: 0`, `Smpl: 0`).

4. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]AllOn` — Checkbox toggle to select/mark all files in the catalog.
   - **F2:** `---` — Disabled placeholder.
   - **F3:** `Load` — Action button to execute loading of selected files into RAM.
   - **F4:** `[ ]OW Off` — Overwrite protection toggle (`OW Off` / `OW On`).
   - **F5 / Side:** `VolInfo` — Displays disk volume information and total capacity.

---

## 2. Screen DISK-2: Disk Load — File Scanning Modal

- **Image File:** `d:\S-760\screenshots\DISK-2.jpeg`
- **Active Mode Tab:** `Disk`
- **Screen Title:** `Disk Load`
- **Modal Popup Window:** Enclosed popup with thick border placed in screen center.

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | Sample | [ DISK ] | System                                        |
| Disk Load                                                     [Disk]  Mark  Jump  Com         |
+-----------------------------------------------------------------------------------------------+
|                                                                                               |
|               +-------------------------------------------------------+                       |
|               |              !!  Now Working  ++++                    |                       |
|               |                                                       |                       |
|               |    Load...   PNO:Acoustic Pno 1/ 1                    |                       |
|               |                                                       |                       |
|               |    # File Scanning ......                             |                       |
|               |                                                       |                       |
|               |                 ( [EXIT] for Cancel )                 |                       |
|               +-------------------------------------------------------+                       |
|                                                                                               |
+-----------------------------------------------------------------------------------------------+
| [ ]AllOn      ---         Load         [ ]OW Off     VolInfo                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Modal Frame Properties:**
   - Width: ~340 pixels; Height: ~140 pixels. Centered horizontally and vertically over the disk file list.
   - Border: Solid double-line frame with high contrast.

2. **Modal Content & Typography:**
   - **Header:** `!! Now Working ++++` — Flashing or animated work banner indicating disk head movement / bus activity.
   - **Current Item:** `Load... PNO:Acoustic Pno 1/ 1` — Name of the current performance/sample entity being read.
   - **Progress / Status:** `# File Scanning ......` — Progress animation reading the allocation tables or sector cluster chains.
   - **Cancel Instruction:** `( [EXIT] for Cancel )` — User instruction to abort disk operation via the front-panel EXIT button.

3. **Background State:**
   - The underlying Disk Load screen is dimmed/inactive while modal execution is in progress.
