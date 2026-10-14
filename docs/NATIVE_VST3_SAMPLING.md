# Native VST3 sampling input

The native instrument has one optional stereo float32 input bus, inactive by
default. Activate it while processing is stopped, at 44,100 Hz. Hosts may omit
the inactive bus; an active bus requires two channels in each process call.
The factory still advertises only `Instrument|Sampler`. The Live Sampler FX
class remains unavailable. VST2 and CLAP are outside this qualification.

## Clock and ownership

Host callbacks own elapsed sample time. Incoming L/R buffers are copied into
preallocated storage before output is cleared, including when a host aliases
input and output. Channel silence flags supply zeros without requiring a source
pointer. NaN/Inf, missing active channels, oversized blocks and invalid event
offsets reject and latch a stream fault. Inactive input supplies zeros.

The existing bounded single-producer queue carries input with the block's MIDI
offsets. No allocation, socket, disk or UI work occurs in the realtime callback.
The worker clamps finite PCM to [-1,1], rounds to signed PCM16 and feeds the
existing Milestone 3 native ADC peripheral. Firmware performs recording and
sample creation; the host never writes sample RAM or substitutes a recorder.

Input is delayed by 4,096 native frames, sharing the MIDI scheduling lead.
That initial zero padding is inserted once when the stream starts. Rendering
retains native video-frame surplus. Input and rendering use one control request;
each peripheral ingress chunk contains at most 2,048 frames. A render transaction
can enqueue several contiguous chunks after validating the entire batch. The
C++ JSON transport splits requests above 4,096 frames to stay within its framing
limit. FIFO overflow rejects before insertion.
Starvation supplies zeros and increments the native recording-underrun counter.
The existing reported output latency is unchanged: 12,288 samples at 44.1 kHz.
This is software scheduling latency, not measured round-trip device latency.

Output-only processing remains supported at 44.1/48/96 kHz. Activating input at
48/96 kHz, or negotiating either rate while input is active, rejects explicitly.
Input resampling and physical ADC clock/gain fidelity remain Milestone 5 work.

## Suspension and state

Suspension retains queued input and the native FIFO. State version 3 includes
pending host input PCM as well as native machine/FIFO state, unread output,
MIDI offsets and converter history. The native ADC profile is pinned in state
identity. Versions 1/2 remain decodable with zero pending input; encoding nonzero
input into an older format rejects. Cross-build migration is not supported.
Bus activation belongs to the host and is not serialized in component state.

## Native host acceptance

The verifier uses the independent Steinberg SDK interfaces in the private
SoundCheck 1.0.0 Windows x64 host. It activates the real input bus and supplies
distinct deterministic L/R PCM through actual process buffers. Original OS 2.24
Sampling, Ready, Start, Stop and Sample Save controls perform the recording.
The source formatted floppy remains unchanged.

The host's real `getState` archive captures the recorded machine. A diagnostic
native child reads that machine checkpoint to inspect wave RAM, ADC loss counters
and saved controller media. A separate fresh native boot performs Sample Load
from the exported floppy. Every recorded word must match a contiguous interval
of its own host channel; all allocated sample bytes must agree between recorded
wave RAM, saved disk and cold-loaded wave RAM. Diagnostic checkpoint inspection
does not establish a third-party DAW project-container contract.

Run with a fresh private evidence directory and free loopback ports:

```powershell
python scripts/verify_vst3_sampling_input.py --host <private-SoundCheck.exe> --module <WebView-Roland_S760.vst3> --blank-disk <formatted-empty.img> --state-dir <new-private-directory>
```

The private host patch and exact result identities are retained with the
[acceptance evidence](condensed/validation/milestone-4-host-sampling-2026-10-13.json).
Physical input devices, analog parity, other recording clocks, third-party DAWs
and the separate FX class are not inferred from this host qualification.
