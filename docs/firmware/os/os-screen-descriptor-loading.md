# Screen descriptor loading and control flags

The earlier screen extractor provides heuristic label candidates. This report instead follows the actual consumer005A:42E8 from startupC337. [Validation](../../condensed/validation/os-screen-descriptor-loader-2026-10-16.json) preserves351 byte-checked instructions and the single startup-qualified index0130. It does not establish a complete screen count or replace physical screen evidence.

The loader uses a four-byte entry at data0219:`8000 + 4*index`: a16-bit data page and16-bit pointer. It selects that page through010C, caches it at215C, caches the descriptor pointer at215E, and reads eight16-bit descriptor fields. Referenced values are cached in2160..219B.

| Descriptor offset | Observed consumer |
| --- | --- |
| 00 | Pointer cached at2160; interpretation pending |
| 02 | Geometry/flags pointer cached at2162; reads16 bytes |
| 04 | Pointer cached at2164 |
| 06 | Pointer cached at2166; reads bytes at+7,+15,+23,+31,+39,+47 |
| 08 | Pointer cached at216E |
| 0A | Pointer cached at2170 |
| 0C | Pointer cached at2172; startup modifies its first word |
| 0E | Pointer to ten four-byte pairs copied into2174..219B |

This16-byte pointer descriptor is distinct from the title/label sequence recognized by the older magic-byte scanner. A universal17-byte layout header or full field-binding schema is not justified by either tool.

Geometry byte0 is cached whole, with its low7 bits and highbit also stored separately. Bytes1/2 are x/y; FF means center using `(40-width)/2` and `(25-height)/2`, respectively. Bytes3/4 supply width/height. Bytes5..9 are cached individually; bytes10..15 copy into2152..2157. Additional meanings require their consumers.

Geometry byte9 controls several output bits through003B:4127/416D and004B:53D6/5402. A later list of exact screen IDs overrides one control. The IDs seen in these comparisons do not establish an exhaustive table bound.

## Startup-qualified resource

StartupC32A supplies index0130. Its table entry at file08B0C0 selects data027C:93A8, file0A4BA8. The descriptor points to geometry93BA and a40-byte pair table at93D2. All ten initial pairs are8000/0171; their target/page ordering and all ten callback-slot consumers are now traced in [resident UI event dispatch](os-ui-event-dispatch.md); mutable runtime targets remain unresolved.

Startup reads the pointer at descriptor+0C and changes its first word to93FA or9404 according to configuration0299:8F94. This is direct evidence that loaded UI resource data can be mutable. Initial-image pointer values are not proof of invariant runtime targets.

Only the four-byte index entry,16-byte descriptor,16-byte geometry,40-byte pair table and two-byte writable target are classified here. Unreferenced gaps and the full index-table extent remain unknown.

## Peripheral control helpers

[Additional anchors](../../condensed/validation/os-panel-fdc-startup-2026-10-16.json) establish the helper operations.003B:4127 ORs ordinary masks intoF010;416D clears them. With bit7 set, low bits0/1 instead clear or setF000 bits7/6. FF handles all those outputs together. Physical label/polarity names are not inferred solely from these writes.

004B:53D6 sets a bit in210A and5402 clears it, only in control mode2476=2. Input indices above15 select all16 bits.548A transmits the210A/210C word state through54E2, sending high bytes masked7F and low bytes in order.54E2 shifts each byte MSB-first ontoF008 bit6 while toggling bit5, with explicit delay loops. Mode2476=1 instead uses the existing mouse polling path57A9; mode0 returns from5322. These findings preserve the distinct control-mode paths and do not claim timing parity.
