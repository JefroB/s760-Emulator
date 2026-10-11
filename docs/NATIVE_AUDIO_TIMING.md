# Native host audio timing

The explicitly configured C++ native processor supports float32 stereo at
44100, 48000 and 96000 Hz, with 1–1024 frames per callback. MAME stays at
44100 Hz. The production factory, native recording input and complete plugin
state remain separate roadmap work. This is processor-harness qualification,
not a DAW, audio-interface or physical-hardware latency measurement.

## Clock and conversion

The worker maps an absolute host event position `h` to
`capture_origin + ceil(h * 44100 / host_rate) + 4096` native samples. Rounding
is less than one native sample and never schedules early. Integer positions
avoid accumulated block rounding. Note-on and note-off are supported; controller
and transport-seek semantics are not established by this test.

44100 Hz is a bit-preserving bypass. The other rates use a continuous rational
phase, 33-tap Blackman-windowed sinc converter with 16 native samples of delay.
Construction allocates the phase table before processing; conversion, sockets,
JSON and native rendering run on the worker. The callback copies bounded events
and PCM through preallocated queues. Output padding and worker batch targets
scale with host rate, preserving their duration and fitting the fixed queues.

| Host rate | Initial zero frames | Reported software latency (frames) |
| --- | ---: | ---: |
| 44100 | 8192 | 12288 |
| 48000 | 8917 | 13393 |
| 96000 | 17833 | 26785 |

The approximately 279 ms reported latency includes output padding, MIDI lead
and converter delay. Serial transmission, guest firmware, capture phase and
envelope response add observable onset delay. It is not a calibrated total
MIDI-to-analog latency. Low-latency product acceptance remains open.

Once a stream starts, changing its rate rejects explicitly, including while
suspended. Create a new instance for a different rate. Same-rate suspend/resume
retains the pending queues and clock. Queue overflow or a missed render deadline
latches a fault and returns silence; stale PCM is not replayed to conceal it.

## Reproduction and acceptance

Supply the original boot ROM, OS 2.24 and ROBOFULL disk under the configured
`roms` paths. Build the Release C++ targets, then run from the repository root:

```powershell
./build/Release/s760_native_rate_converter_tests.exe
./build/Release/s760_native_plugin_tests.exe . docs/ic20-hle-findings/chatGPT-work/timing44 --paced-var 44100 60
./build/Release/s760_native_plugin_tests.exe . docs/ic20-hle-findings/chatGPT-work/timing48 --paced-var 48000 60
./build/Release/s760_native_plugin_tests.exe . docs/ic20-hle-findings/chatGPT-work/timing96 --paced-var 96000 60
```

The native test boots and loads through firmware, saves a paused checkpoint,
restores it into a separate reference child, and renders offline. It then drives
the original processor at wall-clock deadlines with 64/127/256/511/1024-frame
callbacks, holding a note until two seconds before the end. Every output sample
after initial padding must equal the offline native reference. It also checks
scheduled note offsets, silent release, display conversion, independent children,
rate rejection, suspension and termination. The reference shares the converter;
independent analytical tone and impulse tests establish conversion accuracy.

Converter tests cover 100, 1000, 10000 and 18000 Hz, independent stereo impulses,
block partition invariance and a ten-minute integer event-clock sweep. The worst
tested tone RMS error is 0.0184%; that is a converter measurement, not proof of
hardware DSP parity or the entire Nyquist band.

The [acceptance record](condensed/validation/native-audio-timing-2026-10-11.json)
contains artifact identities and local measured deadlines. Results qualify these
rates, callback patterns and workload on the recorded machine. They do not
guarantee deadlines under arbitrary CPU load, plugin hosts or audio drivers.

## Separate checkpoint issue

During reference setup, rewinding the already-rendered process to a checkpoint
saved before capture could produce `Audio overflow during render`, reproduced
at both 44100 and 96000 Hz. Restoring that checkpoint into a fresh child works.
This limits in-process rewind; it does not invalidate the earlier capture-enabled
scheduled-checkpoint cases. Full snapshot integration remains open and must
cover this capture-start/rewind sequence before exposing it as plugin state.
