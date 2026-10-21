# Roland S-760 front-panel controls

## Verified physical controls

Source: visually inspected Owner's Manual (`Manuals/S-760_OM.pdf`), Basic
0-6/0-7 (PDF pages 222–223), About SHIFT (Basic 7-9, PDF page 287),
and Value knob (Basic 7-10, PDF page 288). The owner's rack photograph
provided on 2026-10-11 independently confirms the labels and arrangement.
OCR is not required to read a scanned page.

| Physical button | Dedicated Shift action | Native input chord |
| --- | --- | --- |
| Mode | None documented | MODE |
| Command | None documented | COMMAND |
| Exit | None documented | EXIT |
| F1 | F4 | SHIFT + F1 |
| F2 | F5 | SHIFT + F2 |
| F3 | F6 | SHIFT + F3 |
| S1/Dec | None documented | S1 |
| Up | None documented | UP |
| S2/Inc | None documented | S2 |
| Left | Home | SHIFT + LEFT |
| Down | Mark | SHIFT + DOWN |
| Right | Jump | SHIFT + RIGHT |
| Shift | Modifier | SHIFT |

The physical navigation cluster is two rows, in this exact order:

| Left column | Middle column | Right column |
| --- | --- | --- |
| S1/DEC | Up | S2/INC |
| Left | Down | Right |

There are two S buttons and four arrows, not six S buttons. There are 13
matrix buttons including Shift, plus the Value/Menu knob's push switch.
The six documented Shift functions are F4, F5, F6, Home, Mark and Jump.
S1/S2 functions are context dependent; they are not substitutes for encoder
rotation. Basic 7-10 limits Value operation to Dec/Inc or -100/+100 contexts.

## Software controls

The physical labels and Shift chords above are the hardware reference. Application routing, controller modes and UI qualification belong in the [emulator documentation](../emulator/README.md); historical disabled-knob and bug-status notes are not a hardware specification.
