# Standalone media-defaults revision — 2026-10-17

The [v2 acceptance ZIP](https://github.com/JefroB/s760-Emulator/releases/download/standalone-acceptance-2026-10-17-v2/s760-standalone-acceptance-2026-10-17-v2.zip)
contains the rebuilt host with portable media folders and OS `.OUT` discovery.
The original accepted kit remains available unchanged.

## Portable layout

The ZIP explicitly preserves these empty directories inside `S760Studio/`:

| Folder | First-run default |
| --- | --- |
| `roms/BOOT/` | IC15 raw boot ROM; standard name or one 32KB `.bin`/`.rom` |
| `roms/System/` | OS `S760224.IMG` or `S760224.OUT`, or one correctly sized alternative |
| `roms/FDD/` | Gotek sample floppy library |
| `roms/SCSI/` | Supported named SCSI images; copied to private instance storage without replacing existing edits |

Explicit Configuration/command-line paths take priority. IMG is preferred when
both standard OS filenames exist. Ambiguous nonstandard files require a choice
in Configuration. OUT uses the same raw bytes as IMG, with no conversion.
No user firmware or media is included. OUT is also excluded by distribution and
source-bundle media filters.

## Validation and source delivery

The frozen executable boots to original-firmware Perform Play in a relocated
folder using only `roms/BOOT/ic15.rom` and `roms/System/Roland OS 2.24.OUT`.
Neither path was passed on the command line. Real WebView2 canvas readback is
640×480 with 225,776 nonzero pixels. Native regression also passes firmware
boot/load, audio pull rendering and scheduled MIDI.

The exact previously source-built MAME and ASIO binaries, third-party binaries,
license notices and dependency source archives are retained. The new executable
is rebuilt from the delivered host source, including the media-path module.
Every first-party frozen module matches its corresponding-source file hash.
The standard-library ZIP changed only container metadata: all uncompressed
entries match the previous package. A new dated distribution manifest identifies
this exact tree rather than rewriting the historical review.

Archive size: 287,293,134 bytes. SHA-256:
`2a512ea752d8f613d2489cb790969474fe529780fc92d3abd1cd48fa52b213ab`.
See [machine-readable evidence](../condensed/validation/standalone-media-defaults-2026-10-17.json)
and [exact distribution manifest](../distribution/windows-standalone-2026-10-17-media-defaults.json).

## Clean-machine handoff

The user [accepted the prior kit's clean-machine launch/setup](clean-machine-acceptance-2026-10-17.md),
waiving the full media workflow because no sample disk was available there.
That handoff gate is closed. This rebuilt host has the separate workstation
verification above; no new execution on the clean machine is invented.

Unblock a browser-downloaded ZIP before File Explorer extraction, or use
`install-acceptance-v2.ps1` from the v2 prerelease. Its hash pin identifies this
v2 ZIP. The v1 helper continues to identify the original ZIP.
