# Device probing, startup templates and concrete numeric fields

[Byte evidence](../../condensed/validation/os-device-probe-and-numeric-2026-10-16.json) records new instruction anchors, counted device signatures and six concrete numeric metadata records. All OS results here are static and mapping-conditional. The separate native result concerns boot-ROM display upload only.

## Eight-target startup device scan

Explicit startup0000:C677 reaches0129:8000. It initializes3622=FF, displays the counted/NUL banner SCSI Device check throughdata02CC:6D8E, and visits eight targets3624=0..7.811F initializes each3627[target]=FF and3630[target]=0, invokes0068:561E three times, then calls0129:8355 for identification. When relevant classification results85/83/82/86 occur, it calls0068:58DF and5A1C. The full scan later selects the first target with a recognized/usable status, or leaves3624=FF. Local status labels are not a complete physical-device compatibility claim.

8355 returnsFD for the self target3623. Otherwise it calls0068:56A8 and combines `(response[0]&7F)|(response[1]&80)` at2E0E/2E0F, advancing the signature pointer to2E16. Counted comparisons againstdata02CC identify JVC/OMTI, Sony/Toshiba/Matsushita/Chinon/Pioneer CD-ROM families, Sony SMO-C, SyQuest and upper/lower-case Iomega prefixes. Every compare is bounded by its literal byte count; zero bytes within a signature are compared, not treated as terminators. Original strings classify firmware branches only, not tested support for those products.

003B:7592 temporarily selectsdata010A=02CC and copies a count-prefixed command into5F12. Two explicit0068 pointers resolve to seven-byte initial records:5F4E=`06 03 00 00 00 0A 00`;5F55=`06 12 00 00 00 23 00`. Corresponding transfer counts are0A and23 bytes. These provide the byte-level request/sense and identification-query contracts without assuming that every bus/error branch has executed.

003B:7482 retries its helper whileRBB is7 or5, using a32-bit decrementing counter initialized0. The initial decrement wraps toFFFFFFFF; this is not a zero-attempt loop. Callee waits and timing remain unqualified.0129:84E0 gates checks in bit order0,1,2,3,4,5,7,14,15 fromRW48; each exits early on carry. The startup display caller passes0017, enabling only bits0/1/2/4. Other branches are decoded generic helper code, not all dynamically accepted by that invocation. The additional counted media comparisons use16 andC4(196) bytes; signed decoder presentation ofC4 does not make a negative length.

## Object startup templates

004B:730A selectsdata010C=0299 and expands the32-bit value361E/3620 shifted8 into five32-bit fields at8100..8113: base, base, base+0400, base+0E00, base+1200. It copies3618 into8114. The32-bit carry/order is preserved; units remain unresolved.

7362 copies the type4 indexFF object through6A26 into two128-byte records underdata0356:7060 and70E0 and clears each+4B byte.73D3 copies type2 index0 into7160 (256 bytes), type11 index0 into7260 (128 bytes), then clears words7240/724A.7423 copies type3 index0 into72E0 (256 bytes). These are runtime template copies, not additional immutable resource extents or guessed object types.

0196:88B4 updates22A8 from mode2145 and pointer position. For mode1 it converts pointer coordinates by shifting3, compares half-open geometry bounds2148/2149 plus214A/214B, and selects low state0 inside or2 outside (screen000C uses3 inside). State changes can set bit7. Outside-state2 with events2E/2F enqueues event2 and clearsRDF. Other modes clear the low state while retaining change information. This is a conditional input-state contract, without physical mouse acceptance.

## A concrete menu-to-numeric-metadata chain

The initial data02DB:48AA table contains five screen indices0120,012B,012F,0137,0139. The five initial011E fields supply indices0..4;0196:9AA4 reads the selected word and enqueues event1. Only those ten table bytes are classified. Other writers/invocation indices remain unresolved; the followingFFFF is not read by this path and is not newly classified.

Index2 selects initialscreen012F, descriptor027C:900E. Its first six records are type3; their six-byte tuples point at metadata indata02DB. Only the first six records/tuples are classified, not the entire field-list extent.

| Metadata | Parameter address | Display / edit targets (fetch01EC) | Signed lower / upper words |
| --- | --- | --- | --- |
| 5CE4 | 8F96 | B23E /806F | -1 /15 |
| 5CEC | 8F95 | B273 /8069 | 0 /1 |
| 5CF4 | 8FBB | B297 /8069 | 0 /1 |
| 5D40 | 8F9A | B2BB /806F | 0 /31 |
| 5BBC | 8F9B | B059 /8069 | 0 /1 |
| 5D48 | 23A6 | B2D9 /8069 | 0 /4 |

01EC:8000 loads edit+2 and sign-extends words+4/+6. Normal metadata invocation clearsRAE bit6 at803A.8069/806F read a signed byte unless event3C supplies an existing value. Their adjustment helpers increment on2F and decrement on2E;806F also decrements on3C.81BD compares the signed32-bit result with the upper bound first, then lower, copies a bound on overflow and marksRAE bit7 when clamped. It setsRAE bit0. This resolves the former provisional limit interpretation for these concrete records.

The edit handlers call01D1:A0A2/9FDF before storingRC8. Those postprocessing roots are decoded, but their nested callee preservation is not fully closed.81BD's clamp is statically established; full final-value/event propagation and native editing remain unvalidated. RAE-bit6 alternate helper entries and all other metadata invocations remain explicitly unqualified. Unknown indirect edges remain alongside the initial-target annotations.

## Remaining work

Follow all writers and selection transitions before treating the five-entry initial table as a complete runtime bound. Finish01D1 postprocess dependencies, qualify additional concrete type3 fields, and attach native value-change evidence. Device-scan labels, bus-error mapping and all eight physical targets need separate runtime/hardware acceptance.
