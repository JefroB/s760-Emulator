# IM1 IRQ, MIDI and incoming SDS ownership results

**Date:**2026-10-19. **Decision:** IM1 OPEN. The private selectable **GB-6 v9 X4/Y4** candidate is `4196c31ec7466b53fa001f266cdad38eb506c5d0b48469122bc16a7b384538f3`. The compatible boot ROM and original firmware are unchanged. [Validation, matched observations and exact sources](../condensed/validation/bluescsi-im1-irq-ownership-2026-10-19.json) record six native cases, two IRQ analyses, failing baselines and an exact exclusive rebuild. Inputs use ordinary GB-6/panel/MIDI ports; observers never write guest RAM/registers/PC.

## Conditional interrupt service

The callback captures its original DATA1 bank and saved PUSHA WSR/MASK1 and PSW/MASK0 words from its own stack. Before the common dispatcher return is pushed, their offsets are70/74/76 bytes. The separate RW1E save remains preserved. The service routine restores the original masks/data mapping and enables IRQs only when the caller's saved I bit permits it. It masks again before returning to private code. Readiness waits also service interrupts.

The corrected matched baseline receives48 exact MIDI realtime-clock bytes **after** D7 completes; the cooperative version receives all48 **during** D7. On the final hash, all128 realtime-clock bytes arrive inside service windows before the4,000-byte reply completes. Native timer/MIDI vector reads are observed at200A/203A; no SPC write occurs inside service. BUG-152 corrects the initial observer's invalid MIDI array argument: the endpoint requires a byte string. Invalid zero-RX trials are excluded from firmware conclusions.

| Final-hash observation |128-clock input|21-byte SDS header|
| --- | ---: | ---: |
| Matched service entry/exit pairs |188|188|
| D7 command duration |332.056ms|360.627ms|
| Largest whole service call |1.033ms|35.482ms|
| Conservative observed mask bracket |3.000ms|37.564ms|
| Timer wraps inside measured service |2|1|
| Observed extra stack below callback entry |192 bytes|192 bytes|

Brackets include enabled service work; they are not measurements of one continuous masked interval. These are observed workloads, not worst-case ISR/stack or physical latency guarantees. The80-byte local callback frame is only part of the observed192-byte depth. Other MIDI messages/rates, native callers and physical IRQ routing still need qualification.

## Watchdog and ownership repairs

A genuine SDS header can claim sample memory inside an IRQ service window. Two defects were reproduced and fixed:

- **BUG-153:** The first cooperative mount path checked ownership only at action entry. A header arriving during D8/readiness produced cursor1/owner1 while the browser still wrote native drive1 and queued Load. The final candidate checks2BBA at action entry, after enumeration and immediately before committing drive selection/Load. The same input now leaves the native drive unchanged, queues no Load and reports post-switch uncertainty. After normal receive CANCEL/rollback, explicit fresh selection loads13 samples/119,808 exact B bytes and plays.
- **BUG-154:** Native SDS header/UI service took35.502ms in the failing trace. Counting that CPU time against the5ms no-progress watchdog caused a timeout after373 wire bytes. The final service advances only RW38, the last-progress clock, by exact measured modulo16-bit service ticks. The other34 saved scratch words, selectors, SP and mask/I context restore; the overall elapsed and poll budgets are unchanged. Both observed timer-wrap cases validate the arithmetic.

The incoming-header listing now drains all4,000 wire bytes with raw status0/transport0 and retains all100 compact records exactly. It then returns **Busy**, because SDS owns memory, instead of publishing a catalog or switching an image. The native receive modal blocks attempted image clicks; CANCEL rolls allocation cursor1 back to0 and returns ownership to idle. The post-mount case separately proves the final owner check executes (error11 after successful capacity reply), rather than merely relying on a transport failure.

## Regression and fit

On this same hash, listing/switch cancellation, explicit retry/native Load/playback, retained SDS cancellation/retry/publication, silent D8 open-failure recovery, same-/other-target recovery and0/1/100/101-entry catalogs pass. All accepted snapshots preserve browser/SDS code; library hashes stay unchanged in the existing hash-protected runs. Prior PCM/descriptors remain exact and the subsequent SDS receive appends160 exact bytes. No runtime/emulator source changed; the preceding748-test backend baseline was not rerun for firmware-only work.

| Component | Bytes |
| --- | ---: |
| Browser/transport/discovery/IRQ/admission code |2,814|
| Retained SDS helpers |831|
| Resources/signature/status strings |739|
|100 compact records |3,400|
| Context, including service timer scratch |92|
| **Named total / region** |**7,876 /8,002**|

The126 free bytes are split3/2/8/13/100. **Only two bytes remain directly after the main code block.** Unused field/action debug snapshots and dead argument assignments were removed, and three admission checks share one helper. Further work needs savings or repacking;126 bytes is not a complete-fit promise.

Remaining IM1 work includes general native disk load/save/format exclusion, relocated remote/local SDS sender paths, complete UI/filename policy, full stack/ISR bounds, geometry/stereo/cache/reset/checkpoint/Save-cold-Load behavior, remaining controllers and physical browser qualification. Current exact Load tests cover ISO; earlier IMG/repeat/controller acceptance belongs to earlier hashes. The user's physical boot-ROM selection/restart-persistence report remains a separate confirmed result. See the [active roadmap](bluescsi-image-mount-plan.md).
