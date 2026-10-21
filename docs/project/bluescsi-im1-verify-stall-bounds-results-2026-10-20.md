# IM1: Verify Medium repair, stalled targets and native bounds

**Date:** 2026-10-20. **Decision:** IM1 remains open; the timing candidate is not promoted.

Nine native cases pass, with 93 memory snapshots. BUG-173 is fixed: Verify Medium now reads the inclusive last sector before descending to zero. The repair occupies the original 48 bytes and adds no memory requirement. A separate simultaneous MIDI/stalled-target case fails the exact-byte check and is retained as negative evidence under BUG-168.

[Roadmap](bluescsi-image-mount-plan.md) · [Machine-readable evidence, identities, raw matched rows and reproduction sources](../condensed/validation/bluescsi-im1-verify-stall-bounds-2026-10-20.json)

## Exact candidates and scope

| Artifact | SHA-256 | Allocation |
| --- | --- | --- |
| Established candidate with warning and Verify Medium repairs | `0be06d4d11a921a0d0b4a25829ee1441c1266d4c07be0633d04968985865a00e` | 6,452 / 8,002 bytes; 1,550 free |
| Experimental timing candidate with both repairs | `5581ee53a84ea5395ee0bb554fc2b31128bb5740835789b335c83b4c9a548f94` | 6,580 / 8,002 bytes; 1,422 free |
| Unchanged selectable GB-6 boot ROM | `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb` | No new boot-ROM patch |
| Pre-fixture-change emulator | `57e45eaf6fa298b38f3454f4a2a8449c7e1569419b3f38fdfda9a0f4e1f613ec` | First four accepted cases |
| Emulator with opt-in one-shot D7 stall | `a42d26f755d2d902ac1adb79b76c60b3373be167e849c35ad09a568691bfa937` | LCD cancellation and fault cases |

GB-6 v9 and the existing SDS fixes remain in both combined candidates. Each differs from its wording-only predecessor solely within the native 48-byte Verify Medium loop. Historical acceptance remains attached to its actual image/executable; this batch does not relabel the entire earlier matrix as tested on these successors. Original OS and boot-ROM hashes are unchanged.

## Verify Medium: BUG-173 fixed

The loop at `0129:B717`, file `0x52317`, was byte-identical to original OS 2.24. READ CAPACITY supplies the inclusive last LBA, but the original loop decremented before its first read. A fresh run of the preceding combined candidate reproduced the omission. This establishes inherited code as the cause; it is not a claim of a separate full original-OS Format run.

[The guarded patcher](../../scripts/patch_disk_verify_extent.py) moves DEC/SUBC after the zero/end check, retaining native progress, read and error handlers. Relative calls are rebased and all 48 bytes are decoded at their runtime address. The original image size and surrounding bytes are preserved.

Native physical-input Format/Verify runs on private writable images establish:

- Established successor: all 65,536 sectors read exactly once, LBA 65,535 through zero, before native initialization writes.
- Timing successor: all 65,537 sectors read exactly once, LBA 65,536 through zero, including the 16-bit borrow boundary.
- Both complete the native empty Roland header and browser/Utility return flow.

Twelve decoded-loop tests cover one-sector, two-sector and boundary extents, inherited failure reproduction, guarded patching, and native error-handler continue/abort behavior. These model checks complement the native runs; no injected native medium-read-error or physical surface-verification result is claimed.

## Nine accepted native cases

| Case | Result |
| --- | --- |
| Established 65,536-sector Format + Verify | Complete descending read census and native initialization |
| Timing 65,537-sector Format + Verify | Complete census across 16-bit boundary |
| Timing LCD filename selection | Full 32-byte names, Back/held-key behavior, explicit selection and exact 119,808-byte Load/playback |
| Timing CRT cancellation/retry | D7 drain, interrupted D8/no automatic handoff, explicit retry/Load/playback; retained SDS cancel/retry and exact 160-byte publication |
| Timing LCD cancellation/retry | D7/D8 recovery, no automatic follow-on, explicit exact Load/playback |
| D7 stall before byte zero | Error, bus release, no automatic D8; explicit retry and exact Load/playback |
| D7 stall before byte 3,999 | Same recovery at the final byte |
| D7 stall after one byte, MIDI afterward | Exact 769-byte stress plus audition, resident 239,616-byte stereo content and playback/release preserved |
| D7 stall before byte 3,999, MIDI beforehand | Same content and MIDI preservation; traffic precedes the actual stall |

The four accepted stalled-target cases release the bus after approximately 5.210–5.263 ms of withheld REQ. These are observations for a diagnostic peripheral, not worst-case deadlines or physical BlueSCSI timing. Crucially, neither accepted dense-MIDI case contains MIDI reads during the stall itself.

The one-shot peripheral profile is disabled by default and requires both an image root and `S760_TOOLBOX_IMAGE_STALL_AFTER=0..3999`. It holds BSY/data-in while withholding REQ during PIO D7. Bus release, controller reset or bus reset clears the active stall; an explicit retry can succeed. Nine synthetic SPC cases check three thresholds against three release mechanisms. These are fixture-contract tests, not firmware acceptance. The fault's host-timeline state is not checkpointed.

## Simultaneous MIDI case: failed, gate retained

A separate run starts MIDI at the first observed withheld REQ. It records **323 native MIDI reads during the stall**, and the bus releases after **113.279125 ms**. The browser reaches its error screen without an automatic switch, permits explicit catalog retry, and returns to preview.

However, the complete expected byte sequence is absent: **585 observed reads versus 775 expected**, including the six audition bytes. That is a 190-byte deficit. The run fails before exact-PCM acceptance and is excluded from the nine passes. This establishes a failed simultaneous-traffic recovery case, not the exact point where bytes were lost. The longest observed service in this run is 31.747875 ms; that finite maximum does not close BUG-168. Next work must trace receive service across timeout/error return and establish bounded native peripheral waits and total deadlines before promoting the timing trial.

## Stack and parser bounds narrowed

Static decoding proves each immediate init/update/exit/action dispatcher frame uses **12 bytes**: five saved words and one synthetic return. Native observations agree with the return targets. Observed outer prefixes on named routes are 28, 30 or 62 bytes; those are observations, not universal maxima. Neither result closes all modal ancestry, IRQ nesting or stack ownership. The earlier 166-byte synchronous-callee result and conditional 62-byte IRQ result cannot simply be added into a complete proof.

The native parser's sentinel scan at `000F:25A6..25FC` is bounded by its initialization and insertion structure: 16 records of 33 bytes, at most 32 insertions, at most **32 comparisons per scan / 528 total**. Source bytes match the original OS; 4,112 model cases check the derived bound. The proof assumes no concurrent external writer and does not bound the whole parser or peripheral latency.

Reachable native waits still lack a local iteration cap: MIDI TX-ready at `001F:68A2` (helper `689D`, register `0114` bit 1), and wave-port ready at `001F:7118` and `7344` (helpers `6FBF` and `72D0`, `C000` bit 1). Their completion contracts and other remaining loops must be resolved before claiming a service-time bound.

All 93 accepted snapshots preserve 7,360 immutable/gap bytes, with 642 explicitly mutable bytes excluded, plus the repaired loop, timing hook where applicable and four warning resources. This remains named-route lifetime evidence, not a universal indirect-alias/DMA proof.

## Regression results and remaining work

Serial MSBuild completed both native targets. With the fault profile disabled, ordinary boot/input/MIDI/release checks pass before and after the change, and all **33,554,432 wave-memory bytes match exactly**.

The full backend suite reports **1,088 passed, three skipped, one failed**. The failure is `test_rom_boot_loads_compiled_os_into_ram`: the minimal authored OS yields its header read but zero of the expected 112 track transfers. The same test fails on the saved pre-change executable. It is recorded separately as BUG-174; the suite is not reported as green. After correcting the fault test's reported target count to one exercised target, all **44 focused image-fixture and Verify Medium tests pass**.

IM1 still requires BUG-168 timing and simultaneous-MIDI recovery, complete native stack/IRQ and indirect/DMA ownership, other transaction faults and native-write reset qualification. Physical configuration/library/write/timing qualification remains separate. RC-100 input remains user-waived/assumed. No extra firmware region is required by this batch.
