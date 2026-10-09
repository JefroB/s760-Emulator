# Roland S-760 CRT Display — System Mode Screens

This document covers all screens within the **System** mode of the Roland S-760 hardware display (`system-1.jpeg` through `system-5.jpeg`), including System Parameters, SCSI bus drive configuration, System MIDI global settings, Volume ID metadata, and System Parameter disk load/save.

---

## 1. Screen system-1: System Parameter 1

- **Image File:** `d:\S-760\screenshots\system-1.jpeg`
- **Active Mode Tab:** `System` (Highlighted white with red/orange text)
- **Screen Title:** `System Parameter1`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | Dec/Inc`
- **Subheader Right Buttons:** `[Pform]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | Dec/Inc                                              |
| Perform | Patch | Partial | Sample | Disk | [ SYSTEM ]                                        |
| System Parameter1                                             [Pform]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Wave Memory Information:                                                                      |
| [ Total: 32Mbyte,  363.8sec ]   [ 44.1KHz, 48KHz, 32KHz ]                                     |
+-----------------------------------------------------------------------------------------------+
| Master - Frequency           : [ 44.1KHz ]                                                    |
|        - Tune                : [   0cent ]                                                    |
|        - Level               : [   127   ]                                                    |
| LCD Contrast                 : [     0   ]                                                    |
| Output - Mode                : [   4st   ]                                                    |
|        - Assign              : [ C/D => C/D ]                                                 |
| Digital Booster              : [    -6   ]                                                    |
| Time Display                 : [    On   ]                                                    |
| Recover Function             : [    On   ]                                                    |
| Continuous Pan               : [   Off   ]                                                    |
| Analog Input Monitor         : [   Off   ]                                                    |
+-----------------------------------------------------------------------------------------------+
| Page( 1 )                                                                                     |
+-----------------------------------------------------------------------------------------------+
| ---            ---          ---           ---           VolInfo                               |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Wave Memory Header (Rows 4-5):**
   - **Total Installed Memory:** `[ Total: 32Mbyte, 363.8sec ]` (Confirms maximum 32 MB sample RAM expansion installed via SIMMs, providing 363.8 seconds at 44.1 kHz).
   - **Supported Sample Rates:** `[ 44.1KHz, 48KHz, 32KHz ]`.

2. **Master Hardware Parameters (Rows 6-17):**
   - **Master - Frequency:** `[ 44.1KHz ]` (Global hardware DAC clock rate: `44.1KHz` / `48KHz`).
   - **Master - Tune:** `[ 0cent ]` (Global master tuning in cents: `-50` to `+50`).
   - **Master - Level:** `[ 127 ]` (Master analog output volume: `0` to `127`).
   - **LCD Contrast:** `[ 0 ]` (Contrast adjustment for front-panel 160x64 LCD).
   - **Output - Mode:** `[ 4st ]` (4 stereo output pairs: A, B, C, D).
   - **Output - Assign:** `[ C/D => C/D ]` (Bus routing for optional output boards).
   - **Digital Booster:** `[ -6 ]` (Digital gain boost / headroom pad in dB).
   - **Time Display:** `[ On ]` (Enables time display in sample editors).
   - **Recover Function:** `[ On ]` (Enables RAM buffer undo memory for DSP edits).
   - **Continuous Pan:** `[ Off ]` (Enables smooth continuous pan interpolation).
   - **Analog Input Monitor:** `[ Off ]` (Audio pass-through for analog sampling inputs).

3. **Page Indicator:** `Page( 1 )`.

4. **Bottom Softkeys (Row 23-24):**
   - **F1-F4:** `---` — Disabled placeholders.
   - **F5 / Side:** `VolInfo` — Volume memory information.

---

## 2. Screen system-2: System SCSI

- **Image File:** `d:\S-760\screenshots\system-2.jpeg`
- **Active Mode Tab:** `System`
- **Screen Title:** `System SCSI`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | ---/---`
- **Subheader Right Buttons:** `[Pform]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | Sample | Disk | [ SYSTEM ]                                        |
| System SCSI                                                   [Pform]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Wave Memory Information: [ Total: 32Mbyte,  363.8sec ]                                        |
+-----------------------------------------------------------------------------------------------+
| S-760 Self SCSI ID           : [     7 ]                                                      |
| Initial Drive                : [ SCSI:6 ]                                                     |
| Initial Volume               : [    65 ]                                                      |
| Boot Drive                   : [ Default ]                                                    |
| Fast Delete Mode             : [   Off ]                                                      |
| Overwrite Switch             : [   Off ]                                                      |
| CDP Driver Type              : [   Off ]                                                      |
+-----------------------------------------------------------------------------------------------+
| SCSI Information Bus Grid:                                                                    |
| +-------------------------------------------------------------------------------------------+ |
| |  --0:  -- No Drive               --4:  -- No Drive                                        | |
| |  --1:  -- No Drive               --5:  -- No Drive                                        | |
| |  --2:  -- No Drive               --6:  -- No Drive                                        | |
| |  --3:  -- No Drive               ME7:  S-760 Self (Initiator ID 7)                        | |
| |                                 *FDD:  -FloppyDisk-                                       | |
| +-------------------------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------+
| ---            ---          ---           ---           VolInfo                               |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **SCSI Controller Parameters (Rows 6-12):**
   - **S-760 Self SCSI ID:** `[ 7 ]` (Host controller initiator ID on SCSI bus).
   - **Initial Drive:** `[ SCSI:6 ]` (Default drive probed on startup).
   - **Initial Volume:** `[ 65 ]` (Default volume index loaded).
   - **Boot Drive:** `[ Default ]` (Boot device priority: Floppy or SCSI).
   - **Fast Delete Mode:** `[ Off ]` (Instant FAT pointer clearing vs full sector wipe).
   - **Overwrite Switch:** `[ Off ]` (Global overwrite safety warning toggle).
   - **CDP Driver Type:** `[ Off ]` (CD-ROM protocol driver type: Apple, Sony, Toshiba).

2. **SCSI Information Bus Scan Table (Rows 13-21):**
   - Two-column visual layout showing all 8 SCSI bus IDs plus internal Floppy:
     - `--0` to `--6`: `No Drive` (Empty bus slots).
     - `ME7`: `S-760 Self` (The sampler itself as SCSI host).
     - `*FDD`: `-FloppyDisk-` (Internal 3.5" HD floppy drive marked with asterisk as active drive).

3. **Bottom Softkeys (Row 23-24):**
   - **F1-F4:** `---` — Disabled placeholders.
   - **F5 / Side:** `VolInfo` — Volume memory information.

---

## 3. Screen system-3: System MIDI

- **Image File:** `d:\S-760\screenshots\system-3.jpeg`
- **Active Mode Tab:** `System`
- **Screen Title:** `System MIDI`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | ---/---`
- **Subheader Right Buttons:** `[Pform]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | Sample | Disk | [ SYSTEM ]                                        |
| System MIDI                                                   [Pform]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Wave Memory Information: [ Total: 32Mbyte,  363.8sec ]                                        |
+-----------------------------------------------------------------------------------------------+
| Control Channel              : [   Off ]                                                      |
| Control Mode                 : [ Perf/Vol ]                                                   |
| MIDI Out/Thru                : [   Out ]                                                      |
| Device ID                    : [     1 ]                                                      |
| Exclusive RX                 : [   Off ]                                                      |
| Interval (Kbyte)             : [   All ]                                                      |
| Sample Dump Source           : [ 1] PNO:MP-1.                                                 |
+-----------------------------------------------------------------------------------------------+
| Multi-Channel Equalizer Matrix (Channels 1 to 8):                                             |
| [Ch]| H.Freq | H.Gain | L.Freq | L.Gain || [Ch]| H.Freq | H.Gain | L.Freq | L.Gain            |
|-----+--------+--------+--------+--------||-----+--------+--------+--------+-------            |
| [1] |   78   |   24   |   70   |   16   || [5] |   82   |   28   |   74   |   20             |
| [2] |   79   |   25   |   71   |   17   || [6] |   83   |   29   |   75   |   21             |
| [3] |   80   |   26   |   72   |   18   || [7] |   84   |   30   |   76   |   22             |
| [4] |   81   |   27   |   73   |   19   || [8] |   85   |   31   |   77   |   23             |
+-----------------------------------------------------------------------------------------------+
| ---            SmpDump      SysDump       VolDump       VolInfo                               |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **MIDI Global Settings (Rows 6-13):**
   - **Control Channel:** `[ Off ]` (Global system command channel: 1-16 or Off).
   - **Control Mode:** `[ Perf/Vol ]` (Program change destination target).
   - **MIDI Out/Thru:** Hardware switch function `[ Out ]` (`Out` / `Thru`).
   - **Device ID:** Roland SysEx device ID `[ 1 ]` (1 to 32).
   - **Exclusive RX:** System Exclusive reception toggle `[ Off ]` (`On` / `Off`).
   - **Interval (Kbyte):** SysEx packet flow-control delay `[ All ]`.
   - **Sample Dump Source:** Target sample for MIDI Sample Dump Standard (SDS) transmission: `[ 1] PNO:MP-1.`.

2. **8-Part Equalizer Table (Rows 14-21):**
   - Shows High Frequency (`H.F`), High Gain (`H.G`), Low Frequency (`L.F`), and Low Gain (`L.G`) for all 8 parts.

3. **Bottom Softkeys (Row 23-24):**
   - **F1:** `---` — Disabled placeholder.
   - **F2:** `SmpDump` — Initiates MIDI Sample Dump Standard (SDS) transmission.
   - **F3:** `SysDump` — Transmits Roland System Exclusive parameter dump.
   - **F4:** `VolDump` — Transmits entire Volume memory via MIDI SysEx.
   - **F5 / Side:** `VolInfo` — Volume memory information.

---

## 4. Screen system-4: System Volume ID

- **Image File:** `d:\S-760\screenshots\system-4.jpeg`
- **Active Mode Tab:** `System`
- **Screen Title:** `System Volume ID`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | ---/---`
- **Subheader Right Buttons:** `[Pform]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | Sample | Disk | [ SYSTEM ]                                        |
| System Volume ID                                              [Pform]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Wave Memory Information: [ Total: 32Mbyte,  363.8sec ]                                        |
+-----------------------------------------------------------------------------------------------+
|                                                                                               |
|          Volume Name         : [ -     :                  ]                                   |
|          Volume ID           : [ ---   ]  for:                                                |
|                                                                                               |
|                     Volume                       Patch                                        |
|                     Performance                  Partial                                      |
|                                                  Sample                                       |
|                                                                                               |
+-----------------------------------------------------------------------------------------------+
| [ ]AllOn       ---          Exec          ---           VolInfo                               |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Volume Metadata Fields (Rows 7-9):**
   - **Volume Name:** Text entry box for up to 16 characters `[ - : ]`.
   - **Volume ID:** 3-digit numerical ID `[ --- ]` used to identify sound banks across SCSI media.

2. **Target Scope Checkboxes (Rows 10-14):**
   - Allows applying the Volume ID tag selectively across data types:
     - `Volume`
     - `Performance`
     - `Patch`
     - `Partial`
     - `Sample`

3. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]AllOn` — Selects all data types.
   - **F2:** `---` — Disabled placeholder.
   - **F3:** `Exec` — Writes the new ID/name to RAM sound objects.
   - **F4:** `---` — Disabled placeholder.
   - **F5 / Side:** `VolInfo` — Volume memory information.

---

## 5. Screen system-5: LD/SV System PRM (Load / Save System Parameters)

- **Image File:** `d:\S-760\screenshots\system-5.jpeg`
- **Active Mode Tab:** `System`
- **Screen Title:** `LD/SV System PRM`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | ---/---`
- **Subheader Right Buttons:** `[Pform]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | Sample | Disk | [ SYSTEM ]                                        |
| LD/SV System PRM                                              [Pform]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Wave Memory Information: [ Total: 32Mbyte,  363.8sec ]                                        |
+-----------------------------------------------------------------------------------------------+
|                                                                                               |
|                                                                                               |
|                          S-760 System Parameter                                               |
|                                                                                               |
|                          [ ------------------------------ ]                                   |
|                                                                                               |
|                                                                                               |
+-----------------------------------------------------------------------------------------------+
| LoadPRM        ---          SavePRM       ---           VolInfo                               |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Parameter File Container (Rows 8-12):**
   - Displays the system configuration file name currently loaded or targeted for save operations `[ ------------------------------ ]`.

2. **Bottom Softkeys (Row 23-24):**
   - **F1:** `LoadPRM` — Loads hardware settings, SCSI IDs, and MIDI configurations from disk.
   - **F2:** `---` — Disabled placeholder.
   - **F3:** `SavePRM` — Writes current system parameters permanently to the system floppy or boot SCSI volume.
   - **F4:** `---` — Disabled placeholder.
   - **F5 / Side:** `VolInfo` — Volume memory information.
