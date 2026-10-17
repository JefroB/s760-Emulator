# System-message parsing and transfer dispatch

Resident F0/data/F7 paths now connect to instruction page 001F:5E64/5EB2/5F62 under the timer-service fetch context. The added region recursively decodes 1,874 instructions, including transfer helpers reached through dispatch tables. Names and protocol meanings below are limited to what the bytes support; complete protocol or hardware acceptance is not claimed.

## Initialization and header paths

5E64 reads the receive-enable field at data page 0299:8F9B, restores data page 02BE, and checks another gate at 2964. Accepted initialization sets parser class 7, clears command/header/checksum fields B048/B04E/B04C, sets B04A to FF, and initializes the receive pointer B034 to B04F. Rejected initialization selects parser class 8.

The normal header dispatch has four short-jump stubs:

| Header index | Entry | Check/action |
| --- | --- | --- |
| 0 | 5F13 | Accept 41, or select a separate path on 7E; reject other values |
| 1 | 5F31 | Compare byte to configured device byte at page 0299:8F9A |
| 2 | 5F4F | Require model byte 34 |
| 3 | 5F56 | Store command at B048, reset checksum accumulator |

Subsequent normal-path data bytes are written through B034 with a bound comparison against B157. The byte is added into accumulator B04C. F7 handling checks `(B04C & 0x7F) == 0` before selecting a command handler. Failed checks can route to 6950 and the error/status path. This is the observed additive validation rule; it is not proof that all transfer types share it.

## Command dispatch

The command low nibble is multiplied by four. A comparison with 40 selects base 5FB0 or 5FF0, giving two sixteen-entry jump-stub tables. Meaningful destinations in the lower table are nibble 1 → 6049 and nibble 2 → 6261; the others lead to 6030. In the upper table, nibbles 0/1/2/3/5/E/F lead to 668E/66B5/6794/67D0/67FE/6823/683E; remaining entries lead to 6030.

This does not establish that every high-nibble alias is a valid protocol command. The firmware's earlier state checks, operation gates and handler-specific length/address checks must be considered before assigning command names. 6030 resets parser state through 6038; it is not a successful generic implementation of those commands.

## Separate 7E path

Header byte 7E sets B04A=10. Subsequent bytes route through 6C76 and F7 through 6CDD. This path has its own device check, receive-buffer handling and XOR operations in the header processing. It must not be collapsed into the normal additive-checksum path.

6CDD searches data page 02BE:B158 until FF, then dispatches by matched table index. Initial image bytes are `01 02 03 7C 7D 7E 7F FF`; seven short-jump stubs map to:

| Lookup byte | Entry |
| --- | --- |
| 01 | 6D10 |
| 02 | 6D35 |
| 03 | 6D81 |
| 7C | 6D8E |
| 7D | 6D8F |
| 7E | 6DA3 |
| 7F | 6DD5 |

Following these entries expands into packet/transfer helpers through the 74xx area. Their detailed operation names, lengths and acknowledgment rules remain under analysis. The lookup table is established from initial image data and the referencing instructions; runtime immutability is not proved.

## Remaining boundaries

The region still has thirteen unresolved edges: three indirect dispatch unknown-value edges, a call to 4F05, a call to resident 2553, and seven calls to F874/F8A6. The code at 6965 changes fetch selector 0104 and restores it at 696F, so bank context must remain explicit. There were no detected direct writes to its own fetch selector 0102 in this decoded region; this is not a full proof against indirect stores or callee effects.

Searching the currently decoded instruction set found no additional explicit accesses to parameter-state bases 91AB/91BB/91CB beyond the resident controller routines. This does not close the state-writer question: bulk clears, indirect writes and unclassified regions can still initialize or modify those fields.

The [validation record](../../condensed/validation/os-system-message-decoding-2026-10-16.json) contains the checked header/checksum anchors, jump destinations, lookup-table identity and input/tool hashes. This pass changes analysis metadata only; original firmware and emulator behavior remain unchanged.
