# S-760 Reverse Engineering — Findings

Plain-English, digestible notes on what we've learned about the Roland S-760
system disk (`S760224.IMG`, System Ver. 2.24). These docs are the human-friendly
companion to the machine-facing steering files in `.kiro/steering/`.

## Index
- `01-overview.md` — what the artifact is, project goal, current status.
- `02-disk-layout.md` — the on-disk map (region by region), in a table.
- `03-cpu-investigation.md` — the hunt for the CPU/instruction set.
- `04-findings-log.md` — chronological log of discoveries with the evidence.
- `05-manuals.md` — what's in the manuals folder and how we're reading them.

## The one-paragraph summary
`S760224.IMG` is a 1.44 MB floppy image in a **custom Roland format** (not
MS-DOS). It contains the S-760 operating system: a large block of executable
code for an as-yet-unidentified CPU, plus UI text/resources, a fixed-size
record table, and an embedded MS-DOS boot-sector *template* (x86) used when the
sampler formats DOS disks for sample exchange. The main CPU is confirmed **not**
Motorola 68000 (either byte order) and **not** x86; the code looks like a
variable-length instruction set. We're now reading the scanned service manual
(via OCR) to get the CPU part number directly.
