# IM1 current-build native HDD Save and cold Load

2026-10-20. Unchanged candidate `19448d85773dd99081a45cdc33ca7defd82f4a4bd3b9cb28a2b533676d68a45c` is tested through real native GB-6 pointer/panel/MIDI input, genuine persisted controller3 NVRAM and read-only observers. No guest RAM/register/PC forcing is used.

The browser selects ISO index99 through the paged100-image catalog. Native Load restores13 allocations and119808 exact expectedB sample bytes with playback. The browser's Disk options route then enters native Utility, selects the private HD0/512-sector10MiB fixture, and completes native quick initialization. Native Save writes the loaded program/sample hierarchy to that HDD; the runtime exports the private changed medium.

The exported Roland image parser finds13 sample allocations whose concatenated contents match all119808 expected bytes. A fresh emulator process uses the same candidate firmware and the exported HDD. Native Disk options → Load restores the saved data; all119808 bytes again match, allocation count is13, and playback/release passes with the same measured peak. The original HDD fixture and golden firmware inputs remain unchanged. This is native execution and cold reload evidence, beyond menu-label or screen-routing checks.

The named HD0 profile does not establish arbitrary geometry, physical write-protection, interruption/concurrency handling or every native Disk operation. Controller mode2 selection exists, but current native RC-100 input is unimplemented; selecting its mode or using mouse/panel events cannot qualify the RC-100 protocol. The user waived RC-100 testing as an IM1 gate on2026-10-20: its untouched implementation is assumed compatible, and no physical controller is available. This is an accepted assumption, not verified protocol compatibility.

Source firmware remains6487/8002 bytes used,1515 free/1297 contiguous after code. No additional boot-ROM patch; GB-6 v9 remains linked. Full IM1 GO remains open: remaining native operations, broader ownership/parent/concurrency/reset/checkpoint/stack and physical BlueSCSI configuration/timing gates still require qualification.

[Validation](../condensed/validation/bluescsi-im1-hdd-save-current-2026-10-20.json).
