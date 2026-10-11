# Windows standalone distribution qualification

Qualification date: 2026-10-11. The exact Windows x64 standalone artifact recorded
by the repository's `docs/distribution/windows-standalone-2026-10-11.json` manifest is
qualified for redistribution with its accompanying notices and source archives.
This is a distribution engineering review, not a claim of complete emulation,
clean-machine installation acceptance, legal immunity, or VST3 host acceptance.
Nothing has been published by this qualification.

## What was reviewed

The package contains the project launcher/runtime and React player, a separate
modified MAME executable and plugins, Python and its frozen dependencies.
Project-owned code is BSD-3-Clause. The repository history reviewed has one
recorded contributor identity (the owner); original project work is authorized
by the owner's license decision. Existing third-party headers are retained,
including the S-760 driver's Roland S-760 RE Team/Wilbert Pol attribution.
This review covers the assembled artifact, not every unrelated file in the
checkout or future contributions.

| Component | Distribution treatment |
| --- | --- |
| Modified MAME | GPL-2.0 as described by its COPYING; full legal directory and complete buildable source snapshot accompany the executable. Individual source/library notices remain intact. |
| Project Python/Lua/React sources | BSD-3-Clause; source archive and root license accompany the package. |
| PyInstaller loader and runtime hooks | Unmodified loader's explicit bootloader exception; Apache-2.0 runtime hooks. Full COPYING retained. Build-tool modules excluded from the frozen application. |
| Python 3.13.0 | PSF and historical notices retained; 21 DLL/PYD inputs match the official CPython embed archive. OpenSSL 3.0.15, expat, XZ/liblzma, zlib, bzip2 and libffi notices retained. |
| pywebview 6.2.1, websockets 16.0, Jinja2 3.1.6, MarkupSafe 3.0.2, pycparser 2.22 | BSD notices retained. |
| pythonnet 3.2.1, clr_loader 0.3.1, cffi 1.17.1, bottle 0.13.4, more-itertools 11.1.0 | MIT notices retained; cffi's vendored libffi copyright/license headers also retained. |
| proxy_tools 0.1.0 | Actual source matches upstream; upstream BSD notice retained, correcting misleading MIT package metadata. |
| packaging 25.0, wheel 0.45.1, setuptools 80.9.0, typing_extensions 4.14.1 | MIT/BSD/Apache/PSF notices and vendored notices retained. Frozen setuptools vendor modules were inspected; LGPL autocommand is not bundled (its notice appears only in the conservative notice superset). |
| React/react-dom/scheduler | Actual Vite module inventory records these runtime packages; locked versions and MIT notices retained. Tailwind's generated CSS notice and MIT license retained. No font binaries bundled; HTML currently references Google Fonts. |
| WebView2 SDK 1.0.3856.49 | All five bundled SDK DLLs match official NuGet bytes; separate Microsoft BSD-3-Clause notice retained. Installed WebView2 Runtime is a prerequisite. |
| Windows runtime | 42 copied UCRT/API-set/VC runtime DLLs removed from the package. Supported Windows and Microsoft VC v14 x64 runtime are prerequisites; no installer is redistributed. |

`BUNDLED-INPUTS.json` records 170 collected inputs (including 42 excluded system
prerequisites) and 615 frozen modules, with no unattributed collected binaries.
`DEPENDENCY-INVENTORY.json` remains a conservative build-environment notice
superset. Neither inventory by itself grants release status. The artifact-level
review and exact tree manifest are authoritative for this dated qualification.

Upstream identity evidence and verbatim supplementary notices are retained in
`docs/distribution/`. Primary references include [MAME licensing](https://docs.mamedev.org/license.html),
[PyInstaller licensing](https://pyinstaller.org/en/stable/license.html),
[the exact WebView2 SDK license](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.3856.49/License),
and [CPython's official binary archive](https://www.python.org/ftp/python/3.13.0/python-3.13.0-embed-amd64.zip).

## Corresponding source and rebuild

`corresponding-source/mame-source.zip` accompanies the binary, rather than a
promise to provide source later. It includes 27,323 source/build/legal files,
current local modifications, generated Visual Studio projects and generated
build inputs. ROMs, sample audio and precompiled products are excluded. The
snapshot was extracted into a new directory and rebuilt without cached objects.
The resulting executable, not the pre-existing workspace binary, is packaged.
The archive's internal `qualified:false` describes the initial candidate stage;
the subsequent rebuild and this artifact review establish its qualification.

Prerequisites: Visual Studio 2022 C++ tools (v143), Windows SDK and Python 3 on
PATH. From the extracted `mame-source` directory, in PowerShell:

```powershell
$env:CL = '/Z7'
& 'C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/MSBuild.exe' build/projects/windows/mames760/vs2022/mames760.vcxproj /m:1 /p:Configuration=Release /p:Platform=x64 /v:minimal
```

The clean rebuild returned exit 0. The package also includes original host
sources and lockfiles in `corresponding-source/host-source.zip`; the native
archive supplies MAME plugins and the engine's complete source. Keep both
archives and all notices alongside any redistribution of this qualified tree.

## Acceptance and gate

The rebuilt engine boots original user-supplied firmware, loads the test disk,
plays/releases scheduled MIDI and shuts down cleanly. Pull audio requests total
122,616 stereo frames, with zero drops and less than one PCM16 unit difference
from the MAME WAV conversion. The final desktop returns Perform Play at 640×480,
with 225,776 nonzero pixels, and exits cleanly after removing copied Windows DLLs.
The test firmware remains outside the package. Backend regressions: 241 passed;
frontend build and TypeScript checks passed.

The release check recomputes every package file's hash and size, rejects added
files and checks the trusted repository manifest. Editing PACKAGE-AUDIT.json
cannot unlock it. Tests cover changed engine, license, source archive and added
files. Any changed build must be reviewed and its manifest deliberately updated.

```powershell
python scripts/s760_package_audit.py --package <qualified-package-directory> --require-release
```

The builder creates development artifacts by default. Its `-Release` mode
verifies an already assembled, reviewed package; it does not silently qualify
a new build. Source archive contents were checked against their manifest and
for forbidden media extensions and exact private fixture bytes. These checks
do not detect arbitrary transformed proprietary content.

## User prerequisites and remaining product work

Use Windows 10/11 x64 with WebView2 Runtime, .NET Framework 4.8 and Microsoft
Visual C++ v14 x64 runtime installed. Supply authorized boot ROM/system disk
copies using [the firmware setup guide](FIRMWARE_SETUP.md). No Roland binaries,
sample disks or saved sessions are distributed. No replacement firmware is
claimed. Runtime installers are obtained separately from Microsoft.

Signing, first-run setup, testing on a clean machine, physical MIDI/audio-device
qualification, native sampling input and actual DAW/editor qualification remain
product roadmap work. This package is an unsigned development-stage player whose
distribution contents have been qualified, not a finished sampler release.
