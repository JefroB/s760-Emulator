# Front-panel LCD

The [service notes](../../Manuals/ROLAND_S-760_SERVICE_NOTES.pdf) identify an Epson SED1335 controller at IC72 and a 160-by-64-dot LCD. Consult the schematics and manufacturer controller documentation for electrical behavior.

The [native driver](../../mame-source/src/mame/roland/s760.cpp) routes LCD data writes through physical 103800 and command writes through 103802. With data selector 0400 these appear at logical F800 and F802. Read handling includes driver-specific status/data handshakes; do not infer read behavior solely by reversing the write-port labels.

Firmware programs the controller's display and memory parameters. A fixed 4 KiB two-plane layout and a universal internal font have not been established for the instrument. The previous E000/E001 LCD map was a bring-up error; E000 belongs to the FDC window in this bank context.

LCD output from the emulator demonstrates the implemented controller path. It does not independently prove every SED1335 command, external font configuration or physical LCD timing. Preserve programmed pitch, memory bases, font source and controller mode when comparing frames. See [memory and boot](memory-and-boot.md) and [front-panel controls](front-panel-button-mapping.md).
