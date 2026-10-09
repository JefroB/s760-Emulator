# Roland S-760 CRT Display — Sample Mode Screens

This document covers all 15 screens within the **Sample** mode of the Roland S-760 hardware display (`sample-1.jpeg` through `sample-15.jpeg`). This mode encompasses the core audio acquisition, DSP editing, waveform inspection, looping, dynamic processing, and sample combination suite.

---

## 1. Screen sample-1: Sampling (Audio Recording & Input Setup)

- **Image File:** `d:\S-760\screenshots\sample-1.jpeg`
- **Active Mode Tab:** `Sample` (Highlighted white with red/orange text)
- **Screen Title:** `Sampling`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | ---/---`
- **Subheader Right Buttons:** `[Sampl]  Mark  Jump  Com`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Sampling                                                      [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Mode        : [ Stereo   ]   Orig Key : [ C_4  ]   Freq : [ 44.1KHz ]   Time : [  0.6sec ]    |
| Pre-Trig    : [   ---    ]   Normalize: [ Off  ]   Input: [ Analog  ]   Type : [ OneWay  ]    |
| Trigger     : [ Level    ]   Threshold: [   0  ]   Digital ATT : [   0 dB ]                   |
+-----------------------------------------------------------------------------------------------+
| Input Equalizer (2-Band Parametric):                                                          |
| Channel       | H.Freq  | H.Gain | L.Freq  | L.Gain                                           |
|---------------+---------+--------+---------+--------                                          |
| Input - Left  |  6.0K   |   0    |  120Hz  |   0                                              |
| Input - Right |  6.0K   |   0    |  120Hz  |   0                                              |
+-----------------------------------------------------------------------------------------------+
| Input Level Peak Meters:                                                                      |
| LEFT  : [ -inf  -40   -24   -12   -6   -3    0dB ] [|||||||||||||||||||||||                 ] |
| RIGHT : [ -inf  -40   -24   -12   -6   -3    0dB ] [|||||||||||||||||||||||                 ] |
+-----------------------------------------------------------------------------------------------+
| New            [ ]MonOn     Ready         ---           ---                                   |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
1. **Acquisition Parameters (Rows 4-6):**
   - `Mode`: Stereo / Mono.
   - `Orig Key`: Base pitch root key (`C_4`).
   - `Freq`: Sample rate (`48KHz`, `44.1KHz`, `32KHz`, `24KHz`, `22.05KHz`, `16KHz`).
   - `Time`: Buffer recording duration (`0.6sec`).
   - `Pre-Trig`: Pre-trigger buffer size.
   - `Normalize`: Auto-normalization upon capture (`Off`, `On`).
   - `Input`: Source selection (`Analog`, `Digital`).
   - `Type`: Recording type (`OneWay`, `Manual`).
   - `Trigger`: Trigger mode (`Level`, `Manual`, `MIDI`).
   - `Threshold`: Audio detection threshold level (`0` to `127`).
   - `Digital ATT`: Digital input attenuation (`0 dB` to `-24 dB`).
2. **Input Equalizer Table (Rows 7-12):**
   - Independent 2-band EQ for Left and Right analog inputs: High Frequency (`6.0K`), High Gain (`0 dB`), Low Frequency (`120Hz`), Low Gain (`0 dB`).
3. **Dual Peak Meters (Rows 13-16):**
   - Calibrated horizontal stereo bargraph meters in cyan with peak hold ticks.
4. **Bottom Softkeys (Row 23-24):**
   - **F1:** `New` — Allocate fresh sample slot.
   - **F2:** `[ ]MonOn` — Audio input monitor pass-through toggle.
   - **F3:** `Ready` — Arms trigger detection for recording.
   - **F4-F5:** `---` — Disabled placeholders.

---

## 2. Screen sample-2: Loop & Smoothing (Waveform Looping & Splice Zoom)

- **Image File:** `d:\S-760\screenshots\sample-2.jpeg`
- **Screen Title:** `Loop&Smoothing`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | Point/---                                            |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Loop&Smoothing              Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| [ 1] PNO:MP-1.                 Orig Key: G#3      Rate: 48KHz                                 |
| Start : [         0 ]   Loop : [     17888 ]   End : [     23125 ]                            |
| R-Loop: [     27618 ]   End  : [     27622 ]   Mode: [ Forward   ]   Fine Tune: [   0 ]       |
| Loop-Smoothing Length : [   1 ]                R-Loop-Smoothing Length: [   1 ]               |
+-----------------------------------------------------------------------------------------------+
| Tier 1: [================ Cyan Loop Boundary Bar ================]    | [ ---  ]              |
| Tier 2: +------------------------------------------------------------+ | [ Fast ]             |
|         | ~~~~/\~~~\_/\_/\___/\_/\_/\/\/\/\/\_______________________ | | [Point]              |
|         +------------------------------------------------------------+ | [X:---]              |
| Tier 3: +------------------------------------------------------------+ | [Y:---]              |
| (Zoom)  |                                                            | | [L:---]              |
|         +------------------------------------------------------------+ | W.Graph              |
+-----------------------------------------------------------------------------------------------+
| Mono           [ ]KeyStr    [ ]L.Unlk     Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
1. **Loop Addressing & Smoothing Controls (Rows 4-8):**
   - `Start: 0`, `Loop: 17888`, `End: 23125`.
   - `R-Loop: 27618`, `End: 27622`, `Mode: Forward`, `Fine Tune: 0`.
   - `Loop-Smoothing Length: 1` (Crossfade loop smoothing sample count).
   - `R-Loop-Smoothing Length: 1` (Release loop smoothing length).
2. **3-Tier Waveform Display (Rows 9-17):**
   - Tier 1: Selection overview bar with cyan loop bracket.
   - Tier 2: Oscilloscope full waveform view with center zero-line.
   - Tier 3: High-magnification zero-crossing loop splice inspection box.
   - Right Sidebar: Speed toggle `[ Fast ]`, crosshair `[Point]`, coordinate readouts `X`, `Y`, `L`, and `W.Graph` action button.
3. **Bottom Softkeys (Row 23-24):**
   - **F1:** `Mono` — Monophonic preview.
   - **F2:** `[ ]KeyStr` — Key-strike preview trigger toggle.
   - **F3:** `[ ]L.Unlk` — Loop address unlock toggle.
   - **F4:** `Recover` — Restores previous buffer state before execution.
   - **F5:** `Exec` — Executes loop crossfade smoothing.

---

## 3. Screen sample-3: Auto Truncate / Normalize

- **Image File:** `d:\S-760\screenshots\sample-3.jpeg`
- **Screen Title:** `Auto Trun/Norm`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Auto Trun/Norm                                                [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Mode: [ Truncate-Normalize ]   Fade: [ On ]                    Remaining: [ 341.6sec ]        |
+-----------------------------------------------------------------------------------------------+
| No.| Sample Name      | Time   || No.| Sample Name      | Time   || No.| Sample Name    | Time|
|----+------------------+--------||----+------------------+--------||----+----------------+-----|
|  1 | PNO:MP-1.        |  0.6s  ||  7 | PNO:MP-7.        |  0.8s  || 13 | PNO:FF-5.      | 1.1s|
|  2 | PNO:MP-2.        |  0.6s  ||  8 | PNO:MP-8.        |  0.9s  || 14 | PNO:FF-6.      | 1.0s|
|  3 | PNO:MP-3.        |  0.7s  ||  9 | PNO:FF-1.        |  1.0s  || 15 | PNO:FF-7.      | 0.9s|
|  4 | PNO:MP-4.        |  0.7s  || 10 | PNO:FF-2.        |  1.1s  || 16 | PNO:FF-8.      | 1.0s|
|  5 | PNO:MP-5.        |  0.8s  || 11 | PNO:FF-3.        |  1.2s  ||    |                |     |
|  6 | PNO:MP-6.        |  0.8s  || 12 | PNO:FF-4.        |  1.2s  ||    |                |     |
+-----------------------------------------------------------------------------------------------+
| [ ]AllOn       ---          ---           ---           Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
1. **Batch Mode Parameters (Row 4):**
   - `Mode`: Operation (`Truncate-Normalize`, `Truncate Only`, `Normalize Only`).
   - `Fade`: Boundary micro-fade (`On`, `Off`).
   - `Remaining`: Available sample RAM capacity (`341.6sec`).
2. **Multi-Column Sample Selection Grid (Rows 5-15):**
   - 16 selectable sample slots with sample number, name, and duration.
3. **Bottom Softkeys (Row 23-24):**
   - **F1:** `[ ]AllOn` — Selects all samples for batch processing.
   - **F2-F4:** `---` — Disabled placeholders.
   - **F5:** `Exec` — Executes batch truncate and normalization.

---

## 4. Screen sample-4: Time Stretch

- **Image File:** `d:\S-760\screenshots\sample-4.jpeg`
- **Screen Title:** `Time Stretch`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Time Stretch                Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| [ 1] PNO:MP-1.                 Orig Key: G#3      Rate: 48KHz                                 |
| From  : [         0 ] [ ST ]   To: [     23125 ] [ End ]   Length: 23125 (0.481s)             |
| Cor   : [         0 ]          Fin: [        0 ]           Total : 27648 (0.576s)             |
| Ratio : [       100 % ]        Fade: [      20 ]           Mode  : [ Manual   ]               |
+-----------------------------------------------------------------------------------------------+
| Tier 1: [================ Cyan Boundary Selection Track ==========]                          |
| Tier 2: +-----------------------------------------------------------------------------------+ |
|         | ~~~/\~~~/\_/\___/\/\/\/\/\______________________________________________________ | |
|         +-----------------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------+
| Search         [ ]KeyStr    ---           Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
1. **Time Stretch Parameters (Rows 4-8):**
   - `From: 0 [ST]`, `To: 23125 [End]`.
   - `Length: 23125 (0.481s)` (Original duration).
   - `Ratio: 100%` (Time stretch ratio from 50% to 200%).
   - `Fade: 20` (Granular overlap crossfade duration).
   - `Mode: Manual` / `Auto`.
2. **Waveform Overview & Detail View (Rows 9-16):**
   - Cyan boundary bar and full sample envelope graph.
3. **Bottom Softkeys (Row 23-24):**
   - **F1:** `Search` — Auto-detects optimal pitch-synchronous stretch blocks.
   - **F2:** `[ ]KeyStr` — Key-strike preview.
   - **F3:** `---` — Disabled placeholder.
   - **F4:** `Recover` — Undo previous stretch operation.
   - **F5:** `Exec` — Executes offline DSP time stretching.

---

## 5. Screen sample-5: Digital Filter (D.Filter)

- **Image File:** `d:\S-760\screenshots\sample-5.jpeg`
- **Screen Title:** `D.Filter`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| D.Filter                    Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| [ 1] PNO:MP-1.                 Orig Key: G#3      Rate: 48KHz                                 |
| Filter Mode : [ LPF ]          Cutoff Freq : [ 10.0 kHz ]                                     |
| Resonance   : [   0 ]          Level       : [  127     ]                                     |
+-----------------------------------------------------------------------------------------------+
| Tier 1: [================ Full Sample Selection Bar ==============]                          |
| Tier 2: +-----------------------------------------------------------------------------------+ |
|         | ~~~~/\~~~\_/\_/\___/\_/\_/\/\/\/\/\______________________________________________ | |
|         +-----------------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------+
| ---            ---          ---           Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
1. **Filter DSP Parameters (Rows 4-7):**
   - `Filter Mode: LPF` (Destructive digital offline filter: `LPF`, `HPF`, `BPF`).
   - `Cutoff Freq: 10.0 kHz`.
   - `Resonance: 0` (0 to 127).
   - `Level: 127` (Post-filter gain).
2. **Full-Width Waveform Display (Rows 8-15):**
   - Large oscilloscope window rendering the audio waveform.
3. **Bottom Softkeys (Row 23-24):**
   - **F1-F3:** `---` — Disabled placeholders.
   - **F4:** `Recover` — Restores audio buffer before filtering.
   - **F5:** `Exec` — Computes digital filtering pass on RAM sample data.

---

## 6. Screen sample-6: Compressor / Expander (Comp/Expand)

- **Image File:** `d:\S-760\screenshots\sample-6.jpeg`
- **Screen Title:** `Comp/Expand`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Comp/Expand                 Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| [ 1] PNO:MP-1.                 Orig Key: G#3      Rate: 48KHz                                 |
| Threshold : [  50 % ]          Ratio       : [ 100 % ]          Level : [ 100 % ]             |
| Attack    : [   0   ]          Release     : [   0   ]          Normalize: [ Off ]            |
+-----------------------------------------------------------------------------------------------+
| Waveform Envelope View:                       | Compression Transfer Characteristic Curve:    |
| +-------------------------------------------+ | +-------------------------------------------+ |
| | ~~~/\~~~/\_/\/\/\/\______________________ | | |                                         / | |
| |                                           | | |                                       /   | |
| |                                           | | |                                     /     | |
| |                                           | | |                         ___________/      | |
| +-------------------------------------------+ | +-------------------------------------------+ |
+-----------------------------------------------------------------------------------------------+
| ---            ---          ---           Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
1. **Dynamics DSP Parameters (Rows 4-7):**
   - `Threshold: 50%`, `Ratio: 100%`, `Level: 100%`.
   - `Attack: 0`, `Release: 0`, `Normalize: Off`.
2. **Dual Graphical Visualization Windows (Rows 8-16):**
   - Left Window: Audio waveform envelope display.
   - Right Window: Input-to-output compression curve graph showing knee and compression ratio slope.
3. **Bottom Softkeys (Row 23-24):**
   - **F4:** `Recover` — Undo.
   - **F5:** `Exec` — Render dynamic processing.

---

## 7. Screen sample-7: Sampling Rate Converter (Rate Convert)

- **Image File:** `d:\S-760\screenshots\sample-7.jpeg`
- **Screen Title:** `Rate Convert`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Rate Convert                Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| [ 1] PNO:MP-1.                 Orig Key: G#3      Rate: 48KHz                                 |
| Sampling Rate  : [ 48KHz ] ===> [ 15KHz  ]                                                    |
| Coarse Tune    : [ ***   ] ===> [   0    ]                                                    |
| Fine Tune      : [ ***   ] ===> [   0    ]                                                    |
| Sample Length  : [ 0.6sec] ===> [ 0.2sec ]                                                    |
+-----------------------------------------------------------------------------------------------+
| Tier 1: [================ Waveform Overview Bar ===================]                          |
| Tier 2: +-----------------------------------------------------------------------------------+ |
|         | ~~~~/\~~~\_/\_/\___/\_/\_/\/\/\/\/\______________________________________________ | |
|         +-----------------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------+
| Correct        ---          ---           Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
1. **Sample Rate Conversion Parameters (Rows 4-9):**
   - Source vs Destination transformation readouts:
     - Rate: `48KHz` -> `15KHz`.
     - Coarse Tune: `[***]` -> `0`.
     - Fine Tune: `[***]` -> `0`.
     - Resulting Memory Duration: `0.6sec` -> `0.2sec` (Significant RAM savings).
2. **Waveform Display (Rows 10-16):**
   - Visual waveform tracking before/after conversion.
3. **Bottom Softkeys (Row 23-24):**
   - **F1:** `Correct` — Auto-calculates pitch and tuning offsets to preserve original musical pitch.
   - **F4:** `Recover` — Restores previous buffer.
   - **F5:** `Exec` — Computes anti-aliasing resampling.

---

## 8. Screen sample-8: Bit Convert

- **Image File:** `d:\S-760\screenshots\sample-8.jpeg`
- **Screen Title:** `Bit Convert`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Bit Convert                 Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| [ 1] PNO:MP-1.                 Orig Key: G#3      Rate: 48KHz                                 |
| From : [         0 ] [ Start ]       To : [     23125 ] [ End ]                               |
| Bit  : [ Off       ]                 Skip Address : [ Off       ]                             |
+-----------------------------------------------------------------------------------------------+
| 3-Tier Waveform Inspection Display:                                                           |
| Tier 1: Selection overview track.                                                             |
| Tier 2: Full waveform display box.                                                            |
| Tier 3: Zoom box.                                                                             |
+-----------------------------------------------------------------------------------------------+
| ---            [ ]KeyStr    ---           Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- Re-quantizes audio resolution (e.g., bit reduction / lo-fi crunchy effects or data compaction) across the selected address range `From: 0` to `To: 23125`.
- `Skip Address`: Skips downsampling for transient attacks.

---

## 9. Screen sample-9: Truncate

- **Image File:** `d:\S-760\screenshots\sample-9.jpeg`
- **Screen Title:** `Truncate`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Truncate                    Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| [ 1] PNO:MP-1.                 Orig Key: G#3      Rate: 48KHz                                 |
| From : [         0 ] [ Start ]       -Fade : [   0 ]                                          |
| To   : [     23125 ] [ End   ]       -Fade : [   0 ]           [New Length: 0.6sec]           |
+-----------------------------------------------------------------------------------------------+
| 3-Tier Waveform Inspection Display:                                                           |
| Shows cyan boundary bracket highlighting audio to retain; discarded heads/tails are unselected|
+-----------------------------------------------------------------------------------------------+
| ---            [ ]KeyStr    ---           Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- Truncates audio data before `From` and after `To`, freeing unused sample memory.
- `-Fade`: Micro-fade smoothing length to prevent clicks at cut boundaries.

---

## 10. Screen sample-10: Cut & Splice

- **Image File:** `d:\S-760\screenshots\sample-10.jpeg`
- **Screen Title:** `Cut & Splice`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Cut & Splice                Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| [ 1] PNO:MP-1.                 Orig Key: G#3      Rate: 48KHz                                 |
| From : [         0 ] [ Start ]       To : [     23125 ] [ End ]        Fade: [   0 ]          |
+-----------------------------------------------------------------------------------------------+
| 3-Tier Waveform Inspection Display                                                            |
+-----------------------------------------------------------------------------------------------+
| ---            [ ]KeyStr    ---           Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- Removes an internal section between `From` and `To` and splices the surrounding segments together with crossfade smoothing (`Fade: 0`).

---

## 11. Screen sample-11: Area Erase

- **Image File:** `d:\S-760\screenshots\sample-11.jpeg`
- **Screen Title:** `Area Erase`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | Point/---`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | Point/---                                            |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Area Erase                  Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| [ 1] PNO:MP-1.                 Length: 0.6sec / 341.6sec       Orig Key: G#3   Rate: 48KHz    |
| -> From : [         0 ] [ Start ]     -Fade: [   0 ]                                          |
| -> To   : [     23125 ] [ End   ]     -Fade: [   0 ]                                          |
+-----------------------------------------------------------------------------------------------+
| Tier 1: [================ Cyan Highlight Selection Bar ============]  | [ ---  ]              |
| Tier 2: +------------------------------------------------------------+ | [ Fast ]             |
|         | ~~~~/\~~~\_/\_/\___/\_/\_/\/\/\/\/\_______________________ | | [X:---]              |
|         +------------------------------------------------------------+ | [Y:---]              |
| Tier 3: +------------------------------------------------------------+ | [L:---]              |
|         |                                                            | | W.Graph              |
|         +------------------------------------------------------------+ |                      |
+-----------------------------------------------------------------------------------------------+
| ---            [ ]KeyStr    ---           Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- Erases audio within the selected range (`From` to `To`) by replacing it with silence, without altering the sample length.

---

## 12. Screen sample-12: Insert

- **Image File:** `d:\S-760\screenshots\sample-12.jpeg`
- **Screen Title:** `Insert`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | Mark/Area`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | Mark/Area                                            |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Insert                      Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Destin  : [ 1] PNO:MP-1.                     Remaining: 341.6sec              48KHz           |
| Source1 : [ 1] PNO:MP-1.                                                      48KHz           |
|   -> From: [     0 ] [ ST ]   -Fade: [ 0 ]                                                    |
|   -> To  : [ 23125 ] [ End]   -Fade: [ 0 ]                                                    |
|   Level  : [   127 ]                                                                          |
| Source2 : [ 1] PNO:MP-1.                                                      48KHz           |
|   -> From: [     0 ] [ ST ]                                                                   |
|   -> To  : [ 23125 ] [ End]                                                                   |
|   Level  : [   127 ]                                                                          |
+-----------------------------------------------------------------------------------------------+
| Dual Waveform Inspection Tracks (Source 1 & Source 2)                                         |
+-----------------------------------------------------------------------------------------------+
| ---            [ ]KeyStr    ---           Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- Inserts audio from `Source2` into `Source1` at a specified insertion point to create `Destin`.

---

## 13. Screen sample-13: Mixing

- **Image File:** `d:\S-760\screenshots\sample-13.jpeg`
- **Screen Title:** `Mixing`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | Mark/Area`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | Mark/Area                                            |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Mixing                      Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Destin  : [ 1] PNO:MP-1.                     Remaining: 341.6sec              48KHz           |
| Source1 : [ 1] PNO:MP-1.                                                      48KHz           |
|   -> From: [     0 ] [ ST ]   -Fade: [ 0 ]                                                    |
|   -> To  : [ 23125 ] [ End]   -Fade: [ 0 ]                                                    |
|   Level  : [   127 ]                                                                          |
| Source2 : [ 1] PNO:MP-1.                                                      48KHz           |
|   -> From: [     0 ] [ ST ]   -Fade: [ 0 ]                                                    |
|   -> To  : [ 23125 ] [ End]   -Fade: [ 0 ]                                                    |
|   Level  : [   127 ]          delay: [ 0 ]                                                    |
+-----------------------------------------------------------------------------------------------+
| Dual Waveform Inspection Tracks                                                               |
+-----------------------------------------------------------------------------------------------+
| ---            [ ]KeyStr    ---           Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- Blends/mixes two audio sources together (`Source1` and `Source2`) into a single new sample with independent levels and optional delay offset (`delay: 0`).

---

## 14. Screen sample-14: Combine (Parameter Setup)

- **Image File:** `d:\S-760\screenshots\sample-14.jpeg`
- **Screen Title:** `Combine`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | Mark/Area`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | Mark/Area                                            |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Combine                     Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Destin  : [ 1] PNO:MP-1.                     Remaining: 341.6sec              48KHz           |
| Source1 : [ 1] PNO:MP-1.                                                      48KHz           |
|   -> To  : [ 23125 ] [ End]   -Fade: [ 0 ]                                                    |
|   Level  : [   127 ]                                                                          |
| Source2 : [ 1] PNO:MP-1.                                                      48KHz           |
|   -> From: [     0 ] [ ST ]                                                   48KHz           |
|   Level  : [   127 ]                                                                          |
+-----------------------------------------------------------------------------------------------+
| Dual Waveform Display Bars for Source1 and Source2                                            |
+-----------------------------------------------------------------------------------------------+
| ---            [ ]KeyStr    ---           Recover       Exec                                  |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- Appends `Source2` directly onto the end of `Source1` with boundary crossfade (`-Fade: 0`) to concatenate samples.

---

## 15. Screen sample-15: Combine (Waveform Editing View)

- **Image File:** `d:\S-760\screenshots\sample-15.jpeg`
- **Screen Title:** `Combine`
- **Top Banner:** `Volume[ -  :                  ]  ID:01 | ---/---`
- **Subheader Center Badge:** `Samp1`

```
+-----------------------------------------------------------------------------------------------+
| Volume[ -  :                  ]  ID:01 | ---/---                                              |
| Perform | Patch | Partial | [ SAMPLE ] | Disk | System                                        |
| Combine                     Samp1                             [Sampl]  Mark  Jump  Com        |
+-----------------------------------------------------------------------------------------------+
| Target Source1                                                                                |
| Tier 1: [================ Selection Bar ==========================]   | [ ---  ]              |
| Tier 2: +------------------------------------------------------------+                        |
|         | ~~~~/\~~~\_/\_/\___/\_/\_/\/\/\/\/\_______________________ |                        |
|         +------------------------------------------------------------+                        |
| [ To ]: [ 23125 ]     D: [ 1892 ]                                                             |
| Tier 3: +------------------------------------------------------------+                        |
| (Zoom)  |                                                            |                        |
|         +------------------------------------------------------------+                        |
+-----------------------------------------------------------------------------------------------+
| Zoom X: [ --- ]   Y: [ --- ]   L: [ --- ]                             | [ Fast ]              |
+-----------------------------------------------------------------------------------------------+
| ---            [ ]KeyStr    ---           ---           Param                                 |
+-----------------------------------------------------------------------------------------------+
```

### Detailed Element Breakdown
- Specialized graphical editing view for the Combine tool.
- Shows fine target splice boundary `[ To ]: 23125` with distance indicator `D: 1892`.
- Softkey **F5** switches back to the parameter screen: `Param`.
