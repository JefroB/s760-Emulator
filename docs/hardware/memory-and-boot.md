# CPU banking and native boot contract

The S-760 CPU is an Intel S80C196KB. IC15 is the external boot EPROM; IC20 is an I/O gate array. Earlier claims that IC20 contained an undumpable boot ROM are withdrawn.

The current native driver has independent fetch selectors at 0100–0106 and data selectors at 0108–010E, covering four 16 KiB logical windows. Its bank translation is `physical = (selector << 10) + (logical & 3FFF)`, with hexadecimal addresses throughout this page. Fetch context and data context must be recorded separately when identifying code and operands.

For a data selector of 0400 in the C000–FFFF window, the implemented peripheral addresses include:

| Logical | Physical | Native interface |
| --- | --- | --- |
| C000 | 100000 | Wave host |
| D000 | 101000 | TVF |
| D800 | 101800 | MEQ |
| DC00 | 101C00 | Panning window; physical chip attribution unresolved |
| E000 / E002 | 102000 / 102002 | FDC status/auxiliary and FIFO |
| E400–E41E, even addresses | 102400–10241E | SCSI |
| E800 | 102800 | VDP window |
| F000 | 103000 | I/O gate window |
| F800 / F802 | 103800 / 103802 | LCD data and command writes |

These are contextual addresses from the implementation and observed firmware, not an unconditional flat CPU memory map. See [s760.cpp](../../mame-source/src/mame/roland/s760.cpp), particularly `banked_address` and banked physical read/write dispatch.

The IC15 loader path copies 112 tracks from disk offsets 004800–1007FF into physical memory 000000–0FBFFF, then hands off at logical C000 with fetch selector 0106 set to zero. The earlier diagnostic relation `file = runtime + 2780` described a synthetic flat-load path; it is not a general mapping for original-firmware execution. Likewise, low-memory HLE selector stubs from early bring-up are not a hardware boot-service specification.

The current native CPU path and synthetic diagnostic path have different scope. Do not infer silicon instruction semantics from a boot workaround. In particular, old instructions to keep PUSHA/POPA as stack-neutral no-ops are obsolete. Low-power instruction behavior remains subject to the [bug backlog](../project/bug-backlog.md).

For independently identified input bytes and bank-aware analysis, use the [firmware manifests](../../scripts/firmware_manifests/) and [firmware documentation](../firmware/README.md). The [native firmware status](../emulator/runtime/native-firmware-status.md) records qualified profiles; successful emulator boot does not prove physical hardware equivalence.
