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

## Embedded rack presentation

F1–F6 sit beneath the LCD. F4–F6, Home, Mark and Jump send their native
Shift chords, releasing the target before Shift. Mode/Command/Exit remain
separate. The six navigation controls retain the physical arrangement above;
Home/Mark/Jump sit beneath Left/Down/Right.

Input Level and Output Level are separate knobs left of the LCD, per the
owner's description of the concentric hardware control. Value has a separate
Menu button. The three knobs remain disabled pending verified routing. Menu is wired to the
SC0/SP4 push switch documented on Service Notes p18 and opens the firmware menu.
Absolute mouse positioning after Menu/Exit remains BUG-030.

The Gotek has its own encoder and Up/Down/Select buttons. They browse the host-owned default floppy inventory and successfully inserted
paths; Select opens the image dialog, prefilled with the selected path, for confirmation or choosing another image. Its display
separates selection from the last backend-confirmed inserted filename. This is
an emulator media UI, not FlashFloppy firmware emulation or automatic USB scanning. The host starts with `roms/FDD`; Select offers recursive folder configuration.
Independent selection and inserted-source metadata survive editor recreation and
version-2 native plugin-state recall. See [media limits and qualification](../emulator/guides/native-media-library.md).

This mapping supersedes the earlier 23-entry unverified demonstration inventory.
`NativePanelControls.tsx` implements the verified native mapping. The old
`shiftButtonMap.ts` remains a legacy demo/spec fixture and is not hardware evidence.
