# Fixed screen callbacks and temporary status rows

[Validation](../../condensed/validation/os-fixed-screen-callbacks-2026-10-16.json) checks new instructions against the immutable OS image and records initial descriptors for indices011E/011F. These are static, conditional initial-image paths. No native UI interaction or runtime mutation trace was performed.

## Fixed screen selection chain

Page0000:F09C/F0A2 supplies RW4A=011E/011F; F0A8 enqueues event1 through resident000F:2080. F49E/F4A3 reads its two payload bytes intoR48/R49. CF82 (CRT) orD7CF (LCD) calls005A:42E8 with that16-bit screen index. Index entries underdata0219 atfile08B078/08B07C select0219:92AE/9380. Both initial descriptors have mode1 geometry and five seven-byte type2 field records terminatedFF.

| Index | Descriptor | Field pointer/list | First two callback slots |
| --- | --- | --- | --- |
| 011E | 0219:92AE | 9318 ->931C | 0196:9960;0171:8172 |
| 011F | 0219:9380 | 9434 ->9438 | 0196:9AC7;0171:818F |

The remaining eight initial callbacks are0171:8000 (RET). Only two index entries, two16-byte descriptors, two40-byte callback arrays, two2-byte field pointers and two36-byte field lists are newly classified (196 bytes). Geometry and tuple extents are not newly classified in this pass. Runtime rewriting and other selection indices remain open.

0196:9960 fills/highlights a row and emits glyphC2.0196:9AC7 emitsC2 at y=1+2152. Their0171 update callbacks test22E8, return if zero, otherwise clear it, copy2152 intoRB7 and invoke0196:99D9/9AE5 throughCDED. Those routines map2143 values0..10 to counts1,2,3,4,5,2,3,4,2,3,2. When2142=5 andRB7 already equals2152 they enqueue only one event2; otherwise they update2152, enqueue one event2 plus the selected count, then call9AA4/9BB0. The latter select data010A=02DB and read a16-bit next screen index from48AA+2*R48 or48B6+2*R48, restore010A, and enqueue event1. These mutable tables are not bounded by this closure; no full target-set claim follows.

## Field hit testing and numeric callback metadata

ResidentE1E1 starts RWA6=0 and reduces incoming pointer coordinates by shifting right3. E225 selects descriptor data page215C and dereferences2170. Each seven-byte record compares row with y+2149 and x with the half-open range [x+2148, x+2148+width), subject to byte overflow. A hit loads record bytes3/4/5 intoRA8/RAF/RB7, writes byte6+1 to21AB, and returns carry set. A miss advances tuple offsetRWA6 by2,4,6,2 for record types1,2,3,4 after masking the type with0F, then advances the record pointer7. The redraw scanner87A5 compares unmasked type bytes; these two consumers should not be silently conflated.

F13A andF651 dereference2172 and addRWA6 to select tuple bytes. The numeric path at01EC:8000 loads a function pointer from metadata+2 and sign-extends words+4/+6 to32 bits, before calling object-selection helper004B:6B2E. The two signed words are candidate limits; their actual lower/upper enforcement cannot be confirmed until indirect handlers are identified. It branches the function pointer through805A, savingR48/R4A with explicit return8063.876C reads the metadata's first word for the display callback. Both paths retain unresolved indirect targets and data-window qualifications.

## Temporary status rows

Event0E calls005A:747E; event10 calls746E. They store countdown4000/2000 in3642 respectively (time units unresolved), then share7489. Control mode2476 selects CRT row2 or LCD row7. The service saves40 CRT character/attribute pairs or25 LCD pairs atdata02CC:571A, unless a marker glyph0D already indicates an overlay. NonzeroR48 clears the row, writes marker0D and displays an entry from576A+20*R48. R48=0 restores only when the marker is present. This is a mutable backup buffer, not a newly classified immutable resource.

Transfer supervisor0166:8A24..8A47 maps result bytes2/3/4/5 to message indices5B/15/5C/5D, passed through8A7A to747E. The four referenced20-byte entries consist of attribute90,18 text bytes andNUL:

| Result byte | Message |
| --- | --- |
| 2 | Illegal Sample # |
| 3 | Memory Full |
| 4 | Dump Adrs Error ! |
| 5 | Dump Data Error ! |

These names qualify the corresponding error-result meanings on that path. Other callers/status values and the whole message-table bound remain unresolved. This adds80 classified data bytes. Display timing, countdown decrement cadence, row-backup concurrency and firmware error-path acceptance require ordinary native execution.

## Remaining work

Trace writers of data02DB:48AA/48B6 and2152/22E8 before bounding submenu invocations. Recover concrete numeric metadata pointers before declaring types or clamping semantics. Preserve explicit selector context for callbacks and shared display helpers. Reproduce with the standard OS analyzer and coverage commands inos-decoding-progress.md; generated sources remain private.


Follow-up: [concrete numeric metadata](os-device-probe-and-numeric-fields.md) now follows initial011E index2 through02DB:48AA toscreen012F, resolves six display/edit target pairs and statically confirms signed clamp words via01EC:81BD. Initial table data is now known for the five valid field indices; exhaustive runtime writers and postprocess preservation remain open.
