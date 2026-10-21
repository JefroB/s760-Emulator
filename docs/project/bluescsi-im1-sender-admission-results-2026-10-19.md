# IM1 sender admission and completion

Seven ordinary native workflows pass on the existing compact-catalog candidate. No firmware bytes were added: mandatory GB-6 v9, browser and retained SDS fixes remain at7776/8002 bytes, with226 free and98 directly after code. The retained guards suffice for these cases; this does not establish a general disk-operation lock.

| Case | Observed result |
| --- | --- |
| Remote sender with menu attempts | Owner7 persists; no browser Toolbox command starts. Peer CANCEL releases ownership, allocation and descriptor survive, then image selection commits normally. |
| Local sender with menu attempts | Owner8 becomes0 on clicks; no browser command starts during the attempt. Subsequent explicit selection succeeds after cleanup. |
| Local sender without clicks | Owner8 persists across two2.8-second intervals with intervening packet ACK progress, distinguishing input cancellation from natural timeout. Peer CANCEL and image re-admission succeed. |
| Complete remote send | Packets0..115, all checksums,9216 allocation PCM bytes and96 zero wire-padding bytes match. Owner returns0; selection resumes. |
| Complete local send | Same complete116-packet/9216-byte result, then ordinary image selection. |
| Outgoing request during D7 | All seven command03 bytes arrive before D7 ends; native ownership becomes7 during the transfer. D7 drains4000 bytes/status0/transport0, then Busy prevents catalog publication. CANCEL/retry restores the catalog. |
| Outgoing request during mount/readiness | Ownership becomes7 before READ CAPACITY finishes. Busy leaves native drive8 unchanged and handoff0; CANCEL/retry restores catalog access. The image itself may already have switched. |

Both complete sends preserve the received160-byte seed payload and emit the full9216-byte native allocation. The last packet contains only16 allocation bytes plus96 zero encoded padding bytes. Those raw padding zeros must not be treated as64 extra PCM bytes; the native unsigned SDS decoder would map them to-32768. All232 complete data packets match their checksum and allocated PCM oracle. Cancelled/control runs also validate every emitted data packet. All accepted RAM snapshots preserve browser and relocated SDS code, allocation cursor1 and the seed descriptor through cleanup. The403 library fixtures match the prior checkpoint hashes in both test roots. The original OS/boot ROM remain immutable.

These are actual MIDI transfers and ordinary GB-6 controls in native MAME. Menu attempts do not prove concurrent execution of native Load/Save/Format. The broad disk/session, reset/save, media/controller, stack/ISR and physical gates remain open. Manufacturer41 Remote Mode and pre-supervisor cases retain their older, separate evidence. Native1FA4 remains a session flag rather than a generic disk-busy flag.

Initial exploratory harness assertions incorrectly required a local sender to remain active on clicks and assumed reopening reset the previous catalog. The corrected harness includes a no-click control and selects from the retained catalog; no firmware change was needed. A first packet-oracle draft compared final encoded padding with extra wave RAM; the final oracle separately validates allocation bytes and raw zero padding, consistent with the earlier sender contract.

Candidate SHA-256 `b299af70002fb4e16177179bab3cf8b38a51bab03aaa3d7ed9cc1b422d7184d7`; boot ROM `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb`. [Validation](../condensed/validation/bluescsi-im1-sender-admission-2026-10-19.json). [Active roadmap](bluescsi-image-mount-plan.md).
