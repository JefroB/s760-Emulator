# Native VST3 engine selection

Historical paths into the former findings tree below identify past runs; that scratch tree was removed on 2026-10-21. Generate new run output under `temp/work/`. See [hardware evidence policy](../../hardware/evidence-and-open-questions.md).

The exported `Roland_S760.vst3` factory creates the native MAME processor only.
Its bridge, MIDI and PCM use the same child process. It does not consult the
historical `S760_BACKEND` selector and never falls back to the buffer-only core
when firmware or runtime startup fails. Direct historical constructors remain
for diagnostic tests; VST2 and CLAP remain outside this milestone's release scope.

## Development configuration

Set these absolute paths in the environment inherited by the host before it
loads the module. For a source checkout, for example:

```powershell
$env:S760_NATIVE_ROOT = 'D:\S-760'
$env:S760_NATIVE_STATE_ROOT = 'D:\S-760\docs\ic20-hle-findings\chatGPT-work\plugin-instances'
$env:S760_BOOT_ROM = 'D:\S-760\roms\BOOT\Roland_S-760_v1.11.BIN'
$env:S760_SYSTEM_DISK = 'D:\S-760\roms\System\S760224.IMG'
```

The runtime root contains `mame-source/mames760.exe` and
`scripts/s760_runtime.lua`. Firmware is user-supplied. Each component creation
reserves a unique child directory under the state root, including when several
instances share one host. The native client locks that directory and owns its
child process. Instance files are retained for diagnosis; they are not complete
host project state or an automatic recovery mechanism.

Missing configuration/files and runtime startup failures now create a silent
native configuration instance with the startup reason displayed in its editor.
Correct and save paths there, then reload through the host. No historical engine
is substituted. Unknown requested interfaces still fail with a null pointer;
missing installed editor assets require installation repair. Errors are also
written to stderr and the settings-side diagnostic file. No exception escapes
component creation. See [graphical setup and recovery](../runtime/native-vst3-configuration.md).

## Supported surface and compatibility

The factory advertises the instrument class only. The former Live Sampler FX
class remains unadvertised and cannot be instantiated. Qualified input is on the
native instrument's optional stereo bus; a separate FX class is not delivered.
Existing projects referencing that FX class cannot instantiate it in this build;
silently substituting the historical core would conceal the missing native path.
The instrument class identifier is unchanged.

Supported native processing is float32 stereo at 44.1/48/96 kHz with note-on/off;
see the [timing contract](../runtime/native-audio-timing.md). Optional native input supports
44.1 kHz stereo float32 through the same native ADC as the standalone. Input at
48/96 kHz rejects explicitly; see [sampling](../runtime/native-vst3-sampling.md). State
outside the bounded native profile rejects. Suspended native save/recall is
now implemented; see the [state contract](../runtime/native-plugin-state.md). These operations
do not use the historical core. Factory selection retirement therefore does not close the separate full
third-party DAW project-state and hardware qualification objectives.

## Acceptance

```powershell
cmake --build build --config Release
./build/Release/s760_native_factory_tests.exe . docs/ic20-hle-findings/chatGPT-work/factory-acceptance --paced-var 48000 10
```

Use a fresh private state root for this test. It loads the actual module using
`LoadLibrary`, resolves `GetPluginFactory`, checks silent missing-configuration recovery,
requests both component and processor interfaces, and verifies distinct native
children. With the historical selector explicitly set to `core`, the exported
component still boots native firmware, loads ROBOFULL through firmware controls,
returns authentic converted CRT/LCD frames and renders exact offline-reference
PCM at wall-clock pace. The test also checks note offsets/release, rejected
unsupported input clocks and invalid state requests, suspend/resume and termination. The
separate `--state` acceptance covers supported native save/recall.

This exported-module harness uses this repository's interface definitions.
Independent SDK ABI and actual SoundCheck host/editor qualification are recorded
separately in the [roadmap](../../project/completion-roadmap.md); other DAWs remain unqualified.
The [original factory record](../../condensed/validation/native-factory-2026-10-11.json)
is historical and predates graphical recovery.
