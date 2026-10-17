# OS code research inventory

## Unverified inventory

This historical catalogue is a research checklist. Its item names and contexts
(including addresses and manual pages) have not been individually revalidated.
They are not verified binary mappings, component ownership, implementation
status, or test results. Earlier automatic Tested badges and broad citations
have been removed because they did not establish the behavior of each row.

**Catalogue entries:** 81. **Individually qualified rows in this inventory:** 0.
**No coverage percentage** is reported: neither a verified feature denominator
nor an assertion-to-feature mapping has been established. This does not mean
the project has no tests or working features.

## Reviewed test evidence by layer

These are examples of what the actual assertions establish, not coverage of
the inventory below. React Vitest and Playwright suites exist. This generator
does not run tests or infer a passing result from a test file existing.

| Layer | Test selector | Assertion scope | Limit |
| --- | --- | --- | --- |
| Image bytes | [tests/test_image_invariants.py::test_banner_tag_present](../../../tests/test_image_invariants.py) | Checks the banner bytes at one disk-image offset. | Does not execute the bootloader or validate a save/load workflow. |
| Static source | [tests/test_mame_invariants.py::test_mame_driver_contains_mcs96_cpu](../../../tests/test_mame_invariants.py) | Checks CPU configuration and address strings in driver source. | Does not execute CPU instructions or establish interrupt behavior. |
| React component | [google-ui/src/components/NativePanelControls.test.tsx::routes Value wheel and keyboard steps through the encoder rather than S1/S2](../../../google-ui/src/components/NativePanelControls.test.tsx) | Renders the Value control and asserts DIAL_DELTA commands through mocked transport. | Does not execute MAME, prove a firmware value changed, or establish hardware parity. |

For qualified native runtime, host and hardware results, use the
[testing guide](../../condensed/08-testing-coverage-and-verification.md),
[completion roadmap](../../project/completion-roadmap.md) and their dated validation records.
Python peripheral mirrors and offline DSP tests are model evidence. A Lua
completion flag or screenshot file alone is not a firmware workflow assertion.
Hardware parity requires matched physical captures and stated tolerances.

## 1. CPU Vectors, Reset & Early Hardware Initialization

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| CPU Vector Table | 0x000000 - 0x00001F | Unverified |
| IPL Boot Sector Header | 0x000020 - 0x0001FF | Unverified |
| Work RAM Clear & Stack Init | 0x000200 - 0x00111F | Unverified |
| SIMM Memory Auto-Detect | 0x001120 - 0x002FFF | Unverified |
| Gate Array MMIO Setup | 0x003000 - 0x0047FF | Unverified |
| OS Kernel Entry & Scheduler | 0x004800 - 0x005FFF | Unverified |

## 2. Video Controllers & Graphics Rendering (LCD & OP-760 CRT)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| SED1335 LCD Command Driver | 0x006000 - 0x007FFF | Unverified |
| LCD Framebuffer Draw Engine | 0x008000 - 0x009FFF | Unverified |
| RFSC16A VDP Core Driver | 0x00A000 - 0x00CFFF | Unverified |
| TC511664 128KB VRAM Port | 0x00D000 - 0x00DFFF | Unverified |
| 8x8 ROM Bitmap Font (React shell) | 0x08B000 - 0x08C000 | Unverified |
| 10-Pen Palette Hardware LUT (RFSC16A VDP) | 0x08C000 - 0x08E000 | Unverified |
| VDP Text & Box Rendering (React shell) | 0x08E000 - 0x091FFF | Unverified |
| VDP Waveform Graph Plotter (React shell) | 0x092000 - 0x093FFF | Unverified |

## 3. Input Devices & Controller Multiplexer

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Rotary Encoder & Button Input (React shell) | 0x010000 - 0x011FFF | Unverified |
| VDP Hardware Mouse Registers | 0x012000 - 0x013FFF | Unverified |
| Mode / Navigation Cluster (React shell) | 0x014000 - 0x015FFF | Unverified |
| Pointer / Focus Ownership (React shell) | 0x0BCEFA - 0x0BDFFF | Unverified |

## 4. DSP Sound Engine & Voice Synthesis (24-Voice Polyphony)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Voice Allocator & Polyphony Engine | 0x016000 - 0x018FFF | Unverified |
| Patch Common Parameter Parser | 0x09446A - 0x094963 | Unverified |
| Patch Split & Partial Crossfade | 0x094964 - 0x095FFF | Unverified |
| Partial TVF (Time-Variant Filter) | 0x09A1DC - 0x09A871 | Unverified |
| Partial TVA (Time-Variant Amp) | 0x09A872 - 0x09AC9F | Unverified |
| Partial LFO Generator | 0x09ACA0 - 0x09BFFF | Unverified |
| Micro-Tuning & Scale Tables | 0x09C000 - 0x09DFFF | Unverified |

## 5. DSP Sample Manipulation & Wave Processing Suite

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| SOLA Time Stretch Engine | 0x08BA97 - 0x08BAC7 | Unverified |
| Sinc Polyphase Resampler | 0x08BAC8 - 0x08BAD7 | Unverified |
| Bit Depth Converter | 0x08BAD8 - 0x08BAE7 | Unverified |
| Crossfade Loop & Smoothing | 0x08BA73 - 0x08BA96 | Unverified |
| Digital Comp/Expand DSP | 0x08BAB9 - 0x08BAC7 | Unverified |
| Auto-Truncate & Peak Normalizer | 0x08BAE8 - 0x08BAF2 | Unverified |
| Destructive Wave Splicer | 0x08BAF3 - 0x08BBFF | Unverified |

## 6. Storage, File Systems & SCSI Bus Architecture

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| uPD72068 FDC Floppy Controller | 0x01E000 - 0x01FFFF | Unverified |
| Roland Floppy Volume Parser | 0x08D713 - 0x08DFFF | Unverified |
| S-550 / S-330 / W-30 Converter | 0x0B94F7 - 0x0BA59F | Unverified |
| Akai S1000 / S1100 ISO Reader | 0x08E426 - 0x08EFFF | Unverified |
| MB89352A SCSI Controller Driver | 0x020000 - 0x023FFF | Unverified |
| SCSI Multi-Drive Manager | 0x08BEED - 0x08C4FF | Unverified |
| SCSI DAT TapeStreamer Driver | 0x0BA5A0 - 0x0BB4FF | Unverified |
| Disk Defrag & Optimization | 0x09674E - 0x097FFF | Unverified |
| MS-DOS FAT12 Floppy Formatter | 0x098000 - 0x099FFF | Unverified |

## 7. MIDI Protocol, SysEx & Sample Dump Standard (SDS)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| UART MIDI Interrupt Service | 0x024000 - 0x025FFF | Unverified |
| Roland SysEx Protocol Engine | 0x04B6F9 - 0x04CFFF | Unverified |
| MIDI Sample Dump Standard (SDS) | 0x04D000 - 0x04EFFF | Unverified |
| Multi-Timbral Part Router | 0x04F000 - 0x051FFF | Unverified |

## 8. Complete UI Page State Machine (React shell — google-ui)

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| PERFORM Play 1 (01) | 0x08D818 - 0x08D89F | Unverified |
| PERFORM EQ (02) | 0x08D8A0 - 0x08D91F | Unverified |
| PERFORM MIDI Filter 1 (03) | 0x08D920 - 0x08D99F | Unverified |
| PERFORM MIDI Filter 2 (04) | 0x08D9A0 - 0x08DA1F | Unverified |
| PERFORM MIDI Filter 3 (05) | 0x08DA20 - 0x08DA9F | Unverified |
| PERFORM Listen Delete (06) | 0x08DAA0 - 0x08DB1F | Unverified |
| PERFORM PartMap (07) | 0x08DB20 - 0x08DB9F | Unverified |
| PATCH Common 1-4 (01) | 0x05DC9B - 0x05DD1F | Unverified |
| PATCH Split & Keyboard (02) | 0x05DD20 - 0x05DDAF | Unverified |
| PATCH Control 1-4 (03) | 0x05DDB0 - 0x05DE2F | Unverified |
| PATCH Q-Sampling (04) | 0x05DE30 - 0x05DEAF | Unverified |
| PARTIAL Common 1-2 (01) | 0x08D6FE - 0x08D708 | Unverified |
| PARTIAL SMT (02) | 0x08D709 - 0x08D712 | Unverified |
| PARTIAL TVF (03) | 0x09A1DC - 0x09A871 | Unverified |
| PARTIAL TVA (04) | 0x09A872 - 0x09AC9F | Unverified |
| PARTIAL LFO (05) | 0x09ACA0 - 0x09B000 | Unverified |
| PARTIAL Q-Sampling (06) | 0x09B001 - 0x09BFFF | Unverified |
| SAMPLE Sampling (01) | 0x08D709 - 0x08D71F | Unverified |
| SAMPLE Loop & Smooth (02) | 0x08D720 - 0x08D73F | Unverified |
| SAMPLE Auto-Truncate (03) | 0x08D740 - 0x08D75F | Unverified |
| SAMPLE DSP Tools 1-11 (04-14) | 0x08D760 - 0x08D817 | Unverified |
| DISK Load / Save / OW (01-02) | 0x08D713 - 0x08D72F | Unverified |
| SYSTEM Parameter 1-2 (01-02) | 0x08BED2 - 0x08BEFF | Unverified |
| SYSTEM SCSI Matrix (03) | 0x08BF00 - 0x08BF4F | Unverified |
| SYSTEM MIDI (04) | 0x08BF50 - 0x08BF9F | Unverified |
| SYSTEM Volume ID / PRM (05) | 0x08BFA0 - 0x08BFFF | Unverified |
| Modals: Mark, Jump, Command | 0x0C147F - 0x0C1FFF | Unverified |
| Modals: Confirm, VolInfo, Working | 0x063EB6 - 0x064FFF | Unverified |

## 9. OS String Catalog & Token Lookup Tables

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| String Table: UI Labels & Page Names | 0x08B000 - 0x090000 | Unverified |
| String Table: Parameter Names & Units | 0x090000 - 0x0A0000 | Unverified |
| String Table: Storage & SCSI Commands | 0x0A0000 - 0x0B0000 | Unverified |
| String Table: Diagnostic & Error Prompts | 0x0B0000 - 0x0C8000 | Unverified |

## 10. Floppy FAT12 File Allocation, Directory Table & Free Space

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| FAT12 Boot Sector & BPB | 0x0C8000 - 0x0C81FF | Unverified |
| FAT12 Allocation Tables 1 & 2 | 0x0C8200 - 0x0C9FFF | Unverified |
| FAT12 Root Directory Entries | 0x0CA000 - 0x0CBFFF | Unverified |
| Sample Wave Buffers & Free Space | 0x0CC000 - 0x167FFF | Unverified |

## Promotion requirements

Before qualifying an inventory row, record the current owner, a specific
test selector, the assertion that exercises that behavior, a dated run
and its build/media identities, and the limits of the result. A passing
model test must never qualify original firmware or physical hardware.
