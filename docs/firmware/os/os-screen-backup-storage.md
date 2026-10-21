# Screen backup storage and extension ownership

The original OS owns physical CPU RAM `0F0000..0FFFFF` for screen backup and related clearing. It cannot be treated as a permanent extension area because it contains fill bytes in the system disk. This closes the upper-tail question raised by the [BlueSCSI feasibility investigation](../../project/bluescsi-feasibility.md).

The [validation record](../../condensed/validation/bluescsi-stereo-ui-followup-2026-10-18.json) contains 970 byte-checked exported instruction annotations, 299 additional instruction decodes, immutable image/build identities and ordinary native observations. These include stereo-selection dependencies as well as the storage routines below. Addresses are bank-qualified; physical RAM is `(selector << 10) + (logical_address & 3FFF)`, and loaded OS file offsets add `4800`.

## CRT backup

`004B:62D4` rejects nesting depth `2144 >= 3`. It reads the four geometry bytes at `2148..214B` and rejects a width-times-height product greater than `026C` (620). For accepted depth 0, 1 or 2, the backup offset is respectively `0000`, `5554` or `AAA8`.

It writes a four-byte geometry header using `004B:647D`, then invokes `005A:4000` and `005A:413C`. For valid nonzero dimensions, their storage is:

| Component | Bytes | Evidence |
| --- | ---: | --- |
| Geometry | 4 | Four calls to the byte writer `647D` |
| CRT text | 2,000 | `4000` reads 1,000 VDP words starting at VDP address `1000` |
| Pixel rectangle | `32 * width * height` | `413C` runs eight scanlines per row and stores two words per column |
| Maximum per slot | 21,844 (`5554`) | `4 + 2000 + 32 * 620` |

The valid maximum extents are end-exclusive:

| Depth before save | Physical start | Maximum end |
| --- | --- | --- |
| 0 | `0F0000` | `0F5554` |
| 1 | `0F5554` | `0FAAA8` |
| 2 | `0FAAA8` | `0FFFFC` |

The helpers choose data selector `010C=03C0/03D0/03E0/03F0` from the offset's high two bits, then access `8000 + (offset & 3FFF)`. The word loops change pages at 16 KiB boundaries. Thus these are contiguous physical slots across bank windows, not independent small buffers limited to the first page.

`004B:65B6` decrements the depth, reads the saved header and invokes the inverse text/pixel routines at `005A:409E/4212`. `010A:8D43` can separately fill the entire last page `0FC000..0FFFFF` with `FFFF`; entry through `8D2C` is conditional. The analysis does not claim that clearing happens on every popup or that malformed zero dimensions are safe.

## LCD backup

The normal entry `004B:64D0` also rejects depth **3 or greater**. Its accepted depths 0, 1 and 2 select pages `03C0`, `03D0` and `03E0`, with logical destination `8000`. `003B:5F42` copies `2000` LCD bytes and the two `100`-byte buffers at logical `274E` and `284E`, totaling `2200` bytes. `003B:5FCE` reverses that operation; `004B:6698` selects the source after decrementing the depth.

The accepted save extents are physical `0F0000..0F21FF`, `0F4000..0F61FF` and `0F8000..0FA1FF`. The encoded save/restore dispatch also contains a depth-3 page-`03F0` arm, but the normal save-entry guard excludes it. Its presence is not evidence of a reachable fourth normal LCD save.

## Runtime scope and design consequence

The retained Mouse+CRT run observes a depth-1 Command popup with header `14 05 11 0A` at physical `0F0000`. Its width 17 and height 10 imply 7,444 bytes for that backup. It does not exercise the maximum three-slot extent. The upper-tail exclusion rests on the byte-checked reachable storage mechanisms, not on claiming complete dynamic coverage.

Permanent code, browser state and file buffers must therefore live elsewhere. Borrowing any of this area would require an explicit overlay contract that preserves live backups and survives native drawing, nested dialogs, errors and screen changes. No such overlay or reservation is qualified here. The lower candidate `003D3E..005C7F` remains unqualified.
