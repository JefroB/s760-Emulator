# Transfer field packing and length checks

This analysis follows seven direct helper calls from the system-message region to page 0:F874/F8A6. The mapping applies to timer-service execution with fetch selector 0106=0; other contexts still require evidence. No firmware or emulator behavior changes.

## Four-byte fields

For seven-bit input bytes `a,b,c,d`, both helpers compute:

`value = (a << 21) | (b << 14) | (c << 7) | d`

F874 reads B04F..B052 and stores the low/high words at B03C/B03E. F8A6 reads B053..B056 and stores B040/B042. Each helper then shifts the full value right once and stores **only its low 16 bits**, at B044 or B046. Those derivatives are not full-width lengths or addresses. The formulas assume seven-bit data input; malformed high-bit bytes are handled by the surrounding parser, not qualified by these helper equations.

The input byte order and shifts are taken directly from the decoded instructions. A separate arithmetic check applies the individual 8-, 16- and 32-bit register operations and compares them with the compact formula on boundary and deterministic randomized cases. This checks the algebra, not hardware execution.

## Normal-path length gates

6049 compares the receive pointer with B058 before calling both helpers. With initial pointer B04F, that means nine received data bytes after the header: two four-byte fields plus one byte. Interpreting the last byte as checksum is supported by the preceding additive validation at F7.

6261 instead derives a payload count as `receive_pointer - B054`, stores it at B040/B042, and stores its shifted low-word derivative at B046. This subtracts the four-byte initial field plus one checksum byte. It then checks the receive pointer before calling only F874. Thus B040/B042 can be populated either from an explicit packed field or from received-byte count, depending on the command path.

66B5 also requires pointer B058, then calls both helpers. A zero value in B040/B042 follows an early completion/reset path. Nonzero values are compared with 256 before transfer setup continues. This is evidence of a bounded transfer chunk, not yet proof of every packet format or overall transfer limit.

## Different packing in the 7E path

At 6E05, two bytes from B04F are unpacked as `a | (b << 7)` and stored at B180. The next byte is stored at B1AA. Four calls to 6E43 unpack three bytes each as:

`value = a | (b << 7) | (c << 14)`

They write four-byte fields at B182, B186, B18A and B18E. A following byte goes to B1AB. These fields are least-significant-group first, unlike the normal four-byte helpers. Semantic names for every field are not yet promoted to confirmed facts.

6E64 limits B180 to 511. It also compares B18A and B18E against B186 minus one and adjusts out-of-range cases while setting B1AB to 7F. These are observed validation/normalization paths; full transfer semantics and corner cases remain under analysis.

## Evidence and remaining work

The [validation record](../../condensed/validation/os-transfer-fields-2026-10-16.json) records exact instruction anchors, tool/input identities and arithmetic-check results. The exploration manifest adds the two fixed helpers and their context-qualified callers. Next work is to trace these fields into address mapping, memory allocation and packet acknowledgment routines. No hardware transfer has been performed by this analysis.
