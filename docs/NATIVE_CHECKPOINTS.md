# Native runtime checkpoints

The Python native client can now save and restore a versioned checkpoint into a
fresh MAME process, including bounded SCSI media and transfers. The plugin
combines this with host queues and converter state; see [plugin state](NATIVE_PLUGIN_STATE.md).
Automatic recovery of unsaved edits is not implemented.
The standalone now exposes [explicit session save/restore and last-save recovery](NATIVE_SESSIONS.md).

## Contract

Stop incoming host MIDI, disconnect physical MIDI and pause the runtime before
checkpointing. Saving/loading rejects a running machine or an external MIDI
device. Pending scheduled events, an active voice and bytes already inside the
native MIDI serial transmitter are supported.
Existing host/plugin PCM and event queues are outside this contract.

```python
runtime.request('pause')
runtime.save_checkpoint(Path('session.s760state'))
# In a fresh runtime with the same executable and firmware:
runtime.request('pause')
runtime.load_checkpoint(Path('session.s760state'))
# Continue demand rendering, or resume normal firmware execution:
runtime.request('resume')
```

Save publishes through a flushed temporary file and atomic replacement. Failed
save preserves the previous destination. The archive starts with `S760CKP2`, a
little-endian u32 JSON length, the manifest and a native payload. Version2 pins
SHA256 identities of MAME, the boot ROM, system disk, runtime Lua script and
external SCSI backing files, plus
payload length/hash. Restore validates these before invoking native state load.
This intentionally rejects other builds; migration is not implemented.

The private `runtime-checkpoint.bin` slot is a transport file, not the public
archive. Its three little-endian u32 lengths describe runtime JSON, MAME state
and retained interleaved stereo PCM. Lua metadata restores capture counters,
queued PCM, mouse counters/targets, host button values and scheduled MIDI. On
load, MAME cancels old coroutine waiters before Lua installs and rearms the saved
events. Absolute sample timestamps, delivery history and scheduler errors are
retained. Version1 archives are rejected; migration is not implemented. Host sockets and file
handles remain attached to the new process. Driver state includes handler-backed
banks/wave RAM, native voice/filter state, VRAM/LCD controllers, EEPROM, gate/IRQ
registers, floppy controller state and its in-memory disk contents/revisions.
The MIDI transmitter ring and busy/read/write state are registered as well as
the serial interface's existing bit/timer state.

The live floppy vector can resize; fixed1474560-byte save storage plus an actual
length avoids registering a pointer that media replacement could invalidate.
Restored export acknowledgements are invalidated because host export files belong
to the previous timeline. Dirty restored media remains protected until export.
SCSI device metadata, startup-sized image buffers and transfer bytes are now saved.
External SCSI images are limited to 64 MiB total and must have identical backing
filenames/content at startup and recall. Native state is bounded to 256 MiB, the
transport slot to 257 MiB and Python archive to 258 MiB. Floppy support remains
720KB/1.44MB raw images. See [SCSI acceptance](condensed/validation/native-scsi-state-2026-10-11.json).

## Evidence and limitations

The [native acceptance record](condensed/validation/native-checkpoint-2026-10-11.json)
contains source/binary/fixture hashes and results. Tests boot original firmware,
load ROBOFULL through its controls, checkpoint, then launch a fresh process:

- Active playback replays65536 stereo float frames byte-exactly; note-off returns
  to silence. Both CRT/LCD frames match after the next native refresh.
- A second checkpoint taken22.676 microseconds after MIDI enqueue (before one
  320-microsecond serial byte completes) also replays65536 frames exactly.
  The fresh process is supplied no sample disk; the archive is sufficient.
- Firmware Save creates dirty media; cold restoration preserves the bytes and
  dirty revision. Ejection still rejects. Export matches byte-for-byte and a
  fresh firmware reload preserves all13 sample payloads (119808 bytes).
- Corrupt archives reject before native mutation; running checkpoints reject
  without publication.204 Python regressions pass.
- [Version2 evidence](condensed/validation/native-scheduled-checkpoint-2026-10-11.json):
  pending note-on/off survives cold restart and repeated recall, reproducing
  131072 stereo float frames exactly with silent release. Loading cancels an
  unrelated event from the previous timeline. A measured serial-boundary test
  at45.351 microseconds after enqueue replays65536 frames exactly.

Immediately after restore, MAME's cached screen pixels still belong to the new
process's previous frame. The next emulated frame refreshes them from restored
VRAM/controller state. Do not present that initial cached frame as restored UI.
C++ stream snapshot primitives now preserve unread PCM, pending input blocks,
MIDI offsets and the host clock at a stopped boundary. Unit tests verify sample
order, padding and a queued note-off across reconstruction. These primitives are
now combined with native machine and converter state in suspended VST3
getState/setState. Cold and repeated exact replay passes at all three supported
rates; see the [plugin state contract](NATIVE_PLUGIN_STATE.md). Larger SCSI profiles, relocation
across builds, concurrent UI actions and automated recovery remain open.

Reproduce from the repository root with user-supplied firmware and ROBOFULL:

```powershell
python scripts/verify_native_checkpoint.py --state-dir docs/ic20-hle-findings/chatGPT-work/checkpoint-test
python scripts/verify_native_checkpoint.py --serial --state-dir docs/ic20-hle-findings/chatGPT-work/checkpoint-serial-test
python scripts/verify_native_checkpoint.py --scheduled --state-dir docs/ic20-hle-findings/chatGPT-work/checkpoint-scheduled-test
python scripts/verify_native_media.py --checkpoint
```

## Additional rewind limitation (timing qualification)

Saving before audio capture, rendering, then rewinding that same process and
restarting capture can produce `Audio overflow during render`; observed at both
44100 and96000 host Hz. Cold restore into a fresh reference child passes. Earlier
capture-enabled scheduled-checkpoint results remain valid for their tested case.
Full snapshot acceptance must cover this additional sequence. See the
[timing qualification](NATIVE_AUDIO_TIMING.md); see the newer plugin-state acceptance below.

Follow-up: `verify_native_checkpoint.py --pre-capture` now exercises the original
firmware-loaded process: save before capture, render note-on/off, then restore
twice and compare131072 stereo frames exactly. This passes with zero drops on
2026-10-11, as does a separate cold-process repeated rewind probe. The earlier
overflow has not reproduced in these isolated tests; no cause or MAME fix is
claimed. Keep it in broader host-state integration acceptance.

## Checkpoint callback boundary correction

The standalone browser regression exposed restored empty patches or stalled
execution even though the archive was valid. A frame hook can pause while still
inside an emulated timer callback; that frame's periodic hook runs before the
timer returns. Buffer save/load now defer until a later paused periodic hook.
The first periodic callback after each pause is skipped for checkpoint purposes.
This changes no firmware registers or opcodes. The original real-browser failure
now passes with the saved ROBOFULL patch-table pixels; native and scheduled MIDI
replay also pass. Earlier137/138 failures remain historical observations, not a
claim that every former rewind case has been retested. Archives from earlier Lua
revisions reject by their protocol identity as designed.
