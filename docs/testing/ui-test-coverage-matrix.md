# UI research inventory

## Unverified inventory

This historical catalogue is a research checklist. Its item names and contexts
(including addresses and manual pages) have not been individually revalidated.
They are not verified binary mappings, component ownership, implementation
status, or test results. Earlier automatic Tested badges and broad citations
have been removed because they did not establish the behavior of each row.

**Catalogue entries:** 141. **Individually qualified rows in this inventory:** 0.
**No coverage percentage** is reported: neither a verified feature denominator
nor an assertion-to-feature mapping has been established. This does not mean
the project has no tests or working features.

## Reviewed test evidence by layer

These are examples of what the actual assertions establish, not coverage of
the inventory below. React Vitest and Playwright suites exist. This generator
does not run tests or infer a passing result from a test file existing.

| Layer | Test selector | Assertion scope | Limit |
| --- | --- | --- | --- |
| Image bytes | [tests/test_image_invariants.py::test_banner_tag_present](../../tests/test_image_invariants.py) | Checks the banner bytes at one disk-image offset. | Does not execute the bootloader or validate a save/load workflow. |
| Static source | [tests/test_mame_invariants.py::test_mame_driver_contains_mcs96_cpu](../../tests/test_mame_invariants.py) | Checks CPU configuration and address strings in driver source. | Does not execute CPU instructions or establish interrupt behavior. |
| React component | [google-ui/src/components/NativePanelControls.test.tsx::routes Value wheel and keyboard steps through the encoder rather than S1/S2](../../google-ui/src/components/NativePanelControls.test.tsx) | Renders the Value control and asserts DIAL_DELTA commands through mocked transport. | Does not execute MAME, prove a firmware value changed, or establish hardware parity. |

For qualified native runtime, host and hardware results, use the
[testing guide](../condensed/08-testing-coverage-and-verification.md),
[completion roadmap](../project/completion-roadmap.md) and their dated validation records.
Python peripheral mirrors and offline DSP tests are model evidence. A Lua
completion flag or screenshot file alone is not a firmware workflow assertion.
Hardware parity requires matched physical captures and stated tolerances.

## 1. Chassis, Physical Hardware Controls & Dual-Display Shell

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| OP-760 CRT Screen Bezel & Canvas | Global CRT Top | Unverified |
| CRT 15kHz Scanline Shader Layer | Global CRT Top | Unverified |
| CRT Phosphor Radial Glow Layer | Global CRT Top | Unverified |
| 1U Rack Chassis Front Panel | Global Rack Bottom | Unverified |
| Power Rocker Switch | Rack Top-Left | Unverified |
| Phones Level Knurled Pot | Rack Lower-Left | Unverified |
| 1/4" Stereo Headphone Jack | Rack Lower-Left | Unverified |
| Contrast Adjustment Trimmer | Rack Center-Left | Unverified |
| SED1335 160x64 Monochrome LCD | Rack Center-Left | Unverified |
| LCD Page Header Readout | LCD Top Row | Unverified |
| LCD 4-Row Parameter Summary | LCD Center | Unverified |
| LCD Soft-Key Prompt Bar | LCD Bottom Row | Unverified |
| Front Panel Rotary Value Dial | Rack Center-Right | Unverified |
| S1 Macro Pushbutton | Rack Center-Right | Unverified |
| S2 Quick-Command Pushbutton | Rack Center-Right | Unverified |
| DEC Pushbutton | Rack Right | Unverified |
| INC Pushbutton | Rack Right | Unverified |
| EXIT Pushbutton | Rack Right | Unverified |
| ENTER Pushbutton | Rack Right | Unverified |
| MODE Pushbutton | Rack Right | Unverified |
| Gotek 0.91" I2C OLED Display | Gotek Subpanel | Unverified |
| Gotek OLED Image Name Readout | Gotek Subpanel | Unverified |
| Gotek OLED Track Readout | Gotek Subpanel | Unverified |
| Gotek Push-Rotary Encoder | Gotek Subpanel | Unverified |
| Gotek Step Down Button | Gotek Subpanel | Unverified |
| Gotek Step Up Button | Gotek Subpanel | Unverified |
| Gotek USB Flash Drive Socket | Gotek Subpanel | Unverified |
| Gotek USB Activity Green LED | Gotek Subpanel | Unverified |
| Front Panel MIDI IN Activity LED | Rack Right | Unverified |
| Front Panel SCSI Activity LED | Rack Right | Unverified |

## 2. Global CRT Shell, Headers, Meters & Soft-Key Function Bar

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Top Mode Tab: PERFORM | CRT Header | Unverified |
| Top Mode Tab: PATCH | CRT Header | Unverified |
| Top Mode Tab: PARTIAL | CRT Header | Unverified |
| Top Mode Tab: SAMPLE | CRT Header | Unverified |
| Top Mode Tab: SYSTEM | CRT Header | Unverified |
| Top Mode Tab: DISK | CRT Header | Unverified |
| Subpage Navigation Tab Strip | CRT Subheader | Unverified |
| Work RAM % Free Vertical Meter | CRT Top-Right | Unverified |
| Disk Free % Vertical Meter | CRT Top-Right | Unverified |
| Active Polyphony Voice Stack | CRT Top-Right | Unverified |
| Sample Rate Status Badge | CRT Top-Right | Unverified |
| Master MIDI RX Indicator Dot | CRT Top-Right | Unverified |
| Soft Key [F1] Trigger Button | CRT Footer | Unverified |
| Soft Key [F2] Trigger Button | CRT Footer | Unverified |
| Soft Key [F3] Trigger Button | CRT Footer | Unverified |
| Soft Key [F4] Trigger Button | CRT Footer | Unverified |
| Soft Key [F5] Trigger Button | CRT Footer | Unverified |
| Soft Key [F6] Trigger Button | CRT Footer | Unverified |
| Mouse Pointer Cursor | CRT Viewport | Unverified |

## 3. PERFORM Mode (Pages 01 - 07)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Perform Play 1: Performance Name Input | PERFORM 01 | Unverified |
| Perform Play 1: Part 1-32 Selector Grid | PERFORM 01 | Unverified |
| Perform Play 1: Volume Faders 1-32 | PERFORM 01 | Unverified |
| Perform Play 1: Pan Pots 1-32 | PERFORM 01 | Unverified |
| Perform Play 1: Output Assign Dropdowns 1-32 | PERFORM 01 | Unverified |
| Perform Play 1: Part Mode Selectors 1-32 | PERFORM 01 | Unverified |
| Perform Play 1: Part Mute Checkboxes 1-32 | PERFORM 01 | Unverified |
| Perform Play 1: Part Solo Radio Buttons 1-32 | PERFORM 01 | Unverified |
| Perform Play 1: Part Level VU Meters 1-32 | PERFORM 01 | Unverified |
| Perform EQ: Bass Gain Dial | PERFORM 02 | Unverified |
| Perform EQ: Bass Frequency Slider | PERFORM 02 | Unverified |
| Perform EQ: Treble Gain Dial | PERFORM 02 | Unverified |
| Perform EQ: Treble Frequency Slider | PERFORM 02 | Unverified |
| Perform EQ: 4-Band Graphic Response Plotter | PERFORM 02 | Unverified |
| Perform EQ: Bypass Toggle Switch | PERFORM 02 | Unverified |
| Perform MIDI Filter 1: Pitch Bend Checkboxes | PERFORM 03 | Unverified |
| Perform MIDI Filter 1: Modulation Checkboxes | PERFORM 03 | Unverified |
| Perform MIDI Filter 2: Expression Checkboxes | PERFORM 04 | Unverified |
| Perform MIDI Filter 2: Program Change Checkboxes | PERFORM 04 | Unverified |
| Perform MIDI Filter 3: Velocity Curve Selectors | PERFORM 05 | Unverified |
| Perform MIDI Filter 3: Key Transpose Dials | PERFORM 05 | Unverified |
| Perform Listen Delete: Audition Trigger Key | PERFORM 06 | Unverified |
| Perform Listen Delete: Audition Velocity Slider | PERFORM 06 | Unverified |
| Perform Listen Delete: Patch Delete Trigger | PERFORM 06 | Unverified |
| Perform PartMap: 32-Cell Overview Grid | PERFORM 07 | Unverified |

## 4. PATCH Mode (Pages 01 - 04)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Patch Common: Patch Name Input Box | PATCH 01 | Unverified |
| Patch Common: Patch Level Slider | PATCH 01 | Unverified |
| Patch Common: Patch Pan Rotary Dial | PATCH 01 | Unverified |
| Patch Common: Coarse Tune Dial | PATCH 01 | Unverified |
| Patch Common: Fine Tune Dial | PATCH 01 | Unverified |
| Patch Common: Key Assign Dropdown | PATCH 01 | Unverified |
| Patch Common: Bender Range Selector | PATCH 01 | Unverified |
| Patch Split: 88-Key Graphic Piano Roll | PATCH 02 | Unverified |
| Patch Split: Partial 1 Key Split Brackets | PATCH 02 | Unverified |
| Patch Split: Partial 2 Key Split Brackets | PATCH 02 | Unverified |
| Patch Split: Partial 3 Key Split Brackets | PATCH 02 | Unverified |
| Patch Split: Partial 4 Key Split Brackets | PATCH 02 | Unverified |
| Patch Split: Velocity Crossfade Toggle | PATCH 02 | Unverified |
| Patch Control: Pitch Bender Depth Slider | PATCH 03 | Unverified |
| Patch Control: Modulation Wheel Depth Slider | PATCH 03 | Unverified |
| Patch Control: Aftertouch Depth Slider | PATCH 03 | Unverified |
| Patch Q-Sampling: Quick Sample Button | PATCH 04 | Unverified |

## 5. PARTIAL Mode (Pages 01 - 06)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Partial Common: Partial Name Input Box | PARTIAL 01 | Unverified |
| Partial Common: Sample 1-4 Slot Selectors | PARTIAL 01 | Unverified |
| Partial Common: Partial Level Slider | PARTIAL 01 | Unverified |
| Partial Common: Partial Pan Dial | PARTIAL 01 | Unverified |
| Partial SMT: Velocity Threshold Sliders | PARTIAL 02 | Unverified |
| Partial TVF: 4-Point Filter Envelope Canvas | PARTIAL 03 | Unverified |
| Partial TVF: Cutoff Frequency Dial | PARTIAL 03 | Unverified |
| Partial TVF: Resonance Peak Feedback Dial | PARTIAL 03 | Unverified |
| Partial TVA: 4-Point Amp Envelope Canvas | PARTIAL 04 | Unverified |
| Partial TVA: Level & Velocity Sens Dials | PARTIAL 04 | Unverified |
| Partial LFO: Waveform Dropdown & Rate Dial | PARTIAL 05 | Unverified |
| Partial LFO: Mod Depth Dials | PARTIAL 05 | Unverified |
| Partial Q-Sampling: Quick Sample Button | PARTIAL 06 | Unverified |

## 6. SAMPLE Mode & DSP Tools Suite (Pages 01 - 14)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Sampling 01: High-Res Peak VU Meters | SAMPLE 01 | Unverified |
| Sampling 01: Rate & Pre-Trigger Selectors | SAMPLE 01 | Unverified |
| Sampling 01: Record / Stop Transport Buttons | SAMPLE 01 | Unverified |
| Loop & Smooth 02: 440px Audio Waveform Canvas | SAMPLE 02 | Unverified |
| Loop & Smooth 02: Start / Loop / End Drag Markers | SAMPLE 02 | Unverified |
| Loop & Smooth 02: Zoom Match Buttons | SAMPLE 02 | Unverified |
| Loop & Smooth 02: Crossfade Length Slider | SAMPLE 02 | Unverified |
| Auto-Truncate 03: Silence Threshold Slider | SAMPLE 03 | Unverified |
| DSP Tools 04: SOLA Time Stretch Controls | SAMPLE 04 | Unverified |
| DSP Tools 05: Sinc Polyphase Resampler Selectors | SAMPLE 05 | Unverified |
| DSP Tools 06: Bit Depth Converter Buttons | SAMPLE 06 | Unverified |
| DSP Tools 07: Compressor / Expander Sliders | SAMPLE 07 | Unverified |
| DSP Tools 08: Digital Filter Frequency Sliders | SAMPLE 08 | Unverified |
| DSP Tools 09-14: Destructive Wave Splicers | SAMPLE 09-14 | Unverified |

## 7. DISK Mode (Pages 01 - 02)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Disk: Drive Selector Dropdown | DISK 01 | Unverified |
| Disk: 16-Row File Directory Table | DISK 01 | Unverified |
| Disk: Directory Vertical Scrollbar | DISK 01 | Unverified |
| Disk: Load Action Trigger [Load] | DISK 01 | Unverified |
| Disk: Save Action Trigger [Save] | DISK 01 | Unverified |
| Disk: Overwrite Trigger [Overwrite] | DISK 01 | Unverified |
| Disk: Delete Trigger [Delete] | DISK 01 | Unverified |
| Disk: Volume Information Readout | DISK 02 | Unverified |

## 8. SYSTEM Mode (Pages 01 - 05)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| System Parameter: Master Tune Dial | SYSTEM 01 | Unverified |
| System Parameter: Output Gain Switch | SYSTEM 01 | Unverified |
| System Parameter: LCD Contrast Slider | SYSTEM 02 | Unverified |
| System Parameter: Mouse Speed Multiplier | SYSTEM 02 | Unverified |
| System SCSI: 7-Row Target Matrix | SYSTEM 03 | Unverified |
| System SCSI: Bus Scan Action Button | SYSTEM 03 | Unverified |
| System MIDI: Device ID & Channel Dials | SYSTEM 04 | Unverified |
| System MIDI: SysEx RX/TX Toggles | SYSTEM 04 | Unverified |
| System Volume ID: Volume Label Editor | SYSTEM 05 | Unverified |

## 9. Modals, Popups, Overlays & Dialogs

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Mark Modal: 10 Quick-Bookmark Slots | Global Modal | Unverified |
| Jump Modal: 10 Rapid Screen Hops | Global Modal | Unverified |
| Command Modal: 6 Quick Command Actions | Global Modal | Unverified |
| Confirmation Modal: 'Are You Sure?' Dialog | Global Modal | Unverified |
| Volume Information Modal | Global Modal | Unverified |
| Now Working... Progress Spinner Banner | Global Overlay | Unverified |

## Promotion requirements

Before qualifying an inventory row, record the current owner, a specific
test selector, the assertion that exercises that behavior, a dated run
and its build/media identities, and the limits of the result. A passing
model test must never qualify original firmware or physical hardware.
