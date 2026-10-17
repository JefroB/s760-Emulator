# Roland S-760 CRT Display — Partial Mode Screens

This document covers all screens within the **Partial** mode of the Roland S-760 hardware display (`partial-1.jpeg` through `partial-6.jpeg`), including Partial Common parameters, SMT velocity crossfades, TVF digital dynamic filters, TVA amplifier envelopes, LFO modulators, and Partial Quick Sampling.

---

## 1. Screen partial-1: Partial Common

- **Image File:** `d:\S-760\screenshots\partial-1.jpeg`
- **Active Mode Tab:** `Partial` (Highlighted white with red/orange text)
- **Screen Title:** `Partial Common`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | ---/---`
- **Subheader Center Badge:** `[ 1] PNO:Piano p/f AA`
- **Subheader Right Buttons:** `[Partl]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | [ PARTIAL ] | Sample | Disk | System                                        |
| Partial Common              [ 1] PNO:Piano p/f AA             [Partl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Used: 1.9sec                                                                                  |
| Partial Level     : [ 127 ]   |---|------------------|   (Range: 0 ~ 127)                     |
| Panning           : [   0 ]   |---------|------------|   (Range: -50 ~ +50)                   |
| Output Assign     : [   A ]                               (Options: A, B, C, D, 1~8)          |
+-----------------------------------------------------------------------------------------------+
| Coarse Tune       : [   0 ]   |---------|------------|   (Range: -24 ~ +24 semitones)         |
| Fine Tune         : [   0 ]   |---------|------------|   (Range: -50 ~ +50 cents)             |
| SMT Vel Ctrl      : [  On ]                               (Velocity Control Enable)           |
+-----------------------------------------------------------------------------------------------+
| ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| | | ||| | ||| |
| C1        C2        C3        C4        C5        C6        C7                                |
+-----------------------------------------------------------------------------------------------+
| [ ]Single      ---          ---           ---           ---                                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Header & Memory Readout (Rows 4-5):**
   - Active Partial: `[ 1] PNO:Piano p/f AA`.
   - Sample Memory Used: `Used: 1.9sec`.

2. **Mixing & Output Controls (Rows 6-8):**
   - **Partial Level:** Numerical value `[ 127 ]` with horizontal slider and downward red triangle cursor.
   - **Panning:** Value `[ 0 ]` with center-detented slider (`-50` L to `+50` R).
   - **Output Assign:** Selection `[ A ]` (`A`, `B`, `C`, `D`, `1` to `8`).

3. **Tuning & SMT Trigger (Rows 9-11):**
   - **Coarse Tune:** Value `[ 0 ]` with slider widget (`-24` to `+24`).
   - **Fine Tune:** Value `[ 0 ]` with slider widget (`-50` to `+50`).
   - **SMT Vel Ctrl:** Toggle `[ On ]` (`Off`, `On`).

4. **88-Key Keyboard Widget (Rows 12-15):**
   - Graphical keyboard rendering across screen width.

5. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]Single` — Solo audition toggle.
   - **F2-F5:** `---` — Disabled placeholders.

---

## 2. Screen partial-2: Partial SMT (Sample Mixing Table)

- **Image File:** `d:\S-760\screenshots\partial-2.jpeg`
- **Active Mode Tab:** `Partial`
- **Screen Title:** `Partial SMT`
- **Subheader Center Badge:** `[ 1] PNO:Piano p/f AA`
- **Subheader Right Buttons:** `[Partl]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | [ PARTIAL ] | Sample | Disk | System                                        |
| Partial SMT                 [ 1] PNO:Piano p/f AA             [Partl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Smp| Sample Name          | K.F | C.T | F.T | Pan |Ky+| Lev | Vel.L | Vel.H | Fade.L | Fade.H |
|----+----------------------+-----+-----+-----+-----+---+-----+-------+-------+--------+--------|
| [1]| 1 PNO:MP-1.          | Norm|  0  |  0  |  0  | + | 127 |   1   |   79  |    0   |   15   |
| [2]| 2 PNO:ff-1.          | Norm|  0  |  0  |  0  | + | 127 |  70   |  127  |   15   |    0   |
| [3]| --Off--              | --- | --- | --- | --- | - | --- |  ---  |  ---  |   ---  |   ---  |
| [4]| --Off--              | --- | --- | --- | --- | - | --- |  ---  |  ---  |   ---  |   ---  |
+-----------------------------------------------------------------------------------------------+
| SMT Velocity Crossfade Graphic Display:                                                       |
| Layer 1: [====================== Cyan Bar (1 to 79) ==========]                               |
| Layer 2:                [========== Orange Bar (70 to 127) =================================] |
| 0                      32                      64                      96                 127 |
+-----------------------------------------------------------------------------------------------+
| [ ]Single      [ ]Mono      ---           ---           ---                                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **4-Layer Sample Assignment Matrix (Rows 4-10):**
   - Columns:
     - `Smp` : Layer slot (`[1]` to `[4]`).
     - `Sample Name` : Assigned sample name (e.g. `1 PNO:MP-1.`, `2 PNO:ff-1.`).
     - `K.F` : Key Follow mode (`Norm`, `Hold`, `Fixed`).
     - `C.T` / `F.T` : Coarse Tune / Fine Tune.
     - `Pan` : Layer stereo pan.
     - `Ky+` : Key-to-pan tracking enable.
     - `Lev` : Layer playback level (0 to 127).
     - `Vel.L` / `Vel.H` : Velocity window lower/upper limits (1 to 127).
     - `Fade.L` / `Fade.H` : Crossfade smoothing depth at velocity window edges.

2. **SMT Velocity Crossfade Graphic Display (Rows 11-15):**
   - Dual horizontal color-coded bars:
     - Layer 1: Cyan bar spanning velocity values `1` through `79`.
     - Layer 2: Orange/yellow bar spanning velocity values `70` through `127`.
   - The overlapping region (`70` to `79`) indicates active dynamic crossfade.

3. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]Single` — Solo audition toggle.
   - **F2:** `[ ]Mono` — Monophonic playback trigger toggle.
   - **F3-F5:** `---` — Disabled placeholders.

---

## 3. Screen partial-3: Partial TVF (Time-Variant Filter)

- **Image File:** `d:\S-760\screenshots\partial-3.jpeg`
- **Active Mode Tab:** `Partial`
- **Screen Title:** `Partial TVF`
- **Subheader Center Badge:** `[ 1] PNO:Piano p/f AA`
- **Subheader Right Buttons:** `[Partl]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | [ PARTIAL ] | Sample | Disk | System                                        |
| Partial TVF                 [ 1] PNO:Piano p/f AA             [Partl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Filter Mode     : [ LPF ]     Cutoff Freq : [  37 ]   |---|------------------|   (0 ~ 127)    |
| Resonance       : [   0 ]     |---|------------------|                           (0 ~ 127)    |
| Cutoff KF       : [ -41 ]     |---------|------------|   KF Point: [ B_2 ]       (-63 ~ +63)  |
| Vel-Curve       : [   2 ]     Vel-Curve Sens : [ -32 ] |---------|------------|               |
+-----------------------------------------------------------------------------------------------+
| TVF Envelope Parameters:                                                                      |
| TVF Depth: [ 63 ]   Vel Sens: [ 48 ]   Pitch Depth: [  0 ]                                    |
| Time Vel Sens: [  0 ]   Key Follow: [ 32 ]   R.Velo Sens: [  0 ]                              |
+-----------------------------------------------------------------------------------------------+
| Stage | Time | Level |  TVF Graphic Envelope Curve:                                           |
|-------+------+-------|   +-----------------------------------------------------+              |
|   1   |   0  |  127  |   |*                                                    |              |
|   2   |  74  |   45  |   | \                                                   |              |
|   3   | 102  |    0  |   |   \*-------.                                        |              |
|   4   | 127  |    0  |   |             \_______________________________        |              |
|       |      |       |   +-----------------------------------------------------+              |
+-----------------------------------------------------------------------------------------------+
| [ ]Single      ---          ---           ---           ---                                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Filter Parameters (Rows 4-7):**
   - **Filter Mode:** Dropdown `[ LPF ]` (`Off`, `LPF` [Low Pass], `BPF` [Band Pass], `HPF` [High Pass]).
   - **Cutoff Freq:** Value `[ 37 ]` with slider widget (`0` to `127`).
   - **Resonance:** Value `[ 0 ]` with slider widget (`0` to `127`).
   - **Cutoff KF:** Key follow value `[ -41 ]` with slider widget (`-63` to `+63`).
   - **KF Point:** Pivot note `[ B_2 ]`.
   - **Vel-Curve & Sens:** Curve shape `[ 2 ]` and sensitivity `[ -32 ]` with slider.

2. **TVF Envelope Modulation (Rows 8-10):**
   - `TVF Depth: 63`, `Vel Sens: 48`, `Pitch Depth: 0`.
   - `Time Vel Sens: 0`, `Key Follow: 32`, `R.Velo Sens: 0`.

3. **4-Stage Envelope Table & Graphic Curve (Rows 11-17):**
   - 4 Envelope Stages:
     - Stage 1: Time `0`, Level `127` (Instant attack).
     - Stage 2: Time `74`, Level `45` (Initial decay).
     - Stage 3: Time `102`, Level `0` (Second decay down to sustain).
     - Stage 4: Time `127`, Level `0` (Final release).
   - Graphical vector envelope display with cyan nodes and green release boundary line.

4. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]Single` — Solo toggle.
   - **F2-F5:** `---` — Disabled placeholders.

---

## 4. Screen partial-4: Partial TVA (Time-Variant Amplifier)

- **Image File:** `d:\S-760\screenshots\partial-4.jpeg`
- **Active Mode Tab:** `Partial`
- **Screen Title:** `Partial TVA`
- **Subheader Center Badge:** `[ 1] PNO:Piano p/f AA`
- **Subheader Right Buttons:** `[Partl]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | [ PARTIAL ] | Sample | Disk | System                                        |
| Partial TVA                 [ 1] PNO:Piano p/f AA             [Partl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Vel-Curve       : [   2 ]     Vel-Curve Sens : [   0 ] |---------|------------|               |
| Level KF        : [   0 ]     |---------|------------|   KF Point: [ B_2 ]                    |
| Time Vel Sens   : [   0 ]     Key Follow: [ 32 ]         R.Velo Sens: [   0 ]                 |
+-----------------------------------------------------------------------------------------------+
| Stage | Time | Level |  TVA Graphic Amplitude Envelope Curve:                                 |
|-------+------+-------|   +-----------------------------------------------------+              |
|   1   |   0  |  127  |   |*                                                    |              |
|   2   | 127  |  125  |   | \___________                                        |              |
|   3   |  99  |    0  |   |             \                                       |              |
|   4   |  20  |  ---  |   |              \______________________________        |              |
|       |      |       |   +-----------------------------------------------------+              |
+-----------------------------------------------------------------------------------------------+
| [ ]Single      ---          ---           ---           ---                                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Velocity & Tracking Controls (Rows 4-6):**
   - **Vel-Curve / Sens:** Curve shape `[ 2 ]` and sensitivity `[ 0 ]` with slider.
   - **Level KF:** Level Key Follow `[ 0 ]` with slider (`-63` to `+63`). Pivot note `[ B_2 ]`.
   - **Envelope Time Tracking:** `Time Vel Sens: 0`, `Key Follow: 32`, `R.Velo Sens: 0`.

2. **4-Stage TVA Amplitude Table & Graphic Curve (Rows 7-14):**
   - Stages:
     - Stage 1: Time `0`, Level `127` (Immediate transient attack).
     - Stage 2: Time `127`, Level `125` (Extended acoustic sustain).
     - Stage 3: Time `99`, Level `0` (Decay to silence).
     - Stage 4: Time `20`, Level `---` (Key-off release time).
   - Graphic display of acoustic decay envelope curve.

3. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]Single` — Solo toggle.
   - **F2-F5:** `---` — Disabled placeholders.

---

## 5. Screen partial-5: Partial LFO (Low Frequency Oscillator)

- **Image File:** `d:\S-760\screenshots\partial-5.jpeg`
- **Active Mode Tab:** `Partial`
- **Screen Title:** `Partial LFO`
- **Subheader Center Badge:** `[ 1] PNO:Piano p/f AA`
- **Subheader Right Buttons:** `[Partl]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | [ PARTIAL ] | Sample | Disk | System                                        |
| Partial LFO                 [ 1] PNO:Piano p/f AA             [Partl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Waveform          : [ Sin ]   (Options: Sin, Tri, SwUP, SwDW, Squ, Rnd, B.UP, B.DW)          |
| Rate              : [  88 ]   |---|------------------|   (Range: 0 ~ 127)                     |
| Detune            : [   0 ]   |---------|------------|   (Range: -50 ~ +50)                   |
| Delay             : [   0 ]   |---|------------------|   (Range: 0 ~ 127)                     |
| Key Follow        : [   0 ]   |---------|------------|   (Range: -63 ~ +63)                   |
| Key Sync          : [  On ]   (Options: Off, On)                                              |
+-----------------------------------------------------------------------------------------------+
| Modulation Depths:                                                                            |
| Pitch Depth       : [   0 ]   |---|------------------|   (Vibrato: 0 ~ 127)                   |
| TVF Depth         : [   0 ]   |---|------------------|   (Filter Wah: 0 ~ 127)                |
| TVA Depth         : [   0 ]   |---|------------------|   (Tremolo: 0 ~ 127)                   |
| PAN Depth         : [   0 ]   |---|------------------|   (Auto-Pan: 0 ~ 127)                  |
+-----------------------------------------------------------------------------------------------+
| [ ]Single      ---          ---           ---           ---                                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Oscillator Waveform & Timing (Rows 4-9):**
   - **Waveform:** Dropdown `[ Sin ]` (`Sin` [Sine], `Tri` [Triangle], `SwUP` [Saw Up], `SwDW` [Saw Down], `Squ` [Square], `Rnd` [Random], `B.UP` [Bend Up], `B.DW` [Bend Down]).
   - **Rate:** Value `[ 88 ]` with slider widget (`0` to `127`).
   - **Detune:** Value `[ 0 ]` with slider widget (`-50` to `+50`).
   - **Delay:** Value `[ 0 ]` with slider widget (`0` to `127`).
   - **Key Follow:** Value `[ 0 ]` with slider widget (`-63` to `+63`).
   - **Key Sync:** Toggle `[ On ]` (`Off`, `On`).

2. **Destination Modulation Depths (Rows 10-15):**
   - **Pitch Depth:** Vibrato intensity `[ 0 ]` with slider.
   - **TVF Depth:** Filter cutoff modulation `[ 0 ]` with slider.
   - **TVA Depth:** Tremolo amplitude modulation `[ 0 ]` with slider.
   - **PAN Depth:** Auto-panning stereo modulation `[ 0 ]` with slider.

3. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]Single` — Solo toggle.
   - **F2-F5:** `---` — Disabled placeholders.

---

## 6. Screen partial-6: Partial Q-Sampling (Quick Sampling)

- **Image File:** `d:\S-760\screenshots\partial-6.jpeg`
- **Active Mode Tab:** `Partial`
- **Screen Title:** `Partial Q-Sampling`
- **Subheader Center Badge:** `[ 1] PNO:Piano p/f AA`
- **Subheader Right Buttons:** `[Partl]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | [ PARTIAL ] | Sample | Disk | System                                        |
| Partial Q-Sampling          [ 1] PNO:Piano p/f AA             [Partl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Smp| Sample Name          | Time   | Orig Key | Loop Mode | Length Mode                       |
|----+----------------------+--------+----------+-----------+-----------------------------------|
| [1]| 1 PNO:MP-1.          | 0.6sec |   G#3    | Forward   | Unlock                            |
| [2]| 2 PNO:ff-1.          | 1.3sec |   G#3    | Forward   | Unlock                            |
| [3]| --Off--              | ------ |   ---    | ---       | ---                               |
| [4]| --Off--              | ------ |   ---    | ---       | ---                               |
+-----------------------------------------------------------------------------------------------+
| Pitch Parameters       | TVF Parameters          | TVA Parameters                             |
|------------------------+-------------------------+--------------------------------------------|
| Key Follow : Normal    | Filter Mode : LPF       | Level   : 127                              |
| Coarse     : 0         | Cutoff Freq :  37       | Release :  20                              |
| Fine       : 7         | Resonance   :   0       | Velo-Crv: 2./                              |
+-----------------------------------------------------------------------------------------------+
| Sample Addresses:                                                                             |
| Start : [         0 ]   Loop : [     17888 ]   End : [     23125 ]                            |
| Orig Key : [ G#3 ]      Length : [ Unlock   ]  E.Mode : [ Mono     ]                          |
+-----------------------------------------------------------------------------------------------+
| Smpling        ---          ---           Loop          ---                                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown

1. **Assigned Samples Overview (Rows 4-10):**
   - Shows duration, root key, and playback loop configuration for all 4 partial sample layers.

2. **Synthesis Summary (Rows 11-15):**
   - Direct access to pitch, filter, and amplifier parameters.

3. **Sample Address Readouts (Rows 16-19):**
   - Exact sample memory address locations (`Start: 0`, `Loop: 17888`, `End: 23125`).

4. **Bottom Softkeys (Row 23-24):**
   - **F1:** `Smpling` — Sampling launch trigger.
   - **F2-F3:** `---` — Disabled placeholders.
   - **F4:** `Loop` — Jump to `Loop&Smoothing` editor.
   - **F5:** `---` — Disabled placeholder.
