# 05 — Manuals

Located in `manuals/`. All three are **scanned image PDFs** (no embedded text
layer), so reading them programmatically requires OCR.

| File | Pages | Size | What it's for |
|------|-------|------|---------------|
| `ROLAND_S-760_SERVICE_NOTES.pdf` | 24 | 7.7 MB | **Highest value.** Block diagram, parts list, board layouts — should name the CPU/ROM/RAM part numbers and the memory map. |
| `S-760_OM.pdf` | (owner's manual) | 10.1 MB | Feature/behavior reference; useful for correlating UI strings and functions with code. |
| `S-760_MI.pdf` | 14 | 2.0 MB | MIDI implementation chart; correlates with the MIDI-handling code and the MIDI label strings found at ~0x88400. |

## Reading strategy
1. Render pages to images with PyMuPDF (`fitz`) — available.
2. OCR the images. No OCR engine is installed yet (`tesseract` not found,
   `pytesseract`/`easyocr` not installed). Options:
   - Install Tesseract + `pytesseract` (best for text/parts lists).
   - Or `easyocr` (pure-Python, heavier, good on noisy scans).
3. For the **service notes specifically**, prioritize the pages with the block
   diagram and the parts/IC list — that's where the CPU part number is.

## Priority questions the manuals should answer
- **CPU part number** (settles the disassembly question).
- ROM/RAM sizes and the **memory map / load address** for the OS.
- Any mention of the disk format or a boot/checksum scheme.

## OCR results / manual reads (DONE for the service notes)
Full OCR of all 24 service-note pages is in **`docs/service-notes-ocr.txt`**
(rough text; diagrams/pin-tables are noisy but readable). Key extractions:

- **CPU = Intel `S80C196KB`** (MCS-96, ~16 MHz) — confirmed on the block diagram
  (p.3): "CPU GATE ARRAY ... S80C196KB for CPU". Settles the disassembly target.
- **Block diagram (p.3)** names the memory/peripheral blocks: BOOT ROM (IC20),
  ROM (IC27-29), S-RAM, D-RAM (IC24/25), EEPROM (IC2), WAVE MEMORY SIMMs, FDC,
  SPC/SCSI, LCD, TVF/MEQ, A/D, D/A. OP-760-1 = VDP + D-RAM video board.
- **IC DATA (pp.11-13)** give peripheral part numbers: FDC NEC uPD72068GF,
  SCSI Fujitsu MB89352A, LCD Epson SED1335F0B, wave DSP Fujitsu
  MB87422PF/MB87423APF, DAC AKM AK4328VS, DRAM Toshiba TC514260.
  (All copied into the hardware steering + docs/03/04.)

### Still to extract (needs eyeball on the schematic, OCR can't linearize it)
- Exact CPU **address windows** (BOOT/ROM/RAM/SFR) from the MAIN BOARD schematic
  (pp.16-20) — this yields the OS **load/base address** for disassembly.
- Any disk boot/checksum scheme.
- Rendering + OCR are reproducible via the scripts in `.kiro/scripts/`
  (see the header of `service-notes-ocr.txt`).
