# S-760 modulation-related IC documentation

Checked2026-10-15. This index distinguishes manufacturer datasheets from Roland-authored service notes and unverified research leads. No public register-level manual was located for the custom TVF/wave/mixer ASICs in this search; that is a search result, not proof that none exists.

| Part / S-760 location | Available documentation | What it establishes |
| --- | --- | --- |
|MB87424A / IC29 TVF|Existing [S-760 service notes](../../Manuals/ROLAND_S-760_SERVICE_NOTES.pdf), printed pp18–19; downloaded [JD-800 notes](../../Manuals/IC_Documentation/Roland_JD-800_Service_Notes.pdf) and [JD-990 notes](../../Manuals/IC_Documentation/Roland_JD-990_Service_Notes.pdf)|Board connections, pin labels and shared-family implementations. No decoded register commands or interpolation law located.|
|MB87422 / IC27 and MB87423A / IC28 wave ASICs|Existing S-760 notes; [Roland S-770 service notes](https://synfo.nl/servicemanuals/Roland/ROLAND_S-770_SERVICE_NOTES.pdf)|Sampler address/data pipeline and synchronization context; S-770 is a comparison platform, not an exact S-760 specification.|
|TC24SC220AF-007 / IC30 mixer|S-760 notes; JD-800 notes list TC24SC220AF-001|Custom mixer family comparison only. The -001 and -007 suffixes differ; register/algorithm identity is unproven.|
|HC151 / IC51 clock selector|[Toshiba TC74HC151AF documentation](https://toshiba.semicon-storage.com/us/semiconductor/product/general-purpose-logic-ics/detail.TC74HC151AF.html)|Manufacturer pinout, selection truth table and electrical timing. Publisher's automated PDF download returned403; no local datasheet was saved.|
|F74 / IC49 clock logic|Downloaded [TI SN74F74 datasheet](../../Manuals/IC_Documentation/TI_SN74F74.pdf); [manufacturer page](https://www.ti.com/product/SN74F74)|Flip-flop pinout, clock edges, preset/clear behavior and timing. Family reference; verify the actual board package/vendor before applying electrical limits.|

The three downloaded PDFs were opened successfully and their title pages visually checked. [Source URLs, sizes and SHA256 identities](../../Manuals/IC_Documentation/sources.json) accompany them. The existing S-760 manual was not changed.

## Schematic findings relevant to the current timing investigation

Visual inspection of printed S-760 p19 confirms IC29 is labeled MB87424A, with WI0–WI17 input lines, WO0–WO23 output lines, address/data bus connections and clock/synchronization/control pin labels. The clock section shows crystals16.9344MHz,18.432MHz and12.288MHz alongside the HC151 selector and flip-flops. These are external wiring observations, not an internal arithmetic-width claim or a20ms control-period specification.

The schematic-derived physical map already places the101000 aperture under CS_FILT; see [hardware map](../condensed/01-hardware-and-memory-map.md). The001B/001A command words,101020 initial coefficient and101030 target coefficient still derive from firmware/native transaction evidence. Neither these drawings nor the retrieved standard-logic datasheet explain what those commands do inside the custom TVF.

Useful remaining checks are tracing the selected clock and synchronization nets into IC29, matching CPU read/write/chip-select strobes to the emulator bus interface, and checking reset/state lifetime. Do not assign a hardware ramp duration from crystal frequencies alone. The current20ms ramp remains a hardware-tested diagnostic candidate, not a decoded register contract.

## Reverse-engineering lead

Giulio Zausa's [39C3 talk](https://media.ccc.de/v/39c3-from-silicon-to-darude-sand-storm-breaking-famous-synthesizer-dsps) and [MMO-CHIP repository](https://github.com/giulioz/mmo-chip) are primary accounts/tools for custom Roland silicon research. The talk description focuses on TC170C140 ESP, and the repository is a general die-analysis tool. This search did **not** verify a public MB87424A register map, netlist or emulator there. Do not treat the lead or secondary reports as a recovered TVF datasheet. No contact/message was sent.
