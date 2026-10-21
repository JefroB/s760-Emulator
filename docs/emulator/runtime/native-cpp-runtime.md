# Native C++ runtime adapter

Historical paths into the former findings tree below identify past runs; that scratch tree was removed on 2026-10-21. Generate new run output under `temp/work/`. See [hardware evidence policy](../../hardware/evidence-and-open-questions.md).

The Windows `NativeRuntimeClient` launches the same MAME executable and Lua
protocol used by the Python standalone. It does not use Python, a second synth,
or a separate display model. It is a blocking worker-side interface.

Configure `S760MameHost` explicitly before calling `init()`:

```cpp
s760::NativeRuntimeConfig cfg{application_root, private_state_directory,
    boot_rom_path, system_disk_path, optional_sample_disk_path};
s760::S760MameHost host;
host.configure_native(cfg);
if (!host.init()) { /* report host.native_error() */ }
```

The state directory is exclusively locked. Firmware is staged under that
directory without modification. Local sockets use the per-launch token and
bounded replies; inherited diagnostic environment switches are cleared.
Only the log handle is inherited by the child. A Windows job binds child
lifetime to the client process, including abnormal parent exit. This cleanup
does not restore unsaved machine or media state.

In native mode, `run_frame()` refreshes real CRT/LCD output; it does not add a
second emulation clock. The host converts native pixels into the existing
640x480 RGBA and160x64 MONO1 bridge formats. Native pointer/panel inputs, MIDI,
guarded floppy insertion and worker PCM use the same owned runtime. The
unconfigured historical buffer-only mode remains for existing seam tests.
It must not be interpreted as native execution or full product integration.

## Audio worker boundary

Pause the runtime and enable capture before demand rendering. A
`NativeAudioWorker` renderer can call `host.render_native_audio()`. The worker
requests1024-frame blocks and prefills at most4096 frames. Its preallocated SPSC
queue supports one producer and one audio callback consumer. Callback `read()`
does no allocation, locking, I/O or emulation; missing frames become explicit
host silence and increment an underrun counter. Backpressure never overwrites
unread native PCM. The renderer must bound its own I/O; the native client has
socket timeouts. Start/stop and destruction belong outside the audio callback.

This is not a qualified DAW latency policy: the machine may run ahead by a
video/sound quantum, and the test consumer waits for prefill. Live deadline
performance, host event offsets and sample-rate negotiation remain open.

## MIDI schedule

`schedule_midi` takes1–256 ordered events, each with an absolute44100Hz emulated
sample timestamp and1–3 bytes. Submit while paused; `append:true` permits adding
ordered events after the pending tail (256 total pending maximum),
and within the next30 seconds. Invalid/late batches are rejected atomically.
The Lua scheduler waits in emulated time and enqueues bytes through the native
MIDI device's existing31250-baud transmitter. Status reports pending count,
delivery timestamps and errors. Timestamp means enqueue time, not audible
onset; serial transmission and firmware service still take time. The binding
checks transmitter capacity before accepting the bytes.

## Reproduction

Requires locally supplied original firmware, ROBOFULL fixture and native MAME.
Use a private state path under `docs/ic20-hle-findings/chatGPT-work`.

```powershell
cmake --build build --config Release
./build/Release/s760_native_audio_queue_tests.exe
./build/Release/s760_native_runtime_tests.exe . docs/ic20-hle-findings/chatGPT-work/cpp-native-test
python scripts/verify_native_runtime.py --runtime-contract --pull-render --scheduled-midi --state-dir temp/work/midi-native-test
```

The C++ native test boots, loads via firmware, checks exact converted displays,
independent instances, state-directory exclusion and scheduled MIDI through
worker PCM. Queue tests additionally compare a supplied captured `.f32` file
without changing any samples. Model queue tests do not establish hardware parity.

## Explicit native VST3 development path

Construct `S760Vst3Plugin(config)` to own a native machine. Its bridge, MIDI
scheduler and PCM renderer use that same machine. The exported factory now uses
this native constructor exclusively; see [production selection](../guides/native-plugin-selection.md).
Historical direct construction remains for diagnostic tests. Missing native
artifacts fail explicitly. Configure
44100/48000/96000Hz float32 stereo with at most1024 frames per block, load through firmware,
then call `setProcessing(true)` off the audio thread. Native input buses are not
advertised; `getState`/`setState` reject rather than saving a different core.

`NativeStream` preallocates128 input packets (64 note events per packet) and32768
PCM frames. The callback copies events with their sample offsets and reads PCM;
all JSON, sockets and emulation run on the worker. Small packets coalesce into
at least2048 native-sample-duration render requests (scaled to host rate) unless the event limit requires an earlier
flush. Rendering never speculates ahead of supplied callback input. The native
renderer runs between video boundaries and pauses when enough PCM is captured;
it preserves surplus, rather than sleeping at every single-video-frame step.

The development clock maps absolute host note positions to native samples using
integer rational conversion and4096 native samples of MIDI lead. Initial padding
is8192 native-sample durations. A worker-side33-tap converter supports48/96kHz;
44100Hz bypass remains exact. Reported software latency is12288/13393/26785 host
samples at44.1/48/96kHz (approximately279ms). Serial, firmware, capture phase and
envelopes add audible delay. See [timing contract and acceptance](native-audio-timing.md).
Changing rate after stream start rejects; same-rate suspend/resume retains queues.
Transport-position seek semantics are not implemented.

Overflow, late scheduler rejection, unsupported events or a missed PCM deadline
latch an observable stream fault. The callback returns failure and silence; stale
audio is never replayed later to hide an underrun. A fault requires a new instance
at this stage. Only note-on/off are supported through this processor API. The
worker retains its bounded backlog and clock over suspend/resume; without callback
input it finishes that backlog and idles. Termination stops the worker and closes
the child. Lifecycle and bridge users must be quiescent before teardown.

Native acceptance commands (requires user-supplied firmware and ROBOFULL):

```powershell
./build/Release/s760_native_stream_tests.exe
./build/Release/s760_native_plugin_tests.exe . docs/ic20-hle-findings/chatGPT-work/plugin-test
./build/Release/s760_native_plugin_tests.exe . docs/ic20-hle-findings/chatGPT-work/plugin-paced --paced
./build/Release/s760_native_plugin_tests.exe . docs/ic20-hle-findings/chatGPT-work/plugin-var --paced-var
python scripts/verify_native_midi_queue.py --state-dir temp/work/midi-queue-test
```

Sixty-second varied64/127/256/511/1024 callback runs pass at44.1/48/96kHz on the
local machine, with exact offline-reference PCM and no missed callback deadlines.
Earlier ten-second fixed256 and varied callback runs also passed at44.1kHz. These call the actual processor class and native MAME, but do not scan
or load the exported plugin in a DAW/SoundCheck. No actual editor lifecycle or
unbounded-duration performance claim follows from this harness.

Graphical configuration, recording input, complete snapshots,
crash recovery of user work and release/distribution qualification remain open.
RapidJSON is the existing vendored MAME dependency; retain its `license.txt`
with any distribution that includes this client.

[Native checkpoint support](native-checkpoints.md) now exists in the shared Lua
runtime and Python client, including pending scheduled MIDI. C++ stream snapshot
primitives now preserve unread PCM, pending blocks/events and clock/padding at a
quiescent boundary. Queue reconstruction is unit-tested; C++/VST3 archive
integration remains open and the native processor still rejects getState/setState.
