# IM1: Exit repair, full CD and recovery qualification

Later same-day [compatibility results](bluescsi-im1-final-gates-results-2026-10-20.md) update the remaining-work list below. The user clarified that FDD and SCSI IMG are writable; the earlier all-library-read-only assumption is superseded. Historical case identities and results here remain unchanged.

2026-10-20. **BUG-165 and BUG-166 are fixed.** The combined browser/GB-6 v9/SDS candidate is now `6297274dd5c33b0b37409d3cddcd53e40b8af6140f2c416fc0213181cd3ba628`. It uses **6,452/8,002 resident bytes**, leaving **1,550 free**, including **1,332 immediately after the browser code**. No additional Boot ROM patch or memory region was needed.

IM1 remains open for the complete native caller/interrupt/resource-ownership contract and broader conflicting-operation/reset coverage. The results below close specific checks; they are not a worst-case stack proof or physical BlueSCSI qualification.

## Completed checks

| Check | Result |
| --- | --- |
| Nested Exit, BUG-165 | Native redraw event `0B` replaces the extra close/open sequence. Mouse System preserves depth `3 → 4 → 3` and ancestor `8120`; System is highlighted correctly. GB-6 completes **26 cycles across 13 screens**, preserving every active ancestor entry, code, PCM and final playback. |
| LCD confirmation and navigation | Full 32-byte names with shared prefixes; preview, Back and held activation issue no mount. Explicit index1 loads 119,808 exact bytes and plays/releases. All four collection identities, Back/reopen and HD2 IMG loading pass. |
| LCD errors | Ordinary-target refusal, silent D8 open failure, four bounded TUR/sense attempts, no native handoff, then independent-target recovery with exact B samples/playback. |
| Full-size CD, BUG-166 | The opt-in emulator fixture's 64MiB cap prevented full-CD testing. Its ceiling is now 1GiB. A 67,110,912-byte image passes capacity and first/last-sector checks; over-ceiling and unaligned media remain rejected. This is a fixture ceiling, not a sampler or BlueSCSI limit. |
| Genuine Roland CD | Browser mounts the complete **606,709,760-byte JMD CD**. Native Load imports its first K4 performance: **79 exact sample allocations, 6,054,912 bytes**, with four notes on two MIDI channels and silent release. Original and private source images remain unchanged. |
| Cold checkpoint | A fresh emulator process loads A, restores an earlier B-ready checkpoint, refuses stale Load with zero allocations, then explicitly selects/loads B: 119,808 exact bytes and playback. |
| Active checkpoint | Pause during D7 after 1,200 bytes using the ordinary emulator pause API. **Three restores** drain the cached transaction, issue no automatic D8, and allow explicit index99/B selection and exact Load/playback. Host catalog remains unchanged in this test. |
| MIDI and receive ownership | 128 clock bytes serviced during D7; 188 matched service pairs preserve scratch words, selectors, masks and stack pointer. Incoming SDS during list and mount blocks publication/native Load. Cancel, explicit retry, exact Load and playback pass. |
| Remote Mode ownership | Genuine manufacturer41 requests during listing and mounting produce Busy and prevent native drive/Load commit. Cancellation releases ownership and fresh enumeration succeeds. |
| Cancellation and retained SDS | D7 Exit drains 4,000 bytes; interrupted D8 starts no follow-on command/Load. Explicit index99 retry loads 119,808 exact bytes. Retained SDS cancellation/retry preserves those samples and publishes 160 exact new bytes. |
| Resident lifetime | **366 snapshots** preserve all **7,360 immutable/gap bytes** of the 8,002-byte region. Only the documented 642 mutable bytes are excluded. This checks more than code alone, including constant resources and unused gaps. |
| Stack analysis | All custom conditional paths and direct calls balance. Maximum custom contribution is **166 bytes**, including the common 80-byte frame. Native callees and IRQs are excluded. The parent workflow observes SP no lower than `1048` against `1120` initial SP: 216 bytes used. MIDI service observes 192 bytes below callback entry. These are different reference points, not a universal bound. |
| Build and regression | Exact firmware rebuild, instruction/branch boundaries, disjoint GB-6/SDS patches and unchanged golden inputs pass. Rebuilt emulator: **769 backend tests passed**, no failures/skips; ordinary fixture-disabled native menu and three Disk/Load voice-restriction trials pass. |

The Exit fix saves 35 code bytes. Native event02 uses the recursive close path at `0000:D383`; it can consume a mode2 ancestor. Event0B instead calls `D297`/`DA9A` after the popup has closed, refreshing a mode0 parent with one-level pop/reopen. The ordinary Disk handoff flag still suppresses this parent refresh. The fix changes no native menu dispatcher or GB-6 decoder.

[Correct System return](../condensed/validation/bluescsi-im1-closeout-system-return-2026-10-20.png).

## Identities and reproduction

| Artifact | SHA-256 |
| --- | --- |
| Combined OS | `6297274dd5c33b0b37409d3cddcd53e40b8af6140f2c416fc0213181cd3ba628` |
| Retained selectable GB-6 Boot ROM | `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb` |
| Rebuilt native emulator | `5720c78bdc2e129d7f2264b524b86ab914a3c109cf86194a5131484952399540` |
| Earlier emulator used before the fixture change | `1188bff3c3d125dec93b25c3776681ddccd4cdf8a799784fabab8e5e67f055b5` |

The validation records which emulator each workflow used. Parent, cold-checkpoint, LCD-error and initial IRQ checks used the earlier executable. Full-CD, active-checkpoint, final cancellation/LCD/IMG/Remote Mode/mount-race checks used the rebuilt executable. Do not relabel earlier runs as tests of the later executable. Both use the same repaired OS bytes.

Private reproducible builders, observers, native scripts and results are retained under the Codex work directory `bluescsi-im1-closeout-2026-10-20`. The durable validation contains the builders/auditor sources, instruction records, commands, identities and accepted results. Native acceptance uses physical input, MIDI and normal checkpoint/pause APIs; observers do not force guest RAM, registers or PC. The six SPC fixture tests are explicitly synthetic and remain separate from native firmware acceptance.

Excluded exploratory runs: an unsupported Lua stop callback, the expected old-executable large-CD failure, a mount-retry fixture with a placeholder at index99, and a Remote Mode probe that armed before entering the image list. The accepted runs correct their setup and assert the relevant preconditions.

## Remaining decision work

1. Bound the **combined native caller/callee/ISR stack and maximum service time**, and resolve remaining indirect native aliases. The 166-byte custom bound and observed low-water marks cannot close that requirement alone.
2. Finish the **conflicting native Disk operation and reset contract**, including attempts during active native operations, repeated external faults, and D8/reset outcomes. Idle cold recall and active D7 replay are now complete for their named fixture cases; they do not establish physical reset behavior or a changed host catalog.
3. Preserve the explicit compatibility backlog: populated Volume Dump FD, fragmented Optimize, Copy overwrite Yes/No, additional Roland stereo/media geometries and final-image persistence/controller coverage where only predecessor evidence exists. No new algorithm or extra memory is implied by these tests.
4. Physical qualification remains separate: installed BlueSCSI build/configuration, available IDs, actual CD1/CD2/CD3/CD6 library, writable IMG/protected ISO behavior and hardware timing. RC-100 input testing remains waived by the user; compatibility is assumed, not verified.

The concrete stock layout remains **300 ISOs plus 100 IMGs across four target folders**, subject to available IDs. It is not arbitrary folder switching on one target. There is no measured code-space blocker; the remaining feasibility blocker is the native safety contract above. **A full IM1 GO is not yet claimed.**

[Validation](../condensed/validation/bluescsi-im1-closeout-2026-10-20.json). [Active roadmap](bluescsi-image-mount-plan.md).
