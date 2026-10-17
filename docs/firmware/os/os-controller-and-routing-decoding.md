# Controller assignment, registered parameters and routing refresh

This pass explains more of the resident OS beyond message dispatch. Addresses are bank-qualified CPU addresses; data addresses must use their data selector, not the instruction page. Claims below are static code evidence, not new hardware acceptance.

## Assigned controller processing

000F:2ACB computes `33 * channel` and scans bytes at data address 8D56 plus that offset until FF. For each entry it visits 24 voice positions and compares the entry against each voice's field at 804D. Matching voices call 2AEE. This establishes a channel-to-assignment list with a 33-byte stride; it does not prove every list is populated or correctly terminated at runtime.

2AEE selects performance/context data through 02FA or 0356, then selects assignment data page 030A or 031A. At 2B3F it compares the received controller number R76 against configured byte 40F0. A match records the controller number/value at 9006/8FE6 plus assignment index and invokes 2B57.

2B57 performs a nonlinear calculation using signed amount 40F2 and writes the result at per-voice 8814. The nonzero-value path applies additional signed amounts:

| Parameter offset | Destination base | Arithmetic visible in code |
| --- | --- | --- |
| 40F1 | 8724 | Signed multiply, double, then signed-high-byte adjustment |
| 40F3 | 8844 | Signed multiply and double |
| 40F5 | 8754 | Signed multiply and double |
| 40F6 | 8784 | Signed multiply and shift left two |
| 40F7 | 87B4 | Signed multiply and double |
| 40FC | 87E4 | Signed multiply and double |
| 40F4 | 8BD5 | Signed multiply, shift left two, store high byte |

The destination bases are offsets used by these particular indexed instructions. They must not be equated blindly with similarly numbered fields indexed by a different voice convention. User-facing names for all destinations remain unqualified. A zero controller value clears these destinations, but the 8814 nonlinear calculation runs before that zero-value branch. An additional mode-dependent branch updates 89C5/8994.

## Registered-parameter state

The fixed controller handlers maintain per-channel state:

| Address base | Observed role |
| --- | --- |
| 91DB / 91EB | Low/high parameter-selection bytes, written by CC100/101 |
| 91AB / 91BB | Flags indicating the selection bytes have been received |
| 91CB | Selection/data-entry state bits |
| 91FB / 920B | Low/high data-entry bytes, written by CC38/6 |

Once both selection flags are present, either selection handler writes state 1 to 91CB. CC98/99 clear bit 0 while preserving bits 1/2 (`state &= 6`); this disables the registered-parameter data-entry path. CC6/38 do nothing in this fixed path unless bit 0 is set. They store their byte, set bit 2/1 respectively, and invoke 2E2D once the counterpart's received bit is present. This does not prove that every transaction requires fresh data bytes: the flags' initialization and all other writers still need auditing.

2E2D recognizes selection word 0 or 1; other values return. Selection 0 applies the high data-entry byte, capped at 48, to assignment fields 40E0/40E1 for entries in the channel list. Selection 1 first checks the configured channel, derives a value from both data-entry bytes, clamps it to 78..178 before subtracting 128, and stores the resulting signed byte to page 0299:8F97. It sets bit 4 in RW9E. The selection-zero path sets bit 5 in RW9E when its list ends. Musical units and end-to-end behavior remain to be verified; these are the firmware operations behind the parameter paths.

## Routing refresh callees

The calls from resident 2567/256A/256D target B299/B247/B489. They are now decoded under **instruction page 002D**, which is established for the timer service. Other calling contexts still need their own bank evidence.

- **B247:** saves/restores data selector 010C, reads page 0299:8FB9, indexes a word table on page 02A6 at 84C0, then performs eight DC00/DC02/DC06 transactions. Tags come from page 02A6:84B8 and are ORed with 0200.
- **B489:** reads page 0299:8FC7, indexes page 02BE:B23C, then performs two transactions using tags at page 02A6:856C. It also saves/restores 010C.
- **B299:** branches on page 0299:8F98, sets helper pointers, and invokes a loop processing IDs 0..7 followed by 16..23. More detailed routing interpretation remains open.

The existing [hardware map](../../condensed/01-hardware-and-memory-map.md) identifies DC00/DC06 as the pan-command aperture. These routines connect the resident refresh calls to that known aperture; they do not newly establish the hardware meaning of tag bit 9. Different data-page selections and table lengths are retained explicitly rather than treated as one flat table.

The bounded tag tables in the original image contain `BC 5D BD 5E 1D 7E 1E 7F` at data page 02A6:84B8 and `76 7A` at 02A6:856C. Their eight/two lengths come from the decoded loop bounds. These are initial image values; runtime immutability is not yet proved. The coefficient tables indexed by configuration values remain only partially bounded and are not declared fully decoded.

## Verification and next work

The broader manifest adds the B247/B299/B489 entries, with 195 instructions decoded without warnings. It includes the conditional caller links. The [validation record](../../condensed/validation/os-controller-routing-2026-10-16.json) checks instruction anchors for list traversal, state flags, limits, loop bounds and selector handling against the original image.

Next: identify all writers of the parameter-state flags; connect assignment destinations to their consumers; characterize the routing tables and branch modes; and establish bank mappings for system-message paths. No OS, ROM, native MIDI or audio behavior was modified.


## Initialization follow-up

Startup0000:C371/C375/C37A selects fetch001F and calls4F7F, and C380/C384/C389 repeats the call with a different R9D. Recursive decoding reaches5046, which saves data selectors010A/010C and selects page02BE. Three pointer-driven loops at5102..5127 zero exactly16 bytes each:91AB..91BA,91BB..91CA,91CB..91DA. This establishes a reset writer for both selection-byte receipt flags and the selection/data-entry state across all16 channels. The routine restores both data selectors before returning.

4F8D compares requestedR9D with state1BA5. An equal value returns without this reset; a changed zero value takes4FC5, while a changed nonzero value eventually takes502A/5046 after mode-dependent setup. Thus this is not evidence that every controller selection or every call resets the flags. No direct reset of selection values91DB/91EB or data-entry values91FB/920B occurs in these three loops; state zero gates their interpretation.

The two selection handlers explicitly replace91CB with1 once both receipt flags are set, clearing the prior data-entry receipt bits. CC6/38 then set their corresponding bits. Whole-image indirect writers and native sequences remain unqualified. [Reset evidence](../../condensed/validation/os-parameter-reset-2026-10-16.json) retains146 decoded instructions and original bytes.


## SCSI controller-state save/restore pair

001F:4F28 and4F5E are now caller-qualified from166:8BA6/8D90 through exact LD/ST0102/LCALL triples. The first savesR9D at1BA7 and data010C, selects0299, and tests8F9C. Zero invokes known4F7F throughCE14 withR9D=0; nonzero storesFF at1BA7. It restores010C on declared return paths.4F5E skips reset when saved1BA7 isFF, otherwise calls4F7F with the savedR9D; finally it invalidates1BA7 toFF. These are static conditional controller-reset contracts; caller-suppliedR9D meaning and arbitrary interrupt effects remain qualified. [Original bytes and links](../../condensed/validation/os-controller-session-pair-2026-10-16.json).
