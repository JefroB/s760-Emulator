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
and pending native MIDI/captured PCM under the [checkpoint contract](NATIVE_CHECKPOINTS.md).
The runtime executable, firmware and Lua protocol identities must match. SCSI
media, external MIDI device handles and plugin-side queues are not supported.
The browser sends no filesystem paths; the service owns the fixed session slot.

Recovery returns to the last successful save. Changes after it are lost; there
is no periodic autosave. Keep using the same `--state-dir` when reopening the
standalone to discover that saved slot. Session archives may contain copyrighted
firmware/sample data and belong in private user storage, not release packages.

Native acceptance:

```powershell
python scripts/verify_native_checkpoint.py --standalone-session --state-dir docs/ic20-hle-findings/chatGPT-work/session-acceptance
```

The runner boots and loads through firmware controls, verifies131072 exact
stereo frames and restored displays, kills its own native child, restores into
a new child, and checks recovered patch playback/release and unchanged archive.
The real-browser test also covers Save session → restart → confirmed restore
and restored ROBOFULL patch-table pixels. See the
[acceptance record](condensed/validation/native-session-2026-10-11.json).
