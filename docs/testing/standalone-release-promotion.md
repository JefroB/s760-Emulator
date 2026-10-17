# Standalone release candidate promotion — 2026-10-17

The frozen standalone has a new source/dependency distribution qualification.
The dated review covers the exact tree in
[`windows-standalone-2026-10-17.json`](../distribution/windows-standalone-2026-10-17.json).
It preserves the 2026-10-11 review as history. Neither review establishes
clean-machine acceptance, signing, publication or a release tag.

## Source and dependency delivery

The previous frozen ASIO library matched the binary supplied by sounddevice0.5.2,
but its upstream build fetched an unpinned Steinberg SDK. The user selected a
source build using the GPLv3 SDK. The replacement uses PortAudio19.7.0 and
Steinberg ASIO SDK2.3.4, dated2025-10-15, with its GPLv3 option. Original project
BSD notices remain; the assembled ASIO-enabled host's distribution profile
identifies its GPLv3 obligations. The separate MAME process retains GPL-2.0.
Full license texts and the embedded BSD helper notices accompany the library.

Source archives accompany the package:

| Archive | Validation |
| --- | --- |
| `mame-source.zip` | 27,323 source/build/legal files; full Visual Studio rebuild from the exported tree returns0. The rebuilt engine passes original-firmware boot/load, scheduled MIDI, rendered audio and exact silent note release. |
| `host-source.zip` | 304 Python/Lua/React/native bridge/build/test files with SHA-256 manifest; the ASIO bridge builds from this exported tree with MAME headers as its sibling. |
| `portaudio-asio-source.zip` | 405 source/build/license files with SHA-256 manifest; a second fresh build verifies the delivered PowerShell recipe. |
| `python-dependencies/` | Exact upstream source distributions, including CPython3.13.0 and PyInstaller6.19.0, with version/URL/size/SHA-256 provenance. |
| `python-native-dependencies/` | Exact source tags selected by CPython3.13.0 for bzip2, libffi, OpenSSL, mpdecimal, SQLite, XZ and zlib. |

The source manifests match every delivered archive entry. Their files and the
upstream source distributions contain no exact local Roland firmware/media
hashes. Original upstream source distributions retain their public test assets;
they are separate from the application's firmware/media library.

For a host rebuild, extract the MAME and host source archives into one root.
Stage an editable copy of the delivered package README at
`docs/emulator/guides/standalone-package-readme.md` in that source root. For a
development rebuild, make its distribution-profile reference plain text until
the corresponding distribution companion files are assembled; otherwise the
development builder correctly rejects the missing local link. Install the
pinned requirements and locked npm dependencies, configure `core/` into
`build/`, and use the supplied builder. The separate ASIO source recipe produces
the replacement library; default development builds remain unqualified.

The corrected dependency inventory binds versions to actual input ownership.
The frozen candidate previously reported global metadata for different installed
versions. Actual bundled versions include websockets16.1.1, cffi2.1.1,
pycparser3.11 and typing_extensions4.16.0. Their notices and original sources
are supplied. MSVCP140.dll joins the external Windows runtime prerequisites;
43 copied Windows runtime files are excluded. See BUG-102.

Unchanged Microsoft WebView2 SDK binaries retain the previously reviewed exact
upstream identities and notices. WebView2 Runtime, .NET Framework4.8, Microsoft
VC v14 x64 and selected device drivers remain installed prerequisites.

Primary inputs: [PortAudio19.7.0](https://github.com/PortAudio/portaudio/tree/v19.7.0),
[the exact earlier PortAudio binary build](https://github.com/spatialaudio/portaudio-binaries/tree/083325660f3e002371213eef8f6a4bd579b647d6),
[Steinberg's SDK](https://download.steinberg.net/sdk_downloads/ASIO-SDK_2.3.4_2025-10-15.zip)
and the provenance URLs recorded with each delivered Python source distribution.

## Runtime revalidation

The new engine, ASIO bridge and ASIO DLL are built from delivered sources. The
launcher and layered configuration UI retain the previously tested bytes.
The new audio stack enumerates ASIO4ALL, MOTU Pro Audio v2 and Realtek ASIO;
a bounded actual MOTU44.1kHz output stream consumes125,952 silent frames with
zero reported underruns, discards or driver flags. This is a device/ABI check,
not musical-audio or analog parity evidence.

The final source-complete archive was extracted into a fresh folder with spaces.
All611 packaged files match its full manifest, including the generated audit
report. Two fresh-profile normal-speed workflows pass in four actual WebView2
launches: load, measured play/release, Level127→64 edit, physical stereo sampling
while retaining the program, firmware Save/export, combined-session restore and
cold reopen/play. Eight Windows output captures preserve20,004.272Hz pitch,
approximately0.502703 edited/baseline peak ratio and a released tail below1e-7.
The observer's startup discontinuity flag is retained; this is not a zero-loss
or analog-output qualification.

Twelve fresh native processes confirm all119,808 original sample bytes and both
new sample allocations through recorded/restored checkpoints and cold firmware
Sample Load. The cycles retain32,429 and36,871 recorded-marker frames/channel,
with73,728 and82,944-byte allocations/channel and440.085/879.833Hz tones.
Edited-volume and combined-session native playback agree and release to exact
silence. These are short clips; no recording-duration guarantee, long-run drift,
cross-build migration or physical round-trip latency is inferred.

The rebuilt ASIO DLL/bridge also pass a separate physical calibration loop:
MOTU outputs3/4 to inputs1/2,159,744 captured frames,439.917/880.001Hz, and zero
reported underruns, overflows, discarded frames or driver flags. This checks
the new audio dependency path; it is separate from sampler musical playback.

The host source rebuild, fresh npm install and development package audit pass
after staging the delivered editable README for the development packaging
profile described above. Its rebuilt development output is not a separately
qualified release. Backend regressions:532 passed. Focused distribution/static
checks:38 passed, plus six final static-report status regressions. TypeScript
passes. BUG-102 fixes actual dependency attribution; BUG-103 preserves historical
artifact identity; BUG-104 prevents static checks from qualifying unrun machines
or DAWs. No test-owned app/audio processes remain.

The final archive is `S760 standalone GPLv3 source-built 2026-10-17.zip`,
287,210,283 bytes, SHA-256
`b1dd036c9331058fb2db0dde75d038e985fc75d5919c19040766460f5cdb08f9`.
Its package, source archives, notices, manifest and handoff scripts stay together.
The final extracted PowerShell5.1 launcher boots the real WebView2 interface
from an unrelated working directory with child development-tool paths removed.
Its clean-machine collector correctly returns INCOMPLETE with nine pending
manual steps, since this remains the development workstation.

## Remaining acceptance

Clean-machine prerequisite discovery, installation/remediation, two complete
workflows and evidence review still require a separate Windows installation.
The user has no clean machine or VM available. Local inspection finds no
Windows Sandbox, Hyper-V service/module, VirtualBox or VMware installation.
Removing development-tool paths on this workstation does not close that gate.

Use the [clean-machine handoff](standalone-clean-machine-handoff.md) with the
promoted package's complete manifest. Its collector must retain incomplete
status until actual observations and evidence exist. This task publishes no
release, creates no tag and makes no VST3 qualification claim.

[Machine-readable review and results](../condensed/validation/standalone-release-promotion-2026-10-17.json)
record exact binaries, source identities, tests and limitations.
