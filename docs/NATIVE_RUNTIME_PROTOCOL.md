# Native runtime boundary

Development protocol1, extended 2026-10-11. `scripts/s760_runtime.py` owns one MAME process;
`scripts/s760_runtime.lua` exposes its frames and physical controls. React and
WebView are consumers, not engine dependencies. An explicit C++ VST3 development adapter now uses
this transport through a preallocated callback/worker boundary; production
selection, state/input and actual DAW acceptance remain open. Never perform these blocking requests on a realtime thread.

## Lifecycle and isolation

Each process gets separate state, NVRAM, config, logs and a staged copy of the
selected system image under MAME's required ROM-set filename. An OS file lock
prevents simultaneous use of the same state directory. Two different directories
can run independently. The launcher validates inputs and reports missing files,
early process exits, connection failure and handshake timeout. Closing it requests
normal MAME exit, waits, then terminates a nonresponsive child if necessary.

Inherited `S760_*` environment switches are cleared before the explicit native
configuration is applied. The selected boot ROM and disk are used unchanged;
there are no runtime RAM/PC overrides or forced firmware completion flags.

## Control channel

Parent listens on an ephemeral127.0.0.1 TCP port. Lua connects using
`S760_RUNTIME_PORT` and sends a little-endian u32 JSON length followed by UTF-8
`{"protocol":1,"token":"..."}`. The token is unique to the launch.

Requests are newline-terminated JSON with an `op` field. Responses use the same
length-prefixed JSON framing as the handshake and contain `ok` or an error.
The parent serializes requests; there are no concurrent outstanding commands.

| Operation | Payload and behavior |
| --- | --- |
| `frames` | Metadata includes `surfaces`, emulated `seconds` and diagnostic guest cursor coordinates. Each surface is followed by exactly width×height×4 native little-endian ARGB bytes. CRT640×240; LCD160×64. |
| `button` | `port`, `name`, boolean `down`; invokes MAME input fields. The public standalone server permits only the known panel/mouse controls. |
| `dial` | `id` ALPHA or VOLUME, integer `delta` -32..32; relative Value input or clamped 0–100% output level. Direct and worker display responses include `output_level`. See [rack control contract](NATIVE_RACK_CONTROLS.md). |
| `pointer` | Absolute target in the legacy half-resolution coordinate space (`x` 0..320, `y` 0..120). The OS 2.24 adapter reads cursor position, bounds and sensitivity, then sends bounded ordinary MU-1 deltas. No guest state is written. |
| `midi_device` | A device `name` opens MAME's existing MIDI input image/backend; an empty name disconnects physical input. The public server restricts names to MAME's enumerated input list. |
| `quit` | Acknowledge then request normal machine exit. |
| `status` | Returns running/paused, emulated seconds, capture enabled and dropped-frame count. `firmware_ready` is explicitly `unknown`; this is not a boot-complete signal. |
| `pause` / `resume` | Stop/resume emulated time. The control channel remains responsive while paused. |
| `step` | Requires paused state. Advances one video frame using MAME single-step and replies once paused again. Not sample-count stepping. |
| `audio_capture` | Boolean `enabled` toggles native speaker hooks and resets the capture queue/counters. Disabled by default. |
| `audio` | Drain capture: JSON `audio` descriptor then frames×8 bytes interleaved left/right float32 little-endian PCM.44100Hz,2 channels, at most44100 frames. Includes `first_sample` and cumulative `dropped_frames`. |
| `render` | Integer `frames` from1 to8192. Requires paused machine, capture enabled and no prior overflow. Advances video frames until enough PCM exists, returns exactly the requested count and retains excess. Returns paused, or an error after60 unsuccessful steps. |
| `schedule_midi` | While paused:1–256 ordered events; `append:true` can extend the pending tail, with at most256 pending events total. Without append, no earlier batch may be pending. Events with absolute44100Hz `sample` timestamps within30 seconds and1–3 `bytes`. Rejects late/invalid batches before queueing. Status includes pending count, delivered timestamps and errors. |

The bridge converts CRT to wire RGBA and doubles rows to640×480. It packs actual
LCD pixels into160×64 MONO1. This conversion is tested independently of MAME.
Display delivery runs at up to15Hz; slow clients have a one-update queue and old
display frames are replaced. Device emulation continues at the native rate.

## Live PCM and clock ownership

MAME owns emulated time. PCM comes from its actual left/right speaker sound hooks,
not a parallel synthesizer or a reread of WAV files. Capture is optional and
keeps at most one second; overflow drops oldest whole blocks and reports every
lost frame. Counters restart at capture subscription, not at machine boot.
The Lua producer never waits for an audio consumer, though servicing a socket
response can block the machine. Python `read_audio()` drains the stream on a
worker. An empty read means no queued samples; no silence is manufactured.

For demand-driven/offline work, pause, enable capture, then call
`render_audio(frames)`. The host determines how many output samples to consume;
MAME advances in video-frame quanta and retains the extra samples for subsequent
requests. Status/display reads while paused do not advance time. Do not mix free
running and demand-driven operation without accounting for queued samples.
Rendering after overflow is rejected until capture is restarted. A rejected
request does not imply a successful block or synthesize replacement audio.

This is exact output-block sizing, not sample-exact guest scheduling: the guest
can be ahead of delivered audio by a video/sound quantum. MIDI still arrives
through the existing serial channel. Absolute emulated-time MIDI batches and
bounded C++ worker prefetch now exist. Host callback event mapping, latency
qualification and sample-rate negotiation remain open.

Native regression verifies pause, one1/60-second step, contiguous PCM with zero
loss during draining, reported overflow, MIDI note-off and both channels against
MAME's WAV within one PCM16 count. It repeats shutdown/restart in the same state
directory. This is an accelerated transport test, not latency qualification.

The allocating Lua capture and blocking socket transport are not a DAW audio
callback. The [C++ native client and worker](NATIVE_CPP_RUNTIME.md) supply a
preallocated callback queue and underrun reporting. Their host integration and
realtime deadline qualification remain necessary for VST3.

## MIDI channel

The driver connects to a second private loopback port, authenticating with the
launch token. Raw MIDI bytes enter the existing `midiin_device` transmit queue
and its31250-baud serial output. The driver's existing IC4 receiver and firmware
handle the resulting data; the host never sets guest MIDI-pending flags.
The port is polled at1500Hz with a bounded256-byte read. This is live host input,
not sample-offset-accurate DAW scheduling or proof of exact IC4 arbitration.

## Desktop and media

The desktop serves built React assets on a private HTTP port and frames/controls
on a WebSocket port. WebSocket upgrades require the exact local origin and a
per-launch token. No service binds to public interfaces. WebView2 is supplied
through pywebview; the C++ plugin WebView scaffold is still separate work.

Media selection is limited to enumerated raw floppy images. Insertion copies
the selected image into the instance's working slot and uses the existing native
media-change input. The native controller rechecks busy/dirty state and writes
acknowledged status to the private S760_MEDIA_STATUS path. Insertion success is
reported only after that acknowledgement. The guest OS then performs its own Disk/Load workflow.
`NativeRuntime.export_media(destination)` pulses a host export input and reads
an acknowledged snapshot of actual controller media through private instance
files. The driver rejects a busy controller. The parent validates image size,
flushes a temporary destination file and publishes it using a no-clobber hard
link; unsupported filesystems fail without replacing an existing file. The
standalone `EXPORT_DISK` message accepts no client-supplied path and returns
`MEDIA_EXPORTED` only after publication to the instance's exports directory.
Publication is followed by an acknowledgement of the snapshot generation and
revision; failure before publication never clears dirty state. Newer writes
remain dirty. Internal ejection has the same busy/dirty checks; UI ejection is
deferred until firmware empty-drive behavior is qualified. The standalone can explicitly recover the last saved checkpoint after a native
crash; unsaved changes after it and automatic recovery remain unsupported.
Wait for firmware Save to finish before exporting: controller idleness alone
does not prove a whole multi-command firmware operation has completed.

The native driver now handles observed FA RAM-to-floppy and E2 wave-to-floppy
DMA writes. Their bounded synchronous implementation does not establish exact
bus timing or full FDC error/format semantics. Automatic library writeback,
snapshot/session recall, audio input and SCSI media operations remain open.
The standalone layer now publishes conservative firmware screen observations
separately from the transport status. It recognizes OS 2.24 Perform Play and
Disk Load/activity labels; unknown screens remain explicit. See
[firmware readiness and recovery](NATIVE_FIRMWARE_STATUS.md). Disk idle is not
a claim that every requested sample loaded successfully.

## Remaining VST3 boundary work

The C++ native client, scheduled MIDI, bounded PCM, sample-clock advancement,
latency/fault reporting and bounded same-build state are implemented. Actual
SDK/DAW acceptance, portable project state, graphical plugin configuration and
native sampling input remain open. See [completion gates](COMPLETION_ROADMAP.md).

## Native checkpoints

`checkpoint_save` and `checkpoint_load` operate on the instance-private
`runtime-checkpoint.bin` slot. Both require paused execution and disconnected
external MIDI. Version2 preserves pending scheduled MIDI and cancels the previous
timeline before rearming restored events. The Python client wraps the slot in an
atomic, versioned, identity/hash-checked archive. See [checkpoint contract](NATIVE_CHECKPOINTS.md)
for state coverage, cold-restart evidence and remaining host/plugin/SCSI limits.
These blocking controls do not belong on an audio callback.

## Standalone session controls

`SAVE_SESSION` accepts an empty payload and reports `SESSION_SAVED` only after
atomic publication of the service-owned session slot. `RESTORE_SESSION` requires
exactly `{discard:true}`, validates before touching live state, protects busy or
dirty live media, and reports `SESSION_RESTORED` only after native load. A failed
child is replaced before loading. `SESSION.savedSession` reports slot presence;
it does not bypass restore-time validation. Clients cannot supply archive paths.
See [standalone session recovery](NATIVE_SESSIONS.md).


## Standalone graphical configuration messages

The authenticated standalone WebSocket accepts `CONFIGURE_RUNTIME` with exactly
`bootRom`, `systemDisk`, `mediaDirectory` (path strings), `sound` (boolean), and
`discard:true`. These are host settings, not native Lua opcodes. Paths and image
sizes are checked before stopping the existing machine; dirty/busy media rejects
the request. Startup failures return `ERROR` and keep configuration available.
Successful startup returns `CONFIGURATION_APPLIED` with configuration/media and
publishes version-1 settings in the state profile. `SESSION` supplies current
configuration plus `needsConfiguration`. A configured transport is not proof that
the firmware booted; readiness remains independently observed.


## Render display snapshots

`render` accepts an optional boolean `display` (default false). When true, its
reply advertises CRT/LCD surface sizes and sends the existing stereo float PCM
first, followed by CRT then LCD pixel bytes. Non-display clients retain the
existing payload. The C++ audio worker consumes a coalesced display request and
caches the returned surfaces separately from PCM. During processing, editor
frame reads return that cache and request a future update, without a competing
control request. Outside processing, normal synchronous `frames` reads remain.
This changes the runtime source identity used by same-build snapshots. See
[native editor qualification](MILESTONE_2_PROGRESS.md).


Menu push is `BUTTON_PRESS/RELEASE` with id `MENU`, mapped to `:PANEL0`,
field `Value Menu` (active-low SP4 on SC0, Service Notes p18). The raw runtime
button operation accepts that same field. BUG-030 is corrected: firmware can
relocate the cursor and select 1x/2x sensitivity, so accumulated host counters
cannot represent its absolute position. Read-only OS 2.24 registers D0/D2 and
program memory 2138..213F,2140,272E guide bounded relative input. At most16
corrections are attempted; each packet is limited to63 counts with two settling
frames. At 2x sensitivity the nearest reachable pixel may differ by one pixel.
The adapter stops after convergence and does not fight later firmware cursor
relocation. Paused renders service movement as emulated frames advance;
checkpoint metadata retains pending work. `verify_native_runtime.py --panel-menu
--pull-render --scheduled-midi` covers both scheduling modes. Other OS versions
need independent mapping qualification.

C++ embedded telemetry carries `mediaPaths` (up to1024), `mediaFolder`,
`selectedMediaPath`, `lastInsertedPath` and `libraryError`. These are host-owned
browser metadata; insertion and selection are independent. `CONFIGURE_MEDIA_LIBRARY`
uses `{diskPath: folder}` for an explicit recursive scan; `SELECT_MEDIA` uses
`{diskPath: image}` to select an existing inventory item without inserting it.
Unsupported backends reject these operations. Scans are bounded and transactional;
see [limits and state semantics](NATIVE_MEDIA_LIBRARY.md). Native VST state v2
captures this metadata alongside the actual mounted checkpoint bytes.
