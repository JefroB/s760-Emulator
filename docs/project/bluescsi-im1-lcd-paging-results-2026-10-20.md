# IM1 LCD paging and boundary recovery

2026-10-20. Native Panel+LCD acceptance checks all100 full32-byte catalog names across15 seven-name pages, forward and backward, and returns to Collections without a mount. Fixture files remain byte-exact. Physical panel inputs drive the test; RAM snapshots and Lua taps are read-only.

BUG-164 was reproduced on prior candidate `efec015fa431f571b6bcb685d0ab0d20eb6de940d227cd40409fbd34a4f09996`: on the final page FIRST98/COUNT100, selecting disabled Next changes SCROLL2 to0 without redraw. Immediately selecting the visible Previous leaves FIRST98 instead of91. The old broad paging test recovered by scrolling down again, so its success alone did not cover this sequence.

The fix moves the existing scroll reset from action entry to render. Ignored actions preserve the displayed window; successful page/confirmation transitions still reset it when rendering. Candidate `19448d85773dd99081a45cdc33ca7defd82f4a4bd3b9cb28a2b533676d68a45c` adds no bytes:3951 code,6487/8002 total,1515 free/1297 code-adjacent. Mandatory GB-6 v9 and retained SDS patches remain linked; the selectable boot ROM is unchanged.

Native acceptance and exact rebuild results are recorded in the accompanying validation. Complete LCD collection/IMG/Disk/error/cancellation/cold-state qualification, RC-100, broader ownership/reset/stack and physical BlueSCSI configuration/timing gates remain open. This is not a full IM1 GO.

On the corrected hash, disabled Next preserves SCROLL2; immediate Previous reaches FIRST91. Full-name/shared-prefix confirmation, Back/held-key no-mount, explicit index1 exact119808-byte native Load/playback pass. Same-hash GB-6 CRT D7 drain cancellation, uncertain D8/no automatic handoff, explicit index99 retry/exact Load/playback and SDS cancel/retry/publication160 exact bytes pass. Exact rebuild, branch targets, nonoverlap and immutable originals pass.

[Validation](../condensed/validation/bluescsi-im1-lcd-paging-2026-10-20.json).
