# Original resonant sweep: source and control discrimination



2026-10-15. BUG-005 remains OPEN. No native DSP or production playback behavior changed in this investigation. The source experiment remains off by default.



The original case is ROBO_TVF patch04, LP SW R64, MIDI60/velocity127. Its envelope continuously rises and falls; it does not provide a useful sustained high-cutoff plateau. Existing separate LP C64/R64 and C96/R64 recordings therefore supply the stationary controls. Hardware WAV starts are RoboSampler silence-trimmed audio references, not MIDI timestamps. No digital capture or additional hardware recordings were required.



## Stationary controls



Apply the unchanged LP transfer function to the measured bypass, retaining recording-band image harmonics. Cutoff/damping are fixed from the firmware trace:428/85 and2732/85. Gain and affine source phase are calibrated only over1.0–2.4s, then frozen.



| Control | Error at3.0–4.5s | Error at6.0–7.5s | Error at9.0–10.5s |

| --- | --- | --- | --- |

| LP C64/R64 |0.061%|0.095%|0.135%|

| LP C96/R64 |0.086%|0.089%|0.094%|



Training gains are0.999825 and0.998787, respectively. These controls strongly constrain stationary behavior at those two points. They do not qualify every cutoff, level, filter-state transition or dynamic arithmetic detail.



## Source experiment on the exact native patch



Original firmware loads ROBO_TVF and renders bypass, static64/R64 and sweep/R64 at MIDI60. Source-off and source-on runs start from the same supported native checkpoint and use identical MIDI. Control writes, coefficient activation frames and playback address positions match exactly.



After accounting for the known one-native-sample source phase change, bypass output is exact; stationary LP output is exact in later windows. The moving LP waveform differs by0.554% over file seconds1–12. Thus the source experiment has only a small effect on this unity-pitch sweep after phase alignment; it does not explain the older roughly18% moving residual. Those percentages measure different comparisons and must not be subtracted as if they share a denominator.



## Moving comparison



The historical18% result already interpolated between firmware cutoff writes. It was an offline trajectory diagnostic, not direct acceptance of the current native stepped implementation.



Preserving recording-band harmonics changes that historical fit only slightly:17.778% and17.713% error for the accepted quiet/repeat recordings. The static folding-analysis correction therefore does not remove this moving discrepancy.



The new diagnostic uses the actual native application trace and the measured hardware bypass excitation. Fractional-phase recurrence lanes retain the recording-band spectrum while using the unchanged native LP recurrence and damping85. A numerical stationary check against the analytic transfer function verifies this lane implementation; its use for moving coefficients remains an approximation to the recording chain, not literal DAC arithmetic.



| Actual native cutoff points | Quiet error | Repeat error |

| --- | --- | --- |

| Hold until next write; independently fixed clock |44.031%|46.246%|

| Interpolate between writes; independently fixed clock |19.142%|20.593%|

| Hold; diagnostic envelope scale fitted |45.014%|45.438%|

| Interpolate; diagnostic envelope scale fitted |17.770%|17.749%|



All comparisons keep gain1 and damping85. Fixed-clock rows use the source-clock ratio independently measured from the bypass,1.00002134767. One constant envelope alignment and one constant source phase are fitted on alternating0.4s training blocks over1.5–6.4s and frozen for the other blocks. No local time warp or evaluation-window refit is used. These blocks have been reused in historical exploration and are not fresh independent validation.



The large held-versus-interpolated difference persists with the clock fixed. This points toward how changing cutoff values become effective, while leaving the stationary response well constrained. It does not prove that hardware uses linear interpolation: the explanatory interpolation uses the next write's endpoint. A causal implementation must use only values already received, and may instead slew from the previous value, smooth a parameter, or implement different moving-state arithmetic. Fitted alignment offsets cannot identify physical latency because capture starts were trimmed.



## Next discriminating experiment



### Causal transition results



Causal coefficient smoothing was tested offline at shared5/10/20/40ms settings: a one-pole and a finite linear ramp from the current coefficient to each newly received target. Both use only already received, quantized cutoff words. A future-write perturbation check leaves all preceding output exactly unchanged for both models. No native code or playback default changed.



| Transition rule | Setting | Quiet evaluation error | Repeat evaluation error |

| --- | --- | --- | --- |

| Held baseline | — |44.03%|46.25%|

| One-pole |5ms|27.66%|30.38%|

| One-pole |10ms|22.96%|28.01%|

| One-pole |20ms|23.29%|33.21%|

| One-pole |40ms|31.34%|42.54%|

| Linear ramp |5ms|38.43%|40.92%|

| Linear ramp |10ms|29.85%|32.24%|

| Linear ramp |20ms|20.00%|21.33%|

| Linear ramp |40ms|24.96%|37.20%|



The20ms linear ramp is chosen using quiet training error only. Its model/duration transfer unchanged to the repeat take; each take fits only constant alignment and source phase on its own training blocks. Gain1, damping85 and independently measured clock ratio remain fixed. The selected duration is close to the native median20.09ms interval between changed cutoff values. This association is not a measurement of physical hardware smoothing time; recording alignment and smoothing delay are not independently identifiable here.



With the selected rule frozen, rise/fall evaluation errors are14.85%/23.51% for quiet and17.24%/24.87% for repeat, split at the trace-derived apex with each take's constant alignment. Larger falling-sweep residuals occur in both recordings. This is a diagnostic split of historically reused evaluation data, not fresh validation or proof of asymmetric hardware behavior.



The causal ramp recovers most of the improvement previously obtained with future-endpoint interpolation. It is still an offline coefficient-space candidate with substantial residual. Constant stationary coefficients are preserved; half/quarter source paths, reset/retrigger, release, general cutoff/resonance and other patches are unqualified. Parameter-space smoothing, coefficient quantization order, source phase drift and dynamic filter-state arithmetic remain unresolved. No production smoothing change is justified by these rows alone.



### Residual source phase versus cutoff trajectory



The20ms causal ramp was retained while testing a linear excitation-phase drift, cutoff timing scale, or both. Gain, damping and transition duration stay fixed. Added parameters are trained only on the same alternating blocks; evaluation blocks are historically reused. Zero-drift/unit-scale predictions match the preceding causal baseline exactly.



| Added diagnostic parameter | Quiet evaluation | Repeat evaluation |

| --- | --- | --- |

| None |20.004%|21.334%|

| Excitation-phase drift |20.045%|21.429%|

| Cutoff time scale |17.670%|17.937%|

| Both |17.728%|18.049%|



Excitation-phase drift is allowed±20ppm and pivots at3.8s; fitted values with the fixed cutoff trajectory are−1.01ppm and+4.96ppm. They do not improve evaluation. This tests a small linear phase-drift explanation, not every possible source error, and does not measure a physical oscillator or change the filter sample clock.



Individually fitted cutoff scales are1.00251612 and1.00072659, corresponding to+0.252% and+0.073% progression after constant alignment. Source phase and alignment remain per-recording training parameters; these offsets are not MIDI latency. Rise/fall evaluation errors with these scales are16.06%/18.92% and15.04%/20.50%, respectively. Substantial dynamic residual remains.



Cross-recording transfer is more useful than the differing best-fit scales alone:



| Scale selected on training data from | Applied to | Evaluation error |

| --- | --- | --- |

| Quiet:1.00251612 | Repeat |16.417%|

| Repeat:1.00072659 | Quiet |18.044%|



During transfer, only the target recording's constant alignment and source phase are recalibrated on its training blocks. The cutoff scale stays frozen. Thus the quiet-selected scale supports one shared candidate yielding17.670%/16.417%, rather than requiring independent per-take speed settings. Repeat training error is worse with the quiet-selected scale than with its own optimum, despite the lower evaluation error; do not select a scale based on that evaluation improvement.



The residual is more sensitive to cutoff trajectory than to the tested small source-phase drift. The scale is still an effective offline fit: it can compensate for transition-law, coefficient-mapping or dynamic-state errors and is not a measured physical envelope-rate correction. Do not alter the CPU/audio clocks or production modulation speed from these rows. The following transition-space, quantization and state-form tests retain this shared candidate as a reference.



[Residual fits, cross-recording transfer, hashes and limitations](../../condensed/validation/resonant-phase-trajectory-2026-10-15.json).



### Transition space and quantization order



With the20ms ramp and quiet-selected shared scale frozen, four transition variants were compared. Each take fits only constant alignment and source phase on training blocks. The logarithmic coefficient variant is a proxy for a parameter-space hypothesis; it is not a decoded firmware envelope parameter.



| Transition | Quantize received words before ramp | Quantize applied coefficient after ramp |

| --- | --- | --- |

| Linear coefficient |17.670% /16.417%|17.900% /16.393%|

| Log coefficient |17.797% /16.519%|18.060% /16.539%|



Cells show quiet/repeat evaluation error. Before-ramp quantization retains the native multiple-of4 endpoint and ramps continuously; after-ramp quantization ramps raw words then quantizes the applied coefficient. All variants preserve the constant428 endpoint and pass a future-write causality check. Log variants are restricted to positive captured words; zero/reset behavior remains unqualified.



Quiet training selects linear/after, but it gives no consistent evaluation improvement over the reference. None of these choices explains the residual. [Rows, endpoint/causality checks and hashes](../../condensed/validation/cutoff-space-quantization-2026-10-15.json).



### Equivalent stationary filter forms



Different internal state representations can share a fixed-coefficient transfer function while behaving differently during coefficient changes. Four double-precision forms were therefore compared with the same trajectory, ramp, scale, gain and damping. Their constant-coefficient predictions agree within2.18e-13 relative RMS at428 and2732; the reference SVF moving baseline is reproduced exactly.



| Form | Quiet evaluation | Repeat evaluation |

| --- | --- | --- |

| Existing SVF |17.670%|16.417%|

| Direct I |18.069%|16.318%|

| Direct II |17.297%|17.648%|

| Transposed II |18.069%|16.320%|



Quiet training selects Direct II, but its slight quiet improvement worsens repeat. None gives a consistent improvement. This tests basic floating-point realizations, not hardware fixed-point arithmetic, saturation or every possible state-update order. No native filter was changed. [Numerical contracts and moving rows](../../condensed/validation/moving-filter-realization-2026-10-15.json).



### Where the remaining error occurs



The two precise stationary controls constrain cutoff words428 and2732; the native sweep reaches15451. Assigning the reference model's evaluation samples to its candidate cutoff ranges gives:



| Candidate cutoff range | Quiet residual energy share | Repeat residual energy share |

| --- | --- | --- |

| Below428 |12.15%|9.48%|

|428–2732 |47.33%|42.32%|

|2732–8192 |31.45%|39.35%|

|8192 and above |9.08%|8.84%|



These are shares of total squared residual, not waveform error percentages. The428–2732 band has29.46%/33.11% local waveform error despite accurate stationary endpoint controls. The highest band has8.78%/7.35% local error. Most observed signal energy lies above the stationary control points, but the residual is not confined there. Good stationary endpoints therefore neither qualify the entire sweep nor justify attributing all remaining error to untested high-cutoff behavior.



Bin assignment uses the candidate native trajectory, not physically measured cutoff. No extra parameters were fitted for this localization. The remaining discrepancy spans moving cutoff ranges; simple quantization-order, logarithmic transition and equivalent-form changes do not resolve it. Keep BUG-005 OPEN and retain the existing native default. [Coverage rows and limitations](../../condensed/validation/resonant-cutoff-coverage-2026-10-15.json).



### Firmware path follow-up



The [firmware modulation audit](../../firmware/os/modulation-firmware-path.md) now verifies1336 cutoff calculations/word deliveries and456 envelope counter calculations exactly on this fixture. It also confirms a separate short-time path issuing commands through unmodeled DSP control register101018. Time4 survey notes take that path; Time8/72 use software counters. Command semantics are unqualified, and this fast-path gap does not prove the cause of the separate Time80 resonant residual. No native behavior changed.



[Causal grid, selection, rise/fall rows, causality check and hashes](../../condensed/validation/causal-cutoff-transitions-2026-10-15.json).



[Full rows, native trace comparisons, numerical checks, hashes and limitations](../../condensed/validation/resonant-source-control-2026-10-15.json).





### Ramp-duration refinement and derived-coefficient transitions



A new training-only duration fit tests whether the earlier coarse grid hid a useful correction. With measured source clock, gain1 and damping85 fixed, quiet training chooses19.6836ms. Transferring that duration unchanged to the repeat gives19.970%/21.263% evaluation error, versus20.004%/21.334% for20ms. This negligible improvement does not resolve the resonant discrepancy. A1024-frame duration (23.220ms) worsens the repeat to24.682%; no binary-length ramp is established.



A separate test ramps the derived direct-I coefficients `c*c` and `c*damping` from received endpoints instead of deriving them from the ramped cutoff. Both models preserve the stationary transfer at428/2732 and pass future-write causality checks. Derived-coefficient smoothing yields20.856%/21.754% versus20.657%/21.504% for cutoff smoothing in the same direct-I form. It is worse on both recordings. Both retain the fixed measured clock and20ms duration; only constant alignment/source phase are fitted on training blocks.



These tests reuse historical evaluation blocks and the fractional-phase recording-chain approximation. They justify neither a new production coefficient law nor an envelope-speed correction. The existing opt-in native ramp remains the supported partial improvement; BUG-005 stays OPEN. No emulator source or default changed in this follow-up. [Results, input identities and limitations](../../condensed/validation/filter-transition-refinement-2026-10-15.json).





### Seven-channel isolated-transition hardware capture — 2026-10-16



The replacement Ableton WAV contains all11 correctly spaced notes and the intended held, step and ramp contrasts. It is mono48kHz/24-bit, finite and unclipped (peak about−26.46dBFS). The185.045second file includes the last audible release; only some final scheduled silence is absent. The recording is accepted for analysis.



A same-session bypass calibration gives an effective source rate44100.9533Hz relative to the recording clock. Existing LP equations with masked words416/2613 and damping85 predict later stationary windows within0.270–0.289% for low hold and0.070–0.076% for high hold. Gain and phase are trained on1..5s; these later checks use6..11s.



For the isolated transitions, source phase and constant gain are calibrated on each take's9..11s endpoint plateau. Only constant control alignment is fitted over the7.45..7.95s transition window. With the existing SVF and immediate received-target changes, opening takes4/8/10 fit0.321/0.319/0.421%; closing takes5/9/11 fit1.224/1.112/0.921%. These are descriptive transition-window fits, not independent held-out waveform qualification or measured hardware command latency. Coarse alignment searches gave much larger, misleading errors; the refined results supersede any apparent direction-dependent state defect from those initial searches.



The fractional-phase recording-chain model is an approximation. Changing its time origin changed the first closing prediction0.207% relative RMS; the final result uses the same6s origin as the other takes. These data support retaining the current filter equations for this isolated-step experiment and do not justify smoothing every cutoff change.



The slower envelopes remain distinct. With source phase/gain fixed from their later plateaus and alignment fitted on alternating200ms blocks, immediate native targets give3.227% rising/10.403% falling evaluation error. A fixed20ms ramp gives2.697%/10.222%. A10.844ms duration selected only on rising training blocks gives2.325% rising and10.211% falling when transferred unchanged. This is not a measured hardware slew constant and does not solve the software-counted closing trajectory. No emulator behavior changed; BUG-005 remains OPEN. Existing native targets/timestamps are not hardware bus measurements.



[Capture identity, all rows, calibration, method limitations and script hashes](../../condensed/validation/tvfstep-hardware-controls-2026-10-16.json).





### Localizing the seven-channel slow-ramp discrepancy



With the rise-selected 10.844ms transition fixed, fitting an endpoint-preserving cutoff map and control progression on opening training blocks gives only small corrections. Transferring those unchanged to closing (refitting only constant alignment) leaves 9.504% evaluation error versus 10.211% baseline. The shared correction is insufficient.



An independently fitted closing progression scale of 1.00314034 reduces closing evaluation error to 1.729%, with source clock, plateau phase/gain, damping and filter recurrence fixed. Opening instead selects 1.00007149 and its evaluation worsens slightly (2.371% versus 2.325%). The closing result is a diagnostic fit, not a transferable hardware law or a reason to change emulator speed.



Separate 500ms window fits preserve full filter history and fit only constant alignment. Opening alignment ranges 38.494–39.868ms; closing falls from 46.526ms at 0.8s to 36.456ms at 4.3s. Closing's linear trend is -2.913ms per second (R-squared 0.9952), supporting a progressively accumulating trajectory discrepancy. These window errors are fitted on the same samples, not held-out validation; alignment can absorb coefficient/dynamic/model errors and is not measured MIDI latency.



The next discriminating implementation investigation is the original-firmware envelope counter, stage and coefficient conversion for these exact opening/closing fixtures. Do not apply a global or direction-specific speed correction from these fits. No production code changed; BUG-005 remains OPEN.



[Trajectory fits, transfer, local alignment rows, identities and limits](../../condensed/validation/tvfstep-trajectory-2026-10-16.json).



### Exact opening/closing firmware audit and cadence control

A fresh original-firmware run of all11 seven-channel fixture takes passes the existing sample, MIDI, endpoint, step, ramp and release checks. An additive read-only observer captures the inputs to cutoff conversion. Independent integer replay matches all1204 cutoff calculations and442 scored counter calculations across the two slow ramps. Each ramp also has one initialization row and380 sustain rows outside the counter-step score. This run does not repeat the earlier observer-disabled same-state audio identity check.

Both ramps execute stage3 with divisor219. Opening uses endpoint24672 and signed delta-8224; closing uses endpoint16448 and delta+8224. The signed division truncates toward zero in both directions. There is no different closing-rate arithmetic in the observed path. Native mean update periods estimated against counter index are20.05327ms opening and20.04989ms closing; the earlier capture-reference traces likewise give20.05253/20.04956ms. These native timing observations do not measure the hardware cadence.

Replacing native write times with an exact20ms schedule, keeping words/source/filter/slew fixed and fitting only constant alignment, gives7.866% opening and2.505% closing evaluation error. Relative to2.325%/10.211% baseline, this helps closing but substantially worsens opening. Reject a universal20ms scheduling correction. The arithmetic audit also does not justify modifying signed division or the firmware coefficient map.

Only one physical slow ramp per direction was captured. Thus the apparent directional difference remains confounded with take-to-take timing variation. A136second repeat MIDI sequence now uses the existing disk unchanged: bypass, up, down, down, up, up, down, bypass. Three repetitions per direction and bypass at both ends will test repeatability and source-clock stability. This is the next required hardware evidence; native arithmetic agreement alone cannot choose the physical control law. No production code changed; BUG-005 remains OPEN.

[Full integer replay, raw inputs, native validation, cadence control and identities](../../condensed/validation/tvfstep-firmware-audit-2026-10-16.json).


### Repeated hardware ramps: accepted064504 recording

The138.112second mono48kHz/24bit recording contains all eight intended notes and releases, no nonfinite/full-scale samples, and peak -26.803dBFS. Starting/ending bypass source-clock estimates are44100.948392/44100.947729Hz relative to the recording clock. Their fitted difference is0.015ppm; this is an estimate, not an absolute physical accuracy bound. A coarse lag search was necessary: the initial single-start search selected a false minimum, and its private ramp fits are rejected. Qualified calibration errors on later filtered plateaus are0.068–0.070% high and0.172–0.178% low.

| Take | Direction | Original trajectory evaluation | Prior-recording scale, frozen | Independently fitted scale |
| --- | --- | --- | --- | --- |
|2|Opening|2.756%|2.798%|1.000003|
|3|Closing|7.830%|3.328%|1.002354|
|4|Closing|7.779%|3.307%|1.002363|
|5|Opening|2.143%|2.214%|0.999602|
|6|Opening|2.105%|2.055%|1.000179|
|7|Closing|10.188%|1.741%|1.003019|

The frozen scales are1.00007149 opening and1.00314034 closing, selected on the previous recording before this capture. Source clock comes from bypass, phase/gain from each later plateau; filter recurrence, damping and prior rise-selected10.844ms slew stay fixed. Only constant control alignment is fitted on new alternating200ms training blocks for the frozen transfer. Independently fitting the new closing scales gives1.678–1.772% evaluation. Selecting1.00235386 on only the first new closing take and freezing it gives1.746%/2.760% on the two later closes. Thus the useful closing adjustment transfers across takes and recordings, although its best-fit value varies.

The exact20ms schedule still worsens all openings (6.954–8.212% evaluation), while improving closes (1.872–2.399%). This reinforces rejection of a global cadence adjustment. Repetition now establishes a direction-associated discrepancy in this fixture, but does not establish a physical direction-dependent clock or justify a hardcoded rate correction. The next investigation should test causal coefficient-transition behavior against these repeated ramps and the existing isolated-step controls. No new capture is requested; no production behavior changed; BUG-005 stays OPEN.

[Capture identity, per-take fits, frozen transfer, calibration and limitations](../../condensed/validation/tvfstep-repeat-hardware-2026-10-16.json).


### Causal transition-law checks on the repeated ramps

Two additional families retain original native write times, source clock, plateau phase/gain, damping and filter recurrence. Candidate selection uses only the first opening/closing training blocks (takes2/3); later takes transfer the selected law and fit only constant alignment. Evaluation blocks are reused research data.

A precision sweep quantizes the per-source-sample cutoff increment, testing downward rounding and truncation toward zero, then integrates over the fractional lanes. Overshoot is clamped and the target is reached at the duration deadline. The initial grid tests4/8/12 fractional word bits and10.844/20ms; a refinement covers6–10 bits and15/20/25ms. Both training selections choose downward rounding at8 bits with20ms duration. Across the three openings it gives3.207/2.903/3.182% evaluation error, worse than2.756/2.143/2.105%. Closings improve to4.954/4.952/7.293% from7.830/7.779/10.188%, but substantial error remains. This is insufficient and does not identify actual ASIC precision.

A separate common slew law interpolates duration against log target cutoff, with no direction-specific parameter. Two optimizer starts converge near2.33ms at word416 and12.87ms at2612. Both durations are fitted on first-pair training only. Transfer gives3.854/3.155/4.219% opening and3.996/3.953/6.298% closing error. Again, every opening worsens. Neither family supports a production correction. Held-target identity and future-write causality checks pass for every quantization candidate and the selected cutoff-dependent law.

The read-only firmware trace shows all six isolated jumps issue command0 before the cutoff word, then restore command27 (0x1B) approximately3microseconds afterward. This concrete transaction distinction must be preserved when testing slow-command behavior. Applying the20ms/8bit candidate indiscriminately to isolated opening step4 raises same-window fitted error from0.318% immediate to8.318%. This check uses a common full origin0 renderer; scores fit the scored window and are not held-out acceptance. It does not decode command0x1B or prove the hardware's transition algorithm.

No emulator change was made; BUG-005 remains OPEN. The next investigation is original-firmware update scheduling and timer/counter cadence. Arithmetic replay alone does not qualify physical write timing, and neither a fitted clock nor these tested slew laws explains all controls.

[Candidate grids, training selection, transferred rows, causal checks, step commands and hashes](../../condensed/validation/tvfstep-transition-laws-2026-10-16.json).


### Combining the independently useful corrections

At the user's suggestion, the20ms/8bit downward-rounded increment candidate was combined with the already selected prior-recording progression scales (opening1.00007149; closing1.00314034). Parameters remain frozen; only each take's constant control alignment is fitted on training blocks. Source phase/gain remain plateau-calibrated. This tests a combination without a new joint parameter search.

| Take | Direction | Timing adjustment with10.844ms slew |20ms rounded increments | Combined |
| --- | --- | --- | --- | --- |
|2|Opening|2.798%|3.207%|3.230%|
|3|Closing|3.328%|4.954%|6.352%|
|4|Closing|3.307%|4.952%|6.354%|
|5|Opening|2.214%|2.903%|2.952%|
|6|Opening|2.055%|3.182%|3.146%|
|7|Closing|1.741%|7.293%|4.323%|

All numbers are evaluation RMS waveform residuals. The combination is worse than the timing-adjusted reference on every take. This suggests overlapping compensation rather than independent additive improvements; it does not rule out every possible combination. Static identity and future-target causality pass at both combined scales. Earlier experiments already combined smoothing with timing, and timing with a bounded cutoff map. No production change is supported by this added combination.

The [firmware scheduling audit](../../firmware/os/modulation-firmware-path.md) now verifies1808 rearms as service-time TIMER1 +20000ticks. This explains how emulated service delays accumulate, while leaving their hardware correctness unresolved. Keep BUG-005 OPEN.

[Combined rows, contracts, scheduler evidence and input hashes](../../condensed/validation/tvfstep-scheduler-combinations-2026-10-16.json).


Current-build [matched scheduler localization](../../firmware/os/modulation-firmware-path.md) verifies mouse-handshake critical sections delay native control interrupts:all24 delayed intervals end at004B:5812 afterPOPA; paired observers preservePCM exactly. Mean periods20.071802ms opening/20.068255ms closing in twohalf-second windows. This identifies a common native delay mechanism, not a direction-specific hardware clock or justified filter correction. BUG-005 remainsOPEN; companion101018/transition semantics and physical timing are still unqualified. [Evidence](../../condensed/validation/filter-scheduler-localization-2026-10-16.json).


## Fresh hardware comparison after the CPU correction

Fresh original-firmware opening/closing trajectories on the corrected executable pass MIDI delivery, full sample-allocation and silent-tail checks. The existing repeated hardware recording is compared using the same frozen10.844ms diagnostic coefficient transition, bypass-derived source clock and plateau-calibrated source phase/gain. No speed scale is fitted (both1.0); only constant control alignment uses training blocks.

| Take | Direction | Historical target schedule error | Fresh corrected-build target schedule error |
| --- | --- | --- | --- |
|2|Opening|2.756%|6.281%|
|3|Closing|7.830%|2.870%|
|4|Closing|7.779%|2.831%|
|5|Opening|2.143%|6.155%|
|6|Opening|2.105%|4.934%|
|7|Closing|10.188%|4.961%|

These are waveform residuals from the offline diagnostic law, not evidence that the production renderer implements that slew. Historical/current control phases and build histories differ; recordings/evaluation blocks are reused research data. The result is mixed: closing improves, opening worsens. It explicitly **does not closeBUG-005** or justify a global/direction-specific speed fudge. Retain the documented CPU repair; investigate missing companion-command101018/coefficient-transition semantics against the step/static/bypass controls. [Exact model contract, fresh target/sample validation, rows, source/recording hashes and limitations](../../condensed/validation/filter-hardware-after-kb-timing-fix-2026-10-16.json). The corrected workspace emulator is built; packaged application artifacts have not been rebuilt by this change.


## Frozen candidate replay on the corrected CPU build

Replaying earlier methods against fresh corrected-build trajectories gives these mean evaluation waveform residuals over three takes per direction:

| Frozen transition model | Opening | Closing |
| --- | --- | --- |
| Immediate | 6.181% | 3.783% |
| 10.844ms linear smoothing | 5.795% | 3.552% |
| 20ms linear smoothing | 5.915% | 4.074% |
| 20ms, 8 fractional bits, downward-rounded increments | 6.032% | 2.670% |

Short smoothing improves both direction averages relative to immediate changes. Rounded increments improve closing further with a small opening tradeoff. Reapplying historical direction speed scales worsens closing to 7.639% (short smoothing) or 10.746% (rounded increments); those scales should not carry forward automatically. These are frozen offline models, with constant alignment fitted on training blocks and reused research evaluation blocks. They do not establish physical coefficient arithmetic.

Fresh native isolated-step capture passes sample, MIDI, silent-tail and unchanged-media checks. In the corresponding same-window hardware diagnostic, immediate changes give 0.317% residual; unconditional short smoothing gives 6.641%, and unconditional 20ms transitions approximately 8.32%. Any native trial must preserve the fast command path. Existing opt-in 20ms rendering already gates on command 0x001B and LP mode; its gate is not a resonance restriction. A command-gated short or rounded transition remains a useful next native experiment, even though neither frozen model is perfect. Production filter behavior is unchanged and BUG-005 remains OPEN.

[Replay rows, contracts, fresh step capture, input identities and limitations](../../condensed/validation/filter-frozen-candidates-after-kb-fix-2026-10-16.json).


## Native short-smoothing trial (2026-10-16)

The workspace emulator now supports `S760_NATIVE_CUTOFF_SHORT_CANDIDATE`: a separate, disabled-by-default diagnostic path using 478 native samples (10.839002ms), nearest to the frozen 10.844412ms offline model. It reuses the existing command 0x001B / LP gate and preserves immediate initialization/fast writes. The existing 20ms candidate stays at 882 samples when used alone; the short flag wins if both flags are supplied. Neither flag changes firmware or CPU scheduling. The normal Python runtime sanitizes these environment flags; this trial explicitly injects the short flag in a private launch harness. Packaged application artifacts are unchanged.

Four original-firmware native takes cover both ramps and both abrupt steps, with deterministic paused setup and pull rendering. With the flag disabled, all 2,998,800 stereo PCM frames match the prior executable exactly. Enabled and disabled guest cutoff trajectories and note times are identical. Both enabled ramp outputs change. Full sample allocation, MIDI delivery, unchanged-media and silent-release checks pass.

Step PCM is not entirely identical because smoothing changes the preceding filter state. In the first 200ms after each jump, peak differences are 0.0000139% and 0.001404% of the corresponding baseline take peak. A separate read-only applied-coefficient trace proves both fast target jumps reach the exact target on the next native audio frame, with no smoothing ramp. The observer preserves 1,499,400 stereo PCM frames exactly and drops no rows.

The driver/executable builds pass, all 488 current regression tests pass, and native boot/input/playback/release/clean-shutdown acceptance passes. This qualifies an opt-in implementation trial, not a new measured hardware improvement or resonant-filter repair. The motivating offline short-smoothing comparison was 6.181% to 5.795% opening and 3.783% to 3.552% closing; those numbers are not native analog acceptance. BUG-005 remains OPEN. Next compare the actual native trial against analog recordings with source/clock/alignment rules frozen, including resonant and static controls before considering any default change.

[Native comparisons, applied rows, build identities, regression and runtime evidence](../../condensed/validation/native-short-cutoff-trial-2026-10-16.json).


## Short smoothing plus rounded increments (2026-10-16)

The user's proposed combination was replayed with the short duration (10.844412ms), eight fractional cutoff-word bits and all source/clock/gain/damping rules fixed. Only constant control alignment is fitted on training blocks. Mean evaluation waveform residual over three takes per direction is:

| Model | Opening | Closing |
| --- | --- | --- |
| Short smoothing alone | 5.795% | 3.552% |
| Short smoothing + downward-rounded increments | 5.774% | 2.659% |
| Short smoothing + truncation toward zero | 5.774% | 3.566% |

The combination lowers closing residual by approximately25.1% relative to short smoothing alone, with essentially unchanged opening error. Signed floor rounding supplies the closing improvement; truncation toward zero does not. This is reused analog research data, not fresh validation or established ASIC arithmetic. Stationary identity and future-target causality checks pass for all three frozen models.

A separate opt-in native implementation, `S760_NATIVE_CUTOFF_SHORT_ROUNDED_CANDIDATE`, is now built. It implies the 478-sample short transition and floors each signed coefficient increment to 1/4194304 (1/256 cutoff-word unit), clamps overshoot and snaps to the target at the deadline. Existing command0x001B/LP gating and immediate fast/initialization writes remain. It takes precedence over the other cutoff candidate flags. The ordinary runtime sanitizes diagnostic environment flags; the private qualification harness explicitly injected this flag. Packaged application artifacts are unchanged.

Native disabled output matches 2,998,800 prior stereo PCM frames exactly. Enabled/disabled firmware cutoff trajectories and note times agree. Applied trace has18,371rows, zero drops and1,703 intermediate coefficient rows; every applied coefficient lies on the expected increment grid. Both abrupt target changes apply exactly on the next audio frame. Recursive filter state from the changed lead-in means step PCM is not entirely identical: first200ms post-jump peak differences are0.0000139% opening and0.001532% closing relative to baseline take peak. Full loaded samples, MIDI delivery, unchanged-media and silent tails pass. Both native builds, all488 regression tests and native runtime boot/input/playback/release/clean shutdown pass.

BUG-005 remains OPEN. These results support retaining the combination as an opt-in trial; actual native analog accuracy, resonant behavior and physical command/rounding semantics still need qualification before changing defaults. [Frozen rows, native comparisons, raw applied step rows, input/build identities and limits](../../condensed/validation/native-short-rounded-cutoff-trial-2026-10-16.json).


## Third-method combinations (2026-10-16)

With short smoothing and eight-bit signed-floor increments frozen, three additional candidates were tested: an endpoint-preserving cutoff-map correction, a shared target-progression adjustment, and both. The map adds beta*(high-low)*u*(1-u), u clipped to0..1 between cutoff words416 and2612. Beta is bounded to+/-0.01; the selected map-only beta0.00174037 shifts the midpoint by less than one cutoff-word unit. The shared scale is bounded to+/-500ppm. These parameters use only first opening/closing training blocks, then freeze for the four later takes. Source clock, phase, gain, damping, recurrence and the two established transition parameters remain fixed; constant alignment is fitted per take on training blocks.

| Added method | Opening mean evaluation residual | Closing mean evaluation residual |
| --- | --- | --- |
| None | 5.771% | 2.660% |
| Endpoint-preserving cutoff map | 4.790% | 3.173% |
| Shared target progression adjustment | 4.549% | 3.985% |
| Map and progression adjustment | 3.913% | 4.058% |

The new methods offer useful tradeoffs rather than improving both directions relative to the current two-method candidate. Map-only improves opening by about17% while increasing closing error by about19%; it still beats the earlier immediate-change reference in both direction averages. Combining map and progression substantially improves opening but gives up more closing accuracy. The fitted scales are approximately0.999501, near the lower search bound; these are effective model fits and do not establish a CPU/OS/audio clock defect. Retain these as exploratory alternatives, rather than rejecting every tradeoff or declaring a universally superior correction.

A correction to the analysis separates target progression from coefficient slew: the final replay keeps the physical short-transition duration fixed. Parameter selection used the historical scaled-slew implementation on training blocks; the final replay reuses those frozen parameters without evaluation-driven refitting. The180-evaluation bounded optimizers hit their budgets, so no global/converged optimum is claimed. Exact endpoint/held-anchor and future-target causality checks pass. The map only preserves the two tested static anchors; other stationary cutoffs remain unqualified. Evaluation blocks are reused research data. No additional native rendering change or new hardware parity claim follows from this batch.

Other concrete follow-up experiments are fractional-increment error feedback (retain discarded remainder instead of permanent bias), rounding of recursive filter state, and command-dependent transition shape/latching. Each needs stationary and fast-command controls as well as both ramp directions; none is established ASIC behavior. BUG-005 stays OPEN. [Fit parameters, training/evaluation rows, corrected fixed-duration replay, contracts, identities and limitations](../../condensed/validation/filter-third-method-combinations-2026-10-16.json).


## Direction-specific progression transfer (2026-10-16)

To test whether the approximately4% shared-fit residual was a compromise, the preceding map-plus-short-slew-plus-floor model was retained and only its progression scale was fitted separately for opening and closing. Map beta0.00108703928, physical slew duration10.844412ms, eight fractional increment bits, source clock/phase/gain, damping and recurrence remain frozen. A coarse17-point scale search over0.998..1.002 followed by local refinement uses only take2 opening/take3 closing training blocks. Constant control alignment is profiled on training samples. The resulting direction scales are0.9983235600 opening and1.0004058684 closing. Both refinements converge. These scales are diagnostic trajectory fits, not measured CPU/audio clock ratios.

| Take | Direction | Shared scale evaluation residual | Frozen direction scale evaluation residual |
| --- | --- | --- | --- |
|2|Opening|4.355%|2.309%|
|3|Closing|3.354%|2.265%|
|4|Closing|3.316%|2.264%|
|5|Opening|4.308%|1.935%|
|6|Opening|3.074%|1.885%|
|7|Closing|5.504%|2.945%|

Mean opening residual falls3.913% to2.043%; closing4.058% to2.491%. All six takes improve. All four later takes improve with the direction scales frozen; only their constant alignment is fitted on training blocks. This supports a useful direction-dependent correction even though residual error remains. Historical research evaluation samples have been reused, so this is not new analog hardware acceptance. The map still only qualifies its two static anchors.

No native change was made. Implementing a direction-dependent real-time response requires a causal law that handles direction reversals and command/voice changes. Offline scale greater than1 can advance a write relative to the original input stream; its future-target check in retimed coordinates does not prove live-stream causality. It must not be implemented by changing CPU clocks or reading future writes. Treat these fits as a target for a causal coefficient/state model and independent native/hardware testing, rather than calling them a complete hardware fix. BUG-005 stays OPEN. [Search profiles, frozen fit parameters, all rows, contracts, identities and limitations](../../condensed/validation/filter-direction-transfer-2026-10-16.json).


## Below-one-percent acceptance target (2026-10-16)

The user accepts below1% waveform residual in both directions as the practical completion target. Use the established evaluation RMS waveform percentage, and continue reporting repeated-take results; do not substitute correlation or redefine the error. Static and fast-command controls must remain acceptable, with native implementation and independent hardware qualification distinguished from offline fits. The target has not yet been achieved.

Direction-specific endpoint-preserving map curvature was trained only on take2/take3 training blocks with the learned direction scales, slew, floor increments, source clock/phase/gain, damping and recurrence fixed. Opening beta0.00123606798 and closing beta-0.000488061945 give mean evaluation residual2.0139% opening/2.0007% closing, versus2.0430%/2.4914% previously. The midpoint target shifts are+0.67860/-0.26795 cutoff-word units. Parameters transfer frozen to later takes; only constant alignment is fitted on their training blocks. Intermediate stationary cutoff accuracy is still unqualified.

Retesting physical transition duration over2..30ms with coarse search/local refinement selected the existing10.844412ms duration for both directions, adding no improvement. Testing target precision with all other corrections frozen gives:

| Target conversion before smoothing | Opening mean residual | Closing mean residual |
| --- | --- | --- |
| Existing truncate bottom two bits | 2.014% | 2.001% |
| Retain raw target bits | 4.029% | 6.456% |
| Round to nearest multiple of four | 6.572% | 9.564% |

The existing conversion wins first-pair training selection and later evaluation in this fixed combination. This does not rule out every refitted model or prove physical target precision. No native change was made. Further useful work is residual localization against update/latching timing and a causal dynamic coefficient/state response; avoid adding unrestricted waveform correction parameters merely to force a number below1%. BUG-005 remains OPEN. [Acceptance threshold, full curvature/duration/precision rows, frozen fits, identities and limits](../../condensed/validation/filter-sub-one-percent-target-2026-10-16.json).


## Dynamic residual tests and further CPU repair (2026-10-16)

Residual localization on the historical corrected model shows similar errors during coefficient transitions and between them: mean opening2.077%/1.960%, closing2.007%/1.980%. Bounded derivative-shape changes produce no meaningful improvement after signed-floor quantization. Alternative stationary-equivalent state forms are also worse: SVF2.014%opening/2.001%closing, direct-I2.061%/2.136%, direct-II2.361%/2.699%, transposed-II2.061%/2.136%. Stationary anchor predictions agree within1e-10 relative RMS. For fixed ceil-latching grids of1/4/16/64frames at phases0/half-grid, first-pair training selects4frames/phase2, which worsens means to2.016%/2.006%. The unselected1frame/half-frame variant gives tiny exploratory gains to2.013%/1.999%; it does not approach1%. Only these phase/period variants are tested, not every possible hardware latch. Models selected using first-pair training; later research evaluation blocks reused.

A new documented CPU defect was found during timing follow-up. Native SKIP, selected unary/word-byte-shift/NORML/unconditional-jump/DJNZW and stack operations retained legacy base-state assumptions. Intel270651-003 Table3.3B and isolated execution disagree in42 of49cases. BUG-092 corrects30 opcode groups for native KB, with actual internal/external stack accesses distinguished. All49 cases now pass, and all39 tested legacy timing cases retain exact before/after durations. This does not qualify wait states, prefetch, bus width, every opcode or complete physical IRQ timing. Stack fixtures avoid boundaries.

Both CPU dependency and workspace executable were rebuilt. All495 current regressions pass; native boot/input/MIDI/playback/zero-release/clean-shutdown checks and four new original-firmware step/ramp captures pass. The initial suite had two false failures: ROM SCSI tests sampled a transient observer stage every60frames. Actual SCSI attempt, timeout/bad-header and floppy handoff still occurred. BUG-093 now observes boot selection at the ordinary Exit input event, retaining every timeout/header/handoff/media assertion. Archived observer sources and firmware are unchanged.

| Deterministic target capture, same frozen filter corrections | Opening mean residual | Closing mean residual |
| --- | --- | --- |
| Before additional CPU repair | 2.000% | 1.934% |
| After additional CPU repair | 2.024% | 1.930% |

These matched captures share original-firmware setup and note times. Frozen direction/map corrections were selected on an earlier capture; only constant alignment is fitted here. The repair fixes CPU correctness but does not solve the filter residual. Without the progression/map correction, the new-build diagnostic gives5.995%opening/2.343%closing. Reusing old-build checkpoints was avoided. Packaged application artifacts were not rebuilt.

The new captured updates have mean periods20.013618msopening/20.014148msclosing, with affine timing residual RMS63.063/53.909microseconds. Replacing native timestamps by an offline affine schedule barely changes waveform errors:2.024%to2.021%opening and1.930%to1.927%closing. This excludes recorded update irregularity as a substantial explanation under the tested model; no guest timer/events were changed.

The below1% target remains unmet. Intermediate stationary cutoff measurements are the next useful discriminator: current map corrections preserve only two measured endpoints and cannot independently distinguish cutoff-map error from moving-state behavior. [All dynamic variant/localization/jitter rows](../../condensed/validation/filter-dynamic-residual-tests-2026-10-16.json), [CPU/test repairs, raw before/after, builds,495 regressions, native acceptance and fresh captures](../../condensed/validation/native-kb-control-state-time-fix-2026-10-16.json).


## Prepared hardware midpoint calibration (2026-10-16)

The remaining below1% target needs independent constraints between the two static endpoints. `scripts/build_tvf_midpoint_capture.py --out-dir <fresh-private-folder>` reproduces the private720KB TVFGRID.IMG, TVFGRID_CAPTURE.mid and instructions. The disk extends the unchanged seven TVFSTEP controls with seven stationary holds at envelope levels68,72,76,80,84,88,92; all use LP/resonance64 and the original deterministic noise source. Fourteen performance parts receive on MIDI channels1..14; no program changes are used. The19-take sequence lasts257seconds (4m17s): initial bypass/endpoint/midpoint controls, three opening/closing pairs, two fast steps, final bypass.

Two fresh builds produce byte-identical image, MIDI, PCM source, spec and sequence. Image size737280bytes and performance routing are checked. Normal native protocol validation loads the image through original firmware and plays all14 parts.129024 allocated sample bytes match exactly; MIDI delivery, finite nonclipping audio, static midpoint words, both ramps, both fast jumps,44100-frame silent tails and unchanged exported media pass. The measured midpoint effective words are524,656,828,1040,1312,1648,2076. These are native stimulus checks, not physical cutoff measurements. The initial long run with unused broad research observers disconnected during the eighth note; root cause remains BUG-094 OPEN. Removing those auxiliary probes leaves every functional check intact and the normal-protocol run passes all14 cases.

For physical capture, load the TVF GRID performance, retain all14 original MIDI channels, and record the whole257second sequence as one mono48kHz/24bit WAV with the previous input gain and no normalization/dynamics/effects/sample-rate conversion. Preserve the starting/ending bypass and release gaps. This recording can independently test whether the fitted cutoff curve is a stationary transfer correction or compensation for moving behavior. Do not apply the system-disk repacker to this720KB sample disk. Generated template-derived media remains private. [Reproduction hashes, full stimulus/spec/sequence, exact native checks and limits](../../condensed/validation/filter-midpoint-capture-2026-10-16.json).

A prior native short-smoothing validation limit mislabeled TVFSTEP as R0. Its spec actually uses resonance64/damping85; that limit is corrected, with source hashes/results unchanged. The distinct earlier software-counted R0 experiments remain separate.
