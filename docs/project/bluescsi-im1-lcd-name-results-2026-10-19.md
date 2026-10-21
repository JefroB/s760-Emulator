# IM1 LCD full-name confirmation

2026-10-19. Candidate SHA256 `efec015fa431f571b6bcb685d0ab0d20eb6de940d227cd40409fbd34a4f09996` adds a full-name confirmation view to the experimental LCD browser. Selecting an image displays its32 returned filename bytes as two16-byte lines. The chooser can still show21 bytes per row; the confirmation reveals the hidden suffix before any mount. It provides Mount + Load, Back and a persistent CD identifier on its own row. The native header can display status without hiding that identifier.

## Workflow and safety

On Panel+LCD, open Image Library with Value/Menu from the settled native Disk Load screen, choose the collection, then the image. Read both filename lines and the CD identifier. Move to Mount + Load and press Value/Menu to commit, or choose Back. The guest callback initializes its cursor on the non-action name row when opening confirmation; this is firmware UI behavior, not test-side RAM/register forcing.

Three generated32-byte ISO names share all21 initially visible bytes: ABCDEFGHIJKLMNOPQRSTU followed by AAA0000.iso, BBB0000.iso or CCC0000.iso. The native test verifies both16-byte lines in owned RAM and their actual reads by the native LCD rendering routine. The CD1 row is separately verified in RAM and rendering reads. Preview and Back issue noD8. Holding the original activation for0.6 seconds on the third image also leaves confirmation open with no mount, despite Mount using that same field index in the new view.

Explicitly confirming the second image issues exactly oneD8 with index1. Native LCD Load restores13 allocations and119808 exact expectedB bytes; playback/release passes. The first image contains differentA data, so the oracle distinguishes a wrong selection. Every fixture hash remains unchanged. Confirmation uses the validated protocol index rather than reconstructing a path from text. It does not lock the SD directory or reconcile changes made externally while open.

## Rendering and regression evidence

BUG-162 fixes an initial confirmation path that copied unsupported control bytes directly to LCD text. The emitted guard passes256 instruction-decoded cases: printable32..126 stay unchanged, NUL padding becomes space, and all other bytes become question marks. The raw byte01 baseline fails as expected. This is defensive rendering, not expanded filename/Unicode support; the first-profile printable ASCII policy remains.

BUG-163 fixes the confirmation's CD identity being obscured by native Open/status text. It is now printed on its own row. General list-header/status presentation remains part of the broader LCD UI review.

On this same final hash, GB-6 CRT D7 drain cancellation, D8 uncertain/no follow-on, explicit index99 retry,119808-byte native Load/playback and retained SDS cancel/retry/publication160 bytes pass. Native LCD snapshots preserve all browser code and the LCD pointer header. Exact rebuild, decoded branches, nonoverlap, immutable originals and mandatory GB-6 v9 checks pass. The boot ROM is unchanged.

## Fit and remaining gates

Footprint6487/8002 bytes,1515 free/1297 contiguous after code. Relative to the prior6141-byte LCD trial, confirmation/guard/identity adds314 code bytes and32 string bytes. Total browser code3951, help/confirmation strings312, with the212-byte LCD descriptor and26-byte temporary buffer unchanged. No additional workspace region is used.

The full-name display contract is32 returned bytes including extension; D7 cannot reveal a longer hidden tail. The earlier100-image LCD paging/short-name pass remains attached to e798c0bf... . Complete the final-hash LCD paging/collection/IMG/Disk/error/cancellation/cold-state matrix, then broader controllers/concurrency/reset/checkpoint/stack/hardware gates. Full IM1 GO remains open. [Validation](../condensed/validation/bluescsi-im1-lcd-names-2026-10-19.json). [Preview A](../condensed/validation/bluescsi-im1-lcd-preview-a-2026-10-19.png), [preview B](../condensed/validation/bluescsi-im1-lcd-preview-b-2026-10-19.png).
