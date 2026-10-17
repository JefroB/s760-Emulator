# TVFSTEP — analog capture kit for BUG-005

## Recommended: seven-channel kit (2026-10-16)

Use `tests/hardware_recordings/TVFSTEP_7CH_CAPTURE.zip`: it contains the paired
`TVF7CH.IMG`, `TVFSTEP_7CH_CAPTURE.mid`, setup instructions and verified performance
screen. This supersedes the single-channel/program-change workflow below for
Ableton captures. Load the **TVF STEP** performance from the new image.

| MIDI track / output channel | Performance patch |
| --- | --- |
| 1 | BYPASS |
| 2 | LOW HOLD |
| 3 | HIGH HOLD |
| 4 | STEP UP |
| 5 | STEP DOWN |
| 6 | RAMP UP |
| 7 | RAMP DOWN |

Import as seven separate MIDI tracks, align them at the same Arrangement start,
and preserve leading rests. Set tempo to120BPM and explicitly route each track
to the S-760 port and its named output channel. Leave clip Bank/Sub/Program unset;
disable looping and transposition. Record the entire3min7sec run without trimming,
effects or normalization. Note60/velocity127,12second holds and repeated takes
are unchanged. No program changes occur in this MIDI file.

The original-firmware UI/Save probe confirms part2/channel14 changes the high
nibble at4E30 from0 toD and the enable bit at4E41 from7F toFF in this template.
The new image changes only10 performance-routing bytes: packed channel nibbles
at4E30..4E33 and receive enables at4E41..4E46. All patch/partial/sample/PCM bytes
remain identical. A fresh native Load displays channels1..7 and all11 channel-only
takes pass: stationary words416/2613, six delayed steps, two ramps, silent release,
no clipping/nonfinite PCM, no dropped traces and64512 exact loaded sample bytes.
The MIDI independently passes type1/seven-track/channel/timing checks and contains
zero program changes. This verifies the capture stimulus, not hardware parity.
[Validation](../../condensed/validation/tvfstep-multichannel-2026-10-16.json).

Rebuild with `python scripts/build_tvf_transition_capture.py --multichannel --out-dir <fresh-folder>`;
the existing native verifier detects the channel layout from `capture-sequence.json`.

## Original single-channel kit

Use the same analog recording path as your earlier S-760 captures. Keep sampler output level, interface gain and recording sample rate unchanged between takes. Record raw WAV without normalization, compression, noise gating or trimming.

1. Copy **TVFSTEP.IMG** to the Gotek. Boot the sampler with your normal OS disk, then insert TVFSTEP and use Disk > Load to load its **TVF STEP** performance. Return to Perform.
2. Check the loudest patches (HIGH HOLD and STEP DOWN) and set recording gain so peaks have comfortable headroom (around -18 to -12 dBFS). Keep that gain fixed for the entire session.
3. Start analog recording, then play **TVFSTEP_CAPTURE.mid** into the S-760 on MIDI channel1 at120BPM, without transposition. It takes **3 minutes7 seconds**. Leave a little recording space before and after it. Keep the original WAV and any capture-tool metadata.

The MIDI file selects all seven patches, plays MIDI note60 at velocity127 for12seconds, and allows4seconds for release. It then repeats STEP UP and STEP DOWN twice more: three takes of each step. Program numbers in MIDI are zero-based; the display numbers below are one-based. Slots08–22 are labelled UNUSED and are outside this capture matrix; ignore them.

| Display | MIDI program | Patch | What it provides |
| --- | --- | --- | --- |
| 01 | 0 | BYPASS | Known repeated noise, filter bypassed |
| 02 | 1 | LOW HOLD | Constant low endpoint |
| 03 | 2 | HIGH HOLD | Constant high endpoint |
| 04 | 3 | STEP UP | Small downward lead-in, then a large upward cutoff change |
| 05 | 4 | STEP DOWN | Small upward lead-in, then a large downward cutoff change |
| 06 | 5 | RAMP UP | Slower opening transition across the same endpoints |
| 07 | 6 | RAMP DOWN | Slower closing transition across the same endpoints |

If recording individual patches in your existing capture tool, use the same note/velocity,12second hold and4second release. Record01–07 once, then04/05 twice more. Preserve their names and take numbers. The octave name for MIDI60 varies between programs; use the numeric note.

The delayed steps occur near7.6seconds in the native emulator. Hardware timing is what this experiment measures, so keep the full held note rather than editing around an expected time. The lead-in changes the envelope by one level; it is deliberately small, not a perfectly flat delay. LOW/HIGH HOLD are the separate steady references. All filtered cases use resonance64; all LFO depths and velocity sensitivities are disabled, and all seven use identical known noise PCM.

This is a **720KB /737280-byte sample disk**. Use it directly on Gotek; do not run a1.44MB system-disk repacker on it. The disk contains a locally supplied template and stays out of source distributions. Your original template, OS and boot ROM were preserved.

## Native verification and reproduction

All11 original-firmware/MIDI takes pass: no clipped/nonfinite native PCM, silent release, complete read-only cutoff traces, both steady controls constant, repeated steps at7.58–7.60seconds, matching step/ramp endpoints and64512 exact loaded allocation bytes. These are native stimulus checks, not a claim that hardware response already matches. Native float WAV references are in the private pack's native-reference folder; the compact ZIP omits those large files.

The native steady cutoff words are416 and2613. Three step-up writes jump416→2613; three step-down writes jump2613→416. These measured words are native evidence only; no hardware timing or waveform fit is assumed.

Build with `python scripts/build_tvf_transition_capture.py --out-dir <fresh-private-folder>` and verify with `python scripts/verify_tvf_transition_capture.py --pack <folder> --state-dir <fresh-native-state>`. The canonical builder is `scripts/build_sample_disk.py`; explicit TVF envelope levels are at partial+0x52 and times at+0x56 (JSON rates). BUG-073 corrects the old helper's reversed mapping, confirmed against the firmware TVF screen. Implicit legacy presets retain their established bytes.


## Ableton Live capture setup

Live sends one Bank/Program Change per clip when that clip launches; use separate clips with explicit Program settings to change patches within this capture sequence. One MIDI track routed to channel1 is sufficient, but importing the full sequence as one clip does not establish that all embedded program changes will play. See [Ableton program-change guidance](https://help.ableton.com/hc/en-us/articles/209070489-Sending-Program-Change-messages-from-Ableton-Live).

For11 successive clips, the intended display patch sequence is1,2,3,4,5,6,7,4,5,4,5. Confirm the actual S-760 patch name before recording the full run. Alternatively, select each named patch manually and record12seconds held plus4seconds release per take. The MIDI note remains60, velocity127.

The first Ableton recording, `3-Audio 0001 [2026-10-16 054040].wav`, contains11 correctly spaced notes in a48kHz/24-bit mono recording, with no full-scale clipping. However all intended patches have essentially identical level and spectrum, with no expected step/ramp contrasts. Program changes apparently did not take effect; actual hardware patch state was not recorded. This take cannot identify filter transitions. [Integrity and per-take measurements](../../condensed/validation/tvfstep-ableton-capture-2026-10-16.json).


## Slow-ramp repeatability follow-up (2026-10-16)

The accepted capture and exact-firmware audit leave one slow take per direction. Before choosing a timing correction, record `tests/hardware_recordings/TVFSTEP_RAMP_REPEAT/TVFSTEP_RAMP_REPEAT.mid` using the existing TVF7CH disk and performance unchanged. The MIDI contains three tracks; explicitly route CH1 BYPASS to channel1, CH6 RAMP UP to channel6, and CH7 RAMP DOWN to channel7. Keep the tracks aligned at the same Arrangement start and silence the old capture tracks. Tempo120 BPM, no program changes.

Record the full136seconds plus surrounding silence: bypass, up, down, down, up, up, down, bypass. Use the previous audio connection and fixed gain; no effects or normalization. Save the untrimmed WAV in `tests/hardware_recordings/`, preferably `TVFSTEP_RAMP_REPEAT.wav`. The companion README and sequence JSON contain exact note times. MIDI readback verifies eight notes, correct channels and duration; the reordered sequence reuses already qualified patches but has not itself been fully replayed natively.


Repeat capture received and accepted: `1-Audio 0001 [2026-10-16 064504].wav`. All8 takes are present; the repeated closing mismatch and cross-recording diagnostic transfer are recorded in [the repeat analysis](../../condensed/validation/tvfstep-repeat-hardware-2026-10-16.json). No repeat recording is currently needed.
