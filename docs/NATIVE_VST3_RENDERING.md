# Native VST3 rendering

The native instrument supports realtime (0), prefetch (1) and offline (2)
processing modes at 44.1, 48 and 96 kHz. Negotiate the mode with
`setupProcessing` while processing is stopped; each nonempty `ProcessData`
block must use that mode. Unknown modes are rejected. A running native timeline
still cannot change sample rate; use a fresh instance for a different rate.

Realtime and prefetch calls retain the bounded, nonblocking worker transport.
Offline calls may wait for worker PCM and packet-queue space, allowing hosts to
render without wall-clock pacing. A full queue of tiny blocks requests a partial
worker batch. Each wait has a ten-second limit; runtime failures or timeouts
reject processing with cleared audio rather than returning a successful bounce
containing missing samples. Emulation, filesystem and socket operations remain
on the worker. Offline processing is not subject to a realtime callback deadline.

Suspension retains the sample clock, queued PCM and pending MIDI. The worker may
finish a finite backlog before idling. Resuming the same instance preserves the
timeline; it does not reboot firmware or discard sustained voices.

## Host reporting

The supported instrument advertises one stereo output, one 16-channel event
input and one optional, inactive-by-default stereo audio input. Input is qualified
at44.1kHz through the native ADC; the FX class remains unadvertised. See
[host sampling](NATIVE_VST3_SAMPLING.md).
`getTailSamples()` returns SDK `kInfiniteTail` because held or looped voices have
no finite duration bound. This is a maximum-tail declaration; note-off can still
release a particular voice to silence.

| Host rate | Reported latency samples |
| --- | ---: |
| 44,100 Hz | 12,288 |
| 48,000 Hz | 13,393 |
| 96,000 Hz | 26,785 |

These reports cover transport delay, MIDI scheduling lead and rate-converter
delay, approximately 279 ms. They exclude the audio device and firmware-specific
note response. First audible PCM is recorded separately; it is not assumed equal
to the declared latency.

## Qualification and limits

SoundCheck 1.0.0 Windows x64, using the private Steinberg SDK QA adapter, renders
221,184 frames at 44.1 kHz with 512-frame blocks. From the same real plugin state,
realtime playback with a 1.5-second suspension during a held note and an unpaced
offline bounce match sample-for-sample. Note-off releases to zero. Original
OS 2.24 and ROBOFULL media are used without firmware or RAM modifications.

Native processor tests also compare unpaced offline PCM to independent native
checkpoint rendering at all three supported rates with varying 64/127/256/511/
1024-frame blocks. Worker tests cover unpaced 1024-frame and one-frame blocks.
An independent Steinberg-header probe checks negotiated latency, infinite tail
and rejection of an unknown process mode.

The QA adapter adds explicit mode, suspend/resume and in-memory state commands;
the independent SoundCheck checkout is unchanged. Its reproducible patch is
included with the [validation record](condensed/validation/milestone-4-rendering-2026-10-12.json).
SoundCheck's amplitude-threshold “dropout” flag counts intended silent blocks;
it is not used as evidence of transport loss. Exact PCM comparison and processor
return values determine this acceptance result.

This closes the scoped host output-rendering gate. Host ADC/input sampling has
separate acceptance. The accepted SoundCheck project-runner profile now has
[separate cold-project acceptance](SOUNDCHECK_PROJECTS.md); other DAWs and
arbitrary crash recovery remain unqualified. The rendering test
snapshot supports this render comparison; it is not a real DAW save/reopen test.

## Reproduction

Build the normal Release targets, then run `s760_native_plugin_tests.exe ROOT
PRIVATE_STATE --offline RATE 3` for each supported rate, with a fresh private
state directory. `--paced-var 44100 12` checks the realtime path against the same
independent reference. Run `s760_native_stream_tests.exe` for offline packet
backpressure. The optional `s760_vst3_sdk_tests.exe MODULE` target requires the
local Steinberg SDK and normal native firmware configuration.

For SoundCheck, apply the validation patch to a private copy of its server and
configure the SDK path. Load the exact module, boot user-supplied firmware and
load ROBOFULL through the original firmware Disk Load screen. Keep processing
512-frame realtime blocks throughout startup. The added `qa_processing` command
takes `instanceId` and `action`: `report`, `save`, `restore`, `suspend`, `resume`
or `mode` (with numeric `mode`). It reports latency, tail, buses and mode. Save
the loaded instance state, then capture 432 one-block `process_test_chunk`
responses with note 60/velocity 127 at block 0, explicit note-off at block 258
and `autoNoteOff:false`. Pace realtime calls, suspend after block 180 for 1.5
seconds without processing, then resume. Restore the snapshot, select mode 2
and repeat the same blocks without sleeps. Compare every returned PCM sample,
assert finite output and silence over the final 22,050 frames, then remove the
plugin before closing the host. Save and restore are test snapshots held in the
QA host, not simulated audio or firmware edits.
