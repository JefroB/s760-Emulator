# CRT display and native VDP interface

The optional display subsystem produces the CRT interface shown in the [physical screen photographs](screens/index.md). Photographs establish visible content; they do not establish video timing, exact RGB voltages, palette hex values or all ASIC registers.

The current [native driver](../../mame-source/src/mame/roland/s760.cpp) models a banked VDP window at physical 102800 (logical E800 with data selector 0400). This supersedes the old proposed flat D000 register map.

Observed firmware transactions implemented by the driver include command 08 for cell writes, 0A for reads and 0C for read/modify/write. E800/E802 transfer data, E804/E806 hold the live word pointer, and E808 carries command/status handling. The boot ROM polls an advancing pointer; successful execution of that handshake is not a measurement of complete silicon timing.

In the observed configurations, the OS uses a 40-by-25 text matrix based at word 1000 and the boot ROM uses 0800, configured through E812. Graphics bases are 1400 and 0C00 respectively through E816; E814 participates in font configuration. Uploaded glyphs are read from VRAM, rather than established by a universal hardcoded font ROM. The current model treats graphics bytes as RGB channels; the fourth byte's complete mask semantics remain unresolved. Attribute bits 4–6 supply RGB in the observed path, and bit 0 supports the observed hover inversion; a general text-enable interpretation of bit 7 is unproven.

The modeled cursor uses E80C/E810 for X and E80E for Y; X=512 parks it in the observed firmware path. Cursor shape and other mode semantics remain provisional.

The native CRT frame is currently 640 by 240 pixels; a host may normalize it to 640 by 480 for presentation. These software frame sizes do not establish the physical CRT scan timing or pixel aspect ratio. The previous 27-register table, calibrated palette claims and fixed plane-layout specification were unsupported and have been removed.

See [display research](../condensed/README.md), [screen evidence limits](screens/00-ui-architecture-and-palette.md) and [open questions](evidence-and-open-questions.md). This page documents a bounded firmware/native contract, not a complete RFSC16A programming manual.
