# IM1 space recovery: seven-name page window

The current prototype reclaims **2936 bytes net** inside the same8002-byte candidate region. It retains only the seven visible32-byte filenames instead of all100 names. Next/Previous reread DA/D7, draining the full catalog and validating every wire index before display. Selection still uses the verified global index; there is no filtering, sorting, shortened filename or reduction of the100-image-per-folder cap.

Catalog storage falls3200 ->224 bytes, saving2976. Window selection, refresh and origin-clamp logic add40 code bytes. The retained buffer is physical57F0..58D0 (data000F:5BF0); discovery replies up to96 bytes, sense and capacity share it outside catalog display. The buffer never holds the whole collection. All existingGB-6 v9, Disk options and SDS fixes remain included; no boot-ROM change or new RAM region is needed for this checkpoint.

| Component | Bytes |
| --- | ---: |
| Browser/transport/admission/refresh code |2996|
| Retained SDS helpers |831|
| Resources/status/signature |739|
| Seven32-byte filenames |224|
| Context |92|
| Disk options label table |100|
| **Named total / region** |**4982 /8002**|

**3020 bytes remain**, split3/3004/13. **3004 bytes directly follow code**, compared with68 previously. Exact rebuilding, decoded instruction targets, patch separation and immutable original firmware hashes pass. This closes the immediate space-recovery checkpoint; unfinished features still need a complete linked fit measurement.

## Acceptance and tradeoff

The old whole-catalog build fails the new page-buffer assertion as expected. Nine native workflows pass on the same new hash:

- All100 full32-byte names are checked through15 pages forward and back. A second trip to page98 followed by a generated100-to1 catalog shrink resets the origin to0. There are44 complete D7 transfers in this test.
- Empty, one-entry and100-entry catalogs work; the generated101-entry fixture returns an error. Every adjacent static resource header and code span stays intact.
- A failed Next refresh returns to collections, offers no stale image action, sends no D8 and recovers on explicit retry.
- Listing/switch cancellation, actual index99 selection, native13-sample Load/playback and retained SDS cancel/retry/publication remain exact.
- Browser ISO -> separate private HD0 initialization/Save/export -> fresh cold Load preserves119808 exact sample bytes and matching playback peak.
- Silent mount-open failure remains bounded, with same-/other-target retry and exact native loading.
- Remote Mode during mount/readiness prevents native drive/Load commitment and recovers after session exit.
- All128 realtime MIDI clocks arrive during D7; the saved IRQ context and measured idle-clock adjustment pass.
- An SDS header during a Next refresh drains4000 bytes, then shows Busy; native receive ownership blocks image clicks and CANCEL rolls back safely. Its new window registers (FIRST7/end14) restore across IRQ service.

The instruction-decoded index checker passes25700 cases; the new window predicate passes all10000 origin/index pairs and retains at most224 bytes. These model results do not substitute for malformed-index wire fault acceptance.

Paging now adds one full catalog read per change. Across43 observed100-entry rereads, DA-completion to D7-completion takes348.279..351.715ms, median349.998ms. This excludes other command/UI time and is an emulator measurement, not a hardware timing guarantee. The library cap remains100 images per folder, and stock target-folder constraints are unchanged.

Both IRQ runs contain188 matched service pairs. All34 ordinary scratch words, bank/mask/SP state and the exact RW38 service-time adjustment match. The SDS-header case observes194 bytes below callback entry, versus192 in the clock run; neither is a worst-case stack bound. The caller-local callback frame remains80 bytes. No ISR SCSI-controller write is observed in these runs; physical routing remains unqualified.

## Remaining fit work

The linked footprint above includes current browser, native Disk access, transport/discovery, existing cancellation/recovery, ownership, GB-6 v9 and retained SDS fixes. The following costs are still unmeasured and must be included before full-fit GO:

- Owned footer/help/image identity and LCD/RC-100/other-controller behavior.
- Completed filename/preflight/error policy; host-side tooling is separate from OS bytes.
- Any repairs required by general native-operation, geometry/cache/stereo/reset/Save System qualification.
- Complete native caller/ISR and stack-lifetime proof; the stack is outside this8002-byte code/data region and is not covered by its remaining bytes.

The next work can use the recovered3004-byte contiguous area. A second RAM-region search is deferred unless the complete implementation later requires it. Physical qualification, arbitrary-folder protocol limitations and unfinished IM1 gates are not solved by memory savings. The403 shared fixture files remain unchanged; shrink/overflow tests mutate only their own generated copies. No runtime/emulator source changed; the earlier748-test backend baseline was not rerun.

Candidate SHA-256 `512e34680767ffd3cae8dbca67aa77f3528cb62bf5ad44880ade581b90c759a2`; existing selectable boot ROM `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb`. [Validation](../condensed/validation/bluescsi-im1-page-window-2026-10-19.json). [Active roadmap](bluescsi-image-mount-plan.md).
