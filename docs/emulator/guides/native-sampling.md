# Native sampling implementation status

Physical capture-device selection is delivered for Windows MME and ASIO at
44.1 kHz stereo. Standalone Input Level passes recording-gain and cold
session-recall acceptance. An
opt-in offline ADC profile now accepts bounded 44.1 kHz stereo PCM16, records
through the original firmware controls, and preserves both samples through
firmware Sample Save and a fresh machine's Sample Load. Normal launches keep
this experimental profile disabled; their input register reads remain unmapped.

## Completed offline input profile

`RuntimeConfig.experimental_adc=True` explicitly enables `S760_NATIVE_ADC`.
`NativeRuntime.queue_input_pcm(bytes)` accepts 1–2048 interleaved little-endian
stereo PCM16 frames per paused worker request. A preallocated 16,384-frame FIFO
feeds the existing machine's native sound clock. Submission validates every
sample before publishing; malformed formats and overflow reject atomically.
The callback performs no allocation, socket I/O, disk I/O or locking. Queue
starvation supplies zeros and counts missing frames while recording. Reset
clears the queue/counters; checkpoint identity distinguishes the experimental
profile, and queued samples/counters are included in native state. Cold replay
of a partially queued recording is not yet qualified.

For this experimental 44.1 kHz profile, firmware-selected recording slots4/20
in mode8 receive left/right PCM into their programmed wave addresses. Position
reads at0x100010–13 advance with recording;0x100200–3FF selects the control slot.
The0x10001C/D meter reads expose alternating channel samples. This is a narrow
implementation that executes the observed OS2.24 workflow, not a claim of
complete hardware register, meter, end interrupt or alternate-rate semantics.

The repeatable verifier uses ordinary mouse controls: Sample/Sampling, Ready,
name confirmation, Start, right-button Stop, waveform End, Disk/Save target
Sample with both records marked, export, then cold Disk/Load target Sample.
It never writes guest CPU RAM or forces firmware events. Independent periodic
left/right input patterns are checked at every recorded sample. The final run
recorded56,661 frames per channel with zero underruns; all239,616 allocation
bytes, including zero padding, agree between wave RAM, exported disk and cold
reload. Firmware L/R names and fractional address fields are checked separately.

```powershell
python scripts/verify_native_sampling_input.py --blank-disk <firmware-formatted-720KB.img> --state-dir <new-private-evidence-directory>
```

The input disk must be an existing empty firmware-formatted720KB image; the
verifier checks its fill and preserves its hash. `verify_native_media.py --format`
can produce this prerequisite. Evidence includes ROM/OS/source/binary hashes,
queue rejection results, sample metadata and exact PCM comparisons in
[offline input validation](../../condensed/validation/native-sampling-input-2026-10-12.json).
Default-off deterministic replay also matches the preserved previous binary
bit for bit for132,300 stereo frames and both displays.
This offline result alone does not qualify physical capture, calibrated analog
gain, realtime latency, dropout duration or hardware parity. The standalone
Configuration screen now exposes explicit MME and ASIO input selection; their
separate physical qualification is documented below.

## Completed postprocessing transfer

OS 2.24 Start uses IC4 control A7 to copy wave RAM into CPU RAM. The observed
initial transfer selects wave word8, CPU destination0x0ED712 and byte count0x2400.
CPU routine73B1–7410 programs the transfer and polls the count. The missing
implementation previously left Now Working on screen indefinitely (BUG-043).

The native driver now implements this inverse of the existing BC RAM-to-wave
transfer: validate an even nonzero count and both complete memory ranges, copy
bytes, advance the CPU byte pointer and wave word pointer, then exhaust count.
Unsupported/invalid transfers do not acknowledge completion or partially copy.
Execution is synchronous; hardware DMA timing and arbitration are unqualified.
No guest RAM/PC override or forced firmware event is used to obtain acceptance.

The same firmware controls now reach waveform review and End returns to Sampling.
The preserved pre-fix executable fails the count-exhaustion regression. This
qualifies the observed transfer workflow, not ADC capture, recorded PCM integrity,
normalization accuracy or physical hardware equivalence.

```powershell
python scripts/verify_native_sampling_dma.py --state-dir docs/ic20-hle-findings/chatGPT-work/sampling-dma-check
python scripts/verify_native_runtime.py --bus-trace --state-dir docs/ic20-hle-findings/chatGPT-work/sampling-observer-check
```

Prerequisites: local IC15 v1.11, OS2.24 and built native MAME; observer playback
also requires ROBOFULL. Inputs are unchanged. The sampling verifier accepts
`--executable` for comparison with a preserved binary.

## Read-only diagnostics and next implementation

The authenticated native `bus_trace` operation observes the banked CPU bus;
callbacks return nil, preserving accesses. It is disabled by default, bounded
to256 rows and explicitly counts drops. Read polls retain first/last timestamps
and counts by address/value/PC/mask; those aggregated rows are not an ordered
full instruction trace. Writes retain order until the bound. IC4 bank tracking
handles byte and word stores. Tracing must stop before checkpointing and is not
persisted in a session. It adds diagnostic overhead; it cannot qualify latency.

Traced versus untraced cold replay preserves all131072 stereo frames, both
displays and silent note-off. Normal independent load/play/release also passes.
Keep rewind comparisons separate from monotonic WAV-offset acceptance.

Arming writes control mode8 for slots4 and20 and Start enables bits4/20. The
experimental profile above now exercises these transactions. Alternate-rate
capture clocks, physical input routing, calibrated analog gain, end interrupts and
hardware meter behavior remain open before production input is enabled.

Source/binary identities, regression commands and limitations are in the
[validation record](../../condensed/validation/native-sampling-dma-2026-10-12.json).


Standalone Input Level now implements independent recording gain and acknowledged
readback. Unity/half/mute recording after cold recall, with muted Output Level,
and Sample Save/fresh Load pass. See the [rack control contract](native-rack-controls.md)
and [input gain evidence](../../condensed/validation/native-input-level-2026-10-12.json).
Physical input routing and analog calibration remain separate.

## Physical standalone input profile

The standalone now enumerates and opens an explicitly selected Windows MME
capture endpoint at 44100 Hz stereo PCM16; no input device is selected by
default. The worker polls eight fixed 2048-frame OS buffers, primes8192 frames,
and submits bounded PCM blocks to the native16384-frame FIFO. One bounded
64KB control read and at most one command execute per video frame; live PCM
delivery continues during mouse settling. Unsupported formats, missing devices,
two-second capture stalls, overflow/discard counts and checkpoint discontinuities
are exposed. Windows may convert the physical device format.

MOTU ASIO fixture outputs3/4 physically looped to MME inputs1/2 pass original
firmware Sampling, right-click Stop, End, Sample Save/export and fresh Load.
Each recorded65514-frame channel matches captured device PCM exactly, and
all276480 allocated sample bytes remain identical after disk Save/cold Load.
Native underruns are zero;18432 discarded frames over the complete workflow
remain explicitly reported. This closes external sampling for this supported
profile, while production register semantics, alternate clocks, measured physical
latency and driver-level losses remain open. [Evidence](../../condensed/validation/native-physical-sampling-2026-10-12.json).
