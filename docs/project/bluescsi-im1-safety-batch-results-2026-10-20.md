# IM1: Volume Dump, stereo, LCD and recovery qualification

2026-10-20. This batch completes eight remaining compatibility/recovery checks on the current combined OS: populated Volume Dump restoration, Roland stereo on a larger writable IMG, full LCD paging, LCD Save System/cold boot, three machine-reset boundaries, completed-D8 checkpoint recovery with a changed catalog, browser exclusion during native Save, and mounted-IMG Delete/cold directory scan. The evidence contains **16 native case records** and **177 additional resident-memory snapshots**.

**IM1 remains open.** Dense MIDI notes expose **BUG-168**: a long native service call makes the browser's elapsed-time accounting miss whole timer wraps. Data, context and command completion pass in this run; the timing gate fails. Complete native stack and indirect ownership bounds also remain unfinished.

## Accepted native results

| Check | Result and scope |
| --- | --- |
| Complete Volume Dump restore | Native whole-Volume Save creates a matching 10 MiB HD2 source with counts 1 Volume / 1 Performance / 22 Patches / 88 Partials / 13 Samples. Reload that Volume, save Volume Dump to a private 720 KB floppy, then start a new process with the dump and matching HDD source. Native F3 Load/Continue restores all 13 clusters and **119,808 exact PCM bytes**, followed by playback and silent release. |
| Roland stereo and 32 MiB writable IMG | Load a native-recorded 44.1 kHz L/R pair from FDD, browser-mount a blank 32 MiB HD2 IMG, and use native Initialize and Sample Save. An independent disk reader verifies both 119,808-byte sample allocations. A fresh browser mount/native Sample Load restores **239,616 exact bytes / 26 clusters**. Native Loop/Smoothing audition produces distinct active left/right channels and silent release; browser Exit preserves playback. |
| LCD paging on current OS | All **100 full 32-byte filenames**, 15 pages forward/back, disabled final Next, immediate Previous and return to Collections pass. No D8 mount is issued. |
| LCD Save System and cold boot | Native LCD Save System formats/saves a private 1.44 MB floppy. A new process boots that exported image, starts with all 76 operation-context bytes cleared, and sends no Toolbox command until explicit collection selection. Index1 Load restores **119,808 exact bytes** and playback. Browser, LCD descriptor, SDS repairs and GB-6 v9 checks survive the export. |
| Three transaction reset boundaries | Ordinary emulator machine soft reset during D7 DATA IN (at least 1,200 bytes), during the first D8 CDB byte, and after successful D8 but before readiness. Each reboots with zero sample allocations, opens fresh Collections with cleared context/no automatic command, and recovers by explicit selection and exact 119,808-byte Load/playback. |
| Completed D8 checkpoint and changed catalog | Capture after D8 succeeds but before readiness. Three restores invalidate fixture media and refuse stale handoff with bounded readiness failure and zero allocations. During one restore, rename private B.iso to C.iso and replace its content with A. A fresh catalog and explicit index1 selection load **A's exact 119,808 bytes** and play correctly. No automatic D8 replay occurs. |
| Conflicting browser/Mode input during Save | Mouse cursor is verified at the Disk header before native WRITE(10). Pressing that header and Mode while subsequent writes are active issues **no Toolbox command**. Save completes with all 119,808 expected sample bytes intact. The native owner word at physical `083BBA` is zero in this case: this demonstrates native UI serialization, not a universal owner-word guard. |
| Native Delete on mounted writable IMG | Native performance Delete and related hierarchy on a browser-mounted 10 MiB HD2 IMG. Before the actual confirmation the file remains byte-identical. Yes changes counts **1/22/88/13 to 0/0/0/0**, and the independent sample reader finds no samples. A new process mounts the saved result and displays an empty native performance list with zero sample allocations. The source fixture remains unchanged. |

The Volume Dump result resolves the earlier source-media test gap by using a native-saved whole Volume as its matching source. It does **not** establish that Volume Dump is a standalone floppy sample backup. The earlier `SINE BIN0023` request remains a failed fixture restoration, not a diagnosed browser defect.

The stereo result extends the qualified writable-media geometry from the earlier 10 MiB examples to a named 32 MiB, 512-byte-sector Roland disk. It does not establish arbitrary geometries or formats. FDD and SCSI IMG remain writable; ISO/CD remains read-only.

## MIDI stress: data pass, timing defect

With 13 samples already loaded, start a 100-entry D7 listing and send one realtime clock plus **128 Note On and 128 Note Off messages**. The native input API accepts at most 256 bytes per call, so the 768 note bytes are supplied in four 192-byte chunks through the ordinary serial MIDI path.

All **769 bytes** arrive in order inside service windows before D7 completes. Across **188 matched service entry/exit pairs**, 34 scratch words, selectors, caller context and SP are preserved; RW38 advances by the exact measured **modulo-65536** service ticks. There are no observed SPC writes from native service. D7 completes all 4,000 bytes successfully, resident PCM remains exact, and playback before/after is unchanged. Lowest observed SP is `1030`; this is an observation, not the complete stack bound or an audio-timing acceptance test.

One service call lasts **479.111125 ms**. Its timer-read interval is **479,039 ticks**, but the 16-bit difference is only **20,287 ticks**. The missing **458,752 ticks equal seven complete TIMER1 wraps**. The outer browser budget also subtracts only successive 16-bit timer readings, so it cannot recover those whole wraps. D7 lasts about **998.470125 ms** in this finite workload.

This is the concrete failure behind **[BUG-168](bug-backlog.md#bug-168--long-midi-service-loses-whole-timer-wraps-from-browser-deadlines)**. Native parser `000F:213A` drains a live MIDI ring while arrivals remain enabled; no per-service quota has been established. The browser's total command deadline cannot be claimed as a wall-time bound while an unbounded service call can bypass its checks. RW38's modulo idle adjustment is not itself a scratch-corruption bug.

The remaining timing work must establish bounded service/arrival behavior or a scheduling workaround and make elapsed-time accounting safe across the resulting service interval. Then repeat dense note traffic, stalled-transfer deadlines, cancellation, SDS and Remote Mode races. No timing repair or new firmware image is claimed in this batch.

## Resident memory and identities

All **7,360 immutable/gap bytes** in the 8,002-byte browser reservation survive **177 new snapshots** across the accepted workflows. The same 642 explicitly mutable bytes are excluded. This extends the earlier 366-snapshot census; it does not prove absence of unobserved indirect aliases or DMA.

| Artifact | SHA-256 |
| --- | --- |
| Unchanged combined OS, GB-6 v9/SDS included | `6297274dd5c33b0b37409d3cddcd53e40b8af6140f2c416fc0213181cd3ba628` |
| Unchanged selectable GB-6 Boot ROM | `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb` |
| Unchanged native emulator | `7c994e8679c51e71801ce7c4ad570983b5a7a7e55f1ae135ed5fc58dda658962` |
| Native LCD Save System export | `9a895c66829644320bfa25e4a0ca29b0c6852d6c765f976a60e8a91e7de87d18` |

Allocation stays **6,452/8,002 bytes**, with **1,550 free / 1,332 code-adjacent**. Original OS and Boot ROM hashes remain exact. No production C++, Python runtime or firmware bytes changed in this batch. The previous **773-test** regression remains the baseline for this same executable; it was not rerun or counted as a new result.

## Reproduction and exclusions

The durable [validation](../condensed/validation/bluescsi-im1-safety-batch-2026-10-20.json) embeds accepted per-case results, fixture/output identities, input scripts, actual observer sources, matched MIDI/service rows and the snapshot manifest. Private runners are under `docs/ic20-hle-findings/chatGPT-work/bluescsi-im1-safety-batch-2026-10-20`; run with `python -X utf8` from the repository root. Each runner creates a new isolated case directory and refuses to overwrite it. Prerequisites are the identified combined candidate, current native executable, saved controller NVRAM and named source fixtures; only private media copies are writable.

The accepted sequences are `create_volume_hdd.py` then `volume_from_hdd.py`; `run_lcd_save_system.py` then `run_lcd_cold_system.py`; `run_reset.py list`, `switch`, `ready`; `run_d8_checkpoint.py`; `run_busy_save.py`; the Save phase of `run_stereo_geometry.py` then corrected `run_stereo_cold.py`; `run_pages.py`; `run_mounted_delete.py`; and `run_midi_stress.py` followed by `analyze_stress.py`. The validation includes the LCD Save System input-command files and dependent source text.

Excluded probe setups are explicit: a performance-only HDD with no Volume record; a soft-reset wrapper that tried to initialize the host bridge twice; a stereo Load key pressed before native All On marking settled; an oversized MIDI API call rejected before sending its note bytes; and a Delete confirmation click attempted during file scanning. The accepted Delete run waits for screen22 confirmation. The reset probe initializes the bridge only once across ordinary soft reset; the stereo cold case waits for marking before F3. These changes fix private test setup; they do not repair sampler firmware.

Machine soft reset does not qualify physical power/cable/BlueSCSI-only resets. The D8 checkpoint case is at completed-command/pre-readiness, not arbitrary partial-CDB replay. Save exclusion does not qualify every Disk/FDC/conversion conflict. Complete caller/callee/ISR stack, indirect resource ownership and these remaining recovery classes stay open in the [roadmap](bluescsi-image-mount-plan.md). Physical target configuration, actual library preflight and S-760/BlueSCSI timing remain separate. RC-100 input compatibility remains assumed under the user's waiver.
