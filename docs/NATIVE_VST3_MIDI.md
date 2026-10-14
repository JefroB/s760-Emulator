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

Configured audible bend is now qualified in SoundCheck1.0.0 Windows x64 at
44100 Hz/512 frames. Using only original firmware controls, set Patch Control
**Bend Up** and **Bend Down** to12 on ROBOFULL patch01. Through actual host
parameter queues, centre measures20004Hz, high bend4108Hz (the high source tone
folds into the output band), low bend10002Hz, and centre restoration20004Hz.
Note release reaches exact silence. The earlier fixture's displayed ranges
were both0; its unchanged bend was not evidence of broken transport.
This is audible-effect acceptance in one native profile, not hardware pitch,
resampling/alias or amplitude fidelity across all notes/ranges.

The repeatable verifier edits the ranges through the authentic CRT/Value control,
measures native host PCM and asserts both directions, centre return and release:

```powershell
python scripts/verify_vst3_configured_bend.py --host <private-SoundCheckServer.exe> --module <WebView-Roland_S760.vst3> --state-dir <new-private-directory>
```

Use the [private QA host patch](condensed/validation/soundcheck-project-qa-2026-10-13.patch)
and the same prerequisites/port ownership as the [project verifier](NATIVE_PLUGIN_STATE.md).
[Configured-bend and reset evidence](condensed/validation/milestone-4-configured-bend-2026-10-13.json).

## Completed controller and panic/reset profile — 2026-10-13

The current-artifact55-case requalification also passes unchanged. One preceding
run rejected an audio block while editing the assigned controller; BUG-060 tracks
that intermittent failure and remains open. The successful repeat establishes
controller effects for this profile, not failure-free host reliability.
[Current artifact hashes and measured results](condensed/validation/milestone-4-controller-requalification-2026-10-13.json).

The remaining controller objective is complete for SoundCheck1.0.0 Windows x64
native SDK hosting at44100Hz/512 frames with original OS2.24/ROBOFULL. The
55-case matrix measures native PCM effects and recovery, with separate left/right
peak measurements. The C++ native launcher now enables the existing firmware
stereo coefficient path (BUG-056); it previously bypassed pan and returned
identical channels. No DSP algorithm or firmware bytes changed. Stereo centre
level consequently differs from older mono-profile recordings.

| Behavior | Qualified result |
| --- | --- |
| Configured bend | Firmware Up/Down12: centre20004Hz, folded high4108Hz, low10002Hz, restored centre and silent release |
| Configured expression | Patch Ctrl Select11 / TVA Control+63: CC11=127/64/0 gives descending levels;127 restores the level |
| Assigned modulation | The same TVA control assignment with Ctrl Select1 gives descending CC1=127/64/0 levels and restoration; this tests an assigned gain effect, not LFO vibrato fidelity |
| Volume | CC7=64/127 gives0.50387 of the full-volume peak with expression configured |
| Pan | CC10=0/127 before note-on routes the next note left-only/right-only;64 returns equal centre channels |
| RPN0 | Ordered CC100=0,101=0,6=2,38=0 sets a two-semitone range; high21654Hz folded, low17822Hz, centre20004Hz |
| RPN null | CC100=127,101=127 prevents subsequent Data Entry from changing that range |
| Sustain/channel modes | CC64 holds after note-off; pedal up releases. CC123–127 each release a fresh note with pedal up |
| Panic | A32-message all-channel pedal-off/All Notes Off macro releases the held fixture; subsequent notes still play |
| Neutral reset | A64-message all-channel modulation/expression/pedal/bend reset releases a sustain-held fixture and restores a fresh note to centre |

The primary behavior reference is Roland *S-760 MIDI Implementation*, v1.00,
1993-11-18, pages1–3 (see [manual inventory](05-manuals.md)). It documents
assignable controls0–95, RPN0, Hold1 and CC123–127. Its All Notes Off description
preserves damper-held notes until pedal release. It does not list CC120 or CC121;
both are observed ignored by this original-firmware profile. **Raw CC120 All
Sounds Off and CC121 Reset All Controllers are explicitly unsupported.** They
are not silently translated or advertised as modern hard-kill/reset commands.

Use these explicit supported-message sequences, with values shown as MIDI7-bit
integers (bend is14-bit):

- **Panic:** for each channel, send CC64=0 followed by CC123=0. This releases
  notes through firmware envelopes; it is not an instantaneous host hard mute.
- **Neutral controllers:** for each channel, send CC1=0, CC11=127, CC64=0 and
  pitch bend8192. This resets those inputs, not arbitrary patch assignments,
  EQ, RPN tuning, bank/program or all firmware settings. Volume and pan are
  retained. It releases an already note-off/sustain-held voice; held keys are
  released separately with the panic sequence.

The tested all-channel bursts contain32 and64 controller points. The existing
64-combined-event callback bound still applies: send the reset in a block with
no other events, or split it across blocks. Notes precede controller queues at
equal offsets. Pan is latched on note start in this fixture, so send pan in a
preceding block. RPN controller messages are also sent in ordered distinct
blocks; host queue enumeration at equal offsets is not wire-message ordering.

```powershell
python scripts/verify_vst3_controllers.py --host <private-SoundCheckServer.exe> --module <WebView-Roland_S760.vst3> --state-dir <new-private-directory>
```

Build the private SDK host with the [controller QA adapter patch](condensed/validation/soundcheck-controller-qa-2026-10-13.patch).
The verifier boots/loads through original controls, configures patch assignments,
uses real SDK parameter queues, checks both channel peaks and keeps captures
private. It requires the same original local fixtures, Python packages and free
ports as the earlier bend verifier. Separate paced44.1/48/96kHz exported-module
runs reproduce independent native reference PCM exactly with zero missed
callback deadlines;48kHz cold state replay matches240000 stereo frames. Core/
plugin tests,354 backend regressions and the original native runtime verifier pass.

This closes controller qualification for this supported native profile. Other
DAWs, aftertouch/program/SysEx mapping, LFO/tuning/gain-law hardware fidelity,
arbitrary controller combinations and an immediate hard-kill extension are not
claimed. Old-build snapshots intentionally reject after a module rebuild; the
state format and same-build constraints are unchanged.
[Source/binary identities, metrics and limits](condensed/validation/milestone-4-controller-semantics-2026-10-13.json).

See the [text/audio report](condensed/validation/milestone-4-midi-automation-2026-10-12.txt)
and [binary/source evidence](condensed/validation/milestone-4-midi-2026-10-12.json).
