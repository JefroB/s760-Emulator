# IM1 native callback ancestry: named CRT routes

The current image's normal CRT/GB-6 browser routes now have matched native
stack traces and audited call-frame explanations. A fresh run records **15,309
callbacks**, all returning with their stack restored and none nested inside
another callback. This closes the named-route ancestry checkpoint; complete
ancestry across additional modal/LCD paths and IRQ nesting/state remains open.

The OS is unchanged at SHA256
`e78750c233cc77faad9f2b6751fc9eddff9296beabfa17650297f3b5c63b0a35`.
MAME remains
`a42d26f755d2d902ac1adb79b76c60b3373be167e849c35ad09a568691bfa937`.
GB-6 v9, the boot ROM and the 6736/8002-byte allocation are unchanged. Original
OS/boot hashes and test inputs remain exact.

[Self-contained validation](../condensed/validation/bluescsi-im1-ancestry-2026-10-21.json)
contains the compressed raw JSONL trace, native identities, decoded call sites,
frame/return checks and observer/runner/audit sources. The preceding
[synchronous stack result](bluescsi-im1-current-stack-results-2026-10-21.md)
supplies the closed native and IRQ graphs, pinned by its evidence SHA256.

## Native acceptance

Physical pointer/button input drives cold boot, opening Image Library, ISO
listing, Next/Previous, panel Exit, reopening, Disk options and the native Disk
Load handoff. Screens were inspected, including the final native Load screen.
No guest memory/register/PC writes are used. Read-only SP taps record each
callback's entry stack and minimum SP through its final POPA.

| Callback | Count | Bytes already used from initial SP1120 at callback entry |
| :-- | --: | --: |
| Initialize | 2 | 62 |
| Update | 15300 | 28 |
| Action | 5 | 30 |
| Exit | 2 | 62 |

All 15,309 traces match the expected saved-frame offsets and native/synthetic
return words. Every initial PUSHA subtracts four bytes; every final POPA at
`000F:947D` restores the entry SP. The observed total low-water depth is
248 bytes. That observation is not a worst-case bound.

## Audited ancestry

Resident calls use fetch page0000; file offsets are
`4800 + (logical_pc & 3FFF)`. Each CDC6 far wrapper contributes 16 bytes,
including its incoming return word; the callback dispatcher contributes 12.

| Named route | Outstanding native call chain | Prefix bytes |
| :-- | :-- | --: |
| Main update | C81C -> CDC6 -> DD77 dispatcher | 16+12 = 28 |
| Main action | C811 -> DE9C; E0ED -> CDC6 -> DE4E dispatcher | 2+16+12 = 30 |
| CRT open | C807 -> F468; F4B7 -> CDC6 -> CF5A; CF72 -> CDC6 -> CF82; CFEA -> CDC6 -> DD1C dispatcher | 2+48+12 = 62 |
| CRT exit | C807 -> F468; F4ED -> CDC6 -> D383; D38B -> CDC6 -> D3AB; D3DB -> CDC6 -> DDB2 dispatcher | 2+48+12 = 62 |

Temporary pushes made before these call sites have already been popped; the
recorded native stack confirms the live frame words. Retry instructions at
CF7F and D3A8 are SJMPs back to CF5A/D383. Repeating these loops does not itself
accumulate call frames.

The current synchronous native graph has no indirect branches and does not
reach the resident callback dispatchers. The declared-domain IRQ graph also
reaches neither those dispatchers nor the browser callbacks. The browser's
decoded calls/jumps do not target its callback entry prologues. Its LCD update
can jump directly into the action body using the existing frame; that is not
another callback entry. Event helpers queue changes rather than invoking the
UI dispatcher in their call graph. These checks establish no synchronous
browser self-reentry under the closed-graph, normal return/selector restoration
and declared jump-table assumptions. They do not cover corrupted native
function pointers or arbitrary new interrupt owners.

## Remaining scope

Additional modal/LCD/screen-transition entry routes still require equivalent
ancestry qualification. Full IRQ priority/nesting and mutable-state invariants,
indirect alias/DMA ownership, remaining recovery phases and physical BlueSCSI
qualification remain open. This run does not add Load/audio acceptance or a
fresh backend-suite result.

The initial sandbox run could not connect runtime MIDI. An early observer
incorrectly subtracted one from CURPC and observed PUSH after PUSHA; it was
rejected and corrected against the CPU implementation. The next run passed
collection routes but missed the Disk options click. Only the final V4 run is
used for the combined acceptance above. These were observer/input-harness
corrections; no firmware change was made.
