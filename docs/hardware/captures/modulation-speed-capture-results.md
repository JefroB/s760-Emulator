# TVF modulation speed survey â€” 2026-10-15

Six complete midrange falls broadly track native timing, but MIDI73 has an unresolved near-antiphase periodic audio mismatch. The initial overall overlay conclusion was too broad; this survey does not establish modulation parity. No DSP or emulator timing change was made. BUG-005 remains OPEN for moving/resonant filter response.

RoboSampler metadata records MIDI35â€“95, every semitone, velocity127, 3000ms held and3000ms tail. The pack contains stereo48kHz WAVs plus SFZ; analysis uses WAV channel1 directly, without SFZ volume or envelope adjustments. Numeric MIDI metadata takes precedence over ambiguous octave labels. Sixteen distinct TVF Time settings are covered (4 through112), with six midrange settings completing a measurable first fall in the held interval. These captures are useful and do not require repeating at this stage.

| TVF Time | Hardware fall, median across four pitches (s) | Native cutoff fall (s) | Difference (ms) |
| --- | --- | --- | --- |
| 16 | 0.2325 | 0.2386 | -6.1 |
| 24 | 0.3825 | 0.4002 | -17.7 |
| 32 | 0.5525 | 0.5604 | -7.9 |
| 40 | 0.6900 | 0.7214 | -31.4 |
| 48 | 0.9600 | 0.9821 | -22.1 |
| 56 | 1.3000 | 1.3027 | -2.7 |

Hardware fall is the interval from the first smoothed RMS maximum to the following minimum. Native fall is the interval from the first cutoff2613 endpoint to the following416 endpoint. Measuring an interval avoids assuming a hardware WAV start offset. Hardware medians differ by roughly3â€“31ms. Individual pitch-dependent carrier beating and audio/filter/smoothing delay affect extrema; these numbers do not establish a systematic speed error. Same-note native audio landmarks also differ by tens of milliseconds with mixed signs. Gain-centered plots track the larger envelope trajectories closely. These are exploratory comparisons, not independent held-out accuracy qualification.

Time64 and slower do not complete the first fall within3seconds, so their held traces are partial measurements. Fast settings4/8/12 approach the15ms smoothing resolution and are excluded from duration inference. The short TVA release makes this fixture unsuitable for fully qualifying slow TVF note-off behavior. LFO speed and TVA speed are not covered. Nonresonant LPF results cannot close the prior resonant moving-filter bug.

Reproduction and exact source identities are in [validation](../../condensed/validation/modulation-speed-survey-2026-10-15.json). Private analysis retains all61 waveform audits,16 native references/cutoff traces and hardware/native overlays. Native stimulus uses original firmware Load and MIDI only, with CC7/CC10 initialized; read-only trace capacity is increased in a private Lua copy. No guest state is forced.

Static capture regression rerun: PASS. Corrected held-out BP RMS error 0.07924%, HP 0.10408%, with unchanged cutoff428/damping85. This confirms the existing stationary baseline only; moving/resonant mismatch remains open.

## MIDI73 correction

MIDI73/Time72 has nearly opposite periodic fluctuations. Over0.2–2.8s, exploratory detrended RMS fits yield hardware1.874Hz/0.744dB and native1.851Hz/1.312dB, with phases nearly opposite relative to the plotted waveform origins. Overall rise slopes are similar (2.924 versus2.885dB/s), but this does not explain or dismiss the mismatch.

A Hann spectrum independently shows a shared carrier near410.8Hz and nearby408.95Hz component; the latter is approximately17.4dB below the carrier in hardware versus9.7dB native. This is a spectral audio difference, not just an RMS plotting effect. Its cause is unidentified.

Native cutoff writes rise monotonically over0.2–2.7s, before reaching their first peak near2.76s, while audio fluctuates repeatedly. Individual RMS dips cannot be treated as envelope reversals. Playback/phase, filter response and timing remain candidates. No production fix or extra hardware capture is justified yet. Exact measurements and methods are in the updated compact validation.

## Louder MIDI73 repeat

The V2 hardware capture increases held RMS23.5255dB, peaks at−25.4348dBFS and has no full-scale clipping. After gain centering, its waveform-level ripple closely repeats the first hardware recording: fits1.870 versus1.868Hz,0.757 versus0.776dB amplitude and100.5 versus97.4degrees relative to each WAV start. The native reference remains different (1.849Hz/1.336dB/−86.5degrees). This argues against low recording level alone as the explanation, without identifying modulation, source phase or filter behavior as the cause. The native comparison is the original V1 render with independent gain centering, not a newly rendered V2 acceptance run.

## Native application timing and static controls

The native renderer's changed active coefficient sets use the latest completed firmware words, with application within one44.1kHz frame (under23microseconds). Cutoff writes occur around20ms apart. The new read-only bounded trace leaves1,543,500 stereo PCM frames exactly unchanged in a common-checkpoint trace-on/off comparison. The referenced source sample0 imports exactly9216 bytes; unused identical disk slots are not required to import.

At MIDI73, static native controls hold cutoff words416/1042/2613 constant, yet their output retains the roughly1.85Hz RMS ripple. Fixed-frequency diagnostic sinusoid amplitudes are approximately1.62/1.58/0.69dB; bypass falls to0.087dB. Thus the native ripple does not require moving cutoff. Source/interpolation and filter response remain confounded. MIDI73 is just beyond the measured pitch-interpolation model's+12-semitone upper bound, so it takes the linear fallback; this is a candidate to investigate, not a proven physical cause.

Next hardware controls are only patch03 STATIC L80 and patch05 BYPASS at MIDI73, each3s held/3s release, same RoboSampler ZIP format and recording gain as V2. No full keyboard batch is required. Static/bypass hardware has not yet been measured, so modulation timing and the original moving/resonant bug remain open. See [application validation](../../condensed/validation/modulation-application-2026-10-15.json).

## Physical static/bypass controls received

Both requested MIDI73 captures are clean stereo48kHz, velocity127,3s held/3s release. Static80 peaks at−28.69dBFS; bypass at−12.58dBFS. Neither contains full-scale clipping or nonfinite audio.

| Case | Hardware1.86Hz RMS component amplitude (dB) | Native amplitude (dB) |
| --- | --- | --- |
| Moving T72 |0.79|1.35|
| Static L80 |0.91|1.58|
| Bypass |0.086|0.087|

These are descriptive fixed-frequency sinusoid fits after a separate linear trend, not measured modulation depths. The static hardware result retains the near-opposed phase/depth relationship seen in the moving comparison, even though the patch uses equal TVF levels and zero envelope times/LFO depths. The ripple therefore is not evidence requiring cutoff movement. Bypass makes it much smaller in both outputs, but matching low RMS variation does not establish matching source waveform or spectral phase.

Native position/frame observations confirm pitch word34716 (step2.118896484375), above the measured interpolation model's upper bound32768. It uses linear fallback at this note. The next diagnostic is to separate source reconstruction/spectral phase from stationary filter response using these existing bypass/static controls; the fallback remains a candidate, not an isolated fix. Earlier static BP/HP qualification remains limited to its named settings and does not qualify all LP/pitch configurations. No production DSP or timing change, and no further hardware capture is required at this stage.

[Hardware control validation](../../condensed/validation/modulation-hardware-controls-2026-10-15.json) includes archive identities, integrity, static/bypass spectral-ratio diagnostics and limitations.

## Source-isolation result

The unchanged filter fed with hardware bypass predicts hardware static ripple. A source-only candidate (existing cubic kernel plus effective one-source-sample phase offset), calibrated on bypass, predicts moving RMS at MIDI73 within0.086dB and additional keys74–76 within0.104–0.206dB, using unchanged native cutoff trajectories and no per-key fitting. This supports a source reconstruction/phase explanation for this survey symptom rather than a required envelope-speed correction. Raw waveform parity remains incomplete; the one-sample offset is effective, not a proven ASIC address rule. No production correction has been made. See [source-isolation report](modulation-source-isolation.md).

Older native RMS overlays used approximate WAV origins and cannot qualify absolute MIDI latency (BUG-076). Exact source replay and actual stream-frame traces are used in the new diagnostic. The earlier inter-extrema durations cancel constant origin error and remain exploratory audio-landmark measurements.
