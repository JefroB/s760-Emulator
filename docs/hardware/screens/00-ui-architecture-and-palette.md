# Roland S-760 CRT Display — UI Architecture & Design System Reference

This document defines the visual design system, frame architecture, color palette, typography, coordinate grid, and reusable interactive widget components observed across the Roland S-760 hardware display screenshots (OP-760-1 / OP-760-2 video output connected to a CRT monitor).

---

## 1. Screen Architecture & Coordinate Grid

The Roland S-760 video system outputs a 640x400 / 640x480 raster image with a standard 80-column text / graphic overlay grid.

```
+-----------------------------------------------------------------------------------------------+
| Row 1: Volume / Global Context Banner (Forest Green background #008800)                      |
+-----------------------------------------------------------------------------------------------+
| Row 2: Mode Navigation Bar (Light Gray / White background)                                   |
| [ Perform ]  [  Patch  ]  [ Partial ]  [  Sample  ]  [  Disk  ]  [ System ]                  |
+-----------------------------------------------------------------------------------------------+
| Row 3: Subheader & Mode Actions (Cobalt Blue / Section-dependent)                            |
| Screen Title         Active Context Tag          [Pform/Mode]  [Mark]  [Jump]  [Com]          |
+-----------------------------------------------------------------------------------------------+
| Rows 4-22: Content Workspace Area (Solid Cobalt Blue background #0000AA)                      |
|                                                                                               |
|  * Parameter Tables & Data Fields (Yellow & Cyan Section Headers)                             |
|  * Graphic Widgets (Sliders, Envelopes, Waveform Displays, 88-Key Piano Keyboard)             |
|  * Modal Overlays & Action Popups                                                             |
|                                                                                               |
+-----------------------------------------------------------------------------------------------+
| Row 23-24: Softkey Toolbar (Row of 5 Cyan Action Buttons)                                     |
| [   F1   ]     [   F2   ]     [   F3   ]     [   F4   ]     [   F5   ]  |  [ VolInfo / Status ] |
+-----------------------------------------------------------------------------------------------+
```

### Zone Coordinates & Spacing
- **Total Resolution:** 640 x 400 (or 640 x 480 60Hz VGA timing, active area 640x400).
- **Global Banner (Row 1):** Y: 0 to ~16 px. Height: ~16 px. Full screen width (640 px).
- **Mode Bar (Row 2):** Y: 17 to ~34 px. Height: ~18 px. Six primary tab segments.
- **Subheader (Row 3):** Y: 35 to ~52 px. Height: ~18 px. Screen name left-aligned; breadcrumb / channel center; top right buttons.
- **Workspace Canvas:** Y: 53 to ~360 px. Height: ~308 px.
- **Softkey Toolbar:** Y: 365 to ~395 px. Height: ~30 px. 5 softkey boxes + optional VolInfo right button.

---

## 2. Color Palette System

The hardware palette relies on high-contrast 16-color digital RGB levels:

| Role | Hex Color | Visual Appearance | Usage |
| :--- | :--- | :--- | :--- |
| **Workspace Background** | `#0000AA` | Saturated Cobalt Blue | Main background behind all workspace elements, tables, and graphs. |
| **Global Banner BG** | `#008800` | Forest Green | Topmost status strip (Volume, SCSI ID, context controls). |
| **Active Mode Tab BG** | `#FFFFFF` | Solid White Box | Highlights the currently active mode tab in Row 2. |
| **Inactive Mode Tab BG**| `#B0B0B0` | Light Gray Box | Inactive mode tabs in Row 2. |
| **Active Mode Text** | `#D03000` | Bright Orange/Red | Text inside the active mode tab. |
| **Inactive Mode Text** | `#000000` | Pitch Black | Text inside inactive tabs and yellow/cyan header banners. |
| **Primary Header BG** | `#FFFF00` | Bright Solid Yellow | Primary parameter table banners and section title strips. |
| **Secondary Header BG**| `#00FFFF` | Bright Solid Cyan | Sub-tables, secondary lists, stereo channel headers, softkey buttons. |
| **Primary Labels** | `#00FFFF` | Bright Cyan | Field titles, group labels, units, and non-editable labels on blue background. |
| **Editable Field Values**| `#FFFFFF` | Crisp Pure White | Numerical values, sample names, switch states (`On`/`Off`), dropdown selections. |
| **Slider & Cursor** | `#FF0000` | Pure Red | Inverted triangle slider cursors, split-point pointers, critical markers. |
| **Waveform Trace** | `#FFFFFF` | Crisp White Lines | Audio sample oscilloscope display and zero-axis lines. |
| **Loop Boundary Overlay**| `#00FFFF` | Cyan Fill / Lines | Start/Loop active audio span indicators on waveform strips. |
| **Envelope Vectors** | `#00FFFF` | Cyan Lines & Dots | Envelope attack/decay/sustain segments and junction vertices. |
| **Envelope Release Line**| `#00FF00` | Green Vertical Marker | Stage 4 release boundary line on envelope displays. |
| **Piano White Keys** | `#FFFFFF` | Solid White | 88-key piano keyboard white keys. |
| **Piano Black Keys** | `#000000` | Solid Black | 88-key piano keyboard black keys. |
| **Active Split Range Bar**| `#00FFFF` | Solid Cyan Horizontal Bar | Visual key-range spans positioned immediately above piano keys. |

---

## 3. Top-Level Navigation & Banner Anatomy

### Row 1: Global Volume & Hardware Status Banner
```
Volume[ -  :                  ]  ID:01 | Dec/Inc (or Point/---, ---/---, MIDIset)
```
- **Volume Container:** Displays currently loaded volume index and name (e.g. `Volume[ - : ]`).
- **SCSI / Drive ID:** Indicates active hardware SCSI initiator ID or drive target (typically `ID:01`).
- **Context Status Tag (Far Right):**
  - `---/---` : Default neutral mouse/knob state.
  - `Dec/Inc` : Front panel or mouse scroll wheel step mode.
  - `Point/---`: Graphical pointer / crosshair active.
  - `Mark/Area`: Waveform range marking or marker selection.
  - `MIDIset` : Interactive MIDI controller assignment active.

### Row 2: Mode Navigation Tabs
Contains exactly 6 persistent top-level tabs:
1. `Perform` (Performance multi-timbral mode)
2. `Patch` (Patch editing, splitting, modulation matrix)
3. `Partial` (Partial parameters, TVF filter, TVA envelope, LFO)
4. `Sample` (Sampling, DSP editing, looping, cutting, stretching)
5. `Disk` (Disk load, save, format, backup)
6. `System` (System parameters, SCSI configuration, MIDI global setup)

### Row 3: Screen Title & Navigation Buttons
- **Left:** Screen Name (e.g. `Perform Play 1`, `Patch Split`, `Partial TVF`, `Loop&Smoothing`, `System SCSI`).
- **Center:** Active selection breadcrumb or status badge:
  - `[Part1]` ~ `[Part8]` (Performance part)
  - `[Samp1]` ~ `[Samp4]` (Active partial sample layer)
  - `[Muted]` / `[Sol]` (Solo/Mute state)
- **Right Button Cluster:**
  - `[Pform]` / `[Patch]` / `[Partl]` / `[Sampl]` : Mode submenu dropdown toggle.
  - `Mark` : Opens 10-slot memory marker popup.
  - `Jump` : Opens 10-slot jump shortcut popup.
  - `Com` : Opens Context Command menu (Edit, Copy, Delete, Initialize, CD Player).

---

## 4. Reusable Graphic Widget Library

### Widget 1: Horizontal Slider with Triangle Cursor
Used across `Patch Common`, `Partial Common`, `Partial TVF`, `Partial TVA`, and `Partial LFO`.
- **Anatomy:**
  - Left numerical value: 3-4 digit white text (e.g. `120`, `+37`, `-32`).
  - Slider Track: A thin white or gray horizontal baseline with vertical end-stop ticks at minimum and maximum extents.
  - Slider Cursor: An inverted solid red isosceles triangle pointing downward directly onto the track. Center-detented sliders (e.g., Pan `-50` to `+50`, Fine Tune `-50` to `+50`) have a small center tick mark.

### Widget 2: Multi-Stage Envelope Curve Graph
Used in `Partial TVF` (Filter envelope) and `Partial TVA` (Amplifier envelope).
- **Anatomy:**
  - Graph Box: Blue background enclosed by a thin yellow or cyan border.
  - Axis: Horizontal zero-baseline with time divisions.
  - Trajectory Segments: Four bright cyan vector lines connecting Attack (Time 1, Level 1), Decay 1 (Time 2, Level 2), Decay 2 (Time 3, Level 3), and Release (Time 4).
  - Vertex Nodes: Small solid cyan dots marking each stage transition.
  - Release Marker: A vertical lime-green dashed or dotted vertical guideline indicating Key-Off time (transition to Release).

### Widget 3: 3-Tier Waveform Inspection & Editing Suite
Used consistently across all 15 `Sample` screens:
1. **Tier 1 — Position / Boundary Overview Strip (Top):**
   - Slender horizontal rectangular track representing 100% of the sample's total duration.
   - Shows cyan highlighted selection spans (From `Start` to `End`) and loop boundaries.
2. **Tier 2 — Full Overview Oscilloscope Box (Middle):**
   - Enclosed yellow border frame showing the audio waveform with a center zero-crossing line.
   - White waveform envelope displaying peaks and RMS profile.
   - Red vertical cursor lines for `From` and `To` edit cut-points.
3. **Tier 3 — Detail Zoom / Splice Inspection Box (Bottom):**
   - High-magnification waveform display for sample-accurate zero-crossing loop splicing.
   - Shows detailed zero-crossings and phase alignment.
4. **Right Control Sidebar:**
   - Coordinate indicators: `[X:---]`, `[Y:---]`, `[L:---]`.
   - Speed toggle button: `[ Fast ]` / `[ Slow ]`.
   - Action Button: `[ W.Graph ]` (Regenerate Waveform Graph).

### Widget 4: 88-Key Interactive Piano Keyboard
Rendered at the bottom of keyboard-centric screens (`Perform Play 1`, `Patch Split`, `Patch Q-Sampling`, `Partial Common`).
- **Anatomy:**
  - Full 88-key visual span from `A0` to `C8`.
  - White keys rendered as vertical white boxes; black keys as shorter black vertical boxes.
  - Key Split Zone Bars: Rendered directly above the keyboard. Dual horizontal cyan bars indicating Upper and Lower split regions, velocity switch ranges, or active played notes.
  - Octave Labels: `C1`, `C2`, `C3`, `C4`, `C5`, `C6`, `C7` text markers positioned beneath the keys.

### Widget 5: Bottom Softkey Action Strip
Five cyan bordered buttons (`F1` through `F5`) positioned horizontally across the bottom row.
- **Checkbox Toggle Softkeys:** Formatted as `[ ]Name` or `[*]Name` (e.g. `[ ]KbdOn`, `[ ]Single`, `[ ]Mono`, `[ ]AllOn`, `[ ]KeyStr`, `[ ]L.Unlk`, `[ ]MIDISel`).
- **Execution Buttons:** Formatted as solid labeled boxes (e.g. `Exec`, `Recover`, `Ready`, `Load`, `Set`, `Smpling`, `VolInfo`).
- **Inactive / Disabled Softkeys:** Displayed as dashed placeholders: `---`.
