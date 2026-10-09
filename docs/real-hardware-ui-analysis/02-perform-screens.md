# Roland S-760 CRT Display — Perform Mode Screens

This document covers all screens within the **Perform** mode of the Roland S-760 hardware display (`perform-1.jpeg` through `perform-5.jpeg`), including the main multi-timbral mixing console and the navigation popups (`Mark`, `Jump`, `Command`, `Perform MENU`).

---

## 1. Screen perform-1: Perform Play 1 (Multi-Timbral Mixing Console)

- **Image File:** `d:\S-760\screenshots\perform-1.jpeg`
- **Active Mode Tab:** `Perform` (Highlighted white with red/orange text)
- **Screen Title:** `Perform Play 1`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | ---/---`
- **Subheader Center Badge:** `[Part1]` (Active selected part)
- **Subheader Right Buttons:** `[Pform]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| [ PERFORM ] | Patch | Partial | Sample | Disk | System                                        |
| Perform Play 1              [Part1]                           [Pform]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Performance: [ 1] PNO:Concert Grand                                         Master: [ 127 ]   |
|                                                                             [|||||||||||||]   |
+-----------------------------------------------------------------------------------------------+
| Part | Patch Name              | MIDI Ch | Level | Pan | Output | Voice | Tune | Priority     |
|------+-------------------------+---------+-------+-----+--------+-------+------+--------------|
|  1   | [ 1] PNO:Piano p/f AA   |    1    |  127  |  0  |   A    |   16  |   0  |   Last       |
|  2   | [ 2] EP :Stage Rhodes   |    2    |  110  | -15 |   A    |    8  |   0  |   Last       |
|  3   | [ 3] STR:Stereo String  |    3    |  100  | +10 |   B    |   12  |   0  |   Last       |
|  4   | [ 4] BAS:Upright Bass   |    4    |  120  |  0  |   C    |    4  |   0  |   Last       |
|  5   | [ 5] VOX:Choir Aahs     |    5    |   95  | +25 |   B    |    8  |   0  |   Last       |
|  6   | [ 6] SYN:Analog Pad     |    6    |   90  | -20 |   A    |    8  |   0  |   Last       |
|  7   | [ 7] GTR:Nylon Acoustic |    7    |  105  |  0  |   D    |    6  |   0  |   Last       |
|  8   | [ 8] DRM:Standard Kit   |   10    |  127  |  0  |  1-8   |   16  |   0  |   Last       |
+-----------------------------------------------------------------------------------------------+
| [===== Keyboard Split Zone Bar: Part 1 Active (A0 to C8) ===================================] |
| ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| |
| C1        C2        C3        C4        C5        C6        C7                                |
+-----------------------------------------------------------------------------------------------+
| [ ]KbdOn       Q-Samp       Sol/Mut       PartMap       VolInfo                               |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Header & Master Level Meter (Rows 4-5):**
   - **Current Performance Selector:** `Performance: [ 1] PNO:Concert Grand` (Selects active multi-patch setup 1-64).
   - **Master Level Numerical:** `Master: [ 127 ]` (0 to 127).
   - **Master Output Meter:** Solid cyan horizontal peak bar with tick increments showing combined digital master bus headroom.

2. **8-Part Multi-Timbral Mixer Table (Rows 6-15):**
   - Table columns with cyan header labels:
     - `Part` : Part number (1 to 8).
     - `Patch Name` : Patch slot index and assigned patch name (e.g. `[ 1] PNO:Piano p/f AA`).
     - `MIDI Ch` : Assigned MIDI channel (1 to 16, or `Off`).
     - `Level` : Part volume (0 to 127).
     - `Pan` : Stereo pan placement (`-50` [L] to `0` [Center] to `+50` [R]).
     - `Output` : Hardware DAC output bus assignment (`A`, `B`, `C`, `D`, or individual `1` to `8` outputs).
     - `Voice` : Voice reserve allocation count.
     - `Tune` : Part coarse/fine tuning offset.
     - `Priority` : Note-stealing priority (`Last`, `First`, `Off`).

3. **88-Key Interactive Piano Keyboard (Rows 16-20):**
   - Rendered across the full screen width from `A0` to `C8`.
   - **Split Zone Bar:** A solid cyan horizontal band situated immediately above the keys showing the assigned playable pitch zone for the currently focused Part.
   - **Octave Markers:** `C1` through `C7` text labels centered under corresponding C keys.

4. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]KbdOn` — Toggles on-screen keyboard preview via mouse clicks.
   - **F2:** `Q-Samp` — Quick Sample jump shortcut.
   - **F3:** `Sol/Mut` — Toggles Solo/Mute mode for individual parts.
   - **F4:** `PartMap` — Opens full 16-part / 32-part overview layout.
   - **F5 / Side:** `VolInfo` — Opens Volume memory overview.

---

## 2. Screen perform-2: Perform Play 1 — Mark Popup

- **Image File:** `d:\S-760\screenshots\perform-2.jpeg`
- **Active Modal:** `Mark` Popup (Triggered by clicking `Mark` in Row 3)

```
+-----------------------------------------------------------------------------------------------+
| Perform Play 1              [Part1]                           [Pform] [Mark]  Jump  Com       |
+-----------------------------------------------------------------------------------------------+
|                                      +------------------------------------+                   |
|                                      | #  Mark Screen List                |                   |
|                                      |------------------------------------|                   |
|                                      | 01: Perform Play 1                 |                   |
|                                      | 02: Perform EQ                     |                   |
|                                      | 03: Patch Common                   |                   |
|                                      | 04: Patch Split                    |                   |
|                                      | 05: Partial Common                 |                   |
|                                      | 06: Partial TVF                    |                   |
|                                      | 07: Partial TVA                    |                   |
|                                      | 08: Sample Edit                    |                   |
|                                      | 09: Loop & Smoothing               |                   |
|                                      | 10: Disk Load                      |                   |
|                                      +------------------------------------+                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- **Frame Style:** Yellow-bordered popup box (`#FFFF00`) with high-contrast text.
- **Position:** Anchored directly beneath the `Mark` button on the right side of the screen.
- **Slots:** 10 user-configurable memory bookmark locations (`01` through `10`).
- **Functionality:** Allows instant bookmarking of deeply nested editor screens for rapid switching during sound design sessions.

---

## 3. Screen perform-3: Perform Play 1 — Jump Popup

- **Image File:** `d:\S-760\screenshots\perform-3.jpeg`
- **Active Modal:** `Jump` Popup (Triggered by clicking `Jump` in Row 3)

```
+-----------------------------------------------------------------------------------------------+
| Perform Play 1              [Part1]                           [Pform]  Mark  [Jump] Com       |
+-----------------------------------------------------------------------------------------------+
|                                              +------------------------------------+           |
|                                              | #  Jump Screen Destination         |           |
|                                              |------------------------------------|           |
|                                              | 01: Perform Play 1                 |           |
|                                              | 02: Perform Play 2                 |           |
|                                              | 03: Perform EQ                     |           |
|                                              | 04: MIDI Filter                    |           |
|                                              | 05: Voice Monitor                  |           |
|                                              | 06: Wave Memory                    |           |
|                                              | 07: Quick Load                     |           |
|                                              | 08: Patch Edit                     |           |
|                                              | 09: Sample Edit                    |           |
|                                              | 10: System Setup                   |           |
|                                              +------------------------------------+           |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- **Frame Style:** Yellow-bordered popup box (`#FFFF00`).
- **Position:** Anchored directly under the `Jump` header button.
- **Slots:** 10 predefined destination shortcuts (`01` to `10`).
- **Functionality:** Direct jump execution to assigned screens without traversing parent mode tabs.

---

## 4. Screen perform-4: Perform Play 1 — Command Popup (`Com`)

- **Image File:** `d:\S-760\screenshots\perform-4.jpeg`
- **Active Modal:** `Command` Popup (Triggered by clicking `Com` in Row 3)

```
+-----------------------------------------------------------------------------------------------+
| Perform Play 1              [Part1]                           [Pform]  Mark  Jump  [Com]      |
+-----------------------------------------------------------------------------------------------+
|                                                              +----------------------------+   |
|                                                              | *  Command Menu            |   |
|                                                              |----------------------------|   |
|                                                              | Edit Patch                 |   |
|                                                              | Copy Performance           |   |
|                                                              | Delete Performance         |   |
|                                                              | Initialize Performance     |   |
|                                                              | Disk Save                  |   |
|                                                              | CD-ROM Player              |   |
|                                                              +----------------------------+   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- **Frame Style:** Red-bordered popup box (`#FF0000`) denoting system/modification commands.
- **Position:** Anchored under the far right `Com` button.
- **Items:**
  1. `Edit Patch` — Transitions immediately into `Patch Common` for the focused part.
  2. `Copy Performance` — Duplicates active performance settings to another slot.
  3. `Delete Performance` — Erases selected performance parameters.
  4. `Initialize Performance` — Resets performance to factory defaults.
  5. `Disk Save` — Direct jump to disk save utility.
  6. `CD-ROM Player` — Launches the audio CD player utility if a SCSI CD-ROM drive is connected.

---

## 5. Screen perform-5: Perform Play 1 — Perform MENU Submenu (`Pform`)

- **Image File:** `d:\S-760\screenshots\perform-5.jpeg`
- **Active Modal:** `Perform MENU` Dropdown (Triggered by clicking `[Pform]` in Row 3)

```
+-----------------------------------------------------------------------------------------------+
| Perform Play 1              [Part1]                          [[Pform]] Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
|                                      +------------------------------------+                   |
|                                      | Perform MENU                       |                   |
|                                      |------------------------------------|                   |
|                                      | Perform Play                       |                   |
|                                      | Perform EQ                         |                   |
|                                      | MIDI Filter                        |                   |
|                                      | Listen Delete                      |                   |
|                                      | Perform Utility                    |                   |
|                                      | Monitor                            |                   |
|                                      | Quick Load                         |                   |
|                                      +------------------------------------+                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- **Frame Style:** Green-bordered popup box (`#00FF00`) denoting mode-level navigation.
- **Position:** Anchored directly under the `[Pform]` mode dropdown button.
- **Submenu Options:**
  1. `Perform Play` — Main multi-timbral mixing console.
  2. `Perform EQ` — 4-band / 8-channel master equalization.
  3. `MIDI Filter` — Per-part MIDI event filtering (Pitch Bend, Aftertouch, Modulation, Sysex).
  4. `Listen Delete` — Interactive auditioning and purging of unused patches.
  5. `Perform Utility` — Bulk copy, rename, and slot arrangement tools.
  6. `Monitor` — Real-time 24-voice polyphony monitor showing active voice assignment.
  7. `Quick Load` — Express loading of performance templates from disk.
