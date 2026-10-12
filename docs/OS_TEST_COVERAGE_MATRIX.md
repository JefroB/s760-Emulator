# OS subsystem research inventory

## Unverified inventory

This historical catalogue is a research checklist. Its item names and contexts
(including addresses and manual pages) have not been individually revalidated.
They are not verified binary mappings, component ownership, implementation
status, or test results. Earlier automatic Tested badges and broad citations
have been removed because they did not establish the behavior of each row.

**Catalogue entries:** 33. **Individually qualified rows in this inventory:** 0.
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

## Subsystems

| Historical item | Historical context (unverified) | Qualification |
| --- | --- | --- |
| Bootloader / IPL | 0x000000 - 0x000200 | Unverified |
| CPU Core Init | 0x000200 - 0x004800 | Unverified |
| MMIO Gate Array | 0x004800 - 0x008000 | Unverified |
| OP-760 VDP Regs | 0xD000 - 0xD0FF | Unverified |
| Front LCD VRAM | 0xE000 - 0xEFF7 | Unverified |
| ROM Bitmap Font (React shell) | 0x08B000 - 0x08C000 | Unverified |
| 10-Pen Palette (RFSC16A VDP) | 0x08C000 - 0x08E000 | Unverified |
| Patch Common | 0x09446A | Unverified |
| Patch Split Matrix | 0x094964 | Unverified |
| Partial TVF | 0x09A1DC | Unverified |
| Partial TVA | 0x09A872 | Unverified |
| Partial LFO | 0x09ACA0 | Unverified |
| Time Stretch DSP | 0x08BA97 | Unverified |
| Rate Convert DSP | 0x08BAC8 | Unverified |
| Bit Convert DSP | 0x08BAD8 | Unverified |
| Loop & Smoothing | 0x08BA73 | Unverified |
| Comp/Expand DSP | 0x08BAB9 | Unverified |
| Wave Edit Tools | 0x08BAF3 | Unverified |
| Roland Floppy Parser | 0x08D713 | Unverified |
| S-550/W-30 Converter | 0x0B94F7 | Unverified |
| Akai S1000 ISO Engine | 0x08E426 | Unverified |
| SCSI Bus Driver | 0x08BEED | Unverified |
| DAT Tape Streamer | 0x0BA5A0 | Unverified |
| Disk Defrag Engine | 0x09674E | Unverified |
| PERFORM Mode (1-7) (React CRT) | 0x08D818 | Unverified |
| PATCH Mode (1-4) (React CRT) | 0x05DC9B | Unverified |
| PARTIAL Mode (1-6) (React CRT) | 0x08D6FE | Unverified |
| SAMPLE Mode (1-14) (React CRT) | 0x08D709 | Unverified |
| DISK Mode (React CRT) | 0x08D713 | Unverified |
| SYSTEM Mode (1-5) (React CRT) | 0x08BED2 | Unverified |
| Modals & Dialogs (React CRT) | 0x0C147F / 0x063EB6 | Unverified |
| Controller Multiplex (React shell) | 0x0BCEFA | Unverified |
| MIDI SDS / SysEx | 0x04B6F9 | Unverified |

## Promotion requirements

Before qualifying an inventory row, record the current owner, a specific
test selector, the assertion that exercises that behavior, a dated run
and its build/media identities, and the limits of the result. A passing
model test must never qualify original firmware or physical hardware.
