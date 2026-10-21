# IM1 mandatory v9 GB-6, IMG handoff and packed SDS results

**Date:**2026-10-19. **Decision:** IM1 remains OPEN. The resulting image-selection OS must include selectable **v9 GB-6 (X4/Y4)**. V8 is excluded from delivery. Browser-only images are diagnostics.

The later [cancellation/recovery results](bluescsi-im1-cancel-recovery-results-2026-10-19.md) supersede this document's partial fit census:7,835/8,002 bytes, scoped Exit drain cancellation, paced readiness, visible interrupted-mount/error messages and explicit selection/native Load recovery now pass. IRQ/MIDI service, full operation admission and complete fit remain open. The user also confirms real-hardware boot-ROM GB-6 selection and retention after restarting; that report does not qualify the browser on hardware.

The existing selectable boot ROM is retained unchanged: `temp/work/gb6_combo/Roland_S-760_v1.11.GB6.BIN`,32,768 bytes, SHA256 `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb`. The browser adds no boot-ROM change. Originals are byte-exact. All results below are private native emulator evidence using ordinary physical-port/MIDI inputs and read-only observers; they do not establish physical BlueSCSI/GB-6 parity.

## Mandatory v9/browser candidate

[Native evidence](../condensed/validation/bluescsi-im1-gb6-native-2026-10-19.json) contains build identities, exact private builder/runner sources and per-profile observations. The OS hash is `44a1141f0b8a1cfe10a0b03a76ae6a47f4bb58a621a95eeed32cca7a02ba50f4`. A fresh exclusive rebuild reproduces it; v9 is mandatory in that builder.

| Check | Observed result |
| --- | --- |
| Boot-ROM Setup | Controller sequence0,0,1,2,3,3; both limits respected; ordinary Exit saves mode3 |
| Cold reboot | Boot staging and running OS both retain controller3 |
| No CRT option board | Boot and OS fall back to controller0 |
| Original controller modes | Modes0/1/2 selected through Setup, saved and booted; Mouse moves from0,0 to10,6 through native relative input |
| GB-6 ISO browser | Four100-entry catalogs,15 pages on ISO A, actual index99 mount, native CD1 Load/Perform,13 samples/119,808 exact B bytes, playback/release before and after Exit |
| GB-6 IMG browser | Dedicated collection on target2, actual index99 mount, automatic native HD2 handoff without Scan, same exact sample/playback/Exit acceptance |
| Same-session IMG switch | B index99 to A index0, automatic handoff and ordinary native clear-memory confirmation; both119,808-byte variants match and playback peaks have ratio1.999979 |

The library remains unchanged during each accepted run. Staging valid A/B media before a run is separate from the hash-protected acceptance interval. RC-100 selection/boot does not qualify remote packets; Panel/LCD boot does not qualify the LCD browser. The v9 decoder and sensitivity were unchanged.

BUG-147 was a private input-target error: requested coordinates between reachable8-pixel positions can round into gaps. One centre-point retry also missed Next. Read-only cursor tracing led to exact reachable native text-row coordinates, retaining the actual D8 index and exact PCM assertions. Both failed runs are preserved and excluded from acceptance. This did not require changing GB-6 code or runtime pointer behavior.

## Packed v9/browser/SDS successor

[Packed native evidence](../condensed/validation/bluescsi-im1-packed-sds-2026-10-19.json) contains the layout, patch bytes/disassembly, callback targets, sources and native results. Its OS hash is `286064ff224f81fe345e1da78c94fd4ee1cb7f48c7cc8fa3e4bccc085b1e5540`.

The old addresses collide:831 retained SDS helper bytes overlap the earlier browser code reservation (734 conflicting changed bytes). They cannot simply be layered. Sharing callback save/restore code reduces browser code from2,597 to2,278 bytes. The retained640-byte remote helper,160-byte local owner and31-byte early-cancel helper are regenerated at new addresses; listing, resources and context are repacked. All code spans disassemble, all four indirect callback body pointers and the common return point to decoded instruction starts, and occupied intervals do not overlap.

| Candidate-region component | Bytes |
| --- | ---: |
| Browser/sender/UI/handoff/Exit code |2,278|
| Retained SDS helpers |831|
| Screen resources |639|
| One100-entry listing |4,000|
| Context |92|
| **Named total / region** |**7,840 /8,002**|

The remaining162 bytes are split across gaps. GB-6 baseline patch sites are preserved separately outside this OS region. The shared callback local frame is80 bytes (prior76 plus the saved dispatch register and common return); native caller/ISR depth is additional and unbounded by this result.

On this exact packed hash, GB-6 ISO browsing, index99 mount, native Load/Perform,13 allocations/119,808 exact bytes, playback/release, four catalogs and Exit pass. Every retained SDS patch span and browser code survives. After loading, ordinary System/MIDI controls enable SysEx reception. An early receive CANCEL settles at allocation cursor13/owner0; retry reserves14/1, then publishes14/0 with160 exact appended PCM bytes. All13 preexisting descriptors and119,808 PCM bytes remain unchanged, and all packed code/repair spans remain exact through the lifecycle. No guest RAM/register/PC forcing was used.

The dedicated IMG and repeat-switch runs above use the preceding mandatory v9/browser image. The packed successor directly qualifies ISO plus sequential SDS receive lifecycle so far. Relocated remote-send timeout/ACK paths, local sender paths and concurrent browser/SDS operations remain unqualified. No native driver/runtime source changed; the preceding748-test backend result was not rerun for these firmware-only experiments.

## Remaining feasibility gate

The newer discovery/compact-list candidate below supersedes the162-byte residual. Operation admission/cancellation/recovery and unfinished UI still require a complete fit measurement. General cache/geometry/reset/cross-target faults, filename collisions/filter equivalence (BUG-145/146), writable Save/cold Load, stereo media, remaining controller paths, full stack/IRQ bounds and physical qualification remain open. The [active roadmap](bluescsi-image-mount-plan.md) carries the split checkpoints. No feature-level GO or release is claimed.

## Selected-target discovery and compact listing

[Discovery/fit evidence](../condensed/validation/bluescsi-im1-discovery-fit-2026-10-19.json) records a byte-exact exclusive rebuild of candidate `bcc31a783cb4e7cafbc4942eab3af98a8d0a3038632c6ea45341fb242b4b9f21`, retaining selectable GB-6 v9 and every relocated SDS repair. The boot ROM stays unchanged.

The PIO receiver consumes all40 wire bytes per D7 row but stores34: protocol index, file kind and all32 name bytes. The trailing wire terminator and five-byte file size are discarded. Rendering already bounds names to32 bytes. The sender counts actual wire bytes separately, so a100-row reply still must contain exactly4,000 bytes. Native RAM comparisons verify all100 retained rows, including exact32-byte names, rather than only visible rows. The listing is private storage; no native disk buffer is borrowed.

| Candidate-region component | Bytes |
| --- | ---: |
| Browser, sender, selected-target discovery and SDS guard |2,577|
| Retained SDS helpers |831|
| Screen resources and complete vendor signature |683|
| One100-entry compact listing |3,400|
| Context |92|
| **Named total / region** |**7,583 /8,002**|

This saves257 named bytes against the preceding packed build despite adding discovery. The419 residual bytes comprise3 before browser code,239 after code,56 after the listing,21 after resources and100 after context. They are not419 contiguous code bytes. Callback local stack remains80 bytes; full caller/ISR depth is open. Static disassembly, direct branch/call targets, all five indirect callback/return literals and occupied intervals pass.

Each selected configured target is qualified with six-byte extended INQUIRY (allocation96), BlueSCSI identity/API checks, then MODE SENSE(6), DBD/current page31/allocation48, including the full44-byte page header/signature. All four configured IDs pass. An ordinary target's36-byte INQUIRY is refused before DA/D7/D8. This does not implement a dynamic collection/target map or identify the installed physical firmware version. BUG-148 fixes the first private candidate's erroneous ten-byte discovery dispatch; that failed experiment is excluded from acceptance.

Native ordinary GB-6 input qualifies empty, one-entry and100-entry catalogs. All32 bytes of each100-entry filename remain exact. A101-entry folder's DA returns CHECK CONDITION; no D7 follows. The compact buffer boundary and every browser/SDS code span remain intact. ISO index99 selection through15 pages, automatic native Load,13 allocations/119,808 exact bytes, playback/release, all four collection catalogs and Exit pass again on this exact hash. Library files remain unchanged. IMG/repeat switching still refers to the earlier v9/browser candidate.

After loading, a genuine SDS receive header while the browser is open displays the native Sample Dump Receiving modal. Collection clicks leave the92-byte browser context,3,400 listing bytes and SCSI command log unchanged, with cursor14/owner1 still active. CANCEL returns13/0. Another early cancel settles13/0; retry then publishes14/0 with160 exact new PCM bytes while preserving all13 prior descriptors and119,808 PCM bytes. Every packed code span remains intact. BUG-149 fixes an initial test expectation that the browser callback should run beneath the modal. This demonstrates native receive-modal exclusion, **not execution of the newly linked direct busy guard**, general disk-operation exclusion or protection against incoming MIDI during the masked SCSI callback.

Native cancellation/recovery, load/save/format ownership, relocated sender paths, error/footer/identity presentation, filename policy and the other remaining gates above still need implementation and measurement. The419-byte residual remains a partial fit result. No emulator/runtime source changed; the prior748-test backend suite was not rerun for these firmware-only experiments.
