# Hardware & Current Emulator Memory Map

Latest: finding58. The experimental IC15 ROM boot now loads all112 OS tracks
and reaches interactive Perform Play. Correct OP-760 identification and live VDP
pointer readback remove the video blockers. New native EEPROM profiles default
to Mouse+CRT at the user's request; existing profiles retain their setting.
Native LCD writes and its screen surface are restored. Rendering, mouse input,
complete chip behavior and power-on bank defaults still need work.


Previous result: finding57. Original IC15 now reads the system disk through the
native FDC/observed IC4 DMA mode, loads all112 tracks (disk4800..1007FF to
RAM0..FBFFF), and enters the disk OS without payload preloading. The ROM path
services timer interrupts and scans the panel, but its CRT remains blank.
Reset bank defaults are experimental; DMA is synchronous and CPU/peripheral
emulation remains partial. The older direct handoff still reaches Perform Play.

**Banked physical map (findings53/54/55) — the leading, schematic-verified map.
The flat "Current MAME map" table below is the superseded comparison baseline.**
Separate fetch selectors 0100..0106 and data selectors 0108..010E give
`(selector<<10)+(CPUaddress&3FFF)`. ROM4FBF loads disk cylinders1..56 (file
4800..1007FF) into physical0..FBFFF; ROM4750 clears0106 and4755 hands off at
CPU **C000** (disk payload backed by physical0), NOT the flat2080.

Device selects at external data page0400 (Service Notes p18, visually checked;
CPU gate IC4 expands A0..A19, IC17/18/19 decode the high bits):

| Device | CPU address | Candidate physical | Notes |
| --- | --- | --- | --- |
| SAMPLE host port (IC27/28 MB87422/23) | C000 | 100000 | addr C00E/C00C; C00A data; poll C000 bit0/bit1 |
| TVF (**IC29 MB87424APF**) | D000 | 101000 | CS_FILT; 101040=channel, 101030=coefficient; flagged and unflagged writes observed — reviews75/76 |
| MEQ control (**IC30 TC24SC220AF-007**) | D800 | 101800 | CS_MEQ; 24-store initialization observed; distinct per-voice registers/attenuation law unproved |
| Pan command aperture (exact chip-select coverage unresolved) | DC00 | 101C00 | 101C00=coefficient, 101C06=tag OR0200; bit9 hardware function unproved — finding76 |
| FDC (uPD72068) | E000 | 102000 | **E000=MSR/auxiliary, E002=FIFO** (not old generic765 at F040) |
| SCSI | E400 | 102400 | |
| VDP (RFSC16A) | E800 | 102800 | address E804/E806, data E800/E802, cmd/status E808 |
| I/O | F000 | 103000 | |
| LCD | F800 | 103800 | |

Audio pipeline (finding68, schematic p18): SP2(IC28) → TVF(IC29) → MEQ(IC30) →
dual DAC(IC91/92). **MIDI** (finding73) is on the **CPU gate array IC4**, not the
CPU UART: IN → IC3 PC410 → IC4 RXD pin38; TXD pin37 → IC5 HC125 OUT/THRU.
Firmware byte port 0116, status 0114 bit1 = TX-ready; see document 06.

**External-interrupt stubs (findings73/74):** seven 4-byte stubs at `0120 + 4*i`.
Identified sources — 0: FDC service; 2: wave-related C000/C002/C016 service;
4: completion (sets RB3 bit0); 6: byte-receive handler (→ CD1F) = MIDI. Normal
interrupt mask 0x54 includes bit6. Exact IC4 source arbitration/vectoring is not
yet established (finding74 models source6→0138 as an inferred, opt-in response).

EEPROM (AK93C45-class, 64×16 Microwire) is wired to CPU P1.0/1/2 (CS/SK/DI) and
P2.7 (DO) per p18 — not the old gate-register model. IC15 BOOT ROM gets A0..A14
+ CS_BOOT from IC17 Y7. Opt-in `S760_BANKED_OS=1` executes these real banked
services (reaches Perform Play, finding55); full peripheral/CPU fidelity,
page-register reset defaults/mirroring, and DMA remain incomplete.

**ROM-driven loader map (finding57, `S760_ROM_BOOT`).** The IC15 v1.11 image is
mirrored over physical1E0000..1FFFFF; reset executes at2080 with initial
fetch/data page selectors0780/0790/07A0/07B0, after which the ROM programs the
banks itself. The ROM's functional disk→RAM DMA (decoded at ROM4E97..4FBE /
4FF1..5014):

| Control cell | Meaning |
| --- | --- |
| 0118 | transfer count |
| 0108..010E | destination translated through the four data selectors |
| 011A..011C | resulting 24-bit physical destination address |
| 011D | mode byte `D7` (disk→RAM); ROM4FB1 reuses the same control for track reads |

IC20 (uPD65012) port-B wiring at F002 (Service Notes p18): **PB0=disk-change
(CN5), PB1=density/mode, PB2=drive-select**. Disk-change clears on stepping with
inserted media; density currently derives from image size.

**LCD port orientation (finding58, corrected).** ROM29BC..29E7 writes SYSTEM SET
`0x40` and other commands to **F802**, writes parameters/data to **F800**, and
reads status at **F800**. The command/data ports were previously reversed; native
mode now routes them correctly and exposes the existing LCD rasterizer as a second
screen surface (previously the LCD was omitted from the MAME machine config). The
LCD renderer remains provisional.

**Front-panel scan upper bits = 00 (finding58).** OP-760-1 CN1 pins 49/50 ground
SP6/SP7 (Service Notes p14), so the native scan supplies upper bits `00` while the
low six panel inputs stay independent. ROM3C68 complements the scan; 4143..417E
recognizes complemented `C0` as board-PRESENT. The earlier raw `0x80` complemented
to `0x40` and wrongly selected board-absent (this is what left the ROM path on
Panel+LCD / blank CRT in finding57). `S760_F00A` is an explicit diagnostic
override only. FDC correction: ROM
4A92 writes **0x27** to the FDC command register (NOT START CLOCK 0x47) → the NEC
invalid-command result **0x80**; immediate one/two-byte-result commands no longer
spuriously raise INT (reading the first result byte releases FDC INT, enabling
the following SEEK edge). This DMA is synchronous/functional, not cycle-accurate
DRQ/DACK/TC; the ROM path loads+runs but leaves the CRT blank (VDP activity 0),
and the CPU-gate reset bank defaults still need independent hardware evidence.

Native CPU (findings55/57): a separate **I80C196KB** device adds SFR windows
0/14/15, common interrupt registers (INT_MASK1/INT_PEND1 at13/12), reverse SFR
access, timer writes, and separate capture storage. HSI FIFO, watchdog, full
IOC2/HSO modes, serial timing and external Timer2 remain incomplete.

Verified 2026-10-09/10 against scanned Roland S-760 Service Notes (printed pp.1,
5, 18), the Intel 80C196KB User's Guide 270651-003, the NEC FDC manual ch.4, and
`mame-source/src/mame/roland/s760.cpp`.

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
`4800–1277F`. This describes the current flat preload, not established hardware
banking. Shared38 and52 leave fetch/data selection and loaded-code backing open.
Later disk resources are not automatically mapped by this formula.

The old E000–EFF7 LCD handler consumed resident code; the four-byte window is
the correction (finding 13 and installed handlers). Historical D800 palette,
C000/C400, and D400 labels do not mean those ranges currently have installed
peripheral handlers. Disk reset sets SP=1120. MAME uses `N8097BH` with added
196 opcodes and boot workarounds; it is not yet an exact S80C196KB model.
