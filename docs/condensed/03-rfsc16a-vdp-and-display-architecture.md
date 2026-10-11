# VDP & Display Implementation

User hardware observation (2026-10-10): hovered options have a white background with inverted text; hovering the Perform Play keyboard turns its surrounding border pink. Finding62 implements and checks both effects against guest VRAM and runtime screenshots. Exact analogue colours remain unmeasured.

Latest display update: finding63, correcting finding62's text colours. Text RGB uses attribute bits4/5/6: the active Perform tab is red, B0/B1 labels yellow, E0 labels cyan. Native original-ROM boot now composes the guest graphics planes and uploaded text font. Perform hover reverses red/white text, keyboard hover turns its border pink, and Command/Exit remains functional. The colour/attribute model matches these observed transitions; exact output intensity, mask/alternate-font behavior, cursor pixels and other display modes remain provisional or unresolved.


Latest: finding58. The experimental IC15 ROM boot now loads all112 OS tracks
and reaches interactive Perform Play. Correct OP-760 identification and live VDP
pointer readback remove the video blockers. New native EEPROM profiles default
to Mouse+CRT at the user's request; existing profiles retain their setting.
Native LCD writes and its screen surface are restored. Rendering, mouse input,
complete chip behavior and power-on bank defaults still need work.


**Native banked VDP (findings53/54/55) — the leading path; the flat D000/D010
model below is superseded for native mode.** The VDP is at physical102800
(CPU E800 at data page0400): address bytes E804/E806, data cells E800/E802,
command/status E808 (firmware writes08/0A at E808 and polls E808 bit1). A
provisional synchronous VRAM-transaction adapter follows the actual bank004B
firmware sequences (4B77..4BDB, 4D1F..4D34, 4DD7..4E28): command08 write-cell
advances after low-port commit, 0A read-cell advances after low-port read, 0C
read-modify-write advances on write. Missing advancement had previously
overwritten cells. Firmware addressing, verified in finding55:
- **Text:** VRAM word `1000 + y*40 + x` (40×25 character matrix).
- **Graphics:** word `1400 + 2*(y*40 + x/8)`, three colour bitplanes (R/G/B byte order, finding62) + a fourth
  byte whose mask semantics remain unverified, two words per 8 pixels.

**Live VDP pointer readback (finding58, corrected).** ROM3736..3744 polls E806/
E804 for the ADVANCING word address and waits for it to reach `0800`. The native
offsets 04/06 must therefore return the live 16-bit word pointer, not the
originally-written address bytes; with that fix the firmware's upload terminates
naturally. (This was one of the two video blockers in the ROM path; the other was
the OP-760 identification in doc 01.) It does not establish complete RFSC16A
timing/command semantics.

Native E800 register usage decoded from the guest transaction stream over a 60 s
run (offsets from E800; `chatGPT-work/native-panel-fresh-60s.log`):

| Reg | Role | Writes/60 s |
| --- | --- | ---: |
| 00/02 | Data cell low/high byte | 54,738 each |
| 04/06 | VRAM word-address low/high byte | 28,065 each |
| 08 | Command (08 write-cell, 0A read-cell; poll bit1) | 26,075 |
| 0C/0E/10 | Cursor X low / Y / X high (corrected, finding60) | 18,665 each |

The `reg=00 value=XX` bytes at sequential `wordaddr=10XX` decode directly to the
ASCII the firmware writes (the "Perform Play 1" title and a "32Mbyte" wave-RAM
report), confirming genuine guest text composition, not a drawn raster.

**Cursor position registers (finding60/61, corrects the old "graphics-plane"
reading of 0C/0E/10).** The firmware (OS file 18D7B..18D89) stores the cursor
coordinate directly: **E80C = X low, E810 = X high, E80E = Y**. These are the same
registers the mouse integration updates (file 18CCA..18D0D). The OS hides the
cursor by writing X = 512 (0x200, i.e. E810=02 E80C=00), beyond the normal 0..319
range — an off-screen park, NOT a separate enable bit. The user's crosshair
observation is implemented with provisional size and RGB inversion (finding62).
Exact cursor pixels, colour controls and pattern source remain unresolved.

**Character-matrix base follows E812 as a word-address page (finding60).** ROM
sets E812 = 08 (word 0800); the disk OS sets 10 (word 1000); both matrices are
40 columns × 25 rows. The renderer must follow E812 rather than hard-coding 1000,
or it cannot display the ROM's own matrix.

**Firmware font (finding60).** The native text renderer reads each glyph row from
guest VRAM at byte `2*(character_code*8 + row)`, low byte = 8 pixels — i.e. it
draws the font the firmware actually uploaded (digits, upper/lowercase, borders,
arrows, UI symbols), not a host ASCII font. The high-byte font plane is still
unresolved/unrendered.

**Composition model at a glance (findings 60/62/63).** Page registers (high
address byte each): **E812** text matrix (OS 1000 / ROM 0800, 40×25), **E814**
font (observed 00), **E816** graphics (OS 1400 / ROM 0C00, two words per 8 px).
Graphics planes: bytes **0/1/2 = R/G/B**; 4th byte all 0xFF on Perform (unapplied).
Text attribute byte:

| Attribute bits | Meaning |
| --- | --- |
| 4/5/6 = R/G/B | text colour (90/91 red, B0/B1 yellow, E0 cyan, F0/F1 white) |
| bit 0 | XOR glyph coverage = reverse video (Perform 91 white-on-red → 90 red-on-white) |
| bit 7 | text enable (all observed set; disable unverified) |

Compositing: graphics shows where glyph coverage = 0; attribute colour where = 1.
Full-scale RGB pens 10..17 are separate from legacy pens 0..9; exact analogue
intensities unmeasured.

**Option-hover highlight (findings61/62).** Hovering Perform changes exactly 11
VRAM bytes, reversibly: 7 attribute high bytes (`0x91 → 0x90`, bit0) for the label
cells plus 4 low bytes rewriting the context text (e.g. ` ---` → `Open`). This
pins **bit0 of the attribute byte** as the highlight bit for that transition (not
proven to be a universal inverse-video rule). Per the user's first-hand hardware
observation, a highlighted option is **white background + inverted text**, and
hovering the Perform-Play keyboard turns its **border pink**. Finding62 now
renders both transitions: attribute bit0 XORs glyph coverage, and the keyboard
border comes from graphics bytes0/2 (red/blue). Graphics byte1 supplies green.
Text colour uses attribute RGB bits4/5/6 (finding63 hardware-observation correction). Exact analogue
intensity, other attribute bits and non-FF fourth-plane behavior remain unverified.

**Historical result (finding55): the native disk OS reaches the Perform Play
screen.** A 30/60-second native run writes the actual Perform Play matrix to
guest VRAM (title "Perform Play 1", Volume, the Perform/Patch/Partial/Sample/
Disk/System tabs, eight Off patch slots, Command menu, bottom soft keys), and
MAME renders it through a **diagnostic monochrome ASCII raster** (snapshot
`55-native-perform-play-diagnostic.png`). This is the first native OS screen.
That historical raster used an approximate ASCII font and omitted uploaded
glyphs, colour attributes, and graphics composition. Findings60/62 replace those
limitations for the observed mode; full hardware fidelity remains unproved. The old `D010`/
`display_enabled_ever` enable metrics describe the superseded flat register model
and must NOT be used as native-mode enable tests.

Verified against `s760.cpp` and shared findings 13, 21, 23, 25 on 2026-10-09.
This is the **emulated interface**, not a complete RFSC16A silicon specification.
The former 27-register table mixed inferred and unimplemented functions.

## Implemented VDP writes

D000–D0FF uses a byte handler. Word stores split into low/high byte accesses.

| Offset from D000 | Action |
| --- | --- |
| 10 | Enable when `(data & 0x19)!=0`; bit1 interlace, bit3 tile, bit4 bitmap; latch enabled-ever |
| 18/19 | Stream byte at VRAM pointer; increment modulo 20000; mark VRAM-active |
| 20/21 | Mouse X low/high |
| 22/23 | Mouse Y low/high |
| 24/25/26 | Active pointer bits 0–7 / 8–15 / 16 |
| 30/31 | Tile-base low/high |
| 34/35/36 | Also active pointer bits 0–7 / 8–15 / 16 |
| 40 | Status = data & 7F |

Both pointer groups load **one `m_vdp_addr`**. The D024/D025 trace establishes
preservation of a full address such as 0299, not two independent pointer states.
128 KB VRAM requires **17 bits**, not 18. D018 reads also advance the pointer.
Other written values are saved in `m_vdp_regs`; this is not a complete blitter
or timing implementation. No D800–D87F palette write-handler is installed.

## Rendering

MAME native CRT: **640×240, 60 Hz**. Bridge canonical CRT: **640×480**; the host
normalizes it. Photo estimates of 640×400/480 are not MAME's native geometry.

Reset defaults: matrix=0000, attributes=0A00, tiles=1400, bitmap=3400. D030/31
can update the tile base. These are model defaults, not proved universal hardware
layout. The firmware's observed D034=8299 stream pointer does not establish
attributes at 0A00. Mapping firmware streams to the renderer remains an evidence
request. `crt_update()` gates the VRAM path on content/activity and display enable.

The driver fixes ten software RGB pens:

| Pen | RGB |
| --- | --- |
| 0 | 0,0,0 |
| 1 | 255,255,255 |
| 2 | 0,0,192 |
| 3 | 0,200,80 |
| 4 | 255,230,0 |
| 5 | 220,60,20 |
| 6 | 190,195,205 |
| 7 | 0,0,96 |
| 8 | 0,220,220 |
| 9 | 24,26,30 |

These are implementation constants, not calibrated hardware DAC measurements.
Attribute high/low nibbles select foreground/background in the renderer.

## LCD and latest boot result

E000=command/status, E002=data, within E000–E003. Status reads return 90;
data reads advance a cursor masked to 4 KB. See document 07 for commands.

Finding 25 reports a stable six-second run with VDP activity, SED activity 83,
pointer 074BA, **enabled-ever=0 and D010=0**. Earlier blue-screen observations
were different runs. Task 26 seeks the natural firmware enable condition;
forcing D010 or fabricating an event is not an established fix.

Task 26 static decode (shared finding 27): the candidate sync writers at
92D0, 9326, 9F95, A012 and A900 extract **the high byte of RAM word 2A8C**
into D010. Under the current driver, enable therefore requires
`(RAM[2A8D] & 19h) != 0` at a sync. The blank routine at 2923 has guards;
it does not blank unconditionally every empty tick. Event 0C takes SETC after
5714; event 0E follows a separate handler and returns to queue processing.
The natural boot producer and initialized shadow/mask values remain unproved.

Finding 28 reports live queue indices 21AC=0102 / 21AE=EF1C (invalid for
the decoded 7-bit queue), and 2085=C3 rather than supplied F00A=80. These
locations overlap original image instructions. Establish actual initialization
and loading before treating 2085 as a persistent strap cache or queue reads
as posted events. C3 is also the original image byte at 2085; a later overwrite
has not been demonstrated by that value alone.
