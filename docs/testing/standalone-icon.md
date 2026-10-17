# Standalone application icon

The 2026-10-17 v4 candidate embeds the selected floppy-disk S-760 artwork in
`S760Studio.exe`. Windows Explorer and pywebview's WinForms window use the
executable resource. The source PNG, seven-size ICO and generation prompt are
in [assets](../../assets/README.md). The build clears PyInstaller's cache so a
replacement icon at the same filename cannot retain stale executable resources.

Verification on the development workstation:

- PE icon resources at 16, 24, 32, 48, 64, 128 and 256 pixels match the ICO's
  corresponding image payloads byte for byte.
- The real WinForms window's 48-pixel icon, read through `WM_GETICON`, matches
  the selected ICO frame pixel for pixel.
- Three real frozen WebView2 cases pass: missing-firmware window close, OUT
  firmware boot followed by save/quit, and recovery refusal followed by explicit
  discard. Every app exits with code 0 and its native children stop. Profiles
  remain outside documentation.
- MAME, native audio and third-party source snapshots retain the v3 identities.
  The updated corresponding host source includes the icon and build instructions.

This is icon and workstation regression evidence. The previous user-accepted
clean-machine scope remains recorded separately; this revision was not tested
on that machine. [Machine-readable evidence](../condensed/validation/standalone-icon-2026-10-17.json).
