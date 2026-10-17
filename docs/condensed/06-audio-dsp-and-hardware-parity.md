# Audio DSP & Hardware Parity

## Current status — static filter correction2026-10-14

Static C64/R64 BP/HP capture comparison now passes the1% waveform target:0.07924% BP and0.10408% HP on the withheld interval, with unchanged428/85 equations. Corrected capture analysis retains DAC image harmonics present in the48kHz recording and uses training-only timing/gain. The former HP1.59% failure was analysis aliasing. Moving/resonant response remains BUG-005; no native filter constants changed. [Correction, controls and identities](validation/static-filter-capture-correction-2026-10-14.json).

### Historical2026-10-10 review

Finding124 establishes sub-1% normalized RMS agreement for the documented interpolation captures and settings, with an opt-in native implementation. Loop/envelope and filter audition work has progressed beyond the earlier raw monitor. Physical dynamic-resonance fidelity remains open. Normal-default combined-path qualification is recorded below alongside historical diagnostic evidence. Dated findings below preserve the investigation history; early claims that interpolation is unresolved or filters are absent are superseded within the tested domains by the later findings.

See the [completion roadmap](../project/completion-roadmap.md) and [native runbook](11-native-boot-and-audio-runbook.md).

## Normal filter profile — 2026-10-14

Python and C++ VST3 launchers now enable the existing native filter renderer
alongside stereo, interpolation and envelope/loop processing. No coefficient
algorithm changed. Normal72-case firmware acceptance covers bypass, LP32/64/96,
resonant LP64 and nonresonant LP/BP/HP sweeps at MIDI57/60/63 and three pan
positions. Finite bounded output, spectral/cutoff effects and silent release pass.

Native filter words require44.1kHz, command0, cutoff<=0x3fff and damping<=0x0fff.
LP mode0 accepts that damping range; BP0x0400/HP0x0200 accept only damping0x0fff
or85. Other words/clocks retain the raw path and clear filter history. Firmware
coefficient writes are stepped. Exact moving/resonant response remains outside
the qualified domain; BUG-005 is still open.

Normal seven-mode/retrigger acceptance replays1,058,400 frames exactly. Firmware
partial edit/Save/fresh Load preserves the measured octave change; native cold
scheduled/SCSI recall reproduces131072 stereo frames and refreshed displays.
Variable PCM/scheduled MIDI and paced48/96kHz variable-block plugin tests pass;
these are not physical device-latency or final-package measurements. All363
backend tests and core/plugin unit suites pass.

Standalone state uses audio profile `native-stereo-filter-interpolation-44100-v2`;
old bypass-profile archives require their matching application. VST3 rebuilt-module
identity already enforces the same-build state rule. Recording remains opt-in.
Actual SoundCheck SDK host acceptance passes nine named LP/bypass/pan cases,
silent releases, editor reopen and220500 exact fresh-instance replay frames
with variable blocks. Active LP-history cold native recall separately matches
65536 frames. The first host attempt times out on editor readiness; the second
hits existing BUG-060 block rejection. Fully paced repetition passes, without
a production reliability fix or closure of BUG-060.
[Exact artifacts, commands, results and limits](validation/milestone-5-normal-filter-2026-10-14.json).

## Supported loop-mode acceptance — 2026-10-14

Current native firmware Load/playback acceptance covers all seven ROBOLOOP modes
at 44.1 kHz/unity pitch. Five repeating modes match the fixture sign/direction
sequence exactly, including reverse and alternate; both one-shots finish while
held, and all modes release silently. Eight overlapping seven-mode retrigger
cycles deliver 112 note-ons per run and exact replay of 1,058,400 stereo frames
from a same-process checkpoint, with a full second of silence after each cycle.
This is native functional evidence, not voice-count/stealing, simultaneous disk
activity, cold-process recall, realtime device timing or physical parity.
Named octave transitions are now qualified below. Reproduce with
`python scripts/verify_native_runtime.py --loop-modes --loop-stress` and explicit
absolute `--sample-disk` ROBOLOOP and private `--state-dir` paths.
[Identities, command, measured rows and limits](validation/milestone-5-loop-modes-2026-10-14.json).

## Bounded native allocator acceptance — 2026-10-14

ROBOFULL original-firmware Load and serialized MIDI allocate all 24 playable
wave slots. Each of eight excess notes disables/re-enables a slot (24 to 23 to
24 enabled voices). Releasing all original notes preserves eight replacement
voices; releasing the replacements clears the bitmap and leaves a full second
of exact silence. Eight single-note retriggers and sustain hold/release also
pass counted allocation and silent-tail checks. Read-only bus traces have no
dropped rows. This establishes bounded native allocation/release behavior, not
exact hardware steal priority, arbitrary layered-patch behavior, concurrent disk
activity or a spectral proof of every mixed voice.
[Measured rows, identities and reproduction command](validation/milestone-5-polyphony-2026-10-14.json).
The [workflow matrix](../testing/milestone-5-acceptance.md) separates completed and pending
product coverage.

## Native loop/pitch acceptance — 2026-10-14

A private ROBOLOOP-derived fixture copies partials and adjusts their coarse tuning
and key map, preserving all sample records and PCM. Original firmware loads all
seven modes at -12/0/+12 semitones. Read-only pitch observations match8192/16384/
32768; repeating modes have >0.99 correlation at their expected recurrence lags,
one-shot durations scale within8 frames of expected, and all notes release to a
full silent second.42 overlapping transitions across those mapped notes remain
finite/bounded and release silently. This is functional octave/key-transition
acceptance, not continuous glide, arbitrary ratio, click-free transition or new
physical interpolation parity. For odd-length loops at double speed, recurrence
uses two cycles to obtain an integral lag; pitch observations independently verify
speed. Existing physical measurements retain their original domain limits.
[Commands, fixture recipe/hash, pitch traces and PCM metrics](validation/milestone-5-loop-pitch-2026-10-14.json).

## Diagnostic combined-path acceptance — 2026-10-14

The explicit native diagnostic profile enables stereo and the existing filter
monitor alongside interpolation/envelopes.72 original-firmware cases cover bypass,
LP static cutoff32/64/96 at resonance0, LP cutoff64/resonance64 and LP/BP/HP
nonresonant sweeps, at MIDI57/60/63 and pan0/64/127. All produce finite bounded
output, correct stereo routing and a silent release second. Static cutoff changes
alter spectral balance; the moving LP patch changes RMS across its envelope.
These are functional assertions, not physical moving/resonant filter equivalence.

The historical six-case baseline confirmed BUG-061: Python normal output
bypassed stereo gains. The later normal-profile correction enables the stereo
mixer and passes six pan cases, variable-block audio and131072-frame cold replay.
Normal filter selection/default qualification remains open; the diagnostic result
does not promote filtering.
[Normal stereo qualification](validation/milestone-5-normal-stereo-2026-10-14.json). The profile is explicitly
opt-in and has separate checkpoint identity;363 backend tests pass.
[Commands, identities,72 diagnostic rows and baseline comparison](validation/milestone-5-combined-audio-2026-10-14.json).

## Technical reference and dated milestone history

Milestone labels below apply to their cited finding, not to the present project status.


Condensed from the DSP architecture, recording methodology, testing guide, and
LLE roadmap. Source descriptions mix implemented software models with claims
about original silicon; keep those categories distinct.

## Audio path and software model

The Windows standalone exposes persistent MAME output-backend selection
(Automatic/WASAPI/XAudio2) and a requested 0–1000 ms buffer target. Zero uses the
backend default; WASAPI/XAudio2 use 30 ms for zero and clamp nonzero values to
10–1000 ms. Native transport stays stereo 44.1 kHz. Normal-speed WASAPI with a
60 ms target passes original-firmware boot/load/play/release and shutdown;
this checks native WAV PCM, not physical loopback or audible latency. Device
selection, negotiated rate/conversion, sustained dropout and measured latency
qualification remain open. See
[exact configuration evidence](validation/standalone-audio-settings-2026-10-12.json).

The physical path uses MB87422/MB87423 wave ASICs (IC27/28), MB87424 TVF (IC29),
TC24SC220 MEQ mixer (IC30), and AK4328VS-E DACs (IC91/92). The ADC is
**CS5339-K (IC58)**, not AK5339. These identities are visually confirmed in
service-note parts list p.5. Specifications p.1 establish **24 hardware voices**
and **Differential Interpolation (DI)**. The software models have 32 voice slots.

**Maximum polyphony = 24 voice channels, one voice per partial.** A mono,
single-partial note consumes one channel → up to **24 simultaneous notes**; a
stereo sample or a 2-partial-per-key patch consumes two channels per note →
**12-note** polyphony. This is confirmed in firmware: the MEQ init loop at bank
001F:527D..5288 configures exactly 0x18 (24) channels in MEQ registers
101840..10186E, and the voice-routing loop at bank002D:B320..B337 allocates
across channels **0–7 and 16–23** (skipping the reserved diagnostic slots) for 24
playable channels. The 32 initialized register slots are therefore NOT 32
playable voices.

Current architecture correction (2026-10-14, BUG-008): standalone and native VST3 use the same modified MAME machine implementation, including its `s760_sound_device` renderer, through isolated runtime processes. The VST3 worker transports MIDI/PCM and converts host output rates. They do not link or render through `S760HardwareCore`.

`S760HardwareCore` in `core/include/s760/s760_core.hpp` and `core/src/s760_core.cpp` is an unlinked reference model, deliberately absent from the product CMake source list. Its Hermite interpolation and four-stage resonant filter are software experiments; their presence is not evidence of product integration or hardware parity. The earlier shared-reference-DSP completion claim is withdrawn. Native reference replay qualifies software agreement for named workflows; physical fidelity retains its measured limits.

## Native firmware voice interface (2026-10-10)

**MILESTONE (findings 64–71): the native OS loads real samples and produces
audible native-wave audio.** Original-ROM boot + a mouse-operated Disk > Load now
loads an actual performance (TX81Z waves) from a swapped sample floppy, maps
on-screen keyboard notes to genuine Wave Custom voice/control transactions, and —
with an opt-in monitor — renders a verified non-silent stereo waveform with a
firmware-driven amplitude envelope. All driven by unmodified firmware + host
input; no synthetic notes or forced state. This is a diagnostic audio path, NOT
finished MB87422/24 + MEQ + DI emulation (filter/mixer/pan/DI/loop-mode fidelity
all remain open — the filter/mixer decode is delegated to Gemini in task 68).

Finding64
establishes sample loading end-to-end. Two blockers were fixed: (a) a CPU **BMOV**
(`0xC1`) over-fetch — the generated core fetched the two operand bytes twice,
consuming the next instruction and corrupting the directory-buffer copy; (b) the
**IC4 control-`BC` RAM→wave DMA** (programmed at bank005A:6A31..6A73 via wave
address C00E/C00C, RAM source 011A..011C, count 0118, control BC) was implemented
as a bounded synchronous copy. Result: the TX81Z single disk completes **23 wave
DMA transfers and 211,968 wave-memory bytes that match the original disk**
byte-for-byte (`verify_wave_64.py` replays disk→RAM→wave ranges). `S760_SAMPLE_FLOPPY`
+ host action "Insert Sample Floppy (F5)" swaps media while the FDC is idle. Audio
not yet produced at this step — wave data just reaches the guest wave-memory model.

Finding65
records 6,676 native sound-aperture writes after original-ROM boot and TX81Z
sample loading. Wave parameter selection uses physical `100400 + slot*10h +
parameter*2`, followed by data at `100014`. A second bank selects through
`100200 + slot*10h` and receives paired words at `100010/100012`.
The tested playable channel0 uses wave slot4. Two notes D#2/F#3 retain their
address fields and change pitch parameter2 from `0677` to `0F60`, a ratio of
14.9988 semitones. Firmware writes a wave-slot enable mask at `100000/100002`.
Downstream channel selection occurs at `101040`; release changes a parameter
at `101034` before clearing the wave enable bit.

Finding69
verifies the firmware side:316 writes to `101034` match the doubled high word
of a per-channel product, and68 release updates match a quadratic integer
calculation generated by the OS. Initialization separately sets bit15 and writes
a companion value to `101024`; its meaning, hardware gain scaling and smoothing
remain unresolved. The raw monitor currently bypasses these coefficients.

Finding70
adds storage for the four envelope/companion words per channel:902 updates
across32 selectors match independent bus replay. Original code also writes
`8000` on a state-clear path, supporting a control-bit interpretation without
establishing its precise action. No audible envelope or hardware gain law has
been established by finding70.

Finding71
adds a separate opt-in coefficient audition (`-EnvelopeMonitor` in the native
launcher): low15 bits of `101034` divided by32768 multiply the raw waveform.
This is a provisional diagnostic gain model, not an established MB87424 law;
command-bit action, companion words and smoothing are bypassed.311 captured
intervals match the chosen scaling within one PCM16 unit, including release to
zero. Raw-only playback remains bit-identical to67; default sound is unchanged.

Finding72
extends this to six rapid/short/long mouse auditions:330 audio intervals,
1486 envelope writes and2610 wave-register updates pass. The firmware stops
and reuses channel0, so this is retrigger coverage, not simultaneous polyphony.
The driver has no host MIDI input connection yet.

Finding73
corrects the proposed CPU-UART route: MIDI IN reaches IC4 RXD pin38. Firmware
receives/transmits bytes at0116 and polls0114 bit1 after transmit. IC4 receive
interrupt dispatch remains unresolved; direct CPU-serial injection is not a
verified route to firmware multi-voice allocation.

Finding74
adds an **opt-in IC4 experiment**: serial MIDI bytes are latched at0116 and
source6 is hypothesized to supply vector0138.18 bytes reach the OS parser and
allocate three overlapping voices, verified by register replay and a three-tone
WAV. Vector arbitration, FIFO/overrun behavior and MIDI output remain unresolved;
this is successful firmware compatibility under an explicit peripheral model,
not proof of exact IC4 behavior. Default-mode raw audio is unchanged.

Finding76
verifies firmware pan tables and all24 channel tag pairs, with MIDI CC10 values
0/64/127 selecting07FF:0000,0596:0596 and0000:07FF for separate notes.814 writes
match independent bus replay. Optional `-StereoMonitor` adds provisional Q11
coefficient audition and implies the envelope diagnostic. Left/centre/right
WAV comparisons agree within one PCM16 step; disabling it preserves74's chord
bit-for-bit. Hardware gain law, clipping, smoothing and output routing remain
unresolved. See finding76.

These are verified transaction sequences, not complete ASIC semantics. Absolute
pitch normalization, address endpoint/loop behavior, and DI remain open. Thirty-two
initialized slots do not imply thirty-two playable voices — and finding72's rapid
retrigger stress (6 note cycles, holds of 1/8/180 frames, all returning to silence)
all reuse channel 0 / wave slot 4, so it does NOT demonstrate simultaneous
polyphony. Finding74 separately demonstrates three overlapping firmware-allocated
voices through the experimental MIDI path (see below).

### Downstream TVF + MEQ evidence (68, reviewed in75–78)

The board identifies IC29 MB87424APF (TVF) and IC30 TC24SC220AF-007 (MEQ).
Firmware transactions establish a channel selector at101040, envelope words
at101024/26/34/36, and coefficient/command pairs at101C00/06. Exact IC30
chip-select coverage across101800 and101C00, and address aliases, still need
independent wiring verification; Gemini's IC10 decode interpretation is not
yet an implementation specification.

- Runtime includes both flagged and unflagged101030 writes, including nonzero
  unflagged values. The earlier universal bit15 requirement is withdrawn.
- Original OS002D:B1EF..B246 clamps pan to±32 and selects complementary65-word
  tables through data bank02BE at B38A/B41A. Channel tag tables B4BC/B4D4 select
  the DC06 command after the coefficient is written to DC00. OR0200 is observed;
  bit9's physical function is unresolved.
- A24-store initialization reported in68 at101840..10186E does not by itself
  establish24 distinct hardware volume registers or an attenuation law. Those
  labels and any alias model remain unverified.
- Resonance and mode addresses are verified in78 below. Filter transfer function,
  gain law, clipping and routing remain open; writes do not establish topology.

Finding77 verifies646 recurring101030 writes against original firmware arithmetic
at001F:46F1..480B, covering note velocities1/64/100/127 and channels0..2.
Velocity/depth scaling and a saturated control value feed the193-word9D34
pitch table and9ED8 octave shifts; interpolation truncates its difference/16
before multiplying by the remainder, then shifts the result right2. This proves
the firmware coefficient calculation, not a frequency-in-Hz or hardware filter
law. The tested sensitivities/depths are nonnegative. Separately, six writes to
101008 match the A3EE lookup (partial404D plus signed patch40EF, clamped0..127,
lookup then right4); its resonance label was subsequently verified in78.
See finding77.

Finding78 isolates original-OS edits: displayed Resonance0→1 changes partial404D
and101008 from0FFF→0F0F, matching A3EE wordsFFFF/F0F5 shifted right4. Displayed
LPF/BPF/HPF select10100A words0000/0400/0200 respectively. Stored partial404B
values00/01/02 are incremented before the A4EE lookup. Off (storedFF) bypasses
the lookup and writes10100A=0000,101008=0FFF,101032=0000,101030=BFFF; the mode
word alone cannot distinguish Off from LPF. These are verified firmware control
semantics, not measured chip transfer functions. Finding78
includes screenshots, input scripts and independent trace/table validation.

Finding79 implements write-side storage for101008/0A/30/32 using the shared
101040 channel selector. All control bits and companion words are retained;
518 writes across five channels match independent replay, including OffBFFF
and post-release8000. The storage resets and is registered for save states
(round-trip untested). Stereo PCM is bit-identical to76. No filter transfer
function, readback, command-bit action or selector aliasing is inferred.
See finding79.

Finding80 identifies101012 (low16) and101010 (high16) as a global packed voice
bitmap, independent of101040. Firmware computes low=`(L>>4)|((H&FF)<<8)` and
high=`H>>8` from wave shadows L=2A94/H=2A8C. New write-side storage preserves
all bits without inferring hardware gating. A24-note MIDI test reaches wave
FFF0FFF0/filter00FFFFFF, then releases both to zero;144 bytes,194 bitmap writes,
4,997 wave writes and9,030 envelope writes validate. All24 channel selectors are
covered. Stereo regression is unchanged; this establishes firmware allocation
and register coverage, not24-voice audio parity. Remaining101018 and companion
transactions still need interpretation. See finding80 in the shared index.

The2026-10-15 exact-fixture audit verifies1336 firmware cutoff calculations and
raw-word deliveries,456 envelope counter calculations, and7133 applied native
word/coefficient rows.413 scored active changes apply within one native frame;
first/inactive sets are excluded. Read-only observation preserves2,249,100
resonant/control stereo frames exactly. This establishes native implementation
agreement, not physical envelope timing or ASIC arithmetic. The active rise and
first decay in that fixture are linear; its later quadratic/release segments
have zero delta and do not qualify nonzero quadratic behavior.

Companion DSP control101018 remains uninterpreted in the native audio paths.
Firmware short-table words at02BE:AC7A begin0000/000E/0014/0018/001A/001B.
Survey Time4 takes a zero-software-counter,001A-command path, whereas Time8/72
use software divisors4/139.21 observed lookup rows match the original table;
926,100 survey stereo frames remain exact under the observer. This supports
investigating hardware-assisted fast transitions, not assigning command values
to milliseconds or implementing guessed latching/slew behavior. It does not
prove the cause of the separate Time80 resonant residual. BUG-005 remains OPEN.
[Firmware arithmetic/application validation](validation/resonant-firmware-path-2026-10-15.json)
and [companion-control validation](validation/modulation-firmware-controls-2026-10-15.json).

Ordered write observation additionally confirms five initial101020 cutoff words
equal the preceding101030 word, with command-scoped fast target writes and TVA
target writes sharing101018. This establishes transaction ordering, not a slew
law. An offline onset check retaining the initial cutoff improves Time4 MIDI35
startup error35.285% to1.840%, but fails transfer to MIDI36 (54.754% to48.736%).
Longer ramps also damage later onset windows that already match. These two
low-note comparisons use an offline source outside the native candidate's
coverage; they are not direct native audio acceptance. Existing silence-trimmed
captures do not separate initial filter state, TVA onset and command behavior.
No shared command law or production change is qualified.
[Ordered transactions](validation/dsp-companion-transactions-2026-10-15.json)
and [onset discrimination](validation/fast-command-discrimination-2026-10-15.json).

Software-counted LP/R0 transitions have a stronger diagnostic candidate:
a causal20ms linear coefficient ramp selected on Time8 MIDI37–39 transfers
unchanged to previously unused MIDI40/43/47/51 (Time8/12/16/24). Evaluation
waveform residuals fall23.92/27.48/22.94/9.14% to2.04/2.60/3.05/2.92% with a
training-only constant control-phase offset per recording. The zero-phase
ramp alone yields2.30/6.04/8.05/3.23%. Native source replay matches within5.02e-8
for all four notes; future-target perturbation preserves earlier ramp output.
Initial-state and amplitude-only corrections explain much less of the Time8
onset mismatch. This supports investigating a missing cutoff transition,
not assigning a physical latency or decoding101018. Negative diagnostic phase
offsets must never become future-write lookahead. No native behavior changed;
fast Time4 commands and the separate Time80 resonant residual remain open.
[Time8 separation](validation/time8-onset-discrimination-2026-10-15.json)
and [frozen ramp transfer](validation/control-ramp-transfer-2026-10-15.json).

The native driver now exposes this as off-by-default
S760_NATIVE_CUTOFF_RAMP_CANDIDATE: changed LP targets under control001B ramp over
882 active44100Hz samples, initialized from101020; fast-command targets remain
immediate. No filter equation or default playback change. Same-state disabled
PCM matches1,234,800 prior-build stereo frames exactly. Enabled replay matches
offline reconstruction around5e-8; active-ramp save/restore reproduces4096
stereo frames. Original bypass/static controls remain exact. Experimental save
state requires its matching flag profile; default native save registration and
managed cross-build identity rejection remain unchanged.404 tests and native
runtime PCM/display checks pass.

Using the actually rendered coefficients in the existing recording-band model,
the accepted original resonant captures improve44.13/46.31% to19.99/21.35%
evaluation residual. This is a native-trajectory diagnostic with training-only
alignment/source phase, not direct WAV acceptance or a fix for the remaining
resonant error. The earlier roughly18% inferred/interpolated-trajectory result
is a different baseline. BUG-005 remains OPEN.
[Native ramp validation](validation/native-cutoff-ramp-2026-10-15.json).

Finding66 implements the observed wave selector/data write banks and enable mask;1,080 runtime updates match independent replay. Wave reads, synthesis, loop modes and downstream filtering/mixing are still incomplete. Native reset suppresses the independent host audition; the raw diagnostic output described below is now established, while complete native synthesis remains unfinished. CMPL decode and sticky VT are now corrected,
including the opcode used by alternate loop setup; those complete loop paths
still need runtime coverage.

Finding66
also verifies the firmware exponential pitch table and sample-rate correction
matrix. The arithmetic supports a `4000` unity pitch reference and candidate
output rates44.1/48/32kHz; hardware clock selection and full playback behavior
still need validation. See its numerical evidence rather than assuming these
inferences establish audio parity.

## MIDI path (finding73 — on the CPU gate array, not the CPU UART)

MIDI IN routes through IC3 PC410 opto-isolator to **IC4 HG62E33B08 RXD (pin38)**;
IC4 TXD (pin37) feeds the OUT/THRU select via IC5 HC125 (Service Notes p18). So
MIDI is handled by the **CPU gate array (IC4)**, NOT the 80C196KB UART — the
earlier "hook `i8x9x_device::serial_w`" idea is withdrawn. Firmware-visible byte
port is **0116** (RX at bank0000:CD1F `LDB R90,[0116]`, TX at bank001F:53AA),
with status **0114 bit1 = transmit-ready**; the receive ring is 512 bytes (wraps
1B6C→196C). The receive handler is at bank000F:0138 (`PUSHA; jump CD1F`), reached
through the external-interrupt path. Open: how IC4 selects the 0138 entry
(interrupt source/vector routing) — the live idle serial vector 200C is a plain
RET (CAA2), so the driver cannot receive real MIDI yet. Do not force the PC,
patch vector 203A, or synthesize a CD1F call. Connecting ordinary MIDI input via
the IC4 gate-array receive/status contract is the gateway to real polyphony.

**First firmware-driven polyphony via experimental IC4 MIDI (finding74,
`S760_IC4_MIDI_EXPERIMENT=1`, opt-in).** Both ROM and OS hold seven 4-byte
interrupt stubs at `0120 + 4*i`: source0 = FDC service, source4 = completion
(sets RB3 bit0), **source6 = the byte-receive handler at CD1F**, source2 = a
wave-related C000/C002/C016 service. The normal captured interrupt mask 0x54
includes bit6. The experiment feeds a standard MAME MIDI device through a
31250-baud 8N1 receiver into a one-byte IC4 latch (0114 bit0 = ready, 0116
consumes), and — only while a MIDI byte is pending, the backing vector is 0120,
and no FDC request is pending — substitutes the low vector byte so external
vector 203A resolves to the 0138 receive stub. It never writes vector RAM or
forces the PC. **Result:** an 18-byte MIDI chord (notes 60/64/67) traverses the
receiver, fires 18 normal external interrupts, and the firmware's own
parser/allocator produces **three simultaneous voices** (wave slots 4/5/6,
channels 0/1/2; enable masks 10h→30h→70h then 60h→40h→0 on release) — unlike the
channel-0-only mouse tests (finding72). FFT of the three overlapping tones
matches the monitor's predicted 263.07/331.40/394.07 Hz; 476 wave + 828 envelope
updates verified by independent replay. Hard limits: the IC4 vector response is
an **inferred model**, not measured — source priority, latching, FIFO
depth/overflow, reassertion, transmit path, and physical host-MIDI are all
unestablished; it is disabled by default and must not be promoted to normal
emulation until real IC4 arbitration/buffering is resolved.

## Raw native-wave monitor (finding67)

Finding67
adds an opt-in monitor consuming native wave RAM, pitch, position and enable
registers. Firmware bank0166:A4D1 selects PORT1 bits7:6 for internal clocks:
00=44.1kHz,10=48kHz,11=32kHz, matching the schematic mux and rate tables.
The original-ROM test selects44.1kHz and produces two tones plus verified
silent intervals. This is a diagnostic raw PCM path with fixed gain, provisional
linear interpolation/inclusive forward looping and no TVF, amplitude envelope,
MEQ routing or DI emulation. It is disabled by default; the interactive launcher
accepts `-RawWaveMonitor`. Signal evidence is in finding67.

## Legacy software command interface

The legacy audition model uses byte-valued address/data latches (`0xF008`/`0xF006` in
MAME). `S760HardwareCore::write_mmio_data(uint8_t)` selects voice in address
bits 4:0 and parameter in bits 7:5. The actual byte mappings are:

| Index | Parameter |
| --- | --- |
| 0 | Step=data/128, with zero changed to 1 |
| 1 | Step=data+1 (replaces the prior value) |
| 2 | Wave start=data×4096 |
| 3–4 | Loop start/end=data×256 |
| 5 | Active bit0; loop bit1; output bus in bits7:4 |
| 6 | Cutoff bits6:0; resonance=64 if bit7 set, otherwise 0 |
| 7 | Level bits6:0, volume=level/127 |

The earlier 16-bit packed protocol, 24-bit address writes, continuously packed
resonance/filter-mode and pan/envelope fields are **not this implementation**.
This is not the native firmware protocol above. Native `F008` is the mouse interface; silicon behavior beyond the observed voice writes remains an evidence request in `shared/`.
The separate D400 block is cleared by firmware but has no dedicated current
handler; its chip-select/function needs hardware evidence.

## Mathematical model retained for reproduction

For original sample rate `f_orig`, output rate `f_s`, MIDI note `N`, root `R`,
and fine tuning in cents, the modeled ratio is:

`r = (f_orig / f_s) * 2^((N - R + fine/100) / 12)`;
The source advances a floating-point `voice.pos` by floating-point `voice.step`;
it does not use the claimed 16.16 accumulator.

Hermite interpolation uses four neighbors `y0..y3` and fractional position `u`:

```text
c0 = y1
c1 = (y2 - y0) / 2
c2 = y0 - 2.5*y1 + 2*y2 - 0.5*y3
c3 = (y3 - y0)/2 + 1.5*(y1 - y2)
y  = c0 + u*(c1 + u*(c2 + u*c3))
```

The source's filter mapping is `fc = 20 * 10^(3*cutoff/127)` and
`k = 3.98 * (resonance/127)^1.4`. With `g = tan(pi*fc/f_s)`, each pole uses
`v = g/(1+g)*(x-s)`, `y = v+s`, `s = y+v`, with feedback described as
`x_in = x - k*tanh(y4)`. These equations document the behavioral approximation;
they do not prove the original coefficient tables, feedback timing, numerical
precision, or an actual implicit zero-delay solver.

## Real-hardware filter captures and the fitted LP model (findings 80–96)

The parity methodology below is now partly EXECUTED against real hardware.

**24-voice polyphony validated (finding80).** A 24-note MIDI chord (notes 48–71)
through the experimental IC4 receiver allocates all 24 voices at once (peak wave
mask FFF0FFF0 / packed filter mask 00FFFFFF). The global filter bitmap lives at
**101010/101012** (not 101040-selected): firmware packs it from the wave-enable
shadows as `101012 = (word[2A94]>>4) | ((word[2A8C]&FF)<<8)`, `101010 =
word[2A8C]>>8`. 194 bitmap + 4,997 wave + 9,030 envelope writes verified.

**First real analog captures (finding82).** The user supplied RoboSampler
recordings from the physical S-760 analog output (MIDI note 60, velocity 127,
48 kHz/24-bit): a reference/bypass plus LP sweeps at resonance 0 and 64. These
are genuine filter-response evidence (with analog noise-floor/clock caveats), the
first matched hardware data in the project.

**Fitted LP filter model (findings 83/84/85, static), validated natively (96).**
Of six candidate response families, a discrete two-pole state-variable form fits
both resonance settings best. The implementation recurrence is:
```
low  += c * band
band += c * (input - low - damping * band)
output = low
```
with **register scaling `c = cutoff_word / 16384`, `damping = resonance_word /
4096`** (cutoff word masked to drop the low 2 bits). On the STATIC captures this
predicts R00/R64 to −45 dB / −58 dB residual. The opt-in native audition
(`S760_NATIVE_LPF_MONITOR`, finding96) applies it per playable channel and
matches an independent SciPy reference at correlation 0.99999 (−41.96 dB).
Firmware filter words observed: R00 cutoff 0x01AE(430)/res 0x0FFF, R64 res 0x0055.

Hard limits (do NOT overstate): this is validated against **static** recordings
only; the **moving/sweep** resonant response does not yet match, the filter
**topology is not uniquely identified** (analog-form and bilinear two-pole remain
close at low cutoff), the cutoff low-bit precision (430→428, confirmed low-2-bits
cleared in finding108) and fixed-point width, saturation, update timing and reset
behaviour are unresolved. The model is opt-in/diagnostic, not the default audio
path, and not a hardware-parity claim.

**BP/HP filter modes (findings 98/99/106/108).** DSP mode register 10100A =
**0000 LP, 0400 BP, 0200 HP** (directly observed as the OS plays BP/HP patches —
these are DSP words, not patch bytes). Transfer forms share the LP denominator
`1-(2-c·d-c·c)z+(1-c·d)z`: **BP numerator c(1-z), HP numerator (1-z)²**, and
BP/HP use UNSCALED (unity) band/high — the damping-scaled BP hypothesis is
rejected (finding106). On STATIC captures at cutoff 428/damping 85: BP residual
−60.84 dB BP and1.59% HP were the historical4096-point analysis results. The2026-10-14 correction above supersedes the HP failure: retained recording-band image harmonics yield0.10408% HP and0.07924% BP, with resolution stability and a failing wrong-cutoff control. Implemented in the opt-in
audition for res words 0FFF and 85 at 44.1 kHz. Resonant/moving BP/HP, other
clocks and HP precision remain open.

**Pitch & interpolation (findings 110–124).** Pitch words: C4=0x4000 (unity),
D4=0x2000 (half speed), 0x1000 (quarter); effective source clock ≈44100.95 Hz
relative to the capture clock. The source-position phase is a **128-step (7-bit
fractional) quantizer** (finding120, matched via HF-sine sidebands). The
interpolation is a measured response implemented as an opt-in audition
(`S760_NATIVE_INTERPOLATION_MONITOR`): a Catmull-Rom-like cubic **B=1.04227,
C=−0.02284** plus 128-step phase. Validated after fixing a SciPy anti-imaging
*measurement* artifact (finding124 — this, not the ASIC, caused the earlier
3–8% fractional errors): 28 pulse rates (quarter→double) 0.70–0.93% held RMS,
4 independent noise cases 0.38–0.54%, over 100 Hz–18 kHz. LIMITS: this is a
measured audition model, not the ASIC's exact coefficient table/precision; the
1% claim is pulse/noise 100 Hz–18 kHz only (NOT 20 kHz sine images); floor-rounding
convention, combined pitch+filter, transitions and other clocks are unresolved.
Reusable reconstruction at `scripts/audio_capture_reference.py`; results in
`condensed/validation/audio-pitch-2026-10-10.json`.

**Loop modes & sample-completion service (findings 102/103/104).** Seven loop
controls traced (mode byte 0–6: Forward End, Forward Release, One Shot, Forward
One Shot, Alternate, Reverse One Shot, Reverse Loop; DSP flag words 0000/2000/
4000/8000/A000). Hardware boundary behaviour (unity pitch, 44.1 kHz): forward
loop **end-exclusive**, alternate turnarounds one sample above the specified
points, reverse loop a **−4-sample register offset**. The completion-service
firmware is decoded (source2 stub 0128→CBCF; reads C002 slot/status, acks via
C016 read; per-channel type at 1ECA: type1 = continuing release, else clear wave
enable). All seven implemented in the opt-in `S760_NATIVE_LOOP_MONITOR`; electrical
timing, ack edge, source priority and fractional-pitch cases remain provisional.

The current supported Python/C++ runtime profiles enable interpolation, which
also enables this loop path. Fresh original-firmware load/playback with the
identified ROBOLOOP disk verifies all seven modes at 44.1 kHz/unity pitch:
forward/reverse/alternate sign sequences, one-shot completion while held, and
note-off silence. BUG-003's assertion that the supported default still drops
all non-forward modes was stale. This is a regression qualification of existing
code, not a new hardware comparison or support claim for other sample clocks,
flags or fractional pitches. Use `verify_native_runtime.py --loop-modes
--sample-disk roms/FDD/ROBOLOOP.IMG --state-dir <fresh-private-dir>`.
See [validation](validation/s2-loops-and-restore-2026-10-11.json).


## Three-stage hardware measurement plan

| Stage | Stimulus / capture | Measurement and isolation |
| --- | --- | --- |
| 1: analog input + ADC | Calibrated sine, chirp, impulse recorded into sampler; Save via Gotek and extract PCM | Input response, THD+N, noise, phase; avoid routing through the output DAC |
| 2: pitch/interpolation | Known sine/saw test disk, open filter and sustained envelope; chromatic RoboSampler capture C0–C8 (MIDI 12–108) | Imaging/foldover spectrum, interpolation behavior; analog output still contributes |
| 3: TVF + DAC/output | Noise cutoff steps; impulse resonance steps; envelope sweep; silence/high resonance | Cutoff/Q mappings, transfer magnitude/phase, saturation, bass loss, oscillation |

Stage 3 source test values: cutoff 16, 32, 48, 64, 80, 96, 112, 127; resonance
0, 16, 32, 48, 64, 80, 96, 112, 127. Capture sample rate, note, velocity,
gain, patch settings, and alignment with each recording. Separate source/interface
coloration from the sampler before attributing errors to a DSP kernel.

The methodology proposes >60 dB null depth and ±0.2 dB response agreement as
targets. Stage-3 LP capture/fit is now partly executed (findings 82–96 above):
static LP response is matched to ~−45/−58 dB residual, but the moving sweep,
BPF/HPF, resonance feedback and full chip law are not yet matched. Do not infer
complete measured parity from the static-LP milestone.

Existing tooling is `scripts/build_calibration_disk.py`,
`scripts/extract_s760_sample.py`, and `scripts/analyze_hardware_parity.py`.
The builder currently makes sine/saw/noise and four named patches; it does not
implement the methodology's full parameter-step/impulse/self-oscillation suite.
The analyzer's stage 1 measures RMS/gain and approximate THD+N; stage 2 lists
length/rate/RMS; stage 3 reports peak/RMS. It does **not** yet implement the
promised FFT waterfalls, transfer-function deconvolution, phase/null matching,
or response-tolerance validation. Use `--stage`, `--source`, `--recorded` as
implemented; extraction uses positional image and `--out`.
Capture organization:
`tests/hardware_recordings/{input_tones,gotek_extracted,robosampler_out}` with
stage-specific recording subfolders. Full detailed procedures remain in
[hardware recording methodology](../hardware/captures/hardware-recording-parity-methodology.md).





RoboSampler hardware capture: see finding81 for the native720KB test disk,22 validated patch selections, exact reference audio and analog recording protocol. Hardware transfer-function measurements remain pending.


Finding82: real analog captures from disk81 confirm opening/closing LPF sweeps and a moving resonance boost at setting64. Three note60/velocity127 recordings have unchanged capture gain and no clipping. They are suitable for analysis; exact envelope timing, DSP topology and coefficient-to-transfer-function mapping remain unestablished. See measurements and limits.

Finding83 compares six magnitude-response candidates against the real sweeps. A discrete two-pole state-variable candidate has the lowest tested spectral error, but sweep-window sensitivity prevents treating fitted damping as an exact hardware constant. Relative trajectories align within a0.2104s file-time shift; absolute note-on timing is unestablished. Static patches15/18 are the next targeted evidence. See fit methodology and limitations.

Finding84 supersedes interpreting finding83's sweep-derived effective Q as stationary damping. Static C64/R00 and C64/R64 captures are compatible with a two-pole response candidate using c=cutoff_word/16384 and damping=resonance_word/4096; later-audio spectral RMS errors are approximately0.60/0.36dB with only a constant gain fitted. This is evidence for a candidate, not verified ASIC topology or bit accuracy. Register-derived sweep paths agree after inferred trimming offsets without time stretching. See static measurements and limitations.

Finding85: offline static waveform validation strongly supports the tested two-state recurrence at cutoff64. The R64 fitted effective cutoff is427.998 versus firmware word430; damping fits85.0029 versus85. Held-out folded-waveform correlation is0.9999993 after diagnostic refinement. Low-two-bit truncation is only one explanation and is not established universally. Unrefined moving R64 spectral error remains4.42dB; no default-emulator integration yet. See waveform method and limitations.

Finding86: the second static cutoff (patch19) fits2731.996 for firmware2733, while damping fits84.9959 for85. Combined with430-to428 in85, this supports candidate c=(word & ~3)/16384 at two operating points; subtract2 and a proportional correction fit worse. This is not universal hardware proof. The moving resonant sweep remains unvalidated. See second-cutoff evidence.

Finding87: applying the supported cutoff truncation and native write timestamps does not solve the resonant moving-waveform mismatch. Held-out R00 correlation is about0.9964; the best tested linear timing variant reaches only0.647 for R64. State-form and smoothing diagnostics are insufficient; state clipping improves but does not validate the model. A byte-audited, native-OS-load-tested18dB-quieter disk is prepared to distinguish amplitude dependence. Static results85–86 do not yet justify default audio integration. See dynamic validation and next capture.

Finding88: the quiet bypass measures18.0655dB below the original, matching division by8. Quiet R64 improves the linear-interpolation candidate to0.982 held-out correlation with gain0.992, versus0.647 and gain0.244 originally. This supports level-dependent behavior but identifies neither a limiter nor its location; coefficient timing and structured residuals remain unresolved. See quiet capture evidence.

Finding89: shared per-sample tanh state-limiting models improve loud/quiet moving fits to approximately0.944/0.971 correlation, but fail independent static patches18/19 (correlations0.72–0.78 versus the linear model above0.99997). These specific fitted models are rejected; level dependence does not establish a generic limiter. Preserve the static response in subsequent dynamic hypotheses. See joint fits and static rejection.

Finding90: hard state limits constrained to preserve both validated static responses still fail the louder moving recording at unity calibrated gain. Alternative coefficient-transition diagnostics give quiet correlations0.979–0.985 without resolving residuals. The existing native trace has constant envelope34=43D6 and36=0000 during the sustained R64 sweep; this is emulator trace evidence, not hardware bus observation. See constraints and control audit.

**Finding91 correction to88–90:** the original sweep fits a linear response with fixed damping590 at0.99868 withheld correlation and unity gain. That ROM coefficient corresponds to resonance32; quiet/static R64 support approximately85. This does not prove the hardware control was32: the user reports keeping the intended patch unchanged, and both disk images encode64. Effective damping differs for an unresolved reason; a specific limiter or operator mistake is not established. See evidence and limits.

Finding92: local fits retain approximately590 damping throughout the original sweep across a15dB output RMS range. Quiet central intervals remain near85; edge residuals limit their interpretation. A targeted original-disk patch04 repeat is requested to test reproducibility. See local analysis and capture request.

**Finding93 resolves the repeat test:** original-level133400 capture fits effective damping87.88, consistent with quiet88.05 and expected register85. Fixed85 correlation is0.97853; fixed590 is0.64343 at unity calibrated gain. The first recording remains an unexplained outlier;88’s limiter inference is unsupported by this repeat. Use repeat/quiet captures for ongoing moving validation, preserving static85–86. See repeat measurements.

Finding94: timing-warp and analog-path-order diagnostics on the accepted quiet/repeat captures do not consistently improve both. Damping85 and unity calibrated gain stay fixed; moving residuals remain approximately14–15dB below signal. No empirical warp or limiter is established. See methods and limitations.

Finding95 revisits87’s state-form test after correcting its capture/damping confound. On accepted quiet/repeat recordings, five stationary-equivalent forms have similar moving fits and reverse ranking between recordings; none identifies silicon topology. Local timing shifts also fail to generalize. Static LP evidence remains strong, moving behavior provisional. See identification limits.

Finding96 adds **opt-in** `S760_NATIVE_LPF_MONITOR` to the native MAME monitor. For44.1kHz LP/unflagged supported words it renders the measured stationary recurrence with stepped writes and stream synchronization. Default output is unchanged; unsupported modes/clocks/commands use the prior audition path. Native static rendering matches an independent filter at0.999990 correlation. This does not settle moving precision or complete IC29 emulation. See implementation, tests and restrictions.

Finding97: the opt-in LP audition clears channel states immediately at wave-enable transitions. A native sweep plus30 retriggers reuses12 channels, all enables start zero, and the final tail is silent. Logged-write numerical replay correlates0.999994; this validates implementation, not physical sweep precision. BP/HP remain bypassed pending targeted hardware captures. See lifecycle test and next evidence.

Finding98: replacement BP and accepted HP hardware sweeps support band/high outputs of the same candidate recurrence at resonance0, with unity calibrated gain and withheld correlations0.996438/0.991801. Earlier BP capture was all-zero and unusable. Free phase cannot distinguish old/new BP state; resonance0 cannot establish resonant BP gain. Offline coefficient interpolation and fitted timing remain diagnostic; native BP/HP audition is still bypassed. See capture evidence and limits.

Finding99 extends the existing opt-in filter monitor to native DSP mode0400 BP and0200 HP at resonance word0FFF only,44.1kHz and the existing unflagged domain. Native replay correlations0.999789/0.999993, unsupported BP R32 raw output identical, boot checks pass and release tail is silent. This is implementation validation; hardware coverage remains finding98's resonance0 captures. See implementation and checks.

Finding100 registers native banked RAM, bank selectors, wave memory and wave registers for snapshots, fixing a reproducible reload CPU fault with both raw and filtered monitors. An active BP sweep restores with57,330 identical PCM samples. This does not establish full-system save support. See save/load evidence. Finding101 audits remaining coverage and prioritizes currently unsupported loop/direction modes.

Finding102 traces sample loop-mode bytes0–6 to distinct native control/parameter flags. Current monitor rejects six of the seven configurations; code and native test reproduce the coverage gap. A native-load-tested single patch maps modes across notes60–66 at constant pitch, ready for hardware capture. Encodings establish controls, not physical sample order or endpoint semantics. See mode table and recording fixture.

Findings103–104 identify and implement the seven-mode unity-pitch loop fixture behind S760_NATIVE_LOOP_MONITOR. Forward/alternate/reverse periods are1023/2046/1024 source samples; one-shots emit2047/2048 samples in native tests. An opt-in source2 completion model lets the original OS retain type1 release looping and stop type3. Exact source ordering, alternate save/load and unchanged disabled output pass; physical interrupt timing/arbitration and fractional-pitch coverage remain provisional. Finding105 requests resonance64 BP/HP captures to resolve output gain before expanding filter support.

Finding106: hardware R64 BP/HP sweeps support unscaled band/high outputs with calibrated gains0.994/1.030. Damping-scaled BP is rejected; moving withheld correlations0.978/0.981 still leave substantial error. Opt-in native BP/HP now also accepts resonance word85, with independent numerical replay above0.99999, silent release tails and unchanged R32 fallback. This is not exact moving-filter hardware parity. See evidence and tests.

Finding108 validates stationary BP/HP at C64/R64 using the new hardware captures. Fixed effective cutoff428/damping85 gives withheld correlations0.999999588/0.999873196 and calibrated gain within0.03% of unity. Folded RMS residuals are0.091% BP and1.59% HP; HP remains sensitive to phase/reconstruction method. No DSP constant or native-code adjustment is warranted. This supports stationary outputs, not exact moving sweeps or whole-chip accuracy. See validation and limits.

Finding110: physical noise captures verify unity, approximately43CE/4000 and half-speed pitch relationships. Interpolation remains unresolved: simple linear/hold/cubic candidates do not explain both half and fractional captures, and spectral results depend on reference reconstruction. No inferred kernel was added to the renderer. See measurements and qualifications; sparse-pulse fixture111 is the next discriminator.

Finding112: pulse-derived effective half-speed response predicts withheld pulses at0.185% RMS error and independent noise at0.481% over100–18000Hz, with phase alignment and fixed gain. New opt-in S760_NATIVE_HALF_INTERPOLATION_MONITOR applies only to the tested44.1kHz, word2000, integer-bound forward-loop domain. Native replay passes, unsupported unity/upward paths and disabled full output remain bit-identical. Effective taps are not a generalized ASIC interpolation law. See physical evidence, implementation and limits.

Finding114: two cascaded copies of112's half-speed response predict withheld physical quarter-speed pulses within0.515% normalized RMS, without new coefficients. The existing opt-in interpolation switch now supports word1000 under the same restricted forward-loop domain. Native pulse/noise replay checks pass. A broader cubic model fits averaged fractional pulses but fails independent upward-noise validation (~8.3% RMS); arbitrary-pitch changes are not justified. See prediction, implementation and rejected extrapolation.

Finding116: fixed quarter-speed response predicts independent physical noise within0.742% normalized RMS over100–18000Hz, strengthening the existing opt-in case. Separating output-clock phase from waveform alignment supersedes114's8.3% fractional mismatch: unchanged pulse-derived cubic coefficients give1.01% down/1.35% up (0.947%/1.320% with separate unity-noise response calibration). This correction does not identify a general ASIC interpolator. Remaining upward error is concentrated above16kHz; phase-quantization and broader-kernel diagnostics do not resolve it. Finding117 requests louder known noise to test amplitude dependence. See measurements and timing correction.

Finding118: eightfold noise PCM amplitude leaves fractional mismatch approximately unchanged. Fixed-pulse predictions give1.06% down/1.38% up RMS; independent same-session unity calibration gives0.906%/1.268%. This argues against a simple additive noise/rounding floor as the main cause. Higher reconstruction precision and flexible kernel diagnostics do not resolve it; no arbitrary-pitch coefficients were implemented. Finding119 supplies a high-frequency sine discriminator. See capture comparison and limits.

Finding120: twelve16kHz-sine sidebands match128-step source-phase predictions within0.019Hz; first-pair levels within0.067dB. This strongly supports effective seven-bit interpolation phase in the tested path, but does not identify rounding convention or the coefficient table. Applying relative clock correction to the complete output avoids artificial phase drift. The fixed cubic plus128-step model gives0.827% withheld upward-sine error; independent upward noise still leaves1.24–1.30%, so general interpolation remains provisional. Finding121 requests an18-note grid spanning six source frequencies at unity/down/up, including20kHz to constrain the stronger image response. See sideband evidence and limits.

## Frequency grid and full-keyboard follow-up (122–123)

The18-note hardware grid spans six source frequencies around1–20kHz at unity/down/up. It confirms increasing interpolation images at high source frequencies, but neither a weighted curve nor a512-parameter phase-table diagnostic establishes the remaining coefficients. The latter still leaves approximately1.225% held-window RMS error on earlier high-level noise; this is not an independent-capture accuracy result.128-phase evidence from120 remains supported. No arbitrary-pitch model is promoted, and measurements above18kHz do not extend the previous noise-validation band.

Finding122 and measured artifacts distinguish measurements from rejected candidate fits. Finding123 provides a native-verified88-key fixture: twelve sine frequencies at five pitch settings and28 dense-pulse rates. All88 routed notes/pitch words/loop lengths and60 sine frequencies pass MAME verification; physical capture is pending. This verifies the fixture, not full-chip fidelity.

## Current pitch result: capture124 and reconstruction correction

The full88-key analog capture completed on2026-10-10. All28 pulse rates pass0.697–0.926% held normalized RMS error in100Hz–18kHz; four independent earlier noise cases pass0.380–0.538%. B=1.042273935870565, C=-0.022841914081554338 and128 fractional phases are unchanged from earlier evidence. Only transport/phase alignment is fitted; gain is fixed. Pulse comparisons use the common44100.952Hz clock inferred from60 sine cases. This relative clock includes recorder error.

The apparent1–3% residual in earlier waveform diagnostics was substantially caused by insufficient anti-imaging in the analysis resampler. A short default polyphase FIR left images that folded into the comparison band on the44.1kHz grid. Raising the upsampling factor did not fix its transition band. A256-input-sample Kaiser reconstruction FIR does; the reusable helper and analytic tests are committed under scripts/audio_capture_reference.py and tests/test_audio_capture_reference.py. Raw captures and original spectra are preserved. Earlier128-phase evidence remains supported; rejected flexible fits must not be treated as ASIC behavior.

S760_NATIVE_INTERPOLATION_MONITOR extends the opt-in native wave path over quarter-to-double speed at44100Hz, control4, unflagged integer-bound forward loops. It retains the measured half/quarter kernels and leaves unity unchanged. General rates use the fixed128-phase cubic followed by a25-tap symmetric inverse of U(w)=1-B/3+B/3*cos(w), yielding a response relative to the existing unity path. All88 native notes agree with an independent frequency-domain reference within1.378 16-bit PCM units. Disabled output is bit-identical to the preceding build. No new persistent filter state is introduced.

This is practical sub1% waveform agreement in the specified pulse/noise domain, not bit-exact full-chip emulation. Absolute phase rounding, other clocks/loop directions, pitch transitions, combined filter/pitch parity and full-band20kHz behavior remain unvalidated. [Committed per-case results and hashes](validation/audio-pitch-2026-10-10.json); local shared finding124 contains the full evidence trail.


## Native sampling postprocessing checkpoint (2026-10-12)

BUG-043 is fixed for the observed OS2.24 synchronous IC4 A7 wave-to-RAM
transfer. Start now exhausts the count and reaches waveform review; the preserved
previous executable fails the same native regression. The inverse BC transfer
validates both full byte ranges and even count, copies, advances addresses and
clears count. Read-only diagnostic taps preserve exact131072-frame native PCM
and both displays; independent load/play/release and307 backend tests pass.
ADC capture remains open: input meter0x10001C and recording-position0x100010/12
return unmapped values. Arming observes slots4/20 with mode8, which is a constraint
rather than a qualified input model. No captured signal, recorded PCM integrity,
physical timing, packaged acceptance or full sampling workflow is claimed.
See [sampling contract](../emulator/guides/native-sampling.md) and
[validation](validation/native-sampling-dma-2026-10-12.json).


## Offline native sampling input

The opt-in44.1kHz stereo PCM16 profile now records known independent channel
patterns through OS2.24 Sampling controls, then Sample Save/export and fresh
Sample Load.56,661 frames/channel match every input value, and239,616 allocation
bytes including padding remain exact across wave RAM, disk and cold reload.
The16,384-frame FIFO rejects unsupported formats/overflow atomically; recording
reported zero underruns. This is native offline workflow evidence, not physical
capture or hardware parity. Default launches keep ADC disabled. Capture-device
selection, analog gain calibration, alternate capture clocks, hardware meter/interrupt
semantics and realtime timing remain open. See
[validation](validation/native-sampling-input-2026-10-12.json) and
[sampling contract](../emulator/guides/native-sampling.md).


Standalone Input Level now controls0–100% linear recording gain separately from
Output Level. Unity/half/mute after cold armed-session restore match every
injected stereo PCM sample and survive Sample Save/cold Load with zero input
underruns. Source/packaged browser acknowledgement, saved-gain recall and
reconnect pass; default-off playback/displays remain bit-identical. This closes
the standalone gain objective for the documented software profile, not analog
pot calibration, physical capture or VST host input routing.
[Evidence](validation/native-input-level-2026-10-12.json).

Physical standalone sampling now passes for the explicit MOTU Windows MME
44.1 kHz stereo PCM16 profile. ASIO fixture outputs 3/4 looped to inputs 1/2
produce unclipped 440/880 Hz signals. Both 65,514-frame firmware recordings
match contiguous captured device PCM exactly at the same source offset;
all 276,480 allocated bytes match native wave RAM, saved floppy and fresh Load.
Native input underruns remain zero. The complete workflow reports 18,432
discarded frames, including outside the recorded interval; physical driver
loss accounting, measured latency, alternate rates and analog calibration
remain open. Default launches have no input device; explicit selection opts
into the native ADC profile. [Evidence](validation/native-physical-sampling-2026-10-12.json).
## Standalone ASIO option

Standalone Configuration now offers ASIO driver, stereo input/output pair and
buffer selection. A native PortAudio ASIO callback copies bounded preallocated
SPSC rings without Python, sockets, UI, disk, allocations or mutexes. MAME owns
sampler execution and PCM; the device owns its callback clock. Normal-speed
44.1 kHz duplex is qualified on MOTU Pro Audio v2 outputs3/4 and inputs1/2 at
128/512/1024-frame buffers. Native ROBOFULL playback/release passes with zero
output underruns/discards/driver flags, including display streaming. ASIO
firmware recording matches64754 captured frames per channel exactly; all276480
allocated bytes survive Sample Save/fresh Load. The full sampling workflow
reports61440 discarded input frames outside the exact recorded interval.

Driver-reported latency at512 frames is12.4ms input /13.6ms output, excluding
transport/rings. This is not measured round-trip latency or indefinite clock
drift/dropout qualification.341 backend/121 React tests, source/package browser
settings and actual WebView boot/close pass. Alternate rates, hotplug, analog
calibration and release redistribution qualification remain separate.
[Evidence](validation/standalone-asio-2026-10-12.json).

## Physical standalone MIDI acceptance

The Windows standalone's micro lite Port 5 input is qualified with its physical
output cabled back to the input. Original-firmware ROBOFULL playback responds to
physical note-on, releases to silence, ignores notes while the input is detached
in software and resumes after reselecting it. A 180-second run contains all 90
native note pulses and finite PCM; MOTU outputs 3/4 looped to inputs 1/2 confirm
physical audio. This is not USB hotplug or every MIDI controller/channel test.
Sustained audio loss counters are evaluated separately from note delivery.

## Standalone device qualification update

Windows output selection now uses stable render endpoint IDs with MAME's required
`o:` node prefix. Native44.1kHz audio reaches Realtek Digital Output's48kHz shared
mix with the expected20004.5Hz fixture peak, finite PCM and silent note-off;
packaged apply/reconnect persists the endpoint. This is digital output conversion
evidence, not analog parity.

ASIO binary PCM ingress preserves newline/NUL/signed samples and atomic overflow
rejection. A full live input queue discards the complete packet while continuing
output delivery and bounded wall-time clock feedback. Native PCM clocks remain
unchanged. An8192-frame output prime and16384-frame target provide scheduling
headroom; the target371.52ms and queued duration are displayed separately from
driver latency. Five minutes/150 physical MIDI notes produce every native pulse
with a silent release and zero output underruns/discards/native drops/driver
flags.2048 input frames are discarded during this playback workload.

Closed-stream failure pauses the same native machine. Reopening the real MOTU
driver re-primes selected input, resumes native time and preserves PID/media.
Physical audio/MIDI unplug tests are removed from Milestone3 by user direction.
Physical bridge write-to-input upper bounds10.45–88.43ms include2048-frame input
completion and worker delivery, excluding MAME/MIDI transport. Firmware sampling
through the revised ASIO path records66245 exact captured frames/channel, with
zero native input underruns and276480 allocated bytes surviving Save/cold Load.
4096 input frames are discarded over the full workflow. Alternate ADC clocks,
unreported physical driver losses and hardware register/meter fidelity remain
open. [Evidence](validation/standalone-audio-devices-2026-10-12.json).


## Native host configured bend and reset qualification (2026-10-13)

SoundCheck1.0.0 Windows x64,44.1kHz/512-frame SDK processing delivers audible
bend after original OS2.24 Patch Control Bend Up/Down are set to12. The ROBOFULL
fixture measures20004Hz at centre,4108Hz at maximum upward bend (folded into the
output band),10002Hz downward and20004Hz after return to centre. Release reaches
zero. The earlier zero-range fixture did not test configured bend. These are
native host effect measurements, not hardware tuning, alias/interpolation or
amplitude parity across the musical range.

A controlled sustain-held trial establishes that CC121 does not release the
note or restore CC7 volume on this fixture. Same-channel CC123 leaves held-pedal
audio sounding; CC64 up releases it. The later supported-message controller qualification below resolves this
Milestone4 gate without claiming rawCC120/121 support. [Contract](../emulator/runtime/native-vst3-midi.md) and
[measured evidence](validation/milestone-4-configured-bend-2026-10-13.json).


Native VST controller qualification now includes the existing stereo coefficient
path in normal C++ native launches (BUG-056). Left/right/centre CC10 routing,
configured CC11 and assigned CC1 TVA gain, RPN bend range/null selection and
explicit supported-message panic/reset macros pass measured native SDK hosting.
Stereo centre gain differs from the previous mono bypass. Three-rate exact
reference PCM and bounded cold state replay pass. These are software integration
results; physical gain/pan law, LFO/filter/tuning and alias fidelity remain separate
Milestone5 domains. [Current evidence](validation/milestone-4-controller-semantics-2026-10-13.json).


## Native VST3 host sampling — 2026-10-13

Milestone 4 host input now passes the Windows SoundCheck 1.0.0 native instrument
profile. Its optional inactive stereo bus accepts float32 at 44.1 kHz. Callback
buffers are copied before output clearing, preserving aliased input/output and
channel silence flags. A bounded worker queue carries PCM alongside MIDI;
worker conversion feeds the existing native ADC peripheral in the same render
transaction, using validated 2,048-frame ingress chunks. Firmware performs the
recording; no guest/sample RAM writes or substitute recorder are used.

Original OS 2.24 records 45,649 exact host frames/channel with varying
64/127/256/511/1024-frame callbacks and shared input/output buffers. Native
recording underruns are zero. All 184,320 allocated sample bytes match recorded
wave RAM, firmware Sample Save/export and fresh native Sample Load. The source
floppy is unchanged. Actual SDK getState captures the machine for diagnostic
wave/FIFO inspection; this is separate from third-party DAW project containers.

A strict 12-second active-input clock produces 529,200 exact output frames with
36.9 µs maximum callback and zero missed deadlines. Output-only 48/96 kHz runs and
240,000-frame cold state also pass.354 backend tests and independent SDK metadata,
input-clock rejection, silence flags and disconnection checks pass. State v3
preserves pending input PCM; older formats remain decodable with zero input.

Live Sampler FX remains unadvertised. Other input clocks, physical ADC fidelity,
other DAWs and release qualification remain open. Actual DAW project portability
is the sole remaining Milestone 4 checkbox. See the
[host sampling contract](../emulator/runtime/native-vst3-sampling.md) and
[exact source/binary validation](validation/milestone-4-host-sampling-2026-10-13.json).


### Static filter timing diagnostic (BUG-005,2026-10-14)

Using the original stationary BP/HP captures and fixed428/85 recurrence, affine phase drift fitted only on1.0..2.4s forecasts the withheld3.0..4.5s interval with0.0789% BP and1.1311% HP normalized RMS error. HP remains above1%, and moving/resonant accuracy remains unresolved. This improves the timing analysis without adjusting native coefficients or fitting held-out data; it does not qualify the filter or justify an emulator change. [Investigation and limits](validation/remaining-bug-investigation-2026-10-14.json).


### Reproduce static capture correction

Run `python scripts/verify_static_filter_captures.py --state-dir <fresh-private-directory>` with numpy/scipy/soundfile and the original fingerprinted local hardware ZIP recordings. The script checks all input identities, reproduces the old folded failure, qualifies8192/16384-point resolution checks and rejects a wrong-cutoff model. It never changes captures or emulator constants. Tests independently verify fractional source delay for image harmonics above the source Nyquist. The original static/moving investigation remains historical; the corrected static result does not qualify moving resonance or arbitrary coefficients/clocks.


### Moving-filter remainder: negative diagnostics (2026-10-14)

The accepted quiet and repeat LP R64 recordings were rechecked with the same85 damping/unity calibrated gain and original inferred coefficient trajectory. Fourier fractional excitation alignment changes evaluation error from17.627% to17.898% (quiet) and18.444% to18.038% (repeat); it is not a consistent correction. Diagnostic stepped writes and32/64/128-sample coefficient cadences are worse. These reused evaluation blocks do not provide fresh independent validation. No native renderer or coefficient change was made, and BUG-005 stays open for moving/sweep response. Static agreement from the corrected recording-band analysis above remains valid. [Commands, candidate parameters, capture identities and next evidence](validation/moving-filter-investigation-2026-10-14.json).


Current-build matched modulation timing localizes all24 delayed timer deliveries in48 measured intervals to theF008 mouse handshake ending004B:5811POPA. Native periods average20.071802/20.068255ms opening/closing, with constant9.125us ISR prologue; observed/unobserved/repeated PCM windows are exact. Original code rearms from service-timeTIMER1+20,000, so delay accumulates. This is not measured hardware cadence and does not explain every direction-dependent analog residual; BUG-005 remainsOPEN and no production timing/filter constants changed. [Exact evidence](validation/filter-scheduler-localization-2026-10-16.json), [decoded path and limits](../firmware/os/modulation-firmware-path.md).


## Verified CPU state-time correction (2026-10-16)

The follow-up found a real emulator defect beyond the original firmware's mouse masking: nativeKB CLRC,SETC,DI,EI,CLRVT,NOP used4states, whereas Intel270651-003 Table3-3B specifies2. The native path now uses2; the legacy path retains4. No CPU clock, OS/ROM, rearm policy, filter equation, cutoff map or hardcoded rate adjustment changed. BUG-091 isFIXED.

An isolated CPU execution fixture cancels identical marker overhead. For each opcode,2048 repetitions measured1024us before and512us after, exactly matching16MHz/two oscillator cycles per state. This proves the changed instruction timing under the model; full CPU bus/IRQ timing remains outside the result.478 full regressions pass, with4 previously documented source-builder expected failures. Native original-firmware boot, mouse input, playback, zero release tail and clean shutdown pass.

Fresh paired observer/baseline/repeat audio windows again match exactly, with no dropped rows. Opening/closing mean control periods are now20.009266/20.009078ms; ISR prologue8.875us versus9.125us before, consistent with itsEI correction. In these particular half-second windows, no delivery ends at the mouse handshake; the few delays above2us occur at00DB:92FA. Before/after runs have different setup/tick phases, so the dramatic mean-delay reduction is descriptive and is not proof that mouse blocking never recurs or that hardware waveform error is fixed.

BUG-005 remainsOPEN. The next acceptance operation is to regenerate the same TVFSTEP/resonant native reference on this new executable and apply the existing frozen ramp/step/static/bypass comparison rules against hardware recordings. Previous native coefficient schedules and checkpoints belong to their recorded build; do not reuse them as if current. The still-uninterpreted101018 control register remains a separate potential transition-law dependency. [Exact code change, Intel source, measured before/after, builds, regression results and limitations](validation/native-kb-state-time-fix-2026-10-16.json), [after-fix matched scheduler rows](validation/filter-scheduler-after-state-time-fix-2026-10-16.json).


## Native short-smoothing trial (2026-10-16)

The workspace emulator now supports `S760_NATIVE_CUTOFF_SHORT_CANDIDATE`: a separate, disabled-by-default diagnostic path using 478 native samples (10.839002ms), nearest to the frozen 10.844412ms offline model. It reuses the existing command 0x001B / LP gate and preserves immediate initialization/fast writes. The existing 20ms candidate stays at 882 samples when used alone; the short flag wins if both flags are supplied. Neither flag changes firmware or CPU scheduling. The normal Python runtime sanitizes these environment flags; this trial explicitly injects the short flag in a private launch harness. Packaged application artifacts are unchanged.

Four original-firmware native takes cover both ramps and both abrupt steps, with deterministic paused setup and pull rendering. With the flag disabled, all 2,998,800 stereo PCM frames match the prior executable exactly. Enabled and disabled guest cutoff trajectories and note times are identical. Both enabled ramp outputs change. Full sample allocation, MIDI delivery, unchanged-media and silent-release checks pass.

Step PCM is not entirely identical because smoothing changes the preceding filter state. In the first 200ms after each jump, peak differences are 0.0000139% and 0.001404% of the corresponding baseline take peak. A separate read-only applied-coefficient trace proves both fast target jumps reach the exact target on the next native audio frame, with no smoothing ramp. The observer preserves 1,499,400 stereo PCM frames exactly and drops no rows.

The driver/executable builds pass, all 488 current regression tests pass, and native boot/input/playback/release/clean-shutdown acceptance passes. This qualifies an opt-in implementation trial, not a new measured hardware improvement or resonant-filter repair. The motivating offline short-smoothing comparison was 6.181% to 5.795% opening and 3.783% to 3.552% closing; those numbers are not native analog acceptance. BUG-005 remains OPEN. Next compare the actual native trial against analog recordings with source/clock/alignment rules frozen, including resonant and static controls before considering any default change.

[Native comparisons, applied rows, build identities, regression and runtime evidence](validation/native-short-cutoff-trial-2026-10-16.json).


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

BUG-005 remains OPEN. These results support retaining the combination as an opt-in trial; actual native analog accuracy, resonant behavior and physical command/rounding semantics still need qualification before changing defaults. [Frozen rows, native comparisons, raw applied step rows, input/build identities and limits](validation/native-short-rounded-cutoff-trial-2026-10-16.json).


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

Other concrete follow-up experiments are fractional-increment error feedback (retain discarded remainder instead of permanent bias), rounding of recursive filter state, and command-dependent transition shape/latching. Each needs stationary and fast-command controls as well as both ramp directions; none is established ASIC behavior. BUG-005 stays OPEN. [Fit parameters, training/evaluation rows, corrected fixed-duration replay, contracts, identities and limitations](validation/filter-third-method-combinations-2026-10-16.json).


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

No native change was made. Implementing a direction-dependent real-time response requires a causal law that handles direction reversals and command/voice changes. Offline scale greater than1 can advance a write relative to the original input stream; its future-target check in retimed coordinates does not prove live-stream causality. It must not be implemented by changing CPU clocks or reading future writes. Treat these fits as a target for a causal coefficient/state model and independent native/hardware testing, rather than calling them a complete hardware fix. BUG-005 stays OPEN. [Search profiles, frozen fit parameters, all rows, contracts, identities and limitations](validation/filter-direction-transfer-2026-10-16.json).


## Below-one-percent acceptance target (2026-10-16)

The user accepts below1% waveform residual in both directions as the practical completion target. Use the established evaluation RMS waveform percentage, and continue reporting repeated-take results; do not substitute correlation or redefine the error. Static and fast-command controls must remain acceptable, with native implementation and independent hardware qualification distinguished from offline fits. The target has not yet been achieved.

Direction-specific endpoint-preserving map curvature was trained only on take2/take3 training blocks with the learned direction scales, slew, floor increments, source clock/phase/gain, damping and recurrence fixed. Opening beta0.00123606798 and closing beta-0.000488061945 give mean evaluation residual2.0139% opening/2.0007% closing, versus2.0430%/2.4914% previously. The midpoint target shifts are+0.67860/-0.26795 cutoff-word units. Parameters transfer frozen to later takes; only constant alignment is fitted on their training blocks. Intermediate stationary cutoff accuracy is still unqualified.

Retesting physical transition duration over2..30ms with coarse search/local refinement selected the existing10.844412ms duration for both directions, adding no improvement. Testing target precision with all other corrections frozen gives:

| Target conversion before smoothing | Opening mean residual | Closing mean residual |
| --- | --- | --- |
| Existing truncate bottom two bits | 2.014% | 2.001% |
| Retain raw target bits | 4.029% | 6.456% |
| Round to nearest multiple of four | 6.572% | 9.564% |

The existing conversion wins first-pair training selection and later evaluation in this fixed combination. This does not rule out every refitted model or prove physical target precision. No native change was made. Further useful work is residual localization against update/latching timing and a causal dynamic coefficient/state response; avoid adding unrestricted waveform correction parameters merely to force a number below1%. BUG-005 remains OPEN. [Acceptance threshold, full curvature/duration/precision rows, frozen fits, identities and limits](validation/filter-sub-one-percent-target-2026-10-16.json).


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

The below1% target remains unmet. Intermediate stationary cutoff measurements are the next useful discriminator: current map corrections preserve only two measured endpoints and cannot independently distinguish cutoff-map error from moving-state behavior. [All dynamic variant/localization/jitter rows](validation/filter-dynamic-residual-tests-2026-10-16.json), [CPU/test repairs, raw before/after, builds,495 regressions, native acceptance and fresh captures](validation/native-kb-control-state-time-fix-2026-10-16.json).


## Prepared hardware midpoint calibration (2026-10-16)

The remaining below1% target needs independent constraints between the two static endpoints. `scripts/build_tvf_midpoint_capture.py --out-dir <fresh-private-folder>` reproduces the private720KB TVFGRID.IMG, TVFGRID_CAPTURE.mid and instructions. The disk extends the unchanged seven TVFSTEP controls with seven stationary holds at envelope levels68,72,76,80,84,88,92; all use LP/resonance64 and the original deterministic noise source. Fourteen performance parts receive on MIDI channels1..14; no program changes are used. The19-take sequence lasts257seconds (4m17s): initial bypass/endpoint/midpoint controls, three opening/closing pairs, two fast steps, final bypass.

Two fresh builds produce byte-identical image, MIDI, PCM source, spec and sequence. Image size737280bytes and performance routing are checked. Normal native protocol validation loads the image through original firmware and plays all14 parts.129024 allocated sample bytes match exactly; MIDI delivery, finite nonclipping audio, static midpoint words, both ramps, both fast jumps,44100-frame silent tails and unchanged exported media pass. The measured midpoint effective words are524,656,828,1040,1312,1648,2076. These are native stimulus checks, not physical cutoff measurements. The initial long run with broad research observers disconnected during the eighth note. BUG-094 is repaired for the maintained diagnostic path (2026-10-17): removed native taps no longer retain their own Lua trace tables; the optional probes cache a live PC state handle and filter unrelated writes before exporting state. `scripts/verify_tvf_midpoint_capture.py --pack <pack> --state-dir <fresh-state> --research-observers` retains all original observer fields and all14 acceptance cases. Under a controlled2GiB process-memory budget, original probes reproduce a socket reset with a native Lua out-of-memory panic after11 completed takes; repaired probes complete14 at about1727MiB and exit normally. The historical unconstrained eighth-take failure's resource conditions remain unknown. [Controlled failure, repair, matching data and limits](validation/bug094-observer-capture-2026-10-17.json).

For physical capture, load the TVF GRID performance, retain all14 original MIDI channels, and record the whole257second sequence as one mono48kHz/24bit WAV with the previous input gain and no normalization/dynamics/effects/sample-rate conversion. Preserve the starting/ending bypass and release gaps. This recording can independently test whether the fitted cutoff curve is a stationary transfer correction or compensation for moving behavior. Do not apply the system-disk repacker to this720KB sample disk. Generated template-derived media remains private. [Reproduction hashes, full stimulus/spec/sequence, exact native checks and limits](validation/filter-midpoint-capture-2026-10-16.json).

A prior native short-smoothing validation limit mislabeled TVFSTEP as R0. Its spec actually uses resonance64/damping85; that limit is corrected, with source hashes/results unchanged. The distinct earlier software-counted R0 experiments remain separate.

## Observed native PCM origin (2026-10-17)

BUG-076 is repaired: speaker-hook metadata supplies the absolute frame index of
returned PCM rather than inferring WAV frame zero from machine status. The
modulation verifier records contiguous block mappings and rejects unqualified
origins. A fresh five-case capture reproduces an881-frame first-case origin error
and146-frame later offsets; all four filtered source-trace starts map to WAV
exactly with the expected one-frame LP startup and no fitted shift. Varied pulls,
capture reset and buffered checkpoint recall pass. This changes diagnostic
indexing, not renderer behavior or physical latency claims. Historical captures
without metadata still need independent alignment. See the
[transport contract](../emulator/runtime/native-runtime-protocol.md) and
[raw rows, origins and identities](validation/bug076-pcm-origin-2026-10-17.json).
