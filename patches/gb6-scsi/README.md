# GB-6 + SCSI hardware-test candidate

**Hardware testing pending. IM1 is incomplete.** This is the 2026-10-21 candidate
with the BUG-176 ownership rechecks. It retains selectable GB-6 v9 (X4/Y4), adds
the BlueSCSI Image Library, and includes the SDS lifecycle, Verify Medium and
warning-text repairs. It is an experimental hardware-test image.

The exact candidate passed 16 native emulator workflows. Full stack/alias proofs,
physical media/configuration acceptance, and hardware timing remain unfinished.
See the [recorded results](../../docs/project/bluescsi-im1-owner-and-recovery-results-2026-10-21.md)
and follow the [hardware test guide](../../docs/project/bluescsi-hardware-test-guide.md).

## Build

Run from the repository root with Python and `pypcode` installed:

```powershell
python patches/gb6-scsi/build.py --boot-input roms/BOOT/Roland_S-760_v1.11.BIN --os-input S760224.IMG --out-dir temp/work/patches/gb6-scsi
```

Supply the unmodified IC15 v1.11 Boot ROM (32,768 bytes) and OS 2.24 system disk
(1,474,560 bytes). The builder checks both original hashes, checks disassembly and
patch collisions, and requires the generated files to match the hashes below.
The output directory must be new; choose another directory for a second build.

| Output | SHA-256 |
| --- | --- |
| `S760224-BS-IM1.IMG` | `606e277e5f11a4ca1b59dadaf4e9a8395e6c8eed1e3674b4efa78bf3bf1767e4` |
| `Roland_S-760_v1.11.GB6.BIN` | `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb` |

The output includes a manifest, checksums, an example BlueSCSI configuration and
intermediate build/disassembly reports. Keep all generated firmware local.
Use the same GB-6 Boot ROM as the [GB-6-only bundle](../gb6/README.md); if already
installed, keep it and change only the OS disk. Preserve the original EPROM and
system disk for recovery.

## Sources

`build.py` runs `build_browser.py` and `build_full.py` in fresh processes. The
browser uses `asmkit.py`, `relax.py` and `parser_quota.py`; the combined builder
links the GB-6 implementation and the `patch_sds_*.py` and `patch_disk_*.py`
components in this folder. Individual SDS files retain earlier repair stages
for reproducibility; use `build.py` for the complete candidate.

[source-provenance.json](source-provenance.json) records the restored candidate
source identities. These builders no longer depend on the deleted research
archive or private validation JSON files. The included configuration is an
example to merge with the device's existing configuration, as explained in the
hardware test guide.
