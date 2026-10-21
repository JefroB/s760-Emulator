# Native standalone player

Historical paths into the former findings tree below identify past runs; that scratch tree was removed on 2026-10-21. Generate new run output under `temp/work/`. See [hardware evidence policy](../../hardware/evidence-and-open-questions.md).

Development implementation, 2026-10-10. The player runs one native MAME machine
and displays its actual CRT/LCD surfaces in React, hosted in a Windows WebView2
window. The original OS handles mouse/panel controls, disk loading and MIDI.
Audio comes from the native MAME machine. The standalone routes it through
MAME's Windows output or the native ASIO bridge.

## Wave memory — 2026-10-14

Standalone and VST3 support **8, 16 or 32 MB**, defaulting to **32 MB**.
Select Wave memory in runtime/plugin settings; standalone applies by restarting,
and VST3 applies after reloading the plugin. Both command-line setup tools accept
`--wave-memory-mb 8|16|32`. Existing settings without this field use32 MB.
The native driver also accepts `S760_WAVE_MEMORY_MB=8|16|32` for direct launches;
managed launchers always supply their configured value.

Original OS2.24 reports8/16/32 Mbyte and90.8/181.8/363.8 seconds respectively.
Memory size is included in checkpoint identity: restore requires the same size.
Older2 MB checkpoints need the matching older application; there is no automatic
migration. [Native validation](../../condensed/validation/milestone-5-wave-memory-2026-10-14.json).

## Supported audio defaults — 2026-10-14

Normal standalone output enables firmware stereo pan alongside the existing
interpolation, envelopes, loops and the native filter renderer. Firmware TVF
controls affect normal output within the documented LP/BP/HP word profiles;
unsupported commands/modes retain the raw path. Functional acceptance does not
establish hardware-exact DSP.
Recording remains off until explicitly selected within the supported44.1kHz
stereo profiles. Diagnostic flags inherited from the shell do not enable it.

The stereo correction changes audible center levels from the earlier duplicated
mono path. Native checkpoint identity now includes the stereo audio profile;
earlier mono-path saves require the matching earlier application, and reject
explicitly here before replacing current memory. Automatic migration is unsupported.
[Native acceptance and limits](../../condensed/validation/milestone-5-normal-stereo-2026-10-14.json).

## Native Roland CD development profile — 2026-10-14

The full JMD S760 Freeware CD is qualified for normal firmware Disk/Load: CD1,
2048-byte sectors,32 MB wave RAM, first K4 :KAWAI K4 performance. Stage a private
copy of the original image at `STATE_DIR/roms/SCSI/CD10_2048.iso` before launch.
Open firmware Disk/Load drive selection, use F3 Scan, select CD1 (Formatted),
select the first volume and execute Load. Wait for Now Working to clear, then
return to Perform Play. Its native patches are already assigned to parts;
channel1 notes36/38/42 audition drums, and channel2 note60 auditions the brass.

All79 sample allocations match source exactly; playback/release and cold recall
pass. The complete606.7 MB CD remains external to saved sessions and must be
present with matching name/content on restore. Recognized read-only CDs have
an aggregate1 GiB budget; writable SCSI images remain limited to64 MiB.
This qualifies a native development workflow; final packaged media selection,
other volumes/libraries, SCSI Save and hot-plug remain unqualified.
[Full-CD results and reproducer](../../condensed/validation/milestone-5-roland-scsi-load-2026-10-14.json).

## Native Akai CD development profile — 2026-10-14

Native firmware Convert Load is qualified for the first volume/program of the
user-supplied String.Ensembles Akai S1000 CD (28,180,480 bytes), with32 MB RAM.
Stage a private copy as `STATE_DIR/roms/SCSI/CD10_2048.iso` before launching.
In firmware Disk/Load, open drive selection, use F3 Scan and select CD1. Normal
Roland Load can label an Akai CD Unformatted; use **Disk → Convert Load** to
browse its Akai volumes. Select the first volume and execute ConvLD. Wait until
Now Working clears, then return to Perform Play and assign the first imported
patch to part1 before auditioning.

Thirty imported samples, source data plus observed firmware loop-tail adjustments,
three-key playback/release, unchanged CD contents and cold session recall pass.
This is a native development workflow; mounting CDs through the final shipped
interface, larger/other Akai CDs and SCSI Save remain unqualified. Native Roland performance
Load has its own qualified profile above. Floppy Export disk does not export a SCSI CD.
[Fixture and reproducible verifier](../../condensed/validation/milestone-5-akai-scsi-load-2026-10-14.json).

## Disk/Load playback restriction

In the qualified OS2.24 Disk/Load directory workflow, firmware clears playable
voices before its disk reads and suppresses new note allocations. MIDI serial
transport can continue, but notes are not promised to play or be preserved.
Return to Perform Play before auditioning. Three native trials verify responsive
navigation, clean post-mode playback/release and unchanged disk bytes; they do
not establish simultaneous FDC/MIDI/voice interrupt priority.
[Control traces and limits](../../condensed/validation/milestone-5-disk-voice-restriction-2026-10-14.json).

## Standalone configuration and on-screen keyboard

Use the gear button to open **Configuration** to select MIDI input, enable audio output, choose the
audio backend/buffer target, and set firmware/media paths. MIDI selection applies
immediately after native acknowledgement. Audio/firmware edits require the
explicit restart confirmation and preserve existing dirty-media protection.
Automatic and WASAPI offer **Windows output device** selection and a refresh
button; leaving it empty uses the Windows default. XAudio2 uses the default.
ASIO offers explicit driver and stereo channel selection for playback and recording.

**Show on-screen keyboard** is off by default. It applies immediately and is
saved in the instance's `standalone-ui.json`, independently of firmware restart
settings. The keyboard offers 61 keys (C2–C7), MIDI channel1, velocity100 and chords.
Hold keys with a pointer or focus a key and hold Space/Enter. Release, cancellation,
lost capture, blur, disconnect and hiding/unmounting release held notes. Opening
Configuration hides the keyboard and releases its notes. Invalid preference
files fall back to hidden with a visible warning; failed writes do not acknowledge
the change. MIDI selection currently belongs to the running native instance and
must be reselected after a sampler restart.

This configuration and keyboard belong to the standalone native entry point.
The VST editor does not expose them; the host supplies MIDI and audio routing.
Packaged browser configuration/persistence/audio-restart and actual WebView boot
checks pass, alongside312 backend tests and the original117 React tests. These are development
acceptance checks, not physical MIDI/capture, latency or clean-machine release
qualification. See [validation](../../condensed/validation/standalone-configuration-2026-10-12.json).

## Run from source

First supply the files listed in [firmware setup](firmware-setup.md). The project
does not bundle or automatically download Roland firmware or sample libraries.

Use the current MAME build (including the runtime MIDI socket support):

```powershell
python -m pip install -r scripts/requirements-standalone.txt
cd google-ui
npm run build
cd ..
python scripts/s760_standalone.py
```

The default firmware paths are `roms/BOOT/Roland_S-760_v1.11.BIN` and
`roms/System/S760224.IMG`. Supply your own firmware. Override paths with
`--boot-rom`, `--system-disk` and `--media-dir`. Windows WebView2 Runtime is
required for the desktop window. `--browser` uses an external browser instead;
`--no-browser` starts only the local service for automated tests.

## Runtime settings and startup recovery

Configuration opens above the sampler in a viewport-bound window. Choose
**Session & disks**, **MIDI & display**, **Firmware & media** or **Audio** from
its category navigation. Apply and Cancel stay at the bottom of the window;
small displays scroll only the active panel. Restart, restore and recovery
confirmations open in a higher layer. Escape closes the top layer and returns
focus to the control that opened it. Switching categories preserves unapplied
settings. First-run firmware repair opens **Firmware & media** directly.

**Runtime settings** in React accepts the boot ROM (32KB), system disk (1.44MB),
media directory and MAME audio-output enablement. Use your own files; no firmware
is downloaded. A missing path or failed startup leaves the interface available
with the settings form open. Correct the paths, confirm replacement of current
sampler memory, then apply. Dirty/busy media must be exported/finished first.

Validation occurs before closing a live machine. Successful startup atomically
publishes `settings.json` in the profile's `--state-dir`; failed startup preserves
the previous saved settings. Applying settings reboots and loses unsaved memory,
as the confirmation states. Save a session/export disks before applying.

The next launch reads the saved settings. Explicit `--boot-rom`, `--system-disk`
and `--media-dir` arguments override saved paths; `--no-sound` forces initial
muting. A corrupt settings file is reported in the setup UI and can be replaced
by applying valid settings. Runtime executable and state-directory selection stay
with the launcher. The plugin configuration adapter is still pending.

Browse the configured sample images with Gotek **Up**, **Down** or its encoder,
then press Gotek **Select** to insert. The drive display distinguishes the
selected image from acknowledged insertion. Use the firmware's **Disk → Load**
menu to load its performance. Allow listing/loading to finish before the next
action. **Session and media** inside Configuration contains recovery, session,
restart/reconnect, disk export/eject and write protection.

The native standalone shares the VST front-panel renderer and CRT housing,
including the same crop of unused transport rows. No captions or controls
separate the rack and optional keyboard; both scale together to fit the window.
The MIDI selector in Configuration lists MAME input ports; **On-screen keyboard
only** disconnects physical input. Physical-device timing still needs a
hardware-input acceptance run.

Closing the desktop window stops its runtime. State/logs default to the local
`docs/ic20-hle-findings/chatGPT-work/standalone-state` folder; use `--state-dir`
for a separate session. Do not share a state directory between instances.

## Build a desktop executable

Install PyInstaller and the standalone requirements, then run:

```powershell
./scripts/build_standalone.ps1
```

The script packages the executable, React assets, Lua adapter and existing MAME
binary/plugins. Firmware and sample images are excluded. Copy your own firmware
to the paths above, or use command-line path overrides. The package is a
development player, not a signed installer. The exact reviewed distribution
profile is documented separately below.

Every build now retains full MAME license texts and available dependency notices,
then runs an identity/private-media audit. `PACKAGE-AUDIT.json` records the
result and `DEVELOPMENT-ONLY.txt` labels an ordinary new build. The reviewed
Windows standalone profile includes source archives and a `DISTRIBUTION.md`
record. `-Release -OutputDirectory <existing-output>` verifies that existing
package against the trusted exact-file manifest; it does not build or approve
new artifacts. See [distribution qualification](../../testing/distribution-qualification.md).

## Validation and boundaries

`python scripts/verify_native_runtime.py` explicitly requires local firmware and
`ROBOFULL.IMG`. It checks boot pixels, long mouse movement and reversal, firmware
disk loading, MIDI-triggered native audio, a silent note-off tail and shutdown.
It writes evidence only under the local work folder. The Python unit tests also
cover transport EOF, frame geometry/colour conversion and malformed inputs.

The runtime uses private loopback connections and per-launch authentication.
Browser display updates are bounded and replaceable; the transport does not
replace firmware execution. The runtime protocol is separate from React so a
native/plugin client can implement it. The [native VST3 development factory](native-plugin-selection.md)
now uses the same runtime and passes host-clocked PCM tests; actual DAW/editor
acceptance, native sampling input and full project state remain unfinished.
Standalone audio continues to use MAME's system output.

Runtime settings offers **Audio output backend** (Automatic, WASAPI, XAudio2 or
ASIO). The Windows backends use **Audio buffer target (ms)**. Applying settings restarts the sampler
after confirmation and persists the selection after successful startup. Existing
settings use Automatic and 0 ms. CLI overrides are `--audio-backend wasapi
--audio-latency-ms 60`; apply the settings form to persist an override.

The buffer target accepts 0–1000 ms; 0 selects the backend default. MAME expresses
this in 20 ms units, so 60 ms becomes `-audio_latency 3`. WASAPI/XAudio2 clamp
nonzero targets to 10–1000 ms and use 30 ms for zero. This is a requested buffer
target, not measured end-to-end latency. Native transport remains stereo
44.1 kHz; Windows/MAME owns device output and conversion. Output uses the Windows
default device; per-device selection, negotiated device-rate reporting, measured
latency and dropout qualification remain open. Input sampling is still disabled.

Normal-speed WASAPI with a 60 ms target passes original-firmware boot/load,
ROBOFULL playback, silent note-off and clean shutdown. This measures native WAV
PCM, not a physical loopback recording or audible output. See
[audio configuration evidence](../../condensed/validation/standalone-audio-settings-2026-10-12.json).

For saving, use the firmware's **Disk → Save** workflow and wait for it to finish,
then click **Export disk**. This writes a new raw image in the session's `exports`
folder and displays its full path. It never overwrites the selected library image.
Move that exported image into your media library to select it in a later session.
Export snapshots controller media; it does not save edits still only in sampler
memory. A busy controller or file error is reported instead of export success.
Insertion reports success only after the controller accepts it. Busy disks and
unexported controller writes prevent replacement. Save and export work you need
before closing: disk-write tracking does not cover edits still in sampler RAM.
Separate periodic/normal-close recovery covers both RAM and controller media
through its last successful checkpoint; exports remain independent portable files.

**Eject disk** removes clean, idle controller media and updates the drive label
only after native acknowledgement. Rejected ejection preserves the displayed
disk. In OS 2.24, Disk/Load with an empty drive displays **Please Insert Disk**;
the player reports that a disk is required. Insert a sample disk and select
Disk/Load again to read its directory. Ejection does not erase samples already
loaded in sampler memory; their playback and note-off remain qualified. Empty
drive export fails without publishing an image.

**Write protect disk** changes the inserted private floppy's native protection
state after acknowledgement. It is unavailable without confirmed inserted media
and while a protection request is pending. Busy controllers reject the change.
OS 2.24 Save reports **Write Protected** and preserves every disk byte; turn
protection off to save again. Protection survives same-build session recall and
is refreshed after display reconnect or restore. Ejection or a new insertion
resets protection. This logical setting is independent of library file permissions;
library originals are always preserved. Read/export remains available while
protected.

For a supported 720KB raw floppy, **Disk → Utility → Format** runs the original
firmware confirmation and formats the private controller copy. Formatting erases
that disk's data; samples already loaded in sampler memory remain available for
Save afterward. Wait for Format to finish, then Export disk to retain the new
image, or use Disk/Save before exporting to put loaded samples back onto it.
Protected media remains unchanged. Formatting makes controller media dirty, so
replacement/ejection requires export. Same-build session recall retains formatted
bytes and dirty state. The qualified profile is OS 2.24, standard 720KB/512-byte
sectors and IC4 RAM DMA; HD, foreign geometries and physical controller timing
remain unqualified. [Format acceptance](../../condensed/validation/standalone-formatting-2026-10-12.json).

`python scripts/verify_native_media.py --write-protect --checkpoint` checks the
firmware protection error, unchanged export, cold recall, writable Save and a fresh
machine reload. All13 generated ROBOFULL sample payloads (119808 bytes) are
preserved exactly; note60 playback and release pass after reload. This does not
qualify every disk format or saving workflow.
Use `--format --checkpoint` instead of `--write-protect` to verify protected
Format rejection, full writable formatting, dirty cold recall and Save/reload.

Remaining work includes physical device hotplug, Windows non-ASIO output endpoint
selection, sustained dropout/clock qualification, measured latency, broader ADC
semantics and clocks, broader formatting profiles,
SCSI workflows and remaining DSP domains. There is no
automatic writeback to library images or recovery beyond the last successful checkpoint.
See [the completion roadmap](../../project/completion-roadmap.md).

## Firmware status and recovery

The header distinguishes booting, observed Perform Play readiness, firmware disk
activity, Disk Load idle, unknown screens and timeout/process failures.
**Disk Load ready** means the firmware operation line is clear, not that every
sample necessarily loaded. Inspect the authentic display for its result.
Recognition currently covers the supplied OS 2.24 profile; other firmware reports
unrecognized status.

**Reconnect display** preserves the running machine and loaded patch. **Restart
sampler** requires confirmation that unsaved sampler memory will be discarded.
A live machine with busy/dirty floppy media rejects restart until the operation
finishes and its writes are exported. If the native child has crashed, the UI
service remains available to start a new child and boot again. Booting alone does
not recover memory; use Restore recovery or Restore saved session to recall a checkpoint. See the
[readiness and recovery contract](../runtime/native-firmware-status.md).

## Saved sessions

Use **Save session** to atomically store the current floppy-runtime checkpoint.
**Restore saved session** requires confirmation before replacing sampler memory;
it also recovers that checkpoint into a new child after a native crash. Disconnect
physical MIDI and export live disk writes before restoring. Reopen with the same
state directory to find the saved slot. The separate automatic recovery slot is
updated every60 host seconds after firmware boot and on normal close; saving
briefly pauses audio. **Save recovery now**, **Restore recovery** and the last
successful recovery time are exposed in the recovery controls. Existing recovery
is held on startup/restart until explicitly restored or replaced with a new
history. A failed close-save cancels desktop close; **Quit without recovery**
requires explicit confirmation to discard later work. Connected physical MIDI
and busy disks can prevent snapshots. Changes after the last successful recovery
remain at risk on forced termination. See the [session contract](native-sessions.md).


## Recording Input Level

The rack Input Level knob sets recording gain independently of Output Level.
Drag vertically, scroll or use arrow keys on the knob. Its indicator follows
native acknowledgement, and saved-session recall restores its gain. Native
unity/half/mute recording, cold recall and Sample Save/fresh Load are qualified
for the experimental44.1kHz stereo input profile. Explicit physical-device capture
is now qualified for the MOTU profile below; input stays disabled by default.
[Control contract and limits](native-rack-controls.md).

## Recording device configuration

The standalone Configuration screen lists Windows MME recording devices. Select
an explicit input, confirm the sampler restart, and apply. **No audio input** is
the default. **Refresh recording devices** updates the list after connection
changes. VST input remains owned by the host application.

The current capture interface requests 44100 Hz, stereo, signed 16-bit PCM.
Unsupported formats, missing devices and stalled capture produce a configuration
error; Windows may convert the device's physical format before this interface.
Live input requires normal-speed emulation. The worker uses eight preallocated
2048-frame Windows buffers and primes four blocks before delivery to the native
16384-frame FIFO. Configuration reports delivered/discarded frames and native
underruns; Windows MME does not expose a reliable physical-driver loss count.
Checkpoint save/restore reopens capture buffers and reports a discontinuity;
physical device buffers are not part of a saved sampler session.

MOTU ASIO test outputs 3/4 physically looped to MME inputs 1/2 deliver distinct
440/880 Hz tones without clipping. Original firmware records 65,514 samples per
channel, matching the captured input PCM exactly, with zero native underruns.
All 276,480 allocated sample bytes survive Sample Save/export/fresh Load.
The full workflow reports 18,432 discarded input frames outside the exact
recorded interval; this is not a zero-loss claim for all wall time. Alternate
rates, physical disconnect/reconnect, driver-level losses and measured latency
remain open. [Physical sampling evidence](../../condensed/validation/native-physical-sampling-2026-10-12.json).

## ASIO playback and recording

Choose **ASIO** under **Audio output backend**, select an installed driver,
then choose **ASIO output pair**, **ASIO input pair** and **ASIO buffer (frames)**.
Input defaults to **No audio input**. Confirm restart and apply; the selections
persist per instance. **Refresh ASIO drivers** discovers the available drivers.
VST audio remains owned by the host application.

The supported interface is44.1 kHz stereo. Buffers64/128/256/512/1024/2048 frames
are offered; unsupported driver/rate/channel/buffer combinations report an error
without silently switching to another backend. Output-off still allows selected
ASIO input. Normal-speed emulation is required. The single duplex device stream
uses native preallocated65536-frame SPSC rings. Its callback performs no Python,
socket, disk, UI, allocation or mutex work. MAME remains the only sampler engine.

Configuration reports driver latency, native/input/output losses and ASIO status
flags. Driver-reported latency excludes native transport and buffering; it is not
measured physical round-trip latency. Save/restore reopens the hardware stream
and reports a discontinuity. Automatic hotplug, alternate rates and indefinite
clock-drift/low-latency qualification remain separate.

An active ASIO driver that stops consuming primed output for two seconds now
reports an error, including when input is disabled. A capture failure pauses
the native sampler and offers **Reopen audio** in Configuration. Reconnect the
configured device and use this button to reopen and re-prime input before
resuming the same machine. Failed reopening leaves it paused. This preserves
RAM and media, but cannot recover audio that was never captured while disconnected.
An empty output queue is not treated as a stopped driver. Low output queues
request an earlier native drain rather than waiting for the normal fallback.

MOTU Pro Audio v2 outputs3/4 and inputs1/2 are tested at44100 Hz with512-frame
buffers. Native ROBOFULL playback, physical loopback, source/package settings and
ASIO firmware sampling/Save/fresh Load are documented in the
[ASIO validation record](../../condensed/validation/standalone-asio-2026-10-12.json).
The packaged development app includes the native bridge and ASIO-enabled
PortAudio. Source builds additionally need `cmake --build build --config Release
--target s760_asio` and the Windows `sounddevice` package's ASIO PortAudio runtime.

Physical MIDI playing is qualified with micro lite Port 5 out cabled to its input:
90 note-on/off cycles reach original-firmware ROBOFULL playback and release to
silence. Software input detach/reselect also passes. Two three-minute runs expose
ASIO output underruns (1610 and102 frames); the earlier-drain change is not a
complete sustained-playback fix. See the
[MIDI and sustained audio evidence](../../condensed/validation/standalone-midi-sustained-2026-10-12.json).

Subsequent binary PCM delivery, full-input-queue output draining and bounded
device-clock pacing use an8192-frame prime watermark and16384-frame output
transport target (371.52ms). Configuration shows the currently queued duration
and target separately from driver-reported latency. This increases scheduling
headroom at the cost of audition latency. A five-minute/150-note physical MIDI
run now reports zero output underruns/discards/native output drops/driver flags;
2048 discarded input frames remain explicitly reported. Every150 native note
pulses and the silent release tail are independently checked. Software failure
pauses native time and actual MOTU stream reopening resumes the same machine.
These results qualify this finite supported profile, not indefinite playback,
arbitrary CPU load or lossless input recording. Physical unplug/replug tests
are outside the requested scope. [Device qualification](../../condensed/validation/standalone-audio-devices-2026-10-12.json).

Windows WASAPI output selection is tested using Realtek Digital Output at its
48 kHz shared mix rate. Native PCM remains44.1 kHz; digital loopback captures
finite output with the expected20,004.5 Hz fixture peak and silent note-off.
This qualifies the selected endpoint and output conversion domain, not analog
converter fidelity. Physical MOTU outputs3/4 to inputs1/2 probes at128/512/1024
ASIO frames measured10.45–88.43 ms from host write to observed input. That upper
bound includes full2048-frame input block completion and worker/API delivery;
it excludes MAME and MIDI transport and is not pure ADC/DAC latency.

## Normal filter rendering

Normal standalone playback now enables the native filter renderer alongside
stereo, interpolation and envelope/loop processing. Firmware TVF settings affect
output within the supported LP/BP/HP word profiles documented in
[native-runtime-protocol.md](../runtime/native-runtime-protocol.md). Unsupported filter
commands/modes retain the raw path; physical moving/resonant accuracy remains
limited. Recording remains opt-in. Existing filter-bypass session archives need
their matching application; the changed audio-profile identity rejects them.
