# IM1 native Optimize no-change roundtrip

2026-10-20. Unchanged candidate `19448d85773dd99081a45cdc33ca7defd82f4a4bd3b9cb28a2b533676d68a45c`, mandatory GB-6 v9 and existing selectable boot ROM. Real native GB-6/panel inputs open Disk options → Optimize and select a private copy of the verified10MiB512-sector HD0. Native F3 opens the unsaved-memory warning; Yes returns to the normal Optimize options screen after processing. The test begins with no loaded sample allocations. A second F3/warning is dismissed with No before export; both input sequences are preserved in validation.

The exported HDD equals the source byte-for-byte (SHA256 `a8259a569101440c0ba30d96c63f1811d30f3c294e2f0fc69364fd4698c644f7`). Counts remain1 performance/22 patches/88 partials/13 samples. A fresh emulator process scans and Loads this export:13 allocations and119808 expectedB sample bytes match exactly, then playback/release passes. Browser/SDS code remains intact in every captured RAM snapshot; original media and firmware remain unchanged.

This is a valid-media/no-change Optimize roundtrip on the already-packed fixture. It does not prove fragmented-data relocation, recovered free space, interruption handling or physical behavior. Native Copy/Convert Load/Vol. Dump FD and broader parent/concurrency/reset/checkpoint/stack/full fit/hardware gates remain open. RC-100 testing is waived under the user's accepted compatibility assumption. Footprint remains6487/8002 bytes,1515 free/1297 contiguous after code. Full IM1 GO remains open.

The first attempt exceeded the120-second harness wait while generating over818MB of register logs; it is excluded from acceptance. The accepted repeat removes broad read-only loader tracing and the MAME -log flag, keeps read-only snapshots, and permits a bounded600-second wall wait. The emulator and firmware binaries are identical. The faster repeat and exact cold Load support an instrumentation-overhead diagnosis; no firmware failure or fix is claimed.

[Validation](../condensed/validation/bluescsi-im1-optimize-roundtrip-2026-10-20.json).
