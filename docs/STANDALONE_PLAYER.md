# Native standalone player

Development implementation, 2026-10-10. The player runs one native MAME machine
and displays its actual CRT/LCD surfaces in React, hosted in a Windows WebView2
window. The original OS handles mouse/panel controls, disk loading and MIDI.
Audio is played by MAME, not synthesized by the React UI.

## Run from source

First supply the files listed in [firmware setup](FIRMWARE_SETUP.md). The project
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

Choose a raw 720KB/1.44MB sample image, press **Insert disk**, then use the
firmware's **Disk → Load** menu to select and load its performance. Allow the
firmware to finish listing/loading the disk before the next action. Hold the
audition button to send channel-1 MIDI; its note selector defaults to60.
The MIDI input selector lists MAME's available input ports. Selecting a device
opens it through MAME's MIDI backend; **Audition only** disconnects physical
input. Physical-device timing/playing still needs a hardware-input acceptance run.

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
new artifacts. See [distribution qualification](DISTRIBUTION_QUALIFICATION.md).

## Validation and boundaries

`python scripts/verify_native_runtime.py` explicitly requires local firmware and
`ROBOFULL.IMG`. It checks boot pixels, long mouse movement and reversal, firmware
disk loading, MIDI-triggered native audio, a silent note-off tail and shutdown.
It writes evidence only under the local work folder. The Python unit tests also
cover transport EOF, frame geometry/colour conversion and malformed inputs.

The runtime uses private loopback connections and per-launch authentication.
Browser display updates are bounded and replaceable; the transport does not
replace firmware execution. The runtime protocol is separate from React so a
native/plugin client can implement it. The [native VST3 development factory](NATIVE_PLUGIN_SELECTION.md)
now uses the same runtime and passes host-clocked PCM tests; actual DAW/editor
acceptance, native sampling input and full project state remain unfinished.
Standalone audio continues to use MAME's system output.

For saving, use the firmware's **Disk → Save** workflow and wait for it to finish,
then click **Export disk**. This writes a new raw image in the session's `exports`
folder and displays its full path. It never overwrites the selected library image.
Move that exported image into your media library to select it in a later session.
Export snapshots controller media; it does not save edits still only in sampler
memory. A busy controller or file error is reported instead of export success.
Insertion reports success only after the controller accepts it. Busy disks and
unexported controller writes prevent replacement. Save and export work you need
before closing: shutdown/crash recovery and edits still in sampler RAM are not
protected by this disk-write tracking.

`python scripts/verify_native_media.py` checks firmware Save, export and a fresh
machine reload. All13 generated ROBOFULL sample payloads (119808 bytes) are
preserved exactly; note60 playback and release pass after reload. This does not
qualify every disk format or saving workflow.

Remaining work includes the full rack-shell integration, physical MIDI acceptance,
audio device/input configuration, sampling, formatting/ejection/write-protection
behavior, session recall, SCSI workflows and remaining DSP domains. There is no
automatic writeback to library images or automatic recovery of unsaved changes.
See [the completion roadmap](COMPLETION_ROADMAP.md).

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
service remains available to start a new child and boot again. This does not
recover unsaved RAM or unexported writes after a crash. See the
[readiness and recovery contract](NATIVE_FIRMWARE_STATUS.md).

## Saved sessions

Use **Save session** to atomically store the current floppy-runtime checkpoint.
**Restore saved session** requires confirmation before replacing sampler memory;
it also recovers that checkpoint into a new child after a native crash. Disconnect
physical MIDI and export live disk writes before restoring. Reopen with the same
state directory to find the saved slot. Changes after the last save are not
recoverable automatically. See the [session contract](NATIVE_SESSIONS.md).
