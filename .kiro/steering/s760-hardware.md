---
inclusion: always
---

# S-760 Hardware Reference

Reference facts about the target machine. Use these to constrain hypotheses when
analyzing firmware (endianness, likely CPU opcodes, peripheral registers, etc.).
Anything marked (UNVERIFIED) has not yet been confirmed against the image bytes
or a service manual — verify before relying on it.

## Overview
- Roland S-760: 16-bit, 24-voice stereo rack sampler (1 U). Released ~1994.
- Sample rates: 48 / 44.1 / 32 / 24 / 22.05 / 16 kHz; 16-bit linear; 24-bit
  internal processing.
- Storage: 3.5" floppy (2DD / 2HD) + SCSI for external drives.
- Optional boards: OP-760-1 (extra outputs), the DA/AD expansions, and the
  **OP-760-2 / color video + mouse** UI board (VGA output, GUI editing).

## System software
- The OS ships on a bootable floppy ("System Disk"). Our image is **Ver. 2.24**.
- Roland distributed multiple system versions; behavior/features differ by
  version. Roland's own download lists "S-760 System Version 2.24".
- The `S770` marker in our image header indicates format/code kinship with the
  S-770 (the larger sibling). Cross-referencing S-770 material may help.

## CPU / architecture — CONFIRMED: Intel MCS-96 (80C196KB)
- **CONFIRMED CPU: Intel `S80C196KB` (MCS-96 family, 16-bit, ~16 MHz).**
  - Source 1: named in the S-760 SERVICE MANUAL parts list ("S80C196KB 16M").
  - Source 2: byte-level opcode densities in the OS payload match MCS-96 (see
    below and docs/03-cpu-investigation.md).
- **Implications for disassembly:**
  - **Little-endian**, variable-length instructions (mostly 3- and 5-byte).
  - **Register-memory architecture**: operands are addresses into the on-chip
    register file (low RAM) / SFRs. Not stack-machine, not load-store RISC.
  - Key opcodes: `F0`=RET, `EF`=SCALL(rel11), `E7`=LJMP(rel16), `27`=SJMP(rel8),
    `D0..DF`=conditional short jumps, `A0..A3`=LD family, `C0..C3`=ST family,
    `FE`=signed mul/div prefix.
  - Use an **MCS-96 / 8xC196 disassembler** (Ghidra/IDA processor module or a
    standalone tool). Payload starts at file offset 0x4800.
  - Determine the load/base address + reset vector from the service-manual
    memory map (or emulation) before resolving absolute addresses.
- Measured opcode scan (`opcodes -Arch mcs96` over 0x4800..0x40000): F0=3462,
  EF=3902, A0-A3(LD)=14022, C0-C3(ST)=6742, D0-DF(Jcc)=16346 — a coherent,
  load-heavy, subroutine-dense code profile.

### (Historical) The 68000 assumption was WRONG
- The Roland S-series is often *assumed* to be Motorola 68000. For the S-760
  that is INCORRECT — it is the Intel MCS-96. Both aligned-68k and
  word-swapped-68k opcode scans returned **0** signatures. The only x86 on the
  disk is a data template (the MS-DOS boot sector the S-760 writes to DOS
  floppies), not the S-760's own code. Full evidence trail:
  docs/03-cpu-investigation.md and docs/04-findings-log.md.

## System block diagram (CONFIRMED via service-manual OCR, p.3)
The S-760 MAIN BOARD is built around the 80C196KB + a **CPU GATE ARRAY**
(IC1/IC4) that bridges the CPU to memory and peripherals. Blocks named on the
diagram:
- **BOOT** ROM (IC20) — power-on boot code (the OS proper is loaded from disk).
- **ROM** (IC27/IC28/IC29 area, "PCM/CO CONT ROM") — control/PCM ROM.
- **S-RAM** — CPU work RAM.
- **D-RAM** (IC24/IC25 etc.) — larger RAM.
- **EEP** (IC2) — EEPROM (settings/calibration).
- **WAVE MEMORY** — SIMM sockets (8M/16M), sample RAM.
- Peripherals: **FDC** (floppy), **SPC** (SCSI protocol ctrl), **SCSI**, **LCD**
  (160x64), **TVF/MEQ** (filter/EQ DSP path), **A/D**, **D/A** (IC91/IC92),
  **ADRS** (address generator).
- **OP-760-1** option: VIDEO BOARD with **VDP** (IC2) + its own D-RAM, RGB/
  S-Video out, mouse/digital connector.

Implication: the disk OS payload is loaded into RAM and executed by the
80C196KB. Exact address ranges (BOOT/ROM/RAM/SFR windows) are on the **IC DATA
pages 11-13** and the **MAIN BOARD ASSY pages 16-20** — OCR/read those to build
the precise memory map and the load/base address for disassembly.

### Peripheral chip identities (CONFIRMED via IC-DATA OCR, pp.11-13)
These are the chips the OS driver code communicates with — label I/O accesses
against these during disassembly:
- **CPU:** Intel `S80C196KB` + **CPU gate array IC1** (Fujitsu, part 15239118).
- **FDD controller IC24:** NEC **uPD72068GF** (floppy).
- **SCSI controller IC25:** Fujitsu **MB89352A** (SCSI protocol controller).
- **LCD controller IC72:** Epson **SED1335F0B** (160x64 graphic LCD).
- **Wave custom IC27/IC28 (SP1/SP2):** Fujitsu **MB87422PF / MB87423APF**
  (sample playback / voice DSP gate arrays).
- **D/A IC91/IC92:** AKM **AK4328VS**; **D-RAM 4M IC68/69:** Toshiba TC514260.
- OP-760-1 video board: **VDP** + D-RAM (RGB/S-Video, mouse).
Exact CPU address windows are in the wiring diagrams (not OCR-linearizable);
derive them during disassembly / from the MAIN BOARD schematic pages.

## Memory / boot — CONFIRMED via disassembly (Session 5)
The memory map was derived from the code itself (the service manual has no
explicit map). Disassembled with Ghidra's SLEIGH MCS-96 module via pypcode
(`.kiro/scripts/mcs96_disasm.py`); base verified at 92.2% clean call targets.

- **LOAD/BASE ADDRESS = 0x2080, at file offset 0x4800.** The OS code segment is
  mapped so that file 0x4800 == runtime address 0x2080 (the MCS-96 reset
  execution address). File 0x4800 disassembles as a textbook reset routine
  beginning with `FA` = `DI`.
- **Derived map:**
  - `0x0000-0x00FF` — register file + SFRs. Confirmed: SP=0x18, IOS0=0x15,
    IOS1=0x16, INT_MASK=0x08, INT_PEND=0x09, INT_MASK1=0x13, INT_PEND1=0x12,
    PORT1=0x0F, PORT2=0x10, TIMER1, AD_result (standard 80C196KB layout).
  - `0x0100-0x011D` — boot-initialized pointer/parameter table.
  - `0x0120-0x111F` — zeroed work RAM (~4KB); `0x1120` = initial stack pointer.
  - `0x2080..~0xD4FE+` — OS code (call/jump target span, first segment).
  - `~0x8000-0x9CFF` — data/state window (indexed accesses; == on-disk UI
    resource region at file ~0x87000).
  - `0xF000-0xF00A` — memory-mapped I/O (CPU gate array / peripheral latches:
    reset pulse at 0xF000, config at 0xF002/0xF004, status at 0xF00A).
- **Resident image + banking:** the resident code image is the **first 64KB**
  (file 0x4800-0x1277F == runtime 0x2080-0xFFFF). The on-disk payload is ~520KB
  of coherent code/tables, so the rest is banked/overlaid — it cannot all be
  resident in the 64KB MCS-96 space at once.
  - **0xF000 is a control/strobe LATCH, not a bank register** (read-modify-write
    bit pulses for reset/strobe lines via the gate array). Do NOT mistake it for
    the bank selector.
  - **CORRECTION:** the 0x4000/0x3FFF math is **fixed-point (Q14) arithmetic**
    (`value * ratio / 16384`, pitch/tuning/level/rate DSP scaling), NOT 16KB
    memory paging. An earlier note claiming a 16KB paging unit was retracted
    after reading the instruction context (see findings F29->F30). 0x4000 = 1.0
    in Q14.
  - **Bank/window-select register: NOT yet identified.** The only firm evidence
    of banking is capacity (~520KB code can't be resident in 64KB at once). To
    find the actual mechanism, locate the disk LOADER (code that reads sectors
    and copies segments into RAM) and read its segment table, or use MCS-96
    emulation to watch the mapping. Do not assert a scheme without this.
- **Reset routine (0x2080-0x218D):** DI; init pointer table; clear RAM
  0x120-0x1120; set SP; init interrupt SFRs (INT_MASK=0, INT_MASK1=0x20);
  pulse/config the 0xF000 I/O window with delay loops; set PORT1/PORT2; EI;
  `SCALL 0x23E9`; `INT_MASK=0x24`; `LJMP 0x2831` into main init.

### How to disassemble
```
pip install pypcode
python .kiro\scripts\mcs96_disasm.py S760224.IMG --off 0x4800 --len 0x200 --base 0x2080
```

## Useful external references
- **Roland S-760 Service Notes** — CONFIRMED CPU part `S80C196KB`. Also holds the
  memory map / ROM-RAM layout (scanned PDF in `manuals/`, needs OCR).
- **Intel MCS-96 / 80C196KB User's Guide** (Order #270651) and datasheet — the
  authoritative opcode map, register-file/SFR layout, and reset behavior for the
  disassembly work.
- Roland S-760 Owner's / MIDI manuals (feature behavior; in `manuals/`).
