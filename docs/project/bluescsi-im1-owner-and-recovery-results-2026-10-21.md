# IM1 ownership repair, native gate batch and hardware-test handoff

**BUG-176 is fixed** in the final experimental OS image. Sixteen native
workflows pass, including the ten retained performance-policy regressions,
CRT/LCD ancestry, interrupt tracing and three genuinely incomplete-write resets.
The rebuilt emulator passes **1123 backend tests, 3 skipped**. IM1 remains open
for broader native-state/alias proofs, other fault models and physical testing.

The [hardware-test guide](bluescsi-hardware-test-guide.md) identifies the local OS
image and exact SD layout. This is readiness for controlled hardware testing,
not a release qualification or a claim that the entire feasibility gate closed.

## Exact artifacts

| Artifact | SHA256 |
| :-- | :-- |
| Final OS, 1,474,560 bytes | `606e277e5f11a4ca1b59dadaf4e9a8395e6c8eed1e3674b4efa78bf3bf1767e4` |
| Retained selectable boot ROM | `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb` |
| Rebuilt native emulator | `ca9ecc94a5340d41c965fca1c5f529b98dac0ef8782ba4e8e43d9b2d49dfd84c` |

Fresh-source builds reproduce both firmware artifacts byte-for-byte. Original
OS/ROM hashes are unchanged. GB-6 **v9** X4/Y4, SDS repairs, Verify Medium and
warning text repairs remain. No further ROM burn is required for this handoff.
Allocation is **6760/8002 bytes, 1242 free**. Main browser code is 4135 bytes at
physical4080..50A6; the existing parser helper remains at5100..5158.

[Self-contained evidence](../condensed/validation/bluescsi-im1-owner-and-recovery-2026-10-21.json)
contains raw compressed timer, callback and IRQ rows, decoded graphs, ownership
counterexamples/repair proof, build identities, runner sources and backend log.

## Transition ownership repair

The previous e78750c2... image checked2BBA/1FA4 before suspending performance.
Suspension temporarily enables timer/MIDI interrupts while cached1BA5 can still
be nonzero before native4F99. Restoration has a corresponding window after
4FBE restores1BA5 and before the browser masks interrupts again. A queued parser
request can acquire SDS/Remote Mode ownership during either window. Neither
performance transition clears those owner bytes.

The final patch adds **three masked owner rechecks**: after suspension, after
restoration before native Disk-menu dispatch, and after restoration before
publishing the mount/Load handoff. A newly acquired owner routes to Busy without
another SCSI command or native handoff. The existing common exit releases any
performance lease. This adds24 bytes and keeps the synchronous maximum166.

The actual decoded admission helper rejects all510 cases in which either owner
byte becomes1..255. A control-flow check covers these outcomes at all four
transition returns: **2040 combinations**. The predecessor has bypass paths;
the final image has none. This is an instruction/control-flow race proof, not a
claim that the narrow original race was timed in native execution or hardware.
The preliminary single-recheck candidate is superseded by the final repair.

## Native timing and retained behavior

All ten final-image production cases/101 RAM snapshots pass: dense MIDI,
CRT/LCD cancellation and explicit retry, full-name confirmation, first/last D7
stall with simultaneous MIDI, busy/idle SDS and Remote Mode, and native Load
with exact PCM/playback/release afterward. Staged image hashes and preserved
browser/parser/SDS code bytes are checked independently.

Across these cases, **9003 suspended-service pairs** preserve the saved context.
All **891942 elapsed samples across236 commands** match the guest accumulator
and raw timer/wall-time values. Maximum observed suspended service is0.428375ms;
these observations are not physical WCET measurements. Production retains its
32-wrap total deadline. The predecessor's separate one-wrap timeout experiment
remains historical diagnostic evidence; it was not rerun as this production OS.

## Ancestry and interrupt results

| Final-image workflow | Balanced callbacks | Observed total stack depth |
| :-- | --: | --: |
| CRT/GB-6 collections, paging, Exit, native Load handoff | 15387 | 248 bytes |
| LCD panel paging, confirmation/back, Exit, native Load handoff | 50345 | 198 bytes |
| CRT with MIDI and IRQ tracing | 15154 | 248 bytes |

No callback nests inside another; every final POPA restores entry SP. Entry
prefixes remain update28/action30/open62/exit62 bytes. The native call graphs
and callback composition again resolve54 contextual functions/1211 instructions
with synchronous maxima166/90/156/166 for action/exit/init/update.

The final trace balances2677 native IRQ entries/returns, including nine MIDI
interrupts inside the timer handler. Native handler targets are filtered before
tracking nesting; boot-ROM handlers are outside this census. Feature callback
entries in the trace use MASK0/MASK1=20/20.

For that mask profile, timer PUSHA clears both masks and CAE7 enables only
MASK1 bit5 (MIDI). The closed native timer/parser/control graph has no explicit
mask writers beyond balanced PUSHA/POPA. The receive handler never enables
interrupts. The CPU fetch/POPA implementation prevents another interrupt before
the first handler PUSHA or between final POPA and RET. This gives a conditional
IRQ contribution of **56 bytes**:14 timer/control entry +36 control callee +6
non-nesting MIDI. The parser path18+22+6 is smaller. The resulting named-route
conditional envelope is **62+166+56=284 bytes**.

This envelope assumes the stated masks, normal returns and declared native
jump-table domains. It does not reserve a stack region, prove every native
caller/state invariant, establish arbitrary interrupt ownership, or qualify
physical IRQ behavior. The observed low-water marks are not worst-case bounds.

## Mid-write reset recovery

An opt-in driver diagnostic, `S760_IMAGE_WRITE_RESET_AFTER`, interrupts the
first incomplete fixture WRITE DMA after a selected byte. It schedules an
emulator soft reset before the DMA completion counters are published. It is
disabled by default, scoped to the enabled image fixture and consumed once;
guest reset does not rearm it. The helper's admission/one-shot tests pass.

Three final-image cases interrupt a1024-byte native Initialize WRITE at bytes
**1, 511 and1023**, with1023/513/1 bytes remaining. Each unfinished buffered
command leaves the backing image exact. Reboot clears the browser's operation
state, permits no automatic Toolbox selection, and explicit remount/reinitialize
recovers to the same final image hash and empty filesystem counts in all cases.
A live render timestamp is excluded from the cleared-context comparison.
Boot-time ordinary SCSI activity is not misclassified as a browser selection.

The fixture persists complete WRITE commands, so discarding its incomplete
buffer is **not evidence of physical write atomicity**. These cases do not
establish rollback of a multi-command operation, partial-sector SD behavior,
power-loss safety or every SCSI failure phase.

The diagnostic-only driver change rebuilt successfully with serial MSBuild.
The final backend suite passes1123/3skip. A prior run's15 failures were missing
private harness directories, corrected before the passing rerun. Intermediate
observer/input setup errors and the preliminary ownership candidate are
excluded from final native acceptance.

## Remaining work

The source-level transition ownership gap and the named LCD/IRQ/mid-write
checkpoints above are closed. Complete indirect aliases/physical DMA ownership,
native state/caller invariants beyond the qualified routes/masks, broader target
faults and real media configuration remain open. The BlueSCSI is attached to the
user's S-760, so its SD card and physical behavior cannot be inspected here.
Follow the hardware guide for the first controlled test; do not perform a
physical write-interruption experiment based on this emulator result.
