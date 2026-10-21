# IM1 LCD Save System and exported-system cold boot

2026-10-20. Base candidate `19448d85773dd99081a45cdc33ca7defd82f4a4bd3b9cb28a2b533676d68a45c` remains unchanged. Native Panel+LCD selects Disk options → Save System, inserts a private blank1.44MB floppy, presses F3, confirms formatting with S2/Yes, then invokes F3 Save System after formatting. The exported image SHA256 is `74bbfa288f06ec8c9d9cfdb9898f34542c85cff732a67607b5b007e911128a31`. Only real panel/media inputs drive the firmware; observations are read-only. Initial F1/F2 probes at the format prompt were no-ops and are retained in the private input record.

The resulting1474560-byte image preserves all3951 browser code bytes, the212-byte LCD descriptor and all retained SDS repair spans. Mandatory GB-6 v9 instruction checks pass against the saved system image and unchanged selectable boot ROM. Save System naturally changes disk metadata, configuration and other saved bytes; the export is not expected to equal the source image globally.

A fresh emulator process boots this exported system with genuine saved controller0 NVRAM. Opening Image Library clears all76 operation-context bytes and issues no image command before choosing a collection. Explicit ISO target1/index1 selection then reaches native LCD Load, restores13 allocations and119808 exact expectedB sample bytes, and passes playback/release. A/B fixture contents differ, making the byte oracle sensitive to wrong selection. The library files remain byte-exact.

This qualifies native LCD Save System/format/export and the named exported-system cold-boot/load workflow. It does not qualify external emulator checkpoint synchronization, interrupted formatting/system saving, arbitrary disk geometry or physical floppy/BlueSCSI behavior. The unchanged source candidate remains6487/8002 bytes used,1515 free/1297 contiguous after code. Full IM1 GO remains open: native remaining Disk operations, RC-100, broader ownership/reset/checkpoint/stack and physical BlueSCSI configuration/timing still require evidence.

[Validation](../condensed/validation/bluescsi-im1-lcd-cold-system-2026-10-20.json).
