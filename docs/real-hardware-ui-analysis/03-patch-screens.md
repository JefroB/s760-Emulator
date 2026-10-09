# Roland S-760 CRT Display — Patch Mode Screens

This document covers all screens within the **Patch** mode of the Roland S-760 hardware display (`patch-1.jpeg` through `patch-4.jpeg`), including Patch Common parameters, Key Split zoning, Modulation Matrix routing, and Quick Sampling.

---

## 1. Screen patch-1: Patch Common

- **Image File:** `d:\S-760\screenshots\patch-1.jpeg`
- **Active Mode Tab:** `Patch` (Highlighted white with red/orange text)
- **Screen Title:** `Patch Common`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | ---/---`
- **Subheader Center Badge:** `[Patch 1] PNO:Piano p/f AA`
- **Subheader Right Buttons:** `[Patch]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | [ PATCH ] | Partial | Sample | Disk | System                                        |
| Patch Common                [Patch 1] PNO:Piano p/f AA        [Patch]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Patch Level        : [ 120 ]   |---|------------------|   (Range: 0 ~ 127)                    |
| Pan                : [   0 ]   |---------|------------|   (Range: -50 ~ +50)                  |
| Output Assign      : [   A ]                                                                  |
| Priority           : [ Off ]   Octave Shift: [  0 ]       Velocity Sw Threshold: [  64 ]      |
+-----------------------------------------------------------------------------------------------+
| Fine Tune          : [   0 ]   |---------|------------|   (Range: -50 ~ +50)                  |
| Coarse Tune        : [   0 ]   |---------|------------|   (Range: -24 ~ +24)                  |
| Analog Feel        : [  12 ]   |---|------------------|   (Range: 0 ~ 127)                    |
| Bender Range       : [   2 ]   (Pitch Bend Depth: 0 ~ 12 semitones)                           |
+-----------------------------------------------------------------------------------------------+
| Partial Select     : [ 1: Piano p/f AA ]  [ 2: --Off--        ]                               |
|                      [ 3: --Off--      ]  [ 4: --Off--        ]                               |
+-----------------------------------------------------------------------------------------------+
| [ ]Single      Split        Ctrl          Q-Samp        VolInfo                               |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Top Parameter Block (Rows 4-7):**
   - **Patch Level:** Numerical box `[ 120 ]` accompanied by a horizontal slider widget with a red downward-pointing triangle cursor.
   - **Pan:** Numerical box `[ 0 ]` with center-detented horizontal slider widget (`-50` Left, `0` Center, `+50` Right).
   - **Output Assign:** Dropdown selector `[ A ]` (Options: `A`, `B`, `C`, `D`, `1` through `8`).
   - **Priority:** Switch `[ Off ]` (Options: `Off`, `Last`, `First`).
   - **Octave Shift:** Numerical box `[ 0 ]` (`-3` to `+3`).
   - **Velocity Sw Threshold:** Velocity trigger point `[ 64 ]` (1 to 127).

2. **Tuning & Modulation Block (Rows 8-12):**
   - **Fine Tune:** Numerical box `[ 0 ]` with slider widget (`-50` to `+50` cents).
   - **Coarse Tune:** Numerical box `[ 0 ]` with slider widget (`-24` to `+24` semitones).
   - **Analog Feel:** Numerical box `[ 12 ]` with slider widget (`0` to `127`) introducing subtle analog pitch drift.
   - **Bender Range:** Depth in semitones `[ 2 ]` (`0` to `12`).

3. **Assigned Partials List (Rows 13-15):**
   - Four partial assign slots showing assigned partial names or `--Off--`:
     - Slot 1: `[ 1: Piano p/f AA ]`
     - Slot 2: `[ 2: --Off-- ]`
     - Slot 3: `[ 3: --Off-- ]`
     - Slot 4: `[ 4: --Off-- ]`

4. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]Single` — Checkbox toggle to isolate and audition the current partial in solo mode.
   - **F2:** `Split` — Jump to `Patch Split` editor.
   - **F3:** `Ctrl` — Jump to `Patch Control` modulation matrix.
   - **F4:** `Q-Samp` — Jump to `Patch Q-Sampling`.
   - **F5 / Side:** `VolInfo` — Volume memory information.

---

## 2. Screen patch-2: Patch Split

- **Image File:** `d:\S-760\screenshots\patch-2.jpeg`
- **Active Mode Tab:** `Patch`
- **Screen Title:** `Patch Split`
- **Subheader Center Badge:** `[Patch 1] PNO:Piano p/f AA`
- **Subheader Right Buttons:** `[Patch]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | [ PATCH ] | Partial | Sample | Disk | System                                        |
| Patch Split                 [Patch 1] PNO:Piano p/f AA        [Patch]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Split Table:                                                                                  |
| Zone | Lower Key | Upper Key | Partial Assign          | Tune | Pan | Level | Output          |
|------+-----------+-----------+-------------------------+------+-----+-------+-----------------|
|  1   |    A 0    |    B 2    | [ 1] PNO:Piano Low AA   |   0  | -10 |  127  |    A            |
|  2   |    C 3    |    F#4    | [ 2] PNO:Piano Mid AA   |   0  |   0 |  127  |    A            |
|  3   |    G 4    |    C 8    | [ 3] PNO:Piano High AA  |   0  | +10 |  127  |    A            |
|  4   |   ---     |   ---     | --Off--                 |  --- | --- |  ---  |   ---           |
+-----------------------------------------------------------------------------------------------+
| Split Graphic Range Bar:                                                                      |
| [ Zone 1: A0 to B2 ]========[ Zone 2: C3 to F#4 ]========[ Zone 3: G4 to C8 ]==============   |
| ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| |
| C1        C2        C3        C4        C5        C6        C7                                |
+-----------------------------------------------------------------------------------------------+
| [ ]MIDISel     [ ]O.W       Set           ---           ---                                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Split Definition Table (Rows 4-11):**
   - Columns:
     - `Zone` : Zone index (1 to 8 zones per patch).
     - `Lower Key` : Bottom note of zone (e.g. `A 0`, `C 3`, `G 4`).
     - `Upper Key` : Top note of zone (e.g. `B 2`, `F#4`, `C 8`).
     - `Partial Assign` : Partial assigned to this key zone.
     - `Tune`, `Pan`, `Level`, `Output` : Per-zone mixing overrides.

2. **Split Graphic Range Bar & 88-Key Piano Keyboard (Rows 12-18):**
   - **Cyan Zone Bars:** Rendered directly over the keyboard keys; visual segments show key spans for Zone 1, Zone 2, and Zone 3 without overlap or gaps.
   - **88-Key Keyboard:** Interactive visual keyboard from `A0` to `C8`.

3. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]MIDISel` — Checkbox toggle allowing keyboard note selection via MIDI input.
   - **F2:** `[ ]O.W` — Overwrite confirmation toggle.
   - **F3:** `Set` — Commits the current split boundaries.
   - **F4 / F5:** `---` — Disabled placeholders.

---

## 3. Screen patch-3: Patch Control (Modulation Matrix)

- **Image File:** `d:\S-760\screenshots\patch-3.jpeg`
- **Active Mode Tab:** `Patch`
- **Screen Title:** `Patch Control`
- **Subheader Center Badge:** `[Patch 1] PNO:Piano p/f AA`
- **Subheader Right Buttons:** `[Patch]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | [ PATCH ] | Partial | Sample | Disk | System                                        |
| Patch Control               [Patch 1] PNO:Piano p/f AA        [Patch]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| SMT Ctrl Sel : [ After Touch ]     Sens : [ +32 ]     Breath Ctrl : [ Mod Wheel ]             |
+-----------------------------------------------------------------------------------------------+
| Destination       | Pitch Depth | TVF Cutoff  | TVA Level   | LFO Rate    | LFO Pitch Depth   |
|-------------------+-------------+-------------+-------------+-------------+-------------------|
| Bender            |    +2       |      0      |      0      |      0      |        0          |
| After Touch       |     0       |    +15      |     +5      |      0      |      +25          |
| Modulation Wheel  |     0       |     +8      |      0      |    +12      |      +40          |
| Assignable Ctrl   |     0       |      0      |      0      |      0      |        0          |
+-----------------------------------------------------------------------------------------------+
| Pressure Sens     : [ +10 ]   |---|------------------|   (Key Aftertouch Sensitivity)         |
| Modulation Sens   : [ +64 ]   |---------|------------|   (CC#1 Modulation Wheel Depth)        |
+-----------------------------------------------------------------------------------------------+
| [ ]Single      ---          ---           ---           ---                                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Top Global Controller Setup (Rows 4-5):**
   - `SMT Ctrl Sel` : Dynamic velocity/aftertouch selection (`After Touch`, `Modulation`, `Breath`).
   - `Sens` : Sensitivity amount (`-63` to `+63`).
   - `Breath Ctrl` : Physical source mapping.

2. **Modulation Matrix Routing Grid (Rows 6-13):**
   - **Sources (Rows):**
     - `Bender` : Pitch Bend wheel.
     - `After Touch` : Channel pressure / Key pressure.
     - `Modulation Wheel` : MIDI CC#1.
     - `Assignable Ctrl` : MIDI CC#16/CC#80 assignable knob.
   - **Destinations (Columns):**
     - `Pitch Depth` : Pitch modulation amount (`-63` to `+63`).
     - `TVF Cutoff` : Filter cutoff frequency modulation.
     - `TVA Level` : Amplifier level modulation.
     - `LFO Rate` : Speed modulation of the LFO.
     - `LFO Pitch Depth` : Vibrato intensity.

3. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]Single` — Checkbox toggle.
   - **F2-F5:** `---` — Disabled placeholders.

---

## 4. Screen patch-4: Patch Q-Sampling (Quick Sampling)

- **Image File:** `d:\S-760\screenshots\patch-4.jpeg`
- **Active Mode Tab:** `Patch`
- **Screen Title:** `Patch Q-Sampling`
- **Subheader Center Badge:** `[Patch 1] PNO:Piano p/f AA`
- **Subheader Right Buttons:** `[Patch]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | [ PATCH ] | Partial | Sample | Disk | System                                        |
| Patch Q-Sampling            [Patch 1] PNO:Piano p/f AA        [Patch]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Partial: [ 1] PNO:Piano p/f AA        Sample: [ 1] 1 PNO:MP-1.                                |
+-----------------------------------------------------------------------------------------------+
| Pitch Parameters       | TVF Parameters          | TVA Parameters                             |
|------------------------+-------------------------+--------------------------------------------|
| Key Follow : Normal    | Filter Mode : LPF       | Level   : 127                              |
| Coarse     : 0         | Cutoff Freq :  37       | Release :  20                              |
| Fine       : 7         | Resonance   :   0       | Velo-Crv: 2./                              |
+-----------------------------------------------------------------------------------------------+
| Sample Addresses & Playback Mode:                                                             |
| Start : [         0 ]   Loop : [     17888 ]   End : [     23125 ]   Orig Key : [ G#3 ]       |
| Mode  : [ Forward   ]   Length: [ Unlock   ]   E.Mode: [ Mono     ]                           |
+-----------------------------------------------------------------------------------------------+
| ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| |
| C1        C2        C3        C4        C5        C6        C7                                |
+-----------------------------------------------------------------------------------------------+
| Smpling        MoveSet      [ ]MIDISel    Loop          ---                                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Focused Sound Objects (Rows 4-5):**
   - `Partial:` `[ 1] PNO:Piano p/f AA`
   - `Sample:` `[ 1] 1 PNO:MP-1.`

2. **Synthesis Summary Boxes (Rows 6-10):**
   - **Pitch Box:** `Key Follow: Normal`, `Coarse: 0`, `Fine: 7`.
   - **TVF Box:** `Filter Mode: LPF`, `Cutoff Freq: 37`, `Resonance: 0`.
   - **TVA Box:** `Level: 127`, `Release: 20`, `Velo-Crv: 2./`.

3. **Sample Addressing & Mode (Rows 11-13):**
   - Memory addresses: `Start: 0`, `Loop: 17888`, `End: 23125`.
   - `Orig Key: G#3`, `Mode: Forward`, `Length: Unlock`, `E.Mode: Mono`.

4. **88-Key Keyboard Widget (Rows 14-17):**
   - Shows active root key marker at `G#3`.

5. **Bottom Softkeys (Row 23-24):**
   - **F1:** `Smpling` — Initiates sampling workflow immediately.
   - **F2:** `MoveSet` — Adjusts sample assignment offset.
   - **F3:** `[ ]MIDISel` — Selects root key via incoming MIDI note.
   - **F4:** `Loop` — Jump directly to loop editor.
   - **F5:** `---` — Disabled placeholder.
