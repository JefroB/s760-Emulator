# IM1 LCD error and cancellation recovery

2026-10-20. Candidate `19448d85773dd99081a45cdc33ca7defd82f4a4bd3b9cb28a2b533676d68a45c` is unchanged. These native Panel+LCD workflows exercise failures through real panel inputs, with read-only observations and private fixtures. No guest RAM/register/PC forcing is used.

## Error handling

An ordinary target without Toolbox discovery is refused with error9 before any Toolbox command. A zero-length image reproduces the modeled stock D8 GOOD/backing-open failure: exactly four bounded Test Unit Ready/Request Sense pairs follow, then the browser returns to Collections with error9 and mount uncertainty. There is no native Load handoff, no allocation and no selected-drive change. Explicit selection from independent target3 then reaches native LCD Load,13 allocations and119808 exact expectedB sample bytes; playback/release passes.

The zero-length fixture is intentionally outside the supported preflight profile. This qualifies the browser's response to the modeled failure, not physical parity of every switch failure or a new supported image type.

## Cancellation

A physical Exit during the100-entry D7 transfer cancels after draining all4000 bytes. No D8 or native Load follows. A fresh catalog/preview is then opened. Exit during D8 leaves a visible uncertainty state with no follow-on commands, no native handoff and no allocation. The mounted backing may have changed; there is no rollback claim. A fresh explicit selection succeeds, loading13 allocations and119808 exact expectedB bytes and passing playback/release.

## Scope and fit

All private fixtures remain byte-exact, as do the original firmware inputs. Firmware allocation remains6487/8002 bytes,1515 free/1297 contiguous after code. No new firmware or boot-ROM change is needed; GB-6 v9 remains linked. Full IM1 GO remains open: current-hash LCD Save System/cold-state, native Disk-operation execution, RC-100, broader ownership/reset/checkpoint/stack and physical BlueSCSI configuration/timing remain to be qualified.

[Validation](../condensed/validation/bluescsi-im1-lcd-recovery-2026-10-20.json).
