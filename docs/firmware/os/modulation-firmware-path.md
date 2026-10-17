# Firmware modulation path audit — 2026-10-15

2026-10-16 static-analysis extension: [filter modulation dataflow](filter-modulation-dataflow.md) connects waveform-state preparation at 001F:4C9E through the mixer at 002D:83A5 to the per-voice base cutoff at 8516 consumed by 001F:46F1. It also identifies both initial-counter branches writing the companion cutoff pair. These are decoded firmware paths, not additional hardware timing validation.

The exact resonant fixture's native firmware arithmetic and word delivery agree with independent integer replay. A separate fast-envelope control path writes DSP register0x101018, which the current native audio paths do not interpret. Its physical semantics remain unknown; no guessed command behavior or production change was added.

## Exact resonant fixture

ROBO_TVF patch04/MIDI60 and its bypass/static controls were rendered from the existing supported checkpoint with an additive read-only Lua observer. Original ROM/system image, guest state and ordinary MIDI remain unchanged. The observer buffers input/counter snapshots and exports on normal shutdown.

| Check | Result |
| --- | --- |
| Firmware cutoff arithmetic versus emitted words |1336 exact |
| Firmware words versus native raw register writes |1336 exact |
| Signed envelope counter calculations |456 exact;0 mismatches |
| Sustain endpoint |210 zero-valued rows |
| Applied native words/coefficient decoding |7133 exact rows |
| Scored active coefficient changes |413; applied within1 native frame |
| Read-only observer versus baseline audio |2,249,100 stereo frames exact |

Two first/inactive coefficient sets are excluded from activation-delay scoring; waiting for a voice to become active is not a register-latching delay. These are emulator implementation checks, not measured hardware word timing or absolute MIDI latency.

Firmware001F:46F1–480B scales velocity/depth, adds and saturates the control value, then uses data-page02BE pitch words at9D34 and octave shifts at9ED8. It divides the interpolation difference by16 before multiplying by the fractional remainder, then shifts the final word right2. Moving the divide after the multiply produces140 incorrect raw words in this trace. The renderer separately applies its existing low-two-bit cutoff mask. No floating-point replacement of firmware arithmetic is needed or justified.

The original sweep uses internal levels32639/0/0/0 and divisor219 for its active rise and first decay. Stages2 and3 use linear signed multiply/divide calculations. The disassembly contains quadratic later-decay/release paths, but this particular patch does not exercise a nonzero quadratic segment: stage6 sustains zero and stage7 has zero delta. Its456 matching counter rows therefore qualify the observed linear calculations and zero release, not arbitrary envelope shapes.

[Exact rows, disassembly/input hashes, negative control and application checks](../../condensed/validation/resonant-firmware-path-2026-10-15.json).

## Companion DSP control path

The same firmware writes0x101018 around stage/voice operations. The current native audio router handles filter words at101008/0A/30/32, envelope words at101024/26/34/36, channel selection at101040 and activity words at101010/12. It does not interpret101018 in those audio paths. General bus/shadow storage does not implement the register's physical function.

The original resonant/control render emits36 such writes, including000A,000E,001B,001C and4E00. The original firmware's short-table prefix at02BE:AC7A is:

| Index | Word |
| --- | --- |
|0|0000|
|1|000E|
|2|0014|
|3|0018|
|4|001A|
|5|001B|

These are encoded words, not measured durations. Independent replay of21 observed short-table lookup rows across the original and survey traces matches the immutable table. Only observed indices1/4 are qualified by that lookup-row check; the remaining entries are recorded directly from the image, not new hardware observations.

## Fast versus software-counted envelope paths

Three existing survey notes were rendered with the same read-only observer and a matching unobserved baseline. Patch/disk bytes establish their Time settings; the observations distinguish firmware paths rather than infer physical milliseconds.

| Survey MIDI note | Time settings | Observed TVF behavior |
| --- | --- | --- |
|35|4/4/4/4|Software first-stage counter stays0; code001A appears3 times, followed by001B restorations; endpoint-style path |
|39|8/8/8/8|Software divisor4 and counted stages; no001A writes |
|73|72/72/72/72|Software divisor139 and counted stages; no001A writes |

The survey observer preserves926,100 stereo frames exactly. The fast trace recordsFFFF in the unused divisor slot; this is not a physical65535-tick transition. Its zero software counters plus short-table commands support a DSP-assisted fast-transition hypothesis. They do not prove a specific slew, interpolation, reset, latch or handshake law.

The Time80 resonant fixture follows the software-counted path. The fast-path gap therefore does not establish the cause of its remaining waveform error. Common command001B and other companion writes still need interpretation before their effects can be excluded for slow transitions.

[Raw control rows, per-note paths, table checks and audio identity](../../condensed/validation/modulation-firmware-controls-2026-10-15.json).

## Ordered companion transactions

A second read-only observer captured all writes to101000–101041, including the CPU fetch-page selector. It recorded3087 survey writes and12159 original-fixture writes with zero dropped rows. Audio remains exact across926,100 survey and2,249,100 original-fixture stereo frames.

All five observed101020 initial-cutoff writes equal the preceding101030 cutoff word (three survey notes and two original filtered controls; the bypass has no such write). Immutable firmware002D:9270 calls46F1, then writes zero to101022 and the resulting cutoff to101020. The current native audio router ignores this companion pair.

For survey Time4, the ordered sequence starts with101030=0A35 and101020=0A35, then101018=001A, channel selection,101032=0 and101030=01A0, followed by101018=001B. The next fast stage similarly brackets target0A35 with001A/001B. Captured fetch page002D locates the first command store at8106 (observed post-store PC810B); the firmware sets the envelope endpoint and calls46F1 before restoring001B at8125. This establishes command-scoped target writes, not the physical interpolation law.

The same command register also brackets TVA target writes to101034/36 with000E/001B. It therefore participates in both filter and amplitude control transactions. In the original Time80 sweep, recurring software-counted cutoff writes occur while001B is selected; a later endpoint update is bracketed by000E/001B. There is no per-control-tick command toggle. Any proposed timing model must account for this distinction, rather than attach an arbitrary ramp duration to every word.

This capture observes writes only. Status/readback semantics and command-to-duration mapping remain unqualified. No renderer behavior changed.

[Ordered writes, exact initial pairs, command bursts and PCM checks](../../condensed/validation/dsp-companion-transactions-2026-10-15.json).

## Fast-command discrimination against existing recordings

The existing survey ZIP contains only two Time4 notes, MIDI35/36; MIDI37–39 are Time8 controls. Source phase/alignment and constant gain were fitted on0.2–1.2seconds only, with the previously measured clock ratio fixed. Startup was evaluated at5–80ms and later audio at1.2–1.35seconds. Times are relative to the silence-trimmed recording, not MIDI events. The80–1500Hz diagnostic compares identical offline source/filter models with different coefficient trajectories.

| Note | Time | Immediate targets: startup error | Retain initial cutoff: startup error | Later error |
| --- | --- | --- | --- | --- |
|35|4|35.285%|1.840%|1.625%|
|36|4|54.754%|48.736%|1.486%|
|37|8|60.588%|not tested|1.503%|
|38|8|41.232%|not tested|1.651%|
|39|8|77.741%|not tested|1.832%|

For MIDI35, retaining the initial2612 masked cutoff instead of applying the first416 target removes a native-trajectory dip of about12ms. This is a diagnostic ablation, not a proposed instruction to ignore target writes. Its large improvement does **not** transfer to MIDI36. Likewise a20ms linear command ramp improves each Time4 aggregate startup score, but for MIDI35 it damages the already accurate15–35ms region: local gain-fitted residuals rise from1.82/1.58% to47.28/11.70%. Neither result qualifies a shared command law. Comparing local windows prevents an onset improvement from hiding a later regression.

The cubic source replays native audio for MIDI37–39 within5.02e-8 relative RMS. It does not replay native MIDI35/36: those lie below the opt-in source candidate's supported pitch range and on its excluded exact quarter-speed kernel, respectively (native replay residuals53.76/50.72%). Their table values therefore isolate cutoff trajectories using an offline source that fits later hardware audio; they are not direct native waveform acceptance. Source-model sensitivity was also checked with linear reconstruction. There is no low-note bypass calibration, independent repeat, hardware MIDI anchor or separated TVA onset control. No production behavior changed.

[Per-model results, local windows, native replay checks and input hashes](../../condensed/validation/fast-command-discrimination-2026-10-15.json).

## Time8 separation of amplitude, state and control trajectory

MIDI37–39 use Time8 and lie inside the native source candidate's supported range. Their offline cubic source/filter replay agrees with native output within5.02e-8 relative RMS. Audio alignment/gain remain fixed from the prior later-note calibration; the new diagnostic fits only control trajectory phase or initial state on alternating5ms blocks within5–150ms and scores the other blocks.

| Note | Immediate trajectory | Initial filter state fit | Causal20ms ramp + control phase |
| --- | --- | --- | --- |
|37|66.59%|73.43%|3.96%|
|38|44.09%|45.28%|3.01%|
|39|78.12%|83.62%|11.62%|

Even an oracle amplitude correction fitted separately every5ms leaves odd-sample evaluation errors50.49/40.54/66.25%, respectively. Its scoring split differs from the table, so those numbers are supporting discrimination, not identical-score rankings. Initial filter state or scalar TVA gain alone does not explain these waveforms within this model. A delayed held trajectory helps, but a causal ramp helps more. A10ms one-pole nearly ties the20ms linear ramp on MIDI39 training; the linear ramp performs better across MIDI37/38. These three notes form the model-selection set. No shared phase offset is inferred.

[Time8 models, initial-state fits, amplitude controls and causality checks](../../condensed/validation/time8-onset-discrimination-2026-10-15.json).

## Frozen20ms ramp transfer

Before evaluating MIDI40/43/47/51, the candidate was frozen to a causal linear coefficient ramp lasting882 native samples (20ms), starting from the observed companion word416. Each received target restarts a ramp from the current interpolated value. No duration, curve shape, cutoff map, damping, source clock or gain adjustment was selected on these four notes. Source alignment and constant gain use1.5–2.7seconds, after the short envelope has settled. Only a constant control-phase offset is fitted on alternating5ms blocks of5–500ms; other blocks are evaluated. A separate zero-phase ramp isolates the improvement without that diagnostic offset.

| MIDI | Time | Immediate native trajectory | Held trajectory + phase |20ms ramp, zero phase |20ms ramp + phase |
| --- | --- | --- | --- | --- | --- |
|40|8|23.92%|11.74%|2.30%|2.04%|
|43|12|27.48%|12.05%|6.04%|2.60%|
|47|16|22.94%|7.41%|8.05%|3.05%|
|51|24|9.14%|5.06%|3.23%|2.92%|

All percentages are relative RMS waveform residuals in80–1500Hz on the evaluation blocks. Native source/filter replay agrees within5.02e-8 for all four notes. A future-target perturbation leaves earlier ramp output bit-identical, qualifying the candidate's causality given its input sequence. The fitted control phases are−0.439/+3.013/+5.749/−1.909ms. They are comparison parameters for recordings with independent firmware/control-tick origins, not measured hardware MIDI latency. Negative offsets must not be implemented as future-write lookahead. The zero-phase column remains causal relative to the native writes and improves every note.

This supports investigating a missing transition between software-counted cutoff targets, rather than changing envelope speed or amplitude alone. It does not decode101018, qualify the fast Time4 command path, or establish20ms as an exact hardware constant. These are reused analog recordings with no independent bypass calibration/session. The separate Time80 resonant fixture still has substantial residual under the earlier20ms diagnostic; this result does not resolve that test or qualify all modes/resonances. Native playback remains unchanged.

[Frozen transfer, exact source replay, causality and input hashes](../../condensed/validation/control-ramp-transfer-2026-10-15.json).

## Native opt-in ramp and original resonant rerun

`S760_NATIVE_CUTOFF_RAMP_CANDIDATE=1` now implements the diagnostic in the native driver, off by default. It initializes from101020, ramps changed quantized LP cutoff targets written under001B over882 active44100Hz samples, and retains immediate fast-command targets. The filter recurrence and coefficient map are unchanged. `render_c` in applied trace rows records the actual interpolated coefficient; the original `c` remains the raw target.

| Native validation | Result |
| --- | --- |
| Disabled versus prior executable, same native state |1,234,800 stereo frames exact |
| Enabled offline audio replay, four survey and two filtered original cases |within5.00e-8 relative RMS over the scored first2.7seconds |
| Independent ramp recurrence checks |maximum coefficient difference6.36e-15 |
| Original bypass/static controls |1,499,400 stereo frames exact |
| Save/restore during an active ramp |4096 stereo frames exact |
| Final executable versus audited enabled build |1,234,800 survey and2,249,100 original-fixture frames exact |
| Real-runtime bus trace |131072 PCM frames and both displays exact |
| Builds and tests |Native/CMake builds, core/plugin tests;404 pytest passed,0 skipped |

The authoritative disabled regression uses the same native state. Earlier fresh-boot attempts are excluded: even padding both runs to an identical sample-clock origin leaves their firmware control-tick phases different after host-driven media loading. The private cross-build regression first asserts normal managed identity rejection, verifies all other identities and blob integrity, then uses the existing native raw-state endpoint without changing guest state or save headers. Default native save registration remains unchanged. Experimental ramp state is registered only when its flag is present; experimental checkpoints require the same profile on restore. Supported cross-build session migration remains unavailable.

The original LP/R64 sweep was rerun with coefficients actually rendered by the native driver, through the same recording-band source/lane comparison and fixed measured source clock used earlier. Only constant source phase and audio alignment were fitted on training blocks; no envelope speed, gain, damping or coefficient fitting was introduced.

| Accepted recording | Immediate native trajectory | Native ramp trajectory |
| --- | --- | --- |
|Quiet|44.13%|19.99%|
|Repeat|46.31%|21.35%|

These evaluation residuals establish an improvement in that diagnostic, not direct native-WAV hardware acceptance. They agree with the earlier offline20ms results and still leave substantial resonant error. The previously reported roughly18% result used a different inferred/interpolated trajectory and is not the immediate native baseline in this table. Fast command semantics, full modulation parity and the remaining resonant mismatch stay open.

[Native implementation, exact comparisons, checkpoint replay, resonant results and build identities](../../condensed/validation/native-cutoff-ramp-2026-10-15.json).

## Next work

The causal native diagnostic is validated and the original resonant comparison has been rerun. Keep it opt-in while separating the remaining resonant dynamics from the still-undecoded control law; its LP/R0 transfer does not qualify all modes or resonances. Retaining the initial cutoff remains rejected as a shared fast-path fix. BUG-005 remains OPEN.


## Software control scheduler: original-firmware rearm audit (2026-10-16)

The timer ISR at instruction page0:CAD1 (file52D1) reads IOS1. For software timer0 it samples TIMER1 atCB00, saves that value, switches instruction pages to001F/002D, and calls the control service. On return, if elapsed work is at most0x4A38 (19000) ticks, CB51 rearms HSO command0x38 at saved TIMER1 +0x4E20 (20000). The fallback atCB5B instead uses current TIMER1 +1000; it was not observed in this audit. The original firmware therefore schedules from its service-time timer sample, not from the preceding scheduled deadline.

An additive read-only register-space trace of the exact opening/closing fixture captures9493 timer accesses with zero dropped rows. All1808 observed rearms equal the correspondingCB00 read plus20000 modulo65536. All1807 consecutive intervals equal20000 plus the next service sample's lateness relative to that target, within1.01microseconds of timestamp quantization. The native KB model uses16MHz and16 oscillator cycles per TIMER1 increment, i.e.1microsecond per tick.

Over0.1–4.2seconds of each ramp, opening mean period is20.071366ms and closing20.068112ms. Mean lateness is71.368/68.113microseconds; handler work before rearming is about1.098/1.095ms. Thus handler execution time is not added wholesale to the20ms period: the saved pre-service timer sample is used. Lateness includes interrupt delivery, masked/competing work and the ISR prologue beforeCB00; these components have not yet been separated. No physical hardware interrupt timestamps were captured.

This fresh run lacks a same-state observer-disabled comparison. Its periods differ from earlier20.050–20.053ms fresh runs, whose setup/phase is not controlled against this run. Do not attribute that difference to the observer or to a CPU defect without a matched-state test. The observer's `page` column records the data-page selector, not instruction fetch; disassembly uses the established code-page0 mapping. The TVF stage dispatcher is instruction page002D:8000 (fileFC00); the older private disassembly's7800 display origin is offset and must not be used as a runtime PC.

This identifies a mechanism by which servicing delays accumulate in native modulation timing. It does not establish incorrect hardware timing or authorize a guessed speed correction. Next localize deadline-to-service delay with matched-state observation of interrupt masking and competing firmware work. No emulator/ROM changes.

[Raw matched interval rows, timer disassembly, identities and limitations](../../condensed/validation/tvfstep-scheduler-combinations-2026-10-16.json).


## Current-build matched scheduler localization (2026-10-16)

The newly decoded OS explains a concrete native cadence mechanism. Original page0000:CAD1 samplesTIMER1 atCB00 and rearms from that saved service sample plus20,000 ticks atCB51. Page004B:57B4..5811 is specifically the **mouse four-nibbleF008 handshake**, not generic panel polling: PUSHA masks interrupts, port sampling and counted delays run, andPOPA restores them. This identification matches nativeF008 read/write ownership and original byte-checked instructions.

Fresh current-build opening/closing notes were saved/restored only through supported same-build checkpoint APIs. For each direction, observed and unobserved22,050-frame PCM windows match exactly, and repeated unobserved replay matches; zero trace rows dropped. No guest state, original firmware, production timing or DSP equation was patched. The earlier matched run used a different executable and is not pooled.

| Direction | Timer intervals | Mean period | Mean interrupt-delivery delay | Maximum delivery delay | ISR prologue |
| --- | --- | --- | --- | --- | --- |
| Opening |24|20.071802ms|63.078us|130.375us|9.125us|
| Closing |24|20.068255ms|59.563us|123.125us|9.125us|

All48 rearms equal savedTIMER1+20,000 modulo65,536. In each direction12/24 intervals have delivery delay above2us; **all24 such delayed intervals** deliver at004B:5812 immediately following the handshake'sPOPA. After-deadline samples show interrupts disabled, and the actual200A vector reads targetCAD1. The9.125us prologue is constant across all48 intervals. In these windows, mouse-handshake masking supplies the variable delay; servicing time rather than prior-deadline rearming lets it accumulate. Handler work itself is not simply added to each20ms period.

This is an independently reproducible **native timing contributor**, not proof of incorrect physical timing or the complete filter mismatch's cause. Both directions show roughly0.35% extra mean interval, whereas prior analog fits wanted different opening/closing adjustments. A global speed correction therefore remains unsupported. The half-second windows do not establish full-ramp/load bounds. Existing firmware-word and application traces already show exact arithmetic/word delivery and application within one audio frame; that narrows the remaining question toward physical update scheduling and companion-command/coefficient-transition behavior, including still-uninterpreted101018. Static boot-ROM DSP initialization helps bound initial state but does not establish the ASIC's runtime transition law.

[Matched interval records, PSW/stack/vector contexts, original instructions, executable/fixture identities and reproducible analysis](../../condensed/validation/filter-scheduler-localization-2026-10-16.json). BUG-005 staysOPEN. No new hardware capture is requested by this result; use existing ramp/step/static/bypass controls to test whether a candidate preserves both directions before any production correction. A direct physical control-write/IRQ trace would be needed to claim hardware cadence parity.


## Verified CPU state-time correction (2026-10-16)

The follow-up found a real emulator defect beyond the original firmware's mouse masking: nativeKB CLRC,SETC,DI,EI,CLRVT,NOP used4states, whereas Intel270651-003 Table3-3B specifies2. The native path now uses2; the legacy path retains4. No CPU clock, OS/ROM, rearm policy, filter equation, cutoff map or hardcoded rate adjustment changed. BUG-091 isFIXED.

An isolated CPU execution fixture cancels identical marker overhead. For each opcode,2048 repetitions measured1024us before and512us after, exactly matching16MHz/two oscillator cycles per state. This proves the changed instruction timing under the model; full CPU bus/IRQ timing remains outside the result.478 full regressions pass, with4 previously documented source-builder expected failures. Native original-firmware boot, mouse input, playback, zero release tail and clean shutdown pass.

Fresh paired observer/baseline/repeat audio windows again match exactly, with no dropped rows. Opening/closing mean control periods are now20.009266/20.009078ms; ISR prologue8.875us versus9.125us before, consistent with itsEI correction. In these particular half-second windows, no delivery ends at the mouse handshake; the few delays above2us occur at00DB:92FA. Before/after runs have different setup/tick phases, so the dramatic mean-delay reduction is descriptive and is not proof that mouse blocking never recurs or that hardware waveform error is fixed.

BUG-005 remainsOPEN. The next acceptance operation is to regenerate the same TVFSTEP/resonant native reference on this new executable and apply the existing frozen ramp/step/static/bypass comparison rules against hardware recordings. Previous native coefficient schedules and checkpoints belong to their recorded build; do not reuse them as if current. The still-uninterpreted101018 control register remains a separate potential transition-law dependency. [Exact code change, Intel source, measured before/after, builds, regression results and limitations](../../condensed/validation/native-kb-state-time-fix-2026-10-16.json), [after-fix matched scheduler rows](../../condensed/validation/filter-scheduler-after-state-time-fix-2026-10-16.json).


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
