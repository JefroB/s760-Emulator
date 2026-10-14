# Roland S-760 native emulator

An open-source Roland S-760 emulation project built around a modified MAME
runtime, a Windows standalone player and a native VST3 instrument. The original
firmware handles the sampler's interface and workflows; React/WebView2 displays
the live CRT/LCD frames and provides the rack controls.

![Native standalone with original firmware and optional keyboard](docs/images/standalone-keyboard.png)

## Current status

As of **2026-10-14**, Milestones 1–4 are complete for their documented Windows
development profiles. **SoundCheck is the automated DAW/host acceptance framework.**
Hardware coverage and final release qualification remain open in
[Milestones 5 and 6](docs/COMPLETION_ROADMAP.md). This is a development project;
passing model or native-runtime tests does not establish complete hardware parity.

| Product | Qualified scope |
| --- | --- |
| Windows standalone | Original-firmware boot, live displays/controls, floppy load/save/export, MIDI playing, session recovery and supported 44.1 kHz MME/ASIO stereo sampling |
| Native VST3 instrument | SoundCheck SDK discovery, MIDI/controller effects, stereo output, offline rendering, optional 44.1 kHz input and same-build project save/cold reopen |
| GB-6 OS experiment | Reproducible mouse-decoder patches for user-supplied OS 2.24; v8 vertical movement user-confirmed, balanced v9 hardware acceptance pending |

Native plugin output processing is tested at 44.1/48/96 kHz. Input and project
profiles have narrower documented limits. Cross-build/rate/negotiated-maximum
project migration is unsupported; incompatible recall rejects explicitly. Raw
CC120/121 are unsupported by the qualified firmware profile; documented message
sequences provide panic/reset. Live Sampler FX is unadvertised; VST2/CLAP and the
historical core are diagnostic paths rather than qualified native products.

## Start here

1. Supply your own boot ROM and OS disk using [firmware setup](docs/FIRMWARE_SETUP.md).
   Firmware, sample libraries, patched OS images and hardware captures are excluded
   from the repository and packages.
2. Follow the [standalone guide](docs/STANDALONE_PLAYER.md) or
   [VST3 configuration guide](docs/NATIVE_PLUGIN_CONFIGURATION.md).
3. Use Configuration for firmware/media paths, MIDI and audio devices in standalone.
   In VST3, the host supplies audio/MIDI. Audio input and the on-screen keyboard
   are opt-in.

With a current native MAME build and Node/Python dependencies installed:

```powershell
python -m pip install -r scripts/requirements-standalone.txt
npm --prefix google-ui ci
npm --prefix google-ui run build
python scripts/s760_standalone.py
```

The desktop player requires Windows WebView2 Runtime. It does not download
firmware. See the guide for explicit paths, startup recovery and browser mode.

## Build and test

The qualified development environment is Windows x64 with Visual Studio 2022 C++
tools, CMake, Python and Node. The native MAME executable is built separately
from the CMake host/plugins; see the [native build/runbook](docs/condensed/11-native-boot-and-audio-runbook.md).

```powershell
cmake -B build -S core -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
.\build\Release\s760_core_tests.exe
.\build\Release\s760_plugin_tests.exe
python -m pytest tests
```

Some tests require local firmware, native artifacts or optional dependencies;
skips are reported separately. SoundCheck qualification uses actual native SDK
processing and measured PCM. See [SoundCheck projects](docs/SOUNDCHECK_PROJECTS.md),
[controller tests](docs/NATIVE_VST3_MIDI.md), [rendering](docs/NATIVE_VST3_RENDERING.md)
and [host sampling](docs/NATIVE_VST3_SAMPLING.md) for commands, identities and limits.

## GB-6 patching

The [GB-6 patch guide](docs/GB6_OS_PATCH.md) explains how to reproduce v8/v9 from
an original, user-owned OS 2.24. The standard-library Python patcher verifies both
input and output hashes and refuses to overwrite files. Only patch source,
tests and instructions are versioned; generated images remain local.

These experiments replace the Mouse+CRT decoder. A combined mouse/RC-100/GB-6
selection and boot-ROM changes remain deferred in the [controller plan](GB6_CONTROLLER_PLAN.md).

## Documentation

- [Completion roadmap](docs/COMPLETION_ROADMAP.md): completed gates and remaining work.
- [Condensed technical references](docs/condensed/README.md): hardware, firmware and evidence.
- [Media library](docs/NATIVE_MEDIA_LIBRARY.md) and [sessions/recovery](docs/NATIVE_SESSIONS.md).
- [Sampling](docs/NATIVE_SAMPLING.md), [rack controls](docs/NATIVE_RACK_CONTROLS.md)
  and [plugin state](docs/NATIVE_PLUGIN_STATE.md).
- [Bug backlog](docs/BUG_BACKLOG.md): known defects, including intermittent controller-QA rejection BUG-060.
- [Distribution qualification](docs/DISTRIBUTION_QUALIFICATION.md): exact dated standalone artifact review;
  final packages and clean-machine release acceptance remain open.

`mame-source/` contains the native engine, `core/` the C++ host/plugins,
`google-ui/` the shared interface and `scripts/` the runtime and verification tools.
Historical coverage catalogs are inventories, not claims of complete product acceptance.

## License and attribution

Project-owned code is [BSD-3-Clause](LICENSE); MAME and other dependencies retain
their respective licenses and notices. See the distribution review before packaging.
Roland and other product names belong to their owners. This independent project
is not affiliated with or endorsed by Roland Corporation.
