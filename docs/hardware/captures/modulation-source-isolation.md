# MIDI73 sample-source isolation — 2026-10-15

The nearly opposite MIDI73 RMS ripple can largely be explained by the signal entering the filter. No envelope-speed or filter-equation change is needed to reproduce that particular symptom in these offline diagnostics. This is a supported candidate explanation, not a production fix or full modulation-parity result.

## Controlled prediction

Apply the unchanged native LP transfer function to the hardware bypass recording, retaining the recording-band spectrum. It predicts the hardware static80 ripple with0.165dB raw RMS-curve error over1.5–2.7s (0.149dB after freezing a0.055dB gain offset fitted on0.2–1.2s). No filter parameter or time fit is applied. Native bypass similarly predicts native static output. Thus opposite input-dependent ripple does not require differing cutoff motion.

At MIDI73, native pitch word34716 gives step2.118896484375 and source fundamental22.8133142Hz for the4096-sample noise loop. Source harmonics18,1915 and1951 fold to410.640,412.503 and408.776Hz. The adjacent lines are1.864Hz apart, explaining a slow audio beat without a slow LFO or envelope oscillation.

## Source candidate

The renderer uses its linear fallback above pitch word32768. Compare four source hypotheses using the existing fixed cubic B/C kernel,128 phases and existing inverse normalization. No kernel or filter coefficients are fitted. An effective one-source-sample initial phase change is tested separately; it is not claimed as proven literal hardware addressing semantics.

| Source model | Effective source offset | Bypass waveform evaluation error,30–1500Hz |
| --- | --- | --- |
| Linear |0|72.38%|
| Existing cubic kernel |0|51.30%|
| Linear |1|31.80%|
| Existing cubic kernel |1|7.59%|

Each candidate fits only one constant gain and delay on bypass0.2–1.2s, with a common+21.5ppm source-clock ratio estimated from bypass harmonics. Evaluate1.5–2.7s with those values frozen. These are time-window evaluations within recordings already inspected, not independent validation. The0/1 source phase choice was informed by the MIDI73 discrepancy.

The combined candidate predicts static RMS within0.146dB and moving RMS within0.086dB over the evaluation window. Moving prediction retains the actual native cutoff activation trace and unchanged recurrence; no moving-recording gain/delay/timing fit is made.

| Additional MIDI key | Moving RMS prediction error (dB) |
| --- | --- |
|74|0.130|
|75|0.104|
|76|0.206|

Those additional keys use original survey captures and freshly observed native trajectories. Neither reconstruction nor calibration is adjusted per key. Native linear source/filter replay reproduces their actual native PCM to about5e-8 relative RMS, validating the offline recurrence and trace interpretation. The additional keys were not used to choose the source candidate, but all captures remain from the same survey session.

## Limits and remaining work

The [original resonant sweep investigation](resonant-filter-control-results.md) now separates this source confound from control application. At unity pitch, the enabled source candidate changes the phase-aligned native sweep only0.554%. Separate stationary LP controls agree within0.14%, while held versus interpolated actual native cutoff points give44–46% versus19–21% moving diagnostic errors with the independently measured clock frozen. This supports investigating causal cutoff transitions next; it does not establish hardware interpolation or close BUG-005.

### Native experiment and filter rechecks

The candidate is now implemented behind `S760_NATIVE_SOURCE_CANDIDATE`, off by default, exposed by the diagnostic verifier's `--source-candidate`. It shifts reconstruction reads without moving the address accumulator or loop comparator and extends the existing cubic kernel above pitch word32768. Supported44.1kHz forward loops only; half/quarter-speed special kernels are excluded. Release mode0 uses the existing path, so release continuity and general playback remain unqualified.

Disabled behavior matches the saved executable across1,543,500 stereo frames exactly at MIDI60/72/73/77/83. Enabled behavior matches the offline candidate within5.05e-8 relative RMS. On/off firmware control and coefficient-application trace fields are identical. Full backend regression:404 passed, no skips; C++ core/plugin suites pass; native bus-trace regression preserves131072 exact PCM frames and both displays.

Using the newly observed enabled cutoff traces, the same hardware waveform prediction gives4.24/6.08/4.68/5.67/7.63% relative RMS error at MIDI60/72/73/77/83, respectively. These differ slightly from the earlier offline rows because fresh boot/checkpoint timing changes the observed control trajectory. Gain/clock remain frozen from bypass; constant alignment is trained per recording as before. [Enabled-trace hardware prediction](../../condensed/validation/modulation-native-source-hardware-2026-10-15.json).

The existing static BP/HP analysis passes again at0.07924%/0.10408% waveform error. Repeating the original resonant moving-filter analysis reproduces17.898%/18.038% error with Fourier excitation alignment. That older unity-source numerical test does not invoke the native flag, and these results are not an enabled-native resonant acceptance test. The source experiment leaves the filter recurrence unchanged; it does not resolve the original resonant mismatch. BUG-005 stays OPEN.

[Native experiment checks and executable hashes](../../condensed/validation/modulation-native-source-2026-10-15.json).

### Waveform discrimination with shared calibration

Five selected moving captures were compared in30–1500Hz using the same MIDI73 bypass gain and clock for all four source models. Each model fits only one constant recording offset on0.2–1.2s, searching±50ms; later1.5–2.7s is evaluated without refitting. No cutoff timing or filter parameter is adjusted. This is diagnostic alignment, not absolute latency acceptance.

| MIDI | Cubic, phase1 | Linear, phase1 | Cubic, phase0 | Linear, phase0 |
| --- | --- | --- | --- | --- |
|60|4.18%|4.18%|4.17%|4.17%|
|72|4.30%|72.76%|62.53%|130.96%|
|73|4.60%|36.52%|51.45%|86.23%|
|77|5.77%|32.43%|30.11%|49.85%|
|83|7.67%|31.16%|33.20%|49.77%|

These are relative waveform RMS errors with fixed bypass gain, not earlier RMS-envelope errors in dB. The combined cubic/phase1 candidate wins clearly at the non-unity keys. Unity MIDI60 cannot distinguish these models: interpolation normalization preserves unity playback, and a source-sample shift is absorbed by recording alignment. This controlled comparison removes the different-model-gain confound from the earlier envelope rankings.

Candidate constant offsets range−6.78 to+3.00ms across these takes, versus+0.277ms in bypass. Consequently, a global bypass alignment fails waveform comparison, and these offsets cannot establish a hardware modulation delay. Residual waveform error remains4–8%; the result supports an opt-in source experiment, not a production fix or full modulation parity.

[Waveform rows, calibration, search limits and hashes](../../condensed/validation/modulation-source-waveform-2026-10-15.json).

### Wider frozen-calibration check

Twenty-three additional/previously checked survey keys selected across MIDI49–95 give0.067–0.441dB moving RMS-curve error with the MIDI73 bypass calibration frozen. The selected notes are49,53,57,60,61,65,69,72,74–85,89,93,95. MIDI73 remains the calibration case and is excluded from this23-key result. Each replay uses its actual native cutoff activation trace; no hardware moving-recording gain, delay or timing is fitted per key. Native baseline replay matches each rendered waveform within5.05e-8 relative RMS, including the existing cubic path below the fallback boundary and unity playback at MIDI60.

Native pitch word reaches65510 at MIDI84 and remains there for tested85,89,93,95. Those upper keys exercise different envelope settings but do not extend source-speed coverage beyond that cap. This observation does not establish a hardware pitch defect. MIDI35–48, unselected notes and exact half/quarter-speed special kernels remain untested here.

This supports transfer of the combined source/calibration candidate across the survey. It does not independently prove the effective source phase: the four comparison models retain different gains/delays fitted on MIDI73 bypass, so their RMS rankings do not isolate phase or interpolation individually. Waveform comparison, capture-origin metadata and independent-session validation remain necessary before a production correction.

[Full selected-key rows, native replay checks and artifact hashes](../../condensed/validation/modulation-source-wider-2026-10-15.json).

RMS-level agreement is not waveform or envelope-time qualification. With bypass-only global alignment, the candidate static raw waveform still has132% relative RMS error. A separately reported diagnostic fit requires an additional2.846ms static delay and then leaves3.05% waveform error. That extra offset cannot currently be assigned to hardware signal-path latency versus RoboSampler recording alignment and is not acceptance evidence.

Machine status time also cannot be assumed to mark WAV sample0. In the original case, exact source replay places the first source sample at WAV7483 rather than status-inferred6602:881frames, about19.98ms. Older overlays remain illustrative and cannot establish absolute trigger latency; peak-to-valley intervals are unaffected by a constant origin error.

BUG-076 is repaired (2026-10-17): native speaker hooks now export observed absolute PCM frame positions; the modulation verifier records the WAV-to-stream mapping and rejects missing or discontinuous metadata. A fresh five-case capture reproduces the881-frame error in its first case and146-frame offsets in subsequent cases. All four filtered cases map their first native source-trace frame to the WAV exactly, with the expected one-frame LP recurrence startup and no fitted alignment. Varied pulls, capture reset and buffered checkpoint replay also preserve the mapping. This qualifies native capture indexing, not physical hardware latency or a change to the filter/source model. [Observed origins, trace rows and identities](../../condensed/validation/bug076-pcm-origin-2026-10-17.json).

Keep the original resonant moving-filter bug OPEN. Next engineering work is broader source-phase/interpolation validation before considering a native correction; observed native PCM-origin metadata is now available. This evidence does not qualify arbitrary pitch, physical bus timing, LFO, TVA release or the full test plan. No more hardware capture is required for this analysis stage.

[Exact hashes, parameters, candidate rows and limitations](../../condensed/validation/modulation-source-isolation-2026-10-15.json).
