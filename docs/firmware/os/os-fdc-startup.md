# Floppy-controller startup closure

StartupC660/C664/C669 explicitly selects page005A and calls5C83. The199-instruction closure has no unresolved local outgoing edges and is included in the [panel/FDC evidence](../../condensed/validation/os-panel-fdc-startup-2026-10-16.json). This is static control-flow evidence, not a new floppy I/O acceptance test.

5C83 initializes cylinder/head/sector-related working bytesRCC/RCD/RCE/RCF to0/0/1/0. It writes36 to controller portE000, delays, and sends the three-byte command at data02CC:4504 throughE002 with readiness polling. It then issues controller commands5B and4F, consumes their response bytes, and repeats the command04/drive0 status operation until returned bit5 is set.

WhenRCF bit4 is set, the code seeks cylinder10 before recalibration. Seek5D96 sends0F, drive0 andRCC; recalibrate5C24 sends07 and drive0. Both clear1D0E, save the interrupt state and0115, set0115=11 and interrupt masks0/20, enable interrupts, and wait for1D0E. They then disable interrupts, restore0115 and the saved state, and execute bounded delay loops. Thus the wait depends on the interrupt-side producer, not merely a direct status-port transition.

Seek returns carry clear only for response byte1B6C=20. The final startup return checks the same byte's high two bits and clears carry only when they are zero. Local hardware readiness and interrupt waits have no timeout. This is not evidence of an emulator defect; reachability and interrupt behavior must be checked in ordinary native execution.

The three command bytes are classified only from their explicit read count and data mapping. Further work can connect the already decoded FDC ISR producer of1D0E, then extend into read/write/retry routines from justified callers. No controller commands were executed during this analysis.


The interrupt-side producer is now connected statically:0000:CD5D checksE000, issues08 toE002 when the masked status is80, reads result bytes into1B6C until the controller changes phase, waits for masked idle80, and writes1 to1D0E atCDBB. It restoresRW4A/RWDA and flags before returning. The result loop has no local buffer-length check; ordinary controller response lengths and native IRQ timing remain separate acceptance checks.
