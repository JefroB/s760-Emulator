# Adversarial Code Review — S-760 Emulator

**Target repository:** `JefroB/s760-Emulator`  
**Review posture:** hostile-input, failure-path, state-corruption, audio-thread, and cross-implementation review  
**Review date:** 2026-10-08  
**Purpose:** Actionable remediation plan for the coding agent. This is a source review, not a claim that every issue has been reproduced at runtime.

## Instructions to the coding agent

Treat this as a bug-finding task, not a feature task. Re-open the current branch and verify every item before editing. Add a failing regression test for each confirmed defect, make the smallest coherent fix, then run focused and full relevant tests. Preserve APIs/state compatibility unless intentionally versioning them. Do not invent hardware behavior. Report exact commands and exit codes; do not claim tests passed unless executed. Use checked arithmetic and explicit byte decoding for binary formats. Never trust counts or lengths from disk images or plugin state. Keep blocking I/O, unbounded allocation, and potentially contended locks out of audio callbacks.

### Severity definitions
- **P0 — Critical:** likely memory corruption, arbitrary crash, destructive data loss, or release-blocking contract violation.
- **P1 — High:** credible crash/data loss, corrupted project recall, audio deadline failure, or broad functional breakage.
- **P2 — Medium:** correctness/interoperability/robustness defect with a bounded workaround.
- **P3 — Low:** maintainability, documentation accuracy, or limited edge case.

Severity is provisional until reproduced. Do not silently downgrade without evidence.

## Executive summary

The most consequential risks found in the reviewed source:

1. Disk parsers consume untrusted counts and sample lengths with insufficient structural validation.
2. The plugin audio process path is not demonstrably real-time safe; it can synchronously run emulator frames until enough audio exists.
3. Plugin state restore is not transactional and stream reads/writes are incompletely checked.
4. The file-backed drive manager has a self-deadlock when replacing a mounted image and can discard dirty data after a failed flush.
5. Block-device size/LBA arithmetic can overflow, and whole images are allocated into memory without a policy limit.
6. MAME sample-loading paths trust on-disk lengths and do not consistently check exact read counts.
7. The UI, MAME driver, and standalone core are separate behavioral models; test coverage in one layer does not prove fidelity in another.

Prioritize data-loss, deadlock, hostile-input, and audio-thread issues before broad refactoring.

## Findings

## P1 — 1. `FileBackedBlockDevice::mount_file()` can self-deadlock when replacing a mounted image

**Location:** `core/src/s760_drive_manager.cpp`, `FileBackedBlockDevice::mount_file()` and `unmount()`.

**Evidence:** `mount_file()` acquires `m_mutex` with `std::lock_guard`; if already mounted it calls `unmount(true)`, which tries to acquire the same non-recursive mutex.

**Impact:** Mounting a new floppy/SCSI image over an existing one can hang indefinitely, including during state recall.

**Fix:**
- Do not call a public method that reacquires the mutex while locked.
- Add locked internal helpers or perform the entire transition under one lock.
- If flushing the old image fails, preserve it and return failure.
- Make failed mount attempts preserve the prior mount.

**Tests:** Mount A then B and assert completion/B mounted; inject flush failure while A is dirty and assert A remains mounted and recoverable.

## P1 — 2. `unmount()` ignores flush failure and can destroy the only modified copy

**Location:** `core/src/s760_drive_manager.cpp`, `FileBackedBlockDevice::unmount(bool flush)`.

**Evidence:** It calls `flush_to_disk()` but ignores the return value, then clears the buffer/path/mounted/dirty state and returns success.

**Impact:** Disk-full, permissions, or I/O failure can silently discard dirty data.

**Fix:** If a requested flush fails, return false and preserve mounted/dirty data. Clear mount state only after successful flush or explicit user-requested discard. Propagate failures to UI/host callers.

**Tests:** Force a flush failure and verify false return, mounted/dirty state retained, and bytes preserved. Verify successful flush clears dirty state.

## P1 — 3. Block-device file sizes and LBA arithmetic are insufficiently bounded

**Location:** `core/src/s760_drive_manager.cpp`, `mount_file()`, `read_sector()`, `write_sector()`.

**Evidence:** `mount_file()` trusts `tellg()` as a vector allocation size. Sector access computes `lba * m_sector_size` and then `offset + sector_size`; both can overflow before the bounds check. Stream-size-to-`size_t` conversion is not validated.

**Impact:** Oversized images can exhaust memory. Extreme LBA values can wrap arithmetic and make `memcpy` access invalid memory.

**Fix:**
- Reject unrepresentable and policy-exceeding image sizes before allocation.
- Validate `buffer_size >= sector_size`, then check `lba <= (buffer_size - sector_size) / sector_size`; avoid overflow-prone multiply/add checks.
- Validate `tellg()` conversion and stream limits.
- Preserve an existing mount if a replacement mount fails.

**Tests:** `UINT64_MAX` LBA reads/writes fail without modifying memory; test empty/sub-sector/oversized files and failed replacement mount.

## P1 — 4. Roland/Akai parsers trust counts, lengths, and alignment arithmetic

**Locations:** `core/src/s760_disk.cpp::RolandS760Disk::parse()`, `core/src/akai_disk.cpp::AkaiS1000Disk::parse()`, and Python mirror `tests/disk_formats.py`.

**Evidence:** Header counts and sample lengths control record traversal. Checks like `offset + slen <= size` and alignment expressions like `(slen + 511) & ~511` can overflow. Truncated payloads may still yield a sample entry with empty data. C++ decodes packed record structs through `reinterpret_cast`, which does not replace validation or explicit endian handling.

**Impact:** Malformed images can be misparsed, accepted as partial success, produce bad offset progression, trigger excessive allocation, or make C++/Python disagree.

**Fix:**
- Define common invariants for each modeled format.
- Validate header/record/payload bounds, count caps, checked alignment, and legal metadata before allocation.
- Implement overflow-safe `range_fits(offset, length, size)` and checked alignment helpers.
- Reject malformed records explicitly or return a typed partial-recovery result; never silently treat truncated data as valid.
- Decode integers as explicit little-endian.
- Apply equivalent limits and semantics in Python.

**Tests:** counts/lengths `0xFFFFFFFF`; truncated headers/records/data; one-byte-short payloads; alignment overflow; odd-byte PCM; invalid sample rate/loop points/root key; valid round-trip. Run fuzzing under ASan/UBSan if feasible.

## P1 — 5. Disk builders can access empty/undersized output buffers and silently truncate images

**Locations:** `core/src/s760_disk.cpp::build_image()`, `core/src/akai_disk.cpp::build_iso()`.

**Evidence:** Akai builder can allocate an empty vector for `total_mb == 0` and then copy its header through `&img[0]`. Roland builder copies its banner without enforcing a minimum requested `size_bytes`. Both builders advance offsets for records and sample data; a payload that does not fit can be omitted while the builder still returns an image.

**Impact:** Undefined behavior for undersized output, plus apparently successful but corrupt images.

**Fix:**
- Validate minimum output size before indexing.
- Check `size_mb * 1024 * 1024` for overflow.
- Preflight total required size using checked arithmetic.
- Return explicit failure when the image cannot fit; no silent partial image.
- Make each record/payload write all-or-nothing.

**Tests:** `build_iso(0)` fails safely; explicit undersized Roland image fails; oversized sample is rejected rather than truncated; test size multiplication overflow.

## P1 — 6. Plugin audio processing performs unbounded emulator work inside the host callback

**Locations:** `core/src/s760_vst3_plugin.cpp::S760Vst3Plugin::process()`, `core/src/s760_clap_plugin.cpp::S760ClapPlugin::process()`, and corresponding VST2 path/shared host functions.

**Evidence:** VST3 loops while the system is running and available audio frames are fewer than requested, calling `m_host.run_frame()` until enough audio appears. CLAP follows the same design. `run_frame()` synchronously invokes the Libretro core. The host ring uses a mutex; process paths can resize scratch buffers when the block exceeds current capacity.

**Impact:** Unbounded callback duration can cause DAW dropouts or hangs if emulation is slow or fails to produce frames. Blocking locks and allocations increase deadline risk.

**Fix:**
- Use a bounded producer/consumer architecture; run emulation on a worker or impose a strict callback work budget.
- Use an RT-safe queue/ring buffer with no blocking mutex on the audio thread.
- Never wait indefinitely for audio. Define underrun behavior and count underruns without logging synchronously.
- Allocate buffers during activation/setup; handle oversized blocks without allocating in `process()`.
- Audit every method called from process for allocations, locks, I/O, and unbounded work.

**Tests:** Bound `run_frame()` calls per callback; simulate a core that produces no frames and assert prompt return with silence; test maximum and oversized blocks; stress small buffers/high sample rates in a plugin host.

## P1 — 7. Plugin state restoration is non-transactional and stream I/O is incompletely checked

**Locations:** `core/src/s760_clap_plugin.cpp::state_load()/state_save()`, `core/src/s760_vst3_plugin.cpp::getState()` and state loader, `core/src/s760_vst_plugin.cpp::restore_state_chunk()/build_state_chunk()`.

**Evidence:** CLAP checks some lengths but does not consistently check exact reads for path/state payloads. Rejected lengths may be skipped without consuming their bytes, leaving parsing misaligned. It mounts paths incrementally before the whole state is validated, and may return success when later restoration failed. Save paths do not consistently verify every write. VST3 writes multiple fields without consistently validating each result.

**Impact:** Truncated/corrupt DAW state can partially mutate a live instance, mount only some disks, or report false success. Length bugs can cause excessive allocation.

**Fix:**
- Define a versioned format with magic, explicit version, fixed-width little-endian lengths, and a total-size cap.
- Parse into temporary state; validate all fields before mutating the live host.
- Require exact read/write counts for every field.
- Reject invalid lengths rather than skipping bytes and continuing.
- Make restore atomic and define missing-media behavior.
- Validate paths and document whether they are absolute/relative; do not silently mount unintended media.
- Audit VST2 offset/length arithmetic for overflow and truncation.

**Tests:** Truncate at every field boundary; corrupt magic/version/each length; simulate short reads/writes; test limits; failed restore must leave original core state and mounts unchanged; round-trip all plugin formats.

## P1 — 8. MAME sample loading can read malformed payloads into wave RAM without byte-safe validation

**Location:** `mame-source/src/mame/roland/s760.cpp`, `populate_factory_waveforms()` disk-loading branches.

**Evidence:** A disk-provided `data_len_bytes` is converted to a word count for `desc.length`, then the original byte count is read into `&m_wave_ram[word_dest]`. The capacity check uses `word_dest + desc.length`, which can overflow, and does not explicitly prove the byte count fits. Odd byte counts are truncated in the word count while the full byte count may still be read. Some reads do not verify `gcount()` before using the data.

**Impact:** Malformed media can cause out-of-bounds writes, partial sample content, or invalid playback ranges.

**Fix:**
- Require even PCM byte lengths.
- Verify `word_dest <= wave_ram.size()` and `sample_words <= wave_ram.size() - word_dest`; prove byte capacity before reading.
- Verify exact reads and reject incomplete samples.
- Validate loop points, sample rate, root key, and final `wave_offset + length` before publishing descriptors.
- Replace unaligned `reinterpret_cast<uint32_t*>` reads from char buffers with explicit little-endian decoding.
- Extract duplicated format parsing into tested helpers where feasible.

**Tests:** Odd/oversized/truncated lengths, invalid loops, and wave-RAM boundary cases; run MAME tests under sanitizers if supported.

## P1 — 9. Fidelity claims and coverage labels overstate what the implementation proves

**Locations:** `README.md`, `docs/OS_EXHAUSTIVE_CODE_MATRIX.md`, `docs/OS_TEST_COVERAGE_MATRIX.md`, `docs/UI_TEST_COVERAGE_MATRIX.md`, `docs/ROLAND_RFSC16A_VDP_AND_DISPLAY_ARCHITECTURE.md`, and CLAP descriptor in `core/src/s760_clap_plugin.cpp`.

**Evidence:** The MAME driver contains hand-rendered screen functions and a hard-coded font (`render_perform_mode`, `render_patch_mode`, `render_partial_mode`, `render_sample_mode`, `render_disk_mode`, `render_system_mode`, `render_rack_panel`) alongside modeled VDP registers/VRAM and custom FDC/SCSI state machines. The CLAP descriptor calls the instrument “Hardware-accurate.” A passing test of the model is not proof of hardware fidelity.

**Impact:** Developers and users can mistake HLE/UI simulation or code-path coverage for verified hardware emulation, contaminating planning and RE evidence.

**Fix:**
- Maintain one fidelity ledger with classes: `Verified against hardware`, `Verified against service manual/protocol`, `Behavioral model`, `HLE/UI simulation`, `Stub`, `Unknown`.
- Link claims to implementation, tests, and evidence.
- Change “hardware-accurate” wording unless measured parity supports it.
- Separate code coverage, unit tests, behavioral correctness, protocol conformance, and hardware comparisons.
- Generated matrices must not hardcode “tested” without an evidence source.

**Acceptance:** Every major hardware claim maps to an implementation and evidence class; CI or a script flags unsupported fidelity claims.

## P2 — 10. MAME's sample loader can misidentify files and fabricate sample metadata

**Location:** `mame-source/src/mame/roland/s760.cpp::populate_factory_waveforms()`.

**Evidence:** Format detection scans a short header or path substrings (`L701`, `waves`, `sound`). Some paths treat a supposed Akai CD region as fixed slices and assign guessed loop points/root keys; other readers infer metadata from fixed offsets. A file name or short banner is not sufficient structural validation.

**Impact:** Arbitrary/malformed files can be accepted as sample disks; metadata and playback may be fabricated rather than decoded.

**Fix:**
- Use explicit detectors with minimum-size and structural validation.
- Separate genuine-format readers from demo/fallback content and expose the source/status.
- Use a deterministic PRNG (fixed seed) for demo noise; current `rand()` can vary across runs.
- Add known-good image fixtures and expected metadata checks.
- Never report a successful media load unless valid sample records were decoded.

## P2 — 11. Libretro callbacks route through a single global active host

**Location:** `core/src/s760_libretro_host.cpp`.

**Evidence:** `S760LibretroHost::s_active_instance` is a single static pointer. Constructing another host overwrites it, and Libretro callbacks dispatch through it. Plugin hosts may create multiple instances.

**Impact:** Multiple plugin instances can route audio/video/input callbacks to the wrong host, contaminate state, or create lifecycle bugs.

**Fix:**
- Establish whether the loaded core is singleton-only and enforce that contract if necessary.
- If multi-instance support is required, design for Libretro's callback model explicitly; do not assume a simple per-instance userdata pointer is available.
- Test two instances, unload/reload, destruction order, and failed loads.

## P2 — 12. Failed Libretro core loading may leak a dynamic library handle

**Location:** `core/src/s760_libretro_host.cpp::load_core()/unload_core()`.

**Evidence:** `load_core()` opens a module and resolves symbols, then calls `unload_core()` if a symbol is missing. `unload_core()` immediately returns when `m_core_loaded` is false. During partial symbol resolution, `m_module_handle` may already be set while `m_core_loaded` is still false.

**Impact:** Repeated failed loads can leak module handles and leave lifecycle state inconsistent.

**Fix:**
- Track “module open” separately from “core initialized.”
- Always close a non-null module handle during cleanup.
- Clear function pointers after unload.
- Call `retro_deinit()` only if `retro_init()` completed.
- Test missing-symbol modules and repeated retry.

## P2 — 13. Binary formats and state chunks assume host endianness

**Locations:** `core/src/s760_disk.cpp`, `core/src/akai_disk.cpp`, `core/src/s760_dsp.cpp`, plugin state code.

**Evidence:** Multiple integers are copied from raw bytes with `memcpy` or native integer reinterpretation. This assumes host byte order and native object representation.

**Impact:** Formats/state are not portable to big-endian hosts and are brittle across ABI changes.

**Fix:** Add `read_le16/read_le32/write_le16/write_le32` helpers and use them consistently. Keep packed structs as layout documentation, not the primary untrusted-input decoder. Add byte-exact tests.

## P2 — 14. C++, Python, and MAME implement overlapping disk readers with divergent contracts

**Locations:** `core/src/s760_disk.cpp`, `core/src/akai_disk.cpp`, `tests/disk_formats.py`, `mame-source/src/mame/roland/s760.cpp`.

**Evidence:** Multiple independent implementations use different count caps, offsets, defaults, and parsing approaches. MAME contains additional ad-hoc readers. A test passing in one implementation does not establish parity in the others.

**Impact:** The same image can be interpreted differently by tests, the standalone core, and MAME.

**Fix:**
- Document each modeled format and distinguish verified from inferred fields.
- Maintain a common binary fixture corpus and expected canonical decoded representation.
- Require C++, Python, and MAME reader paths to agree on supported fixtures.
- Add round-trip, truncation, malformed-input, and fuzz tests.

## P2 — 15. DSP utilities need edge-case and signal-quality validation

**Location:** `core/src/s760_dsp.cpp`.

**Evidence:** The project includes custom loop crossfade, time stretch, digital filtering, and PCM packing/unpacking. The time-stretch routine is a simple overlapping-window method, not a phase vocoder or correlation-aligned algorithm. PCM conversion uses native-endian `memcpy`. Basic output-size assertions do not prove signal quality.

**Impact:** Artifacts, silence/hole regions, poor transient behavior, invalid numeric inputs, or platform-dependent PCM interpretation can go undetected.

**Fix:**
- Validate finite numeric parameters, sample rates, filter types, output-size arithmetic, and allocation caps.
- Add frequency-response tests, loop-boundary discontinuity metrics, and tone/transient/silence tests for stretching.
- Document the algorithm and limitations.
- Decode/encode PCM explicitly as signed little-endian.

## P2 — 16. React state updater callbacks perform side effects

**Location:** `google-ui/src/App.tsx`, including `handleTogglePower`, `handleSetVolume`, and `handleSoftKey`.

**Evidence:** Some `setState(prev => ...)` updater functions call side-effecting code such as `emitHardwareEvent()`, `soundFx.setVolume()`, `triggerAudition()`, `handleMountDisk()`, or `handleToggleUsb()`. React can re-run updater functions in development/Strict Mode to detect impure updates.

**Impact:** Duplicate events, audio triggers, disk mounts, or inconsistent UI state.

**Fix:**
- Keep state updater callbacks pure.
- Execute each side effect once in the event handler, outside the updater.
- Audit callback dependencies and stale closures.
- Test under Strict Mode; one user action must cause one side effect.

## P2 — 17. Drive-manager device pointer array lacks manager-level synchronization

**Location:** `core/src/s760_drive_manager.cpp::mount_scsi_device()/get_scsi_device()`.

**Evidence:** `mount_scsi_device()` assigns a new `shared_ptr` into `m_scsi_devices[scsi_id]`, while `get_scsi_device()` reads the same array without a manager-level lock. Per-device mutexes do not protect the array of shared pointers.

**Impact:** If mount/eject and emulation reads occur on different threads, this is a data race.

**Fix:**
- Define thread ownership for mount/eject and sector access.
- Synchronize the pointer array or use a safe atomic/shared ownership pattern compatible with the project's C++ standard.
- Prepare new devices off-lock and swap safely; avoid holding manager locks during long I/O.
- Add concurrent mount/eject/read tests.

## P2 — 18. MIDI event handling does not visibly preserve offsets or general MIDI message lengths

**Locations:** `core/src/s760_vst3_plugin.cpp::process_events()`, `core/src/s760_clap_plugin.cpp::handle_events()`, VST2 event handling.

**Evidence:** VST3/CLAP translate note events into MIDI messages, but the inspected code does not visibly schedule them by event sample offset. CLAP forwards `CLAP_EVENT_MIDI` with a fixed length of three bytes, despite MIDI messages having variable lengths.

**Impact:** Events may shift to block boundaries; CC, program change, pitch bend, and shorter messages may be mishandled.

**Fix:**
- Validate event type and MIDI length.
- Preserve and schedule sample offsets/timestamps within the block.
- Handle supported MIDI message classes explicitly.
- Test note-on velocity zero, note-off, CC, pitch bend, program change, and multiple offsets in one block.

## P2 — 19. MAME save-state completeness needs a field-by-field audit

**Location:** `mame-source/src/mame/roland/s760.cpp`, `machine_start()` and custom device state.

**Evidence:** The driver has many mutable fields: VDP VRAM/registers, LCD state, MMIO latches, EEPROM serial state, IRQ state, FDC phase/buffers, SCSI phase/CDB/data buffer, media state, and audio voices. The inspected initialization manually initializes them. The full source must be checked for `save_item`, `save_pointer`, and postload handling.

**Impact:** If fields are omitted, save/load can restore CPU state while leaving peripherals or in-flight transfers inconsistent.

**Required audit:** Inventory every mutable field and register it or document how it is reconstructed. Test save/restore mid-FDC transfer, SCSI data phase, LCD command, EEPROM serial transaction, active voice, and VDP write. Treat as an investigation task until the full save registration is verified.

## P2 — 20. Custom FDC/SCSI state machines need protocol-level negative tests

**Location:** `mame-source/src/mame/roland/s760.cpp`, `fdc_*` and `scsi_*` handlers.

**Evidence:** The driver uses custom FDC/SCSI command/phase state machines rather than actual uPD72068/MB89352 device cores. This is a valid HLE approach but has many error-path cases.

**Impact:** Happy-path tests may miss hangs or incorrect behavior for absent media, read-only images, invalid CDBs, out-of-range LBAs, short transfers, reset mid-phase, and error recovery.

**Fix:**
- Enumerate every implemented FDC command and SCSI opcode, parameter length, phase, and response.
- Reject malformed/unsupported commands deterministically.
- Bounds-check every transfer.
- Test absent media, write protection, invalid LBA, zero transfer count, malformed CDB, interrupted transfers, and reset mid-phase.
- Track evidence/confidence for protocol behavior.

## P3 — 21. React monitor font provenance is asserted without visible evidence

**Location:** `google-ui/src/components/OP760Monitor.tsx`.

**Evidence:** The font table comment calls it the “Complete 8x8 Roland OP-760 ROM Bitmap Font Table from S-760 VDP firmware,” but no extraction procedure, source offset, or verification artifact is linked in the code.

**Impact:** Future contributors may treat a hand-authored/inspired bitmap font as extracted hardware data.

**Fix:** Link the extraction evidence or relabel it as a UI-simulation font. Keep hypotheses separate from verified facts.

## P2 — 22. VST3 interface and bus contracts need official validator review

**Location:** `core/src/s760_vst3_plugin.cpp`.

**Evidence:** In the reviewed source, `queryInterface()` appears to return an `IComponent` pointer for any requested interface ID. `getBusInfo()`, routing, and bus-arrangement methods return generic success without visibly populating requested structures; `getControllerClassId()` returns false. These may violate host expectations depending on the SDK interface contracts.

**Impact:** Host-specific load failures, broken routing/bus discovery, or validator failures.

**Fix:** Compare every implementation against the exact VST3 SDK contracts. Query only supported interfaces and return the correct interface pointer; populate output structures completely or return the appropriate failure. Run the official validator and test multiple DAWs.

## P2 — 23. Plugin state stores paths, not stable media identity

**Locations:** VST2/VST3/CLAP state save/restore and `S760DriveManager`.

**Evidence:** State saves floppy/SCSI paths and reloads those paths. It does not establish that the file exists elsewhere or is the same image.

**Impact:** Project recall is machine-specific and can silently use different media at the same path.

**Fix:** Store path plus optional size/hash/media identifier; detect missing/changed media; define relocation/missing-media policy; avoid silently writing to unintended host paths.

## P2 — 24. Audio underruns are converted to silence without adequate telemetry

**Location:** `core/src/s760_libretro_host.cpp::read_audio_frames()` and plugin process methods.

**Evidence:** The host fills missing frames with silence. The inspected process paths do not visibly expose a reliable underrun counter/diagnostic.

**Impact:** Intermittent silence can be difficult to distinguish from a sampler bug or missing sample.

**Fix:** Record underrun count and missing frames using RT-safe counters; expose diagnostics on a non-audio thread. Never log synchronously from the callback.

---

## Additional audit items before declaring the review complete

- **VST2 state parser:** verify all chunk lengths, offset arithmetic, version handling, and MIDI event-array bounds.
- **CLAP contract:** validate process status, thread affinity, state extension registration, audio-port in-place pairing, and lifecycle with the official CLAP validator.
- **All plugin formats:** test null buffers, missing buses, mono/stereo layouts, maximum/oversized blocks, non-44.1 kHz rates, and input-monitoring mix behavior. Confirm whether adding input to emulated output is intended and whether headroom/clipping is managed.
- **MAME state registration:** verify every mutable field against the complete current source before calling it defective.
- **Build/CI:** run clean Windows and non-Windows builds, C++/Python suites, sanitizers, MAME boot tests, and official plugin validators. This review did not execute builds or tests.

## Recommended remediation order

### Phase A — Stop data loss and unsafe input
1. Fix `mount_file()` self-deadlock and preserve old state on failure.
2. Make failed flush prevent unmount and data discard.
3. Add block-device size limits and overflow-safe LBA checks.
4. Harden Roland/Akai parsers and builders with checked arithmetic and exact bounds.
5. Harden MAME sample loading and exact-read checks.
6. Make plugin state loading bounded, validated, and atomic.

### Phase B — Protect audio reliability
7. Remove unbounded emulator-frame loops from audio callbacks.
8. Remove blocking locks, allocation, and I/O from callbacks.
9. Add underrun telemetry and deterministic fallback behavior.
10. Validate MIDI message lengths and honor event offsets.

### Phase C — Host compatibility and lifecycle
11. Validate VST3 interfaces/buses and stream handling with the official validator.
12. Validate CLAP lifecycle/state/audio-port behavior with the official validator.
13. Fix Libretro module cleanup and define singleton/multi-instance behavior.
14. Synchronize device mounts against emulation reads.

### Phase D — Fidelity and evidence integrity
15. Build an evidence-based fidelity ledger and correct overclaims.
16. Make fallback sample generation deterministic and observable.
17. Add parser fuzzing, cross-language parity fixtures, and save/restore tests.
18. Add audio golden tests and real-hardware capture comparisons where available.

## Definition of done

A finding is not closed merely because the code compiles. Require:
- a regression test reproducing the original failure;
- the test fails before and passes after the fix;
- relevant existing tests pass;
- malformed input fails safely without OOB access, unbounded allocation, partial mutation, or silent success;
- audio callback work is bounded and free of blocking file I/O/locks/allocations;
- state restore is atomic and versioned;
- failed writes preserve dirty data and report failure;
- fidelity documentation matches implementation evidence;
- a report of changed files, exact commands/tests run, and remaining limitations.

## Review limitations

This review used targeted source inspection and code search on the repository's current default branch. It did not run a local build, sanitizer suite, plugin validator, fuzz campaign, or hardware comparison. The direct code-path findings should be reproduced against the latest checkout before editing; items explicitly labeled audit tasks are not confirmed defects.
