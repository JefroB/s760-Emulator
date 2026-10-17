# IC15 SCSI boot transport qualification

The original boot ROM now passes its command-phase transfer wait in the native model. BUG-080 is fixed; SCSI payload boot still stalls at the separate DMA dependency BUG-082. Original firmware and library media remain unchanged.

## Independently supported command transfer

[NetBSD's controller definitions](https://ftp.netbsd.org/pub/NetBSD/NetBSD-release-10/src/sys/dev/ic/mb89352reg.h) identify SSTS80 as initiator,20 as busy and10 as transfer active. SCMD84 selects program transfer. Its [controller driver](https://ftp.netbsd.org/pub/NetBSD/NetBSD-release-10/src/sys/dev/ic/mb89352.c) provides an independent software reference. The local original MAME mb87030 engine sets busy/active for a connected transfer before processing the phase and count, without restricting these bits to DATA phases. This supports the ROM'sB0 high-nibble wait during COMMAND.

The S-760 model formerly excluded COMMAND from active status and omitted counter consumption on CDB writes. The repair includes COMMAND in the existing active-state condition, decrements its programmed count and raises transfer completion when that count reaches zero. That event remains distinct from a target finishing its SCSI command. Manual ACK transfers and the legacy flat profile retain their existing behavior.

[Ordinary menu-selected native execution](../../condensed/validation/ic15-native-scsi-command-contract-2026-10-16.json) now sends CDBs, transfers the header and performs status/message ACK handshakes. The original HD fixture has an incompatible header and returns to the ROM failure path. A new native test uses original firmware, fresh private state and Mode/Panel Up/S2/Exit inputs. It independently observes nine active waits and nine completed transfers with all three SPC counter bytes zero. It does not force guest registers, PC, RAM or bus values.

## Payload DMA remains unresolved

[A private synthetic fixture](../../condensed/validation/ic15-native-scsi-valid-header-2026-10-16.json) has header0000000053373730204D523235410040 and copies the unchanged OS payload toLBA4, plus a duplicate tail atLBA15AC for the split-loader variant. This is a deliberately constructed loader probe, not a claim about real Roland HD media formatting.

It passes the header gate and reaches control47 at post-instructionPC269D with IC4 count0000 and SPC count080000. Execution remains269D through30 emulated seconds, with no handoff. Native control47 requires a nonzero16-bit count; the base native interrupt routing also connects only FDC. ROM261C enables0115=10, starts the DMA and waits forRB3 bit0 before checking SPC completion. The structural0130→02E0 stub sets that bit, but initial CPU vector words do not point to0130. Merely raising the current CPU external interrupt would enter the FDC vector and would not establish this DMA path.

Service Notes printed page18 visually establishes IC25 MB89352PFQ INT(pin36)→INT1, DACK(pin4)→XDACK0 and DREQ(pin3)→inverter IC6→XDREQ0. IC4 has externalINT0..3; the gate-array internal DMA interrupt/vector-selection behavior is not specified by these wires. The rendered crops, source PDF identity and coordinates are preserved in [transport validation](../../condensed/validation/ic15-scsi-transport-validation-2026-10-16.json). A universal zero-count rule, invented DMA interrupt or patched vector would exceed the evidence.

## Validation and remaining acceptance

Both native build stages pass. All452 Python tests pass, including the new ordinary-ROM counter/completion regression. The native runtime check passes boot frames, pointer movement, MIDI playback, note release and clean shutdown. Initial sandbox socket failures and a private screenshot-directory mismatch were corrected before acceptance; these are not firmware failures. Source and executable hashes, commands, test summaries and probe identities are retained in the validation JSON.

The next required contract is IC4 control47's full transfer extent and real DMA interrupt/vector/acknowledgment behavior. Wiring plus firmware identifies the dependency but does not supply that internal behavior. SCSI payload completion, physical parity, unresolved ROM bytes and assembler/rebuild acceptance remain open.
