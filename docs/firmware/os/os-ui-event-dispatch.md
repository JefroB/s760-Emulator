# Resident UI event queue and descriptor dispatch

[Validation](../../condensed/validation/os-ui-event-ring-2026-10-16.json) records 3,969 newly explored instruction anchors, checked against original image bytes and the OS mapping formula. Aliases are deduplicated in the separate coverage inventory. All claims here are static and conditional on declared fetch/data contexts; native event acceptance remains open.

## Queue producer and consumer

Startup C473 sets R48=FF and calls resident 000F:2080 at C476. That case clears words 21AC/21AE. Other tags enter2097: load write cursor21AE, append R48 at21B0+cursor, append selected payload bytes, then publish the resulting cursor at2127. Each append increments and masks the cursor with7F. Tag1 appends R4A and R4B and sets1F6D=FF; tags3,0A,0E,0F,10 append R4A. Other producer tags append only their tag. No capacity/fullness test occurs in2080..2138; this alone does not establish overflow in reachable firmware operation.

Main-loop page0000:C807 calls F468. It loads21AC into local RW38, compares with21AE and, when equal, clears both stored cursors and returns carry clear. F645 fetches21B0+RW38 and wraps modulo128. The consumer does not publish local progress to21AC after each event. Normal dispatch returns toF46D; tag11 explicitly clears both cursors and returns carry clear. Tag0C callsF694 and returns carry set, which main-loop C80A branches on. Producer/consumer concurrency and special-exit cursor ownership require runtime evidence.

| Event tag | Consumer operation |
| --- | --- |
| 01 | Read two payload bytes intoR48/R49; chooseCF5A orD7AD by control mode2476. |
| 02 | ClearRDF/RE0; chooseD383 orDACC by2476. |
| 03 | Read one payload byte intoR48; chooseD477 orDC77 by2476. |
| 07 | Follow descriptor+0C throughF651; read a word/word/byte tuple and call01EC:876C. |
| 08 | Call01EC:87A5 withRF2=0 and preserveRB7 explicitly. |
| 09 | CallDE00, which invokes cached pair2180/2182. |
| 0A | ReadR48; call004B:5B6F. |
| 0B | ChooseD297 orDA9A by2476. |
| 0C | CallF694, return carry set. |
| 0D | Continue without a payload. |
| 0E / 10 | ReadR48; call005A:747E /746E. |
| 0F | Read one byte, call003B:489C, then004B:675C. |
| 11 | Clear queue cursors and return carry clear. |

The tested tags and fallthrough do not establish an exhaustive runtime event enum. Unknown tags currently fall through to the next ring byte; payload validity needs producer qualification.

## Banked wrapper and cached callback pairs

CDC6 saves fetch0106 plusRW38/3A/3C/3E/46. CDD4 selects the page inRW1C. Under page0 invocations, CDD9 pushesCDDE and CDDC branches throughRW1E. CDDE restores those registers and CDE8 restores fetch0106 before RET. The analyzer deliberately stops the original entry atCDD4; post-transition behavior was checked separately against original bytes. Caller pairs with adjacent RW1C=0/RW1E=target loads justify the added roots, without claiming generic indirect-target resolution.

DD77 loads target2178 and page217A, selects data010C=0299 and fetch0104=page, pushesDDA0 and branches through the target. DE00 similarly uses2180/2182 and returnDE35. These are respectively descriptor pair indices1 and3, confirming target-first/page-second ordering. F0C1 uses2184+4*(RE0-17) after testing a shifted2150 mask; the arithmetic is byte-width before multiplication. Exact caller bounds remain open. It reads a target/page pair, selects0299 and0104, then branches with returnF121. Return continuations were seeded from explicit PUSH addresses and remain conditional on normal callee return.

The startup descriptor's initial8000/0171 pairs therefore refer to a fetch0104 target under page0171, rather than a data pointer. Their mutability prevents declaring8000 the only runtime target. Target window membership, caller bounds and other pair consumers remain to qualify.

F651 also confirms cached2172 as a pointer to a mutable pointer. Under cached data page215C, it dereferences2172, addsRWA6, and reads two words plus a byte. RWA6 bounds and tuple field names remain unresolved. This connects event7 to the startup descriptor+0C mutation without inventing an exhaustive resource schema.

## Reproduction

Run the OS analyzer with scripts/firmware_manifests/os_exploration.json, then firmware_coverage.py as in os-decoding-progress.md. Validation carries input/tool/manifest hashes and every new instruction anchor. Original image and emulator behavior are unchanged.


## Closure of the ten callback slots

Following contiguous page0 CDC6 argument pairs reaches a fixed point of68 qualified wrapper call sites. An initial decode stopped atCFFE because the old C000..D000 analysis window cut an instruction; widening only the same declared page0 fetch window to10000 resolves that boundary without introducing gap roots.

| Cached words | Slot | Invoker |
| --- | --- | --- |
| 2174/2176 | 0 | DD1C; targetDD54, returnDD56 |
| 2178/217A | 1 | DD77; targetDD9E, returnDDA0 |
| 217C/217E | 2 | DDB2; targetDDE5, returnDDE7 |
| 2180/2182 | 3 | DE00; targetDE33, returnDE35 |
| 2184..219A | 4..9 | F0C1; targetF11F, returnF121 |

EA42..EA60 admits preciselyRE0=17..1C toF0C1, giving indices0..5 and six four-byte records. This bounds that call path only; other invocation states remain unresolved. The callback page is installed in fetch0104, data010C is0299, and return continuations restore savedRW50..56 and data010C. Fetch0104 is not locally restored by those continuations. Correct downstream callers must establish their own mappings.

The initial startup target0171:8000 decodes as one RET instruction. Only that one byte is added; the following bytes are not swept or inferred as part of a function. Dynamic callback targets still require mutable-descriptor writer analysis.


## Seven-byte field records and value tuples

Explicit event calls qualify01EC:876C/87A5 ([78 anchors](../../condensed/validation/os-ui-field-callbacks-2026-10-16.json)).87A5 selects cached descriptor data page215C and dereferences both2170 and2172. It scans seven-byte records from the first pointer until byte0=FF. Byte0/1 are coordinates offset by2148/2149; byte2 supplies a width to the display path; byte3 controls tuple advancement (types1/4 add2 bytes, type2 adds4, type3 consumes6). Record byte4 bit6 enables a display call004B:5217. Type3 reads a word/word/byte tuple, takes record byte5 intoRB7 and calls876C throughCDED. Other record types do not use this callback path; their names remain unresolved.

876C selects data010A=02DB and010C=0299, reads a function pointer throughRW4C intoRW30, calls004B:6B2E, then branchesRW30 with explicit return879E. Return restoresRW4A and data010C; it does not restore data010A. The decoded6B2E/6A26 closure preservesRW30: no calls, fetch-selector writes or stores toR30/R31 occur; MULU RL2C uses2C..2F. It can replace data010A with an object-specific bank andRW4E with an object address. Indirect target bounds and interrupt effects remain open. Initial startup2170 points via027C:93CC to93D0, whose first byteFF ends the field list immediately. Only that two-byte pointer and one sentinel byte are newly classified. Startup descriptor mutation affects the separate2172 pointer.


## Field border consumer

Explicit field call01EC:8808 reaches004B:5217 ([byte evidence](../../condensed/validation/os-ui-field-border-2026-10-16.json)). Control mode2476=0 returns. Other modes forceRF5=1 and draw through5224: base address1000+40*(RF1-1)+(RF0-1), with both subtractions performed as bytes. It emits top glyphs88/89/8A, side glyphs8B/8C, and bottom glyphs8D/8E/8F. RF4 counts horizontal middle glyphs andRF5 counts side rows; DJNZ byte0 would mean256 iterations. The field caller supplies its record width and one interior row. This supports a field-border interpretation without naming VDP glyph shapes from numeric codes alone. No descriptor data is read by this helper, and it makes no calls or selector writes.
