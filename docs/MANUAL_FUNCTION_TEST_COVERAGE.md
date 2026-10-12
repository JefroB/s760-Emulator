# Manual workflow research inventory

## Unverified inventory

This historical catalogue is a research checklist. Its item names and contexts
(including addresses and manual pages) have not been individually revalidated.
They are not verified binary mappings, component ownership, implementation
status, or test results. Earlier automatic Tested badges and broad citations
have been removed because they did not establish the behavior of each row.

**Catalogue entries:** 63. **Individually qualified rows in this inventory:** 0.
**No coverage percentage** is reported: neither a verified feature denominator
nor an assertion-to-feature mapping has been established. This does not mean
the project has no tests or working features.

## Reviewed test evidence by layer

These are examples of what the actual assertions establish, not coverage of
the inventory below. React Vitest and Playwright suites exist. This generator
does not run tests or infer a passing result from a test file existing.

| Layer | Test selector | Assertion scope | Limit |
| --- | --- | --- | --- |
| Image bytes | [tests/test_image_invariants.py::test_banner_tag_present](../tests/test_image_invariants.py) | Checks the banner bytes at one disk-image offset. | Does not execute the bootloader or validate a save/load workflow. |
| Static source | [tests/test_mame_invariants.py::test_mame_driver_contains_mcs96_cpu](../tests/test_mame_invariants.py) | Checks CPU configuration and address strings in driver source. | Does not execute CPU instructions or establish interrupt behavior. |
| React component | [google-ui/src/components/NativePanelControls.test.tsx::routes Value wheel and keyboard steps through the encoder rather than S1/S2](../google-ui/src/components/NativePanelControls.test.tsx) | Renders the Value control and asserts DIAL_DELTA commands through mocked transport. | Does not execute MAME, prove a firmware value changed, or establish hardware parity. |

For qualified native runtime, host and hardware results, use the
[testing guide](condensed/08-testing-coverage-and-verification.md),
[completion roadmap](COMPLETION_ROADMAP.md) and their dated validation records.
Python peripheral mirrors and offline DSP tests are model evidence. A Lua
completion flag or screenshot file alone is not a firmware workflow assertion.
Hardware parity requires matched physical captures and stated tolerances.

## Section 1: Getting Started, Hardware Setup & Dual-Display System

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Hardware Power-On & Bootloader Flow | pp. 1-6 | Unverified |
| Front-Panel Mode Switching | pp. 7-10 | Unverified |
| Tactile Value Dial & DEC/INC Stepping | pp. 11-14 | Unverified |
| SED1335 160x64 LCD Contrast Tuning | pp. 15-18 | Unverified |
| OP-760 Video Display & 10-Pen Palette | pp. 19-24 | Unverified |
| Mouse Point-and-Click & Coordinate Hover | pp. 25-30 | Unverified |
| Dual-Display Seamless Traversal | pp. 31-36 | Unverified |
| Gotek OLED & Floppy Image Management | pp. 37-42 | Unverified |

## Section 2: Performance Mode (32-Part Multi-Timbral Architecture)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Performance Initialization & Naming | pp. 43-46 | Unverified |
| 32-Part Volume Balancing & Level Faders | pp. 47-52 | Unverified |
| 32-Part Stereo Pan & Output Routing | pp. 53-56 | Unverified |
| Part Mute, Solo & Polyphony Allocation | pp. 57-60 | Unverified |
| Master 4-Band Equalizer Calibration | pp. 61-66 | Unverified |
| MIDI Filter 1: Basic Controllers | pp. 67-70 | Unverified |
| MIDI Filter 2: Performance Controllers | pp. 71-74 | Unverified |
| MIDI Filter 3: Curves & Transposition | pp. 75-76 | Unverified |
| Part Audition, Deletion & PartMap Grid | pp. 77-78 | Unverified |

## Section 3: Patch Mode (Architecture, Key Splits & Modulation)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Patch Header Setup & Master Tuning | pp. 79-84 | Unverified |
| Key Assignment & Voice Stealing Priority | pp. 85-90 | Unverified |
| 88-Key Interactive Piano Roll Audition | pp. 91-98 | Unverified |
| Partial 1-4 Key Split Range Brackets | pp. 99-108 | Unverified |
| Velocity Split & Dynamic Crossfading | pp. 109-116 | Unverified |
| Pitch Bender & Modulation Depth Matrix | pp. 117-124 | Unverified |
| Aftertouch & Expression Controller Routing | pp. 125-130 | Unverified |
| Patch Quick-Sampling Shortcut | pp. 131-134 | Unverified |

## Section 4: Partial Mode (Synthesizer Engine & Acoustic Modeling)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Partial Sample 1-4 Slot Assignment | pp. 135-140 | Unverified |
| Sample Mixing Template (SMT) Velocity Layers | pp. 141-148 | Unverified |
| 4-Point Resonant TVF Filter Envelope Canvas | pp. 149-158 | Unverified |
| TVF Cutoff, Resonance & Keyboard Tracking | pp. 159-166 | Unverified |
| 4-Point TVA Amplitude Envelope Canvas | pp. 167-176 | Unverified |
| TVA Velocity Sensitivity & Stereo Panning | pp. 177-184 | Unverified |
| Multi-Waveform LFO Modulation Engine | pp. 185-194 | Unverified |
| Partial Quick-Sampling Integration | pp. 195-198 | Unverified |

## Section 5: Sample Mode & DSP Sample Manipulation Suite

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Live Sample Recording & Stereo VU Meters | pp. 199-206 | Unverified |
| Pre-Trigger Circular Buffer & Auto-Trigger | pp. 207-212 | Unverified |
| 440px Graphical Audio Waveform Editor | pp. 213-220 | Unverified |
| Zero-Crossing Loop Snap Match | pp. 221-226 | Unverified |
| Equal-Power Crossfade Loop Smoothing | pp. 227-234 | Unverified |
| Auto-Truncate Silence Stripping | pp. 235-240 | Unverified |
| SOLA Time Stretch Processing (50% - 200%) | pp. 241-248 | Unverified |
| Sinc Polyphase Sample Rate Converter | pp. 249-254 | Unverified |
| Bit Depth Reduction (16-Bit -> 12-Bit / 8-Bit) | pp. 255-258 | Unverified |
| Digital Compressor / Expander Dynamics | pp. 259-264 | Unverified |
| Destructive Wave Splicing (Cut, Erase, Insert, Mix) | pp. 265-266 | Unverified |
| 0dBFS Peak Normalization & RAM Defrag | pp. 267-268 | Unverified |

## Section 6: Disk & Media Storage Operations (SCSI & Floppy)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Drive Selection (FDD / SCSI IDs 0-6) | pp. 269-272 | Unverified |
| 16-File Directory Browsing & Pagination | pp. 273-276 | Unverified |
| Sound File Loading (Patch, Sample, Volume) | pp. 277-280 | Unverified |
| Sound File Saving & Overwrite Protection | pp. 281-284 | Unverified |
| File Deletion & Cluster Reclamation | pp. 285-286 | Unverified |
| Floppy & Hard Disk Formatting | pp. 287-290 | Unverified |
| Akai S1000 / S1100 CD-ROM ISO Conversion | pp. 291-294 | Unverified |
| Legacy S-550 / S-330 / W-30 Disk Conversion | pp. 295-296 | Unverified |
| SCSI DAT TapeStreamer Backup & Defrag | pp. 297-298 | Unverified |

## Section 7: System Configuration, MIDI Protocol & Modal Utilities

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Master Tuning Reference (440.0 Hz) | pp. 299-300 | Unverified |
| Analog Output Level & Preamp Gain | pp. 301-302 | Unverified |
| LCD Contrast & Serial Mouse Sensitivity | pp. 303-304 | Unverified |
| SCSI Target Bus Matrix & Dynamic Scan | pp. 305-308 | Unverified |
| Global MIDI Channel & SysEx / SDS Setup | pp. 309-310 | Unverified |
| System Volume ID, Write Protect & Boot Drive | pp. 311-312 | Unverified |
| Mark Quick-Save Bookmarks (01-10) | pp. 313-314 | Unverified |
| Jump Rapid Navigation Hops (01-10) | pp. 314-315 | Unverified |
| Command Quick Menu (1-6) & Confirmation | pp. 315-316 | Unverified |

## Promotion requirements

Before qualifying an inventory row, record the current owner, a specific
test selector, the assertion that exercises that behavior, a dated run
and its build/media identities, and the limits of the result. A passing
model test must never qualify original firmware or physical hardware.
