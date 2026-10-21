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

This is a retained stimulus recipe, not a new capture request. Consult the dated [resonant-filter comparison](resonant-filter-control-results.md) for later results and remaining limits.
