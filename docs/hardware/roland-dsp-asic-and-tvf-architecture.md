# Audio components and limits of the current model

The [S-760 service notes](../../Manuals/ROLAND_S-760_SERVICE_NOTES.pdf) identify these board components. Package names are component identifications, not recovered programming specifications.

| Function | Reference | Component |
| --- | --- | --- |
| CPU | IC1 | Intel S80C196KB |
| CPU gate array | IC4 | HG62E33B08 |
| Boot EPROM | IC15 | AM27C256 |
| I/O gate array | IC20 | uPD65012GF-473 |
| SCSI controller | IC25 | MB89352A |
| Wave processing | IC27, IC28 | MB87422, MB87423A |
| TVF | IC29 | MB87424A |
| MEQ | IC30 | TC24SC220AF-007 |
| ADC | IC58 | CS5339-K |
| DACs | IC91, IC92 | AK4328VS-E |

The instrument has 24-voice polyphony and four individual outputs in addition to the stereo output. A software array containing 32 slots is not evidence of 32 physical voices. The ADC is not an AK5339.

Firmware accesses the wave, TVF and MEQ interfaces through banked windows. See [memory and boot](memory-and-boot.md) for the address context. The native driver's register handling is an implementation supported by particular traces; it is not a complete register specification for these custom chips.

The exact interpolation arithmetic, filter topology, coefficient representation, internal precision and complete physical voice scheduling have not been recovered. In particular, there is no established hardware specification for a Hermite interpolator, a four-pole ZDF ladder or the old proposed F006/F008 parameter map. Those claims have been removed.

Native filter and interpolation implementations must be assessed against identified captures. Agreement on static tones does not establish moving-filter or resonant-filter parity. [Capture results](captures/README.md), [audio research](../condensed/06-audio-dsp-and-hardware-parity.md) and the [bug backlog](../project/bug-backlog.md) describe bounded results and remaining work; BUG-005 remains relevant to filter acceptance.

Sources: service-note component list and block diagrams; native implementation in [s760.cpp](../../mame-source/src/mame/roland/s760.cpp). Consult the [IC documentation index](ic-documentation-index.md) for available manufacturer documents and missing ASIC specifications.
