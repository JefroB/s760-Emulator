# Numeric propagation and the complete initial screen 012F field list

[Byte evidence](../../condensed/validation/os-postprocess-full-fields-2026-10-16.json) records the newly decoded instructions and exact initial field/tuple layout. These OS results are static. Native execution in this run qualifies only the separate boot-ROM panel-input path.

01D1:9ED0 tests bit `(index&7)` in the byte at `base+(index>>3)`, saving/restoring data010C and returning that bit in carry. The caller9FDF supplies base2BBC and iterates object indices0..FE, skipping the current RFD and all marked indices. Thus this invocation reads32 bytes2BBC..2BDB, excluding bit7 of the final byte. This is runtime RAM, not newly classified image data.

A036 resolves the current type4 object through004B:6B2E, saves its source data bank inRW32, then resolves the destination index through6A26. A086 temporarily restores the source bank for the read and restores the destination bank before writing. R34=FF copies the existing source byte; other values write the new byte supplied inRDB. Offsets10/20/30/40 perform a second byte operation, loading RWDA fromRWC8 so thatRDB contains its high byte. Other offsets write one byte.

A0A2 requires2347 bits7 and0. It exchanges offsets12..1A with22..2A and32..3A with42..4A, writes the paired selected-object byte, then invokes9FDF withR4A=FF to copy that value to eligible objects. Both routines restore savedRW48/RW4E and data010A. The closed local call chain has no directRWC8/RWCA writes; for bounded object offsets whose indirect stores remain in the128-byte object records, the value survives. Arbitrary offset aliases and interrupts remain unqualified. The helpers do not imply ordinary UI editing or audio acceptance.

The full initial012F list contains40 seven-byte records, terminated by the firstFF byte. Thirty-nine are type3 and one is type2. Advancing tuples by their observed widths gives238 bytes, rather than incorrectly treating all40 tuples as six bytes. Eight distinct metadata records provide eight display targets and four edit targets; unknown edges remain for other mutable states.

Metadata549A is function-specific: its editor81E2 replaces the generic loaded bounds with zero and `sign_extend16((word[2A2C]-1)&FFFF)`, reads/writes a word at the selected logical address, and uses the existing signed clamp helper. Therefore its trailing loaded words are not effective limits. The concrete tuple addresses logical00FE, also used asRWFE by the type5 selected-object resolver. Runtime count bounds and empty-count behavior have not been qualified by execution.

Metadata5D96 uses displayB31E/editB359 with limits0..95. Both add the unsigned byte23A8 to the tuple's parameter address. The display shows the bounded NUL stringOff for zero, otherwise formats a three-character numeric value through005A:5784.57E4 explicitly selectsdata010A=02DB before forwarding theOff text to the LCD/CRT NUL consumers. Only four text bytes are newly classified; array extent and the meaning of the23A8 selector remain unresolved.

Next: qualify writers/bounds of23A8 and2A2C, then exercise a concrete numeric field through ordinary native input. Continue other initial field/descriptor states without promoting this one screen into a universal schema.
