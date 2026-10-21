# Standalone saved sessions and recovery

Native Studio can save the current floppy-runtime session and restore it after
a restart or native-process crash. This uses the versioned native checkpoint
format, not a second emulation engine. It is not complete VST3 project state.

Press **Save session** and wait for the saved-path acknowledgement. The service
serializes controls, briefly pauses MAME and atomically publishes
`sessions/latest.s760state` under the instance's state directory. It restores
the previous running/paused state afterward, including on save failure. A failed
save retains the previous archive. Each successful save replaces that one slot;
copy the archive separately if you need historical versions.

**Restore saved session** becomes available when the slot exists. Confirm that
current sampler memory may be replaced. Disconnect physical MIDI and export any
live disk writes first. The service checks archive identity/integrity before
stopping or changing a live machine, and refuses live busy/dirty media. If the
machine was paused, media-status acknowledgement briefly runs normal emulation
before pausing again. Native state application then restores the checkpoint.

If the child process has crashed, restore closes the failed runtime, launches a
fresh child and loads the saved session. Normal standalone execution resumes;
the UI re-observes firmware readiness and refreshed native pixels. A healthy
paused machine remains paused after restore. If native state application fails,
execution is left paused for diagnosis and the UI reports the error.

The archive contains sampler memory, sample data, native devices, floppy contents
and pending native MIDI/captured PCM under the [checkpoint contract](../runtime/native-checkpoints.md).
The runtime executable, firmware and Lua protocol identities must match.
Floppy write-protection state is included in the native checkpoint. Standalone
queries the controller after recall/reconnect before enabling the protection
control. A new insertion or ejection resets protection. The changed native build
requires a matching newly saved archive; older executable identities reject.
Bounded native SCSI state is included under the checkpoint contract, but external
SCSI backing files require the same filenames/content in the instance's
`roms/SCSI` directory; automated SCSI-file relocation is not implemented.
External MIDI device handles and plugin-side queues are not included.
The browser sends no filesystem paths; the service owns the fixed session slot.

Manual restore returns to the last explicit save. Standalone also writes a
separate automatic recovery slot, described below. Keep using the same
`--state-dir` when reopening to discover both slots. Session archives may contain
copyrighted firmware/sample data and belong in private user storage, not release packages.

Automatic recovery uses `sessions/recovery.s760state`, independently of manual
`latest.s760state`. Every60 host seconds after observed firmware boot, the service
checks controller idleness, pauses briefly, atomically publishes the native
checkpoint and resumes the previous execution state. Dirty controller bytes and
sampler memory are included; saving recovery does not mark media exported.
Busy disks defer the next attempt; physical MIDI must be disconnected. Failures
retain the previous archive and appear with its last-success timestamp in the UI.
This can pause audio and requires space for the checkpoint plus its temporary
replacement (roughly160MB each in the qualified profile).

**Save recovery now** uses the same path. **Restore recovery** requires explicit
replacement confirmation, validates the same build/firmware/integrity contract
and can launch a new native child after failure. Export busy/dirty live media
before restoring, as with a manual save. Existing recovery is held on startup,
restart, settings changes or manual restore; automatic writes remain blocked
until **Restore recovery** succeeds or **Start new recovery history** explicitly
replaces it. Failed replacement preserves the old archive and pending choice.

Normal desktop close releases held controls/notes and saves recovery first. A
busy controller, connected physical MIDI or save error cancels the close and
reports the reason. Resolve the failure and retry, or explicitly confirm
**Quit without recovery** to discard newer work while retaining existing saved
files. Bounded/headless shutdown attempts the same save and reports a failed
attempt as an error; an external forced termination cannot be cancelled.

Recovery is bounded by the last successful checkpoint. Later edits, work before
the first checkpoint and changes during prolonged busy/error conditions can be
lost on forced termination. Filesystem power-loss guarantees, instantaneous
journaling, plugin autosave and SCSI workflow qualification are not claimed.
Use exports and independent backups for work that must survive these limits.
Native dirty revision134 recovery reproduces131072 stereo frames and both
displays; child-failure and close/reopen disk exports are exact. The production
timer, startup preservation, confirmed restore and explicit quit pass through
the packaged UI. [Recovery evidence](../../condensed/validation/standalone-auto-recovery-2026-10-12.json).

Floppy recovery does not need the original sample image, media-library folder or
private insertion file: the archive contains its own controller media and sample
memory. A missing library may show Runtime settings on startup; **Restore saved
session** remains available and starts a replacement machine from the archive.
Successful restore closes the setup form. Firmware and executable files are
still prerequisites; correct their paths in Runtime settings. Moving those files
is supported when their bytes match. To relocate the session itself, copy
`sessions/latest.s760state` into the new instance's state directory. Keep backups
outside that one replaceable slot.

Version errors explain that migration is unavailable. Identity errors identify
MAME build, boot ROM, system disk, Lua protocol or SCSI media, and direct the user
to the matching application/firmware or backing files. Missing/damaged archives
request the original state directory or a known-good backup. These preflight
failures leave the current machine running with its existing sampler memory.
There is no automatic recovery of edits made after the last explicit save.

Native acceptance:

```powershell
python scripts/verify_native_checkpoint.py --standalone-session --state-dir temp/work/session-acceptance
```

The runner boots and loads through firmware controls, verifies131072 exact
stereo frames and restored displays, kills its own native child, restores into
a new child, and checks recovered patch playback/release and unchanged archive.
The real-browser test also covers Save session → restart → confirmed restore
and restored ROBOFULL patch-table pixels. See the
[acceptance record](../../condensed/validation/native-session-2026-10-11.json).

The same runner now removes its private source library and restores into another
state directory with relocated firmware paths and a deliberately missing initial
sample path. Recovery succeeds, then paused replay reproduces 131072 stereo
frames and refreshed CRT/LCD bytes exactly. The real-browser recovery test starts
with a nonexistent library, restores the loaded patch, and verifies version/build
rejection preserves that live patch before successfully restoring again. See
[current media/session evidence](../../condensed/validation/standalone-media-session-2026-10-12.json).

The rebuilt development executable also passes both native browser workflows,
including missing-library startup/restore and live version/build mismatch
protection. Its WebView returns real firmware pixels and exits cleanly. This is
existing-workstation development-package acceptance; clean-machine installation
and redistribution review of the changed artifact remain separate gates.


Standalone recording Input Level is stored separately from Output Level and
restored before rendering resumes. Native acceptance records exact unity/half/
muted stereo input after cold recall of an armed sampler, with Output Level
muted; Sample Save/fresh Load also preserves those bytes. This is same-build
native offline input evidence; physical capture-device reconnection remains
open. [Input Level evidence](../../condensed/validation/native-input-level-2026-10-12.json).
