"""Historical research catalogue; claims require individual revalidation.

See coverage_report.py for the shared evidence policy. Legacy tuple fields are
retained as research input only; they do not drive coverage or ownership claims.
"""

import os

OUTPUT_MD_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "OS_TEST_COVERAGE_MATRIX.md"))

# Legacy status fields are never used as coverage evidence.
UNTESTED = "Unverified"
TESTED = "Unverified"

MATRIX_DATA = [
    # --- 1. BOOTLOADER & SYSTEM INITIALIZATION ---
    {
        "address": "0x000000 - 0x000200",
        "file_loc": "mame-source/src/mame/roland/s760.cpp:1977",
        "subsystem": "Bootloader / IPL",
        "known": "Yes",
        "functionality": "Floppy boot sector validation, 'S770 MR25A' header verification, IPL load into Work RAM",
        "tested": TESTED,
        "test_file": "tests/test_image_invariants.py::test_banner_tag_present",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x000200 - 0x004800",
        "file_loc": "mame-source/src/mame/roland/s760.cpp:1976",
        "subsystem": "CPU Core Init",
        "known": "Yes",
        "functionality": "MCS-96 / 80C196 CPU vector table, SP initialization (0x1120), Work RAM zero-fill",
        "tested": TESTED,
        "test_file": "tests/test_mame_invariants.py::test_mame_driver_contains_mcs96_cpu",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x004800 - 0x008000",
        "file_loc": "mame-source/src/mame/roland/s760.cpp:1980",
        "subsystem": "MMIO Gate Array",
        "known": "Yes",
        "functionality": "Address decoding for MMIO latches (0xF000-0xF00F), SIMM bank registers (32MB limit)",
        "tested": TESTED,
        "test_file": "tests/test_gate_array_mame.py::test_gate_array_simm_banking",
        "testable": "Yes",
        "difficulty": "Low"
    },

    # --- 2. VDP & VIDEO GRAPHICS SUBSYSTEM (hardware display controllers in s760.cpp) ---
    {
        "address": "0xD000 - 0xD0FF",
        "file_loc": "mame-source/src/mame/roland/s760.cpp:1978",
        "subsystem": "OP-760 VDP Regs",
        "known": "Yes",
        "functionality": "Roland RFSC16A VDP command/status registers, 128KB TC511664 VRAM port access",
        "tested": TESTED,
        "test_file": "tests/test_vdp_mame.py::test_vdp_address_pointer_and_auto_increment",
        "testable": "Yes",
        "difficulty": "Medium"
    },
    {
        "address": "0xE000 - 0xEFF7",
        "file_loc": "mame-source/src/mame/roland/s760.cpp:1979",
        "subsystem": "Front LCD VRAM",
        "known": "Yes",
        "functionality": "Epson SED1335 160x64 monochrome LCD display framebuffer and page memory mapping",
        "tested": TESTED,
        "test_file": "tests/test_lcd_mame.py::test_lcd_renders_only_authentic_sed1335_vram",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        # ROM font is rendered by the React CRT component (shell), not by s760.cpp.
        "address": "0x08B000 - 0x08C000",
        "file_loc": "google-ui/src/components/OP760Monitor.tsx:109",
        "subsystem": "ROM Bitmap Font (React shell)",
        "known": "Yes",
        "functionality": "8x8 VDP ROM glyph table used by the React CRT renderer (getFontGlyph/drawBitmapString)",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        # The genuine 10-pen palette lives in the VDP (s760.cpp); the React shell mirrors it visually.
        "address": "0x08C000 - 0x08E000",
        "file_loc": "mame-source/src/mame/roland/s760.cpp:1978",
        "subsystem": "10-Pen Palette (RFSC16A VDP)",
        "known": "Yes",
        "functionality": "Roland 10-Pen RGB palette DAC (Royal Blue #0000C0, Status Green, Yellow, Red, Cyan)",
        "tested": TESTED,
        "test_file": "tests/test_vdp_mame.py::test_vdp_10pen_palette_lookup",
        "testable": "Yes",
        "difficulty": "Low"
    },

    # --- 3. SYNTHESIS ENGINE & SOUND DSP (IC91/IC92) ---
    {
        "address": "0x09446A",
        "file_loc": "core/include/s760/s760_disk.hpp:11",
        "subsystem": "Patch Common",
        "known": "Yes",
        "functionality": "Patch header record: Level (0-127), Pan (-15..+15), Bend Range (+/-24), 1-Shot mode",
        "tested": TESTED,
        "test_file": "tests/test_cpp_parity.py::test_roland_disk_byte_parity",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x094964",
        "file_loc": "core/src/s760_disk.cpp:89",
        "subsystem": "Patch Split Matrix",
        "known": "Yes",
        "functionality": "Key split zone mapping (C-1 to G9), Partial 1-4 assignment, velocity crossfade switch",
        "tested": TESTED,
        "test_file": "tests/test_cpp_parity.py::test_roland_disk_byte_parity",
        "testable": "Yes",
        "difficulty": "Medium"
    },
    {
        "address": "0x09A1DC",
        "file_loc": "core/include/s760/s760_dsp.hpp:24",
        "subsystem": "Partial TVF",
        "known": "Yes",
        "functionality": "4-Pole 24dB/oct resonant filter: Cutoff Freq (0-127), Resonance (0-127), 4-Point EG",
        "tested": TESTED,
        "test_file": "tests/test_dsp_tools.py::test_digital_filter_lpf_and_hpf",
        "testable": "Yes",
        "difficulty": "Medium"
    },
    {
        "address": "0x09A872",
        "file_loc": "core/include/s760/s760_dsp.hpp:36",
        "subsystem": "Partial TVA",
        "known": "Yes",
        "functionality": "Time-Variant Amplifier: Level (0-127), Pan Depth, 4-Point Envelope Rate/Level curves",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x09ACA0",
        "file_loc": "core/include/s760/s760_dsp.hpp:48",
        "subsystem": "Partial LFO",
        "known": "Yes",
        "functionality": "LFO Generator (Sin, Tri, Saw, Square, Random), Rate, Delay, Detune, Pitch/TVF/TVA depths",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Medium"
    },
    {
        "address": "0x08BA97",
        "file_loc": "core/src/s760_dsp.cpp:110",
        "subsystem": "Time Stretch DSP",
        "known": "Yes",
        "functionality": "SOLA (Synchronized Overlap-Add) time-stretch engine with ratio scaling (50% to 200%)",
        "tested": TESTED,
        "test_file": "tests/test_dsp_tools.py::test_time_stretch_tempo_expansion_and_compression",
        "testable": "Yes",
        "difficulty": "Medium"
    },
    {
        "address": "0x08BAC8",
        "file_loc": "core/src/s760_dsp.cpp:180",
        "subsystem": "Rate Convert DSP",
        "known": "Yes",
        "functionality": "Sinc-interpolated polyphase sample rate converter (48k -> 44.1k/32k/22.05k/16k/15k)",
        "tested": TESTED,
        "test_file": "tests/test_dsp_tools.py::test_sample_rate_conversion_44k_to_22k_and_32k",
        "testable": "Yes",
        "difficulty": "Medium"
    },
    {
        "address": "0x08BAD8",
        "file_loc": "core/src/s760_dsp.cpp:240",
        "subsystem": "Bit Convert DSP",
        "known": "Yes",
        "functionality": "Bit depth reduction (16-bit -> 12-bit / 8-bit) with skip address decimation",
        "tested": TESTED,
        "test_file": "tests/test_dsp_tools.py::test_bit_depth_reduction_16bit_to_8bit",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x08BA73",
        "file_loc": "core/src/s760_dsp.cpp:45",
        "subsystem": "Loop & Smoothing",
        "known": "Yes",
        "functionality": "Zero-crossing search, forward/alternating looping, and crossfade smoothing interpolation",
        "tested": TESTED,
        "test_file": "tests/test_dsp_tools.py::test_crossfade_loop_smoothing",
        "testable": "Yes",
        "difficulty": "Medium"
    },
    {
        "address": "0x08BAB9",
        "file_loc": "core/src/s760_dsp.cpp:310",
        "subsystem": "Comp/Expand DSP",
        "known": "Yes",
        "functionality": "Dynamics compression/expansion with knee threshold, ratio curve, attack/release times",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Medium"
    },
    {
        "address": "0x08BAF3",
        "file_loc": "core/src/s760_dsp.cpp:380",
        "subsystem": "Wave Edit Tools",
        "known": "Yes",
        "functionality": "Destructive wave manipulation (Truncate, Cut & Splice, Area Erase, Insert, Mixing)",
        "tested": TESTED,
        "test_file": "tests/test_dsp_tools.py::test_destructive_wave_editing_cut_splice_erase_mix",
        "testable": "Yes",
        "difficulty": "Medium"
    },

    # --- 4. DISK & STORAGE SUBSYSTEMS ---
    {
        "address": "0x08D713",
        "file_loc": "core/src/s760_disk.cpp:135",
        "subsystem": "Roland Floppy Parser",
        "known": "Yes",
        "functionality": "Binary parser for Roland 1.44M HD (SYS-772) and 720K DD S-760/S-770 sound disks",
        "tested": TESTED,
        "test_file": "tests/test_disk_conversion.py::test_s760_sound_disk_builder_and_parser",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x0B94F7",
        "file_loc": "core/src/s760_disk.cpp:143",
        "subsystem": "S-550/W-30 Converter",
        "known": "Yes",
        "functionality": "Legacy Roland S-50, S-550, S-330, and W-30 12-bit floppy format translation engine",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Medium"
    },
    {
        "address": "0x08E426",
        "file_loc": "core/src/akai_disk.cpp:12",
        "subsystem": "Akai S1000 ISO Engine",
        "known": "Yes",
        "functionality": "Binary parser for Akai S1000 / S1100 CD-ROM volumes (programs, keygroups, sample conversion)",
        "tested": TESTED,
        "test_file": "tests/test_disk_conversion.py::test_akai_s1000_iso_builder_and_parser",
        "testable": "Yes",
        "difficulty": "Medium"
    },
    {
        "address": "0x08BEED",
        "file_loc": "core/src/s760_drive_manager.cpp:45",
        "subsystem": "SCSI Bus Driver",
        "known": "Yes",
        "functionality": "BlueSCSI / ZuluSCSI folder-backed drive mounting (IDs 0-6 Hard Disks & CD-ROM ISOs)",
        "tested": TESTED,
        "test_file": "tests/test_disk_conversion.py::test_bluescsi_zuluscsi_naming_and_scsi_menu_detection",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x0BA5A0",
        "file_loc": "core/src/s760_drive_manager.cpp:120",
        "subsystem": "DAT Tape Streamer",
        "known": "Yes",
        "functionality": "SCSI DAT tape backup streamer driver (ID0 TapeStreamer image backup and recovery)",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Medium"
    },
    {
        "address": "0x09674E",
        "file_loc": "core/src/s760_disk.cpp:211",
        "subsystem": "Disk Defrag Engine",
        "known": "Yes",
        "functionality": "S-760 disk sector defragmentation, allocation map cleanup, and FAT directory verify",
        "tested": TESTED,
        "test_file": "tests/test_dsp_tools.py::test_disk_optimization_and_defragmentation",
        "testable": "Yes",
        "difficulty": "Low"
    },

    # --- 5. INTERACTIVE UI MODES & STATE MACHINE (React shell — google-ui) ---
    # Historical mappings only. Existing React suites do not automatically
    # qualify these broad firmware-page claims.
    {
        "address": "0x08D818",
        "file_loc": "google-ui/src/components/OP760Monitor.tsx:590",
        "subsystem": "PERFORM Mode (1-7) (React CRT)",
        "known": "Yes",
        "functionality": "Perform Play 1, Perform EQ, MIDI Filter 1-3, Listen Delete, PartMap, Monitor, Quick Load",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x05DC9B",
        "file_loc": "google-ui/src/components/OP760Monitor.tsx:750",
        "subsystem": "PATCH Mode (1-4) (React CRT)",
        "known": "Yes",
        "functionality": "Patch Common 1-4, Patch Split (with graphic keyboard), Patch Control 1-4, Q-Sampling",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x08D6FE",
        "file_loc": "google-ui/src/components/OP760Monitor.tsx:880",
        "subsystem": "PARTIAL Mode (1-6) (React CRT)",
        "known": "Yes",
        "functionality": "Partial Common 1-2, Partial SMT, Partial TVF, Partial TVA, Partial LFO, Partial Q-Sampling",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x08D709",
        "file_loc": "google-ui/src/components/OP760Monitor.tsx:1037",
        "subsystem": "SAMPLE Mode (1-14) (React CRT)",
        "known": "Yes",
        "functionality": "Sampling (VU Meters), Loop&Smoothing (Zoom Match), Auto Trun, and all 11 DSP subpages",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x08D713",
        "file_loc": "google-ui/src/components/OP760Monitor.tsx:965",
        "subsystem": "DISK Mode (React CRT)",
        "known": "Yes",
        "functionality": "16-File Directory Table, Time/P# Readouts, RAM/Disk Meter Stack, Load/Save/OW functions",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x08BED2",
        "file_loc": "google-ui/src/components/OP760Monitor.tsx:1620",
        "subsystem": "SYSTEM Mode (1-5) (React CRT)",
        "known": "Yes",
        "functionality": "System Parameter 1/2, System SCSI (Target Matrix), System MIDI, Volume ID, System PRM",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x0C147F / 0x063EB6",
        "file_loc": "google-ui/src/components/OP760Monitor.tsx:1870",
        "subsystem": "Modals & Dialogs (React CRT)",
        "known": "Yes",
        "functionality": "Mark (01-10), Jump (01-10), Command (1-6), Confirm (Are You Sure?), VolInfo, Working",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Low"
    },

    # --- 6. HARDWARE & DIAGNOSTICS ---
    {
        # The seamless dual-controller cursor arbitration is now owned by the React shell front
        # panel (the invented MAME cursor path was removed in spec task 1.8).
        "address": "0x0BCEFA",
        "file_loc": "google-ui/src/components/S760FrontPanel.tsx:27",
        "subsystem": "Controller Multiplex (React shell)",
        "known": "Yes",
        "functionality": "Dual controller support: front-panel keys/nav cluster + pointer; RC-100/mouse pointer ownership",
        "tested": UNTESTED,
        "test_file": "",
        "testable": "Yes",
        "difficulty": "Low"
    },
    {
        "address": "0x04B6F9",
        "file_loc": "core/include/s760/s760_vst_plugin.hpp:60",
        "subsystem": "MIDI SDS / SysEx",
        "known": "Yes",
        "functionality": "Roland SysEx Protocol (0x41 0x6A) & MIDI Sample Dump Standard (SDS) packet transfer",
        "tested": TESTED,
        "test_file": "tests/test_dsp_tools.py::test_midi_sample_dump_standard_sds_header_and_sysex",
        "testable": "Yes",
        "difficulty": "Medium"
    }
]


def generate_markdown():
    if __package__:
        from .coverage_report import write_report
    else:
        from coverage_report import write_report
    sections = [('Subsystems', [(r['subsystem'], r['address']) for r in MATRIX_DATA])]
    write_report(OUTPUT_MD_PATH, 'OS subsystem research inventory', sections)


if __name__ == '__main__':
    generate_markdown()
