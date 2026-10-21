# BUG-168: native disk performance suspension

BUG-168 is **FIXED for the tested native browser profile**. The repair reuses Roland's performance-processing shutdown/restore path during admitted browser actions. It does not add the rejected broad timer checkpoints or change the boot ROM. Full IM1 and physical qualification remain open.

The production test image is `e78750c233cc77faad9f2b6751fc9eddff9296beabfa17650297f3b5c63b0a35`. The selectable boot ROM remains `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb`; mandatory GB-6 v9 X4/Y4, retained SDS repairs, Verify Medium and warning text repairs remain. Native executable `a42d26f755d2d902ac1adb79b76c60b3373be167e849c35ad09a568691bfa937` is unchanged. [Self-contained validation](../condensed/validation/bluescsi-bug168-native-policy-2026-10-20.json) includes builder/runner sources, identities, raw matched clock values and an independent decoder.

## Behavior and code reuse

Dense notes originally exposed a 479 ms native service that lost seven TIMER1 wraps. Concurrent note playback during SCSI is not a product requirement. Stock native Initialize/Save/fresh Load confirms performance mode0 during 115 observed bulk commands (58 reads / 41 writes in the Save process and 16 reads on fresh Load), with 119,808 exact PCM bytes and playback/release. This does not mean every discovery or small SCSI command is muted.

The browser now saves `1BA5` in its previously unused context byte `C+30`, calls native `001F:4F8D` with `R9D=0`, and restores the saved mode at action completion or before native UI handoff. `C+31` is the action lease. The lower entry reuses 4F7F's performance transition without its unrelated UI redraw. Panel/mouse/GB-6 navigation stays usable. The helper requires the original caller's interrupt-enable flag and software-timer mask bit; masked callers are refused before changing R9D or enabling interrupts.

During the action, native `4000` skips the 43A3 performance path and timer `CB67` skips the MIDI parser. Receive interrupts still drain arriving serial bytes. Complete messages arriving while busy are ignored through the native reset; they are not queued for later performance playback. Normal MIDI processing remains available between actions, including fresh idle SDS and Remote Mode requests. The native restore resets ring/parser/voice state and restores the previous performance mode. The device-controller setting at2476, including GB-6 selection, is separate and unchanged.

## Verification

- **10 production-candidate native cases / 101 RAM snapshots pass:** dense 769-byte MIDI; CRT and LCD D7/D8 cancellation and explicit retry;32-byte filename confirmation; genuine first/last-byte withheld-REQ faults with simultaneous MIDI and239616 exact stereo bytes; busy/idle SDS and Remote Mode; both busy-time mount request types followed by 119,808-byte native Load and playback/release.
- **9,003 suspended-service pairs** preserve scratch registers (apart from the intentional idle-timer adjustment), stack restoration, selectors and masks. Longest observed complete service is 0.430125 ms; the original dense reproduction reaches 0.290750 ms. These maxima are observations, not physical WCET measurements.
- **145 commands / 502,771 elapsed-time samples** in eight instrumented production cases agree exactly with the guest's32-bit accumulator. The largest observed TIMER1 sample gap is 0.300250 ms; wall-time comparison differs by less than one timer tick. All sampled commands have R9D=1BA5=0. Compressed raw matched values can be revalidated without private logs.
- **A separate one-byte diagnostic patch** lowers only the total-budget comparison from 32 wraps to 1. While the target continues progressing, total timeout occurs at 65,789 ticks, sends no follow-on mount, and explicit retry with a smaller catalog recovers. Samples/playback/release pass. This diagnostic image is not the production candidate; the production limit remains 2,097,152 ticks.
- **65,536 decoded-byte permission cases** check the caller-I/software-timer guard. Mode0 removes parser/control loops: longest native timer path 66 instructions; MIDI receive wrapper/path 23. This is conditional on the recorded native vectors/mappings, caller masks 20/20 and normal 31.25 kbps serial arrival. No full-hardware or arbitrary-interrupt bound follows from it.
- Exact fresh-directory rebuild, code decode/diff audits, original-image hashes and retained patch identities pass. Allocation is**6,736 / 8,002 bytes**, leaving**1,266 free**. Main browser code 4,111 bytes ends at physical 508F; the existing 89-byte parser admission helper moves to 5100, leaving 935 contiguous bytes before 5500.

The existing 1,122-pass / 3-skip backend result belongs to the preceding BlueSCSI source-patch work. No backend/runtime change or fresh full-suite result is claimed here.

## Limitations and next gate

The native result closes the firmware deadline defect by preventing the unbounded note-processing service path during SCSI. It does not qualify physical BlueSCSI timing/configuration, installed upstream firmware patches, arbitrary target faults or write-reset behavior. The new native controller-transition callee must be included in the remaining stack/ownership proof; the predecessor's 166-byte synchronous bound is not a complete bound for this candidate. RC-100 input remains user-waived, with compatibility assumed.

The earlier clock-hook trials remain rejected. A preliminary stock observer's redundant physical-state field had the wrong address; the proof instead reconstructs1BA5 from actual masked bus writes and cross-checks every native 4F8D read. Candidate observations use corrected physical 82BA5. An initial mount test incorrectly limited its MIDI observation window to D8 completion; it was rerun against the full suspended action including readiness. Neither observation error is used as acceptance evidence.
