# Firmware readiness and UI recovery

The standalone UI observes original OS 2.24 CRT pixels independently of the
runtime connection. A connected process does not establish successful boot.
The observer never changes guest memory, PC, firmware flags or disk contents.

## States

| State | Evidence and UI behavior |
| --- | --- |
| Booting | Connected, but the firmware Perform Play or Disk Load title has not been observed. |
| OS ready | Recognized Perform Play 1 title in the actual CRT frame. |
| Disk operation | Recognized firmware Load... or Now Working label. |
| Disk Load ready | Recognized Disk Load title and cleared operation line. Inspect the firmware result; this does not assert successful loading of every sample. |
| Unrecognized | Another screen, cursor-obscured signature or unsupported firmware. No invented success result. Previous confirmed boot is retained separately. |
| Timeout | Boot unconfirmed after 60 wall-clock seconds, or a recognized disk operation lasting over 120 seconds. Check the native display; the panel Exit control can cancel firmware operations. |
| Stalled | Emulated time has not advanced for 15 seconds while not paused. |
| Failed | Native transport/process is unavailable. The web service stays alive for recovery. |

Recognition uses fixed label regions, not whole-screen hashes, elapsed-time
success assumptions or nonblack-pixel counts. The supported system image SHA256
is `3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd`.
Other images report unrecognized status. This is conservative screen observation,
not a universal firmware state decoder or proof of every peripheral's health.
The low-level Lua `status.firmware_ready` remains unknown; the standalone layer
publishes a separate `FIRMWARE_STATUS` observation with its message and state.

## Recovery

**Reconnect display** reconnects the authenticated browser transport without
restarting the machine. The loaded patch remains in memory. Disconnection still
releases held controls and notes.

**Restart sampler** opens a confirmation requiring **Discard unsaved sampler
memory**. A live machine with busy or unexported dirty floppy media rejects the
restart; finish the operation and export first. On an acknowledged restart the
old child closes, its lock is released, a new native child boots the original
firmware and readiness starts over. After a child crash the still-running web
service accepts the same restart action. If startup fails, its error is reported
and retry remains available. Library originals are never overwritten.

Restart is recovery to a usable booted machine. It is not restoration of unsaved
RAM or automatic disk recovery after a crash. Those remain separate roadmap
objectives. Firmware/media paths are still supplied at launch; first-run path
selection is a later standalone objective.

## Acceptance

[Recorded evidence](../../condensed/validation/native-readiness-2026-10-11.json) covers:

- Normal-speed real firmware boot, Disk/Load busy-to-idle transitions, Perform
  Play, nonzero native audio and silent note-off.
- Killing only the test-owned child, observing failed status while the service
  remains available, and restarting to OS ready with a new process ID.
- Browser media insertion, firmware loading, reconnect with loaded patch data
  preserved, and acknowledged restart to the empty Perform Play screen.
- Rebuilt desktop WebView2: OS-ready status and 640x480 actual CRT pixels.
- Backend confirmation/dirty-media guards, unknown/timeout/stall cases, and
  React confirmation/status regressions. Unit checks are distinct from native
  firmware and browser evidence.

Reproduce with user-supplied firmware and ROBOFULL.IMG:

```powershell
python scripts/verify_native_readiness.py --state-dir temp/work/readiness-test
```

For browser acceptance launch the standalone service with `--no-browser
--no-sound`, read its URL from the private `session.json` into `S760_NATIVE_URL`,
then run `e2e/native-runtime.spec.ts` with Playwright. Without that environment
variable the native test skips; a skip is not acceptance. Run it at normal speed.
