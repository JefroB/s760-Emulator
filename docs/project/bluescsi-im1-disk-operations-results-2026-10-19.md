# IM1 native Disk operations and writable Save

BUG-156 is fixed: the prototype no longer leaves native Disk actions inaccessible behind its replacement popup. From Image Library collections, **Disk options** opens nine native actions in the existing nine fields. They reuse the stock0196:94D9 dispatcher and native event/screen transitions. No second268-byte native menu clone or new boot-ROM change is required. Browser screens still clear the keyboard and keep the blue body.

The new page preserves Load, Save, Copy, Delete, Utility, Save System, Optimize, Convert Load and Volume Dump FD. Eight native action screens were observed on the first menu variant. Convert Load reaches native screen0100 for the staged floppy profile, following initial table target00FE. The ninth action exposed BUG-157: compact stock text tokens were misread as OS Load. Its corrected label is **Vol. Dump FD**. The corrected final candidate reaches the stock Volume Dump FD system-disk caution; the test cancels it without confirming a write. Other action execution is not implied by navigation.

## Writable Save and cold Load

Ordinary saved GB-6 controls select ISO index99, then native Load restores13 allocations and119808 exact B sample bytes. Through Disk options, Utility quick-initializes a separate private10MiB HD0; native performance Save writes that HDD, which is exported explicitly. Parsing the saved Roland allocation chains returns13 samples with all119808 expected bytes. A fresh runtime cold-loads the exported HDD and reproduces the same119808 bytes and audition peak. Original source media and all403 library fixture hashes remain unchanged. This qualifies a separate writable destination; it is not physical BlueSCSI read-only enforcement or concurrent-operation proof.

## Fit and catalog contract

The first Disk page costs100 code+100 data bytes, leaving only16 free. A further catalog reduction stores only all32 filename bytes. Before publishing the catalog, it requires every received D7 index to equal its ordinal0..count-1; unexpected indices latch an error and reject the catalog after successful draining. An index is retained implicitly only after that validation. There is no filtering or sorting, so selection preserves the verified protocol index. This does not repair upstream BUG-145/146.

All25700 decoded checker cases pass:100 valid indices,25500 mismatched pairs and100 already-latched error cases. Native0/1/100-entry catalogs retain every32-byte name exactly;101 entries reject. Native index99 mounting, listing/switch cancellation, exact Load/playback, retained SDS cancellation/retry and Remote Mode late-admission recovery pass. Malformed wire-index draining remains a model/static contract, not a native negative-wire test.

| Component | Bytes |
| --- | ---: |
| Browser, transport, ownership and native Disk dispatch |2956|
| Retained SDS helpers |831|
| Existing resources/status/signature |739|
|100 names, validated implicit indices |3200|
| Context |92|
| Native Disk label table |100|
| **Named total / region** |**7918 /8002**|

There are **84 free bytes**, split3/68/13, with **68 directly after code**. Exact rebuild, instruction targets, nonoverlap, mandatory GB-6 v9 and immutable original hashes pass. Full fit remains open for unfinished UI/controller/error policy and remaining safety gates.

The complete native Save/cold-Load and32-byte-catalog tests use the preceding label variant (`43dddd...`). The final label correction (`8f59f0...`) changes only the100-byte text table and one immediate label-pointer byte; callbacks and SCSI/save logic are unchanged. Final-hash Volume Dump warning/cancel and exact rebuild pass. The first33-byte menu variant (`0cd0cc...`) supplies the other eight navigation observations. These identities remain separate in validation.

General native Load/Save/Format overlap, external initiator/session operations, physical protection, complete filename preflight/footer/help, LCD/RC-100 and remaining controller/media/stereo/cache/reset/stack qualification remain open. No complete-fit or hardware GO is claimed. No runtime/emulator source changed; the earlier748 backend test baseline was not rerun.

Final candidate SHA-256 `8f59f0d0122bcd5dd113bf4820a75406bef026aee96d39e146299ba60fdfb9db`; boot ROM `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb`. [Validation](../condensed/validation/bluescsi-im1-disk-operations-2026-10-19.json). [Active roadmap](bluescsi-image-mount-plan.md).
