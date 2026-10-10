# VDP & Display Implementation

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
