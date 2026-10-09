"""
Script to generate the complete, exhaustive Roland S-760 OS v2.24 Code & Subsystem Matrix.
Covers the S760224.IMG binary layout, disassembly blocks, data structures, UI layouts,
emulator implementation lines, and automated test coverage.

PROVENANCE POLICY (ui-consolidation spec, F4 / R3.1 / R3.2):
- UI shell/chrome rows are owned by the React app in `google-ui/` and attributed to their real
  owning component (OP760Monitor for CRT content; S760FrontPanel / RolandLCD / GotekBay for
  physical shell). `google-ui/` has no automated test tooling yet (F5), so these rows are marked
  "⚪ Untested" with no test reference. The old `tests/test_interactive_ui.py` only drives the
  MAME driver via Lua and never loads the React components; it is NOT a valid test citation for
  any React source line.
- Hardware display controllers (Epson SED1335 LCD, Roland RFSC16A VDP) are the only display code
  owned by `mame-source/src/mame/roland/s760.cpp`; they are covered by the real MAME unit tests
  in `tests/test_lcd_mame.py` / `tests/test_vdp_mame.py`.
- Every "✅ Tested" row cites a `tests/<file>.py` that actually exists. No synthetic test files or
  `::test_*` IDs are emitted. Metrics are computed from the data, not hard-coded.
"""

import os

OUTPUT_PATH = "docs/OS_EXHAUSTIVE_CODE_MATRIX.md"

TESTED = "✅ Tested"
UNTESTED = "⚪ Untested"

# Row tuple shape:
# (offset, func, known, desc, tested, testable, difficulty, source_line, test_file)
# test_file is "" when no real automated test exists yet.
EXHAUSTIVE_SECTIONS = [
    {
        "section_title": "1. CPU Vectors, Reset & Early Hardware Initialization",
        "description": "MCS-96/80C196 hardware vector table, stack pointer initialization, Work RAM scrub, Gate Array MMIO decoding, and SIMM memory detection.",
        "rows": [
            ("0x000000 - 0x00001F", "CPU Vector Table", "Yes", "MCS-96 80C196 reset, NMI, Software Timer, HSI/HSO, Serial, and external interrupt vectors", TESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1976", "tests/test_mame_invariants.py"),
            ("0x000020 - 0x0001FF", "IPL Boot Sector Header", "Yes", "Floppy boot sector validation, 'S770 MR25A' magic signature verification, and IPL bootstrap", TESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1977", "tests/test_image_invariants.py"),
            ("0x000200 - 0x00111F", "Work RAM Clear & Stack Init", "Yes", "Sets SP to 0x1120, clears system scratchpad RAM, initializes internal CPU SFR registers", TESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1976", "tests/test_mame_invariants.py"),
            ("0x001120 - 0x002FFF", "SIMM Memory Auto-Detect", "Yes", "Probes 72-pin SIMM sockets (Bank 1 & 2), detects 2MB onboard + up to 32MB expanded RAM", TESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1980", "tests/test_gate_array_mame.py"),
            ("0x003000 - 0x0047FF", "Gate Array MMIO Setup", "Yes", "Configures custom Roland Gate Array MMIO latches (0xF000-0xF00F) for SCSI, FDC, and VDP routing", TESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1980", "tests/test_gate_array_mame.py"),
            ("0x004800 - 0x005FFF", "OS Kernel Entry & Scheduler", "Yes", "Main cooperative real-time executive, background task timer dispatch loop, and event pump", UNTESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1980", ""),
        ]
    },
    {
        "section_title": "2. Video Controllers & Graphics Rendering (LCD & OP-760 CRT)",
        "description": "Epson SED1335 160x64 monochrome LCD controller and Roland RFSC16A OP-760 CRT VDP with 128KB TC511664 VRAM and 10-Pen Palette DAC. The hardware controllers live in s760.cpp; the on-screen compositing is the React shell's job.",
        "rows": [
            ("0x006000 - 0x007FFF", "SED1335 LCD Command Driver", "Yes", "Initializes 160x64 LCD controller, sets display mode, cursor style, and frame memory banks", TESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1979", "tests/test_lcd_mame.py"),
            ("0x008000 - 0x009FFF", "LCD Framebuffer Draw Engine", "Yes", "160x64 monochrome graphics blitter: draw line, outline box, inverted cursor highlight, bitmap blit", TESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1979", "tests/test_lcd_mame.py"),
            ("0x00A000 - 0x00CFFF", "RFSC16A VDP Core Driver", "Yes", "Initializes OP-760 expansion VDP, configures sync timings (640x480 RGB/S-Video), VRAM access", TESTED, "Yes", "Medium", "mame-source/src/mame/roland/s760.cpp:1978", "tests/test_vdp_mame.py"),
            ("0x00D000 - 0x00DFFF", "TC511664 128KB VRAM Port", "Yes", "Fast MMIO auto-increment read/write port access to dual 64Kx16 DRAM banks", TESTED, "Yes", "Medium", "mame-source/src/mame/roland/s760.cpp:1978", "tests/test_vdp_mame.py"),
            ("0x08B000 - 0x08C000", "8x8 ROM Bitmap Font (React shell)", "Yes", "Full ASCII character set + Japanese kana + Roland musical symbols rendered by the React CRT component", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:109", ""),
            ("0x08C000 - 0x08E000", "10-Pen Palette Hardware LUT (RFSC16A VDP)", "Yes", "Maps 10 pen indexes to 24-bit RGB (Royal Blue #0000C0, Status Green, Red, Yellow, Cyan, etc.)", TESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1978", "tests/test_vdp_mame.py"),
            ("0x08E000 - 0x091FFF", "VDP Text & Box Rendering (React shell)", "Yes", "High-level CRT drawing in the React shell: render text string, draw border rectangle, draw button, fill rect", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:113", ""),
            ("0x092000 - 0x093FFF", "VDP Waveform Graph Plotter (React shell)", "Yes", "Audio sample visualization in the React CRT: decimate 16-bit PCM wave to a graphical trace", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:168", ""),
        ]
    },
    {
        "section_title": "3. Input Devices & Controller Multiplexer",
        "description": "Front panel tactile keys, rotary encoder, and pointer. The invented MAME cursor path was removed (spec task 1.8); the React shell owns the pointer and front-panel inputs. The genuine VDP mouse registers remain in s760.cpp.",
        "rows": [
            ("0x010000 - 0x011FFF", "Rotary Encoder & Button Input (React shell)", "Yes", "Front-panel Value dial and Dec/Inc, Exit, Enter, Mode keys handled by the React front panel", UNTESTED, "Yes", "Low", "google-ui/src/components/S760FrontPanel.tsx:27", ""),
            ("0x012000 - 0x013FFF", "VDP Hardware Mouse Registers", "Yes", "Genuine OP-760-2 VDP mouse position/control registers (0x20/0x21/0x22/0x24) kept in s760.cpp", TESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1978", "tests/test_vdp_mame.py"),
            ("0x014000 - 0x015FFF", "Mode / Navigation Cluster (React shell)", "Yes", "Mode cycle, cursor cross, and function keys emitted as s760_input CustomEvents from the React panel", UNTESTED, "Yes", "Low", "google-ui/src/components/S760FrontPanel.tsx:27", ""),
            ("0x0BCEFA - 0x0BDFFF", "Pointer / Focus Ownership (React shell)", "Yes", "Pointer and focus arbitration between front-panel keys and CRT pointer, owned by the React shell", UNTESTED, "Yes", "Low", "google-ui/src/components/S760FrontPanel.tsx:27", ""),
        ]
    },
    {
        "section_title": "4. DSP Sound Engine & Voice Synthesis (24-Voice Polyphony)",
        "description": "Custom Roland S-Series DSP voice manager, TVF 4-pole 24dB/oct resonant filter, TVA envelope generator, LFO modulator, and patch split matrix.",
        "rows": [
            ("0x016000 - 0x018FFF", "Voice Allocator & Polyphony Engine", "Yes", "Dynamic voice stealing, 24-voice polyphony management, key priority, and pitch assign", UNTESTED, "Yes", "Medium", "core/src/s760_dsp.cpp:12", ""),
            ("0x09446A - 0x094963", "Patch Common Parameter Parser", "Yes", "Patch volume (0-127), pan (-15..+15), pitch bend (+/-24), octave shift, and 1-shot trigger", TESTED, "Yes", "Low", "core/include/s760/s760_disk.hpp:11", "tests/test_cpp_parity.py"),
            ("0x094964 - 0x095FFF", "Patch Split & Partial Crossfade", "Yes", "Maps 88 keys (C-1 to G9) to 4 Partials with velocity split/crossfade switching", TESTED, "Yes", "Medium", "core/src/s760_disk.cpp:89", "tests/test_cpp_parity.py"),
            ("0x09A1DC - 0x09A871", "Partial TVF (Time-Variant Filter)", "Yes", "4-Pole 24dB/oct resonant filter: Cutoff (0-127), Resonance (0-127), 4-Point TVF Envelope", TESTED, "Yes", "Medium", "core/include/s760/s760_dsp.hpp:24", "tests/test_dsp_tools.py"),
            ("0x09A872 - 0x09AC9F", "Partial TVA (Time-Variant Amp)", "Yes", "Time-Variant Amplifier: Level (0-127), Pan Depth, 4-Point TVA Envelope Rate/Level curves", UNTESTED, "Yes", "Low", "core/include/s760/s760_dsp.hpp:36", ""),
            ("0x09ACA0 - 0x09BFFF", "Partial LFO Generator", "Yes", "Low-frequency oscillator (Sin, Tri, Saw, Square, Random), Rate, Delay, Detune, Pitch/TVF/TVA mod", UNTESTED, "Yes", "Medium", "core/include/s760/s760_dsp.hpp:48", ""),
            ("0x09C000 - 0x09DFFF", "Micro-Tuning & Scale Tables", "Yes", "Equal temperament, pure major/minor, Arabic, and user-programmable microtonal tuning tables", UNTESTED, "Yes", "Low", "core/src/s760_dsp.cpp:80", ""),
        ]
    },
    {
        "section_title": "5. DSP Sample Manipulation & Wave Processing Suite",
        "description": "Complete suite of onboard DSP transformation tools for Roland S-Series sample data.",
        "rows": [
            ("0x08BA97 - 0x08BAC7", "SOLA Time Stretch Engine", "Yes", "Synchronized Overlap-Add time-stretching with ratio scaling (50% to 200%) and pitch preservation", TESTED, "Yes", "Medium", "core/src/s760_dsp.cpp:110", "tests/test_dsp_tools.py"),
            ("0x08BAC8 - 0x08BAD7", "Sinc Polyphase Resampler", "Yes", "Sample rate conversion between 48kHz, 44.1kHz, 32kHz, 22.05kHz, 16kHz, and 15kHz", TESTED, "Yes", "Medium", "core/src/s760_dsp.cpp:180", "tests/test_dsp_tools.py"),
            ("0x08BAD8 - 0x08BAE7", "Bit Depth Converter", "Yes", "16-bit to 12-bit / 8-bit dynamic range decimation with optional dither noise shaping", TESTED, "Yes", "Low", "core/src/s760_dsp.cpp:240", "tests/test_dsp_tools.py"),
            ("0x08BA73 - 0x08BA96", "Crossfade Loop & Smoothing", "Yes", "Bidirectional zero-crossing finder, forward/alternating loops, and crossfade interpolation", TESTED, "Yes", "Medium", "core/src/s760_dsp.cpp:45", "tests/test_dsp_tools.py"),
            ("0x08BAB9 - 0x08BAC7", "Digital Comp/Expand DSP", "Yes", "Dynamics compressor/expander: knee threshold, compression ratio, attack, release", UNTESTED, "Yes", "Medium", "core/src/s760_dsp.cpp:310", ""),
            ("0x08BAE8 - 0x08BAF2", "Auto-Truncate & Peak Normalizer", "Yes", "Threshold-based leading/trailing silence stripping and 0dBFS waveform peak scaling", TESTED, "Yes", "Low", "core/src/s760_dsp.cpp:340", "tests/test_dsp_tools.py"),
            ("0x08BAF3 - 0x08BBFF", "Destructive Wave Splicer", "Yes", "Sample wave editing: Cut & Splice, Area Erase, Sample Insert, and Two-Sample Mixing", TESTED, "Yes", "Medium", "core/src/s760_dsp.cpp:380", "tests/test_dsp_tools.py"),
        ]
    },
    {
        "section_title": "6. Storage, File Systems & SCSI Bus Architecture",
        "description": "FDC floppy drive, Roland SYS-772 disk structure, S-550/W-30 legacy format converter, Akai S1000 ISO engine, SCSI hard disk/CD-ROM, and DAT tape streamer.",
        "rows": [
            ("0x01E000 - 0x01FFFF", "uPD72068 FDC Floppy Controller", "Yes", "Low-level MFM sector read/write/format for 1.44M HD (80 cyl, 18 sec) & 720K DD (80 cyl, 9 sec)", TESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1977", "tests/test_fdc_mame.py"),
            ("0x08D713 - 0x08DFFF", "Roland Floppy Volume Parser", "Yes", "Parses Roland proprietary disk layout (SYS-772 sound disk volume table, patch & wave files)", TESTED, "Yes", "Low", "core/src/s760_disk.cpp:135", "tests/test_disk_conversion.py"),
            ("0x0B94F7 - 0x0BA59F", "S-550 / S-330 / W-30 Converter", "Yes", "Legacy Roland 12-bit floppy format translation: converts S-50/S-550/W-30 banks to S-760 format", UNTESTED, "Yes", "Medium", "core/src/s760_disk.cpp:143", ""),
            ("0x08E426 - 0x08EFFF", "Akai S1000 / S1100 ISO Reader", "Yes", "Akai partition table, program chunk, sample header decoding, and pitch root translation", TESTED, "Yes", "Medium", "core/src/akai_disk.cpp:12", "tests/test_disk_conversion.py"),
            ("0x020000 - 0x023FFF", "MB89352A SCSI Controller Driver", "Yes", "SCSI bus arbitration, command descriptor block (CDB) issuing, synchronous/asynchronous data transfer", TESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1980", "tests/test_scsi_mame.py"),
            ("0x08BEED - 0x08C4FF", "SCSI Multi-Drive Manager", "Yes", "BlueSCSI/ZuluSCSI image mounting for SCSI IDs 0-6 (Hard Disks, MO drives, CD-ROM ISOs)", TESTED, "Yes", "Low", "core/src/s760_drive_manager.cpp:45", "tests/test_disk_conversion.py"),
            ("0x0BA5A0 - 0x0BB4FF", "SCSI DAT TapeStreamer Driver", "Yes", "Sequential SCSI tape backup & restore protocol (ID0 TapeStreamer full volume backup)", UNTESTED, "Yes", "Medium", "core/src/s760_drive_manager.cpp:120", ""),
            ("0x09674E - 0x097FFF", "Disk Defrag & Optimization", "Yes", "Disk sector defragmentation, free FAT cluster compaction, and directory table rebuild", TESTED, "Yes", "Low", "core/src/s760_disk.cpp:211", "tests/test_dsp_tools.py"),
            ("0x098000 - 0x099FFF", "MS-DOS FAT12 Floppy Formatter", "Yes", "Formats standard 1.44M MS-DOS disks for WAV file import/export exchange", TESTED, "Yes", "Low", "core/src/s760_disk.cpp:250", "tests/test_dsp_tools.py"),
        ]
    },
    {
        "section_title": "7. MIDI Protocol, SysEx & Sample Dump Standard (SDS)",
        "description": "UART MIDI communications, Roland SysEx implementation, and MIDI SDS sample packet transmission.",
        "rows": [
            ("0x024000 - 0x025FFF", "UART MIDI Interrupt Service", "Yes", "31.25 kbaud serial FIFO ring buffer: Note On/Off, CC, Pitch Bend, Program Change, Clock", UNTESTED, "Yes", "Low", "mame-source/src/mame/roland/s760.cpp:1976", ""),
            ("0x04B6F9 - 0x04CFFF", "Roland SysEx Protocol Engine", "Yes", "Manufacturer ID 0x41, Model ID 0x6A, command packet checksumming, parameter dump & load", TESTED, "Yes", "Medium", "core/include/s760/s760_vst_plugin.hpp:60", "tests/test_dsp_tools.py"),
            ("0x04D000 - 0x04EFFF", "MIDI Sample Dump Standard (SDS)", "Yes", "Universal MIDI Sample Dump Header (0x7E 0x01) and 120-byte data packet streaming with ACK/NAK", TESTED, "Yes", "Medium", "core/src/s760_dsp.cpp:420", "tests/test_dsp_tools.py"),
            ("0x04F000 - 0x051FFF", "Multi-Timbral Part Router", "Yes", "Routes MIDI Channels 1-16 to 32 Internal Parts, with Individual Output routing (Out 1-8)", UNTESTED, "Yes", "Low", "core/src/s760_dsp.cpp:450", ""),
        ]
    },
    {
        "section_title": "8. Complete UI Page State Machine (React shell — google-ui)",
        "description": "Full UI page layouts, parameter fields, and mode screens. These are owned by the React app in google-ui/. Per F5, google-ui has no automated test tooling yet, so every page row is honestly '⚪ Untested' until the React Vitest/Playwright suite lands (spec Phase 4). The old test_interactive_ui.py drove only the MAME driver and never loaded these components.",
        "rows": [
            ("0x08D818 - 0x08D89F", "PERFORM Play 1 (01)", "Yes", "Volume, Pan, Output Assign, Mode (Normal/Mono), Level Meter Stack, Part Assignment", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:590", ""),
            ("0x08D8A0 - 0x08D91F", "PERFORM EQ (02)", "Yes", "Bass Freq/Gain, Treble Freq/Gain, Output Routing, Master EQ Curves", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:610", ""),
            ("0x08D920 - 0x08D99F", "PERFORM MIDI Filter 1 (03)", "Yes", "Bend, Mod, Volume, Pan, Expression, Hold-1, Aftertouch filter flags per part", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:630", ""),
            ("0x08D9A0 - 0x08DA1F", "PERFORM MIDI Filter 2 (04)", "Yes", "Program Change filter, Bank Select filter, SysEx filter, Ext Controller mapping", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:650", ""),
            ("0x08DA20 - 0x08DA9F", "PERFORM MIDI Filter 3 (05)", "Yes", "Velocity curve select, Key Transpose, Channel Pressure routing", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:670", ""),
            ("0x08DAA0 - 0x08DB1F", "PERFORM Listen Delete (06)", "Yes", "Interactive voice audition, solo part monitoring, and patch deletion from performance", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:690", ""),
            ("0x08DB20 - 0x08DB9F", "PERFORM PartMap (07)", "Yes", "32-Part graphical overview grid, patch assignment matrix, and voice allocation meters", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:710", ""),
            ("0x05DC9B - 0x05DD1F", "PATCH Common 1-4 (01)", "Yes", "Patch Level, Pan, Coarse/Fine Tune, Key Assign (Poly/Mono), Priority, Bender", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:750", ""),
            ("0x05DD20 - 0x05DDAF", "PATCH Split & Keyboard (02)", "Yes", "Graphic 88-key piano roll display, Partial 1-4 key split brackets, velocity zones", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:770", ""),
            ("0x05DDB0 - 0x05DE2F", "PATCH Control 1-4 (03)", "Yes", "Bender Depth, Mod Wheel Depth, Aftertouch Depth, Expression Depth, Ext Controller routing", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:790", ""),
            ("0x05DE30 - 0x05DEAF", "PATCH Q-Sampling (04)", "Yes", "Quick-sample recording shortcut directly bound into active Patch split slot", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:810", ""),
            ("0x08D6FE - 0x08D708", "PARTIAL Common 1-2 (01)", "Yes", "Partial Level, Pan, Coarse/Fine Tune, Original Key, Sample 1-4 mapping", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:880", ""),
            ("0x08D709 - 0x08D712", "PARTIAL SMT (02)", "Yes", "Sample Mixing Template: Velocity switch, velocity crossfade, velocity fade curve", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:900", ""),
            ("0x09A1DC - 0x09A871", "PARTIAL TVF (03)", "Yes", "Graphical 4-Point TVF Envelope display, Cutoff, Resonance, Key Follow, Velocity Sens", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:920", ""),
            ("0x09A872 - 0x09AC9F", "PARTIAL TVA (04)", "Yes", "Graphical 4-Point TVA Envelope display, Level, Key Follow, Velocity Sens, Pan Curve", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:940", ""),
            ("0x09ACA0 - 0x09B000", "PARTIAL LFO (05)", "Yes", "Waveform (Sin, Tri, Saw, Sqr, Rnd), Rate, Delay, Detune, Pitch/TVF/TVA Mod depths", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:960", ""),
            ("0x09B001 - 0x09BFFF", "PARTIAL Q-Sampling (06)", "Yes", "Quick-sample recording shortcut directly into active Partial sample slot", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:980", ""),
            ("0x08D709 - 0x08D71F", "SAMPLE Sampling (01)", "Yes", "Stereo Peak VU Meters, Sampling Freq (48k/44.1k/32k/22.05k/16k), Pre-Trigger, Auto Trig", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1037", ""),
            ("0x08D720 - 0x08D73F", "SAMPLE Loop & Smooth (02)", "Yes", "Graphic waveform display, Start/End/Loop points, Zoom Match, Crossfade Length", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1070", ""),
            ("0x08D740 - 0x08D75F", "SAMPLE Auto-Truncate (03)", "Yes", "Threshold slider, start/end marker auto-adjustment, graphic wave display", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1100", ""),
            ("0x08D760 - 0x08D817", "SAMPLE DSP Tools 1-11 (04-14)", "Yes", "Time Stretch, Rate Convert, Bit Convert, Comp/Expand, Cut, Erase, Insert, Mix, Normalize", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1130", ""),
            ("0x08D713 - 0x08D72F", "DISK Load / Save / OW (01-02)", "Yes", "16-file directory browser, Time/P# Readouts, RAM/Disk Meter Stack, Load, Save, Overwrite", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:965", ""),
            ("0x08BED2 - 0x08BEFF", "SYSTEM Parameter 1-2 (01-02)", "Yes", "Master Tune (440.0Hz), LCD Contrast, Mouse Speed, Output Gain (+0/+6dB), Audio Input Gain", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1620", ""),
            ("0x08BF00 - 0x08BF4F", "SYSTEM SCSI Matrix (03)", "Yes", "Target drive matrix (IDs 0-6), Hard Disk / CD-ROM / MO detection, bus speed selector", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1650", ""),
            ("0x08BF50 - 0x08BF9F", "SYSTEM MIDI (04)", "Yes", "Device ID, Control Channel, Program Change RX/TX, SysEx RX/TX, SDS Device ID", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1680", ""),
            ("0x08BFA0 - 0x08BFFF", "SYSTEM Volume ID / PRM (05)", "Yes", "Volume label naming, system write protect, default boot drive assignment", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1710", ""),
            ("0x0C147F - 0x0C1FFF", "Modals: Mark, Jump, Command", "Yes", "Interactive overlay dialogs: 10 Mark quick-save slots, 10 Jump page hops, 6 Command shortcuts", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1870", ""),
            ("0x063EB6 - 0x064FFF", "Modals: Confirm, VolInfo, Working", "Yes", "'Are You Sure?' dialog, Volume Information memory breakdown, 'Now Working...' spinner", UNTESTED, "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1910", ""),
        ]
    },
    {
        "section_title": "9. OS String Catalog & Token Lookup Tables",
        "description": "ASCII strings extracted and categorized from the OS binary payload.",
        "rows": [
            ("0x08B000 - 0x090000", "String Table: UI Labels & Page Names", "Yes", "Screen headers, mode banners ('PERFORM', 'PATCH', 'PARTIAL', 'SAMPLE', 'SYSTEM', 'DISK')", TESTED, "Yes", "Low", "docs/OS_STRING_CATALOG.md:1", "tests/test_image_invariants.py"),
            ("0x090000 - 0x0A0000", "String Table: Parameter Names & Units", "Yes", "'Cutoff', 'Resonance', 'Attack', 'Release', 'Level', 'Pan', 'Freq (Hz)', 'Ratio (%)'", UNTESTED, "Yes", "Low", "docs/OS_STRING_CATALOG.md:500", ""),
            ("0x0A0000 - 0x0B0000", "String Table: Storage & SCSI Commands", "Yes", "'Format Disk', 'Load All', 'Save Patch', 'Akai Convert', 'S-550 Convert', 'Tape Streamer'", UNTESTED, "Yes", "Low", "docs/OS_STRING_CATALOG.md:2500", ""),
            ("0x0B0000 - 0x0C8000", "String Table: Diagnostic & Error Prompts", "Yes", "'Device Not Ready', 'Disk Write Protected', 'Out Of Memory', 'Now Working...', 'Are You Sure?'", UNTESTED, "Yes", "Low", "docs/OS_STRING_CATALOG.md:6000", ""),
        ]
    },
    {
        "section_title": "10. Floppy FAT12 File Allocation, Directory Table & Free Space",
        "description": "Underlying FAT12 filesystem structures, sound disk directories, and reserved sectors.",
        "rows": [
            ("0x0C8000 - 0x0C81FF", "FAT12 Boot Sector & BPB", "Yes", "Standard FAT12 BIOS Parameter Block (512 bytes/sector, 2 sectors/cluster, 1 reserved sector)", TESTED, "Yes", "Low", "core/src/s760_disk.cpp:250", "tests/test_image_invariants.py"),
            ("0x0C8200 - 0x0C9FFF", "FAT12 Allocation Tables 1 & 2", "Yes", "12-bit cluster linked-list allocation maps for OS modules and sound files", UNTESTED, "Yes", "Low", "core/src/s760_disk.cpp:250", ""),
            ("0x0CA000 - 0x0CBFFF", "FAT12 Root Directory Entries", "Yes", "Root directory table entries: filename, extension, attributes, cluster pointer, file size", UNTESTED, "Yes", "Low", "core/src/s760_disk.cpp:250", ""),
            ("0x0CC000 - 0x167FFF", "Sample Wave Buffers & Free Space", "Yes", "Raw PCM wave data blocks and unused disk sectors", UNTESTED, "Yes", "Low", "core/src/s760_disk.cpp:250", ""),
        ]
    }
]


def generate_markdown():
    total_entries = sum(len(sec["rows"]) for sec in EXHAUSTIVE_SECTIONS)
    known_entries = sum(1 for sec in EXHAUSTIVE_SECTIONS for r in sec["rows"] if r[2] == "Yes")
    tested_entries = sum(1 for sec in EXHAUSTIVE_SECTIONS for r in sec["rows"] if "✅" in r[4])
    testable_entries = sum(1 for sec in EXHAUSTIVE_SECTIONS for r in sec["rows"] if r[5] == "Yes")

    pct_known = (known_entries / total_entries * 100.0) if total_entries else 0.0
    pct_tested = (tested_entries / total_entries * 100.0) if total_entries else 0.0
    pct_testable = (testable_entries / total_entries * 100.0) if total_entries else 0.0

    md = []
    md.append("# Roland S-760 OS v2.24 — Exhaustive Code, Routine & Subsystem Matrix\n")
    md.append("This document maps the Roland S-760 OS v2.24 binary (`S760224.IMG`) memory ranges and "
              "subsystems to their real owning implementation — the C++ core (`core/`), the MAME driver "
              "(`mame-source/`), or the React shell (`google-ui/`) — with honest automated-test status.\n")
    md.append("---\n")
    md.append("## Provenance Notes\n")
    md.append("- **UI shell/chrome** rows are owned by the React app in `google-ui/` and attributed to their "
              "real owning component. `google-ui/` has no automated test tooling yet, so those rows are marked "
              "**⚪ Untested**. The former `tests/test_interactive_ui.py` only drove the MAME driver via Lua and "
              "never loaded the React components, so it is not cited for any React source line.\n")
    md.append("- **Hardware display controllers** (Epson SED1335 LCD, Roland RFSC16A VDP) are the only display "
              "code owned by `s760.cpp`; they are covered by the MAME unit tests in `tests/test_lcd_mame.py` / "
              "`tests/test_vdp_mame.py`.\n")
    md.append("- Every **✅ Tested** row cites a `tests/<file>.py` that actually exists.\n")
    md.append("---\n")
    md.append("## Executive Metrics\n")
    md.append(f"- **Total Distinct OS Blocks / Modules Mapped:** {total_entries}")
    md.append(f"- **Reverse-Engineered Functionality Known:** {known_entries} / {total_entries} (**{pct_known:.1f}%**)")
    md.append(f"- **Automated Test Coverage:** {tested_entries} / {total_entries} (**{pct_tested:.1f}%**)")
    md.append(f"- **Headless Automation Testability:** {testable_entries} / {total_entries} (**{pct_testable:.1f}%**)\n")
    md.append("---\n")

    for section in EXHAUSTIVE_SECTIONS:
        md.append(f"## {section['section_title']}\n")
        md.append(f"> {section['description']}\n")
        md.append("| Line of Code / ROM Offset | Subsystem / Function | Known? | What Does It Do? (Function / Subsystem Context) | Tested? | Testable? | Test Difficulty | Owning Source Line | Test Reference File |")
        md.append("| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :--- | :--- |")
        for r in section["rows"]:
            offset, func, known, desc, tested, testable, diff, src, test_file = r
            test_cell = f"[`{test_file}`]({test_file})" if test_file else "—"
            md.append(f"| `{offset}` | **{func}** | {known} | {desc} | {tested} | {testable} | `{diff}` | [`{src}`]({src}) | {test_cell} |")
        md.append("\n---\n")

    md.append("## Verification & Quality Assurance Policy\n")
    md.append("1. **Honest provenance:** every row is attributed to the file that actually implements it, and "
              "every '✅ Tested' row points to a real, existing test function in `tests/`.\n")
    md.append("2. **Parity Testing:** C++ DSP/disk implementations are byte-tested against the Python reference "
              "in `tests/test_cpp_parity.py`.\n")
    md.append("3. **Pending React tests:** `google-ui/` shell rows become testable once the Vitest/Playwright "
              "suite is added (ui-consolidation spec Phase 4).\n")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Exhaustive matrix successfully written to {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_markdown()
