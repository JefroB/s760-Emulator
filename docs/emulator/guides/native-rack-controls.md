# Native rack controls

The Value knob edits the parameter under the firmware cursor. Output Level
attenuates the current Stereo Out 1 signal. Both use the same native runtime
in the standalone and VST3; the approved embedded rack layout is preserved.
Standalone Input Level now controls native recording gain with acknowledged
readback and same-build session recall. The VST knob remains disabled pending
host input routing; physical capture-device selection remains open.

## Evidence and routing

| Control | Source evidence | Implementation |
| --- | --- | --- |
| Value rotation | Owner's Manual Basic 0-6 and 7-10; Service Notes p18 CN10; OS 2.24 bank003B:452D–45A9 | Relative MAME input, read/clear latch at F012; firmware performs the edit |
| Menu | Service Notes p18 CN10 SC0/SP4 | Separate momentary panel switch |
| Output Level | Owner's Manual Basic 0-6; Service Notes p20 VR1 Volume, IC65 phones and IC66 Stereo Out A | Linear software attenuation on the native stereo monitor output, 0–100%; default unity |
| Input Level | Service Notes p20 VR1 Rec Level preceding IC61/IC58 analog conversion | Standalone linear recording gain0–100% before native ADC meter/wave writes; not a firmware parameter or a second Value encoder |

The output control does not change patch/TVA data. The physical manual says it
affects Stereo Out 1 and headphones, not the other outputs. The implementation
currently exposes one stereo monitor stream; this work does not add or qualify
the remaining physical output buses. Linear software gain is not a measured
model of the physical potentiometer taper, analog saturation or noise.

## Value register contract and limits

For the unchanged OS image with SHA256
`3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd`,
bank003B:452D maps to image offset01392D using
`file = 0x4800 + (bank << 10) + (address & 0x3fff)`.
The firmware reads F012, writes zero, and tests two flag/direction pairs.
Bit1 qualifies bit0: values2/3 select firmware events31/30 respectively.
Both flags1/3 set are ignored; a four-scan cooldown follows accepted input.
The second pair is decoded similarly by the firmware but is not exercised
by this single-encoder model.

`S760_NATIVE_VALUE_ENCODER=1` selects the bounded functional latch model;
the native standalone and plugin launchers explicitly enable it. MAME's
`NATIVE_VALUE` relative counter feeds the latch. Reading for debugger inspection
does not consume a detent. A zero write acknowledges a pending latch.
Successive detents are paced at 20ms of emulated time so ordinary host input
does not overrun the firmware cooldown. This is conservative host pacing,
not a measured IC20 timing specification. Rapid opposing input is a net
relative displacement, not a timestamped electrical edge recording.

Native acceptance establishes that positive steps increase and negative steps
decrease the selected value. It does not establish every quadrature transition,
switch-bounce behavior, encoder acceleration or complete IC20 equivalence.
No S1/S2 presses, guest RAM writes, firmware events or opcode changes implement
the rotation; the original firmware translates the peripheral latch itself.

## Transport and state

Public control JSON is `DIAL_DELTA` with `id` equal to `ALPHA` or `VOLUME`
and an integer `delta` in -32..32. Unknown controls, fractional values and
oversized steps are rejected. Runtime operation `dial` uses the same payload.
`ALPHA` adjusts a wrapping 16-bit relative counter; `VOLUME` clamps at0/100.
MAME adjusters require `user_value`, not the digital `set_value` override.

Output readback accompanies direct frames and audio-worker display snapshots.
React uses that confirmed level for the knob position, including editor reopen.
Checkpoint metadata stores the encoder counter and output setting; MAME state
stores the latch and its pacing time. Existing same-build checkpoint constraints
still apply. Additional metadata defaults support older metadata shapes, not
cross-build MAME state compatibility.

## Native qualification

```
python scripts/verify_native_runtime.py --rack-dials --panel-menu --state-dir <private-state>
python scripts/verify_native_runtime.py --panel-menu --pull-render --scheduled-midi --state-dir <different-private-state>
```

The first run verifies Master Level127→126→124→127, checkpoint recall of the
edit and relative position, exact0.5 PCM scaling, exact mute, non-unity state
replay and silent note release. The second separately verifies the monotonic
WAV/PCM timeline and scheduled MIDI. An external WAV writer does not rewind
with guest checkpoints, so these modes cannot be combined.

The C++ native runtime regression exercises public bridge validation and
audio-worker cached50% readback. Unit/React tests complement native acceptance;
none of these results substitutes for physical analog calibration.


SoundCheck's actual SDK host and React/WebView editor qualify Value127→124→127,
output peaks0.04453751817345619 /0.022268759086728096 /0 at100% /50% /0%,
50% readback after editor recreation, restored full-level playback at20,004Hz,
and silent release. See the [qualification record](../../condensed/validation/milestone-2-rack-controls-2026-10-11.json).
This completes Milestone2 playback/UI acceptance for the Windows development
profile. Standalone Input Level is qualified separately below; VST host input
routing remains open.


## Standalone Input Level acceptance

The enabled rack knob sends bounded `DIAL_DELTA` commands with ID `INPUT`.
The native adjuster owns the0–100% value and reports it through firmware-status
packets; React waits for acknowledgement before moving its value indicator.
Input and Output levels are independent. Recording gain is applied when queued
stereo PCM is consumed, before meter values and recording wave-memory writes.
Each signed input sample becomes `s16(s32(sample) * level / 100)`, with integer
division toward zero. Default100% preserves PCM;50% halves it;0% mutes recording.
The callback uses bounded existing storage and performs no new allocation or I/O.
This is linear software gain, not a calibrated analog potentiometer/ADC model.

Checkpoint metadata preserves input gain independently of output volume and
restores the native adjuster before rendering resumes. Native tests cold-restore
an armed sampler after deliberately setting the replacement process's gain to
zero, then record at the restored value. Both independent channel patterns match
every expected sample at100%,50% and0%, with Output Level muted. The resulting
firmware Sample Save/export and fresh Sample Load preserve all allocation bytes;
all three runs report zero recording underruns. Source and packaged browser
checks verify knob readback, reconnect and saved-session restoration.322 backend
and119 React tests plus five shared-shell checks pass; default-off native replay
is bit-identical to the prior binary for132,300 stereo frames and both displays.
[Input Level qualification](../../condensed/validation/native-input-level-2026-10-12.json).

Physical recording-device selection, negotiated capture rates, realtime input
timing/dropouts, analog pot taper/headroom and VST host input routing remain open.
The experimental offline ADC profile remains disabled by default. The standalone
knob retains a valid gain setting even when no input source is connected.
