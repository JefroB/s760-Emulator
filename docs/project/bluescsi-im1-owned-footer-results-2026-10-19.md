# IM1 browser identity and footer ownership

2026-10-19. The private candidate SHA256 `18421aaa97280374c57eac337b31b2d2f0f5e79558401ffb730b0aba25a0f28a` removes the inherited parent softkey labels and supplies the native screen identity `Image Library`. Mandatory GB-6 v9 and the existing selectable boot ROM remain included. This is an emulator-qualified incremental candidate, not a hardware release or full IM1 GO.

The three-byte change relative to the page-window candidate redirects descriptor offset00 to the existing title string and extends the owned CRT clear from rows3..22 to rows3..24. No callback bindings, SCSI transport, IRQ service or catalog storage routines change. Geometry byte9 remains zero: the six softkey callbacks remain native no-ops, rather than acquiring the parent's actions. Dedicated help and additional browser controls are still open.

Native 0/1/100-image catalogs and rejected101-entry fixture pass, preserving full32-byte names, packed browser/SDS code and resource headers. All four screenshots have exactly20480 blue pixels over the former footer area (640x32, y368..399). Read-only RAM confirms cached identity pointer9CF3 and `Image Library` at physical58F3. Visual review confirms Exit restores the Perform keyboard and native footer.

A second native workflow verifies Next to origin7, generated101-entry refresh failure, no stale D8 action, and explicit retry recovery. Exact rebuild, branch-target and immutable-original audits pass. Allocation remains4982/8002 bytes:3020 free,3004 contiguous after code.

[Durable validation](../condensed/validation/bluescsi-im1-owned-footer-2026-10-19.json) includes exact byte changes, build identities, screenshot hashes and both native results. The prior nine workflows remain evidence for SHA512e3468..., not newly rerun claims for this hash. Full help/identity presentation, filename preflight, other controllers/LCD, concurrency/reset/stack bounds and physical BlueSCSI acceptance remain open.
