# Hardware & Current Emulator Memory Map

Verified 2026-10-09 against scanned Roland S-760 Service Notes, printed pages 1
and 5, and `mame-source/src/mame/roland/s760.cpp`.

## Physical hardware

| Component | Correct identity | Evidence |
| --- | --- | --- |
| Main CPU | **IC1, Intel S80C196KB, 16 MHz**, 16-bit little-endian MCS-96 | Parts list p.5 |
| BOOT EPROM | **IC15, AM27C256-15D**, 256 Kbit = 32 KB | Parts list p.5 |
| CPU gate array | **IC4, HG62E33B08** | Parts list p.5 |
| I/O gate array | **IC20, uPD65012GF-473-3B9** | Parts list p.5 |
| Wave custom SP1/SP2 | IC27 MB87422PF / IC28 MB87423APF | Parts list p.5 |
| TVF | IC29 MB87424APF | Parts list p.5 |
| Mixer/MEQ | IC30 TC24SC220AF-007 | Parts list p.5 |
| FDC | IC24 uPD72068GF | Parts list p.5 |
| SCSI | IC25 MB89352A | Parts list p.5 |
| LCD controller | IC72 SED1335F0B | Parts list p.5 |
| ADC | **IC58 CS5339-K** | Parts list p.5 |
| DACs | **IC91/IC92 AK4328VS-E** | Parts list p.5 |

Specifications p.1: **24 hardware voices**, Differential Interpolation (DI),
16-bit linear sample data, 16-bit A/D, 18-bit D/A, 24-bit internal processing.
Wave memory: 2 MB standard, up to 32 MB. Sampling rates: 48, 44.1, 32, 24,
22.05, 16 kHz. Capacities: 1 volume, 64 performances, 128 patches, 255 partials,
512 samples. Outputs: two stereo pairs / four individual outputs. LCD: 160×64.

The software models allocate 32 voice slots; that is not hardware polyphony.
Earlier documents naming IC20 as either ROM or CPU, an AK5339 ADC, or eight
individual analog outputs are incorrect against this primary reference.
Historical `ic20_hle_*` names are retained only for code/path continuity.

The OP-760 video subsystem is modeled as RFSC16A with 128 KB VRAM. A complete
hardware register specification still requires evidence; see document 03.

## Current MAME map

This is the **implemented bring-up map**, not a complete physical chip-select
schematic. `machine_start()` installs resident RAM, then narrow peripheral
handlers over it.

| Address | Current backing / behavior |
| --- | --- |
| CPU operands below `0100` | Internal registers/SFRs in `AS_DATA`; external `AS_PROGRAM` is a different view |
| `0000–1FFF` program space | Work RAM with selected firmware RET read handlers |
| `0102/0104/010A/010C` | Software dispatch/parameter slots |
| `2000–207F` | Vector RAM; timer `200A → 2B51` |
| `2080–FFFF` | Resident OS RAM, overlaid by handlers below |
| `D000–D0FF` | VDP |
| `E000–E003` | LCD: E000 command/status, E002 data |
| `F000–F01F` | Gate array |
| `F020–F02F` | SCSI |
| `F040–F047` | FDC |

**File = runtime + `0x2780`** for resident `2080–FFFF` only: file
`4800–1277F`. No upper resident code banking is needed. Later disk resources
are not automatically mapped by this formula.

The old E000–EFF7 LCD handler consumed resident code; the four-byte window is
the correction (finding 13 and installed handlers). Historical D800 palette,
C000/C400, and D400 labels do not mean those ranges currently have installed
peripheral handlers. Disk reset sets SP=1120. MAME uses `N8097BH` with added
196 opcodes and boot workarounds; it is not yet an exact S80C196KB model.
