# 04 — Findings Log

Chronological record of discoveries and the evidence behind each. Append new
entries at the bottom. Keep each entry short: what, how we know, why it matters.

## Session 1 — orientation
- **F1. Image is a 1.44 MB floppy in a custom Roland format.**
  How: size = 0x168000 (2880 x 512); sector 0 has a Roland ASCII banner, no
  `55 AA`, no BPB. Why: rules out treating it as a DOS/FAT volume directly.
- **F2. Identity = S-760 System Disk Ver. 2.24.**
  How: ASCII at 0x04 (`S770 MR25A`), 0x20 (title), 0x40 (copyright).
  Why: matches Roland's published "S-760 System Version 2.24".
- **F3. Whole-disk block map produced.** Big 0x0F-fill areas at the front
  (0x200–0x47FF) and back third (0x100000+); dense payload in the middle.

## Session 2 — CPU + structure
- **F4. Not Motorola 68000.** How: 0 aligned 68k opcode signatures in
  0x4800–0xC800; only 3 `4E75` in the whole image; word-swapped scan also 0.
  Why: eliminates the most common assumption for the S-series.
- **F5. Payload is not compressed.** How: entropy ~6.3–6.8 bits/byte.
  Why: means we can analyze/disassemble it directly once the ISA is known.
- **F6. UI text/resources live ~0x87000–0x89000.** How: `strings` found MIDI
  labels ("Note On/Off", "P.After", "Bender"…), menu/status strings, "Ver. 2.24",
  "Controller = RC-100+CRT", ">> Please see your CRT <<". Why: gives us
  human-readable anchors to correlate with code.
- **F7. Embedded MS-DOS boot template (x86) at ~0x887A0.** How: `CD 13`/`C3`,
  DOS error strings, `IO.SYS`/`MSDOS.SYS` entries, `55 AA`. Why: shows the S-760
  can format/read MS-DOS floppies (sample interchange); the x86 here is DATA,
  not the S-760's CPU.
- **F8. Payload actually starts at 0x4800, not 0x5000.** How: 0x0F fill ends
  exactly at 0x47FF; same byte texture continues from 0x4800.
- **F9. 256-byte record table ~0xC3000–0xDDFFF.** How: record header repeats
  every 0x100 bytes; a byte at record+0x110 increments as an index. Why: likely
  the preset/parameter slot table — a good target for structural decoding.
- **F10. Main CPU is a variable-length ISA (not 68k/x86).** How: `0xDA` is a
  frequent byte recurring at ~3 and ~5 byte spacing with no 2/4-byte alignment.
  Why: narrows the CPU search to variable-length CISC-style families.
- **F11. All three manuals are scanned images (no text layer).** How: pypdf
  extracted ~300–500 chars from 14–24 pages each. Why: we need OCR to read the
  service-manual block diagram/parts list for the CPU part number.

## Session 3 — CPU CONFIRMED
- **F12. CPU = Intel MCS-96 (`S80C196KB`), 16-bit, little-endian.**
  How: (1) named in the S-760 service manual parts list ("S80C196KB 16M");
  (2) opcode-density scan of the payload matches MCS-96 exactly — `F0`(RET)=3462
  at 1.42%, `EF`(SCALL)=3902, `A0-A3`(LD)=14022, `C0-C3`(ST)=6742,
  `D0-DF`(Jcc)=16346. Why: this is THE key unlock — we can now use an MCS-96
  disassembler. It also explains F10: the register-memory ISA produces the 3-
  and 5-byte instruction cadence we measured.
- **F13. Manuals are scanned images; set up rendering via PyMuPDF.** Rendered
  the 24 service-note pages to PNGs at 200 DPI for OCR. (OCR engine install in
  progress; the user read the CPU part directly from the manual in the meantime.)
- **Correction to F10:** the "unknown variable-length ISA with 0xDA common" is
  resolved — it's MCS-96. `0xDA` is a frequent register-operand byte, not a
  prefix per se; the 3/5-byte spacing is the MCS-96 instruction length mix.

## Session 4 — OCR of the service manual + tooling
- **F14. OCR pipeline stood up (easyocr).** `render_pages.py` -> PNGs, then
  `.kiro/scripts/ocr_pages.py` -> per-page text in `.piggie/svc_ocr/`. Slow on
  CPU but works; models are cached after first run.
- **F15. Service-manual structure confirmed (OCR of TOC, page 0).** Contains:
  BLOCK DIAGRAM; PARTS LIST; **IC DATA (S-760/OP-760-1) on pp. 11-13**;
  **S-760 MAIN BOARD ASSY on pp. 16-20**; ENCODER and PANEL board assemblies;
  MEMORY EXPANDER section. The IC-DATA and MAIN-BOARD pages are where the
  CPU/ROM/RAM part numbers and memory map live -> OCR/inspect those next.
- **F16. Spec confirms preset capacity that matches on-disk tables.** Volume 1,
  Performance 64, Patch 128, Partial 255, Sample 512; Wave memory 2 MB standard,
  up to 32 MB via 2x SIMM72-16. The 256-byte record table (F9) likely holds one
  of these preset classes; correlate counts (128/255/512) with record counts.
- **F17. MCS-96 disassembler build deferred** pending the authoritative 80C196KB
  opcode map (hand-coded table had conflicts; abandoned to avoid a wrong
  disassembler). Plan: transcribe the opcode map from the Intel 80C196KB User's
  Guide (270651) or reuse an existing MCS-96 disassembler, then feed the payload
  at file offset 0x4800 with the load/base address from the service-manual map.

## Session 4 (cont.) — block diagram + peripheral IDs from OCR
- **F18. Block diagram (p.3) CONFIRMS the architecture.** 80C196KB + CPU gate
  array (IC1) bridging to: BOOT ROM (IC20), ROM (IC27-29), S-RAM, D-RAM
  (IC24/25), EEPROM (IC2), WAVE MEMORY SIMMs, FDC, SPC/SCSI, LCD, TVF/MEQ,
  A/D, D/A (IC91/92), ADRS. OP-760-1 video board = VDP + D-RAM.
  => The OS disk payload is loaded into RAM and run by the 80C196KB.
- **F19. Peripheral chips identified (IC-DATA pp.11-13):** FDC = NEC uPD72068GF;
  SCSI = Fujitsu MB89352A; LCD = Epson SED1335F0B; wave DSP = Fujitsu
  MB87422PF/MB87423APF; DAC = AKM AK4328VS; DRAM = Toshiba TC514260. These let
  us label I/O port accesses when disassembling the driver code.
- NOTE: exact CPU address ranges (BOOT/ROM/RAM/SFR) are in the pin-level wiring
  diagrams, which OCR can't linearize. Derive the memory map from the MAIN BOARD
  schematic (pp.16-20) by eye, or infer it during disassembly from how the code
  addresses these chips. This is the remaining input needed for the load/base
  address.

## Session 5 — memory map SOLVED via authoritative disassembly
- **F20. Adopted an authoritative MCS-96 disassembler (no more hand-coded
  opcodes).** How: `pip install pypcode` (Ghidra's SLEIGH engine) ships the
  `MCS96:LE:16:default` language — the NSA/Ghidra MCS-96 processor module.
  New reusable tool `.kiro/scripts/mcs96_disasm.py` wraps it. Why: the earlier
  hand-rolled decoder / opcode-heuristic (mcs96_xref.py, now deleted) was
  defeated by guesswork and by the payload being >64KB; SLEIGH decodes each
  instruction length correctly so linear sweeps are trustworthy.
- **F21. LOAD/BASE ADDRESS = 0x2080, at file offset 0x4800.** How: disassembling
  file 0x4800 with base 0x2080 yields a textbook MCS-96 reset routine:
  `2080: DI` (disable interrupts) — the classic reset start — followed by RAM
  clear, stack setup, SFR init, and a hardware bring-up sequence. 0x2080 is the
  MCS-96 reset execution address, so file 0x4800 == address 0x2080 is the
  loader's mapping for this segment. Why: this is the missing piece needed to
  resolve absolute call/jump/data addresses. THE memory-map unlock.
- **F22. Base verified independently (92.2%).** How: swept 6386 instructions
  from file 0x4800, collected 307 distinct SCALL/LCALL/SJMP/LJMP targets, mapped
  each back to a file offset (file = 0x4800 + target - 0x2080) and re-decoded:
  283/307 (92.2%) land on clean instruction boundaries, 0 out-of-range. A wrong
  base would scatter targets randomly. Why: strong statistical confirmation.
- **F23. Reset/startup routine decoded (0x2080-0x218D).** Sequence:
  `DI`; set up 5 pointer-table words at RAM 0x100-0x10E (values 0x400, 0x0F,
  0x204, 0x2FA, 0x299); **clear RAM 0x120..0x1120** via `ST ZR,[RW38]+` loop;
  **`LD SP,#0x1120`** (stack top); init SFRs IOS0/IOS1, mask+clear INT_PEND/
  INT_PEND1, `INT_MASK=0`, `INT_MASK1=0x20`; a delayed hardware bring-up writing
  a 1->0->1 pulse pattern to **I/O port 0xF000** (with `LCALL 0x218E` = a short
  delay-loop subroutine); program 0xF002/0xF004 (peripheral config); set PORT1/
  PORT2 bits; `EI`; `SCALL 0x23E9`; `LDB INT_MASK,#0x24`; `LJMP 0x2831` (into the
  main OS init). Why: gives the first real map of boot behavior + I/O window.
- **F24. Derived memory map (from the code itself):**
  * `0x0000-0x00FF` — register file + SFRs (SP=0x18, IOS0=0x15, IOS1=0x16,
    INT_MASK=0x08, INT_PEND=0x09, INT_MASK1=0x13, INT_PEND1=0x12, PORT1=0x0F,
    PORT2=0x10, TIMER1, AD_result). Standard 80C196KB layout — Ghidra's SLEIGH
    named these automatically and they line up with the code's usage.
  * `0x0100-0x011D` — boot-initialized pointer/parameter table (words written
    first thing at reset).
  * `0x0120-0x111F` — zeroed work RAM (~4KB); stack grows below 0x1120.
  * `0x1120` — initial stack pointer (top of work RAM).
  * `0x2080` — reset/entry; OS code begins here (== file 0x4800).
  * `~0x2080-0xD4FE+` — OS code region (call/jump targets span this).
  * `~0x8000-0x9CFF` — data/state window (indexed `LOOKUP[RW84]` accesses:
    0x8C06, 0x80AE, 0x8096, plus state bytes 0x8F7C/0x8F7E/0x8F94/0x8FB4...).
    This matches the UI-resource region seen on disk at file ~0x87000.
  * `0xF000-0xF00A` — memory-mapped I/O window (CPU gate array / peripheral
    latches: reset pulse, config regs at 0xF002/0xF004, status at 0xF00A).
- **F25. Payload is LARGER than 64KB => banked/extended addressing.** How: the
  on-disk payload (file 0x4800..~0x86000, 530KB) far exceeds the 64KB MCS-96
  address space; yet call targets like 0xDAB8 decode as clean routines. The
  80C196KB "16M"/gate-array design supports windowed/extended addressing, so the
  loader maps multiple segments. TODO: find the bank/window switch mechanism
  (likely a register in the 0xF000 I/O window) to map file offsets >0x4800+0xD000
  to their runtime addresses. For now, the first ~52KB (file 0x4800.. ) maps
  linearly at base 0x2080.

## Session 6 — banking / addressing model
- **F26. 0xF000 is a hardware CONTROL LATCH, not a memory bank register.** How:
  of 42 accesses to the 0xF0xx I/O window in the resident segment, 0xF000 is by
  far the hottest (21). The accesses are read-modify-write bit pulses, e.g. at
  runtime 0x2B33: `LDB R38,0xF000; ORB R38,#3; STB; ANDB R38,~3; STB` — set then
  immediately clear bits 0-1 = a strobe. The reset code likewise pulses 0xF000
  with delay loops. So 0xF000 drives control/reset/strobe lines (via the CPU
  gate array); 0xF002/0xF004 = config, 0xF00A/0xF00C = status/control, 0xF012 =
  another device. NOT the bank selector. (Tool: .piggie/scan_io.py, now removed.)
- **F27. Resident code image = first 64KB: file 0x4800-0x1277F == runtime
  0x2080-0xFFFF.** How: base 0x2080 maps file 0x4800; 0x2080+0xFFFF-0x2080 wraps
  at file 0x1277F. Code sampled at the top of this window (runtime ~0xF780,
  file ~0x12000) still decodes cleanly with in-range targets. Beyond file
  ~0x12780 a flat single-image model is impossible (would exceed 16-bit space).
- **F28. Payload is ~520KB of coherent code/data (not sparse).** How: 4KB-block
  MCS-96 decode across file 0x4800-0x86000 shows steady RET density (~5-30/KB)
  and branch density (~40-140/KB) in essentially every block (one small data
  gap). Random data does not produce steady RET rates. So the disk holds a large
  body of code/tables that cannot all be resident at once => overlays/banking.
  (Tool: .piggie/code_density.py, now removed.)
- **F29. Addressing uses 16KB (0x4000) pages — evidence-based.** How: 288
  `AND RW7C,#0x3FFF` (mask to a 14-bit / 16KB page offset), plus `DIVU #0x4000`
  (compute page index) and `CMP #0x4000` sites distributed across the payload.
  Example near runtime 0xF793: `MULU RL5C,RW5E,RW62; DIVU RL5C,#0x4000` then a
  store into the 0x8Bxx data window. Interpretation: the OS addresses a large
  external memory (WAVE MEMORY / DRAM, up to 32MB) through a **16KB window**,
  computing page = addr/0x4000 and offset = addr & 0x3FFF. This is the paging
  unit; the page/window select register is most likely in the gate-array I/O
  space (candidates: 0xF00C/0xF00E/0xF012 — TODO confirm by tracing a windowed
  access). (Tool: .piggie/find_pagecalc.py, now removed.)
- **STATUS:** The exact bank/window-select register + how disk file offsets
  >0x12780 map to runtime pages is still open. Two viable next paths: (a) trace
  a routine that does `AND #0x3FFF` back to the preceding window-select write;
  (b) run the OS in an MCS-96 emulator and watch the loader. Recorded as
  hypotheses, not asserted, per the RE workflow.

## Session 7 — CORRECTION: 0x4000 is fixed-point, not paging
- **F30. RETRACT the "16KB paging" reading of the 0x4000/0x3FFF math (F29).**
  How: disassembled every `DIVU #0x4000` site with context. The dominant idiom
  is fixed-point scaling, e.g. at runtime 0xE6A9:
  `LD RW64,0x83F6; MULU RL64,RW62; DIVU RL64,#0x4000; ST RW64,0x83F6` repeated
  for 0x83F6/0x8426/0x8456. That computes `result = value * ratio / 16384` —
  a **Q14 fixed-point multiply** (0x4000 = 1.0 in Q14). The `AND #0x3FFF` sites
  similarly mask fractional/þoffset fields, and one site (runtime 0x7F46) is
  sample-address math with `MULUB ... SHL #2 ... ORB #3`. So 0x4000 is a
  FRACTIONAL SCALE (pitch/tuning/level/rate DSP math), NOT a 16KB memory page
  size. Lesson: pattern-matched too eagerly in F29; corrected after reading the
  actual instruction context.
- **F31. What we CAN still say about banking (evidence-only).** The only solid
  banking evidence is capacity: ~520KB of coherent code/tables (F28) cannot be
  resident in the 64KB MCS-96 space (F27) simultaneously, so some overlay/bank
  mechanism must exist. But we have NOT identified a page/window-select register,
  and the 0x4000 arithmetic is not it. The mechanism remains genuinely open.
  Best next approaches: (a) find the disk LOADER (the code that reads sectors and
  copies them into RAM) and read its segment table directly; (b) MCS-96 emulation
  to watch the mapping happen. Do not assert a banking scheme without one of these.
- **F32. Data/state windows seen in this routine:** heavy TABLE[RW86] access to
  0x83C6/0x83F6/0x8426/0x8456/0x84B6/0x84E6 (per-voice or per-partial parameter
  arrays, RW86 = base index) and stores to 0xD020/0xD022. 0x9FE4 is a TABLE
  read (a coefficient/ratio table). These are RAM data structures, useful when
  we start labelling the voice/DSP engine.

## Session 7 (cont.) — main init sequence mapped (0x2831+)
- **F33. Main init entry = 0x2831** (reached via `LJMP 0x2831` at end of reset).
  Decoded head of the sequence:
  - `LDB HSI_status,#0x3A`; `ADD HSI_time,TIMER1,...` — timer/HSI (high-speed
    I/O) setup.
  - `LD RWDA,#0xC350 (=50000); ST -> 0x2086` — a timer reload/countdown const.
  - `STB ZRlo, 0xF012` — clear the 0xF012 gate-array device.
  - reads `0x8FBA` (a controller-type byte) and compares `#0x40` — matches the
    "Controller = RC-100 / +CRT" option logic seen in the UI strings.
  - init subroutine calls: `LCALL 0x2AD6`, `LCALL 0x54E8` (returns CARRY on
    error -> `JC` taken = likely a device/disk-ready probe), `LCALL 0x3F1C`,
    `LCALL 0x2E46` (called with RW1E=#0xDD77), plus backward LCALLs into other
    resident routines. State bytes touched: 0x1FA3-0x1FA8, 0x1E46, 0x1F6D.
  - These 0x1Fxx / 0x1Exx bytes are in work-RAM and look like init/flag state.
- **F34. Recommended pivot to emulation for the loader/banking.** Static tracing
  of the loader across banked overlays is slow and risks wrong guesses. The disk
  LOADER + the bank/window mechanism are best recovered by running the OS in an
  MCS-96 (80C196KB) emulator with the disk image attached, and watching which
  sectors are read and where they land. This is the workflow steering's Phase-2
  "emulation (optional, powerful)" path. Candidate emulators: MAME (has an
  i8x9x/MCS-96 CPU core) or a standalone 80C196 simulator. This is the next
  concrete step and needs a tool decision.

## Session 8 — emulation infra + BOOT ROM (IC20) acquisition plan
- **F35. Built a static control-flow tracer** `.kiro/scripts/mcs96_trace.py`
  (recursive descent from entry points using the pypcode MCS-96 decoder; follows
  calls/jumps within the resident 64KB image, logs routine entries + I/O
  accesses, and lists far/banked targets). First run from reset 0x2080 + main
  init 0x2831: 5347 instructions, **123 distinct routine entries**, 14 far/banked
  targets (0x018D 0296 0442 045D 0491 04AC 0551 05AA 0B31 0CC4 0EC7 0F15 0F19
  1109 — these are LOW addresses, below the 0x2080 load base, i.e. they point
  into the BOOT ROM / low vector space, NOT into the disk payload).
- **F36. KEY INSIGHT — the boot ROM is a separate physical chip (IC20) and the
  code calls INTO it.** The 14 far targets are all < 0x2080 (e.g. 0x18D, 0x296,
  0x442...). The disk payload loads at 0x2080; addresses below that are the
  reset/vector/boot region that lives in **BOOT ROM IC20**, not on the disk. So
  routines the OS calls at 0x018D/0x0442/etc. are BOOT-ROM services (very likely
  the low-level disk loader, SCSI/FDC primitives, and the bank/window control).
  This explains why the loader/banking mechanism is invisible in the disk image:
  IT IS NOT ON THE DISK. It is in IC20.
- **F37. MAME has an MCS-96 (i8x9x) CPU core but NO S-760/S-770 driver.** MAME's
  src/mame/roland has CM-32P, D-10, etc. (all MCS-96 Roland gear) but no S-7xx.
  A full MAME driver would also REQUIRE the BOOT ROM dump to run. => Emulation is
  blocked until we have IC20's contents.
- **F38. ACTION: dump BOOT ROM IC20 with the user's chip reader.** IC20 is the
  "BOOT" block on the main-board block diagram. Expected: a standard parallel
  EPROM/mask-ROM DIP (27Cxxx/23Cxxx class), likely socketed on Roland gear.
  Need from the dump: (a) exact part number printed on the chip, (b) dump size.
  Then: verify the reset vector / low routines (0x018D etc.) decode as MCS-96,
  confirm the load/bank mechanism, and feed the ROM to MAME or our tracer.
  NOTE: the service-manual OCR did not capture IC20's part number (parts-list
  detail too rough); read it off the physical chip.

## Session 8 (cont.) — IC20 is flat-pack (can't pull); boot-ROM interface analyzed
- **F39. IC20 is a flat/surface-mount package — NOT socket-pullable.** (User has
  a chip reader but IC20 can't be removed conventionally.) So a clean
  pull-and-read is out; options become: hot-air desolder onto an SMD adapter,
  an in-system dump via the running unit (MIDI SysEx / SCSI / floppy), or
  avoiding IC20 altogether.
- **F40. The 14 boot-ROM calls are LOW-FREQUENCY and follow a selector idiom.**
  How: every boot-ROM call is preceded by `LD RW1C,#<id>; ST RW1C, 0x104`
  (store a small constant — 0x166, 0x196, ... — into pointer-table slot 0x104)
  then `LCALL 0x0442/0x0491/0x0551/...`. Most targets are called just 1-3x.
  Interpretation: slot 0x104 is a SELECTOR/parameter and the boot-ROM routines
  are **service calls** (probably overlay/segment map+load, and low-level
  disk/SCSI primitives). This is consistent with IC20 holding the loader/bank
  logic that is NOT on the disk (F36). 0x442 is the most-called (3x).
- **F41. Implication for strategy.** We likely do NOT need to fully disassemble
  IC20 to make progress — we need its INTERFACE (inputs in 0x104/RW1C + regs,
  outputs, side effects). Two tractable paths that avoid desoldering:
  (a) **Behavioral spec by inference:** treat each 0x0xxx routine as a black box,
      infer its contract from all call sites (what's set before, what's used
      after), and document the boot-ROM ABI. Enough to patch/extend the disk OS.
  (b) **In-system ROM dump:** patch the disk OS (which we CAN rebuild) with a
      small routine that reads IC20's address range and emits it over MIDI SysEx
      or writes it to a floppy/SCSI — capturing IC20 without touching hardware.
      This reuses the OS's own working drivers. Higher payoff (gets us the real
      bytes + enables MAME) but needs a verified repack + a capture path.
- **F42. Emulation status.** Full MAME S-760 emulation stays blocked until IC20
  is dumped (no driver + needs boot ROM). Our static tracer
  (`.kiro/scripts/mcs96_trace.py`) + boot-ROM ABI inference is the unblocked path
  and is now the recommended near-term infrastructure.

## Session 8 (cont.) — Gotek changes the capture path
- **F43. User has a Gotek installed (floppy emulator); no SCSI drive yet.** This
  gives a read/write channel the S-760 already supports: we can move floppy
  images between the sampler and PC freely (swap the USB stick). This is the
  ideal in-system I/O path for (a) validating patched images and (b) eventually
  dumping IC20 to a disk file we can read on the PC.
- **F44. Repack tooling is byte-exact but has NO checksum recompute (known TODO
  in s760.ps1 Cmd-Repack).** Cmd-Patch does in-place same-length byte edits;
  Cmd-Repack enforces the exact 0x168000 size and refuses to touch the original.
  OPEN RISK: if the boot ROM validates a disk checksum, a naive patch may fail to
  boot. The Gotek round-trip test will reveal this empirically.
- **F45. Round-trip test target identified.** On-screen version string
  "Ver. 2.24" bytes (`56 65 72 2E 20 32 2E 32 34`) occur 12x in the image; the
  UI/display copy is at **file 0x87FDB** (0x36 is the sector-0 volume banner).
  A safe, visible, reversible test = change the on-screen "Ver. 2.24" to e.g.
  "Ver. 2.25", repack to a copy, serve via Gotek, boot, and see if the screen
  changes (and whether it boots at all -> checksum presence).

## Plan of record (staged, lowest-risk first)
- **M1 — Prove the round-trip.** Patch on-screen version string on a COPY,
  repack (size-exact), run on S-760 via Gotek. Outcomes: confirms our image is
  Gotek-bootable AND whether a disk checksum blocks patches. (User-in-the-loop.)
- **M2 — Handle checksum if present.** If M1 fails to boot, find the loader
  checksum (scan sector 0 / header for a stored sum; brute the algorithm over
  the payload) and add recompute to Cmd-Repack. Re-test.
- **M3 — Boot-ROM ABI by inference.** Document the contract of each IC20 service
  call (0x0442, 0x0491, 0x0551, 0x04AC, 0x05AA, 0x045D, 0x0296, 0x0B31, 0x018D,
  0x0D5D, 0x0EC7, 0x0F15, 0x0F19, 0x1109): inputs (esp. selector in RAM 0x104 /
  RW1C, and 0x166/0x196-style IDs), outputs, side effects, from all call sites.
- **M4 — In-system IC20 dump (optional, high payoff).** Once M1/M2 give a
  reliably bootable patched image, inject a small MCS-96 stub that copies IC20's
  address range to a buffer and writes it to a floppy file (Gotek), then read it
  on the PC. Gets the real boot ROM bytes -> unblocks MAME + settles banking.
- **M5 — Emulation.** With IC20 in hand, stand up MAME (write an S-760 driver or
  reuse an MCS-96 Roland driver as a base) or extend our Python tracer into a
  minimal emulator. Watch the loader map the disk; finish the memory map.

## Session 8 (cont.) — M1 test image built (awaiting hardware test)
- **F46. M1 test image ready: `temp/work/S760_M1_test.IMG`.** Built from a COPY
  (original untouched). Change: on-screen version "Ver. 2.24" -> "Ver. 9.99"
  (file 0x87FE0). Verified byte-exact vs original: exactly 3 bytes differ
  (0x87FE0 32->39, 0x87FE2 32->39, 0x87FE3 34->39), size = 0x168000. Gotek wants
  raw .IMG, which is our native format. AWAITING: user boots it on the S-760 via
  Gotek to confirm (a) it boots and (b) the screen shows "Ver. 9.99" (and thus
  whether a disk checksum blocks patches). Keep the original image handy to
  reflash the Gotek if it doesn't boot.

## Session 8 (cont.) — M1 RESULT: round-trip works, NO checksum
- **F47. M1 CONFIRMED: patched image boots on real hardware via Gotek, NO disk
  checksum.** User booted `S760_M1_test.IMG` (3-byte change) on the S-760 via
  Gotek: booted with no errors. => (1) the Gotek round-trip works, (2) the boot
  ROM does NOT checksum-validate the system disk (a modified image boots).
  This clears the biggest risk and means we can freely patch/extend the disk OS.
  M2 (checksum handling) is NOT needed.
- **F48. But the screen still showed 2.24 -> patched the wrong string copy.**
  There are 12 "Ver. 2.24" copies. The one at 0x87FDB (space-padded, isolated)
  is not what that screen renders. Context analysis of all 12:
  - 0x000036 sector-0 volume banner (not a screen).
  - 0x0BD3AA null-terminated, grouped with ">> Please see your CRT <<" /
    "Controller = RC-100+CRT" -> most likely the on-screen copy.
  - 0x0C1D46 "Roland S-760 Ver. 2.24 ... Volume" -> status/info line.
  - 0x097673/0x9775C disk-label templates; 0x0AC9xx family = disk-type banners
    written when formatting (System/Sound/Backup/Formatted/SYS-772).
- **F49. M1b test built: `temp/work/S760_M1b_test.IMG`.** Patches THREE likely
  on-screen copies (0x87FE0, 0x0BD3AF, 0x0C1D4B) to "9.99" so whichever the
  screen reads will change. Verified: 9 bytes differ, size 0x168000, all three
  read "Ver. 9.99". AWAITING: user boot test to identify which string the
  display uses (and confirm the visible change).

## Session 8 (cont.) — M1 COMPLETE + dump containers ready
- **F50. M1 COMPLETE: on-screen "9.99" confirmed on hardware.** User booted
  `S760_M1b_test.IMG`; main version display now shows "Ver. 9.99". Full closed
  loop proven: edit bytes on PC -> Gotek -> real S-760 -> visible change, no
  checksum. We can patch/extend the OS at will.
- **F51. Boot SPLASH version is a SEPARATE string.** During load the user still
  saw "Ver. 2.24". So the early boot splash reads a different copy than the main
  screen (main screen = one of 0xBD3AA / 0xC1D46; splash = likely 0x87FDB or a
  disk-banner copy). Cosmetic; revisit if we want to rebrand the splash too.
- **F52. Blank 1.44MB dump containers created** via new reusable tool
  `.kiro/scripts/make_blank.py`: `temp/work/BLANK_1440_zero.IMG` (0x00 fill) and
  `BLANK_1440_ff.IMG` (0xFF fill), both exactly 0x168000. These are RAW blanks
  (no S-760 filesystem) — intended for a raw-sector IC20 dump: stub writes IC20
  bytes to known sectors, we read them back on PC. If a dump path must go through
  the OS file-save, format a disk on the sampler instead and image it via Gotek.

## Session 9 — IC20 memory geography (for the dump)
- **F53. IC20 BOOT ROM occupies low memory ~0x0000-0x207F; disk loads at 0x2080
  upward.** How: (a) all boot-ROM call targets span 0x018D..0x1109 (below the
  disk's 0x2080 load base); (b) the runtime region below 0x2080 — interrupt
  vectors (0x2000-0x2011), CCB (0x2018), reset vector (0x2080-area) — is 0x0F
  FILL on the disk (file 0x4780 region), i.e. NOT supplied by the disk. So the
  vectors + reset code + the 14 service routines all live in IC20, resident
  alongside the disk payload. This is the clean split we needed.
- **F54. IC20 service entry points (dump will let us name these):** 0x018D,
  0x0296, 0x0442(x3), 0x045D, 0x0491, 0x04AC, 0x0551, 0x05AA, 0x0B31, 0x0D5D,
  0x0EC7, 0x0F15, 0x0F19(x2), 0x1109. Span 0x018D..0x1109 => IC20 code is at
  least ~4.3KB; the chip is likely 8/16/32KB. Dump a generous range to be safe.
- **F55. RAM map corroborated (data-ref histogram):** heavy 0x0100-0x03FF
  (pointer tables/vars), 0x1B00-0x1FFF (init/flag state), 0x2000-0x207F
  (vector/CCB shadow). Matches the reset routine's RAM clear (0x120-0x1120) and
  pointer-table setup (0x100-0x11D) from F23/F24.

## IC20 dump plan (M4) — mechanism design
- **Target range:** read runtime 0x0000..0x2080 first (covers vectors + all
  known service entry points). If the ROM is larger and stays mapped, extend.
- **Transport (get bytes off the S-760):** two candidates, both use hardware the
  user already has:
  1. **Floppy/Gotek write** — call the OS/boot-ROM disk-write path to store the
     captured bytes into known sectors of a blank .IMG, then read on PC. Cleanest
     (bulk data), but requires identifying a callable sector-write routine.
  2. **MIDI SysEx out** — stream bytes over MIDI from the S-760's MIDI OUT to a
     PC MIDI capture. Slower but simpler if a MIDI-send primitive is easy to call.
- **Trigger/injection:** hook a deliberate, user-initiated action (a key/menu
  event) so the stub runs on demand, after drivers are up — safer than running
  at boot. Need to find the main input/dispatch loop for a safe hook point.
- **CONSTRAINT:** write the stub in MCS-96 machine code, assembled/validated with
  the pypcode decoder (round-trip: our bytes must disassemble back to the intended
  instructions) — do NOT hand-emit opcodes without verifying them.

## Session 9 (cont.) — transport analysis for the dump
- **F56. MIDI is NOT on the MCS-96 on-chip UART.** How: 0 accesses to SBUF /
  SP_STAT / SP_CON SFRs anywhere in the resident code. => MIDI I/O goes through
  external hardware (dedicated UART / gate array) in the memory-mapped window,
  so "MIDI out" is not a trivial SBUF write; it needs a resident/IC20 MIDI-send
  routine. Lowers the appeal of the MIDI-SysEx transport unless we find that
  routine.
- **F57. 0x54E8 is a COMMAND DISPATCHER, not the disk driver.** Reads a command
  byte (via `SCALL 0x56C5` = a get-next-byte primitive), compares 1/2/3..., and
  dispatches; uses `LCALL 0x2E46` (RW1E = string pointer) to show messages
  (strings at 0xDC2C/0xCF5A/0xD7AD). Useful map progress but not the write path.
- **F58. PROPOSED lowest-risk dump approach (TDD-friendly).** Rather than inject
  a from-scratch driver-calling stub (highest risk; hang-on-boot possible, and
  some drivers live in IC20), REUSE the OS's working "Save to disk" path and
  only redirect its SOURCE pointer to IC20's address range (0x0000..). A normal
  save then writes IC20 bytes into a Gotek file we read on PC. Changes a
  pointer+length, not new logic. NEEDS: locate the save routine + where it loads
  its source-buffer pointer/length.
- **OPEN QUESTIONS for the user (to pick the path):** (1) Is there a panel
  "Save" that writes to floppy/Gotek and works? (2) Is a PC MIDI interface
  connected to the S-760 MIDI OUT (would re-enable the SysEx option)?

## Session 9 (cont.) — disk UI operations mapped (piggyback candidates)
- **F59. User has the OP-760-2 video board (monitor + mouse GUI).** The full GUI
  exposes more disk ops than the LCD. This is good: more working disk-write paths
  to piggyback for the IC20 dump.
- **F60. Disk menu operations located (UI strings, file offsets):** a full
  **Disk** menu (0x8BDEA "Disk Menu", 0x955E5 "[ 5: Disk ]") with:
  - **Disk Save** (0x95AF0 / 0x95CA4), **Disk Load** (0x9569C / 0x959C2),
    **Disk Copy** (0x95D8C), **Disk Delete** (0x95F82),
    **Disk Utility -> Format** (0x9674E / 0x96794).
  - **Save System / "SaveSys"** (0x9763A / 0x976A3 / 0x97710) — writes a bootable
    S-760 system disk; sits right next to the "S-760 System Ver. 2.24" header
    banner (0x97665) that gets stamped onto a saved system disk. TOP candidate:
    it bulk-writes a memory region to disk.
  - Also: **Volume Load** (0x8B472), **Quick Load** (0x8FB78), **Disk Copy**
    (whole-disk duplicate — could be useful).
- **NOTE:** these UI handler strings live in the data window beyond the resident
  64KB (file >0x8xxxx), so the handler CODE is likely in a banked overlay not yet
  linearly addressable. The low-level sector-write primitive, however, is
  resident or in IC20. Path forward depends on what the user sees in the GUI.
- **AWAITING USER:** what disk/save/utility options appear in the monitor GUI
  (esp. anything like "Disk Copy", "Save System", a memory/monitor utility, or a
  raw block save). That picks the piggyback target.

## Session 9 (cont.) — "add a menu item?" feasibility + dependency reality
- **F61. Adding a Disk-menu item is a LATE-STAGE feature, not a shortcut.** It
  requires: the menu table (label ptr/position/enable), the menu->handler
  dispatch binding, GUI layout/hit-testing (video board), AND a handler to run.
  Most of that (menu/GUI logic) lives in banked overlays we can't yet address.
  So it bundles ALL the unsolved hard problems together. Lower-risk variant =
  HIJACK an existing bound item rather than add one — but that still needs the
  overlay dispatch table.
- **F62. Critical-path restated.** working data-out transport -> dump IC20 ->
  (IC20 reveals loader/banking) -> address the overlays -> menu/GUI/features.
  The IC20 dump remains THE unlock; it must NOT depend on GUI/menu work.
- **F63. Possible RESIDENT peripheral data/status port at 0xE000/0xE002.**
  How: 0xE000 (x5) and 0xE002 (x2) accessed in resident code, distinct from the
  0xF0xx control-latch window. Candidate FDC (uPD72068) or SCSI (MB89352A)
  data/status register pair — i.e. a resident low-level disk primitive may be
  reachable without overlays. (Other 0xExxx/0xFxxx hits are likely misdecoded
  operands, not real I/O — needs targeted disasm to confirm.) This is the thread
  to pull for a resident, GUI-independent dump trigger.
- **DECISION POINT for the user:** two ways to get the transport:
  (A) Keep statically reverse-engineering the resident FDC/SCSI write primitive
      around 0xE000 until we can call it from a small resident stub (safer to
      analyze, slower; risk = calling it wrong hangs the unit — always keep the
      good image to reflash the Gotek).
  (B) Accept a bit more hardware risk and iterate empirically on hardware via the
      Gotek (patch a resident hook to call a candidate write routine, boot, see
      if a known byte pattern lands on a blank disk) — TDD-style, small steps.

## Session 10 — Path B (test-driven injection): scratch space found
- **F64. Path B milestone ladder (tiny, reversible, hardware-verified):**
  - B0: prove injected code RUNS + is observable (visible on-screen effect). No
    disk-write risk.
  - B1: prove injected code can CALL a resident subroutine and see its effect.
  - B2: map + call the disk-write primitive; write a known pattern to a blank
    Gotek disk; read back on PC (transport proven).
  - B3: point the transport at IC20 (0x0000..) => the dump.
  Each step = one small size-exact patch on a COPY, booted via Gotek; keep the
  known-good image to reflash on any failure.
- **F65. Safe scratch area for a stub = runtime 0x5DBE (file 0x853E), ~8KB of
  0x00.** How: it sits immediately AFTER a clean jump table (0x5DA0-0x5DBD:
  `PUSHA; LJMP <handler>` entries ending `POPA; RET`) and before code resumes at
  runtime 0x7D00 (file 0x10480). 8002 bytes of zero-fill = ample, unused padding.
  Two more smaller gaps exist (0x59CE/978B, 0x9954/812B, 0xD2FA/390B).
- **F66. B0 hook design (PENDING user go-ahead before hardware).** Need a
  resident, reliably-executed instruction to redirect into the stub and back.
  Candidate approach: replace one resident CALL/among the init sequence with a
  call to our stub at 0x5DBE; stub writes a sentinel into the displayed version
  string RAM (proving execution) then performs the original call and returns.
  Must assemble the stub as MCS-96 bytes VERIFIED by round-trip through pypcode
  (disassemble our bytes -> confirm intended instructions) before patching.

## Session 10 (cont.) — 0x2E46 is a DISPATCH TRAMPOLINE (likely the bank/overlay call)
- **F67. Routine 0x2E46 = register-saving indirect-call trampoline `BR [RW1E]`.**
  Decoded:
  `PUSH 0x106; PUSH RW38/3A/3C/3E/46; ST RW1C,0x106; PUSH #0xCDDE; BR [RW1E];`
  ... on return `POP` all; `RET`. So the caller convention is:
  `LD RW1C,#<param>; LD RW1E,#<target_addr>; LCALL 0x2E46` -> it saves context,
  stashes RW1C into slot 0x106, pushes a common return (0xCDDE), and branches to
  the address in RW1E. This is a generic indirect-call/thunk.
- **F68. The RW1E targets cluster in 0xC000-0xE9FF** (0xDD77, 0xCF82, 0xDC2C,
  0xD3AB, 0xDAE4, 0xD7CF, 0xE1E1, 0xE7A2, 0xE914, 0xE8ED, 0xDE9C...). These are
  in the upper resident window. Strong candidate for the OVERLAY / bank-call
  entry region: resident code reaches banked or upper-image routines via this
  trampoline + the RW1C selector in slot 0x106. This is likely the missing
  banking convention (relates to F31/F40 selector-in-0x104 idiom — note 0x104 vs
  0x106; both are pointer-table slots set right before dispatch calls).
- **IMPLICATION:** once we can dump/read those target routines, the trampoline +
  selector give us a clean way to CALL overlay code from an injected stub (useful
  for B1/B2). For B0 we don't need it.

## Session 10 (cont.) — display path: peripheral windows + plan for visible B0
- **F69. Candidate display/peripheral I/O windows (resident code):**
  - **0xC000-0xC016** and **0xC400-0xC40C**: hot (0xC014 x74 = likely a data
    register hit in tight loops), strong display-controller candidates.
  - **0xD008-0xD040** (0xD018 x23, 0xD040, 0xD010...): a second peripheral.
  One of the C0xx/C4xx/D0xx windows is the Epson SED1335 LCD, another is the
  OP-760 VDP (monitor). (Note: 0xDC2C/0xD3AB/0xDAE4 in the list are trampoline
  TARGET addresses from F68, not I/O — false positives.)
  - Controller-type byte 0x8FBA is referenced at 0x2847 (the boot check that
    picks RC-100 / +CRT); gates whether video output is active.
- **F70. Chosen approach for visible B0: reuse the OS's OWN display routine via
  the 0x2E46 trampoline (F67), not a hand-written VDP/LCD driver.** Rewriting the
  VDP/SED1335 protocol from scratch is heavy and error-prone (ambiguous first
  test). Instead the stub will set RW1C/RW1E and `LCALL 0x2E46` to invoke the
  resident "display string" routine with a pointer to our own text. This is both
  visible-on-monitor and low-risk (calls working code), and doubles as the B1
  "call a resident subroutine" capability. NEXT: identify which trampoline target
  is the string/display service and its exact arg convention (what RW1C means,
  where the string pointer goes), by decoding a few targets (0xDD77, 0xCF82,
  0xDC2C) that are called right before/after on-screen messages.

## Session 10 (cont.) — B0 delay-injection image built (awaiting hardware test)
- **F71. B0 approach = delay loop (unambiguous A/B vs a normal boot).** Since the
  user has no boot-time baseline yet, made the delay LARGE (~5x10^7 DJNZW iters)
  so the patched image reaches the screen clearly later than the original/9.99
  images. Safest possible stub: touches only 2 scratch registers + rejoins boot.
- **F72. B0 stub (verified via pypcode round-trip) @ runtime 0x5DBE / file
  0x853E:**
  `A1 00 03 42` LD RW42,#0x300 ; `A1 FF FF 40` LD RW40,#0xFFFF ;
  `E1 40 FD` DJNZW RW40,self ; `E1 42 F6` DJNZW RW42,reload-inner ;
  `E7 62 CA` LJMP 0x2831 (continue boot).
  Bytes: `A1000342A1FFFF40E140FDE142F6E762CA`.
- **F73. B0 hook @ runtime 0x218B / file 0x490B:** original `E7 A3 06`
  (LJMP 0x2831, the reset routine's normal jump into main init) -> replaced with
  `E7 30 3C` (LJMP 0x5DBE). Confirmed original bytes before patching.
- **F74. Image `temp/work/S760_B0_delay.IMG` built + verified.** Byte-exact vs
  original except the stub (17B in scratch) and the 3-byte hook; size 0x168000.
  TEST PROTOCOL for user: (1) boot original/9.99 image, note time to screen;
  (2) boot S760_B0_delay.IMG. If it reaches the screen clearly LATER (~seconds)
  AND still boots normally, B0 PASSES = injected code runs + returns cleanly.
  Keep original handy to reflash. If it hangs/never boots, B0 fails -> revert,
  diagnose (hook math / register clobber).

## Session 10 (cont.) — B0 PASSED on hardware
- **F75. B0 PASSED: injected code runs + returns cleanly on real hardware.**
  User booted `S760_B0_delay.IMG`: a long, obvious delay occurred BEFORE the OS
  screen finished drawing, then the OS came up normally. Confirms end-to-end:
  (1) we can execute arbitrary injected MCS-96 code at a chosen boot point, (2)
  our stub at 0x5DBE runs from the scratch area, (3) the LJMP-back rejoins boot
  with no ill effects, (4) the hook fires where expected (end of reset, pre main
  init / pre screen-draw — consistent with the delay appearing before the screen).
  This is the foundation capability for B1-B3. First code-injection milestone. ✅
- **NEXT (B1): call a resident subroutine from injected code + observe.** Build
  toward visible on-screen text by using the OS's own routines (e.g. the 0x2E46
  trampoline / a display worker), which also gives us the "obvious on monitor"
  signal the user wants.

## Session 10 (cont.) — B1 image built (call a resident routine)
- **F76. 0x218E verified self-contained + safe to call:** `PUSH RWDA; LDB
  RDA,#0; loop{NOP; DJNZ RDA}; POP RWDA; RET`. Saves/restores its own register,
  no args. Ideal known-good call target.
- **F77. B1 stub (verified via pypcode) @ 0x5DBE / file 0x853E:**
  `A1 40 01 44` LD RW44,#0x140 ; `B1 FF 46` LDB R46,#0xFF ;
  `EF C6 C3` LCALL 0x218E ; `E0 46 FA` DJNZ R46,inner ;
  `E1 44 F4` DJNZW RW44,outer ; `E7 60 CA` LJMP 0x2831.
  = ~81,600 calls to the OS's own delay routine, then continue boot. Stack stays
  balanced (stub entered/exited via LJMP; LCALL/RET pairs self-balance).
  Bytes: `A1400144B1FF46EFC6C3E046FAE144F4E760CA`. Hook unchanged from B0.
- **F78. Image `temp/work/S760_B1_call.IMG` built + verified** (21 bytes differ:
  hook + 19B stub; size 0x168000). TEST: boot it. PASS = visible delay + normal
  boot (proves injected code can LCALL a resident routine ~81k times and handle
  every return). This validates the call/return mechanism that B2 (calling the
  disk-write primitive) depends on.

## Session 10 (cont.) — B1 PASSED on hardware
- **F79. B1 PASSED: injected code can LCALL a resident OS subroutine and handle
  the return.** User booted `S760_B1_call.IMG`: visible delay (from ~81,600
  LCALLs to 0x218E), then normal boot. Confirms the call/return mechanism works
  from our stub — LCALL resolves correctly, the OS routine runs and returns, the
  stack stays balanced across tens of thousands of calls, and boot continues.
  This is the prerequisite for B2 (calling the disk-write primitive). ✅
- **B-ladder status:** B0 ✅ (execute injected code), B1 ✅ (call resident code).
  NEXT = B2: identify the disk-write (sector-write) primitive, call it from the
  stub to write a KNOWN byte pattern to a blank Gotek disk, read it back on PC.
  That proves the off-machine transport and sets up B3 (dump IC20).

## Session 11 — B2 recon: locating the disk-write primitive
- **F80. 0xE000/0xE002 accesses cluster in ONE routine (~0x2DD0-0x2E2B).** It
  reads a status/result (via `SCALL 0x2B6B`), compares against 8/9/0xA (error/
  status codes), and reports via `LCALL 0x6100` with message codes in R48
  (0xAC/0xAD/0x0B). This looks like a peripheral STATUS/ERROR handler, not the
  raw sector-transfer loop. Low-level primitives it uses: **0x2B6B** (get byte /
  read result), **0x2B80** (called in an R46-count loop = send/process byte),
  **0x2B14**. 0xE000=status, 0xE002=data (byte-at-a-time handshake).
- **F81. This 0xE00x path is byte-handshake style** (poll 0xE000, move byte via
  0xE002) — consistent with SCSI (MB89352A) OR a handshaked FDC path. NOT yet
  confirmed as the floppy sector writer. Do NOT call it blindly for B2 (wrong
  routine/args could corrupt a disk or hang).
- **B2 SAFETY PLAN (revised):** before calling any writer, positively identify
  the floppy sector-write routine + its argument convention (buffer ptr, sector/
  track, length). Approaches: (a) map 0x2B6B/0x2B80/0x2B14 + 0x6100 to see if
  this is SCSI or FDC; (b) find the resident FDC (uPD72068) command sequences
  (write-data command byte, then 512-byte loop); (c) correlate with the "Disk
  Save"/format handlers. Only then build B2 (write a KNOWN pattern to a scratch
  sector on a BLANK Gotek disk, read back on PC). Keep the write target on a
  throwaway blank image, never a disk we care about.

## Session 11 (cont.) — FDC vs SCSI disambiguated (critical for B2 safety)
- **F82. FDC (uPD72068) window = 0xC000-0xC016 (+ companion 0xD010/0xD012);
  distinct from the SCSI 0xE000/0xE002 path.** How: (a) MSR-poll idiom at 0x2C51
  `LD RWDA,0xC002; JBS RDA,0x5` (status bit test) then clears 0xC002/0xC000 and
  0xD012/0xD010, reads 0xC016 — classic FDC status/interrupt servicing; (b) the
  FDC init/seek command immediates SPECIFY(0x03), RECAL(0x07), SEEK(0x0F),
  SENSE-INT(0x08) cluster densely in 0x44xx-0x59xx (the FDC driver). uPD72068 is
  uPD765-family; Roland wraps it via the gate array (hence both 0xC0xx and
  0xD0xx). => **Floppy path = 0xC0xx/0xD0xx; SCSI path = 0xE00x.** For B2 we must
  drive the FDC (0xC0xx) route and AVOID the 0xE00x SCSI route (user has no SCSI).
- **F83. FDC driver body is ~0x44xx-0x59xx** (SPECIFY/RECAL/SEEK/SENSE-INT
  sequences), with the status ISR near 0x2C40-0x2C8B. WRITE-DATA command byte
  (0x45/0xC5) not seen as a literal -> likely computed (OR'd with MFM/MT bits) or
  issued from a command table; needs targeted decode to find the sector-write
  entry + its (buffer, C/H/S, count) argument convention.
- **F84. B2 remains gated on positively identifying the FDC sector-WRITE entry
  point + args.** Init/seek commands are found; the write DATA path + how a RAM
  buffer is handed to the FDC (DMA vs programmed I/O via 0xC0xx data reg) is the
  remaining unknown. Next: decode the 0x44xx-0x59xx driver to find the write
  entry, OR pursue a lower-risk transport (see decision below).

## Session 11 (cont.) — "Save System" confirmed in GUI: reframes the dump
- **F85. User confirms GUI Disk menu -> "Save System" -> "SaveSys" exists** and
  (per the labels) writes the OS + settings to a disk = produces a bootable
  system disk. This is a FULLY-WORKING, user-triggered, self-verifying write path
  that reads system memory and writes it to floppy in the S-760 format. Exactly
  the capability the IC20 dump needs.
- **F86. KEY REFRAME: a normal Save System is a zero-risk, high-value experiment.**
  If the user does an UNMODIFIED "Save System" to a BLANK Gotek disk and brings
  the image back, we can diff it byte-for-byte vs S760224.IMG to learn: (a) which
  memory regions the save captures, (b) whether low memory / IC20 (0x0000-0x207F)
  is already included, (c) the on-disk layout/format the saver produces (which
  reveals how source memory maps to sectors). No patching -> cannot hang. This
  may even yield IC20 for free if Save System writes low memory.
- **PLAN:** 
  1. (User) Format/prepare a BLANK disk on the Gotek (or use our BLANK_1440
     image), run Disk menu -> Save System -> SaveSys to it, copy the resulting
     .IMG back to the PC.
  2. (Agent) Diff vs original; map captured regions; check for 0x0000-0x207F.
  3. If IC20 not included, we know the save's source range and can (M4) redirect/
     extend it to include low memory — a pointer/length change on a known-good
     path, far safer than a raw FDC write stub.
- **NOTE:** this supersedes the need to hand-build a raw FDC sector-write stub
  for the dump (B2/B3) unless the Save System path proves unsuitable.

## Session 11 (cont.) — capturing a real formatted disk too
- **F87. User is formatting a blank disk on the S-760 before SaveSys.** The
  formatted-empty disk is itself valuable: it reveals the real S-760 empty-volume
  layout (allocation region, empty directory/catalog, confirms the 0x0F meaning)
  and can be compared to the "S-760 Formatted Disk" banner template at 0x0AC948.
- **F87b. UPDATE: "Save System" formats AND saves in one step** (no separate
  formatted-blank stage exposed). So we get ONE output image `savesys_output.IMG`.
  Analysis plan: diff it vs the factory `S760224.IMG` to see which regions match
  (system payload) vs differ (per-unit settings / format metadata), and check
  whether low memory / IC20 (0x0000-0x207F) appears anywhere. Put it in temp/work/.

## Session 11 (cont.) — SaveSys output analyzed (BIG results)
- **F88. SaveSys writes essentially the FACTORY system image** (344/360 4KB
  blocks identical to S760224.IMG; only 993 bytes differ across 105 runs). This
  validates our entire disk-format model and confirms SaveSys = "write the系统
  OS to disk in S-760 format."
- **F89. SaveSys CAPTURES LIVE SYSTEM RAM — including our injected code.** The
  disk used for the save was the **B1 test image**, and the save output contains
  our B0/B1 artifacts: the hook at file 0x0490C (`A3 06`->`30 3C`) and the B1
  stub at 0x0853E. => SaveSys reads the running OS out of memory and writes it
  back. Our patches persist in the live system exactly as placed. (Also means:
  to get a CLEAN factory-equivalent save, boot the unmodified original.)
- **F90. SaveSys does NOT capture IC20 / low memory.** The vector/low region
  (file 0x4600-0x4800 = runtime <0x2080 = IC20 space) is 0x0F fill in BOTH
  factory and saved images. So SaveSys writes only the disk payload (runtime
  0x2080+). => SaveSys alone won't dump IC20, BUT it is now a proven, understood
  write path we can REDIRECT to include low memory (M4).
- **F91. Genuine per-unit differences captured by SaveSys:**
  - Controller string "RC-100" -> "Mouse " at file 0x08801E and 0x0BD367 (user
    switched to the video board + mouse; this is a real saved setting). Good
    anchor: maps a UI/config string to a live setting.
  - MS-DOS FAT12 boot-sector template (x86 code + `IO SYS`/`MSDOS SYS` +
    `55 AA`), factory 0x088656-0x0B7F1C region, is ZEROED in the save. SaveSys
    doesn't emit the DOS interchange template (only written when formatting a DOS
    floppy). Confirms F7's "it's a data template, not S-760 code."
  - Small setting/counter bytes: 0x0BA5B2 (35->36), 0x0F483D/0x0F483F ("17"->"01"
    — likely a date/version/serial field). Candidate settings/RTC fields.
- **F92. IMPLICATION for the dump (M4):** we now have a fully-working, understood
  memory->disk writer (SaveSys) whose SOURCE is the disk-payload RAM. The clean
  path to IC20 = find where SaveSys reads its source region and extend/redirect
  it to also emit runtime 0x0000-0x207F. Since IC20 is resident low RAM/ROM, a
  small change to the save's source range should capture it — far safer than a
  hand-built FDC write stub. This is the new M4 plan.

## Session 11 (cont.) — BETTER dump plan: copy IC20 into the SaveSys-captured RAM
- **F93. Driver region 0x4480+ is drive-status/table logic, not the raw FDC
  transfer loop** (dispatches on RDC command codes 0x0B-0x0D, reads per-drive
  status at 0x2169-0x216B, sets/clears carry). The `#0x3` immediates are status
  values, not FDC SPECIFY. So the raw sector-write entry is elsewhere; and the
  SaveSys handler is in a banked overlay we can't linearly reach. Tracing either
  fully is slow.
- **F94. KEY INSIGHT — skip both. Combine our proven injection (B0/B1) with
  proven SaveSys.** SaveSys captures live RAM in the disk-payload range (runtime
  0x2080+ -> disk file 0x4800+, linear; it captured our injected stub). So:
  1. Inject a boot stub (like B0/B1) that does a MEMORY COPY: source = IC20 low
     region runtime 0x0000..0x2080 (0x2080 = 8320 bytes), dest = an unused RAM
     area INSIDE the SaveSys-captured range (candidate: our scratch 0x5DBE, ~8KB;
     or a larger unused RAM window if IC20 > scratch).
  2. Continue boot normally.
  3. User runs SaveSys to a blank Gotek disk.
  4. IC20's bytes come out embedded in the saved .IMG at a known disk offset
     (dest_runtime - 0x2080 + 0x4800). Read them on PC.
  - RISK: near-zero. The stub only copies RAM (no disk I/O, no FDC, like the
    delay loop). No new driver code. Reuses two proven capabilities.
  - SIZE NOTE: IC20 source is up to 0x2080 (8320) bytes; the 0x5DBE scratch is
    8002 bytes — slightly too small. Either dump IC20 in two passes, or find a
    larger unused RAM window in the captured range. TBD next.
- **NEXT:** pick a dest RAM window >= 0x2080 bytes that (a) is within the
  SaveSys-captured payload range and (b) is unused/safe to overwrite; then build
  the copy stub (verified via pypcode) for a hardware test.

## Session 11 (cont.) — IC20 dump image built (copy-to-RAM + SaveSys)
- **F95. Dump stub built + verified: `temp/work/S760_DUMP_ic20.IMG`.** Boot-time
  copy stub @ 0x5DBE (verified via pypcode):
  `LD RW40,#0x0000; LD RW42,#0x5E20; LD RW44,#0x1EE0;`
  `loop: LDB RB0,[RW40]+; STB RB0,[RW42]+; DJNZW RW44,loop; LJMP 0x2831`.
  Copies low memory 0x0000..0x1EE0 (7904 bytes) into scratch RAM at 0x5E20
  (after the stub), then continues boot. Hook = same as B0/B1 (file 0x490B ->
  LJMP 0x5DBE). Bytes: `A1000040A1205E42A1E01E44B241B0C643B0E144F7E75BCA`.
  Pure RAM copy = near-zero risk (no I/O, like the delay loop). Confirmed the
  MCS-96 indirect-autoincrement encodings (LDB `B2 41 B0`, STB `C6 43 B0`) decode
  correctly via pypcode. Image verified: only hook(2B)+stub(24B) differ; size OK.
- **F96. DUMP PROCEDURE (user):**
  1. Boot `S760_DUMP_ic20.IMG` from the Gotek. (Boots normally; the copy is
     instant, no visible delay.)
  2. In the GUI: Disk menu -> Save System -> SaveSys, save to a BLANK Gotek disk.
  3. Copy the resulting .IMG back to `temp/work/` (e.g. `dump_result.IMG`).
  The captured low-memory (IC20) bytes will be embedded at **file offset
  0x0085A0 .. 0x00A480** in that saved image (= dest 0x5E20 mapped via
  runtime->disk: 0x5E20-0x2080+0x4800). Agent extracts + analyzes that range.
- **NOTE:** first pass covers 0x0000-0x1EE0. If IC20 extends to 0x2080 we do a
  2nd pass for the remaining ~0x1A0 bytes; but 0x018D-0x1109 (all known service
  entries) + vectors are within this range, so one pass likely suffices.

## Session 11 (cont.) — possible freeze on SaveSys with the dump image (WATCH)
- **F97. User reports the OS MAY have frozen when selecting SaveSys on the dump
  image `S760_DUMP_ic20.IMG`.** Boot itself was fine (as expected — same hook as
  B0/B1 which booted OK). If a freeze is real, prime suspect = our stub
  OVERWROTE the 0x5DBE-0x7D00 scratch with the IC20 copy, and that region may
  NOT be truly free RAM — the OS (or SaveSys specifically) might use it as a
  buffer. "Zero at boot" != "unused at runtime". This would corrupt a buffer
  SaveSys relies on -> hang.
  - NOTE: recall SaveSys captures LIVE RAM (F89). If the OS overwrote our copy in
    that region before the save anyway, the dump could also just be stale — but a
    freeze points to us clobbering a live buffer.
- **RECOVERY:** power-cycle; reflash Gotek with the known-good original; hardware
  is unaffected (disk-image issue only, nothing persists on the S-760).
- **FIX OPTIONS if confirmed:**
  1. Choose a dump destination that is provably OS-unused AND SaveSys-captured.
     The safest candidate: a region the factory image already treats as
     free/unused within the saved payload (e.g. one of the OTHER zero gaps:
     0x59CE/978B, 0x9954/812B, 0xD2FA/390B) — but each is <IC20 size; may need
     multiple small dumps.
  2. Better: don't rely on scratch at all. Have the stub copy IC20 into a spot,
     but VERIFY via a small first test that the chosen region survives to the
     saved output (dump a tiny known pattern, SaveSys, check it lands) BEFORE
     dumping the real thing. TDD: prove the container works with a sentinel first.
- **STATUS: awaiting user confirmation (frozen vs just slow).**

## Session 11 (cont.) — course correction: verify the dump container first
- **F98. Outcome of the dump attempt is UNREADABLE (user can't tell frozen vs
  slow).** Lesson: don't fire hardware attempts whose outcome we can't observe.
  The dump approach had an unverified assumption (0x5DBE scratch survives intact
  through SaveSys). Fix the METHOD, not just retry.
- **F99. How to judge frozen vs working (for the user):** Gotek activity LED /
  display flicker = disk access in progress (not frozen); mouse cursor still
  moving = OS not fully locked; quiet + unresponsive for ~2 min = likely hung.
  Recovery is always safe: power-cycle + reflash the original; hardware untouched.
- **F100. NEW METHOD — sentinel-first (TDD).** Before copying the real ~8KB IC20
  blob, patch a stub that writes a TINY known pattern (e.g. ASCII "IC20DUMP" +
  index bytes) into the candidate dest, boot, SaveSys. Read the saved image:
  - sentinel present at expected offset => dest is SaveSys-captured AND OS-safe;
    scale up to the real dump with confidence.
  - sentinel absent / SaveSys hangs => dest is bad; learned cheaply (trivial
    patch, no big clobber). Also isolates the freeze cause: a 12-byte write can't
    break SaveSys, so if the full-dump image hangs but the sentinel image saves
    fine, the large scratch overwrite was the culprit.
- **ACTION:** (user) give it ~2 min, power-cycle, reflash original, verify normal
  boot; optionally drop the saved-to blank in temp/work/ (even a partial save is
  diagnostic). (agent) build the sentinel-container test next.

## Session 11 (cont.) — Gotek LED reading
- **F101. Gotek LED is SOLIDLY LIT (not flickering).** Interpretation: on
  Gotek/FlashFloppy the activity LED FLICKERS during real read/write transfer; a
  STEADY solid LED = drive selected / motor-on but NOT actively transferring.
  Combined with no visible progress, this leans toward HUNG (drive selected,
  waiting) rather than an in-progress save. Not 100% conclusive; the reliable
  tell is change over ~30s — any flicker = working; rock-steady = hung.
- **F102. CONFIRMED: the dump stub hung SaveSys.** Gotek LED solid, zero flicker
  over 30s = drive selected, no transfer = hung. The IC20 copy clobbered the
  0x5DBE scratch, which the OS/SaveSys uses as a LIVE buffer -> "zero at boot" !=
  "free RAM". Root cause: injected a large overwrite into an UNVERIFIED-free
  region. Recovery: power-cycle + reflash original (hardware unaffected).
- **F103. Corrected requirements for a dump destination:**
  (a) inside the SaveSys-captured payload range (runtime 0x2080+),
  (b) PROVABLY unused by the OS/SaveSys at the time of the save,
  (c) verified by a SENTINEL test (tiny marker) BEFORE any large copy.
  The 0x5DBE scratch fails (b). Note also: 0x5DBE was ZERO on the FACTORY disk
  but is clearly used at runtime. Need a destination whose survival we prove
  empirically, not assume. Candidate strategy: write the sentinel to several
  candidate offsets at once and see which survive SaveSys (one image tests many
  spots).

## Session 11 (cont.) — correction: "captured RAM" IS the live OS
- **F104. RETRACT the naive 'find untouched RAM' approach.** A scan for RAM
  buckets never referenced as data operands mostly returns CODE regions (the
  resident 0x2080+ image is code+const loaded into RAM). "Not a data operand
  target" = "it's code," and writing there corrupts code. So most of the
  SaveSys-captured range is NOT free — it's the live OS. This is exactly why the
  0x5DBE overwrite hung SaveSys (F102).
- **F105. Reframed problem.** The SaveSys-captured region ~= the running OS
  image; there isn't an obvious large free-RAM hole inside it we can safely fill
  with an 8KB dump. Genuine scratch/variable RAM (0x0100-0x03FF, 0x1B00-0x1FFF,
  data windows) is small, scattered, and live. So "copy IC20 into captured RAM
  then SaveSys" is fragile.
- **RE-STRATEGIZE — options to get IC20 out (pick next):**
  1. **Tiny multi-sentinel probe:** write a few-byte marker to several candidate
     offsets, SaveSys, see which survive. Low risk; finds any genuinely-free
     captured bytes (may only be a few here and there -> dump IC20 in many small
     pieces across boots; tedious but safe).
  2. **Dump via the DISPLAY instead of SaveSys:** show IC20 bytes as hex on the
     monitor (reuse the OS display path) and read/photograph them. IC20 ~8KB is a
     lot of screens, but chunkable; no disk-buffer risk.
  3. **Reverse the raw FDC sector-write (0xC0xx) after all** and have our stub
     write IC20 directly to specific disk sectors on a blank Gotek image, bypass
     SaveSys entirely (our stub controls the buffer, so no live-buffer clobber).
     More upfront RE, but clean and fully under our control.
  4. **Find where SaveSys STAGES its data** — if SaveSys copies the payload into
     a work buffer before writing, appending IC20 to that buffer (or extending
     its length) rides the real writer. Needs the SaveSys handler (overlay).
- **STATUS: recover hardware (reflash original), then choose a re-strategy.**

## Session 12 — FDC (0xC0xx) register map decoded [hardware recovered OK]
- **F106. Hardware recovered:** power-cycle + reflash original -> normal boot.
  Confirms the freeze was purely the bad disk image (scratch clobber), nothing
  persistent. Safe to continue.
- **F107. FDC gate-array register map (0xC0xx) — NOT a bare uPD765; Roland gate-
  array wrapper with a DMA-style transfer engine:**
  - **0xC000/0xC002** — status/control low pair (0xC002 read + bit-tested at
    2C51 `JBS ...,5`; both cleared to reset).
  - **0xC00C/0xC00E** — WRITE-ONLY pair, always written TOGETHER = a 16-bit
    ADDRESS latch (transfer source/dest addr). (98FD/9902, CD67/CF93, D237/D23C.)
  - **0xC010/0xC012** — read+write pair, always together = a 16-bit COUNT or 2nd
    address (8474/847B, 84F1/84F8, 85A4/85AB).
  - **0xC014** — WRITE-ONLY, 74 writes, hot, tight sequences = data/command FIFO
    (command bytes + transfer data pushed here).
  - **0xC008/0xC016/0xC01A-0xC01E** — control/reset strobes (written w/ ZR/once).
  => Likely a **memory-mapped DMA transfer**: program addr (C00C/E) + count
     (C010/12), push command to FIFO (C014), hardware moves the block. If so, we
     can set addr=IC20, count, and trigger a WRITE to disk — no 512-byte manual
     loop. Core transfer routine cluster ~0x8460-0x85B0 (hot C014 + C010/12).
- **NEXT:** decode 0x8460-0x85B0 to learn the exact write/transfer sequence +
  its args (addr reg, count reg, command values, which C0xx triggers the go).
  Then sentinel-test: write a known pattern to ONE sector of a blank, read back.

## Session 12 (cont.) — FDC transfer protocol is SELECT-then-WRITE w/ timing
- **F108. The 0x8460 transfer routine uses a register-indexed FIFO protocol:**
  for each parameter it (1) strobes a SELECT register (0xC200 or 0xC400-0xC40C,
  written with ZR, indexed by RW60), then (2) writes the value byte(s) to the
  0xC014 FIFO. Every I/O access is separated by `FD FD` (NOP NOP) = required
  gate-array timing delays. Parameters are read from a table at
  **0x4014-0x401B** (indexed by RW7C): pairs at 0x4014/16, 0x4018/1A pushed as
  16-bit values; a command bit is OR'd in (`SHRL RL5C,#8; ORB R5F,R6B` @84C8).
  0xC010/0xC012 are read then written back around the sequence (save/restore or
  transfer addr/count).
- **F109. This is intricate + risky to replicate blind.** Getting the select
  sequence, command bits (R6B), timing NOPs, or the 0x4014-table args wrong could
  hang or mis-write. 0x8460 also appears to be MID-routine (starts with
  `XCH ZR,RWC4`) — real entry is earlier; need the entry + arg convention + what
  op it performs (seek? write? format?).
- **DECISION — reduce risk before building a writer:**
  * Option 3a (SAFEST validation): find the routine that writes ONE sector and
    identify its args by reading callers, THEN sentinel-test writing a known
    pattern to a single sector of a BLANK disk (not SaveSys) and read back.
  * Consider: this select/write/timing protocol is complex enough that calling
    an EXISTING higher-level "write sector(s)" routine (with correct args) is
    safer than replicating the low-level sequence ourselves. Find that routine.
- **NEXT:** find 0x8460's true entry + callers; identify a callable "write N
  sectors from buffer to (track,sector)" routine + its argument registers.

## Session 12 (cont.) — FDC writer is deep; step back and re-scope
- **F110. The FDC write path is deeply overlay-intertwined + protocol-complex.**
  0x8460 transfer routine has only ONE resident caller (0x86BA->0x85C4); 0x85C4
  is state/flag logic (calls 0x8B28/0x8AC6), not a clean "write sector(s)" entry.
  Most callers are in overlays we can't linearly read. Finding a cleanly-callable
  writer with a known arg convention (buffer, track, sector, count) is a LARGE RE
  effort, and a wrong first write is risky. We've now hit this same overlay/
  complexity wall from 3 angles (SaveSys internals, FDC driver, menu handlers).
- **F111. RE-SCOPE the dump.** We don't necessarily need a full 8KB IC20 image.
  What we actually want IC20 for: (a) the loader/banking mechanism, (b) the
  boot-ROM service ABI (routines at 0x018D..0x1109 + vectors). That's a few KB of
  specific routines, not the whole chip.
- **STRATEGIC OPTIONS (need user steer):**
  1. **Persist with FDC writer RE** (option 3): more tracing to find/verify a
     callable sector-write; safest validated by a single-sector sentinel. Slow.
  2. **Display-to-monitor dump** (option 2), but SMART: reuse the OS's own hex/
     value display (it already shows hex addresses/values in the editor UIs), or
     write our own tiny "byte -> 2 hex chars -> screen" via a confirmed display
     primitive. Photograph screens; OCR the hex. ~8KB is many screens but we can
     dump just the needed routines. Very low hardware risk.
  3. **Static-only:** stop trying to dump IC20; infer the boot-ROM ABI purely
     from resident call sites (what regs/RAM are set before each 0x0xxx call,
     what's used after). Gets us the INTERFACE (enough to patch/extend the OS)
     without the bytes. Zero hardware risk. Doesn't get loader/banking internals.
- **RECOMMENDATION:** if the goal is modifying/extending OS features, option 3
  (ABI inference) may be ENOUGH and is zero-risk; pursue the actual IC20 bytes
  (option 1/2) only if we specifically need the loader/banking internals.

## Session 12 (cont.) — PIVOT to UI overhaul (user's goal)
- **F112. User goal: modernize the UI, then add features.** This sidesteps the
  IC20/FDC wall — UI is largely text strings + layout data + drawing code, much
  already located in the image and patchable (no checksum, proven round-trip).
- **F113. UI difficulty tiers:**
  - T1 Text/labels (EASY, PROVEN): rename/reword menus, labels, messages — pure
    string edits at known offsets. Did this already (Ver 2.24->9.99 on hardware).
  - T2 Static layout/content (MED): reorder menu items, spacing/alignment of the
    fixed-width, space-padded screens; needs menu/screen table mapping.
  - T3 Visual style/graphics (HARD): fonts, pixels, colors, drawing routines —
    VDP/LCD protocol + overlay draw code (behind the wall).
  - T4 New screens/widgets/nav (HARDEST): drawing + dispatch, mostly overlays.
- **F114. UI string catalog built -> `docs/06-ui-string-map.txt`** (all printable
  runs in the resource band 0x86000-0xC2000 with file offsets). Reveals the full
  menu tree: top menus (Perform/Patch/Partial/Sample/Disk/System) with numbered
  subitems (`[ 1: System PRM ]` ...), sample ops (Time Stretch/Rate Convert/
  Truncate/...), MIDI labels, status msgs ("Please Wait", "Waiting for Trigger").
  T1 relabel/reword is immediately doable.
- **NEXT:** get user's definition of "modern" (reword/clarify text? reorganize
  menus? visual restyle?) to pick the tier. T1 is the proven, safe starting point
  and the foundation for the rest.

## Session 12 (cont.) — graphical restyle: hunting the font (inconclusive)
- **F115. Graphical restyle = highest tier (T3).** Best first target = the FONT
  glyph table: editing it restyles all text screens at once with no drawing-code
  changes. Two possible display targets: video board VDP (color, tile/char) and
  built-in LCD (SED1335, mono 160x64).
- **F116. Font location NOT yet confirmed on disk.** A loose "structured bits"
  scan pointed at 0x0F9400-0x0F98C0, but rendering it showed a repetitive stripe
  DATA table, not glyphs (that's the 0x0F0000-0x0F9FFF "sparse tables" region).
  A stricter "blank-space-then-visible-digits" detector produced 623 scattered
  false positives across the code region -> not specific enough.
- **F117. KEY OPEN QUESTION: is the font on the DISK or in a character-generator
  ROM?** Many systems keep the font in hardware: the Epson SED1335 LCD often uses
  an external CG-ROM, and the video-board VDP has its own font/char ROM. If the
  font is in ROM (IC20-adjacent or a CG-ROM), disk-patching CANNOT restyle it,
  which would limit a graphical restyle to whatever glyph data IS on disk.
  Must resolve this before promising a font-based restyle.
- **APPROACHES to resolve:** (a) find where the display code reads glyph data
  (trace the char-draw routine's source pointer -> tells us if it's disk-loaded
  RAM or a fixed ROM/CG address); (b) look for a disk region shaped like a real
  font (96 or 128 cells, space=blank, letterforms) with a tighter renderer; (c)
  accept that pixel-level font may be in ROM and instead restyle what IS on disk:
  layout, spacing, any on-disk graphics/logos, and (for the video board) palette/
  color tables if present.
- **REALITY CHECK for the user:** a full pixel-level graphical restyle depends on
  the font/graphics being disk-resident (patchable). If key glyph/graphics data
  is in hardware ROM, the restyle scope narrows to layout + on-disk assets. Need
  to determine which before committing.

## Session 12 (cont.) — MONITOR (VDP) is the target; VDP is CPU-addressable VRAM
- **F118. User scope narrowed: restyle the MONITOR (OP-760 video board / VDP);
  leave the LCD alone. Goal: more graphical, less text-based.**
- **F119. VDP register map = 0xD000-0xD064** (mostly write-only; a classic VDP).
  Key regs from the init routine 0xAF3A-0xB006:
  - 0xD034/0xD036 = 16-bit VRAM ADDRESS pointer (init sets #0x7FFF => >=32KB VRAM).
  - 0xD018 = data/mode reg (init #0x19); 0xD00A #0x200; 0xD040 = bank/window
    selector, looped RW2A=0..0x1F (32 windows/entries); 0xAFEB = per-write helper.
  - Many hi/lo address-pair regs (D020/22, D024/26, ... D034/36) set up VRAM
    windows. 0xD010/D012 cleared at end.
- **F120. VERDICT: the VDP uses CPU-ADDRESSABLE VIDEO RAM.** The CPU programs
  16-bit VRAM addresses and streams data. This is the architecture where the
  CPU LOADS the character/font patterns INTO VRAM at startup from a disk-resident
  source. => **The monitor font/graphics are almost certainly PATCHABLE** (they
  come from the disk OS, not a fixed onboard char-ROM). This is the answer to the
  patchability question for the MONITOR: YES (pending locating the font-load).
- **F121. NEXT: find the font/char-pattern LOAD into VRAM.** Look for a routine
  that sets a VDP VRAM address (D034/36 or D040) then streams a large block from
  a disk-resident source pointer into the VDP data port (D018). That source
  pointer = the monitor font's disk location = what we patch to restyle. Then:
  render it (confirm glyphs), edit, patch, boot, view. Also note the VDP has
  color/window regs (D020-D032, 32 entries) => palette/color restyle is ALSO
  possible, and tile/window setup => layout changes possible.

## Session 12 (cont.) — VDP draw path uses a char->tile INDEX table (0xAC7A)
- **F122. VDP drawing sends TILE INDICES, not glyph bitmaps.** The draw routines
  compute a value from a char code (`LDBZE RW5C,0x4059[RW7C]; ADD RW5C,RW5C` =
  char*2) then `LD RW5E, 0xAC7A[RW5C]; ST RW5E, 0xD018` — i.e. look up a 16-bit
  VDP command/tile value in a table at **0xAC7A** and write it to the VDP command
  port 0xD018. 0xD040 = VRAM address/bank reg (set via helper 0xA371). 0xA342 =
  NOP-sled timing delay between VDP writes.
- **F123. No resident BULK font-stream loop found.** The glyph BITMAP patterns
  are not streamed into VRAM by any resident-64KB loop. => The font patterns are
  loaded either by overlay code (behind the banking wall) or by the video board's
  own firmware, and the resident code just references tiles by index. So editing
  the raw glyph bitmaps may require overlay access (the recurring wall).
- **F124. PROMISING LEVER: the 0xAC7A char->tile/command table.** If it maps
  character codes to VDP tile numbers, we can REMAP characters to different tiles
  WITHOUT touching bitmaps — and if VRAM holds unused/graphical tiles, that is a
  route to a more graphical look. Also the VDP color/window regs (D020-D032, 32
  entries) are programmable for a palette/color restyle. NEXT: dump + decode the
  0xAC7A table (size, entry format) and the char-source table at 0x4059/0x4014
  region; assess what tile set exists.
- **HONEST STATUS:** monitor restyle is FEASIBLE at the architecture level (CPU-
  addressable VRAM, programmable color, an editable char->tile table). Editing
  raw font BITMAPS may hit the overlay wall; color + char->tile remap + layout
  are the accessible levers to pursue first. Recommend a small test edit on the
  0xAC7A table or a color reg to prove monitor patchability end-to-end.

## Session 12 (cont.) — clean VDP color/attribute constants found (test targets)
- **F125. The char->tile tables (0xAC7A/0xA3EE/0x8396) are complex command/mixed
  data, not a flat color LUT** — not a clean single-byte color to flip.
- **F126. CLEAN color-test candidates = VDP constant writes `LD RWr,#imm; ST
  0xD018`.** The value **0x1B** is written to the VDP command/attribute port
  0xD018 at MANY draw sites (8E4F, D576, D5A5, D68D, DA64, DB5F, E976 ... imm
  bytes at file 0x00B5CF, 0x00FCF2, 0x00FD21, 0x00FE09, 0x0101E0, 0x0102DB,
  0x0110F2). A constant repeated across many draw contexts = likely a text
  color/attribute set before drawing. Other constants: 0x0A, 0x1C (also -> D018);
  0x17->D014, 0x19->D018, 0x200->D00A, 0x7FFF/0x8000->D034 (VRAM addr, DON'T
  touch), 0xFFF/0x3FFF->D008/D030 (masks/window).
- **F127. Color test plan (safe, TDD).** Change one or a few `0x1B` immediates to
  a clearly different value and boot to see if screen text/element color changes.
  Risk: LOW — worst case is a garbled/odd-colored monitor (reflash to recover);
  no disk-write, no buffer clobber, no hang path (unlike the SaveSys dump). This
  finally proves we can restyle the MONITOR from the disk. Each imm is 1 byte at
  a known file offset -> trivial, reversible patch. Start by changing the 0x1B
  sites; verify byte-exact; boot; observe which screen elements recolor.

## Session 12 (cont.) — COLOR TEST image built (awaiting monitor test)
- **F128. Color test image built: `temp/work/S760_COLOR_test.IMG`.** Changed all
  8 occurrences of the VDP constant `0x1B` (`A1 1B 00 5E` = LD RW5E,#0x1B before
  `ST 0xD018`) to `0x15`. Value-byte offsets patched: 0xB5D0, 0xB665, 0xFCF3,
  0xFD22, 0xFE0A, 0x101E1, 0x102DC, 0x110F3. Verified: exactly 8 bytes differ
  (1B->15), size 0x168000. Risk LOW: no disk-write/buffer/hang path; worst case
  = odd/garbled monitor colors, recover by reflashing original.
- **TEST (user):** boot `S760_COLOR_test.IMG` on the Gotek WITH the monitor
  connected. Watch for any on-screen color change (text/element color) vs normal.
  - color change visible => CONFIRMS we can restyle the MONITOR from disk (0x1B =
    a VDP color/attribute); huge unlock for the graphical restyle.
  - no change / same => 0x1B isn't the visible color; try other constants (0x0A,
    0x1C) or the color regs.
  - garbled => 0x1B is a non-color VDP command; revert, pick a different target.
  Keep the original handy to reflash.

## Session 12 (cont.) — COLOR TEST: FALSE ALARM (pink = mouse focus, not our edit)
- **F129. RETRACTED: the pink border was NOT our change.** User initially saw a
  pink keyboard border on `S760_COLOR_test.IMG`, but then realized **pink is the
  normal MOUSE-FOCUS highlight** (the element was focused/hovered). So that was a
  red herring, not the effect of our 0x1B->0x15 edit. => We have NOT yet confirmed
  a color change. Do not treat 0x1B as a known color. Lesson: need a controlled
  A/B (same screen, same focus state) vs the ORIGINAL to attribute any change.
- **F130. `0x1B` at VDP 0xD018: role STILL UNKNOWN.** It's a constant written to
  the VDP command port at 8 draw sites; whether it's a color/attribute/command is
  unconfirmed. Our 0x1B->0x15 edit's effect was NOT observed (masked by the mouse-
  focus pink). Need a clean re-test.
- **F132. Re-test method (rigorous):** 
  1. Boot ORIGINAL, note the exact screen + colors WITHOUT mouse focus on the
     element (move mouse away). Establish baseline.
  2. Boot the patched image, SAME screen, SAME (no) focus. Compare.
  3. To make any change unm, pick a value FAR from any existing UI color and
     change a SINGLE, identifiable site (not 8 at once) so the effect is localized
     and attributable. Also avoid values that might collide with the focus color.
  Better yet: first map WHICH element each of the 8 sites draws (trace routine +
  nearby strings) so we test one known element deliberately.
- **STATUS:** monitor color restyle NOT yet proven; the earlier "confirmed" was a
  misread. Re-do as a controlled experiment.

## Session 12 (cont.) — traced the 8 sites: 0x1B is a VDP CONTROL code, not color
- **F133. 0x1B is almost certainly a VDP COMMAND/CONTROL code, not a color.**
  Traced all 8 sites: each has the shape
  `LD RW5E,0xAC7A[RW5C]; ST 0xD018` (send tile/char cmd) -> `LCALL draw-helper
  (0xA371 or 0x9B71)` -> `LD RW5E,#0x1B; ST 0xD018` (send 0x1B). The SAME 0x1B is
  emitted after EVERY char/tile draw regardless of element, so it's a fixed VDP
  control op (e.g. command terminator / execute / fixed attribute), not a
  per-element color. => our 0x1B->0x15 edit was the WRONG lever; explains why no
  real color change was seen (the pink was mouse-focus, F129).
- **F134. Real per-element attributes look like the RW86-indexed values.** Before
  each draw the code moves per-element words: `LD 0x8396[RW86] / 0x8336[RW86] ->
  ST 0x84B6[RW86]` and sets 0x83F6/0x8456 flags, then calls the draw helper
  (0xA371/0x9B71). These RW86-indexed arrays (0x8336/0x8396/0x84B6/0x83F6...) are
  the per-element draw STATE (position/attr/color candidates). RW86 = element
  index. Color is more likely in this state or inside the 0xA371/0x9B71 helpers.
- **NEXT:** decode draw helpers 0xA371 (partially seen) and 0x9B71 to find the
  actual COLOR write to the VDP (which D0xx reg / which value). Then identify a
  real color source we can patch, and design a clean single-element A/B test
  (no mouse focus) to confirm.

## Session 12 (cont.) — VDP is command-stream driven; hunt the PALETTE
- **F135. Draw helper 0x9B71 also emits VDP control codes (0x0A) to 0xD018** in a
  24-iteration loop gated by table compares (0x8C66/0x804E/0x8066). Confirms the
  VDP is COMMAND-STREAM driven: values to 0xD018 (tile idx from 0xAC7A, 0x0A,
  0x1B) are opcodes, not a color register. Color must be either encoded in the
  0xAC7A command words or set via a "set-color" command / a palette.
- **F136. Strong palette lead: the VDP init loops 0x20 (32) times over regs
  0xD020-0xD032** (F119: RW2A=0..0x1F, ST RW2A,0xD040 selecting each entry). 32
  entries = likely a 32-COLOR PALETTE (or 32 attribute/window entries). In init
  these were written with ZR (zeros) but a palette is usually loaded from a table
  elsewhere. If there's a disk-resident 32-entry color table pushed to
  0xD020-0xD032, THAT is the clean color lever (change a palette entry -> recolor
  everything using that color index).
- **NEXT:** find where a 32-entry table is streamed to the D020-D032 palette regs
  (or where non-zero color/RGB values are written to them). That table on disk =
  the palette we patch. Then A/B test a single palette entry (mouse moved away,
  same screen) to confirm.

## Session 12 (cont.) — METHOD course-correction (user: understand, don't hack)
- **F137. User critique (valid in part): we've been hex-poking (esp. the 0x1B
  guess) instead of understanding first.** Correction adopted, but scoped:
  - "Decompile EVERYTHING first" is NOT viable: ~50-65% of code is in banked
    overlays we can't address without IC20 (undumpable so far); there is no C
    decompiler for MCS-96; hand-reading all ~500KB is months and mostly
    irrelevant to a UI restyle.
  - RIGHT correction: fully reverse-engineer the ONE subsystem we care about —
    the VDP/display — so every edit is DERIVED, not guessed. Treat the rest of
    the OS as a black box. Scope = the ~2-3KB draw/VDP-command cluster.
- **F138. Plan to properly understand the display subsystem:**
  1. Identify the actual VDP chip (get its command reference / datasheet). We
     never captured the exact part# (OCR said only "VDP"). Check service manual
     IC-DATA / render the video-board schematic page.
  2. Decode the VDP command LANGUAGE from the draw cluster (0x8Exx, 0xD5xx,
     0xA371, 0x9B71, the 0xAC7A tile/command table, the D0xx regs): opcodes
     (0x1B, 0x0A, tile words), where color/position/tile come from, palette
     setup (D020-D032, 32 entries), VRAM addressing (D034/36, D040).
  3. Build a written spec of the VDP protocol in docs/. THEN restyle edits are
     predictable + testable, not lottery.
- **F139. Palette-load scan (partial): D020-D032 are set only to ZR in init;
  D030 gets #0x8000, D034 gets #0x7FFF/#0x8000 (VRAM addr, not color).** No
  obvious disk-resident RGB palette table pushed to them yet — reinforces that
  color is likely encoded in the command stream / 0xAC7A words, to be decoded via
  the VDP spec (step 1-2). (Scan script had a minor bug; not needed further.)
- **RECOMMENDATION: do step 1 (identify VDP chip) next — a datasheet converts the
  command-language question from guesswork to lookup.**

## Session 13 — IC20 dump, attempt 2: SENTINEL probe first (safe, TDD)
- **F140. Re-approaching the IC20 dump, fixing the attempt-1 mistake.** The
  concept (inject stub -> copy IC20 into SaveSys-captured RAM -> SaveSys ->
  read on PC) is sound; what failed (F102) was the DESTINATION (0x5DBE scratch
  was a live buffer -> hung SaveSys). Fix: validate the destination with a tiny
  sentinel BEFORE any large copy or code injection.
- **F141. SENTINEL probe built: `temp/work/S760_SENTINEL.IMG` (NO code, pure data
  markers).** Placed unique 8-byte ASCII markers into the 4 zero-gaps:
  - `IC2DMPA0` @ file 0x0853E (rt 0x5DBE, the 8KB gap that hung when used)
  - `IC2DMPB0` @ file 0x0814E (rt 0x59CE)
  - `IC2DMPC0` @ file 0x0C0D4 (rt 0x9954)
  - `IC2DMPD0` @ file 0x0FA7A (rt 0xD2FA)
  Verified: exactly 32 bytes differ, size 0x168000. CANNOT hang (no code changed).
- **F142. TEST PROTOCOL (user):**
  1. Boot `S760_SENTINEL.IMG` from Gotek (boots normally — only data changed).
  2. Disk menu -> Save System -> SaveSys to a BLANK disk (blank_02.IMG etc.).
  3. Copy the saved .IMG back to `temp/work/` as `sentinel_out.IMG`.
  Agent then checks which markers survived at their offsets:
  - marker PRESENT at its offset => that location is SaveSys-captured AND stable
    (OS didn't overwrite it) => SAFE IC20 dump destination.
  - marker ABSENT (zeroed/changed) => location is used by OS/SaveSys => avoid.
  Whichever gap(s) survive, we use as the dump dest for attempt 3 (copy IC20
  there via an injected stub, sized to fit, then SaveSys). One round-trip screens
  all 4 candidates at once.

## Session 13 (cont.) — SENTINEL RESULT: all 4 gaps are SAFE, captured & stable
- **F143. ALL 4 sentinel markers SURVIVED the SaveSys round-trip.** In
  `sentinel_out.IMG`, IC2DMPA0/B0/C0/D0 all came back intact at their offsets
  (0x853E, 0x814E, 0xC0D4, 0xFA7A), each preceded by a `...F0` (RET) and followed
  by zeros = genuine inter-routine padding. => SaveSys captures these regions
  faithfully and the OS does NOT overwrite them. All 4 gaps are VALID dump
  destinations.
- **F144. REINTERPRET the attempt-1 hang (F102 was WRONG about the cause).** The
  0x5DBE marker (IC2DMPA0) survived fine -> the 0x5DBE gap is NOT a live buffer
  that gets overwritten. So the hang was NOT "destination is a live buffer." More
  likely causes: (a) our 8KB copy (0x1EE0 bytes to dest 0x5E20) ran to ~0x7D00,
  right at the gap's end (gap = 0x5DBE..0x7D00) — overrunning into the following
  routine's code; or (b) the copy read low memory 0x0000-0x1EE0 including SFRs/
  live regs and the ACT of executing a big copy at that boot point interfered.
  Net: the DESTINATION was fine; the SIZE/overrun or copy execution was the issue.
- **F145. Attempt-3 plan (safe): dump IC20 in SMALL pieces that fit WELL WITHIN a
  proven gap.** Use e.g. the 0x9954 gap (812B) or 0xD2FA (390B), or the 0x5DBE
  gap but only writing a few hundred bytes near its start (far from the end).
  Dump IC20 (0x0000-0x2080, ~8.3KB) in chunks of e.g. 0x200 (512B) per boot+save,
  each chunk copied to a proven-safe offset, incrementing the source each time.
  ~16 round-trips for full IC20 — tedious but safe and PROVEN. Alternatively do
  a single larger copy into the 8KB gap but STOP well short of its 0x7D00 end
  (e.g. copy 0x1C00 bytes to 0x5DC0, ending ~0x79C0, leaving margin) and verify.
- **NEXT:** build attempt-3 dump stub: copy a bounded chunk of low memory into a
  proven gap with margin; verify bytes via pypcode; one boot+save; extract +
  inspect the captured IC20 chunk. Iterate to cover 0x0000-0x2080.

## Session 13 (cont.) — attempt-3 chunk 1 built (safe, bounded copy)
- **F146. Reusable dump-chunk builder: `.kiro/scripts/build_dump_chunk.py`.**
  Args: <src_hex> <len_hex> <out.img>. Injects a boot stub that copies
  [src..src+len) of low memory into the proven-safe gap at DST rt 0x5E00 (well
  within 0x5DBE..0x7D00, big margin -> no overrun), then LJMP 0x2831. Verifies
  the hook site is the expected `E7 A3 06` before patching; caps len for margin;
  round-trips stub bytes via pypcode. After SaveSys the chunk lands at file
  (0x5E00-0x2080+0x4800)=0x8580.
- **F147. Chunk 1 built: `temp/work/S760_DUMP_c0.IMG`** = copy 0x0000..0x0800
  (2KB) -> 0x5E00. Verified: 22 bytes differ (hook 2B + stub 20B), size 0x168000.
  Stub: `LD RW40,#0; LD RW42,#0x5E00; LD RW44,#0x800; loop LDB[RW40]+ / STB
  [RW42]+ / DJNZW; LJMP 0x2831`.
  TEST: boot it (boots normally, copy is instant, no delay), SaveSys to a blank,
  copy saved .IMG to root/temp as `dump_c0.IMG`. Agent extracts file
  0x008580..0x008D80 = low memory 0x0000-0x0800 (IC20 vectors/reset region).
  If it looks like real MCS-96 code/vectors, proceed to remaining chunks
  (0x0800, 0x1000, 0x1800 -> covers 0x0000-0x2080).

## Session 13 (cont.) — chunk 1 ALSO froze -> real root cause found
- **F148. Chunk 1 (`S760_DUMP_c0.IMG`) FROZE despite staying inside the gap with
  margin.** This RULES OUT overrun (F144) and destination (F143 sentinel proved
  0x5E00 safe). The problem is the COPY ITSELF reading low memory 0x0000-0x0800.
- **F149. ROOT CAUSE (high confidence): the copy eats its own registers.** On
  MCS-96, 0x0000-0x00FF (up to ~0x01FF) is the REGISTER FILE / SFRs, not plain
  RAM. Our copy uses working regs RW40/RW42/RW44 (@0x40/42/44) and RB0 (@0xB0) —
  which LIVE INSIDE the source range being copied. As the source pointer sweeps
  0x40..0x44 and 0xB0 it reads our own live loop counter/pointers -> corrupts the
  loop control mid-copy -> runaway/hang. Also some SFRs have read side-effects
  (clearing flags, latching) which can wedge peripherals. You CANNOT linearly
  copy the register-file region using registers that live in it.
- **F150. FIX: start the dump ABOVE the register file, and use out-of-range regs.**
  IC20 ROM content we want (reset vector, service routines 0x018D-0x1109) is at
  >=0x0100. Dump from 0x0200 upward (skip 0x0000-0x01FF register file entirely;
  its live values aren't ROM anyway). Use working registers as high as possible
  and outside the copied span. NOTE: 0x0000-0x01FF is RAM/regfile (runtime state),
  NOT the IC20 ROM code — so skipping it loses nothing for understanding IC20's
  code; the reset VECTOR itself is at a fixed high addr (~0x2080 area) which is
  already on-disk-adjacent. Re-scope the dump target to 0x0200-0x2080.
- **RECOVERY:** power-cycle + reflash original (hardware safe; disk-image issue).
- **NEXT:** rebuild chunk with src=0x0200, and pick copy registers not in the
  copied range; verify; test one round-trip.

## Session 14 — resume after PC crash; resolve low-memory ROM vs RAM before dump
- **F151. Rebuilt chunk with src=0x0200 (`S760_DUMP_c0b.IMG`)** to avoid the
  register-file self-corruption (F149). Source now sweeps 0x0200-0x0A00, never
  touching our regs at 0x40/42/44/0xB0. Stub verified via pypcode.
- **F152. BUT a contradiction to resolve first (avoid dumping the wrong thing):**
  - F54: IC20 service routines are CALLed at 0x018D,0x0296,0x0442..0x1109 -> that
    implies CODE (ROM) at those low addresses.
  - F55: heavy DATA refs to 0x0100-0x03FF (pointer tables/vars) -> implies RAM.
  These overlap (0x018D is within 0x0100-0x03FF). Both can't be true at the same
  address. Must determine the real low-memory map: where is IC20 ROM vs work RAM?
  Possibilities: (a) the "call targets <0x2080" are NOT all IC20 ROM — some could
  be RAM trampolines/vectors the OS fills at boot; (b) the register file/RAM is
  small (0x00-0xFF) and 0x0100+ is ROM; (c) banking maps ROM/RAM differently.
- **ACTION: re-examine the sub-0x2080 call targets** — are they consistent code
  entries (ROM) or do they look like RAM vectors? This decides WHAT to dump and
  from where. Do this statically first (no hardware) since PC just recovered.

## Session 14 (cont.) — MAJOR CORRECTION: low routines are RAM-loaded, not IC20 ROM
- **F153. All 17 sub-0x2080 call targets fall in the reset-CLEARED work-RAM
  window (0x0120-0x1120).** The reset routine zeroes 0x120-0x1120 at boot (F23),
  yet the OS later CALLs 0x0442/0x018D/0x0491/... in that same range. You can't
  call zeroed RAM unless CODE IS COPIED INTO IT after the clear. => these are
  **RAM-resident routines loaded into low RAM during boot**, NOT a separate BOOT
  ROM (IC20). 
- **F154. RETRACT the IC20-boot-ROM interpretation (F36/F53/F54).** The "boot ROM
  holds the loader/banking + these services" model is likely WRONG. The low
  routines are code copied into 0x120-0x1120, and the copy SOURCE is almost
  certainly ON THE DISK (payload) or produced by a resident unpacker. Implication:
  we may not need to dump IC20 hardware at all to get these routines — they (or
  their source) are in the image we already have.
- **F155. This also explains the dump hangs differently:** copying low memory was
  reading ACTIVE work RAM (0x120-0x1120) that holds live loaded code + variables;
  combined with the register-file issue (F149), copying it at that boot point is
  fragile. But more importantly, it's the WRONG target — the interesting code is
  loaded FROM disk, so find it on disk instead.
- **NEXT (static, no hardware): find the loader that copies code into 0x120-0x1120.**
  Look for a resident routine that writes a block to the 0x120-0x1120 RAM region
  with a disk/payload source pointer. That source = the low routines' bytes,
  already in our image. Then we can disassemble them directly. This could unlock
  the 'services' (and maybe banking) WITHOUT any hardware dump.

## Session 14 (cont.) — no resident loader fills low RAM with code; map is ambiguous
- **F156. No resident copy loop writes CODE into 0x0120-0x1120.** Scanned all
  indirect-autoincrement stores: the only writes into that range are the reset
  ZEROING loop (0x20B2, writes ZR) and buffer clears (0x2382 fills 0x2256+ with
  spaces). Other block copies target 0x1B6C/0x40CD/0x42E7, not the low code
  region. => the low 'service routines' are NOT copied into low RAM by resident
  code.
- **F157. My region classifier was too coarse (correction to F153).** Of the 17
  low call targets: 0x018D,0x0296,0x0442,0x045D,0x0491,0x04AC,0x0551,0x05AA are
  BELOW 0x120 (i.e. between the boot ptr-table 0x100-0x11D and 0x120); but
  0x0B31,0x0D5D,0x0EC7,0x0F15,0x0F19,0x1109 ARE inside the reset-cleared
  0x120-0x1120 range. So SOME targets overlap the cleared RAM and some don't.
- **F158. HONEST CONCLUSION: the low-memory ROM/RAM map cannot be resolved by
  static inference alone.** We have conflicting signals (calls to addresses that
  are also zeroed/used as RAM) and no resident loader that populates them. On
  MCS-96 the low space mixes register file, SFRs, on-chip RAM, and external
  ROM/RAM per the chip-select/gate-array wiring — which is exactly what the
  service manual has NO memory map for (F-early). Resolving this definitively
  needs either the hardware (dump) or the schematic chip-select decoding.
- **REALITY CHECK / decision:** we've now spent significant effort circling the
  low-memory/IC20/banking question from many angles (dumps that hang, static
  inference that conflicts). Options:
  1. Accept the low map is unknown; RESUME the UI restyle using ONLY the resident
     64KB we CAN read, decoding the VDP command language from the draw cluster
     (the scoped-understanding plan F138) — no IC20 needed for that.
  2. Persist on the hardware dump with the register-file fix (src>=0x0200) —
     but the target's value is now doubtful (it's live RAM, not clean ROM).
  3. Get the video-board schematic / VDP part number (turns the restyle from RE
     into datasheet lookup) — the single highest-leverage external input.
- **RECOMMENDATION: option 1 + 3.** The UI restyle (user's actual goal) does NOT
  require IC20: the display code we need is in the resident 64KB (draw cluster
  0x8Exx/0xD5xx/0xA371/0x9B71 + VDP regs). Decode the VDP command language there;
  if the user can get the VDP part#, even better. Stop chasing IC20 for now.

## Session 14 (cont.) — reconcile: IC20 IS needed for MAME emulation (user point)
- **F159. User is right: MAME emulation NEEDS IC20.** Two separate goals:
  - UI restyle: does NOT need IC20 (display code is in the resident 64KB).
  - MAME emulation: DOES need IC20 (a driver can't boot without the boot ROM).
  Emulation is high-value (safe sandbox, instant patch testing, watch the loader/
  banking) — so pursuing IC20 for that is legitimate. Earlier I conflated the
  two goals; corrected.
- **F160. The register-file fix was NEVER TESTED (PC crashed first).** The last
  hang (F148) had a concrete diagnosed cause: the copy read the register file
  (0x00-0xFF) where its own working regs live -> self-corruption (F149). The
  FIX = copy from src>=0x0200 (above the register file). That rebuilt image,
  `temp/work/S760_DUMP_c0b.IMG` (src=0x0200, len=0x800 -> dst 0x5E00), EXISTS and
  is verified but untested on hardware. This is the outstanding next experiment.
- **CAVEAT (set expectations):** low 0x0200+ may be live work-RAM (not clean ROM),
  so this dump captures the RUNNING low-memory image (relocated code + vars),
  which is still useful (it's what executes) but may not be a pristine IC20 ROM.
  For MAME we ultimately want the true ROM bytes; the running image is a start.
- **PLAN:** test `S760_DUMP_c0b.IMG` (the register-file fix). If it BOOTS (no
  hang) and SaveSys succeeds, extract file 0x8580.. and disassemble — if it's
  coherent MCS-96 code, the fix worked and we chunk the rest to build the low-
  memory image for emulation. If it still hangs, the copy-at-boot approach is
  fundamentally too fragile and we pivot (schematic/chip-ID, or accept resident-
  only for the restyle).

## Session 14 (cont.) — dump_c0b: NO hang (fix worked) but captured ALL ZEROS
- **F161. Register-file fix WORKED (no hang): `dump_c0b.IMG` booted + SaveSys
  succeeded.** Copying from src=0x0200 (above the register file) does not hang.
  So F149 was the correct diagnosis of the earlier freeze.
- **F162. BUT the captured chunk (file 0x8580, rt 0x0200-0x0A00) is ALL ZEROS.**
  Nothing meaningful copied. Diagnosis: our hook runs at END OF RESET (0x218B),
  which is right AFTER the reset routine ZEROES 0x120-0x1120. At that instant low
  RAM is empty. The low 'service routines' are loaded into RAM LATER in boot, so
  we copied freshly-zeroed RAM. This CONFIRMS 0x0200+ is RAM populated after our
  hook point (ROM would be non-zero immediately) — consistent with F153 (low
  routines are RAM-loaded, not ROM).
- **F163. FIX: hook LATER — after low RAM is populated.** Move the injection point
  from end-of-reset to after the OS finishes loading the low routines (i.e. after
  the first LCALL to a low routine succeeds, or in the main loop). Options:
  - Hook one of the resident routines that runs AFTER boot completes (e.g. a
    frequently-called main-loop or UI routine) instead of the reset tail.
  - Or hook right before the first low-routine call site (0x2237 LCALL 0x0442):
    replace that call with a jump to our stub that (a) does the copy, (b) then
    performs the original LCALL 0x0442, (c) returns.
- **IMPLICATION for emulation:** the low routines being RAM-loaded (not a fixed
  ROM) means for MAME we'd need to capture the POPULATED low RAM (after load), or
  find where the OS loads them from (their source in the payload). Capturing
  populated low RAM via a later hook is the pragmatic path.
- **NEXT: build a LATER-hook dump.** Simplest robust choice: hook a routine known
  to run well into normal operation, copy low RAM (0x0200-0x1120) to the safe
  gap, SaveSys. Need to pick a safe, frequently-executed resident hook point.

## Session 14 (cont.) — later-hook dump built: `S760_DUMP_late.IMG`
- **F164. Later-hook dump built + verified.** Hook moved from reset-tail to the
  FIRST low-routine call site: 0x2237 `LCALL 0x0442` replaced with `LCALL 0x5DBE`.
  Stub (verified via pypcode) copies low RAM **0x0100..0x1120 (0x1020 B)** ->
  0x5E00, then does the ORIGINAL `LCALL 0x0442`, then `RET` (returns to 0x223A,
  boot continues unchanged). Rationale: by 0x2237 the low routines are loaded
  (0x442 is about to be called, so it's resident), so we snapshot POPULATED low
  RAM instead of the freshly-zeroed RAM (F162). Copy src 0x0100 is above the
  regfile (0x00-0xFF) so no self-corruption (F149). Diff: 25 bytes (hook 3B +
  stub 22B), size 0x168000.
- **F165. TEST (user):** boot `S760_DUMP_late.IMG`; SaveSys to a blank; save
  result as `temp/work/dump_late.IMG` (or root — say where). Agent extracts file
  **0x008580..0x0095A0** = low RAM 0x0100-0x1120, and disassembles at base 0x0100.
  - coherent MCS-96 code (esp. valid routines at 0x018D/0x0296/0x0442...) =>
    SUCCESS: captured the RAM-loaded low routines. Chunk more if needed; feed to
    MAME/analysis.
  - still zeros => low routines load even later; hook later still (main loop).
  - hang => revert; but copy proven safe (F161), so unlikely.

## Session 14 (cont.) — late-hook ALSO all zeros -> code/data address split (key!)
- **F166. `dump_late.IMG` chunk (rt 0x0100-0x1120) is ALSO ALL ZEROS**, including
  at 0x018D/0x0296/0x0442. But we hooked RIGHT BEFORE `LCALL 0x0442` executes and
  it boots fine -> 0x0442 IS callable code. Contradiction: the OS executes code
  at 0x0442 but a DATA read of 0x0442 returns zero.
- **F167. HYPOTHESIS (strong): code-fetch vs data-read address SPLIT via the gate
  array.** The 80C196KB + CPU gate array likely routes INSTRUCTION FETCHES at
  0x0100-0x1120 (and the sub-0x2080 low space) to IC20 ROM, while DATA accesses
  (our `LDB [ptr]+`) at those same addresses hit zeroed on-chip/S-RAM. i.e. a
  Harvard-like or chip-select split where ROM answers code fetch only. This
  cleanly explains: (a) reset can 'zero 0x120-0x1120' (the RAM side) yet (b) the
  OS calls routines there (the ROM side), and (c) our data-copy dumps read zeros.
- **F168. IMPLICATION: IC20 CANNOT be read by a data-copy stub, EVER** (our copy
  reads the data side = zeros). To capture IC20 we'd need to read it AS CODE — 
  e.g. a stub that treats the ROM region as its instruction stream, or hardware/
  gate-array-level access. This is why every data-based dump attempt failed. It
  is a genuine architectural block, not a bug in our stub.
- **F166b. Ruled out 'format-only': the save DID write a full system.**
  dump_late.IMG has 1,194,500 non-zero bytes, full sector-0 banner, correct
  payload at 0x4800. AND our patch is present in the saved image: hook @0x49B7 =
  `EF 84 3B` (LCALL 0x5DBE), stub @0x853E = our copy stub. So our stub WAS in the
  running system and executed; the copy ran but read zeros because low RAM
  0x0100-0x1120 genuinely was zero at that instant. This strengthens F167
  (code/data split): 0x0442 executes as code yet data-reads as zero.
- **F166c. Even the boot ptr-table reads zero in the dump.** Reset wrote
  0x400/0x0F/0x204/0x2FA/0x299 to 0x104-0x10E (DATA writes), but our data-copy of
  0x100-0x110 came back zero. Either those writes hit a different bank/context
  than our copy reads, OR (simpler) the ptr-table values were consumed/cleared by
  the time our hook at 0x2237 ran. Ambiguous; user will RE-RUN the save to rule
  out a bad/partial write before we finalize the code/data-split conclusion.
- **REVISED RECOMMENDATION:** IC20/low-ROM is likely UNREADABLE via our injection
  method (architectural code/data split). For MAME we'd need the physical ROM
  (flat-pack, hard) or gate-array-level tricks. => De-prioritize IC20; for the
  UI RESTYLE (which lives in the readable resident 64KB) proceed with decoding
  the VDP command language statically. Revisit IC20 only if we find a code-fetch-
  based read trick or get the chip physically.

## Session 14 (cont.) — REPRODUCED all-zeros -> IC20 unreadable by data copy (SETTLED)
- **F169. RE-RUN confirms: low RAM 0x0100-0x1120 reads ENTIRELY ZERO via data
  copy, on a confirmed-good save.** Reproduced. Even the ptr-table 0x104-0x10E
  (which reset FILLED with 0x400/0x0F/0x204/0x2FA/0x299) reads 0x0000, and the
  executed routines (0x018D/0x0296/0x0442) read 0x0000. Neither code nor prior
  data writes appear in our data read.
- **F170. SETTLED CONCLUSION: code/data address SPLIT.** The 80C196KB + gate
  array present a DIFFERENT physical memory to injected DATA reads (`LDB [ptr]+`)
  than to instruction fetch and the OS's own data writes at 0x0100-0x1120. Our
  copy stub reads a separate, zeroed data view. Therefore IC20 / the low code
  region is **architecturally UNREADABLE via our data-copy injection** — no hook
  timing or register choice fixes it. Every failed dump is explained by this.
  (Reads to the RESIDENT 0x2080+ payload DO work — that's normal mapped RAM;
  only the low split region is inaccessible to data reads.)
- **F171. To ever get IC20 would require:** reading it AS CODE (a stub that jumps
  through it / executes-and-observes), or gate-array/hardware-level access, or
  physically reading the flat-pack chip. All are out of scope / high-effort now.
- **DECISION (final for this thread): STOP pursuing the IC20 data dump.** It's a
  confirmed architectural dead-end for our method. 
  - For MAME emulation: blocked without IC20 (revisit only via physical chip read
    or a code-fetch trick).
  - For the USER'S GOAL (monitor UI restyle): does NOT need IC20 — the display
    code is in the readable resident 0x2080+ region. PROCEED there: decode the
    VDP command language statically (F138 plan), and/or get the VDP part# from
    the video board/schematic to turn it into datasheet lookup.
- **NET for the session:** we now fully understand WHY dumps failed (code/data
  split), can stop chasing it, and refocus on the restyle with the resident code
  we can read + proven safe patch/boot workflow.

## Session 15 — chip ID: RF5C16A is the RTC, NOT the VDP
- **F172. RF5C16A = Ricoh RTC + battery-backed static RAM, not video.** The RF5C
  family (RF5C15/RF5C16) is Ricoh's real-time-clock-with-RAM line (RF5C15
  datasheet: "set/read the clock with the same procedures as Read/Write for
  memory"). So RF5C16A is the S-760's RTC/backup-RAM chip (keeps date + settings)
  on the MAIN board — explains the date-like field change seen in SaveSys diff
  (F91, "17"->"01"). NOT the OP-760 VDP.
- **F173. Still need the VDP part#.** It lives in the **OP-760-1 video board**
  section of the service manual (separate "IC DATA (S-760/OP-760-1)" and
  "OP-760-1 MAIN BOARD ASSY" pages per the manual TOC), not the main-board IC
  list. Look there specifically for the video display processor / the largest
  custom IC on the video board. Common candidates for era: uPD7220/72120 (GDC),
  V9938/V9958, HD63484, or a Roland/OKI/Yamaha custom.
- **NOTE:** the VDP part# would turn the command-language decode into datasheet
  lookup. Absent it, we decode statically from the resident draw code (F138).

## Session 15 (cont.) — VDP CONFIRMED = Ricoh RF5C16A "CRT controller"
- **F174. The OP-760 video chip is the Ricoh RF5C16A, labeled "CRT controller"
  in the service manual.** (Correcting F172 — in the video-board section it's the
  CRTC, not an RTC.) No public datasheet exists (obscure early-90s Ricoh custom).
  So we decode its command protocol from the disassembly ourselves — same as the
  Hackaday precedent of RE'ing obscure Roland display controllers by behavior.
- **F175. What we already know about the RF5C16A interface (from the draw code):**
  - Register window **0xD000-0xD064** (mostly write-only). Access model =
    register-select-then-data (0xD040 selects a register/entry, then value
    written) plus a command/data port at **0xD018**.
  - **0xD034/0xD036** = 16-bit VRAM ADDRESS pointer (init sets 0x7FFF => >=32KB
    VRAM). VRAM is CPU-addressable => font/tiles are loaded into VRAM (patchable
    in principle, though the bulk load wasn't found in resident code -> may be
    overlay/boot).
  - **0xD040** = register/entry selector, looped 0..0x1F (32 entries = palette or
    window/attribute table).
  - **0xD018** = command/data port. Draw path: char -> index -> `LD 0xAC7A[idx];
    ST 0xD018` sends a tile/command word; `#0x1B`,`#0x0A` are fixed control codes
    emitted after draws (F133) — command opcodes, NOT colors.
  - **0xA342** = required inter-write timing delay (NOP sled). 0xD008/D00A/D030 =
    masks/mode; D020-D032 = the 32-entry table (palette/attr).
- **F176. Restyle plan (no datasheet needed):** decode the RF5C16A command set by
  correlating the draw routines with observed on-screen results (TDD): controlled
  single-element A/B tests (mouse moved AWAY to avoid the focus-pink confusion,
  F129). Build a docs/ spec of: the D0xx registers, the 0xD018 command opcodes,
  the 0xAC7A tile table format, and the 32-entry D020-D032 table (test if it's
  the palette). Each confirmed fact -> a reliable restyle lever.
- **NEXT:** decode the 32-entry D020-D032 table + its init/load (palette?), and
  the 0xAC7A tile-word format, then a controlled single-element color A/B test.

## Session 15 (cont.) — video output chain: RF5C16A -> CXA1145M (RGB->composite)
- **F177. Sony CXA1145M-T6 = RGB-to-composite/S-video ENCODER** (classic retro
  video encoder, well documented). It's a FIXED ANALOG converter: RGB+sync in ->
  composite/S-video out. NOT on the CPU bus, NO software-programmable palette/
  registers. => it is NOT a color lever for us; it just renders whatever RGB the
  CRTC feeds it.
- **F178. Video chain established: RF5C16A CRTC (digital RGB + palette) ->
  CXA1145M (RGB->composite/S-video) -> monitor.** Therefore ALL software color
  control lives in the RF5C16A PALETTE. The palette entries are RGB values (what
  the CRTC drives to the encoder). Confirms the 32-entry D020-D032 table is the
  prime color-restyle target, and that its entries encode RGB (some R/G/B bit
  packing) — once decoded we can choose exact colors deliberately.
- **NEXT unchanged:** decode the 32-entry D020-D032 palette (format + where it's
  loaded from), then a clean single-element color A/B test (mouse away).

## Session 15 (cont.) — D020-D032 is a WINDOW/GEOMETRY table, not a palette
- **F179. The 32-entry D040/D020-D032 mechanism is a WINDOW/PLANE/SPRITE table,
  not a color palette.** The init loop (RW2A=0..0x1F) selects each entry via
  D040 then writes ~10 register-pairs per entry: D020/22, D024/26, D028/2A,
  D02C/2E, D030/32 (coords/size), D034/36 (=0x7FFF, the entry's VRAM address),
  D000/02, D004/06, D00C/0E (mode/global). Non-init writes to these regs use
  values like #0x8000, #0x3FFF, computed addrs — i.e. VRAM ADDRESSES / COORDS /
  SIZES, NOT RGB. => the RF5C16A is a **32-window/plane display controller**; the
  UI is composed of 32 hardware windows positioned + pointed at VRAM.
- **F180. Color is NOT in the window table.** It's most likely PACKED INTO THE
  TILE-COMMAND WORDS sent to 0xD018 from the 0xAC7A table (each draw picks a
  0xAC7A entry that encodes tile pattern + color/attribute), and/or carried in
  the VRAM pixel data. This matches F122/F133 (draw = char -> 0xAC7A word ->
  0xD018) and why different elements differ.
- **F181. Architecture understood (RF5C16A working model):** windowed CRTC, 32
  planes, CPU-addressable VRAM (fonts/tiles in VRAM), register-select-then-data
  I/O (D040 selector + D000-D064 regs, D018 cmd/data port, D034/36 VRAM addr,
  A342 timing). Color lives in the tile/command words (0xAC7A) or VRAM, TBD.
- **STRATEGIC CHECKPOINT (be honest about effort):** decoding the exact 0xAC7A
  tile-word bit format (which bits = tile index vs color vs attr) is the next
  needed step for deliberate color/graphics changes, and it's non-trivial (no
  datasheet; must derive from behavior via controlled A/B tests). This is real
  RE work. Options: (a) push on decoding 0xAC7A via targeted single-entry A/B
  tests on hardware; (b) simpler near-term restyle wins that DON'T need the color
  format: relayout windows (move/resize UI elements via the geometry table),
  or edit VRAM tile/font bitmaps if we can find their load. Recommend a controlled
  A/B on ONE 0xAC7A entry next (mouse away) to crack the tile-word format.

## Session 15 (cont.) — 0xAC7A is a CRTC COMMAND-WORD table (hardcoded indices)
- **F182. 0xAC7A is a table of 16-bit CRTC command words, indexed by a HARDCODED
  small index (not char-derived) at many draw sites.** Decoded draw site 0x8E28:
  `LD RW5C,#1; ADD RW5C,RW5C (=2); LD RW5E,0xAC7A[2] (=word idx 1); ST 0xD018`.
  So this draw always emits 0xAC7A word #1 = **0x29C6** (file 0xD3FC), then the
  0x1B control code (F133). => 0xAC7A words are fixed CRTC commands (set-attr/
  color/mode) selected by index; different draw sites use different indices.
- **F183. 0xAC7A word values (idx: value):** 0:0x4210 1:0x29C6 2:0xE000 3:0xFA42
  4:0xC6A1 5:0x288F 6:0x10B1 7:0xC242 ... (values use all 16 bits; format = a
  command opcode + params, split unknown — no datasheet). The word 0x29C6 at
  file 0xD3FC is the concrete A/B-test target for the draw at 0x8E28.
- **F184. Controlled A/B test plan (crack the word format):** change ONE 0xAC7A
  word (idx 1 @ file 0xD3FC, 0x29C6) to a probe value, boot with MOUSE AWAY, note
  what changes on the element drawn by 0x8E28. Vary bits incrementally across a
  couple of tests to separate command bits (change breaks/garbles) from parameter
  bits (change alters color/attr cleanly). First probe: flip low byte only
  (0x29C6 -> 0x29xx) to test if low bits = color/param while high 0x29 = opcode.
- **CAVEAT:** need to know WHICH element 0x8E28 draws (which screen). Trace its
  caller to identify the element so the user knows where to look. Do that before
  the hardware test.

## Session 15 (cont.) — 0x8E28 draws a computed bar/meter element
- **F185. The 0x8E28 draw routine computes a length/position (MUL/DIV by 0x40 on
  a per-element value 0x8456[RW86]) and emits 0xAC7A[1]+0x1B as the element's
  cap/terminator.** Looks like a level meter / envelope / repeated bar element
  (per-element index RW86, char-map source 0x4059[RW7C]). Exact screen still not
  pinned, so the A/B test will observe the WHOLE monitor for any change rather
  than a pre-identified element.
- **F186. Decision: run a controlled single-entry A/B probe on 0xAC7A[1]** (file
  0xD3FC, 0x29C6). Change only that one word, boot with mouse PARKED (no focus),
  compare to a clean boot of the same screen. Isolated to whatever uses index 1.
  Purpose: reveal whether the word controls color/shape/attr and which bits do
  what — cracking the CRTC command-word format empirically (no datasheet).

## Session 15 (cont.) — 0xAC7A[1] probe image built
- **F187. Probe image `temp/work/S760_AC7A_test.IMG`:** changed ONE byte —
  0xAC7A word 1 low byte at file 0xD3FC, 0xC6->0x39 (word 0x29C6 -> 0x2939).
  Verified: exactly 1 byte differs, size 0x168000. Isolates the effect to draws
  using 0xAC7A index 1 (e.g. the bar/meter cap at 0x8E28).
- **TEST (user):** boot it, MOUSE PARKED (avoid focus-pink). Look across the
  monitor for ANY change vs a normal boot — a color, a character/shape, a
  bar/meter cap, etc. Report WHAT changed and WHERE.
  - clean color/shape change => word bits are attr/tile params -> we can iterate
    to map the format.
  - garbled/missing element => we hit command/opcode bits -> try a different bit
    field next.
  - no change => index 1 not visible on the shown screen -> try another index/
    a screen that uses it.
  This is a display-only change (no disk-write/buffer) -> low risk, recover by
  reflashing original if the screen looks wrong.

## Session 15 (cont.) — 0xAC7A[1] probe: NO visible change (ambiguous)
- **F188. Changing 0xAC7A[1] low byte (0x29C6->0x2939) produced NO visible change**
  on the screen the user viewed. Ambiguous: (a) index 1 not drawn on that screen,
  (b) low-byte bits aren't visible params, or (c) the element (bar/meter cap at
  0x8E28) wasn't on screen. Same recurring problem: testing entries without
  knowing which SCREEN renders them.
- **F189. Better tactic: target a draw tied to a KNOWN-VISIBLE element.** Pick the
  command word used by a draw of a string we KNOW is on the always-visible main
  screen (e.g. the version/CRT text at 0xBD3AA that renders). Change THAT draw's
  command word so the test is guaranteed observable. OR do a broad change (many
  0xAC7A entries) to confirm the table affects the visible screen at all, then
  narrow. Need to find a draw site whose element is definitely on the shown screen.
- **NEXT: find a draw/command tied to the main-screen text**, then a targeted A/B.

## Session 15 (cont.) — Perform-screen visible-change test
- **F190. Built `temp/work/S760_PERFORM_test.IMG`:** changed the Perform menu
  TITLE string "Perform Menu" -> "MODDED  Menu" (file 0x8B5CE, 7 bytes
  "Perform"->"MODDED "). Verified 7-byte diff, size 0x168000. Guaranteed-visible
  on the Perform Menu screen (proven string-edit lever).
- **TEST (user):** boot it, navigate to the Perform (menu) screen. Confirm the
  title reads "MODDED  Menu". This (a) re-confirms our patch->screen workflow on
  the monitor for a NAVIGABLE screen, and (b) pins the exact screen for the next
  COLOR probe: once we know the Perform title is ours, we find the command word
  that draws that title and probe its color/attr bits with confidence we're
  watching the right element. Low risk (string data only).
- **PLAN after confirm:** trace the routine that draws the Perform title text ->
  the CRTC command word / attribute it uses -> A/B that word to crack the color
  format, now on a screen we can reliably observe.

## Session 15 (cont.) — "Perform Menu" edit had NO effect; only ONE copy exists
- **F191. There is only ONE "Perform Menu" string in the image (0x8B5CE), we
  patched it, yet the MONITOR still shows "Perform Menu".** Rules out the
  wrong-copy theory. Big implication:
- **F192. HYPOTHESIS (strong): the MONITOR does NOT render text from these ASCII
  strings.** The RF5C16A monitor GUI likely composes text from PRE-RENDERED
  tiles/bitmaps in VRAM (glyphs as graphics), while the ASCII strings feed the
  LCD only. That would explain why editing the ASCII "Perform Menu" changed
  nothing on the monitor. Consistent with the tile/window architecture (F179-182)
  and with the draw path sending TILE indices (F122), not characters.
- **F193. CONFIRMED: LCD shows "MODDED  Menu", monitor shows "Perform Menu".**
  User switched display to LCD and saw our edit. => ASCII strings drive the LCD;
  the MONITOR renders text as pre-rendered glyph TILES/BITMAPS in VRAM, separate
  from the ASCII strings. This explains why EVERY monitor string edit did nothing
  (we were editing LCD text). Settled.
- **IMPLICATION for the restyle:** if the monitor text is tiles/bitmaps in VRAM,
  then restyling monitor TEXT = editing those tile bitmaps (need to find where
  the tile/font graphics are stored on disk + loaded to VRAM), NOT editing ASCII
  strings. This refocuses the hunt on the VRAM tile/font data source.

## Session 16 — monitor restyle = edit the VRAM FONT/TILE bitmaps (path clear)
- **F194. Settled model:** LCD = ASCII-string text; MONITOR = glyph tiles/bitmaps
  in RF5C16A VRAM. To restyle monitor TEXT/graphics we must edit the tile/font
  BITMAP data that is loaded into VRAM, then patch it on disk. Editing ASCII
  strings only ever affects the LCD.
- **F195. So the FONT hunt (earlier, F115-F117) IS the right track after all —
  but specifically the MONITOR's tile font, loaded into VRAM.** Need to find:
  (a) the tile/font bitmap data on disk, (b) the routine that loads it into VRAM
  (sets a VDP VRAM address via D034/D036 or D040, then streams bytes to the data
  port). The load routine's SOURCE pointer = the font/tile bitmaps we edit.
  NOTE: earlier we found NO resident bulk-stream loop into the VDP (F123) -> the
  font load is likely in OVERLAY/boot code, OR the tiles are streamed via the
  same D018 command port in a way we didn't recognize. Re-hunt with this framing.
- **PLAN:** 
  1. Find the monitor tile/font bitmap data on disk (render candidate regions as
     8x8/8x16 glyphs; look for the actual letterforms the monitor shows).
  2. Find how it reaches VRAM (load routine + source).
  3. Test-edit one glyph (e.g. make 'A' distinctive), patch, view on MONITOR.
  This is the true monitor-restyle lever (font/tiles), now correctly identified.

## Session 16 (cont.) — font hunt: 1bpp linear scan finds no letterforms
- **F196. Statistical font scans keep finding false positives (fill regions, or
  high-variety code/data), and rendering candidates shows NO letterforms.**
  Tried 8B/16B cells, MSB/LSB, at many candidate offsets (0xAA180, 0x8EF00,
  0x92840, tail 0x165xxx=0x0F fill). None render as A/B/C glyphs in 1bpp.
- **F197. LIKELY REASON: the monitor font is NOT 1-bit-per-pixel linear.** The
  RF5C16A drives a COLOR RGB display, so glyph tiles are probably MULTI-BIT-PER-
  PIXEL (2bpp/4bpp for palette color) and/or non-linear layout (column-major,
  bit-planes, interleaved). A 1bpp renderer shows multi-bpp glyphs as noise.
  Also the font may be loaded from OVERLAY/banked code (F123: no resident stream
  loop found) and/or the source data compressed.
- **F198. Re-strategy for finding the monitor font:**
  1. Try multi-bpp renderers (2bpp/4bpp, 8px wide => 16B/32B per glyph row-set)
     at the candidate offsets — letterforms may appear at the right depth.
  2. Find the VRAM font-load transfer: a routine early in boot that writes a
     LARGE count of bytes to a VDP data port (D018 or D040-selected) from a
     source pointer = the font's disk location + its exact format.
  3. If both stall, do an EMPIRICAL bulk test: overwrite a big candidate region
     with a recognizable pattern (e.g. all 0xFF), boot, and see if MONITOR text/
     graphics visibly corrupt -> confirms that region feeds the monitor, then
     narrow. (Display-only, low risk.)
- **NEXT: try multi-bpp rendering of the top candidates + hunt the VRAM font-load
  transfer with a 'many writes to VDP port from a source' detector.**
