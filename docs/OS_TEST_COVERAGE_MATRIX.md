# Roland S-760 OS v2.24 — Comprehensive Test Coverage & Understanding Matrix

This matrix maps Roland S-760 OS firmware routines and ROM offsets to their real owning implementation (C++ core, MAME driver, or the React `google-ui/` shell), with honest test verification status. UI shell/chrome rows are attributed to their React component and are marked untested until the React test suite lands; hardware display controllers (SED1335 LCD, RFSC16A VDP) live in `s760.cpp` and are covered by the MAME unit tests.

---

## Executive Summary

- **Total Subsystems & ROM Modules Mapped**: 33
- **Functionality Documented & Known**: 33 / 33
- **Automated Test Coverage**: 19 / 33 (**57.6%**)
- **Testable Status**: 33 / 33 (**100% Testable**)

> UI shell/chrome rows (React `google-ui/`) are intentionally marked **⚪ Untested**: `google-ui/` has no automated test tooling yet and no existing test exercises the React components. They will become tested once the Vitest/Playwright suite is added.

---

## Subsystem Coverage Table

| ROM Offset / Code Line | Subsystem / Function | Known? | What Does It Do? (Function / Subsystem Context) | Tested? | Testable? | Test Difficulty | Test Reference |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| [`0x000000 - 0x000200`](mame-source/src/mame/roland/s760.cpp:1977) | **Bootloader / IPL** | Yes | Floppy boot sector validation, 'S770 MR25A' header verification, IPL load into Work RAM | ✅ Tested | Yes | `Low` | [`tests/test_image_invariants.py::test_banner_tag_present`](tests/test_image_invariants.py) |
| [`0x000200 - 0x004800`](mame-source/src/mame/roland/s760.cpp:1976) | **CPU Core Init** | Yes | MCS-96 / 80C196 CPU vector table, SP initialization (0x1120), Work RAM zero-fill | ✅ Tested | Yes | `Low` | [`tests/test_mame_invariants.py::test_mame_driver_contains_mcs96_cpu`](tests/test_mame_invariants.py) |
| [`0x004800 - 0x008000`](mame-source/src/mame/roland/s760.cpp:1980) | **MMIO Gate Array** | Yes | Address decoding for MMIO latches (0xF000-0xF00F), SIMM bank registers (32MB limit) | ✅ Tested | Yes | `Low` | [`tests/test_gate_array_mame.py::test_gate_array_simm_banking`](tests/test_gate_array_mame.py) |
| [`0xD000 - 0xD0FF`](mame-source/src/mame/roland/s760.cpp:1978) | **OP-760 VDP Regs** | Yes | Roland RFSC16A VDP command/status registers, 128KB TC511664 VRAM port access | ✅ Tested | Yes | `Medium` | [`tests/test_vdp_mame.py::test_vdp_address_pointer_and_auto_increment`](tests/test_vdp_mame.py) |
| [`0xE000 - 0xEFF7`](mame-source/src/mame/roland/s760.cpp:1979) | **Front LCD VRAM** | Yes | Epson SED1335 160x64 monochrome LCD display framebuffer and page memory mapping | ✅ Tested | Yes | `Low` | [`tests/test_lcd_mame.py::test_lcd_renders_only_authentic_sed1335_vram`](tests/test_lcd_mame.py) |
| [`0x08B000 - 0x08C000`](google-ui/src/components/OP760Monitor.tsx:109) | **ROM Bitmap Font (React shell)** | Yes | 8x8 VDP ROM glyph table used by the React CRT renderer (getFontGlyph/drawBitmapString) | ⚪ Untested | Yes | `Low` | — |
| [`0x08C000 - 0x08E000`](mame-source/src/mame/roland/s760.cpp:1978) | **10-Pen Palette (RFSC16A VDP)** | Yes | Roland 10-Pen RGB palette DAC (Royal Blue #0000C0, Status Green, Yellow, Red, Cyan) | ✅ Tested | Yes | `Low` | [`tests/test_vdp_mame.py::test_vdp_10pen_palette_lookup`](tests/test_vdp_mame.py) |
| [`0x09446A`](core/include/s760/s760_disk.hpp:11) | **Patch Common** | Yes | Patch header record: Level (0-127), Pan (-15..+15), Bend Range (+/-24), 1-Shot mode | ✅ Tested | Yes | `Low` | [`tests/test_cpp_parity.py::test_roland_disk_byte_parity`](tests/test_cpp_parity.py) |
| [`0x094964`](core/src/s760_disk.cpp:89) | **Patch Split Matrix** | Yes | Key split zone mapping (C-1 to G9), Partial 1-4 assignment, velocity crossfade switch | ✅ Tested | Yes | `Medium` | [`tests/test_cpp_parity.py::test_roland_disk_byte_parity`](tests/test_cpp_parity.py) |
| [`0x09A1DC`](core/include/s760/s760_dsp.hpp:24) | **Partial TVF** | Yes | 4-Pole 24dB/oct resonant filter: Cutoff Freq (0-127), Resonance (0-127), 4-Point EG | ✅ Tested | Yes | `Medium` | [`tests/test_dsp_tools.py::test_digital_filter_lpf_and_hpf`](tests/test_dsp_tools.py) |
| [`0x09A872`](core/include/s760/s760_dsp.hpp:36) | **Partial TVA** | Yes | Time-Variant Amplifier: Level (0-127), Pan Depth, 4-Point Envelope Rate/Level curves | ⚪ Untested | Yes | `Low` | — |
| [`0x09ACA0`](core/include/s760/s760_dsp.hpp:48) | **Partial LFO** | Yes | LFO Generator (Sin, Tri, Saw, Square, Random), Rate, Delay, Detune, Pitch/TVF/TVA depths | ⚪ Untested | Yes | `Medium` | — |
| [`0x08BA97`](core/src/s760_dsp.cpp:110) | **Time Stretch DSP** | Yes | SOLA (Synchronized Overlap-Add) time-stretch engine with ratio scaling (50% to 200%) | ✅ Tested | Yes | `Medium` | [`tests/test_dsp_tools.py::test_time_stretch_tempo_expansion_and_compression`](tests/test_dsp_tools.py) |
| [`0x08BAC8`](core/src/s760_dsp.cpp:180) | **Rate Convert DSP** | Yes | Sinc-interpolated polyphase sample rate converter (48k -> 44.1k/32k/22.05k/16k/15k) | ✅ Tested | Yes | `Medium` | [`tests/test_dsp_tools.py::test_sample_rate_conversion_44k_to_22k_and_32k`](tests/test_dsp_tools.py) |
| [`0x08BAD8`](core/src/s760_dsp.cpp:240) | **Bit Convert DSP** | Yes | Bit depth reduction (16-bit -> 12-bit / 8-bit) with skip address decimation | ✅ Tested | Yes | `Low` | [`tests/test_dsp_tools.py::test_bit_depth_reduction_16bit_to_8bit`](tests/test_dsp_tools.py) |
| [`0x08BA73`](core/src/s760_dsp.cpp:45) | **Loop & Smoothing** | Yes | Zero-crossing search, forward/alternating looping, and crossfade smoothing interpolation | ✅ Tested | Yes | `Medium` | [`tests/test_dsp_tools.py::test_crossfade_loop_smoothing`](tests/test_dsp_tools.py) |
| [`0x08BAB9`](core/src/s760_dsp.cpp:310) | **Comp/Expand DSP** | Yes | Dynamics compression/expansion with knee threshold, ratio curve, attack/release times | ⚪ Untested | Yes | `Medium` | — |
| [`0x08BAF3`](core/src/s760_dsp.cpp:380) | **Wave Edit Tools** | Yes | Destructive wave manipulation (Truncate, Cut & Splice, Area Erase, Insert, Mixing) | ✅ Tested | Yes | `Medium` | [`tests/test_dsp_tools.py::test_destructive_wave_editing_cut_splice_erase_mix`](tests/test_dsp_tools.py) |
| [`0x08D713`](core/src/s760_disk.cpp:135) | **Roland Floppy Parser** | Yes | Binary parser for Roland 1.44M HD (SYS-772) and 720K DD S-760/S-770 sound disks | ✅ Tested | Yes | `Low` | [`tests/test_disk_conversion.py::test_s760_sound_disk_builder_and_parser`](tests/test_disk_conversion.py) |
| [`0x0B94F7`](core/src/s760_disk.cpp:143) | **S-550/W-30 Converter** | Yes | Legacy Roland S-50, S-550, S-330, and W-30 12-bit floppy format translation engine | ⚪ Untested | Yes | `Medium` | — |
| [`0x08E426`](core/src/akai_disk.cpp:12) | **Akai S1000 ISO Engine** | Yes | Binary parser for Akai S1000 / S1100 CD-ROM volumes (programs, keygroups, sample conversion) | ✅ Tested | Yes | `Medium` | [`tests/test_disk_conversion.py::test_akai_s1000_iso_builder_and_parser`](tests/test_disk_conversion.py) |
| [`0x08BEED`](core/src/s760_drive_manager.cpp:45) | **SCSI Bus Driver** | Yes | BlueSCSI / ZuluSCSI folder-backed drive mounting (IDs 0-6 Hard Disks & CD-ROM ISOs) | ✅ Tested | Yes | `Low` | [`tests/test_disk_conversion.py::test_bluescsi_zuluscsi_naming_and_scsi_menu_detection`](tests/test_disk_conversion.py) |
| [`0x0BA5A0`](core/src/s760_drive_manager.cpp:120) | **DAT Tape Streamer** | Yes | SCSI DAT tape backup streamer driver (ID0 TapeStreamer image backup and recovery) | ⚪ Untested | Yes | `Medium` | — |
| [`0x09674E`](core/src/s760_disk.cpp:211) | **Disk Defrag Engine** | Yes | S-760 disk sector defragmentation, allocation map cleanup, and FAT directory verify | ✅ Tested | Yes | `Low` | [`tests/test_dsp_tools.py::test_disk_optimization_and_defragmentation`](tests/test_dsp_tools.py) |
| [`0x08D818`](google-ui/src/components/OP760Monitor.tsx:590) | **PERFORM Mode (1-7) (React CRT)** | Yes | Perform Play 1, Perform EQ, MIDI Filter 1-3, Listen Delete, PartMap, Monitor, Quick Load | ⚪ Untested | Yes | `Low` | — |
| [`0x05DC9B`](google-ui/src/components/OP760Monitor.tsx:750) | **PATCH Mode (1-4) (React CRT)** | Yes | Patch Common 1-4, Patch Split (with graphic keyboard), Patch Control 1-4, Q-Sampling | ⚪ Untested | Yes | `Low` | — |
| [`0x08D6FE`](google-ui/src/components/OP760Monitor.tsx:880) | **PARTIAL Mode (1-6) (React CRT)** | Yes | Partial Common 1-2, Partial SMT, Partial TVF, Partial TVA, Partial LFO, Partial Q-Sampling | ⚪ Untested | Yes | `Low` | — |
| [`0x08D709`](google-ui/src/components/OP760Monitor.tsx:1037) | **SAMPLE Mode (1-14) (React CRT)** | Yes | Sampling (VU Meters), Loop&Smoothing (Zoom Match), Auto Trun, and all 11 DSP subpages | ⚪ Untested | Yes | `Low` | — |
| [`0x08D713`](google-ui/src/components/OP760Monitor.tsx:965) | **DISK Mode (React CRT)** | Yes | 16-File Directory Table, Time/P# Readouts, RAM/Disk Meter Stack, Load/Save/OW functions | ⚪ Untested | Yes | `Low` | — |
| [`0x08BED2`](google-ui/src/components/OP760Monitor.tsx:1620) | **SYSTEM Mode (1-5) (React CRT)** | Yes | System Parameter 1/2, System SCSI (Target Matrix), System MIDI, Volume ID, System PRM | ⚪ Untested | Yes | `Low` | — |
| [`0x0C147F / 0x063EB6`](google-ui/src/components/OP760Monitor.tsx:1870) | **Modals & Dialogs (React CRT)** | Yes | Mark (01-10), Jump (01-10), Command (1-6), Confirm (Are You Sure?), VolInfo, Working | ⚪ Untested | Yes | `Low` | — |
| [`0x0BCEFA`](google-ui/src/components/S760FrontPanel.tsx:27) | **Controller Multiplex (React shell)** | Yes | Dual controller support: front-panel keys/nav cluster + pointer; RC-100/mouse pointer ownership | ⚪ Untested | Yes | `Low` | — |
| [`0x04B6F9`](core/include/s760/s760_vst_plugin.hpp:60) | **MIDI SDS / SysEx** | Yes | Roland SysEx Protocol (0x41 0x6A) & MIDI Sample Dump Standard (SDS) packet transfer | ✅ Tested | Yes | `Medium` | [`tests/test_dsp_tools.py::test_midi_sample_dump_standard_sds_header_and_sysex`](tests/test_dsp_tools.py) |

---

## Field Definitions & Criteria

1. **ROM Offset / Code Line**: Byte offset inside `S760224.IMG` and the corresponding real owning source file in `core/`, `mame-source/`, or `google-ui/`.
2. **Subsystem / Function**: Roland S-760 hardware or software domain.
3. **Known?**: `Yes` indicates reverse-engineering understanding of inputs, outputs, memory mutations, and behavior.
4. **What Does It Do?**: Concise description of the algorithm, model, or hardware operation.
5. **Tested?**: `✅ Tested` means a real, existing automated test in `tests/` exercises the row; `⚪ Untested` means no automated test currently covers it.
6. **Testable?**: `Yes` indicates the routine can be stimulated and validated headlessly.
7. **Test Difficulty**: Complexity to mock hardware peripherals or stimulate DSP timing (`Low`, `Medium`, `High`).
8. **Test Reference**: The exact `tests/<file>.py::<function>` that verifies the row, or `—` when none exists yet.
