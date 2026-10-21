# IM1 LCD browser feasibility prototype

2026-10-19. Experimental LCD/CRT candidate SHA256 `e798c0bf83cfe49a2c736a63686e1437acbede0999e76cb6dea04874042781bf` adds a separate native LCD descriptor/renderer and shares the existing catalog, admission, cancellation and image-switch routines. Mandatory GB-6 v9 and its existing selectable boot ROM are retained. This is a scoped prototype, not completed LCD support or a hardware release. The preceding broader-qualified CRT baseline remains32143f10... .

## Observed native workflow

Using genuine saved Panel+LCD mode0 NVRAM and physical panel keys, Mode/Shift/F2 enters stock Disk LoadF7. After that screen settles, Value/Menu opens the owned Image LibraryF5; Value/Menu selects the collection. Seven LCD rows show a100-image ISO catalog. Native arrow input scrolls the nine-row action list through origins0..2, exposing Collections/Previous and Next. Value/Menu on Next rereads the catalog and advances FIRST0 to7. Exit returns toF7; reopening invalidates the previous catalog and explicit selection starts at0 again.

The trial displays CD1 in the header. Names are limited to21 visible bytes in this first layout. The short names used by the native fixture are fully visible; full32-byte names, prefix disambiguation and a long-name view remain open. The current host preflight's32-byte profile must not be treated as complete LCD display safety.

The ordinary panel workflow mounts a valid ISO at index0, selects its native Load commands and loads it with All On/Load. The native wave dump contains exactly119808 expected sample bytes in13 allocations. Playback/release passes the existing audition oracle, and every fixture hash stays unchanged. This establishes real LCD-to-native loading, not just a rendered menu or generic audio level. [Loaded LCD](../condensed/validation/bluescsi-im1-lcd-loaded-2026-10-19.png).

## Reuse, fit and regression scope

The separate LCD resource follows the stock F5 geometry and seven field records, with owned callback/tuple pointers. It uses native003B:64FA/62C7 LCD text/glyph services and its own bounded0..2 scroll state. Field actions share the original browser callback; native LCD Disk operations use0196:9798 and the mount handoff uses LCD LoadF7. CRT modes retain their existing descriptor and rendering path. Init clears the activation latch after drawing so a previous panel key cannot activate a new menu implicitly.

BUG-161 records a static alias found during development: the initial trial reused an old selected-index diagnostic word as scroll state. Removing the obsolete five-byte store keeps the real protocol index in C+42 and prevents an image index0..99 becoming a scroll pointer. This defect existed only in an unaccepted trial.

The exact final trial also passes the existing GB-6 CRT D7 drain cancellation, D8 uncertain/no follow-on, index99 retry,119808-byte native Load/playback and retained SDS cancel/retry/publication160 bytes. Browser code and the LCD pointer header remain unchanged in all LCD snapshots. Exact rebuild, decoded branch targets, nonoverlap and immutable-original audits pass. Broader Mouse, IRQ/session and Save System matrices remain evidence for their earlier hashes.

Fit is6141/8002 bytes:3637 browser code,831 SDS helpers,739 CRT resources,280 help strings,212 LCD descriptor,26 temporary LCD text,224 page buffer,92 context and100 native labels. There are1861 free bytes,1611 contiguous after code. Relative to the5408-byte CRT baseline, LCD adds733 bytes. Code ends at physical4EB5; LCD descriptor5650..5724 and temporary text5730..574A fit before the page buffer57F0. No extra memory region or boot-ROM change is used.

## Remaining gates

Complete long-name identity/viewing, all100 entries forward/back, all collection/IMG paths, LCD Disk options, error/cancellation, parent restoration and Save System cold state on the final LCD hash. RC-100 packet input, broader concurrency/reset/checkpoint, full stack/ISR and hardware remain open. Full IM1 GO remains open. [Durable validation](../condensed/validation/bluescsi-im1-lcd-prototype-2026-10-19.json) includes exact identities, native state/command rows and fit audit. [LCD browser screenshot](../condensed/validation/bluescsi-im1-lcd-browser-2026-10-19.png).
