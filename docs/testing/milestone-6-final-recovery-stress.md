# Final-Artifact Sustained Lifecycle, Broader Malformed Media and Release Recovery Stress

Completed 2026-10-17 for the Windows standalone development artifact.
Seven broader malformed-media profiles, a sustained 5-cycle complete boot/load/edit/sample/save/reopen
lifecycle, and release recovery stress pass with byte-exact sample preservation and pitch/level verification.
Unit tests and backend regressions pass.

[Source/artifact identities, commands and measured results](../condensed/validation/milestone-6-final-recovery-stress-2026-10-17.json).

---

## 1. Broader Malformed-Media Stress Handling

Earlier milestone milestones qualified size rejection (empty, 720KB±1B, 1.44MB±1B) and uniform unformatted
profiles (all-00 and all-FF). This qualification extends coverage to seven distinct structural and filesystem
malformations on 720KB and 1.44MB floppy geometry:

| Profile | Image | Geometry | Structural Defect | Observed Behavior |
| --- | --- | --- | --- | --- |
| `corrupt_banner_720k` | `CORRUPT_BANNER_720K.IMG` | 720 KB | Non-Roland volume banner in sector 0 (`NON_ROLAND_FORMAT_MAGIC`) | Safely rejected; directory sentinel shows unknown disk format; zero CPU hang |
| `msdos_fat12_720k` | `MSDOS_FAT12_720K.IMG` | 720 KB | Standard MS-DOS 5.0 FAT12 floppy (BPB, `55 AA` boot signature, FAT tables) | Rejected by firmware directory parser; guest RAM and state intact |
| `corrupt_catalog_720k` | `CORRUPT_CATALOG_720K.IMG` | 720 KB | Valid Roland sector 0, but directory cluster table (0x200..0x4000) filled with out-of-range cluster targets (`0xFFF0`) | Firmware detects corrupted catalog records; displays `xxxxxfiles` sentinel without crash or loop |
| `corrupt_sample_hdr_720k` | `CORRUPT_SAMPLE_HDR_720K.IMG` | 720 KB | Sample descriptor at 0x18E00 specifies frame length `0x7FFFFFFF` exceeding 32MB wave RAM | Bounded memory parser prevents buffer overflow or wave RAM corruption |
| `pseudo_formatted_720k` | `PSEUDO_FORMATTED_720K.IMG` | 720 KB | Intact Roland volume banner, but entire allocation table is zeroed (0x00 fill) | Rejected cleanly; no phantom files or partial loads |
| `corrupt_banner_144m` | `CORRUPT_BANNER_144M.IMG` | 1.44 MB | 1.44MB geometry with non-Roland signature in sector 0 | Rejected safely; media status remains clean |
| `corrupt_catalog_144m` | `CORRUPT_CATALOG_144M.IMG` | 1.44 MB | 1.44MB geometry with corrupt cluster pointers across catalog span | Rejected safely without guest CPU fault |

After encountering all seven malformed profiles consecutively in an active session, reinserting the valid
`ROBOFULL.IMG` sample disk allows an immediate, clean firmware Disk Load, verifying complete subsystem recovery.

---

## 2. Sustained 5-Cycle Complete Lifecycle

Five full, consecutive boot/load/edit/sample/save/reopen cycles were executed on the native runtime:

Each cycle executed:
1. **Cold Boot:** Isolated runtime startup from clean state.
2. **Firmware Load:** Mounted `ROBOFULL.IMG` fixture and executed firmware Disk Load.
3. **Parameter Edit:** Performance Part 1 Level reduced 127 $\to$ 64 via VALUE dial (`0x4E40` = 192 / `0xC0`).
4. **Audio Sampling Input:** Queued stereo test tone (440 Hz L / 880 Hz R) into the native ADC input FIFO.
5. **Firmware Save & Export:** Firmware Save to floppy media; exported exact 737,280-byte disk.
6. **Session Checkpoint:** Quiesced machine and generated session checkpoint (`.s760state`).
7. **Cold Reopen (Process A):** Launched fresh process, restored checkpoint, dumped 32MB wave RAM.
8. **Cold Readback (Process B):** Cold boot with exported disk, measured PCM playback across pitch bends.

### Measured Results Across Cycles

Across all five sustained cycles:
- **Sample Allocation Integrity:** All 119,808 bytes across 13 baseline sample allocations at wave offset 16 remained 100% byte-identical.
- **Audio Pitch:** 20,004 Hz across every cycle.
- **Output Attenuation:** Peak level 0.00853716 (matching expected 50.4% attenuation from baseline 0.01694745 for Level 64).
- **Note Release:** Note-off tail was exactly silent (< 1e-7) in all cycles.
- **Repeatability:** Zero drift, zero memory leaks, and 100% deterministic reproducibility.

---

## 3. Release Recovery Stress

Under release recovery stress:
1. **Dirty Media Loss Prevention:**
   - With unexported changes held after firmware Save, attempting to mount foreign or malformed media via `insert_media` is immediately rejected by the mount guard (`Disk is busy or has unexported changes; finish saving and export first`).
   - The unexported floppy changes remain protected and can be exported cleanly.
2. **Abrupt Process-Tree Crash Recovery:**
   - Terminating the process tree while holding dirty media and restoring from checkpoint reinstates dirty media status and retains all 119,808 sample bytes.

---

## 4. Reproduction

To run the complete qualification suite from the repository root:

```powershell
python scripts/verify_final_recovery_stress.py --package . --state-dir docs/ic20-hle-findings/gemini-work/final-recovery-stress-20261017 --cycles 5
```

To run the accompanying unit tests:

```powershell
python -m pytest tests/test_final_recovery_stress.py
```

---

## 5. Explicit Boundaries & Limitations

As specified in the Milestone 6 qualification roadmap:
- **Unqualified Failure Modes:** Physical power loss during write, and forced process terminations at arbitrary partial-payload write offsets, flush/fsync, and atomic rename stages remain unqualified.
- **Host Scope:** Accelerated native emulation on the Windows x64 development workstation; physical analog converter latency and long-term hardware thermal soak are separate.
- **Distribution Scope:** This qualifies the development runtime; public installer and clean-machine distribution require separate qualification.
