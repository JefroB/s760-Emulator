# Native VST3 MIDI controllers

The native instrument exposes the Steinberg `IMidiMapping` interface. Bus0,
channels0–15 map CC0–127 and pitch bend129 to stable, hidden transport parameters.
Aftertouch128 and program changes are not mapped. These aliases carry MIDI into
the original firmware; they do not replace its controller filters or patch settings.

Parameter IDs are `0x760000 + channel*129 + slot`, where CC uses its number and
pitch bend uses slot128. CC values quantize to0–127 and bend to0–16383; center is
8192/16383 normalized. Controller-side values are transport readback, not a query
of every firmware controller state. Hosts must send processor parameter queues;
calling the controller setter alone does not schedule MIDI.

The processor merges note events and controller points into the existing native
sample clock. Stable ordering puts notes before controller queues at equal
offsets; queue enumeration breaks controller ties. Blocks remain float32 stereo,
1–1024 frames, with at most64 combined events. Invalid IDs, values, offsets or
capacity reject the block, clear output and latch the existing stream fault.
Zero-frame controller flushes are not qualified. No new callback allocation,
disk access, UI call or blocking runtime request was introduced.

## Qualification

Independent Steinberg-header tests verify mapping/metadata ABI, all16 channel
assignments, parameter units/text, actual processor queues and overflow rejection.
A12-second paced44.1kHz processor run with64/127/256/511/1024-frame blocks matches
an independent checkpoint render exactly. Reference MIDI bytes specify bend,
volume, sustain, reset and All Notes Off, including channel15 CC123 while channel0
plays. No callback deadline is missed.

SoundCheck1.0.0 Windows x64 native SDK hosting at44.1kHz/512 frames verifies the
original OS2.24/ROBOFULL fixture at20,004Hz. CC7 changes the peak from0.0445375182
to0.0224378761 at64/127 and back. CC64 holds after note-off and releases to zero;
CC123 releases to zero. These are measured audio effects, not just acknowledgments.

The private SoundCheck backend required a repair: its `set_param` command stored
pending changes, but `process_test_chunk` passed a null parameter-change pointer.
The private rebuild now uses real SDK queues. The independent checkout was not
changed. The [reproduction patch](condensed/validation/soundcheck-native-automation-2026-10-12.patch)
also contains the earlier loopback bind and processor-return checks. Apply it to
a private copy of `.soundcheck/server`, configure its local SDK path and build
Release. Send `set_param` with the numeric ID string, then `process_test_chunk`.

## Remaining acceptance

The full Milestone4 MIDI gate stays open. Pitch bend and expression produced no
audible change on this fixture; its patch controller-offset region is zero, but
that alone does not qualify a configured bender response. CC120 did not silence
the held voice. Reset-sustain was already silent before the reset, so that trial
does not prove reset semantics. Other-channel CC120 is likewise not isolation
evidence; the independent CC123 timeline supplies the channel-isolation check.
Use the demonstrated CC123 release path rather than claiming instantaneous
All Sounds Off support. Configured bend/modulation/expression, reset behavior,
broader workloads and other DAWs still need acceptance. Firmware and ROM bytes
were not modified.

See the [text/audio report](condensed/validation/milestone-4-midi-automation-2026-10-12.txt)
and [binary/source evidence](condensed/validation/milestone-4-midi-2026-10-12.json).
