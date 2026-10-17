# Startup audio control and command tables

Explicit startup calls select page0166 before enteringA3C2/A411/9C1E/A4D1/A42C/A52A/A3DD. Their local closure and same-page CDED callees provide [380 instruction anchors and1,340 referenced resource bytes](../../condensed/validation/os-startup-audio-2026-10-16.json). The original input is unchanged; no native run validates this new analysis.

## Audio command initialization

Entry9C1E saves the currentR9D mode, calls001F:4F7F with mode0, saves the existingPORT1 bit4 selection throughA403, then selects its temporary state throughA3DD. With data page02A6 it clearsDC08/DC0A, submits a zero command tagged0, and clears128 command slots tagged0400..047F.

It then reads200 pairs of16-bit words from8008..8327 intoDC00/DC02, tagging each with its index0..199 throughDC06. A second loop reads200 coefficients from8328..84B7, writesDC00, clearsDC02 and tags0200..02C7. The startup entry also copies two words at8000/8002 intoDC08/DC0A. These are bounded peripheral command/configuration resources; their full device-level instruction meaning has not been recovered.

The routine restores the savedPORT1 selection, reapplies configuration through9E71/9D84/A216, and restoresR9D through4F7F. This ties the existing audio/pan command aperture to explicit initialization tables. It does not establish new filter equations or chip-select coverage beyond existing hardware evidence.

## Routing configuration

9D84 chooses a locally bounded selector:2 when1BA4 equals1; otherwise1 when0299:8FB8 is zero; otherwise0.9DE1 uses that selector to choose one of three36-byte records at02A6:84EA. Each contains nine pairs of words submitted toDC00/DC02 using nine tags at84E0. This establishes the complete108-byte table extent without guessing from nearby bytes.

9E23 reads one of three masks at855C, tests bits2..7, and writes either0 or1400 to six coefficient tags from8556, each ORed with0200. These masks and tags are separately bounded resources.

9E71 selects a coefficient at84C0 using the configuration byte0299:8FB9 and applies it to eight tags at84B8. A216 selects a coefficient from02BE:B23C using its incomingR4A and applies it to two tags at02A6:856C. The eight/two tag arrays are bounded; the coefficient-table extents remain unresolved because these closures do not establish the configuration-index bounds.

## Port operations

| Entry | Observed operation |
| --- | --- |
| A3C2 | Input0 setsPORT1 bit3; input1 clears it |
| A3DD | Input0 setsPORT1 bit4 andF000 bit2; input1 clears them |
| A403 | Returns the inverse ofPORT1 bit4 inR4A |
| A411 | Input0 clearsPORT1 bit5; input1 sets it |
| A4D1 | Inputs0/1/2 selectPORT1 bits7:6 as00/10/11, then pulsePORT2 bit6 low/high |
| A42C | DrivesPORT2 bit0 low/high/low throughA46E with nested delay loops |
| A52A | ReadsF00A high bits after a write; conditionally changesF002 bit5 |

The [existing clock finding](../../condensed/06-audio-dsp-and-hardware-parity.md) maps00/10/11 to44.1/48/32kHz. Other signal names are left unresolved here. Delay-loop iteration counts are visible, but elapsed timing is not claimed. Unhandled input values generally preserve the relevant port bits; they can still execute the following latch/delay operations.

Remaining dependencies are configuration producers/bounds, additional audio command tables, native mode-change traces and peripheral instruction semantics. These do not block independent startup/UI/storage decoding.
