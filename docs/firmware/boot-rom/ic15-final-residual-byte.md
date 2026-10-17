# IC15 final residual byte: file6903

The best current explanation for08 at file6903 (resource mapping0798:8903) is an **unused FDC Sense Interrupt Status command constant**, retained next to the active SPECIFY command template03 BF02. This is a provenance hypothesis, not a recovered symbol or proof of the author's intent.

The active Sense Interrupt routine polls the controller at0182..0195, loads immediate08 at0197, writes it toE002 at019A, and returns019F. It does not read the resource byte. The separate SPECIFY routine starts at8904 and copies exactly three bytes; the preceding setup message ends with NUL at8902. Both neighboring consumers therefore exclude8903. A full-ROM raw search finds no little-endian8903 pointer. Computed or dormant uses are not excluded by that search.

Read-only native probes with unchanged ROM/media and fresh state reach ordinary floppy handoff and Mode-held setup. Byte-lane-aware taps see no read of8903 in either path, while observing the expected neighboring accesses. Normal boot issues the08 command from the immediate-constant routine. Setup observes the preceding terminator at8902. [Assessment and exact anchors](../../condensed/validation/ic15-byte6903-assessment-2026-10-16.json) and [native source/observations/identities](../../condensed/validation/ic15-byte6903-native-v2-2026-10-16.json) retain the limits.

For implementation, preserve the byte unchanged and annotate it `unused_fdc_sense_interrupt_constant_candidate`. It supplies no demonstrated boot dependency; deleting it is unnecessary. Keep semantic status provisional rather than inventing an active consumer.


## Full floppy OS retrieval trace (2026-10-16)

A fresh original-ROM boot monitors all64 possible logical data aliases for file6903, using the actual per-window data selectors and physical ROM-aperture/mirror filtering. Passthrough taps remain active until actual4755 handoff. The matched DMA log proves a512-byte header read, followed by112 contiguous9,216-byte payload transfers from disk004800..1007FF into RAM000000..0FBFFF (1,032,192 bytes), then OS handoff. **Zero accesses read stored byte6903 through any monitored data alias.** The immediate08 routine issues58 Sense Interrupt command writes during the same run. [Trace, observer, identities and checked totals](../../condensed/validation/ic15-byte6903-floppy-load-trace-2026-10-16.json). This establishes non-use on successful ordinary native floppy OS loading; physical hardware, failure/retry paths and dormant diagnostics remain distinct. Coverage unchanged:ROM26,277/32,768=80.19% (+0.00 points),OS62,736/1,032,192=6.08% (+0.00 points); overall not yet quantifiable.


## Read-event watchpoint with history (2026-10-16)

A reusable observer in `scripts/trace_ic15_residual_byte.py` records exact read events, CURPC/post-PC, CPU state, all bank selectors and32 recent instruction addresses. A known-used neighboring FDC template is the positive control. Seven30-second native cases pass with **zero reads of file6903**: successful floppy boot, Mode setup, invalid floppy signature, short floppy (only through first handoff), absent SCSI target with floppy fallback, bad SCSI header with floppy fallback, and valid SCSI header reaching the known269D DMA stall. No unsupported diagnostic input or guest mutation was used.

The debugger's raw disassembly uses the wrong banked data view (BUG-085); all32 positive-control history addresses were matched to original-ROM encodings under the observed0790 fetch context. [Full observer source, events, identities and history](../../condensed/validation/ic15-residual-byte-history-2026-10-16.json). This demonstrates the event logger works and bounds the negative finding to exercised paths; it does not prove no possible caller exists. No target-read event occurred from which to infer a use. Classified coverage unchanged:ROM26,277/32,768=80.19% (+0.00 points),OS62,736/1,032,192=6.08% (+0.00); overall not yet quantifiable.
