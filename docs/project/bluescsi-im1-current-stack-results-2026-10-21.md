# IM1 current-image synchronous stack qualification

The current BUG-168 native-policy image has a freshly recomposed synchronous
stack maximum of **166 bytes from callback-entry SP**, including its 80-byte
common frame. This now includes the reused performance suspend/restore routine.
The complete native stack gate remains open for outer caller ancestry and IRQ
nesting/state invariants.

## Image and scope

- OS SHA256: `e78750c233cc77faad9f2b6751fc9eddff9296beabfa17650297f3b5c63b0a35`.
- No firmware or emulator code changed. Allocation remains 6736/8002 named bytes,
  with 1266 free; GB-6 v9 and the selectable boot ROM remain unchanged.
- This is static analysis of the accepted image. No fresh native emulator run,
  hardware test or backend-suite run is claimed.
- [Self-contained validation](../condensed/validation/bluescsi-im1-current-stack-2026-10-21.json)
  includes decoded bytes, call graphs, callback composition and analysis sources.

## Completed checks

The bank-aware synchronous graph now covers 11 native helper roots through
54 contextual functions and 1211 distinct page/address instructions. All native
function returns balance, all call edges resolve, and the decoded native bytes
match both the current image and original OS. A separate recurrence recomputes
the native root bounds. Address translation is
`file = 0x4800 + (fetch_selector << 10) + (logical_pc & 0x3fff)`.

The new root `001F:4F8D` is analyzed with fetch windows `000F/001F/000F/0000`,
matching the browser's retained window 2. Its eight-function closure needs at
most eight local stack bytes, excluding its incoming return word. The deepest
native chain is `4F8D -> 502A -> 5046`. The CE14 wrapper and browser call frames
bring this path to 112 bytes from callback-entry SP. No new synchronous peak is
introduced.

| Callback | Maximum bytes, including common frame |
| :-- | --: |
| Action | 166 |
| Exit | 90 |
| Initialize | 156 |
| Update | 166 |

Both branches of each conditional are explored in the custom graph. Internal
calls retain explicit return stacks; external calls include their native
callee bounds and audited far-wrapper overhead. All callback returns restore
the common-frame depth. The immediate native dispatcher frames are independently
rechecked on this image: each saves five words and a synthetic return, totaling
12 bytes **outside** the callback-entry bound.

The full active parser/control IRQ graph is also regenerated from the current
image: 152 functions, 9212 instructions and no unresolved graph edges under the
declared jump-table domains. Its control/parser local bounds remain 36/22 bytes.
The prior conditional 62-byte timer/control/wave contribution is retained only
under its interrupt-owner, nesting and state assumptions. The MIDI and wave
tails consume the four bytes saved by their external PUSHA wrappers; their
reported return delta of -4 is intentional and is not an ordinary callee return.

The full active graph remains relevant during performance transitions, even
though active SCSI commands use performance mode zero and skip parser/control
work. Mode-zero timing evidence from the BUG-168 report does not prove the
transition's full IRQ state invariants.

## Remaining gate

Do not label `166 + 12 + 62` a complete stack bound. Outer dispatchers and
recursive UI callbacks still need a bounded ancestry contract; interrupt
enable/priority/nesting and native mutable-state domains remain conditional.
Observed low-water marks do not replace those proofs. The initial native SP of
`1120` and the proposed 512-byte allowance are not evidence that every nested
route fits.

Indirect aliases/DMA ownership, other recovery phases and physical BlueSCSI
qualification remain separate open items. This result closes the new
suspend/restore synchronous-callee subgate without closing IM1.
