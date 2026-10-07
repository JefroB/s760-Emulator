---
inclusion: always
---

# Reverse Engineering Workflow & Safety

Rules and methodology for working on the S-760 OS. Follow these on every task.

## Golden rules
1. **Never modify `S760224.IMG` in place.** It is the ground-truth artifact.
   Copy it to `temp/work/` (or a named experiment folder) before touching.
2. **Byte-exact discipline.** The image is a fixed 0x168000 bytes. Any repacked
   image must keep the exact size, sector alignment, and any loader checksums.
3. **Evidence over assumption.** Record what was actually observed in the bytes.
   Mark guesses as hypotheses. Don't assert the CPU/format until confirmed.
4. **Persist findings.** When you learn something structural, update the
   `disk-image-format.md` / `s760-hardware.md` steering files so it survives
   across sessions. Steering is the project's long-term memory.
5. **Prefer non-destructive, reproducible tooling.** Scripts over one-off manual
   edits, so any result can be regenerated and reviewed.

## Environment note (Windows / cmd)
- Shell is `cmd`; invoke PowerShell scripts explicitly:
  `powershell -ExecutionPolicy Bypass -File .\.kiro\scripts\script.ps1`
- Do not rely on `$env:`-style inline `$` expansion in one-liners passed through
  cmd — write a `.ps1`/`.py` file instead (inline `$vars` get stripped and fail).
- **Script locations:**
  - **Reusable** tools go in `.kiro/scripts/` (the analyzer, disassembler, PDF
    helpers — anything worth keeping/rerunning).
  - **Throwaway/experiment** scripts go in `temp/` (workspace root); delete them
    when the finding is captured in steering/docs or promoted into a reusable
    script. **Do NOT use `.piggie/`.**
  - Image working copies + extraction output go in `temp/work/`.

## Recommended toolchain
- **Reusable scripts** live in `.kiro/scripts/`:
  - `s760.ps1` — the analyzer: info, dump, map, strings, entropy, find, opcodes
    (mcs96/68k/x86), histogram, extract, copywork, patch, repack.
  - `pdf_extract.py` / `render_pages.py` — manual (PDF) text extraction + page
    rendering for OCR.
  The **`s760-image-analysis` skill** (`.kiro/skills/`) documents these tools
  (see its SKILL.md) and carries the discovery keywords. Prefer these tools;
  extend them rather than re-inventing.
- **Disassembly (SOLVED tooling):** CPU = Intel MCS-96 (80C196KB), load base
  = 0x2080 @ file 0x4800. Use the authoritative Ghidra SLEIGH MCS-96 decoder via
  pypcode: `.kiro/scripts/mcs96_disasm.py` (single region) and
  `.kiro/scripts/mcs96_trace.py` (recursive-descent control-flow tracer + I/O
  logger). `pip install pypcode` once. Do NOT hand-code opcode tables.
- **Emulation (blocked on BOOT ROM):** MAME has an MCS-96 (i8x9x) core but no
  S-760/S-770 driver, and any driver needs the BOOT ROM (IC20) dump to run.
  IC20 is a flat/SMD package (can't socket-pull) and holds the disk loader +
  overlay/bank logic that is NOT on the disk. Until IC20 is dumped, prefer the
  static tracer + boot-ROM ABI inference.

## Hardware & capture channel (user's rig)
- The user OWNS the S-760 and has a **Gotek floppy emulator installed** (no SCSI
  drive yet). => We have a working read/write path: build a patched image on a
  COPY, serve it via Gotek, boot, observe. This is also the intended route to an
  in-system IC20 dump (a stub writes IC20 bytes to a floppy file we read on PC).
- The user has a chip reader/burner, but **IC20 is flat-pack** so no clean pull.
- **Never** test unverified patches on real hardware without a rollback image;
  always keep the known-good original to reflash the Gotek.

## Current milestones (staged, lowest-risk first) — see docs/04 "Plan of record"
- **M1 (NEXT) — Prove the Gotek round-trip.** Patch the on-screen version string
  ("Ver. 2.24" at file 0x87FDB) on a COPY, size-exact repack, boot via Gotek.
  Reveals: is the image Gotek-bootable, and does a disk checksum block patches?
- **M2 — Checksum handling** (only if M1 fails to boot): find the loader
  checksum, add recompute to s760.ps1 Cmd-Repack.
- **M3 — Boot-ROM ABI by inference:** document each IC20 service call's contract
  (inputs via RAM slot 0x104 / RW1C selectors, outputs, side effects).
- **M4 — In-system IC20 dump:** stub writes IC20's address range to a floppy
  file via Gotek; read on PC. Unblocks emulation + settles banking.
- **M5 — Emulation** with IC20 in hand (MAME driver or extend our tracer).

## Original phased plan (reference)
### Phase 1 — Format decoding
- Decode sector 0 + allocation region; locate directory/catalog; allocation unit.
### Phase 2 — Code identification  [DONE: MCS-96, base 0x2080, uncompressed]
### Phase 3 — Disassembly & mapping  [IN PROGRESS: 123 routines traced]
- Label entry points, ISRs, main loop, I/O; build subsystem symbol map.
### Phase 4 — Modification & repack
- Smallest possible patch; recompute checksums; size-exact repack (to a COPY);
  verify via Gotek (and/or emulator once IC20 is available).

## When making claims
- State what was checked (which offsets, which tool) and what remains unverified.
- If an approach fails twice, stop and diagnose the root cause before iterating.

## Legal / scope
- This is preservation and interoperability work on hardware the user owns.
- Keep outputs focused on understanding and extending the S-760 OS. Do not
  redistribute Roland's copyrighted code; document behavior and structure.
