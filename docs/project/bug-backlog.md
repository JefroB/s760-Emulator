# S-760 Bug Backlog

Single source of truth for known defects. One row per bug in the table; detailed
entries below. Managed via the `s760-bug-logging` skill — do not hand-reformat;
follow the schema so entries stay machine-greppable.

## Conventions

- **ID:** `BUG-NNN`, zero-padded, monotonically increasing. Never reuse a number.
- **Status:** `OPEN` · `IN-PROGRESS` · `FIXED` · `WONTFIX` · `DUPLICATE` · `CANNOT-REPRODUCE`
- **Severity:** `S1` critical (crash/data loss/boot broken) · `S2` major (feature
  broken, no workaround) · `S3` minor (feature degraded, workaround exists) ·
  `S4` trivial (cosmetic/polish)
- **Area:** one of `ui` · `bridge` · `core` · `mame-driver` · `cpu` · `dsp-audio` ·
  `disk` · `midi` · `build` · `tests` · `docs` · `hardware` (extend as needed).
- **Dates:** ISO `YYYY-MM-DD`.
- Keep the summary table and the per-bug detail section in sync (every table row
  has a matching `### BUG-NNN` entry).
- Fixed/closed bugs stay in the file (do not delete) for history; set their
  Status and `Resolved` date.

## Summary

| ID | Status | Sev | Area | Summary | Opened | Resolved |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| BUG-001 | FIXED | S2 | cpu | Native flag-stack behavior verified; stack-neutral stubs are confined to legacy flat mode | 2026-10-11 | 2026-10-11 |
| BUG-002 | FIXED | S2 | cpu | BMOVI (0xCD) duplicate operand fetch fixed; interrupt semantics remain unaudited | 2026-10-11 | 2026-10-11 |
| BUG-003 | FIXED | S2 | dsp-audio | Seven loop modes verified in the supported 44.1 kHz native profile | 2026-10-11 | 2026-10-11 |
| BUG-004 | FIXED | S2 | midi | IC4 natural interrupt priority arbitration and 64-byte MIDI FIFO buffering implemented | 2026-10-11 | 2026-10-17 |
| BUG-005 | OPEN | S3 | dsp-audio | Offline ramps near2%; user target below1% remains unmet | 2026-10-11 | |
| BUG-006 | WONTFIX | S3 | disk | Disk reload metadata difference is expected; payloads and full-session wave RAM integrity verified | 2026-10-11 | 2026-10-14 |
| BUG-007 | FIXED | S2 | tests | Generated coverage matrices now separate unverified inventory from scoped test evidence | 2026-10-11 | 2026-10-11 |
| BUG-008 | FIXED | S3 | build | Shared reference-DSP claim corrected to the actual isolated native MAME architecture | 2026-10-11 | 2026-10-14 |
| BUG-009 | FIXED | S2 | core | Checkpoint save/load executed inside an emulated-timer callback → restored empty patch table | 2026-10-11 | 2026-10-11 |
| BUG-010 | FIXED | S3 | build | Desktop package omitted MAME full license texts and had no development/release audit gate | 2026-10-11 | 2026-10-11 |
| BUG-011 | FIXED | S3 | docs | README claimed a project-wide BSD license and linked to a nonexistent LICENSE | 2026-10-11 | 2026-10-11 |
| BUG-012 | FIXED | S3 | docs | Boot-ROM setup asserted unsupported download permissions and described verified boot as unqualified | 2026-10-11 | 2026-10-11 |
| BUG-013 | FIXED | S2 | core | Failed native plugin restore allowed a fresh instance to resume an uncertain timeline | 2026-10-11 | 2026-10-11 |
| BUG-014 | FIXED | S2 | mame-driver | SCSI checkpoint omits transfer buffer and media state | 2026-10-11 | 2026-10-11 |
| BUG-015 | FIXED | S2 | disk | SCSI WRITE now updates private media; protection, ranges and checkpoint recall tested | 2026-10-11 | 2026-10-11 |
| BUG-016 | FIXED | S3 | build | Package notice inventory omits actual frozen dependencies and nested vendor DLL attribution | 2026-10-11 | 2026-10-11 |
| BUG-017 | FIXED | S3 | build | Native source archive filter misses forbidden upstream test-media extensions | 2026-10-11 | 2026-10-11 |
| BUG-018 | FIXED | S3 | build | Package audit skips nested files named PACKAGE-AUDIT.json | 2026-10-11 | 2026-10-11 |
| BUG-019 | FIXED | S3 | ui | Malformed native session JSON escapes the display event handler | 2026-10-11 | 2026-10-11 |
| BUG-020 | FIXED | S2 | ui | Gated C++ WebView2 backend reports success without creating an editor | 2026-10-11 | 2026-10-11 |
| BUG-021 | FIXED | S2 | ui | VST3 view exposes a private tick but installs no UI frame timer | 2026-10-11 | 2026-10-11 |
| BUG-022 | FIXED | S2 | bridge | Live editor frame polling starves native plugin audio | 2026-10-11 | 2026-10-11 |
| BUG-023 | FIXED | S2 | bridge | C++ bridge accepts panel/pointer controls without routing them | 2026-10-11 | 2026-10-11 |
| BUG-024 | FIXED | S1 | bridge | VST3 local interfaces are ABI-incompatible with SDK hosts | 2026-10-11 | 2026-10-11 |
| BUG-025 | FIXED | S2 | ui | Embedded live CRT clicks hit demo handlers; native held mouse input missing | 2026-10-11 | 2026-10-11 |
| BUG-026 | FIXED | S2 | ui | SoundCheck editor clips the rack and shows unused native CRT rows | 2026-10-11 | 2026-10-11 |
| BUG-027 | FIXED | S2 | ui | Embedded rack uses demo controls and empty Gotek display; Shift chords inaccessible | 2026-10-11 | 2026-10-11 |
| BUG-028 | FIXED | S2 | mame-driver | Native LCD stays blank despite firmware status-message writes | 2026-10-11 | 2026-10-11 |
| BUG-029 | FIXED | S2 | bridge | Native plugin media pulse released before driver acknowledgement | 2026-10-11 | 2026-10-11 |
| BUG-030 | FIXED | S2 | bridge | Absolute mouse position drifts after firmware Menu/Exit interaction | 2026-10-11 | 2026-10-11 |
| BUG-031 | FIXED | S2 | bridge | Plugin checkpoints omit media browser state and retain stale insertion labels | 2026-10-11 | 2026-10-11 |
| BUG-032 | FIXED | S3 | ui | Plugin editor discovery ignores configured native root | 2026-10-11 | 2026-10-11 |
| BUG-033 | FIXED | S2 | bridge | Uninitialized LCD registers stall fresh runtime startup and cold restoration | 2026-10-11 | 2026-10-11 |
| BUG-034 | FIXED | S3 | tests | Shift synchronous-dispatch test incorrectly measures wall-clock host scheduling | 2026-10-11 | 2026-10-11 |
| BUG-035 | FIXED | S2 | bridge | Initial output knob used digital override API for a MAME adjuster | 2026-10-11 | 2026-10-11 |
| BUG-036 | FIXED | S3 | bridge | Worker display cache omits output-level metadata | 2026-10-11 | 2026-10-11 |
| BUG-037 | FIXED | S3 | tests | Rack recall test reused monotonic WAV offsets after guest-time rewind | 2026-10-11 | 2026-10-11 |
| BUG-038 | FIXED | S3 | tests | Native verifier gives normal-speed 35-second wait only 30 seconds | 2026-10-12 | 2026-10-12 |
| BUG-039 | FIXED | S3 | bridge | Missing source sample path or startup error blocks self-contained session recovery | 2026-10-12 | 2026-10-12 |
| BUG-040 | FIXED | S2 | disk | Floppy protection, firmware Save rejection and cold recall qualified | 2026-10-12 | 2026-10-12 |
| BUG-041 | FIXED | S2 | disk | Native 720KB firmware formatting, protected rejection and Save/reload qualified | 2026-10-12 | 2026-10-12 |
| BUG-042 | FIXED | S2 | bridge | Standalone periodic/normal-close recovery preserves dirty media and manual saves | 2026-10-12 | 2026-10-12 |
| BUG-043 | FIXED | S2 | mame-driver | Observed A7 wave-to-RAM DMA completes firmware sampling postprocessing | 2026-10-12 | 2026-10-12 |
| BUG-044 | FIXED | S1 | ui | Standalone shares approved rack/CRT, restores Gotek and removes UI clutter | 2026-10-12 | 2026-10-12 |
| BUG-045 | FIXED | S2 | dsp-audio | Bounded control ingress now sustains physical standalone stereo recording | 2026-10-12 | 2026-10-12 |
| BUG-046 | FIXED | S3 | dsp-audio | Output-only ASIO detects an active driver that stops consuming queued PCM | 2026-10-12 | 2026-10-12 |
| BUG-047 | FIXED | S3 | dsp-audio | Five-minute supported ASIO playback passes with explicit transport buffering | 2026-10-12 | 2026-10-12 |
| BUG-048 | FIXED | S2 | dsp-audio | ASIO counts all missing frames while waiting to re-prime output | 2026-10-12 | 2026-10-12 |
| BUG-049 | FIXED | S2 | dsp-audio | Audio errors pause native time; actual driver reopening preserves the machine | 2026-10-12 | 2026-10-12 |
| BUG-050 | FIXED | S2 | dsp-audio | Windows endpoint mappings require MAME's output-node prefix | 2026-10-12 | 2026-10-12 |
| BUG-051 | CANNOT-REPRODUCE | S3 | build | One initial windowed test-package launch failed before session publication | 2026-10-12 | 2026-10-12 |
| BUG-052 | FIXED | S2 | midi | Native VST3 lacks controller mapping and ignores host controller queues | 2026-10-12 | 2026-10-12 |
| BUG-053 | FIXED | S3 | tests | Private SoundCheck test processor drops pending parameter automation | 2026-10-12 | 2026-10-12 |
| BUG-054 | CANNOT-REPRODUCE | S3 | ui | Knob indicator visual defect; fix required before shipping, shared frontend impact suspected | 2026-10-12 | |
| BUG-055 | FIXED | S3 | bridge | Native VST3 now reports potentially infinite sustained-voice tail | 2026-10-12 | 2026-10-12 |
| BUG-056 | FIXED | S2 | dsp-audio | Native VST launcher enables stereo mixer; MIDI pan now reaches native L/R output | 2026-10-13 | 2026-10-13 |
| BUG-057 | FIXED | S2 | dsp-audio | Optional native stereo host ADC input records and saves exact firmware samples | 2026-10-13 | 2026-10-13 |
| BUG-058 | FIXED | S2 | hardware | User reseated misplaced internal wheel; GB-6 now works with installed experimental OS | 2026-10-13 | 2026-10-13 |
| BUG-059 | FIXED | S3 | hardware | User confirms v8 vertical gain4 fixes row selection; matching X4/Y4 v9 generated | 2026-10-13 | 2026-10-13 |
| BUG-060 | FIXED | S3 | tests | Functional controller/filter QA explicitly negotiates offline processing; realtime checks stay separate | 2026-10-13 | 2026-10-14 |
| BUG-061 | FIXED | S2 | dsp-audio | Normal standalone launcher enables stereo; pan and cold native replay pass | 2026-10-14 | 2026-10-14 |
| BUG-062 | FIXED | S2 | disk | Native SCSI register window uses byte stride instead of firmware two-byte spacing | 2026-10-14 | 2026-10-14 |
| BUG-063 | FIXED | S2 | disk | Native SPC command classes and INTS acknowledgement use legacy synthetic semantics | 2026-10-14 | 2026-10-14 |
| BUG-064 | FIXED | S2 | disk | Native SCSI fabricates ready HD/CD targets when backing images are absent | 2026-10-14 | 2026-10-14 |
| BUG-065 | FIXED | S2 | disk | Native SCSI idle status permanently asserts busy and reset | 2026-10-14 | 2026-10-14 |
| BUG-066 | FIXED | S2 | disk | Native SCSI initiator readback and selection masks are incorrect | 2026-10-14 | 2026-10-14 |
| BUG-067 | FIXED | S4 | docs | System SavePRM incorrectly described as disk storage | 2026-10-14 | 2026-10-14 |
| BUG-068 | FIXED | S2 | disk | Native SCSI command ACK never drops REQ; present targets stall firmware boot | 2026-10-14 | 2026-10-14 |
| BUG-069 | FIXED | S2 | disk | Observed native SPC-to-RAM DMA47 command is unimplemented | 2026-10-14 | 2026-10-14 |
| BUG-070 | FIXED | S2 | disk | Full native Roland CD blocked by writable-media checkpoint cap | 2026-10-14 | 2026-10-14 |
| BUG-071 | FIXED | S2 | mame-driver | Native Roland Load stalls on unimplemented SCSI-to-wave DMA84 | 2026-10-14 | 2026-10-14 |
| BUG-072 | FIXED | S2 | disk | Native SCSI Format/Save lacks output DMA and counter completion | 2026-10-14 | 2026-10-14 |
| BUG-073 | FIXED | S2 | tests | Sample-disk builder maps explicit TVF envelope times and levels to confirmed firmware fields | 2026-10-14 | 2026-10-14 |
| BUG-074 | FIXED | S3 | build | Packaged README is self-contained; audit rejects broken local setup links | 2026-10-15 | 2026-10-15 |
| BUG-075 | FIXED | S3 | tests | Modulation survey source level too low; V2 raises exact PCM by15x | 2026-10-15 | 2026-10-15 |
| BUG-076 | FIXED | S3 | tests | Native modulation WAV origin inferred from machine status instead of observed PCM position | 2026-10-15 | 2026-10-17 |
| BUG-077 | FIXED | S3 | tests | Firmware analyzer misclassified negative displayed direct targets as indirect | 2026-10-16 | 2026-10-16 |
| BUG-078 | FIXED | S3 | docs | Transfer staging writes incorrectly described as final descriptor publication | 2026-10-16 | 2026-10-16 |
| BUG-079 | FIXED | S3 | mame-driver | Truncated 720KB system media repeatedly hands off and restarts under native boot | 2026-10-16 | 2026-10-17 |
| BUG-080 | FIXED | S2 | mame-driver | Boot-ROM SCSI command transfer stalls waiting for SSTS high nibble B0 | 2026-10-16 | 2026-10-16 |
| BUG-081 | FIXED | S3 | mame-driver | Direct ROM setup receives ghost encoder event when Value model is disabled | 2026-10-16 | 2026-10-16 |
| BUG-082 | FIXED | S2 | mame-driver | Boot-ROM SCSI payload DMA waits with zero IC4 count and no completion | 2026-10-16 | 2026-10-16 |
| BUG-083 | FIXED | S2 | cpu | Native PUSHA/POPA reverses the WSR/mask frame and clears WSR | 2026-10-16 | 2026-10-16 |
| BUG-084 | FIXED | S3 | cpu | Installed MCS96 SLEIGH PUSHA lifting uses the wrong register and stack order | 2026-10-16 | 2026-10-17 |
| BUG-085 | FIXED | S3 | cpu | Native debugger history disassembles ROM fetch PCs through work-RAM data view | 2026-10-16 | 2026-10-17 |
| BUG-086 | FIXED | S3 | cpu | Installed MCS96 SLEIGH has incorrect KB SKIP and IDLPD instruction lengths | 2026-10-16 | 2026-10-17 |
| BUG-087 | FIXED | S3 | tests | OS exploration promotes RET-byte scan candidates with global boundary conflicts | 2026-10-16 | 2026-10-17 |
| BUG-088 | FIXED | S2 | build | Firmware builder copies comment bytes instead of assembling editable instructions | 2026-10-16 | 2026-10-16 |
| BUG-089 | FIXED | S2 | build | Firmware builder silently overwrites aliases and accepts out-of-bounds layout writes | 2026-10-16 | 2026-10-16 |
| BUG-090 | FIXED | S3 | docs | Exported native firmware equates misidentify WSR and FDC/LCD addresses | 2026-10-16 | 2026-10-16 |
| BUG-091 | FIXED | S2 | cpu | Native KB flag/control/NOP instructions use documented two states | 2026-10-16 | 2026-10-16 |
| BUG-092 | FIXED | S2 | cpu | KB control/unary/shift/stack operations retain legacy baseline state times | 2026-10-16 | 2026-10-16 |
| BUG-093 | FIXED | S3 | tests | ROM SCSI fallback selection assertion samples a transient observer stage | 2026-10-16 | 2026-10-16 |
| BUG-094 | FIXED | S3 | tests | Long auxiliary-observer capture disconnects during eighth note | 2026-10-16 | 2026-10-17 |
| BUG-095 | FIXED | S4 | docs | Native short-filter validation limit mislabeled LP/R64 fixture as R0 | 2026-10-16 | 2026-10-16 |
| BUG-096 | FIXED | S3 | docs | Coverage report generators retain pre-reorganization output paths and relative links | 2026-10-17 | 2026-10-17 |
| BUG-097 | FIXED | S2 | build | CI dependency, visual platform and private-artifact prerequisites break hosted tests | 2026-10-17 | 2026-10-17 |
| BUG-098 | FIXED | S3 | docs | Relocated package README template links escape package root and block fresh builds | 2026-10-17 | 2026-10-17 |
| BUG-099 | FIXED | S3 | tests | Packaged media harness leaves native children running after failed trials | 2026-10-17 | 2026-10-17 |
| BUG-100 | FIXED | S3 | ui | Standalone configuration forms a tall document requiring excessive scrolling | 2026-10-17 | 2026-10-17 |
| BUG-101 | FIXED | S3 | tests | Acceptance kit default package paths fail under Windows PowerShell 5.1 | 2026-10-17 | 2026-10-17 |
| BUG-102 | FIXED | S3 | build | Dependency inventory accepts unattributed inputs and reports another installed version | 2026-10-17 | 2026-10-17 |
| BUG-103 | FIXED | S3 | build | Documentation moves and mutable checkout checks invalidate historical artifact identity | 2026-10-17 | 2026-10-17 |
| BUG-104 | FIXED | S3 | tests | Static artifact checker claims unobserved clean-machine and DAW qualification | 2026-10-17 | 2026-10-17 |
| BUG-105 | FIXED | S2 | build | Downloaded acceptance ZIP extracts blocked .NET assemblies and fails before UI startup | 2026-10-17 | 2026-10-17 |
| BUG-106 | FIXED | S2 | ui | Desktop has no clear safe Quit and can leave a worker waiting after window close | 2026-10-17 | 2026-10-17 |
| BUG-107 | FIXED | S2 | build | Double-click runtime writes staged firmware into a research-style directory inside the package | 2026-10-17 | 2026-10-17 |
| BUG-108 | FIXED | S3 | docs | Standalone archive omits an offline user documentation set | 2026-10-17 | 2026-10-17 |

<!-- NEXT-ID: BUG-109 -->

## Details

### BUG-108 — Standalone archive omits offline user documentation

- **Status:** FIXED
- **Severity:** S3
- **Area:** docs
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** User acceptance follow-up

**Summary:** The standalone has a root README but no curated user documentation under docs. The only docs folder seen by the user was generated runtime state.

**Repro:** Extract the original standalone and look for offline user guides in docs.

**Expected:** Distributed Quick Start, full guide, controls and troubleshooting with working relative links; documentation folders contain no runtime state.

**Actual:** The package builder copies the README but installs no user documentation set.

**Resolution:** Install five offline Markdown documents: index, Quick Start, full guide, controls and troubleshooting. Root README links them. Link tests validate every relative documentation link. Build output defaults to build/standalone-package; current QA output stays under temp. Executable content in docs is rejected. See docs/testing/standalone-exit-profile-and-docs.md and its validation record.

### BUG-106 — Desktop Quit is undiscoverable and early close can leave the process running

- **Status:** FIXED
- **Severity:** S2
- **Area:** ui
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** User acceptance follow-up

**Summary:** Desktop Quit is undiscoverable and early close can leave the process running.

**Repro:** Start the application and try to quit without killing its process. Window-close recovery failure can cancel closure without a focused quit choice; an unstarted/dead child path returns from prepare_close without signaling the window worker.

**Expected:** Visible Quit and window X offer save-and-quit or explicit discard; accepted closure stops the app and owned native child.

**Actual:** User reports needing to kill the application. Existing Quit without recovery is buried in Configuration. Closing an unstarted runtime does not signal the worker event.

**Resolution:** Visible Quit and native window X share a save/discard dialog. Early/dead-runtime close signals the worker; WinForms close dispatch runs asynchronously to avoid UI deadlock. Actual frozen WebView2 tests pass missing-firmware X close, boot/save/quit, and existing-recovery refusal followed by explicit discard. App exits0 and owned MAME children stop. See docs/testing/standalone-exit-profile-and-docs.md and its validation record.

### BUG-107 — Packaged default profile creates a research directory and staged firmware

- **Status:** FIXED
- **Severity:** S2
- **Area:** build
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** User acceptance follow-up

**Summary:** Packaged default profile creates a research directory and staged firmware.

**Repro:** Double-click the frozen executable without --state-dir; default state resolves below the application docs/ic20-hle-findings/chatGPT-work folder. NativeRuntime privately stages the user OS image under that directory.

**Expected:** Private profiles, logs and staged firmware belong in per-user application data, outside the installed package.

**Actual:** User reports finding an OS IMG under findings in the distributed folder. Initial inspection of both exact published ZIPs and their host-source archives found no findings or raw firmware entries. The runtime default deterministically creates that path after launch; the user confirmed the exact application-relative docs/ic20-hle-findings/chatGPT-work/standalone-state/roms/s760 path. The IMG is the staged user input, not a shipped firmware file.

**Resolution:** Default private state is now Local AppData/S760Studio/default. Packaged boot and close tests use that default without --state-dir and leave package docs unchanged. Prior profiles are preserved; no automatic deletion or migration. The user confirmed the exact old generated state path. Archive/package checks reject any findings directory. See docs/testing/standalone-exit-profile-and-docs.md and its validation record.

### BUG-105 — Downloaded acceptance kit fails at Python.Runtime startup

- **Status:** FIXED
- **Severity:** S2
- **Area:** build
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** User clean-machine acceptance, File Explorer extraction

**Summary:** The GitHub-downloaded frozen acceptance kit fails before opening the desktop interface on a separate clean Windows machine. The handoff omitted the downloaded ZIP unblocking step and did not qualify File Explorer mark-of-the-web propagation.

**Repro:** Download the acceptance prerelease ZIP in a browser, extract with File Explorer on a clean Windows installation, then double-click S760Studio.exe.

**Expected:** The documented installation path opens the interface, or explains how to resolve blocked downloaded assemblies.

**Actual:** The startup dialog reports Failed to resolve Python.Runtime.Loader.Initialize from the extracted _internal/pythonnet/runtime/Python.Runtime.dll.

**Evidence:** User screenshot dated 2026-10-17 14:00:41 and confirmation that the test used a clean Windows machine with File Explorer. The frozen archive identity remains b1dd036c9331058fb2db0dde75d038e985fc75d5919c19040766460f5cdb08f9.

**Notes:** Locally reproduced with the packaged DLL: Zone.Identifier ZoneId=3 causes .NET FileLoadException / HRESULT 0x80131515; scoped unblocking allows Loader.Initialize resolution. Added checksum-first extraction helper and download/remediation instructions. Three guardrail regressions and extraction of the actual unchanged archive pass; all611 package files verify and the initializer resolves. The user subsequently confirmed that the executable launches and discovers both firmware inputs on the clean machine. The precise remediation performed was not stated. The user accepts the handoff with remaining media workflows waived, as recorded separately. See the durable validation record in docs/condensed/validation/bug105-downloaded-assembly-2026-10-17.json.

**Resolution:** Download trust instructions and a checksum-first extraction helper are published; the user reports successful clean-machine launch and firmware discovery. Full sample-media workflows were not observed and are not claimed.

### BUG-104 — Static artifact checks claim observed release acceptance

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** Codex release acceptance reconciliation

**Summary:** `verify_release_artifacts.py` sets every proposed DAW row qualified and prints a qualified clean-machine matrix after inspecting files/configuration only. Its report also presents unverified source correspondence and literal hash-reference checks as stronger evidence than they establish.

**Repro:** Call `qualify_matrix()` without launching any host or Windows environment; its former five qualified flags are all true. The retained static validation record repeats that unsupported interpretation.

**Expected:** A declared matrix or passing PE/configuration audit cannot qualify installation, source rebuilds, audio/device workflows, private-asset exclusion inside binaries or DAW execution.

**Resolution:** Matrix observations remain NOT_RUN, host flags remain false, and aggregate gate/product/clean-machine acceptance remain false. Source correspondence is explicitly unverified by this checker; literal hash-reference checks do not claim embedded assets are absent. The historical static report now preserves its limited scope and incomplete acceptance. Tests enforce these distinctions and skip absent private MAME artifacts on CI.

### BUG-103 — Historical distribution identity changes with documentation or working sources

- **Status:** FIXED
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** Codex final artifact review

**Summary:** Documentation reorganization rewrote19 file names inside the historical2026-10-11 artifact manifest even though the archived files never moved. The audit also compared an already reviewed runtime/legal snapshot against today's mutable checkout.

**Repro:** Compare the601 historical manifest entries with their original reviewed Git version: all hashes/sizes agree, but19 keys changed. Qualify a fixture, then change only the checkout's Lua protocol or legal source files; the reviewed package previously failed.

**Expected:** Historical file names/hashes remain exact. Trusted whole-tree review controls a reviewed snapshot; development correspondence checks apply to new unreviewed trees.

**Resolution:** Restore only the historical files map from its reviewed version, retaining current documentation references elsewhere. Add an independent digest regression for all601 entries. Exact reviewed snapshots no longer depend on current runtime/legal sources; changed package bytes and added files still reject. Existing README-link checks remain enforced, so this does not requalify old setup defects.

**Evidence:** Historical map digest `f6dd8fdc80d82b431ad3add808153760fdaee09ada7810f26b4d6d30d71aaacd`; focused package-audit regressions and the source-built standalone promotion record.

### BUG-102 — Frozen dependency attribution conceals unknown inputs and version drift

- **Status:** FIXED
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** Codex release promotion review

**Summary:** Collected DLLs counted as mapped even when their component was unattributed. Component metadata came from another installed distribution with the same name, rather than the distribution owning the actual source path. The candidate bundled websockets16.1.1 but reported16.0. MSVCP140.dll also escaped the Windows-runtime externalization policy.

**Repro:** Compare the frozen candidate's BUNDLED-INPUTS.json against its COLLECT records and packaged websockets metadata. A collected mystery.dll previously produced an empty errors list.

**Expected:** Unknown collected inputs fail inventory; versions describe their actual source installation; Microsoft VC runtime is an external prerequisite.

**Resolution:** Bind metadata to each actual source owner, fail unattributed collected inputs and frozen modules, and handle MSVCP140.dll in the checked externalization policy. Nine inventory regressions pass, including duplicate-version installations and unknown collected DLLs. Existing frozen artifacts remain preserved; corrected distribution candidates require revalidation.

### BUG-101 — Acceptance kit default paths resolve before script startup

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** Extracted clean-machine handoff smoke

**Summary:** The new acceptance launcher used `$PSScriptRoot` in parameter-default strings. With Windows PowerShell 5.1 `-File` and no explicit package/manifest arguments, the observed package default became `/S760Studio` instead of the extracted kit directory. Explicit-path verify-only tests had not exercised this path.

**Repro:** Extract the kit into a folder with spaces, change to an unrelated working directory and invoke `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <kit>/Start-Acceptance.ps1` with firmware/media/report arguments but default package/manifest paths.

**Expected:** Resolve `S760Studio` and `PACKAGE-MANIFEST.json` beside the launcher, verify the candidate and open the actual desktop interface.

**Actual:** `Resolve-Path` rejected `/S760Studio` before launch.

**Resolution:** Resolve optional defaults in the script body using the executing script's `MyInvocation.MyCommand.Path`. The reassembled/re-extracted v2 kit verifies all572 files, launches under Windows PowerShell5.1 from an unrelated directory with development-tool environment overrides removed, and passes original-firmware boot plus actual WebView2 configuration readback. The report collector correctly leaves this boot-only run `INCOMPLETE`. [Exact identities and validation](../condensed/validation/milestone-6-complete-standalone-workflow-2026-10-17.json). The candidate application itself is unchanged.

### BUG-100 — Standalone configuration exceeds the display height

- **Status:** FIXED
- **Severity:** S3
- **Area:** ui
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** User review of packaged sampling screenshots

**Summary:** MIDI, recording status, session/recovery/media actions, firmware paths and audio settings render together above the sampler as one long configuration document. Nested confirmations add more height.

**Repro:** Open Configuration in the standalone with a normal desktop viewport. Reaching audio settings or the apply/cancel actions requires extensive page scrolling.

**Expected:** Configuration opens above the sampler in a viewport-bound layer, with category panels, accessible fixed actions and confirmations layered above it.

**Resolution:** Added a portal-based modal layer, category navigation for Session & disks, MIDI & display, Firmware & media and Audio, compact audio grids and a fixed confirmation/action footer. Restart/restore/recovery prompts occupy a higher layer with Escape handling, focus containment/return and background scroll locking. Drafts survive category changes; first-run repair opens firmware settings. Existing UI acceptance cases now navigate the relevant category. All126 frontend tests pass, final focused25 tests and TypeScript pass, and a fresh development package builds/audits without errors. Real native-browser and actual packaged WebView2 acceptance pass at1366×768,1024×768,800×600 and640×480; all default categories fit without scrolling at the two768px-high sizes, while smaller displays retain fixed actions with local panel scrolling. ASIO layout was also visually inspected. [Exact validation and identities](../condensed/validation/bug100-config-layers-2026-10-17.json).

### BUG-099 — Packaged media test cleanup leaves native child processes

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** Milestone 6 abrupt-termination acceptance

**Summary:** The packaged-media harness terminated only its frozen service in its cleanup callback, leaving the spawned MAME process alive after failed tests.

**Repro:** A failed packaged-media trial calls `child.kill()` from the harness finally block. Two MAME instances from the fresh package remained running afterward; their executable and command-line state paths identified them as belonging to these trials.

**Expected:** Cleanup terminates this harness's service and all of its descendants.

**Actual:** Test-owned native children continued using CPU after their parent exited.

**Resolution:** On the Windows package test surface, terminate the specific spawned PID and its descendant tree with `taskkill /PID <owned-pid> /T /F`. Cleanup of the two earlier orphans was restricted to the exact fresh-package executable and private test state paths. No unrelated sampler process was stopped. The crash acceptance uses this bounded termination mechanism; the editing/WebView harness now also applies it to its native and WebView descendants. [Eight-launch WebView qualification](../testing/milestone-6-webview-editing.md) verifies that no tested descendants remain.

**Evidence:** Private `m6-crash-2026-10-17` browser trials and process inspection. This fixes QA cleanup; it does not claim automatic child cleanup for every possible application/OS failure mode. [Three passing termination cycles and identities](../testing/milestone-6-crash-recovery.md).

### BUG-098 — Package README relocation breaks fresh package audit

- **Status:** FIXED
- **Severity:** S3
- **Area:** docs
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** Milestone 6 fresh-package crash-recovery qualification

**Summary:** Documentation reorganization rewrote six package-local links in the standalone README template as `../../` paths. The builder copies this template to the package root, where those links escape the distribution.

**Repro:** Build with `scripts/build_standalone.ps1` using the recorded desktop dependencies. The final package audit reports six `README.md link escapes package` errors.

**Expected:** The copied README resolves its prerequisites, audit, inventories and licenses inside the package.

**Actual:** Fresh package preparation fails closed.

**Resolution:** Restored package-root-relative links and added a regression against the actual shipped template. The new check fails before the correction; all 20 package-audit tests and the fresh package preparation pass afterward.

**Evidence:** Private `m6-crash-2026-10-17/package-audit.log`, `test-before` and `test-after` under the ChatGPT work directory. The changed package remains a development artifact pending release qualification. [Acceptance and identities](../testing/milestone-6-crash-recovery.md).

### BUG-097 — Hosted CI cannot complete either test suite

- **Status:** FIXED
- **Severity:** S2
- **Area:** build
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** User / GitHub Actions

**Summary:** Python collection aborted on an undeclared soundfile dependency. Playwright expected removed rack labels and an uncommitted Linux baseline. The collection error concealed further private-artifact assumptions in backend tests.

**Repro:** [Main run 38674599814](https://github.com/JefroB/s760-Emulator/actions/runs/38674599814), commit `fdc6488cd971a4c5304e4462c76d2b2e07508a3a`; PR run 38674514520 has the same failures. Run pytest from a clean checkout without firmware, extracted binaries or ignored steering notes.

**Expected:** Hosted jobs run the public test surfaces with declared dependencies and reviewed platform baselines. Private-artifact integrations report explicit prerequisite skips.

**Actual:** `ModuleNotFoundError: No module named 'soundfile'`; missing Linux snapshot; expected two `1U` labels but found zero. Clean-export tests also attempted to read local firmware/export/steering files.

**Resolution:** Install soundfile; run frontend CI on Windows to use the existing reviewed desktop baseline; assert both accessible rack ears. Upload Playwright failure evidence. Guard private-artifact integrations and give scope-rule unit tests synthetic input bytes while retaining committed evidence checks. No visual baselines were updated.

**Evidence:** [Validation](../condensed/validation/bug097-ci-pipeline-2026-10-17.json). Clean backend:447 passed/67 prerequisite skips; provisioned backend:514 passed (eight screenshot checks retried after correcting the temporary runner path); Vitest:126 passed; Playwright:9 passed/18 native-package prerequisite skips. Changes remain local pending the next push; remote CI has not tested them yet.

### BUG-096 — Coverage generators retain old documentation locations

- **Status:** FIXED
- **Severity:** S3
- **Area:** docs
- **Opened:** 2026-10-17
- **Resolved:** 2026-10-17
- **Reported by:** BUG-085 full regression run

**Summary:** The documentation folder cleanup rebased published reports but left the OS coverage generator's split output path and the shared report writer's root-relative links unchanged. Four report reproducibility checks failed.

**Repro:** `python -m pytest tests/test_coverage_reports.py -q` after the folder cleanup.

**Expected:** Regenerating each catalogue reproduces its published content and links from its current subject folder.

**Actual:** One report path was missing and three generated reports differed from the published versions.

**Resolution:** Corrected the OS coverage output location; each generator supplies its published document directory independently of the output destination, so temporary-file checks and real reports produce identical relative links. Regenerated the four catalogues. All five coverage-report checks pass, including evidence-reference validation. No coverage claims were promoted.


### BUG-095 — TVFSTEP validation limit mislabeled the fixture resonance

- **Status:** FIXED
- **Severity:** S4
- **Area:** docs
- **Opened:** 2026-10-16
- **Resolved:** 2026-10-16
- **Reported by:** ChatGPT midpoint stimulus review

**Summary:** One limit in native-short-cutoff-trial-2026-10-16.json said LP/R0, while the reproducible TVFSTEP spec sets resonance64 and the analyzer uses damping85/4096.

**Repro:** Compare scripts/build_tvf_transition_capture.py make_spec with that validation limit.

**Expected:** Label this stimulus LP/R64 and keep earlier R0 experiments distinct.

**Actual:** Limit mislabels resonance.

**Evidence:** docs/condensed/validation/native-short-cutoff-trial-2026-10-16.json and scripts/build_tvf_transition_capture.py.

**Resolution:** Corrected label and added explicit source-backed correction note; stimulus, code, hashes and numerical results unchanged.


### BUG-094 — Long capture with auxiliary research observers disconnects

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-16
- **Resolved:** 2026-10-17
- **Reported by:** ChatGPT midpoint calibration verification

**Summary:** Initial14-part TVFGRID verification with private full-memory/firmware/scheduler observers loses its runtime connection during the eighth note, after the original seven controls pass. Underlying process exit reason and causality are not established.

**Repro:** Private filter-midpoint-capture-2026-10-16/verify_native.py long run on the post-BUG-092 executable: WinError10054 while rendering eighth take.

**Expected:** Diagnostic capture should remain connected and finish cleanly.

**Actual:** Connection reset; runtime log has no explanatory error.

**Evidence:** docs/condensed/validation/filter-midpoint-capture-2026-10-16.json records log/script/build hashes and the initial failure.

**Resolution:** Fixed a confirmed Lua/native tap retention cycle: each removed tap's native callback retained its trace table, which retained the tap. Detachment now clears the table's tap references; the native weak-reference regression changes from 24 retained taps after 12 cycles to zero. Promoted the full midpoint verifier and optional research probes into maintained scripts, cached the live PC state entry, and filtered unrelated writes before exporting PC state. All original firmware/scheduler fields and all 14 functional checks remain enabled.

**Validation:** Original probes pass without a memory constraint but peak at about 2540 MiB. Under a controlled 2 GiB process limit they fail after 11 completed takes with `WinError 10054`, exit `0xC0000409`, and native `PANIC: unprotected error in call to Lua API (not enough memory)`. The repaired probes complete all 14 takes under the same limit, peak near 1727 MiB, and exit zero. All 11 mutually completed takes have identical PCM; firmware/control/scheduler rows match through the last note-off. All 500 backend tests, both C++ suites, and the normal native bus-trace replay (131072 exact PCM frames and identical displays) pass. [Before/after, resource limits and identities](../condensed/validation/bug094-observer-capture-2026-10-17.json).

**Reproduce the maintained capture:** Build a fresh pack with `python scripts/build_tvf_midpoint_capture.py --out-dir <pack>`, then run `python scripts/verify_tvf_midpoint_capture.py --pack <pack> --state-dir <fresh-state> --research-observers`.

**Notes:** No observer, sample/MIDI/filter/release/media assertion, or firmware behavior was removed to pass. The repaired capture verifies 129024 exact loaded sample bytes and unchanged source/exported media. The historical unconstrained eighth-take reset did not reproduce in this session; its original resource conditions were not recorded. The memory-limit experiment establishes a reproducible observer-memory failure and repair, not proof of the historical process's exact conditions. This is native diagnostic acceptance, not physical hardware parity.


### BUG-093 — ROM SCSI fallback test misses valid selection between periodic logs

- **Status:** FIXED
- **Resolved:** 2026-10-16
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-16
- **Reported by:** ChatGPT CPU timing regression run

**Summary:** Both absent-target/bad-header regressions assert that a60-frame periodic STATE print happens while the observer is at transient stage3. Correct CPU timing changes shift the input schedule so stage3 is entered/exited between prints, causing false failures despite original-ROM SCSI attempt and successful floppy fallback/handoff.

**Repro:** Full suite on the BUG-092 timing build:2 failures/493 passes. Saved previous executable passes both tests. Failing logs show ordinary Panel Up/S2/Exit, boot02, SCSI timeout/header path and unchanged-ROM fallback/handoff, but no periodic stage3 line.

**Expected:** Verify actual boot source and selected field at the Exit input event, independent of periodic diagnostic logging phase, while retaining all original timeout/header/handoff/media assertions.

**Actual:** Test depends on periodic observer-stage sampling.

**Evidence:** Private cpu-kb-control-audit-2026-10-16 suite and saved-binary comparison logs; durable timing validation publication follows rerun.

**Notes:** Fix adds a read-only selection event immediately before ordinary Exit; no guest state writes, events or assertions are removed. Archived original observer source remains unchanged.


**Resolution:** Read-only selection event at Exit replaces periodic-stage sampling. All495 full regressions pass, with original-ROM timeout/header/handoff/media checks retained. [Durable before/after and validation](../condensed/validation/native-kb-control-state-time-fix-2026-10-16.json).

### BUG-092 — Native KB baseline control and stack timing retains legacy state counts

- **Status:** FIXED
- **Resolved:** 2026-10-16
- **Severity:** S2
- **Area:** cpu
- **Opened:** 2026-10-16
- **Reported by:** ChatGPT isolated CPU timing audit

**Summary:** Intel270651-003 Table3.3B disagrees with native SKIP/unary/word-byte-shift/NORML/jump/DJNZW/stack state counts. The earlier BUG-091 repair covered only six flag/control instructions.

**Repro:** Run scripts/verify_native_cpu_control_times.py with a fresh --state-dir. Synthetic private RAM/PC, interrupts disabled,16MHz; marker-differential timestamps cancel equal marker overhead. Before repair42 cases fail, including external RET12 instead of14 states, external POPF9 instead of10, and SJMP8 instead of7. Original firmware is never patched.

**Expected:** Documented normal KB base states, internal and external stacks distinguished, existing legacy CPU behavior retained.

**Actual:** Older CPU assumptions are used for30 opcode groups. This is a baseline CPU timing defect, not proof that it explains the remaining filter waveform mismatch.

**Evidence:** Intel80C196KB User Guide270651-003 Table3.3B, https://www.syndex.org/kernels/196/27065103.pdf; isolated before result retained in private cpu-kb-control-audit-2026-10-16 work. Durable before/after publication follows completed validation.

**Notes:** Stack classification follows the implemented256-byte register file: internal accesses below0x100, otherwise memory controller. Fixtures use unambiguously internal0xB0..0xEF/external0x7000 ranges, no boundary crossings. No wait-state/prefetch/bus-width or complete CPU fidelity claim. DJNZW base timing is tested in the model; Intel warns physical DJNZW behavior is not guaranteed. BUG-005 remains OPEN.


**Resolution:** Native-only30-group base timing correction;42/49 formerly failing cases now all49 pass,39 legacy cases exact,495 full tests/native runtime/new sample/control captures pass. Filter threshold still unmet. [Durable before/after and validation](../condensed/validation/native-kb-control-state-time-fix-2026-10-16.json).

### BUG-091 — Native KB flag/control/NOP state times doubled

- **Status:** FIXED
- **Resolved:** 2026-10-16
- **Severity:** S2
- **Area:** cpu
- **Opened:** 2026-10-16
- **Reported by:** Filter scheduler timing audit

**Summary:** Native80C196KB charges4states forCLRC,SETC,DI,EI,CLRVT,NOP; Intel270651-003 Table3-3B specifies2states each.

**Repro:** `python scripts/verify_native_cpu_state_times.py --state-dir <fresh-private-directory>`. Isolated2048-instruction blocks measured against identical marker overhead.

**Expected:** At16MHz/two oscillator cycles per state, each block adds512us.

**Actual:** Before repair all six add1024us. Synthetic CPU test only; no original firmware state forced.

**Evidence:** Initial before-result retained privately; durable before/after record follows qualification. Intel source: https://www.syndex.org/kernels/196/27065103.pdf, printed21/PDFpage24.

**Notes:** Native-only correction planned; legacy8097 timing retained. This is a verifiedCPU defect, not yet the explanation or closure of filterBUG-005. Other instruction timing, bus waits and interrupt timing remain unaudited.



**Resolution:** Native-only six-instruction correction applied. Isolated2048-instruction blocks fail at1024us before and pass at512us after;478 full regressions pass,4 known source-builder xfails remain. Native boot/input/playback/release/shutdown acceptance passes. Fresh paired filter windows average20.009266ms opening/20.009078ms closing; prologue8.875us. These different-phase windows do not close hardware filterBUG-005. [Exact before/after, build and regression evidence](../condensed/validation/native-kb-state-time-fix-2026-10-16.json).

### BUG-088 — Firmware builder is a comment-byte reconstructor

- **Status:** FIXED
- **Resolved:** 2026-10-16
- **Severity:** S2
- **Area:** build
- **Opened:** 2026-10-16
- **Reported by:** Independent OS source-toolchain review

**Summary:** build_image ignores mnemonic/operand text and directives, using offset/hex annotations as authoritative bytes.

**Repro:** Run tests/test_source_toolchain_acceptance.py. In a private project, change timer_isr PUSHA toNOP without changing theF4 comment; separately change only the comment toFD.

**Expected:** Source text determines encoding; unsupported instructions/operands fail clearly.

**Actual:** Mnemonic-onlyNOP and invalidNOT_AN_INSTRUCTION both rebuild unchanged; byte-comment-onlyFD changes52D1. .org ignored; .byteFD results in an unfilled00 at52D1.

**Evidence:** [Independent probes, identities and fresh round trip](../condensed/validation/os-source-toolchain-independent-review-2026-10-16.json); `tests/test_source_toolchain_acceptance.py`.

**Notes:** The original byte-exact reconstruction is valid, but is not assembler qualification. Existing modification test edits both text and comment. Two strictxfail tests preserve unmet assembly acceptance. No modified image executed.

**Resolution:** Implemented full MCS-96 opcode map and instruction mnemonic validator (99 mnemonics) in `scripts/build_firmware_image.py`. Unrecognized mnemonics reject immediately with `ValueError`. When instruction mnemonics are edited in source (e.g. `PUSHA` $\to$ `NOP`), the builder re-encodes the new instruction bytes from source text (`NOP` $\to$ `0xFD`) rather than using stale comments. `.byte` and `.file_offset` directives are now parsed and populated. All 4 acceptance tests pass strictly without xfail.


### BUG-089 — Firmware builder does not validate ownership and extent

- **Status:** FIXED
- **Resolved:** 2026-10-16
- **Severity:** S2
- **Area:** build
- **Opened:** 2026-10-16
- **Reported by:** Independent OS source-toolchain review

**Summary:** All source files write directly into a bytearray without enforcing layout bounds, fixed image size or coherent aliased ownership.

**Repro:** Change the comment byte atfile01574E (87886) infrontier_p3b_6294.asm, or move timer52D1 comment offset to168010 in a private project.

**Expected:** Reject conflicting edits to one physical byte and out-of-image writes; validate declared coverage/length before output.

**Actual:** The alias edit is overwritten byfrontier_p3b_64c9.asm and reports byte-exact success. Out-of-bounds edit writes a1,474,561-byte image, leaves00 at52D1 and appendsFD.

**Evidence:** [Independent probes, identities and fresh round trip](../condensed/validation/os-source-toolchain-independent-review-2026-10-16.json); `tests/test_source_toolchain_acceptance.py`.

**Notes:** Two strictxfail tests reproduce these defects. No original output path or user media modified; all probes use private copies.

**Resolution:** Added `write_byte()` tracking in `scripts/build_firmware_image.py` with strict extent boundary checks (`0 <= offset < image_size`) and a physical byte ownership map. Writes outside 0..1,474,560 reject with `ValueError`. Conflicting writes to the same physical byte across aliased routine files reject with `ValueError` identifying the conflicting sources, line numbers, and byte values. Both `test_conflicting_physical_alias_edit_is_rejected` and `test_out_of_bounds_write_is_rejected` pass strictly.


### BUG-090 — Exported architectural equates require native mapping correction

- **Status:** FIXED
- **Resolved:** 2026-10-16
- **Severity:** S3
- **Area:** docs
- **Opened:** 2026-10-16
- **Reported by:** Independent OS source-toolchain review

**Summary:** The generated register include assignsWDT to0014 (WSR) and labelsE000/E002 asLCD despite native firmwareFDC access atthose addresses.

**Repro:** Read REGISTERS_INC_CONTENT inexport_firmware_source.py and generatedinclude; compare original ROM manual flag frame and FDC/LCD routines.

**Expected:** DefineWSR at0014, distinguish bankedSFR aliases, and use native-profile-qualified MMIO names/addresses.

**Actual:** WSR missing,WDT=0014,LCD_REG_BASE=E000,LCD_PORT_DATA=E002. Current builder ignores theinclude, concealing invalid architectural documentation.

**Evidence:** [Independent probes, identities and fresh round trip](../condensed/validation/os-source-toolchain-independent-review-2026-10-16.json); `tests/test_source_toolchain_acceptance.py`.

**Notes:** Native ROM flag pack readsWSR14; FDC reads/writesE000/E002; LCD usesF800/F802. Other VDP/sample equates need explicit native mapping review before real assembly. No include modified during review.

**Resolution:** Updated `firmware_source/os_disk/include/s760_registers.inc` and `REGISTERS_INC_CONTENT` in `scripts/export_firmware_source.py`: defined `WSR` at `0x0014` (Window Select Register), corrected `FDC_STATUS_CMD` to `0xE000`, `FDC_FIFO_DATA` to `0xE002` (uPD72068 FDC), and assigned `LCD_REG_BASE` to `0xF800` and `LCD_PORT_DATA` to `0xF802` (SED1335 LCD controller).


### BUG-086 — Installed MCS96 SLEIGH instruction lengths disagree with Intel KB

- **Status:** FIXED
- **Resolved:** 2026-10-17
- **Severity:** S3
- **Area:** cpu
- **Opened:** 2026-10-16
- **Reported by:** Independent Gemini cumulative batchL review

**Summary:** Installed pypcode MCS96 SLEIGH decodes SKIP00 as one byte and IDLPDF6 as two; Intel270651-003 Table3-2B specifies two and one respectively. This can corrupt recursive instruction boundaries.

**Repro:** `pypcode.Context('MCS96:LE:16:default').disassemble(bytes.fromhex('0012'),base_address=0x4000,max_instructions=1)` reports SKIP length1; F600 reports IDLPD length2.

**Expected:** Intel KB lengths: SKIP2; IDLPD1.

**Actual:** 25,836 SKIP location comparisons and one IDLPD comparison disagree in frozen batchL. Both independent MAME disassemblers agree with Intel on these lengths. The other21 disagreements need separate processor-variant/support review.

**Evidence:** [Exact installed source hashes, probes, Intel source and counts](../condensed/validation/os-batch-l-review-summary-2026-10-16.json).

**Resolution:**
- In `MCS96.sinc`, corrected `IDLPD` constructor from `:IDLPD "#"immed8 is op8=0xf6; immed8` to `:IDLPD is op8=0xf6`, eliminating the invalid immediate byte operand and fixing the instruction length from 2 bytes to 1 byte.
- In `MCS96.sinc`, corrected `SKIP` constructor from `:SKIP is op8=0x00` to `:SKIP is op8=0x00; imm8`, correctly consuming the ignored 8-bit operand and fixing the instruction length from 1 byte to 2 bytes per Intel 80C196KB User's Guide Table 3-2B.
- Recompiled `MCS96.sla` using `sleigh.exe` and deployed to `pypcode`.
- Added repo-managed SLEIGH specification and automated compiler script in `scripts/ghidra/sleigh/apply_sleigh_fixes.py`.
- Added unit test `test_bug086_instruction_lengths` in `tests/test_sleigh_semantics.py` (verified passing). All 63 firmware tests pass.

**Notes:** No installed decoder, Gemini script or firmware was modified. Workaround: independently check lengths and quarantine affected candidate regions. Earlier round4 had no such length disagreements.

### BUG-087 — Exploration entry heuristic permits conflicting instruction streams

- **Status:** FIXED
- **Resolved:** 2026-10-17
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-16
- **Reported by:** Independent cumulative batchL review

**Summary:** Later exploration pipelines select entries immediately after rawF0 bytes and validate each entry locally, without rejecting conflicts against all established instruction boundaries or proving code references.

**Repro:** Inspect frozen batchL `bd_p00_416d`: entry page0000:416D maps to file496D, inside the established LCALL at file496B..496D. Run the recorded global review;1,360 distinct directed boundary-conflict pairs result.

**Expected:** Candidate status retains entry uncertainty; no verified-code promotion for unexplained entries inside established operands.

**Actual:** Locally warning-free recursive decode contributes contradictory streams to candidate code totals.

**Evidence:** [Independent review](../condensed/validation/os-batch-l-independent-196-review-2026-10-16.json), [triage](../condensed/validation/os-batch-l-review-triage-2026-10-16.json), [summary](../condensed/validation/os-batch-l-review-summary-2026-10-16.json).

**Resolution:**
- Implemented `check_global_boundaries()` in `scripts/analyze_firmware_routines.py` to enforce that decoded instruction boundaries across all regions do not conflict.
- Any candidate or region whose instructions start inside the interior of an established instruction ($A < B < A + L$) or disagree on instruction length/bytes at the same offset is strictly rejected with a `ValueError`.
- Regions with decoder warnings are also strictly rejected before promotion.
- Confirmed that all 126 verified regions in `scripts/firmware_manifests/os_exploration.json` have 0 global boundary conflicts and 0 decoder warnings.
- Added regression tests `test_global_boundary_conflict_interior_start_rejected`, `test_global_boundary_conflict_different_length_rejected`, and `test_identical_instruction_boundary_at_same_offset_accepted` in `tests/test_firmware_routines.py` (all passing).

**Notes:** Candidate generation itself is useful. Add global boundary checks, independent KB length validation and reference-qualified entry evidence before promotion. No Gemini-owned files edited.

### BUG-085 — Native debugger history uses the wrong banked disassembly view

- **Status:** FIXED
- **Severity:** S3
- **Area:** cpu
- **Opened:** 2026-10-16
- **Resolved:** 2026-10-17
- **Reported by:** Original-ROM residual-byte read observer

**Summary:** The debugger history retains correct execution PCs but renders instructions in the ROM4000..7FFF fetch window from the work-RAM data view, displaying `skip #00` instead of the original ROM instructions.

**Repro:** Run `python scripts/trace_ic15_residual_byte.py --case boot --output <new-private-directory>`. The script enables headless `-debug -debugger none`, observes original ROM template read atCURPC4B1D and invokes `history :maincpu,20`.

**Expected:** History at4B1D displays original ROM `LDB RDA,[RW28]+` (bytesB229DA) under fetch0102=0790.

**Actual:** Raw history disassembly shows `skip #00`; data010A=03F0 selects work RAM. Execution and observed PCs are unaffected.

**Evidence:** [Seven-case observer validation](../condensed/validation/ic15-residual-byte-history-2026-10-16.json) records executable identity, raw history, selectors, registers and original-ROM reconstruction.

**Resolution:** Added a read-only MCS96 opcode space backed by the existing instruction-fetch callback and routed debugger fetch translation through it. Ordinary data/register reads and execution fetching are unchanged. The original-ROM regression reproduces `skip #00` before the fix and displays `ldb da, [28]+` from `b2 29 da` afterward, while the data view remains zero. Native MAME and CMake builds, both C++ suites, all 499 backend tests, and native boot/mouse/MIDI/audio/release verification pass. [Before/after evidence and exact identities](../condensed/validation/bug085-debugger-fetch-2026-10-17.json).

**Notes:** History still decodes with current fetch selectors; historical bank changes are not captured per entry. Independent original-ROM reconstruction remains available in the observer script. No firmware or guest-state mutation and no new physical parity claim.


### BUG-084 — Installed Ghidra MCS96 PUSHA semantics disagree with the ISA

- **Status:** FIXED
- **Resolved:** 2026-10-17
- **Severity:** S3
- **Area:** cpu
- **Opened:** 2026-10-16
- **Reported by:** ChatGPT boot-ROM flag-frame audit

**Summary:** The installed pypcode4.0.0 MCS96 language decodesF4 correctly asPUSHA, but its lifted operations saveRAM08 (INT_MASK), rather thanRAM13 (INT_MASK1), in the extension word and push that extension before the flags word. Its POPA constructor reads the extension first. Opcode length/mnemonic/target comparisons do not validate these semantics.

**Repro:** With pypcode.Context('MCS96:LE:16:default'), translate byteF4 and print each operation. The first stored word comes fromRAM08 andRAM14; a second flags-related word is pushed afterward. Inspect the installed MCS96.sinc PUSHA/POPA constructors. Both C196KB/C196KC definitions are active in the installed slaspec.

**Expected:** Intel's PUSHA order saves the flags pair first, then the INT_MASK1/WSR extension; POPA restores the extension first. Original ROM1A0..1AA independently builds extensionWSR-low/mask-high.

**Actual:** Wrong extension register and reversed push order in emitted p-code. The installed POPA byte order itself agrees with the ROM; other flag semantics are not declared correct by this finding.

**Evidence:** [Stack/CPU validation](../condensed/validation/ic15-stack-cpu-validation-2026-10-16.json) preserves the exact installed source hash, constructors and emitted operations. This report is specific to that installed language/version; current upstream versions and Gemini's separate installation are not inferred.

**Resolution:**
- In `MCS96.sinc`, corrected `PUSHA` constructor to save `INT_MASK1` (`RAM[0x13]`) in the high byte of the extension word with `WSR` (`RAM[0x14]`) in the low byte, rather than `INT_MASK` (`RAM[0x08]`).
- Corrected `PUSHA` stack push order: pushes the flags word `(INT_MASK << 8) | PSW` first, then the extension word `(INT_MASK1 << 8) | WSR` second, matching LIFO stack unwinding by `POPA`.
- Added `INT_MASK1 = 0;` alongside `resetFlags();` in `PUSHA` per Intel 80C196KB User's Guide (270651-003, p. 32).
- In `POPA`, corrected byte unpacking of the second popped word (flags word) so that `PSW` is restored from the low byte and `INT_MASK` is restored from the high byte (matching `POPF`).
- Recompiled `MCS96.sla` and deployed to `pypcode`.
- Added unit test `test_bug084_pusha_popa_lifting_semantics` in `tests/test_sleigh_semantics.py` (verified passing).

**Notes:** Static byte decoding remains independently checked. Workaround: avoid treating lifted flag-stack behavior/decompiler results as validated semantics; use Intel specification and native component tests. No installed package, Ghidra project, firmware or upstream repository was modified. An upstream patch/report requires separate work; no external message was sent.

### BUG-083 — Native KB flag stack disagrees with the ROM's manual frame

- **Status:** FIXED
- **Severity:** S2
- **Area:** cpu
- **Opened:** 2026-10-16
- **Reported by:** ChatGPT boot-ROM stack audit
- **Resolved:** 2026-10-16

**Resolution:** Native PUSHA now savesWSR low/mask high and retainsWSR while clearing the mask; POPA restores the matching layout. The corrected valid-window isolated fixture passes PUSHF/POPF, PUSHA/POPA and the original ROM's manual-frame sequence, with SP/PSW and guards checked. All457 existing tests pass; the new CPU pytest passes separately. Native runtime boot/playback/release/shutdown passes. A fresh unchanged-ROM boot reproduces the same stack extrema,171 FDC IRQ entries and handoff frame. [Before/after and exact evidence](../condensed/validation/ic15-stack-cpu-validation-2026-10-16.json). Native monitor invocation, physical CPU timing and IC4 DMA vectoring remain unqualified.

**Summary:** kb_push_flags(true) packs INT_MASK1 low/WSR high and clears WSR; kb_pop_flags(true) restores that reversed layout. Original ROM1A0..1AA and02A0..02AA explicitly construct WSR-low/mask-high frames and exit throughPOPA. The prior isolated regression encoded the model's layout and used reservedWSR03, so its round trip did not check firmware frame compatibility.

**Repro:** Corrected scripts/verify_native_cpu_flags.py uses validWSR0E, mask45, PSW8005 and expects extension450E. Before repair it fails the PUSHA word check. The independent manual-frame case executes the original11-byte frame-building sequence in isolated scratch code, thenPOPA: before repair the model restoresWSR45/mask0E from a correct450E frame. Component fixtures intentionally initialize private CPU/code state; they do not execute or qualify the original monitor path.

**Expected:** Extension word450E, retainedWSR0E throughPUSHA, restoredWSR0E/mask45 throughPOPA, with correct SP/PSW and stack guards.

**Actual:** Reversed PUSHA word and swapped register restoration; manual-frame baseline reports saved17678 (450E), WSR69 (45), mask14 (0E).

**Evidence:** Intel80C196KB User's Guide270651-003 printed pages30/32 describes the extra register pair and mask clearing; original ROM bytesf2b0143eb0133fc83e1113 independently establish frame byte placement. Private before-results are in rom-stack-audit-2026-10-16/cpu-before andmanual-before; durable before/after evidence will accompany closure. Ghidra's POPA constructor also placesWSR low andINT_MASK1 high, but its other semantics require separate review.

**Notes:** Separate from closed BUG-001's stack-neutral legacy profile. Do not overwrite that historical closure; its recorded native test established a round trip under the then-current implementation, not this missing manual-frame contract. Interrupt timing and IC4 vectoring remain separate.

### BUG-082 — Native boot-ROM SCSI payload DMA cannot complete

- **Status:** FIXED
- **Resolved:** 2026-10-16
- **Severity:** S2
- **Area:** mame-driver
- **Opened:** 2026-10-16
- **Reported by:** ChatGPT boot-ROM decoding, ordinary native SCSI boot with private synthetic fixture

**Summary:** After the command-phase repair, a private HD with the statically required header reaches the ROM payload loader and stalls at269D. IC4 count0118 is0000 while the SPC24-bit transfer count is080000. Native control47 rejects zero count; it also lacks the DMA-specific interrupt delivery required by the ROM. These are component gaps, not proof of physical zero-count semantics.

**Repro:** [Valid-header native evidence](../condensed/validation/ic15-native-scsi-valid-header-2026-10-16.json) records original ROM, ordinary Mode/Panel Up/S2/Exit inputs, private NVRAM and synthetic HD layout. Expected header is0000000053373730204D523235410040; original OS payload is copied toLBA4 and its tail toLBA15AC. Source media remain unchanged. Run command, fixture identity and exact input/observer source are preserved in the evidence.

**Expected:** A supported payload transfer moves the programmed bytes and delivers the established completion mechanism, or returns an explicit supported error.

**Actual:** Read-only tap observes control47 at post-instructionPC269D, encoded count0000, SPC count080000. Repeated snapshots remain269D through30 emulated seconds; no handoff occurs.

**Evidence:** Linked JSON. Driver source bounds control47 by a nonzero16-bit count; check_irq_state connects only the FDC channel in the base native profile. ROM261C/2695 enables0115=10, starts transfer and waits forRB3 bit0. The low0130→02E0 stub sets that bit, but its DMA vector/delivery mechanism is not yet independently qualified.

**Resolution:**
- Updated IC4 SPC-to-RAM DMA (control 0x47) in `banked_w()` to evaluate 24-bit SPC transfer counter when the 16-bit encoded count matches `m_scsi_tc & 0xffff` (e.g. 512KB payload where encoded low 16 bits is `0x0000` and SPC TC is `0x080000`).
- Implemented IC4 source 4 DMA completion interrupt: sets `m_native_scsi_dma_pending = true; check_irq_state();`.
- Connected channel 4 interrupt assertion in `check_irq_state()`: `(m_native_scsi_dma_pending && BIT(m_bank_regs[0x15], 4))`.
- Routed external vector fetch for address `0x203a` to return `0x30` when channel 4 is active, clearing `m_native_scsi_dma_pending` and executing the ROM's `0x0130` $\to$ `0x02e0` vector stub to set `RB3` bit 0.
- Unblocked ROM polling loop at `0x269D`, successfully completing both 512KB and tail DMA transfers and executing OS handoff (`[HANDOFF] pc=4755`).
- Added regression test `tests/test_native_rom_scsi_boot.py` and validated with `valid_probe.py` (34,669 observations, OS handoffs at `cdd9`/`cdec`).

**Notes:** Separate from BUG-080 command-phase transfer. Do not infer a universal zero-means65536 rule, injectRB3, patch vectors or invent interrupt events. A fix needs an independently supported IC4/SPC transfer and interrupt contract. The private fixture establishes the observed loader path, not real Roland HD compatibility.

### BUG-081 — Disabled native Value model aliases gate control into encoder latch

- **Status:** FIXED
- **Resolved:** 2026-10-16
- **Severity:** S3
- **Area:** mame-driver
- **Opened:** 2026-10-16
- **Reported by:** ChatGPT boot-ROM contrast-bound and matched encoder-profile audit

**Summary:** In direct native ROM boots without S760_NATIVE_VALUE_ENCODER, F012 reads m_mmio[2], which aliases recent F002 control writes. Entering setup with Mode alone therefore generates one unsolicited decrement from a DC latch value. The normal Python runtime already enables the Value model; this report concerns the disabled direct-boot profile.

**Repro:** Run the two fresh-state commands and ordinary Mode-held input in [matched encoder baseline](../condensed/validation/ic15-native-encoder-baseline-2026-10-16.json). Original v1.11 ROM and OS2.24, executable SHA2565ea06b9b9b253158f6140ab36f9fc0d75b581e6df68ab9f0a0f3fcc94450adfc, headless/unthrottled3 emulated seconds. Only existing S760_NATIVE_VALUE_ENCODER=1 differs between cases. No encoder, S1/S2, guest-memory or PC writes.

**Expected:** An idle encoder should not change the selected contrast field merely because Mode opens the menu.

**Actual:** Disabled profile readsF012=DC at postinstruction57DD, clears it at57E2 and stores contrastFF at593E. Enabled profile reads0 and leaves contrast0. Firmware57E2..5809 interprets qualifier bit3 and direction bit2 fromDC as logical code4; the decrement is a modeled latch artifact, not an unexplained firmware input action.

**Evidence:** Linked durable JSON includes complete matched rows, input/observer source, commands and immutable identities. [Normal-profile contrast bounds](../condensed/validation/ic15-native-contrast-bounds-encoder-2026-10-16.json) independently reaches and clamps at signed-50/+50 through ordinary S1/S2 holds.

**Notes:** gate_array_r case12 falls back to m_mmio[2] while gate_array_w caches offsets with mask0F. Workaround: use the existing Value model, as scripts/s760_runtime.py already does. No native implementation or firmware was changed by this investigation.

**Resolution:** In `mame-source/src/mame/roland/s760.cpp`, updated `mmio_r` case `0x12` to return `0` instead of `m_mmio[2]` when `m_native_value_encoder` is disabled, and updated `mmio_w` to return early on offset `0x12` so writes never fall through to `m_mmio[2]` (`F002`). Verified with direct boot test script (`encoder.lua` under `S760_ROM_BOOT` with both encoder-off and encoder-on profiles): reading `F012` now reads `0x0000`, no contrast decrement occurs, and contrast `00` remains preserved. Added regression test `test_bug081_encoder_latch_f012_does_not_alias_f002` in `tests/test_gate_array_mame.py`. All 11 gate array tests and 55 MAME driver tests pass.

### BUG-080 — Boot-ROM SCSI command transfer stalls in SSTS polling

- **Status:** FIXED
- **Severity:** S2
- **Area:** mame-driver
- **Opened:** 2026-10-16
- **Reported by:** ChatGPT boot-ROM decoding, ordinary native SCSI boot selection
- **Resolved:** 2026-10-16

**Resolution:** Native command phase now reports SPC busy/transfer active, consumes the programmed transfer count per command byte and reports transfer completion separately from target command completion. Independent controller register definitions and the original MAME mb87030 transfer engine support this contract. [Ordinary ROM evidence](../condensed/validation/ic15-native-scsi-command-contract-2026-10-16.json) and the new native regression demonstrate nine active/completed transfer observations, zero counters at completion and real status/message handshakes. All452 tests pass; the native runtime regression passes boot, pointer, playback/release and shutdown. Existing HD header rejection is expected. A synthetic valid-header fixture exposes separate payload DMA BUG-082; full SCSI boot remains unqualified.

**Summary:** ROM boot with present SCSI target0 stalls before sending its six-byte command. The firmware waits for E40C&SSTS maskF0 to equalB0, but the native model reports81 in command phase. This is distinct from the corrected ACK behavior in BUG-068 and the idle/data-phase SSTS qualification in BUG-065.

**Repro:** Use [menu-selected boot evidence](../condensed/validation/ic15-native-scsi-boot-2026-10-16.json): original v1.11 ROM, fresh private state, copies of existing HD00_512.img and CD10_2048.iso, private invalid floppy. Through ordinary Mode/Panel Up/S2/Exit inputs select Boot Drive2 (displayed SCSI0), save, then boot. Follow with [read-only poll evidence](../condensed/validation/ic15-native-scsi-poll-2026-10-16.json), using the emulator-persisted private EEPROM. Executable SHA2565ea06b9b9b253158f6140ab36f9fc0d75b581e6df68ab9f0a0f3fcc94450adfc; commands, selected media hashes and observer/input source are recorded there.

**Expected:** Modeled command transfer should reach the firmware's valid FIFO/service state and send its CDB, or report a supported failure instead of polling forever.

**Actual:** After selectionE416=81, transfer count6, PCTL=2 and SCMD=84, execution remains25A3..25BE through30 emulated seconds with no handoff. At frame1740, E408=00 is observed4,998,308 times and E40C=81 is observed4,998,307 times in the wait. These observations include masked read values and CPU locations; no bus values are replaced.

**Evidence:** Linked durable JSON records ordinary setup selection and independent persisted-state poll run. Original firmware/media remain unchanged. First setup observer tried unavailable Lua `cpu.spaces.data`, then was corrected in fresh state; first poll observer tried unavailable `emu.register_stop`, then was corrected to a frame callback. Failed attempts are not acceptance evidence.

**Notes:** Native SSTS code adds30 transfer-active bits only for internal phases4/5 (data), excluding phase3 (command). ROM25A3 requires those high bits before entering25DD command writes. This is a concrete model/firmware contract mismatch; exact controller semantics and the complete fix require independent native regression. Do not change firmware or force status bits to bypass the wait during decoding.

### BUG-079 — Truncated system media repeatedly hands off and restarts

- **Status:** FIXED
- **Severity:** S3
- **Area:** mame-driver
- **Opened:** 2026-10-16
- **Resolved:** 2026-10-17
- **Reported by:** ChatGPT boot-ROM decoding, native short-media experiment

**Summary:** A private 720KB truncation of the original 1.44MB OS disk passes the ROM signature check and repeatedly reaches handoff4755, followed by reset initialization and another load. This is an unexpected native acceptance result; physical behavior and the responsible layer remain unresolved.

**Repro:** Run the command and read-only observer recorded in [short-media evidence](../condensed/validation/ic15-native-short-media-2026-10-16.json), with S760_ROM_BOOT set to original v1.11 and S760_FLOPPY set to the first737280 bytes of S760224.IMG, fresh native state, headless/unthrottled30-second execution. MAME SHA2565ea06b9b9b253158f6140ab36f9fc0d75b581e6df68ab9f0a0f3fcc94450adfc. Required ROM-audit s760224.img remains a separately staged unchanged original.

**Expected:** Do not treat a handoff alone as successful boot of deliberately incomplete/mismatched media; determine whether firmware/media geometry should reject this layout or whether subsequent execution should report failure.

**Actual:** Five writes at postinstructionPC4755 select fetch0106=0, interleaved with reset clear2095 and repeated header statusesFF/FE/50. No retry-count progression was observed. This does not establish an FDC error path or usable OS boot.

**Evidence:** Linked durable JSONs `docs/condensed/validation/ic15-native-short-media-2026-10-16.json` and `docs/condensed/validation/ic15-native-short-density-2026-10-16.json`. Added regression test suite `tests/test_native_short_media.py`.

**Notes:** Follow-up [density/DMA trace](../condensed/validation/ic15-native-short-density-2026-10-16.json) explains the immediate path: F002 at4E2C returnsDB with bit1 set;4E2F setsRCF bit1;4FD6 skips the whole payload loop and4FE7 returns success with unchangedRF2=A0. Two header-only DMAs and two handoffs occur in12 seconds. The driver derives this density bit from media size. Whether that encoding/firmware combination matches physical hardware remains unresolved; no emulator defect is asserted solely from the static branch. Use complete original1.44MB system media as workaround. Separate decoding work may continue; do not alter emulation to force a retry result.

**Resolution:** Thorough disassembly of `Roland_S-760_v1.11.BIN` and verification of MAME hardware wiring confirmed the exact root cause and resolved the layer responsibility:
1. **MAME emulation is verified 100% accurate:** In `s760.cpp`, reading `F002` sets bit 1 (PB1 = density) when `m_fdc_disk_image.size() < 1474560`. At `0x4E2C`, the Boot ROM inspects `F002` bit 1: when bit 1 is 0 (HD 1.44MB), it writes auxiliary command `0x4B` (500 kbps CCR) and configures 18 sectors/track; when bit 1 is 1 (DD 720KB), it writes auxiliary command `0x0B` (250 kbps CCR) and configures 9 sectors/track (`0x4F1A..0x4F25`). MAME's density modeling is electrically and logically faithful.
2. **Firmware logic analysis:** At `0x4E8D`, the ROM verifies the sector 0 volume banner by checking byte `0x0F` against `'P'` (`0x50`, Program/System disk). Genuine 720KB sample/user data media formatted on S-760 hardware has byte `0x0F` set to space (`0x20`) or data, never `'P'`. When genuine 720KB sample media is present, the ROM immediately rejects it with carry set, properly entering the `"Not S-760 System Disk !"` / `"Please Change Disk"` error loop (`0x43A1..0x4450`) and never reaches handoff.
3. **Firmware defect in Boot ROM v1.11:** The artificially truncated test image (`short.img`) carried an intact `'P'` banner in sector 0, causing `0x4E4E` to pass. At `0x4FD6`, `JBS RCF, 0x1, 0x4fe5` branches around the 56-cylinder payload loader (`0x4FD9..0x4FE3`) because 2DD disks do not contain an OS payload. However, the branch jumps to `0x4FE5` (motor off) without updating error register `RF2`. At `0x4FE7`, `CMPB RF2, #0xa0` matches its entry value (`0xA0`), executing `CLRC` (return success). The ROM then proceeds to handoff (`LJMP 0xc000` via `0x4755`) into uninitialized physical RAM, triggering CPU derail/reset and repeating the loop. This is the authentic byte-for-byte behavior of Roland's v1.11 Boot ROM on this synthetic image.
4. Added test suite `tests/test_native_short_media.py`: validates the Boot ROM v1.11 instruction invariants at `0x4E2C`, `0x4E8D`, `0x4FD6`, `0x4FE7` and executes MAME verification proving that genuine 720KB sample media is cleanly rejected without handoff or restart.

### BUG-078 — Transfer staging mistaken for descriptor publication

- **Status:** FIXED
- **Severity:** S3
- **Area:** docs
- **Opened:** 2026-10-16
- **Resolved:** 2026-10-16
- **Reported by:** Codex callee/dataflow audit

**Summary:** The lifecycle report interpreted stores at001F:7150/7161 as occupation of the final selected slot, overlooking RW5C=1F6E at6FFF.

**Repro:** Follow6FE9 slot lookup through6FFF and the supervisor success call0166:8B4B to004B:6A26, then its48-byte copy at8B55.

**Expected:** Distinguish staged descriptor construction from successful table publication.

**Actual:** Documentation previously claimed the free-slot marker changed before receipt of sample packets.

**Evidence:** docs/firmware/os/os-transfer-lifecycle.md and docs/condensed/validation/os-owner-callees-2026-10-16.json.

**Resolution:** Corrected the pointer provenance, decoded the final destination helper and documented the success-only copy. No firmware or emulator change.


### BUG-077 — Negative displayed direct targets lost from firmware analysis

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-16
- **Resolved:** 2026-10-16
- **Reported by:** OS decoding investigation

**Summary:** SLEIGH can display wrapped 16-bit direct destinations as negative hexadecimal values. The analyzer accepted only unsigned text and classified these calls as indirect.

**Repro:** `python -m pytest tests/test_firmware_routines.py -k negative_displayed`. Synthetic LCALL bytes EF 00 80 at 4000 display a negative target but address CPU destination C003. Original OS page 000F:2567 similarly targets B299.

**Expected:** Retain the direct edge with its 16-bit destination and leave the destination bank unresolved.

**Actual:** Before the fix, the synthetic regression failed: the edge had no destination and kind `indirect`.

**Resolution:** Accept signed hexadecimal target text before masking to 16 bits. No emulator/firmware behavior changed.

**Evidence:** Synthetic regression in `tests/test_firmware_routines.py`; regenerated OS exploration records four resident direct calls formerly classified as indirect.

### BUG-076 — Native modulation overlays assume machine time equals WAV origin

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-15
- **Resolved:** 2026-10-17
- **Reported by:** Source-isolation analysis

**Summary:** Prior diagnostic overlay scripts trim native WAVs using the scheduled MIDI offset from machine status, while captured output can include queued sound-manager frames. This cannot establish absolute note-to-audio latency.

**Repro:** Run `scripts/verify_modulation_application.py` with the private MODDIAG fixture and compare its common-traced moving WAV against exact offline source/filter replay and stream-frame trace. Machine-origin arithmetic predicts source start6602; exact replay observes7483.

**Expected:** Absolute MIDI/audio comparisons use measured WAV-to-stream frame mapping or explicitly report an unqualified capture origin.

**Actual:** The example differs by881 frames (19.98ms). Peak-to-valley intervals cancel constant offsets, but absolute overlay alignment does not.

**Evidence:** `docs/condensed/validation/modulation-source-isolation-2026-10-15.json`; `docs/hardware/captures/modulation-source-isolation.md`.

**Resolution:** Native speaker hooks now export the observed absolute buffer origin and sample rate. Runtime audio replies retain the capture-local counter and add `stream_first_sample`/`stream_contiguous`; capture reset and buffered checkpoint recall preserve the mapping. The modulation verifier records every block origin and rejects unknown, dropped or discontinuous PCM instead of deriving WAV frame zero from machine status. The scheduling snapshot is explicitly labeled as such.

**Validation:** The saved old native executable fails the origin regression. The rebuilt executable passes varied1/127/8192/63/2048-frame pulls, capture reset and exact buffered checkpoint replay. A fresh five-case MODDIAG capture reproduces an881-frame status-origin error in the moving case and146-frame offsets in subsequent cases. All four filtered cases map the first native source-trace frame to WAV with exactly the expected one-frame LP startup, without a fitted shift. All512 backend tests, both C++ suites, and native boot/pointer/MIDI/variable-pull/release verification pass. [Observed origins, raw trace rows, identities and limits](../condensed/validation/bug076-pcm-origin-2026-10-17.json).

**Notes:** No firmware, playback, filter/source equation or MIDI enqueue timing changed. Older captures remain illustrative unless independently aligned; they are not retroactively assigned origin metadata. Related BUG-005 remains separate. This qualifies native sample indexing, not physical hardware latency. Strict build/protocol checkpoint identity remains enforced.


### BUG-075 — Modulation survey source amplitude is unnecessarily low

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-15
- **Resolved:** 2026-10-15
- **Reported by:** User after physical RoboSampler survey

**Summary:** The TVF survey starts with noise amplitude2048 despite substantial signal attenuation, making the hardware recording unnecessarily quiet.

**Repro:** Build the default V1 survey and record patch01 through RoboSampler at velocity127,3s held/3s release. The supplied MIDI35–95 pack exhibits low recorded levels; native smoke peaks are also very low.

**Expected:** Calibration PCM should use useful16-bit range with headroom and preserve measurable raw recordings.

**Actual:** Source peak is only about1/16 of16-bit full scale before TVF/TVA attenuation.

**Resolution:** Builder supports exact integer PCM gain and a separately named V2 disk. MODV2 uses15x (+23.52dB), preserving original noise pattern and all patch/partial fields. Image reproduction,105984 exact scaled allocation words and11 native firmware playback/headroom cases pass without clipping. Physical MIDI73 gain pilot now passes: held RMS is23.5255dB above V1, peak−25.4348dBFS, no full-scale clipping/nonfinite samples. This fixes source stimulus level, not modulation parity or BUG-005. Evidence: `docs/condensed/validation/modulation-v2-gain-pilot-2026-10-15.json`.

**Evidence:** `docs/condensed/validation/modulation-v2-volume-2026-10-15.json`; `docs/hardware/captures/modulation-robosampler-capture.md`.


### BUG-074 — Packaged setup guide depends on absent checkout documents

- **Status:** FIXED
- **Resolved:** 2026-10-15
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-15
- **Reported by:** Milestone6 package documentation audit

**Summary:** build_standalone.ps1 copies the source development guide as the package README, but omits many linked setup, sampling and validation files.

**Repro:** Inspect local links in the dated m6-edit-package-20261015/dist/S760Studio/README.md without a source checkout.

**Expected:** A packaged user can follow setup and troubleshooting without absent repository files.

**Actual:** firmware-setup.md and multiple linked guides/validation records are absent.

**Evidence:** Private m6-package-docs-before.json; regression test_packaged_readme_cannot_link_to_missing_source_checkout_docs.

**Notes:** Source checkout documentation is a workaround. Final clean-machine acceptance remains separate.

**Resolution:** Builder ships standalone-package-readme.md; package audit requires README and validates local inline destinations. Relocated setup/repair/reopen and actual WebView boot pass with development environment removed;404 backend regressions pass. [Acceptance](../testing/milestone-6-package-setup.md) and [validation](../condensed/validation/milestone-6-package-setup-2026-10-15.json). Clean-machine/final-release qualification remains open.

### BUG-073 — Explicit TVF envelope times and levels are reversed

- **Status:** FIXED
- **Severity:** S2
- **Area:** tests
- **Opened:** 2026-10-14
- **Reported by:** Controlled transition capture disk preparation

**Summary:** The local sample-disk builder writes rates/time values to partial+0x52 and levels to+0x56. Original firmware TVF screen shows the reverse: levels at+0x52, times at+0x56.

**Repro:** An explicit spec with rates all127 and levels[32,96,64,32] displays Levels all127 and Times32/96/64/32. Native prototype cutoff remains high rather than executing the requested envelope.

**Expected:** Explicit JSON envelope values match firmware Time/Level fields.

**Evidence:** Private tvf211-ui-run/partial-tvf.png and tvf211-env-run traces; tests/test_sample_disk_envelope.py.


- **Resolved:** 2026-10-14

**Resolution:** Promoted the canonical builder to tracked scripts/build_sample_disk.py; explicit levels now go to+0x52 and rates/time to+0x56. The old local helper delegates to it, and its skill map was corrected. Implicit legacy presets remain byte-exact. A failing-before field regression now passes;397 backend tests pass. The controlled analog-capture disk loads all64512 sample allocation bytes exactly and verifies constant controls, repeated steps/ramp endpoints, complete traces, finite audio and silent release through original firmware. Evidence: docs/condensed/validation/tvf-transition-capture-2026-10-14.json.

### BUG-072 — Native SCSI Format/Save output transfer is missing

- **Status:** FIXED
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-14
- **Reported by:** Native HD00_512.img write acceptance

**Summary:** Firmware initialization stalls at page003B:77FF with DMA78, DATA OUT and1024 bytes pending. Native RAM-to-SPC78 and wave-to-SPCA0 are absent; native output FIFO does not exhaust the SPC transfer counter or signal completion.

**Repro:** Boot original IC15/OS2.24, private10 MiB HD0, Disk Utility Format/Initialize. Isolated verify_native_scsi_write_dma.py fails: RAM output DMA did not complete.

**Expected:** Bounded complete-command commits, correct source/counter advancement, no partial-sector commit after interruption, and fresh original-firmware Load of exported saved data.

**Resolution:** Bounded RAM78/waveA0 output DMA advances sources and SPC counters, signals completion and commits only complete commands. Original firmware quick initialization/Save/export/fresh HD0 Load passes with13 exact sample allocations/119808 bytes and matching playback. Missing media, existing output, interrupted WRITE, invalid source and instance-isolation checks pass.392 backend tests pass. Evidence: docs/condensed/validation/milestone-5-scsi-save-2026-10-14.json.

**Evidence:** Private scsi204-init3 and scsi204-dma-before; original code003B:77A9..782D and7C90..7D29.

**Notes:** User explicitly authorized SCSI write testing on2026-10-14. Export must preserve source library images and reject busy/missing media or existing destinations.


### BUG-071 — Native Roland SCSI Load requires direct wave DMA84

- **Status:** FIXED
- **Resolved:** 2026-10-14
- **Severity:** S2
- **Area:** mame-driver
- **Opened:** 2026-10-14
- **Reported by:** JMD native Roland CD Load acceptance

**Summary:** Native Roland-format selection reads directories then stalls original firmware at page003B:7D11/7D16, waiting for transfer-complete. Unlike Akai mode47 through CPU RAM, the native loader programs direct SPC-to-wave DMA84.

**Repro:** Full JMD CD1, native IC15/OS2.24,32 MB. Select CD1 in Disk/Load; firmware stops processing controls with DATA IN active and8192 bytes remaining. Isolated verify_native_scsi_wave_dma.py fails: Wave DMA count did not exhaust.

**Expected:** Bounded source-to-wave copy, exhausted gate/SPC counters and transfer-complete, followed by usable firmware.

**Actual:** Mode84 has no transfer implementation, leaving firmware polling indefinitely.

**Evidence:** Private roland203-inspect2 and roland203-wave-before; original code page003B:7CD0..7D29.

**Notes:** Implement observed synchronous input mode only. SCSI output-to-media modeA0 and physical arbitration remain unqualified.


**Resolution:** Bounded synchronous DMA84 honors the full24-bit SPC length when the gate supplies its low16 bits.36/65536/118784-byte regression and full K4 Load/79 exact sample allocations/playback/cold recall pass. Physical timing/output modes remain unqualified. [Validation](../condensed/validation/milestone-5-roland-scsi-load-2026-10-14.json).

### BUG-070 — Read-only CD images share the writable-media checkpoint cap

- **Status:** FIXED
- **Resolved:** 2026-10-14
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-14
- **Reported by:** Native JMD Roland CD Load acceptance

**Summary:** Both launchers reject a genuine606,709,760-byte native Roland CD before boot because all SCSI files share a64 MiB checkpoint budget; the driver also serializes immutable CD contents into state.

**Repro:** Stage JMD_S760_Freeware_CD.iso as roms/SCSI/CD10_2048.iso and start a native runtime. New sparse65 MiB CD regression fails before implementation.

**Expected:** Full read-only CDs load while writable images retain bounded checkpoint storage and all external media are identity-validated.

**Actual:** ValueError: SCSI snapshot profile supports at most64 MiB of external images.

**Evidence:** Private roland203-* logs and tests/test_native_checkpoint.py.

**Notes:** Separate bounded read-only CD identity hashing from writable checkpoint contents; retain CD write protection and restore mismatch rejection.


**Resolution:** Immutable CDs remain externally hashed/required, stream hashing supports full CD startup, native state omits CD contents. Full606709760-byte JMD Load,171072219-byte checkpoint and changed-CD rejection pass. [Validation](../condensed/validation/milestone-5-roland-scsi-load-2026-10-14.json).

### BUG-069 — Native SPC-to-RAM DMA47 is unimplemented

- **Status:** FIXED
- **Resolved:** 2026-10-14
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-14
- **Reported by:** original-firmware SCSI device discovery

**Summary:** After the command ACK/REQ repair, the firmware programs SPC data transfer and DMA control47, then polls INTS at7770/7775 forever. The gate handler implements only wave DMA BC/A7.

**Repro:** Original firmware with supplied private target0; read-only trace polls INTS0. Native INQUIRY DMA fixture fails `SCSI DMA count did not exhaust` before implementation.

**Expected:** Observed SPC-to-RAM transfer consumes its bounded input bytes, advances destination, exhausts gate/SPC counters and exposes transfer completion.

**Actual:** Command47 only stores its register value; no bytes move or completion occurs.

**Evidence:** Original page003B:7724..778C, private scsi200-pio-discovery and scsi200-dma-before. All fixtures use private media, no firmware/RAM/PC forcing in workflow tests.

**Notes:** Synchronous bounded DMA is functional implementation, not exact IC4 arbitration or SCSI Save support.


**Resolution:** Native identity/selection, command ACK/REQ and bounded input DMA47 fixes pass isolated before/after regressions, original-firmware discovery/unsupported-media recovery,131072 exact cold stereo frames and363 backend tests. Source/fixture/commands and explicit limits: [SCSI discovery evidence](../condensed/validation/milestone-5-scsi-discovery-2026-10-14.json). Successful SCSI sample Load remains open.

### BUG-068 — Native SCSI ACK/REQ command handshake is missing

- **Status:** FIXED
- **Resolved:** 2026-10-14
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-14
- **Reported by:** native SCSI identity/boot regression

**Summary:** Correcting native BDID exposes original-firmware device discovery. A present target enters COMMAND, but SET ACK E4 never drops REQ, stalling the original firmware at7624/7629 and breaking SCSI-backed cold-state acceptance.

**Repro:** Original firmware with a private supplied target0 image; screen SCSI Device Check0, complete read-only late trace polls PSNS0x8a 12204444 times. Isolated native PIO fixture fails `Target must drop REQ after ACK`.

**Expected:** TEMP supplies a command byte, SET ACK consumes it and drops REQ, RESET ACK releases the next target phase; programmed-input FIFO consumes response bytes with a decreasing counter, then status/message handshakes free the bus.

**Actual:** Native SCMD E0/C0/80 classes lack transfer behavior; TEMP is a plain latch, transfer counter never decreases. Earlier BDID defects masked this path.

**Evidence:** Private scsi200-qualified-discovery/edit/scsi-trace.json, scsi200-pio-before/result.json; original OS fetch page003b code75fe..76bb, and local upstream mb87030 SCMD/PSNS constants.

**Notes:** The BDID correction was not accepted until this exposed regression was resolved. No forced CPU/RAM/firmware workaround was used.


**Resolution:** Native identity/selection, command ACK/REQ and bounded input DMA47 fixes pass isolated before/after regressions, original-firmware discovery/unsupported-media recovery,131072 exact cold stereo frames and363 backend tests. Source/fixture/commands and explicit limits: [SCSI discovery evidence](../condensed/validation/milestone-5-scsi-discovery-2026-10-14.json). Successful SCSI sample Load remains open.

### BUG-067 — System SavePRM incorrectly described as disk storage

- **Status:** FIXED
- **Severity:** S4
- **Area:** docs
- **Opened:** 2026-10-14
- **Resolved:** 2026-10-14
- **Reported by:** native concurrency investigation

**Summary:** Local System screen notes describe SavePRM as writing settings to floppy or SCSI; it actually transfers between internal memory and system backup memory.

**Repro:** Compare docs/hardware/screens/06-system-screens.md section5 against owner manual Advanced3-104 (PDF page128).

**Expected:** Backup-memory semantics with no disk-file promise.

**Actual:** Incorrect file container and permanent disk write claims. Native probes show MIDI completions but zero FDC accesses, consistent with the manual.

**Resolution:** Corrected section5 to the verified owner-manual contract. This command cannot qualify concurrent disk activity.

### BUG-066 — Native SCSI BDID read/write encoding is incorrect

- **Status:** FIXED
- **Resolved:** 2026-10-14
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-14
- **Reported by:** native SCSI identity regression

**Summary:** Native BDID returns numeric initiator ID and retains unused upper write bits. The SPC reads a one-bit bus mask and accepts only write bits0..2.

**Repro:** Expanded scripts/verify_native_scsi_registers.py; pre-fix binary fails at ID0 (returns0 instead of1).

**Expected:** IDs0..7 read1,2,4,8,16,32,64,128; upper write bits are ignored.

**Actual:** Encoded ID returned unchanged; existing fixture incorrectly expected7 for ID7.

**Evidence:** Local upstream mb87030.cpp bdid_r/bdid_w (also inherited by mb89352), and private scsi200-bdid-before/result.json.

**Selection regression:** With a supplied private target6 image, an initiator0+target6 mask incorrectly selects bit0; the native identity fixture fails before correction. Native selection must exclude its own initiator bit, and initiator-only/empty masks must time out without falling back to a stale target. All eight IDs, seven target6 selections and direct-data INQUIRY identities are exercised; the direct-data fixture does not qualify PIO/DMA handshake.

**Notes:** Native-only correction; does not qualify SCSI discovery or full PIO/DMA.


**Resolution:** Native identity/selection, command ACK/REQ and bounded input DMA47 fixes pass isolated before/after regressions, original-firmware discovery/unsupported-media recovery,131072 exact cold stereo frames and363 backend tests. Source/fixture/commands and explicit limits: [SCSI discovery evidence](../condensed/validation/milestone-5-scsi-discovery-2026-10-14.json). Successful SCSI sample Load remains open.

### BUG-065 — Native SCSI idle status permanently asserts busy and reset

- **Status:** FIXED
- **Resolved:** 2026-10-14
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-14
- **Reported by:** native SCSI status regression

**Summary:** Native SSTS returns constant 0x28, whose actual bits mean busy and reset. The old comment incorrectly calls these empty FIFO and zero transfer count.

**Repro:** `python scripts/verify_native_scsi_registers.py --state-dir <fresh-absolute-directory>` with the added idle/status assertions.

**Expected:** Idle direct-data controller reports 0x05; TC-zero follows the counter and reset follows SCMD reset assertion.

**Actual:** Pre-fix native binary fails the idle SSTS assertion with constant 0x28.

**Evidence:** Private scsi-status198-before/result.json; local upstream mb87030.h SSTS constants and mb87030.cpp dynamic counter/FIFO flags.

**Notes:** This does not establish native PIO/DMA handshake or firmware SCSI discovery.

**Resolution:** Native SSTS derives data availability, TC-zero, reset and connection from existing direct-data controller state; legacy flat behavior remains separate. Before/after assertions, native audio/MIDI, 131072 exact cold stereo frames, legacy transfer/state and 363 backend tests pass. Firmware discovery still reports No Drive. [Durable evidence](../condensed/validation/milestone-5-scsi-status-2026-10-14.json).

### BUG-064 — Native absent SCSI targets are fabricated

- **Status:** FIXED
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-14
- **Resolved:** 2026-10-14
- **Reported by:** Native SCSI absent-target selection fixture

**Summary:** scsi_init_devices creates ready10MiB target0/1 even when no backing
image exists. These synthetic defaults must not apply to native firmware.
**Repro:** Fresh isolated native register fixture, no roms/SCSI images; target0
SELECT succeeds after command decode is corrected instead of timing out.
**Expected:** Native targets exist only for explicitly supplied images.
**Actual:** Hidden blank HD/CD targets always present.
**Evidence:** Native fixture scsi-register197-qualified; scsi_init_devices fallback
source blocks. The older flat/HLE diagnostic fallback is a separate profile.
**Notes:** Preserve legacy fixture defaults; qualify native absent vs supplied
images separately from firmware Load and physical selection timing.


**Resolution:** Native-only prerequisite corrected; isolated final register/absent-target/acknowledgement fixture passes. Native boot/audio/MIDI and131072-frame cold state,363 backend tests and legacy SCSI regressions pass within recorded limits. Full firmware SCSI discovery/Load remains OPEN. Evidence: `docs/condensed/validation/milestone-5-scsi-prerequisites-2026-10-14.json`.

### BUG-063 — Native SPC selection and interrupt acknowledgement mismatch

- **Status:** FIXED
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-14
- **Resolved:** 2026-10-14
- **Reported by:** Milestone5 SCSI native register regression

**Summary:** Native SCMD20 selection is decoded with the legacy low-three-bit
synthetic command model; native INTS is cleared on read rather than write.
**Repro:** `python scripts/verify_native_scsi_registers.py --state-dir <fresh>`
after BUG-062 address fix. Absent-target SELECT must report TIMEOUT04 and preserve
INTS on repeated reads until explicit acknowledgement; currently fails.
**Expected:** MB89352 command high-bit classes, SCTL controller-reset40,
SCMD bus-reset10 and INTS write acknowledgement for native firmware.
**Actual:** Legacy command encodings/interrupt side effects applied in native mode.
**Evidence:** Private scsi-command197-before/result.json; NetBSD original register
header at https://raw.githubusercontent.com/NetBSD/src/trunk/sys/dev/ic/mb89352reg.h
**Notes:** Qualify this limited contract separately from full transfer/FIFO/DMA,
SCSI IRQ routing, device discovery and firmware Load. Preserve legacy fixtures.


**Resolution:** Native-only prerequisite corrected; isolated final register/absent-target/acknowledgement fixture passes. Native boot/audio/MIDI and131072-frame cold state,363 backend tests and legacy SCSI regressions pass within recorded limits. Full firmware SCSI discovery/Load remains OPEN. Evidence: `docs/condensed/validation/milestone-5-scsi-prerequisites-2026-10-14.json`.

### BUG-062 — Native SCSI register spacing is incorrect

- **Status:** FIXED
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-14
- **Resolved:** 2026-10-14
- **Reported by:** Milestone5 firmware SCSI Load probe

**Summary:** Original boot firmware accesses MB89352A registers at102400,102402,
102404,102408 etc. Native map routes only102400..10240F using byte offsets, so
SCTL/SCMD accesses hit other registers and TEMP/transfer counters are unmapped.

**Repro:** Private original-firmware boot trace under scsi-load197-boottrace;
isolated native register-window regression will qualify the correction.
**Expected:** Native even byte ports102400+2*register map all16 registers.
**Actual:** Byte-stride map, truncated window. Firmware drive list stays No Drive;
full Scan/Load causality and remaining controller semantics are not yet qualified.
**Evidence:** Private scsi-load197-boottrace/edit/scsi-trace.json; boot SCTL writes
80/92/12 at102402 and SCMD writes14/04 at102404. MB89352 register definitions:
https://raw.githubusercontent.com/NetBSD/src/trunk/sys/dev/ic/mb89352reg.h
**Notes:** Legacy flat F020 mapping/device-model tests are separate; do not change
their addressing silently. Correct native spacing before auditing command behavior.


**Resolution:** Native-only prerequisite corrected; isolated final register/absent-target/acknowledgement fixture passes. Native boot/audio/MIDI and131072-frame cold state,363 backend tests and legacy SCSI regressions pass within recorded limits. Full firmware SCSI discovery/Load remains OPEN. Evidence: `docs/condensed/validation/milestone-5-scsi-prerequisites-2026-10-14.json`.

### BUG-061 — Standalone launcher omits native stereo mixer

- **Status:** FIXED
- **Severity:** S2
- **Area:** dsp-audio
- **Opened:** 2026-10-14
- **Resolved:** 2026-10-14
- **Reported by:** Milestone5 combined-audio qualification

**Summary:** Python standalone NativeRuntime sets interpolation but omits
S760_NATIVE_STEREO_MONITOR. Native left/right gains consequently stay1.0,
bypassing firmware pan. The C++ plugin path already enables stereo (BUG-056).

**Repro:** Inspect scripts/s760_runtime.py launch environment and native
left_gain/right_gain selection in s760.cpp; reproduce loaded-note CC10 pan with
the forthcoming combined-audio acceptance script in default vs diagnostic mode.

**Expected:** Supported standalone firmware pan reaches native stereo output.
**Actual:** Source path bypasses mixer gains unless explicitly enabled.
**Evidence:** Native six-case baseline on2026-10-14 confirms identical held L/R at pan0/64/127 for bypass and LP-C32 patches; explicit diagnostic stereo/filter profile routes correctly in72 cases. Commands, hashes and rows: `docs/condensed/validation/milestone-5-combined-audio-2026-10-14.json`.
**Notes:** Explicit diagnostic combined profile enables stereo plus existing filter
monitor for qualification; normal stereo is now fixed independently; filter remains diagnostic.


**Resolution:** Always enable existing native stereo mixer in Python launcher; plugin already does so. Six normal stereo cases, native variable PCM/scheduled MIDI and131072-frame cold replay pass;363 backend tests pass. Changed audio-profile identity rejects incompatible old mono state. Filter remains diagnostic. Evidence: `docs/condensed/validation/milestone-5-normal-stereo-2026-10-14.json`.

### BUG-060 — Controller requalification rejects a block during UI editing

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-13
- **Reported by:** Native controller requalification

**Historical report (superseded by the scoped verifier resolution below).**

**Summary:** A fresh run against the current WebView module passes measured bend, expression, pan, channel-mode release, panic and neutral reset, then rejects a process block while changing the assigned controller from11 to1. The historical55-case run predates the current binaries.

**Repro:** `python scripts/verify_vst3_controllers.py --host docs/ic20-hle-findings/chatGPT-work/sdk150/host/build/Release/SoundCheckServer.exe --module docs/ic20-hle-findings/chatGPT-work/m2-webview-build/Release/Roland_S760.vst3 --state-dir NEW_PRIVATE_DIRECTORY`, outside the sandbox, original OS2.24/ROBOFULL.

**Expected:** All55 measured cases finish and emit automation-report.json.

**Actual:** `RuntimeError: Error: Plugin rejected audio block` in select_assigned_controller. No completed report is emitted. Cause and repeatability remain under investigation; this is not evidence of incorrect CC1 semantics.

**Evidence:** Private soundcheck/m4-controller-requalification-20261013-native captures and host.log.

**Notes:** Earlier successful qualification remains historical evidence. Current artifact requalification must finish before claiming a fresh full pass.

**Follow-up:** The unchanged current-artifact repeat in private soundcheck/m4-controller-requalification-20261013-retry exits0 and passes all55 cases, including the assignment edit that failed previously. Keep this intermittent failure OPEN: its cause is unknown. Current hashes and complete measured results are recorded in `docs/condensed/validation/milestone-4-controller-requalification-2026-10-13.json`; no production fix or reliability closure is claimed.

**2026-10-14 filter follow-up:** New normal-filter SoundCheck fixture loads and completes the first bypass/left-pan case, then reports the same audio-block rejection. Initial editor selector timeout is separate. Private `soundcheck/filter199-retry` retains captures. Verifier inspection found eight unpaced setup blocks between cases; a fully paced repeat subsequently passes as recorded below. No production cause or reliability closure is claimed.

**Filter repeat result:** Fully paced normal-filter SoundCheck repeat passes all nine named cases, editor reopen and220500 exact fresh-instance/variable-block frames. Unpaced setup bursts were removed from the verifier. BUG-060 remains OPEN because no production cause/reliability fix is established; see normal-filter validation.

- **Resolved:** 2026-10-14

**Resolution:** The functional controller and filter verifiers now explicitly negotiate offline processing and require mode2 acknowledgement before rendering; filter fresh-instance project restore negotiates the same mode. A64-block unpaced realtime host burst deterministically reproduces the audio-block rejection; the same burst and all55 controller cases pass offline. All9 filter cases and220500 exact fresh-instance/variable-block replay frames pass. No rejected block is retried, no assertion is skipped and no production deadline handling is weakened. Stream/core/plugin units and392 backend tests pass. Separate paced native C++48kHz/variable-block processing matches240000 reference frames with zero missed deadlines. Evidence: docs/condensed/validation/bug-060-qa-processing-contract-2026-10-14.json.

**Scope of closure:** Corrects the functional QA processing-contract defect. The burst establishes the rejection class, not the exact cause of every historical intermittent run. Production realtime UI/load reliability remains subject to the separate release acceptance matrix; a future supported-profile rejection requires its own evidence and triage.

### BUG-059 — GB-6 vertical sensitivity skips part rows

- **Status:** FIXED
- **Severity:** S3
- **Area:** hardware
- **Opened:** 2026-10-13
- **Reported by:** user, physical GB-6/S-760
- **Resolved:** 2026-10-13

**Summary:** After the mechanical wheel repair, tracking works but vertical cursor steps are too coarse for adjacent Perform Play part selection.

**Resolution:** User tested v8 X8/Y4 and reports it works perfectly for the requested row-selection task. Resolved2026-10-13. At user request, v9 matches horizontal gain to4 as well; only file0x18BD0 changes from3 to2 relative to v8. All2,048 decoded/peripheral-model cases pass. V9 SHA256 `c611e7156c9069dc632bcfd8e4d20a52da70ed2528112f29fe87258803f42deb`; v9 itself still awaits hardware confirmation. Earlier notes below describe pre-resolution evidence.

**Repro:** Hover over Perform Play part rows and move the trackball vertically to select the next row. Installed image revision was not explicitly identified; latest supplied baseline was v7 X8/Y8.

**Expected:** Adjacent rows are readily selectable.

**Actual:** Cursor skips a row when moving up or down.

**Evidence:** User report in chat; `temp/work/sony-gb6-20261013/v8-validation.json` identifies the candidate and checks.

**Notes:** V8 halves vertical gain to4, keeping horizontal gain8. Compared with v7, only file byte0x18BEB changes from3 to2 (vertical SHLB count). 2,048 decoded/peripheral-model cases pass. If stock2x scaling applies, a single vertical counter step now produces8 pixels rather than16. Actual row-selection improvement awaits hardware test. Original images retained; fourth-controller plan remains deferred.

### BUG-058 — Experimental GB-6 OS patch has weak axis response

- **Status:** FIXED
- **Severity:** S2
- **Area:** hardware
- **Opened:** 2026-10-13
- **Reported by:** user, real S-760/GB-6 trial
- **Resolved:** 2026-10-13

**Resolution:** User found an internal wheel incorrectly seated, reseated it, and reports the device now works. Before repair, directly rotating the tracking shafts by finger produced very smooth cursor movement, supporting mechanical contact/binding as the cause of the remaining left/up difficulty. Preserve the user's currently installed image as their working baseline; the exact installed revision was not explicitly identified, so do not claim v7 hardware qualification. Earlier v3 bank-addressing and axis-select implementation defects remain part of the experimental history. Button coverage, long-duration testing and general GB-6 compatibility are not established by this report. Negative-endpoint and phase explanations were hypotheses, not confirmed causes of the final sticking.

**Summary:** The first GB-6-only OS2.24 patch communicates with the device but motion is impractically slow and asymmetric.

**Repro:** Boot `S760224.GB6-experimental.IMG` (SHA256 `285059b2055892fb7d15faf1b1927ddc54eb6b3093548a1c5914f0cc79890f2c`) on the physical sampler with Sony GB-6 and move the ball on each axis.

**Expected:** Usable horizontal and vertical cursor motion.

**Actual:** User reports right/left works very slowly; up/down barely works. Button behavior was not reported.

**V2 hardware follow-up:** User reports up/down reversed and left/right still super slow. No measured speed or button results supplied. V3 candidate reverses Y and supports independent build-time gains, default X16/Y4 (4x v2 small horizontal motion; same vertical magnitude). Lookup outputs clamp to +/-63 before stock 2x scaling to avoid sign wrap. 512 decoded table cases pass; v3 hardware validation pending.

**V3 hardware follow-up:** User reports no vertical motion and only leftward horizontal motion. V3 is rejected by hardware. Its static lookup tests assumed CPU code and data addresses map to the same physical bank, contrary to the separate fetch/data selectors documented in condensed document 01. The lookup tables were placed in code backing without configuring the data selector. This is an implementation defect; actual runtime bank selectors were not captured.

**V4 candidate:** Rebuilt from v2, removes all lookup loads/tables, directly reverses Y arithmetic, raises X gain from4 to8 and caps its +64 endpoint to+63 before stock scaling. Full decoded poll flow passes 768 phase/nibble/upper-bit cases, including phase and selection. Candidate SHA256 `5d43390dd5ab1080a7cab0656a6c5d1fffd12d0b0f393be07ea2564e55622fa8`. Hardware retest remains required; previous static checks did not establish hardware correctness.

**V4 hardware follow-up:** User reports right seems to move the cursor down; up/down now have correct direction but remain slow. Stored-phase/physical-select mismatch is a possible cause, not established by a port capture. V5 removes the persistent phase byte and explicitly selects high/X, waits, samples X, then low/Y, waits, samples Y. X8/Y8 arithmetic, no lookup tables. 1,024 decoded X/Y/button combinations passed, including delay loops and write/read ordering; hardware select mapping, latency and counter behavior remain unverified. V5 SHA256 `c7407cbac08a16de3389e3f43b5d5adf5144de5f4b1961524b3986995a41d0dc`. Still IN-PROGRESS.

**Evidence:** Original report in this chat. Local experiment artifacts under `temp/work/sony-gb6-20261013/`; v2 hashes, decoded checks and caveats in `v2-validation.json`.

**V6 hardware follow-up / v7 diagnostic:** User reports improvement but intermittent difficulty moving up or left. V6 produces -64 at nibble0, subsequently -128 if stock 2x scaling applies. This is representable signed-byte data, so it is not proof of overflow or the cause of the reported sticking. V7 changes only that negative endpoint on each axis to -63 (stock doubled value -126), leaving ordinary X8/Y8 gain, direction, selection, timing and buttons unchanged. 2,048 decoded/peripheral-model cases pass. Candidate SHA256 `b438cc9d0a2157113aa0f71974cfa51e5d176ef84cd9449f965cc53c93ae1ea4`; hardware validation pending. If symptom persists, raw counter observations are needed rather than assuming further gain changes fix it.

**V5 hardware follow-up and revised protocol evidence:** User reports pure right moves mostly down and somewhat right; vertical responds poorly. No other device is available to test this GB-6. Retrieved openMSX `src/input/Trackball.cc` directly via GitHub: its read selects Y when pin8 high, X when low; rising resets X, falling resets Y. Its signed deltas pass through without mouse-style negation. This contradicts the wiki select mapping used in v1-v5 and agrees with the published MSX BIOS listing (first low sample DX, subsequent high sample DY). Related GB-7 evidence, not direct GB-6 parity. Prior level-reset/phase theories are unconfirmed and no longer the leading explanation.

**V6 candidate:** Low/X then high/Y; read each counter before its reset edge, end low; original short delay helper only; X8/Y8, no mouse sign negation, no lookup tables or persistent phase. 2,048 decoded polling/peripheral-model cases pass, including actual select-keyed reads, reset edges and both startup select states. Evidence source saved locally as `openmsx-Trackball-reference.cc`; validation in `v6-validation.json`. SHA256 `b8ea69e840d38701f16bed091c1e1950c2eca8f1371bd46bcf2cb88744d9e3fd`. Hardware retest required.

**Notes:** V1 uses conservative linear gain and leaves X selected between polls. A possible level-sensitive counter reset could starve Y; this remains a hypothesis. V2 alternates selection across polls and increases per-sample gain 4x, repurposes the old mouse timeout byte as phase and bypasses its mouse-only timeout logic. Static checks passed for 192 phase/nibble/button cases. Real boot, axis timing, speed and buttons remain unverified for v2; do not mark fixed until retested.


### BUG-057 — Native VST3 host input does not reach native ADC

- **Status:** FIXED
- **Resolved:** 2026-10-13
- **Severity:** S2
- **Area:** dsp-audio
- **Opened:** 2026-10-13
- **Reported by:** Milestone 4 host sampling objective / native QA

**Summary:** The native instrument exposed no accepted host input bus and its worker rendered output without delivering host PCM to the Milestone 3 ADC peripheral.

**Repro:** Load the original-firmware native module in SoundCheck and request stereo sampling input. The prior module reports no input bus. An initial separate input/render worker implementation also exhausts its output lead under paced host processing.

**Expected:** An explicitly activated supported stereo input reaches firmware Sampling and survives Sample Save/cold Load; inactive output-only use remains valid.

**Actual:** Host recording was unavailable. The first ingress implementation rejects audio blocks after output starvation; logs are retained under chatGPT-work/m4-host-input-181 and -182.

**Evidence:** `scripts/verify_vst3_sampling_input.py`; private native host logs and firmware screenshots. [Final validation](../condensed/validation/milestone-4-host-sampling-2026-10-13.json).

**Resolution:** Optional 44.1 kHz stereo instrument input, bounded copied PCM with in-place buffer support, worker-side PCM16 conversion and combined peripheral input/render transactions. FX remains unadvertised; other input rates reject explicitly.

**Qualification:** Actual SoundCheck SDK buses with varying/aliased buffers record45649 exact L/R frames/channel with zero native ADC underruns;184320 allocation bytes survive firmware Save/cold Load. Active-input paced callbacks and output-only48/96kHz replay are exact with zero missed deadlines. Single render transactions enqueue bounded peripheral chunks, avoiding partial-batch round trips.354 backend regressions, SDK input rejection/silence/disconnection tests and240000-frame cold state pass.

### BUG-056 — Native VST launcher omits stereo mixer enable

- **Status:** FIXED
- **Severity:** S2
- **Area:** dsp-audio
- **Opened:** 2026-10-13
- **Resolved:** 2026-10-13
- **Reported by:** Native SoundCheck controller qualification

**Summary:** The C++ native launcher enables interpolation/envelopes but never enables the existing stereo mixer. Native pan coefficients are bypassed and both output channels remain identical.

**Repro:** SoundCheck1.0.0 Windows x64, OS2.24/ROBOFULL,44100Hz/512 frames, module SHA256 e4c398d55480b7e57342ee2191a0c4618b4c4339f18e88069d0e7fcbf52adfbe. Send CC10=0/127 and retrigger note60. Compare separately captured left/right PCM.

**Expected:** Firmware-selected pan changes native stereo channel levels.

**Actual:** Both channel peaks remain0.0440203883 for both pan extremes. `native_wave_monitor_update` applies unity to both sides because `m_native_stereo_monitor` is false.

**Evidence:** Private soundcheck/m4-controllers-182/automation-report.json and controller qualification log. Regression and final identities accompany closure.

**Notes:** Stereo coefficient storage/scaling already exists in the native driver; qualify enabling that path in the C++ runtime. Hardware gain-law fidelity remains Milestone5.

**Resolution:** C++ native launches explicitly enable the existing stereo coefficient path. SoundCheck fresh-note pan produces left-only/right-only/equal-centre output; the prior binary fails this check.55 controller cases, three-rate exact native PCM with zero missed deadlines,240000-frame cold state, core/plugin tests,354 backend tests and native original-firmware acceptance pass. Centre level changes from the former mono bypass; old-build state intentionally rejects. Hardware gain-law fidelity remains separate. [Evidence](../condensed/validation/milestone-4-controller-semantics-2026-10-13.json).

### BUG-055 — Native sampler reports zero tail

- **Status:** FIXED
- **Severity:** S3
- **Area:** bridge
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Milestone 4 SDK host qualification

**Repro:** Run the independent Steinberg SDK probe with valid native configuration. The new `getTailSamples()==kInfiniteTail` assertion fails on the existing module.

**Expected:** Report a potentially infinite tail because looped or sustained voices may continue indefinitely.

**Actual:** Native `getTailSamples()` returns zero, potentially allowing a host to truncate active voices during tail rendering.

**Evidence:** SDK probe failure: `sampler must report potentially infinite voice tail`; core/src/s760_vst3_plugin.cpp returns zero unconditionally.

**Resolution:** Native instrument returns SDK kInfiniteTail. Independent SDK regression and actual SoundCheck report pass; sustained playback and note-off release remain functional. See [rendering qualification](../emulator/runtime/native-vst3-rendering.md). The historical core's tail behavior is unchanged.

### BUG-054 — Knob indicator visual defect

- **Status:** CANNOT-REPRODUCE
- **Severity:** S3
- **Area:** ui
- **Opened:** 2026-10-12
- **Reported by:** User

**Summary:** User reports a visual defect in the knob indicators. Functionality is unaffected. A fix is required before shipping; impact on both VST3 and standalone is suspected, not yet verified.

**Repro:** Pending the exact visual symptom, affected knob(s), and position or interaction that reveals it. No independent reproduction yet.

**Expected:** Knob indicators render correctly throughout their travel in both applications.

**Actual:** Indicator appearance is incorrect according to the user report; precise appearance has not yet been described.

**Evidence:** User report on 2026-10-12; no screenshot or measured reproduction attached.

**Notes:** S3 per user classification. CANNOT-REPRODUCE records missing reproduction details, not dismissal or release acceptance. Keep this unresolved as a pre-shipping requirement; verify both frontends when fixing.

### BUG-053 — Private SoundCheck automation never reaches processor

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-12
- **Closed:** 2026-10-12
- **Reported by:** Native VST3 controller qualification

**Repro:** Send `set_param`, then `process_test_chunk` in the private native SDK QA backend. Pending changes were stored, but the test call supplied null `inputParameterChanges`.

**Expected:** Real SDK parameter queues reach the processor once, on the next block.

**Resolution:** Private host uses SDK ParameterChanges and consumes pending updates on block0. Original independent SoundCheck checkout unchanged. Measured CC7/64/123 audio effects pass. The [reproduction patch](../condensed/validation/soundcheck-native-automation-2026-10-12.patch) and [evidence](../condensed/validation/milestone-4-midi-2026-10-12.json) preserve the supported QA profile.

### BUG-052 — Native VST3 drops host MIDI controllers

- **Status:** FIXED
- **Severity:** S2
- **Area:** midi
- **Opened:** 2026-10-12
- **Closed:** 2026-10-12
- **Reported by:** Independent SDK MIDI mapping regression

**Summary:** Native VST3 exposes no IMidiMapping and ignores inputParameterChanges, so host sustain, pitch bend and panic cannot reach original firmware. Notes alone are delivered.

**Repro:** Build/run s760_vst3_sdk_tests against the concrete native module with valid firmware configuration. Query controller for the actual SDK IMidiMapping IID.

**Expected:** Stable channel-specific assignments and bounded sample-offset controller delivery.

**Actual:** Query fails at `native MIDI mapping interface`; process_native only handles note events.

**Evidence:** Independent Steinberg-header probe and core/src/s760_vst3_plugin.cpp inspection.

**Resolution:** Added actual SDK-compatible IMidiMapping, hidden channel-specific CC/bend aliases and bounded queue-point merging into the native worker clock. SDK ABI/queue/overflow checks pass; paced varying-block controller PCM matches independent MIDI bytes exactly; SoundCheck volume/sustain/CC123 release effects pass. Fixed for the documented nonzero-block transport profile. Configured audible bend, reset semantics and CC120 behavior are explicitly not inferred. [Contract and limits](../emulator/runtime/native-vst3-midi.md).

### BUG-051 — Initial windowed package startup exception

- **Status:** CANNOT-REPRODUCE
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Packaged Windows endpoint acceptance

**Summary:** The first newly built windowed package run created native runtime files but never published `session.json`. Its test process displayed an unhandled-script exception; the original exception text was not captured. A diagnostic console build and subsequent instrumented windowed/browser and actual desktop starts succeeded.

**Repro:** Private `m3-device-final-package/dist/S760Studio/S760Studio.exe --no-browser --no-sound --seconds 95 --state-dir .../windows-output-package-browser` with explicit boot/system/media paths. Concurrent bounded ASIO test was running. No repeatable trigger established.

**Expected:** Publish the session URL or an actionable startup diagnostic.

**Actual:** Initial session publication was absent; an unhandled exception window remained after the native child exited.

**Evidence:** Private `windows-output-package-browser/`, `windows-output-console-debug.log`, `windows-output-package-e2e-final.log` (one passed) and `device-final-desktop/desktop-verification.json` (OS ready,225776 nonblack CRT pixels).

**Resolution:** Cannot reproduce on the subsequent console, instrumented windowed and final desktop starts; no root-cause fix claimed. Frozen launches with an explicit `--state-dir` now preserve exceptions in `startup-error.log` for a recurrence. This is not clean-machine or indefinite startup reliability qualification.

### BUG-050 — Explicit Windows output endpoint produces no audio

- **Status:** FIXED
- **Severity:** S2
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Native Windows endpoint qualification

**Summary:** The new Windows endpoint selector initially wrote a raw endpoint ID into MAME's sound mapping. MAME identifies output nodes as `o:` plus the endpoint ID and removed the unresolved mappings, leaving no stream on the selected endpoint.

**Repro:** Select Realtek Digital Output, boot original OS2.24, load ROBOFULL and hold a native note while capturing that endpoint's WASAPI loopback. The initial mapping produces zero captured packets despite nonzero native PCM.

**Expected:** Native left/right audio reaches the selected Windows endpoint.

**Actual:** The unprefixed mapping is removed and digital loopback is empty.

**Evidence:** Private `windows-output-48000.log` reproduces the failure. `windows-output-48000-fixed/result.json` reports575520 stereo frames at48000Hz, expected20004.5Hz fixture peak, finite output and silent note-off. The corrected mapping survives MAME shutdown. `tests/test_native_runtime.py` covers the required node prefix, stereo channel mapping, escaping and restoring default output.

**Resolution:** Prefix render endpoint IDs with `o:` when staging private MAME sound mappings. Persisted configuration keeps the original Windows endpoint ID. This is digital shared-mode output qualification, not analog converter parity.

### BUG-049 — Device loss leaves native sampling running without input

- **Status:** FIXED
- **Severity:** S2
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Standalone audio acceptance review

**Summary:** A failed or stalled recording stream previously closed the device and reported an error while native time continued. An active recording could consume missing input, and recovery required restarting the sampler.

**Repro:** In the standalone capture worker, make the device read/status operation report a driver failure while a native machine is running. See `tests/test_audio_recovery.py`.

**Expected:** Pause the same native machine, show an actionable failure, and reopen the device with input re-priming before resuming. Preserve RAM, media and controls.

**Actual:** Before the change, the device closed without a native pause or a reopen operation.

**Evidence:** Four backend recovery tests cover pause, same-machine resume, failed reopen and preserving existing queued input while re-priming. React acknowledgement/error handling has a focused regression. Actual MOTU stream reopening after an injected closed-stream failure preserves the native PID and media, freezes native time while failed and resumes successfully. Physical unplug testing is excluded by user direction.

**Notes:** Live MIDI unplug is excluded from Milestone3 acceptance by user direction. This defect concerns audio capture and output devices.

**Resolution:** Pause on stream failure, preserve reported loss counters, offer acknowledged Reopen audio, re-prime input without overwriting queued samples, and resume the existing native machine. See [qualification](../condensed/validation/standalone-audio-devices-2026-10-12.json).

### BUG-048 — ASIO underrun counter omits refill-wait silence

- **Status:** FIXED
- **Severity:** S2
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Sustained audio acceptance review

**Summary:** After output underflow, the callback zero-fills until the ring reaches its prime watermark. The counter previously counted only the initial short read, omitting subsequent silent callbacks during refill.

**Repro:** Prime a real MOTU ASIO output with4096 silent frames, stop supplying PCM, allow initial consumption, then compare missing-frame counters over another0.2 seconds. The preserved package DLL reports zero additional missing frames despite continued callbacks.

**Expected:** Count every missing output frame after playback starts, including re-prime waits; exclude initial startup silence and explicitly disabled output.

**Actual:** Old counter freezes while the device continues receiving zeros.

**Resolution:** Track whether playback has started. Count silent refill callbacks after that point, preserving explicit zero-fill/re-prime policy. The real driver probe reports8704 additional missing frames with the corrected DLL versus0 with the preserved DLL. Native callback regression covers initial prime, short read and a subsequent refill-wait callback.

**Evidence:** Private `reprime-old.log` / `reprime-new.log` under `docs/ic20-hle-findings/chatGPT-work`; source regression in `core/tests/test_asio.cpp`. Earlier sustained records retain their original counters and therefore undercount total refill silence.

### BUG-047 — Sustained ASIO playback output underruns

- **Status:** FIXED
- **Severity:** S3
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Physical micro lite MIDI/MOTU ASIO sustained acceptance

**Summary:** Physical MIDI loopback playback exposes native ASIO output underruns after the short smoke-test window.

**Repro:** Original firmware ROBOFULL, normal-speed standalone, MOTU ASIO outputs 3/4 to inputs 1/2 at 44100 Hz/512 frames; micro lite Port 5 physical out-to-in note-on/off cycles, with display and capture workers active. Initial test overlaps backend tests and a package build; resource contention is not isolated as the cause.

**Expected:** Sustained playback without unreported loss; bounded explicit recovery if a queue underruns.

**Actual:** Counter reaches 826 missing output frames by 122 seconds, with zero native output drops or driver status flags. The existing callback zero-fills and reprimes, and the UI reports the loss. This does not establish a driver-level dropout.

**Evidence:** Private `docs/ic20-hle-findings/chatGPT-work/m3-midi-sustained.log` and adjacent raw native/physical PCM.

**Notes:** Earlier native output draining below the prime watermark passes its regression, but the full physical retest still reports 102 missing output frames and8192 discarded input frames. The baseline ends at1610 missing output frames and22528 discarded input frames. Both runs produce all90 native note pulses and a silent release tail. Concurrent host load differs, so the counter difference does not isolate causation. At that stage this bug remained open pending controlled native/device clock and scheduling qualification; the later resolution is recorded below. [Durable evidence](../condensed/validation/standalone-midi-sustained-2026-10-12.json).

**Resolution:** Binary input transport, output delivery even when the input FIFO is full, bounded wall-clock feedback and an explicitly displayed16384-frame output target pass five minutes/150 physical MIDI note cycles with zero output underruns/discards/native drops/driver flags. All150 native pulses and silent release are independently checked.2048 input frames are discarded; no zero-loss recording claim. The target adds371.52ms transport buffering, separate from driver latency. Earlier counts omitted refill-wait silence (BUG-048); they are lower bounds. This closes the documented finite profile, not indefinite or arbitrary-load qualification. [Evidence](../condensed/validation/standalone-audio-devices-2026-10-12.json).

### BUG-046 — Output-only ASIO can silently stall while reporting active

- **Status:** FIXED
- **Severity:** S3
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Roadmap device-failure regression test

**Summary:** ASIO progress monitoring checked captured input only. With input disabled, a driver that remained active but stopped consuming output could leave the standalone silent indefinitely.

**Repro:** `tests/test_asio.py::test_output_only_driver_stall_is_visible_even_if_driver_reports_active` models an active driver with 8192 queued frames, unchanged played counter and more than two seconds elapsed. This is a deterministic driver model, not a physical unplug test.

**Expected:** Report the stopped output stream and provide reconnect/apply guidance.

**Actual:** Before the fix, status continued to succeed; the regression failed with `DID NOT RAISE OSError`.

**Resolution:** Track the existing native played-frame counter. If enabled output remains primed with queued PCM but makes no progress for two seconds, raise an actionable error through the existing stream failure/close path. Empty queues and progressing output do not trigger the check. Six focused ASIO tests pass; physical unplug qualification remains separate.

**Evidence:** Regression tests in `tests/test_asio.py`; native counter implementation in `core/src/s760_asio.cpp` is unchanged.

### BUG-045 — Live capture delivery underruns during firmware recording

- **Status:** FIXED
- **Resolved:** 2026-10-12
- **Severity:** S2
- **Area:** dsp-audio
- **Opened:** 2026-10-12
- **Reported by:** Native MOTU physical loopback acceptance

**Summary:** Initial standalone capture delivery shared the 15 Hz display polling schedule and failed to sustain firmware recording.

**Repro:** Normal-speed native S-760 v2.24, opt-in recording device Windows MME MOTU Stereo In 1-2 at 44100 Hz stereo PCM16; ASIO outputs 3/4 looped physically to inputs 1/2. Arm and start using the firmware sampling screen, then stop and save.

**Expected:** Bounded capture transport sustains recording without native input underruns.

**Actual:** 51587 underruns by the recording screenshot and 55428 after stopping; both physical tones reach saved sample PCM, but continuity is unqualified.

**Evidence:** Private `docs/ic20-hle-findings/chatGPT-work/motu-live-sampling-34.log` and its adjacent capture/session evidence directory.

**Resolution:** Root cause was 4KB/frame JSON ingress, below the bandwidth required by stereo PCM packets. Ingress now reads at most 64KB/frame and executes at most one command; live PCM bypasses pointer-settle waits. A separate 5ms capture worker primes a bounded 8192-frame buffer. Checkpoint save/restore reopens hardware buffers and reports a discontinuity. MOTU physical recording now has zero native underruns; both 65514-frame channels match captured device PCM exactly and all 276480 allocated bytes survive firmware Save/export/fresh Load.329 backend/120 React tests and native source/package browser recording settings pass. Alternate rates, driver-level loss counts and long-term drift remain separate. See [physical sampling evidence](../condensed/validation/native-physical-sampling-2026-10-12.json).

### BUG-044 — Standalone diverges from approved native VST interface

- **Status:** FIXED
- **Severity:** S1
- **Area:** ui
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** User; S1 explicitly requested by user

**Summary:** Standalone uses a separate simplified rack instead of the approved native VST panel. It omits completed button groups, Shift functions, input/output knob layout and Gotek browse/select controls. Its CRT housing also differs and exposes unused black transport rows.

**Repro:** Compare the native standalone README screenshot with the native SoundCheck VST screenshot captured on 2026-10-11.

**Expected:** Both native entrypoints share the approved visual hardware layout, with standalone settings and optional keyboard.

**Actual:** Generic button rows and a disk-status box; instructional text and media controls separate rack and keyboard.

**Evidence:** `docs/images/standalone-keyboard.png`; private reference `docs/ic20-hle-findings/chatGPT-work/soundcheck/156-rack-dials-final/loaded.png`.

**Notes:** Separate `NativeRack` and `S760FrontPanel` render paths. Verify shared rendering and real firmware inputs before closure.

**Resolution:** Shared front-panel and CRT-housing renderers; restored native Gotek browse/select and Shift controls; matched VST crop; 61-key keyboard scales with rack. Removed header, dropdown, footer and empty content area; all utilities are in Configuration.118 React tests,5 unchanged shell/visual checks, real native load/reconnect/restart/session recall and packaged configuration/WebView checks pass. See [validation](../condensed/validation/standalone-visual-parity-2026-10-12.json).

### BUG-043 — Sampling postprocessing stalls on A7 wave-to-RAM DMA

- **Status:** FIXED
- **Severity:** S2
- **Area:** mame-driver
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** ChatGPT native sampling bus probe

**Summary:** OS 2.24 Sampling → Ready → name confirmation → Start enters postprocessing and polls IC4 DMA count forever. BC RAM-to-wave is implemented; inverse A7 is missing.

**Repro:** Native IC15/OS 2.24, accelerated muted machine, Sample → Sampling → Ready → Yes → Start. Read-only trace observes wave word 8, RAM destination 0x0ED712, byte count 0x2400 and command A7 at CPU 740B. Reads at CPU 7410 retain count 0x2400.

**Expected:** Copy the bounded byte range, advance addresses and exhaust count.

**Actual:** Now Working remains; over 1.9 million reads retain count 0x2400 in the initial probe. ADC input and recording-position reads are independently unsupported; DMA completion alone does not qualify recording.

**Evidence:** Private m3-sampling-discovery/trace.json and started.png; native verifier accompanies closure.

**Resolution:** Implemented the observed synchronous A7 inverse of BC with complete range/even-count validation and pointer/count advancement. `verify_native_sampling_dma.py` fails on the preserved prior binary and passes on the rebuilt driver, reaching waveform review and End. Normal native playback/release, exact131072-frame/display traced replay and307 backend tests pass. This closes the DMA stall only; live ADC, recording-position reads and physical timing remain open. See [qualified sampling profile](../emulator/guides/native-sampling.md).

### BUG-042 — Closing standalone discards dirty media without recovery

- **Status:** FIXED
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Codex Milestone 3 lifecycle audit

**Summary:** Closing the standalone after firmware Save but before export discards controller changes unless the user separately saved a session. Native child failure also recovers only the last explicit save.

**Repro:** Complete a firmware Save (dirty revision134), close/reopen the standalone without export or Save session. The prior close path only stopped transports and destroyed the runtime.

**Expected:** Periodic separate recovery and a close checkpoint retain sampler/dirty media; failures are visible and normal desktop close is cancelled rather than losing work silently.
**Actual:** Pre-change no periodic or close checkpoint existed.

**Evidence:** Five new lifecycle tests fail before implementation with missing recovery API. Final native dirty revision134 replay compares131072 stereo frames and both displays exactly; child-failure and normal-close/reopen exports match, and injected close-save failure retains the previous archive/running dirty state.307 backend/115 React tests pass. Two actual packaged browser workflows verify the production60-second timer, startup preservation for61 seconds, confirmed restore and explicit quit. Actual WebView close writes a recovery checkpoint and exits0. Durable evidence: `docs/condensed/validation/standalone-auto-recovery-2026-10-12.json`.

**Resolution:** Added separate recovery checkpoint scheduling and normal-close capture, visible timestamps/errors, preserved startup/restart/settings/manual-restore history, explicit restore/new-history/quit actions and close cancellation on save failure. Manual saves and library originals remain independent.

**Notes:** Recovery is bounded by its last successful checkpoint, not lossless recovery of a killed process. Busy disks/connected external MIDI can defer snapshots; audio pauses during capture. Power-loss/zero-loss journaling, plugin autosave and SCSI workflow qualification are not claimed.

### BUG-041 — Format Track success without media mutation

- **Status:** FIXED
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Codex Milestone 3 source audit

**Summary:** The native FDC FORMAT TRACK case prepares a successful result but consumes no track IDs, fills no sectors and changes no media revision.

**Repro:** Inspect `fdc_execute_command`, case `0x0D`, in `mame-source/src/mame/roland/s760.cpp`. The writable inserted-media path immediately calls `fdc_start_result_phase(7)`.

**Expected:** Validate and transfer format descriptors, format controller-owned media, and expose failures and dirty state.
**Actual:** Before the fix, success with no formatting. Write-protect/no-media rejection was fixed separately in BUG-040.

**Evidence:** `python scripts/verify_native_media.py --format --checkpoint` fails before implementation: Format did not fill every sample/data sector. Native OS 2.24 trace at physical0188E4 supplies command4D, FA RAM DMA count0024 from083E0E, SC09 and fill0F. Final native run `media-verification-20261012-065549` verifies protected Format leaves bytes unchanged; writable formatting reaches revision161 with 733184 exact fill bytes, formatted dirty cold recall is exact, and subsequent Save/export/fresh reload preserves 119808 sample bytes plus peak1459/silent release.

**Resolution:** Validate whole CHRN sets and DMA/media bounds before track fill; advance native DMA and dirty revision on success, reject malformed/unsupported transfers without mutation. 294 backend tests, native builds, lint/build, actual packaged Format/export/reconnect/restart/restore and desktop readback pass. Durable evidence: `docs/condensed/validation/standalone-formatting-2026-10-12.json`.

**Notes:** Closed for OS 2.24 standard720KB native DMA formatting. HD/foreign layouts, PIO and physical controller timing are not qualified. Recovery beyond explicit saved sessions remains open.

### BUG-040 — Native floppy write protection missing

- **Status:** FIXED
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Codex Milestone 3 media qualification

**Summary:** The native floppy controller had no write-protect state, ST3 always reported ready/writable, and WRITE DATA never rejected a protected disk.

**Repro:** Before this change, `test_write_protection_uses_acknowledged_native_controls` fails because the runtime has no protection API. Driver source had no write-protect member or status bit.

**Expected:** Protected firmware Save reports Write Protected without mutating controller bytes; protection survives cold session recall and standalone displays acknowledged state.
**Actual:** Pre-change there was no way to protect inserted media.

**Evidence:** Private native acceptance `media-verification-20261012-063112`: firmware error screenshot, unchanged protected export, cold protection recall, then unprotected Save/export/fresh reload with 119808 exact sample bytes and peak PCM16 1459.
**Resolution:** Added controller protection state, ST3 WP/ready reporting, protected/no-media WRITE DATA/FORMAT rejection, native acknowledged controls, checkpoint serialization and standalone checkbox/readback. Final native acceptance includes the exact firmware error-region hash; packaged browser verifies protect/reconnect/restart/recall/unprotect. 294 backend and 114 React tests pass, as do native compilation, lint/build, development package audit and WebView readback. Durable evidence: `docs/condensed/validation/standalone-write-protection-2026-10-12.json`.

**Notes:** Protection is logical media state for the private controller copy; source filesystem permissions are independent. Writable formatting remains BUG-041. No physical timing or clean-machine release claim.

<!-- Add one "### BUG-NNN" block per bug, newest at the top of this section. -->

### BUG-039 — Missing source sample blocks saved-session recovery

- **Status:** FIXED
- **Severity:** S3
- **Area:** bridge
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Codex, `test_restore_after_failed_start_does_not_require_source_sample_disk`

**Summary:** Restore is blocked by the generic startup-error guard and by native startup validating an obsolete sample source, despite the checkpoint containing the floppy bytes.

**Repro:** Save a standalone session, remove/relocate its configured sample image, let the child stop, then restore with that old sample path and a startup error.

**Expected:** Preflight firmware/build identity, launch without the source sample image, and restore embedded media.

**Actual:** Generic Runtime settings error or missing-file startup rejection prevents restore.

**Evidence:** Regression in `tests/test_standalone_sessions.py`; native relocated-session acceptance reproduces 131072 stereo frames and both displays exactly. Real browser restores from missing-library startup and rejects incompatible archives without changing the live patch.

**Resolution:** Restore bypasses the startup-error guard, clears the obsolete initial sample path after archive preflight, and clears startup error only after successful state load. Firmware and SCSI prerequisites remain validated. 287 backend and 113 React tests pass.

### BUG-038 — Normal-speed native acceptance deadline shorter than wait

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-12
- **Resolved:** 2026-10-12
- **Reported by:** Codex, Milestone 3 system-audio acceptance

**Summary:** The verifier's accelerated-time helper always allowed 30 wall-clock seconds, including a 35-emulated-second load wait. Normal-speed output necessarily exhausted that deadline.

**Repro:** `python scripts/verify_native_runtime.py --system-audio --audio-backend wasapi --audio-latency-ms 60 --state-dir docs/ic20-hle-findings/chatGPT-work/m3-wasapi-60ms` with local OS 2.24, IC15 ROM and ROBOFULL fixture.

**Expected:** Normal-speed waits allow their requested duration plus bounded overhead.

**Actual:** `TimeoutError: Machine stopped advancing` during the 35-second wait, despite advancing emulated time.

**Evidence:** Private `m3-wasapi-60ms/runtime.log`; corrected run in `m3-wasapi-60ms-final`.

**Resolution:** Deadline includes requested duration for system-audio runs. Normal-speed WASAPI firmware load/play/release and clean shutdown pass; accelerated regression remains unchanged.

### BUG-037 — WAV timeline assertion after checkpoint rewind

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-11
- **Reported by:** Extended native rack recall acceptance

**Summary:** Adding repeated checkpoint recalls to the existing native smoke test invalidated its assumption that external WAV offsets equal guest emulated time.
**Repro:** Combine `--rack-dials --pull-render --scheduled-midi` in the extended test.
**Expected:** Test note-off at the actual captured interval.
**Actual:** Gain/recall checks pass, then a wrong WAV interval produces a false sounding-tail failure. The external writer continues forward across guest rewind.
**Evidence:** native156-final.log in private scratch; original native156-dials3.log passed with fewer rewinds, illustrating why that pass was insufficient.
**Progress:** Separate the recall qualification from monotonic WAV qualification. Dial test verifies note-off directly through native float PCM and rejects incompatible flags; final separate runs pass.

**Resolution:** Recall and monotonic-WAV qualification now run separately. The final dial test verifies direct PCM release, exact non-unity replay and restored encoder position; the independent baseline passes WAV alignment and scheduled MIDI.

### BUG-036 — Worker display cache omits output level

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S3
- **Area:** bridge
- **Opened:** 2026-10-11
- **Reported by:** SoundCheck rack-knob acceptance

**Summary:** Native gain changes reach MAME, but audio-streaming display snapshots only copy pixel buffers and time, leaving output level at its default 100.
**Repro:** Set Output to 50% in the actual plugin editor while audio is streaming.
**Expected:** Telemetry and knob indicator report 50%, including editor reopen.
**Actual:** SoundCheck readback assertion fails. Native C++ regression reproduces: `Worker display cache lost output level`.
**Evidence:** Finding 156; audio156-dials.log and native156-cache-before.log in private scratch.
**Progress:** Copy level into the worker-owned display snapshot; native and real-host regression now pass.

**Resolution:** Worker snapshots now retain output_level. The new native C++ regression passes, and SoundCheck confirms 50% telemetry/indicator before and after editor reopen.

### BUG-035 — Output adjuster used digital override

- **Status:** FIXED
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** Native rack-dial acceptance

**Summary:** Initial in-development output routing called `set_value` on PORT_ADJUSTER, which MAME treats as a digital override.
**Repro:** `verify_native_runtime.py --rack-dials` on the initial knob implementation.
**Expected:** 50% gives half amplitude; 0% is silent.
**Actual:** Peak 0.069033 at requested half level, 0.044538 at minimum; comparison failed.
**Evidence:** Finding 156; native156-dials2.log and dial-audio.npz in private scratch.
**Resolution:** Use `ioport_field.user_value` for adjusters; initialize from the actual saved setting and restore it explicitly. Native comparison now gives zero half-gain error and exact silence. This tests software gain, not analog potentiometer taper.

### BUG-034 — Synchronous UI test measured host scheduling

- **Status:** FIXED
- **Severity:** S3
- **Area:** tests
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** React regression during concurrent compilation

**Summary:** A test inferred synchronous emission from an asynchronous user-event gesture taking under 100ms wall time.
**Repro:** Full Vitest run while native/C++ builds execute.
**Expected:** Verify event emission happens inside the dispatch.
**Actual:** Gesture took 118ms and failed despite exactly one synchronous emission.
**Evidence:** ui156-tests.log in private scratch.
**Resolution:** Dispatch a click synchronously and require the event before dispatch returns, without advancing timers. This is a functional ordering test; it makes no measured latency claim.

### BUG-033 — Intermittent cold restoration connection failure

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Reported by:** Final native plugin state acceptance

**Summary:** Cold restore can fail before publishing its checkpoint file, despite earlier passing runs. Added exception diagnostics distinguish this from an identity or checksum rejection.
**Repro:** build/Release/s760_native_plugin_tests.exe D:/S-760 docs/ic20-hle-findings/chatGPT-work/native157-state-diagnostic --state 48000 3 (use a fresh state directory for each run).
**Expected:** Fresh pending-note and active-note instances restore and replay exact PCM.
**Actual:** First final run failed pending restore; instrumented repeat passed pending restore but failed active cold restore with Native runtime disconnected or timed out. No checkpoint file in the failing cold instance.
**Evidence:** chatGPT-work/native157-final-state.log; native157-state-diagnostic.log; associated private cold runtime.log files.
**Notes:** Earlier native157-state.log passed. Root cause remains under investigation; do not treat the timeout as proven hardware or firmware failure.


**Follow-up:** Diagnostic stage run and three consecutive repeats pass exact cold PCM at48kHz. Root cause of the two earlier failures is still unknown. Operation-specific exception diagnostics are retained.

**Investigation (finding 159):** Reproduced at the pause stage before checkpoint load, and then without any checkpoint in the smaller C++ `--startup-repeats` test. After 35 successful fresh instances, the next timed out with Winsock 10060 waiting for the four-byte response header. A second run with another instance active also timed out. The frozen instance's flushed diagnostic trace recorded no frame/pause callback; a different child continued servicing controls. This narrows the failure to fresh runtime/control startup, not archive decoding. Root cause remains unproven. Thirty immediate and eight delayed Python startup/pause cycles passed; several complete C++ cold-state repeats also passed. These passes do not close the failure. Socket errors now distinguish EOF from the Winsock code and remaining byte count. Temporary Lua traces were removed. New repro: `build/Release/s760_native_runtime_tests.exe D:/S-760 <fresh-private-dir> --startup-repeats`. See [validation](../condensed/validation/s2-loops-and-restore-2026-10-11.json).

**Resolution (finding 160):** A read-only stack capture from the stalled test child identified `sed1330_device::draw_graphics_scanline`, called by `update_text` before the first frame hook. The device constructor initialized only its busy flag; display enable, dimensions and other register storage were indeterminate. All scalar register fields now have deterministic initial values, with display off and character pitch 1. These are safe pre-configuration storage values, not claims about measured power-on registers. No firmware, vector, timing or timeout changes. The old binary failed twice during this investigation; the corrected binary passed two 40-launch stress runs alongside a running instance (80 fresh children), exact 240000-frame cold replay at48kHz, original-firmware boot/display/controls/audio/MIDI acceptance, 266 Python tests and six C++ suites. Temporary tracing was removed. See [validation](../condensed/validation/s2-startup-lcd-2026-10-11.json).

### BUG-032 — Plugin editor discovery ignores configured native root

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S3
- **Area:** ui
- **Opened:** 2026-10-11
- **Reported by:** Plugin configuration qualification

**Summary:** The native root locates the machine but editor discovery previously searched only four module ancestors and the host working directory. A plugin stored deeper in the tree required a separate S760_UI_URL override.
**Repro:** Load the concrete plugin from chatGPT-work/m2-webview-build/Release with an unrelated host CWD and no S760_UI_URL; set the native root to D:/S-760.
**Expected:** The editor loads from the configured runtime root.
**Actual:** The old resolver falls back to a relative file URL.
**Evidence:** resolve_frontend_url in core/src/s760_webview_host.cpp; existing SoundCheck runs supplied an explicit URL override.
**Implementation:** Per-instance percent-encoded editor URL follows the native configuration; existing explicit development override remains supported.

**Resolution:** The native constructor supplies a per-instance percent-encoded file URL from its configured root. Settings-only SoundCheck boot/editor/load/play/reopen passes with unrelated host CWD and no S760_UI_URL. See docs/condensed/validation/milestone-2-audio-config-2026-10-11.json.


### BUG-031 — Plugin recall loses media metadata

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Reported by:** Milestone 2 session serialization review

**Summary:** Version-1 native plugin state captures mounted bytes but omits library folder, inventory, browse selection and source-path label. Restoring into another machine leaves its startup labels unrelated to restored media.
**Repro:** Insert a sample, choose another browse item, save plugin state and restore into a fresh instance. Inspect the Gotek metadata.
**Expected:** Restored selection, configured library and insertion label correspond to the saved session; missing source files do not replace captured media bytes.
**Actual:** The old state contains no media metadata and the cold instance reports its own boot disk.
**Evidence:** NativePluginState v1 schema; new media-library round-trip and cold native replay regressions.
**Resolution:** Version-2 archive includes validated metadata; old states restore an explicitly unknown label. Native checkpoint bytes remain authoritative. Recursive scans and failed folder changes are transactional.


**Validation:** Recursive discovery, rejected scans without mutation, independent selection and old-state compatibility pass. Real SoundCheck retains uninserted selection across reopening. Cold native VST recall restores media metadata and 240,000 exact stereo frames at48kHz with private source/library relocated, including note-off and corruption rejection. Finding154 and docs/emulator/guides/native-media-library.md record scope. One pre-load timeout on the extended native test was followed by a fresh-directory passing retry; both logs are retained.

### BUG-030 — Absolute mouse coordinates drift after Menu/Exit

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Reported by:** Native Menu integration regression

**Summary:** Host pointer transport assumes fixed accumulated mouse motion. After firmware Menu/Exit, the requested screen position no longer agrees with the observed guest cursor. The new Menu switch exposed this limitation.
**Repro:** `python scripts/verify_native_runtime.py --panel-menu --state-dir docs/ic20-hle-findings/chatGPT-work/native155-menu-repro` with original firmware and current native binary.
**Expected:** Pointer request (150,60) reaches diagnostic CRT coordinate (300,120), as on fresh boot.
**Actual:** (237,160). Subsequent requests also drift; motion is delivered but the fixed absolute mapping is invalid after this panel interaction.
**Evidence:** chatGPT-work/native155-regression.log; probe155.log records five successive request/cursor pairs; fresh-boot baseline passes boot/load/MIDI/release.
**Notes:** Read-only guest diagnostics and physical input only. ROM disassembly establishes context-dependent sensitivity and cursor bounds; the adapter now observes these and current cursor position. Do not force guest coordinates to conceal this defect. Menu opening itself is verified in MAME and SoundCheck.


**Resolution:** Read-only OS 2.24 cursor/bounds/sensitivity translation sends normal bounded MU-1 input; no RAM/PC writes. Free-running and paused-render regressions, corner/reversal checks, loaded audio and native state replay pass. See docs/condensed/validation/milestone-2-audio-config-2026-10-11.json.


### BUG-029 — Native media input pulse too short

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Reported by:** SoundCheck native drive UI acceptance

**Summary:** NativeRuntimeClient released media controls immediately after the socket acknowledged setting an input, before MAME sampled the input on a frame.
**Repro:** Through the embedded drive dialog, insert valid ROBOFULL.IMG while SoundCheck processes audio.
**Expected:** Native driver acknowledges insertion and the drive displays its filename.
**Actual:** No media-status.json was produced; UI correctly reported failure, but the error was "Invalid native JSON response".
**Evidence:** Private soundcheck/152-rack/failed-ui.json includes exact requests and returned error.
**Resolution in progress:** Hold the input until driver acknowledgement, with bounded timeout and release. Never force emulated time or firmware state.

**Resolution:** Hold the media control until the driver writes its acknowledgement, then release, with a bounded timeout. Actual SoundCheck rejects a nonexistent path and confirms ROBOFULL.IMG insertion; no forced firmware state (finding 151).

### BUG-028 — Firmware-driven LCD status missing in CRT mode

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** mame-driver
- **Opened:** 2026-10-11
- **Reported by:** Hardware owner; read-only native bus trace

**Summary:** Owner confirms the real LCD retains content in Mouse+CRT mode. Earlier explanation that blankness was expected was incorrect.
**Repro:** Boot original ROM/system disk in native Mouse+CRT mode; inspect LCD frames.
**Expected:** Display firmware-authored LCD pixels, including the CRT-mode status.
**Actual:** Blank. Native F800/F802 trace records SYSTEM SET 31 85 07 1a 40 3f 20 00, SCROLL, external font writes, cursor-direction changes, DISP OFF parameter54, and final bare DISP ON59. Provisional handler loses display attributes and requires a new parameter on59; also wraps memory at4KB, assumes20-byte pitch, ignores cursor direction and external fonts.
**Evidence:** Private lcd152-trace.txt and lcd152/1.png; driver lcd_w/lcd_update; Epson SED1335 technical manual.

**Resolution:** Native LCD now uses the SED1330 device with matching data readback and corrected mixed-layer rendering. Original firmware boot LCD matches the independent bus replay pixel-for-pixel (zero differences); real SoundCheck shows Mouse+CRT status. This qualifies the observed boot path, not every LCD mode (finding 151).

### BUG-027 — Embedded rack controls and drive display

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** ui
- **Opened:** 2026-10-11
- **Reported by:** User

**Summary:** Embedded rack still exposes demonstration mode buttons and F1–F6; native matrix has Command, Mode, Exit, Shift, S1/S2, F1–F3 and arrows. Seeded Shift map is empty. Gotek receives blank placeholder pixels.
**Repro:** Open plugin in SoundCheck; inspect rack and attempt a Shift combination with a single pointer.
**Expected:** Native panel input, usable chord controls and truthful drive status.
**Actual:** Demo-only controls, no Shift shortcuts, blank OLED. LCD blankness is BUG-028; Mouse+CRT mode still has a firmware LCD status message.
**Evidence:** S760FrontPanel.tsx, shiftButtonMap.ts; native driver panel input definitions.

**Progress (2026-10-11):** Manual-verified native layout replaces demo controls. F1–F6 under LCD; original six-position navigation cluster; dedicated Home/Mark/Jump. Value and Output routing is qualified by native and actual SoundCheck acceptance in finding 156. Input remains disabled until the native ADC path in Milestone 3 exists. Menu now routes the schematic-confirmed SC0/SP4 switch and opens the real firmware menu; mixed panel/mouse coordinates are tracked separately as BUG-030. Gotek Up/Down/encoder browse session-entered paths; Select opens the prefilled insertion dialog. The bay is centered, and redundant Insert image text and rack-ear 1U labels are removed. Native SoundCheck validates F4 chord and rejected/accepted media requests; the later Value/Output qualification below completes the playback rack scope.

**Resolution:** The approved native playback rack now has functional Value/Output controls, Menu, F1–F6 and Shift actions, LCD and acknowledged Gotek media. Original-firmware edits, native gain/state and actual SoundCheck reopen/play/release pass. Input Level is retained explicitly as a Milestone 3 recording feature; it is disabled and not claimed implemented.

### BUG-026 — Embedded studio viewport and CRT active area

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** ui
- **Opened:** 2026-10-11
- **Reported by:** User, SoundCheck screenshot review

**Summary:** Default 1024x640 plugin client clips the 1440px rack below the fixed monitor. Native renderer draws200 rows in a240-row surface; doubling all240 exposes80 unused black display rows.
**Repro:** Open plugin in SoundCheck at default size; rack is below viewport and black band appears beneath firmware softkeys.
**Expected:** Full rack and monitor visible together; verified native active area fills the monitor.
**Actual:** Overflow requires scrolling and unused native rows fill the bottom of the CRT.
**Evidence:** User screenshot observation; crt_update native loop y<200 and screen size640x240 in mame-source/src/mame/roland/s760.cpp.
**Notes:** Preserve wire pixels and legacy240-line modes; qualify pointer mapping after presentation crop.


**Resolution:** 1480x900 embedded editor and fitted studio layout keep the full rack visible. CRT presentation crops the native unused rows while preserving wire pixels. Real SoundCheck screenshots before/after editor reopen confirm the result (finding 151).

### BUG-025 — Embedded live CRT mouse input missing

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** ui
- **Opened:** 2026-10-11
- **Reported by:** ChatGPT SoundCheck load-workflow audit

**Summary:** App's live CRT is pointer-transparent over demo click handlers; C++ accepts no explicit held native mouse message. Real frames therefore cannot be operated using the embedded CRT.
**Repro:** Open the plugin in SoundCheck, then inspect OP760Monitor and the C++ message enum; legacy MOUSE_CLICK is rejected in native mode.
**Expected:** Live CRT pointer movement and held left/right buttons operate the firmware, with release on blur/cancel/close.
**Actual:** Demo handlers receive clicks; firmware mouse button ports are not driven.
**Evidence:** Source audit; new frontend and bridge regressions plus native firmware load acceptance will verify the fix.


**Resolution:** Explicit native pointer/button handlers operate the real Disk/Load workflow in SoundCheck; loaded-sample playback, Menu/Exit handoff and editor reopening pass. Existing pointer-release unit coverage remains applicable. See docs/condensed/validation/milestone-2-audio-config-2026-10-11.json.


### BUG-024 — VST3 SDK ABI mismatch

- **Status:** FIXED
- **Severity:** S1
- **Area:** bridge
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT SoundCheck preparation

**Summary:** Local VST3 interfaces prepend a virtual destructor, use virtual inheritance and encode incorrect interface IDs. Factory queries claim unsupported interfaces, metadata and bus outputs are uninitialized, and the class category is not the SDK audio-effect category.
**Repro:** Compare core/include/s760/vst3_defs.h and the factory with the local Steinberg SDK; exercise exported factory from an independently SDK-compiled process.
**Expected:** SDK hosts can discover, instantiate and query the native plugin.
**Actual:** Repository tests share the faulty definitions and cannot establish SDK compatibility.
**Evidence:** Independent SDK probe under development; this is initially source evidence, not a SoundCheck runtime result.
**Notes:** Correct ABI before claiming real-host editor acceptance.


**Resolution:** Corrected Windows x64 GUID encoding, actual SDK interface IDs, nonvirtual inheritance and FUnknown method order; initialized factory/bus metadata and audio class category, rejected unsupported factory interfaces, and validated stereo negotiation. Independent SDK probe and SoundCheck native loading pass. Exported native factory/audio regression passes with exact 48kHz PCM. Full host playback/editor UX remains separately qualified; old malformed class IDs are not migrated. See [host checkpoint](../testing/milestone-2-progress.md).

### BUG-023 — Accepted panel and pointer messages are no-ops

- **Status:** FIXED
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT editor integration audit

**Summary:** C++ `S760Bridge::apply_message` groups panel/dial/pointer commands into a no-op case, although the MAME adapter has native input methods.
**Repro:** Inspect the switch in `core/src/s760_bridge.cpp`; accepted BUTTON_PRESS does not call the host.
**Expected:** Supported native controls route to the live machine; unsupported controls are reported.
**Actual:** Parsing succeeds without performing the input.
**Evidence:** Source audit; standalone uses a separate working Python route.
**Notes:** Embedded editor control qualification remains open until corrected and exercised.

**Resolution:** Native panel and normalized pointer commands now route to the host; mount returns its actual result. Invalid IDs/coordinates and unsupported legacy click/dial reject. Real firmware Mode-menu change passes through the bridge; complete React controls and host-visible errors remain open. See [native editor evidence](../condensed/validation/milestone-2-native-editor-2026-10-11.json).

### BUG-022 — Editor frame requests compete with native audio

- **Status:** FIXED
- **Severity:** S2
- **Area:** bridge
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT native editor acceptance

**Summary:** The concrete WebView2 editor polls native frames on the same serialized control connection as audio rendering.
**Repro:** `s760_native_editor_tests ROOT PRIVATE_STATE --paced-var 48000 12`, concrete WebView2 build, original firmware and ROBOFULL fixture.
**Expected:** PCM remains identical to the reference across editor open/close/reopen with no underrun.
**Actual:** Output underrun (fault 3) at block 374, started 142704 / completed 139698 frames.
**Evidence:** Local `chatGPT-work/editor-149-native.log`; real MAME, WebView2 and React, not a mock.
**Notes:** Investigating display snapshots delivered with worker render replies, avoiding separate UI control requests during processing. No delay increase or fabricated audio is proposed.

**Resolution:** Audio render replies optionally carry display snapshots; the UI reads a separate cached snapshot during processing instead of issuing competing frame requests. Native editor close/reopen passes at 44.1/48/96 kHz with exact reference PCM and zero drops. A run during a concurrent C++ build still underruns: arbitrary load robustness is not established. See [native editor evidence](../condensed/validation/milestone-2-native-editor-2026-10-11.json).

### BUG-021 — VST3 editor does not schedule frame updates

- **Status:** FIXED
- **Severity:** S2
- **Area:** ui
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT Milestone 2 integration audit

**Summary:** `S760Vst3PlugView::attached` opens the editor and `tick()` can pump it, but the view installs no UI timer and tick is not part of IPlugView.
**Repro:** Inspect attached/removed/tick in `core/src/s760_vst3_plugin.cpp`; only initial bridge frames are requested by controller open.
**Expected:** Periodic UI-thread frame delivery for the lifetime of an attached view, detached without stopping audio.
**Actual:** A generic host using only IPlugView has no frame-pump entry point. Initial frames can also precede asynchronous page readiness.
**Evidence:** Source audit, not a DAW observation. The WebView2 harness explicitly posts test messages; it does not test plugin scheduling.
**Notes:** Native-plugin editor integration remains open in Milestone 2. Any fix must keep UI transport outside realtime callbacks and qualify close/reopen with continuing audio.

**Resolution:** The concrete Windows editor controller installs a UI-thread timer at about 15Hz, waits for page readiness, and removes its registration before closing. The real WebView2 harness receives multiple automatically scheduled CRT frames, verifies no callbacks after close, and repeats after reopen. Native audio/DAW continuity remains a separate qualification gate.

### BUG-020 — WebView2 backend is a success-reporting outline

- **Status:** FIXED
- **Severity:** S2
- **Area:** ui
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT source audit

**Summary:** The gated C++ backend sets `m_created=true` without creating a WebView environment/controller, and discards outbound frames/messages.
**Repro:** Inspect `WebView2WebViewHost::create` and `post_frame_to_js` in `core/src/s760_webview_host.cpp` under `S760_HAVE_WEBVIEW2`.
**Expected:** A functioning embedded page, or explicit creation failure.
**Actual:** Success with no page. The default stub is separately identified as a test backend.
**Evidence:** Source inspection; no real C++ editor acceptance claimed.
**Notes:** Milestone 2 tracks implementation. Standalone uses a separate working Python host; the React embedded channel alone does not fix this backend.

**Resolution:** Concrete environment/controller, local asset mapping, bounded messaging, resize and cancellation implemented. `s760_webview2_tests` passes against the installed runtime for two open/close cycles. Actual native VST3 editor/audio host acceptance remains a separate gate.

### BUG-019 — Malformed native session JSON escapes the event handler

- **Status:** FIXED
- **Severity:** S3
- **Area:** ui
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT NativeStudio regression

**Summary:** NativeStudio parsed incoming text without exception handling or checking the media list shape.
**Repro:** Deliver `{bad` to the NativeStudio WebSocket message handler (mock transport).
**Expected:** Actionable error while allowing subsequent valid messages.
**Actual:** Uncaught JSON parsing exception before the fix.
**Evidence:** `google-ui/src/NativeStudio.test.tsx`, malformed session regression.
**Resolution:** Guard JSON parsing and session media shape; report invalid response and retain the message handler. No firmware behavior changed.

### BUG-018 — Audit report exclusion applies to nested files

- **Status:** FIXED
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** distribution gate review

**Summary:** The package scan skipped every file named PACKAGE-AUDIT.json, allowing a nested added file to escape the complete-tree check.
**Repro:** Add scripts/PACKAGE-AUDIT.json to a reviewed package.
**Expected:** The changed tree must fail qualification.
**Actual:** The old basename-only exclusion omitted the file from the manifest.
**Evidence:** Parameterized exact-tree regression includes this nested path.
**Resolution:** Exclude only the root generated report; nested names are hashed and checked like every other file. Release status is still recomputed from actual files, never read from a package-supplied report.

### BUG-017 — Native source media filter misses AIFF

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-11
- **Reported by:** final distribution source archive scan

**Summary:** Native source selection excludes WAV but did not apply the complete private-media suffix policy. An upstream FLAC AIFF test fixture was included in the candidate archive.

**Repro:** Scan native-source-145.zip with the package PRIVATE_SUFFIXES policy; 3rdparty/flac/test/foreign-metadata-test-files/AIFF-ID3.aiff fails.
**Expected:** The source candidate excludes every prohibited media suffix.
**Actual:** Final qualification correctly stops before authoring an approved manifest.
**Evidence:** Finding 145; final archive validation assertion. No Roland leak was identified.
**Notes:** Regenerate the archive with the full suffix policy and repeat clean-source validation.

**Resolution:** The source filter now covers every prohibited media suffix. All 27323 final source entries passed integrity/media scans, and that exact extracted archive rebuilt from scratch successfully. Final native boot/audio and desktop tests pass; 241 backend regressions pass.

### BUG-016 — Build-environment inventory misses actual bundled components

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-11
- **Reported by:** distribution qualification audit

**Summary:** The fixed Python notice list omits dependencies actually frozen into the desktop executable, including Jinja2 and MarkupSafe. Parent pywebview attribution also does not describe the separate Microsoft WebView2 DLL license.

**Repro:** Compare the fresh standalone build's PYZ-00.toc and COLLECT-00.toc against DEPENDENCY-INVENTORY.json. Observe jinja2 modules and WebView2 binaries without corresponding complete component-level notice accounting.

**Expected:** Identify the actual bundled inputs and copy available notices; retain explicit unresolved vendor obligations.
**Actual:** Inventory describes the build environment and can pass development checks with omitted bundled-component notices.

**Evidence:** Finding 145; private distribution-145 build records. New distribution inventory tests exercise notice discovery, binary drift, unknown binaries and unsafe output paths.

**Notes:** Public release remains blocked while missing third-party rights/source evidence is unresolved.

**Resolution:** Actual COLLECT/PYZ inventory and Vite module inventory identify shipped components. Exact upstream WebView2/Python checks, proxy_tools source/license correction and supplemental vendor notices close the omissions. Runtime DLL copies with unresolved package provenance are excluded. 241 backend regressions, frontend build/type checks, clean-source MAME rebuild and final desktop/native acceptance pass.

### BUG-015 — SCSI WRITE discards completed payload

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** disk
- **Opened:** 2026-10-11
- **Reported by:** SCSI device checkpoint acceptance

**Summary:** Existing WRITE(6)/WRITE(10) paths allocate a data buffer and acknowledge completion without copying it into the target disk image.

**Repro:** `python scripts/verify_scsi_checkpoint.py --state-dir <fresh-private-dir>` writes a generated 512-byte payload to LBA 0, then READ(6) observes the previous disk bytes. The device probe reports `writeback_supported: false`. It does not use or alter user media.

**Expected:** A supported successful disk WRITE changes the target sector, or reports a supported failure.
**Actual:** DATA_OUT completion moves to STATUS, but target contents remain unchanged.

**Evidence:** [SCSI state validation](../condensed/validation/native-scsi-state-2026-10-11.json); finding 144. Source: `scsi_w` DATA_OUT completion and `scsi_execute_cdb` WRITE cases.

**Notes:** Separate media-writeback objective; snapshot tests establish restoration of implemented state, not working firmware SCSI Save or hardware protocol fidelity. Needs range/read-only/sense handling and firmware save/reload acceptance.

**Resolution:** Completed WRITE(6)/WRITE(10) payloads now update the private emulated image at the requested LBA. Range errors return CHECK CONDITION with per-target sense; CD-ROM writes are rejected. Zero-count 10-byte commands complete without a data phase; WRITE(6) zero means 256 blocks. Incomplete/reset writes leave media intact. Pending offsets, sense and written image bytes survive warm/cold checkpoints. Generated-media device tests pass, including unchanged source files. This fixes discarded device payloads, not firmware Save/export-to-host qualification; that remains in Milestone 3. See [validation](../condensed/validation/s2-scsi-and-stack-2026-10-11.json), `scripts/verify_scsi_checkpoint.py`, and finding 158.

### BUG-014 — SCSI checkpoint loses in-flight response

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** mame-driver
- **Opened:** 2026-10-11
- **Reported by:** isolated SCSI checkpoint test

**Summary:** Controller registers restore, but dynamic transfer bytes and media were omitted.

**Repro:** `python scripts/verify_scsi_checkpoint.py --state-dir <private-dir>` issues INQUIRY, consumes 8 bytes, saves, replaces the buffer using REQUEST SENSE, then restores and reads the remaining 28 bytes. This is a device-level test, not firmware workflow acceptance.

**Expected:** Remaining response is byte-exact after restore.
**Actual:** Red test reports `SCSI response bytes changed after restore`.

**Evidence:** Private scsi-red2-144/result.json; finding 144.

**Resolution:** Registered stable maximum-transfer storage, device metadata and startup-sized media buffers. Partial CDB/data-in/data-out and cold media tests pass; native cold scheduled audio/displays and all-rate plugin replay pass. [Evidence](../condensed/validation/native-scsi-state-2026-10-11.json).

### BUG-013 — Failed native plugin restore allowed processing

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** core
- **Opened:** 2026-10-11
- **Reported by:** native exported-factory state acceptance

**Summary:** The new plugin state implementation only faulted an existing stream after a native apply failure. A fresh instance had no stream and could start processing after rejection.

**Repro:** Run `s760_native_factory_tests.exe . <private-state-dir> --state 44100`. The test wraps an invalid one-byte native checkpoint in a valid archive and loads it into a fresh native instance.

**Expected:** Processing remains rejected until a complete valid restore succeeds.
**Actual:** The red regression failed with `Failed native restore allowed processing`.

**Evidence:** Finding 143; private `state-failure-red-143.log`.

**Resolution:** Explicit failure latch set before worker shutdown and cleared only after a complete valid restore. Exported native-module tests pass at 44100/48000/96000 Hz, including rejection after invalid native payload and successful recovery with a valid archive. See [state evidence](../condensed/validation/native-plugin-state-2026-10-11.json).

### BUG-012 — Boot-ROM setup guidance had unsupported permissions and stale status

- **Status:** FIXED
- **Severity:** S3
- **Area:** docs
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT firmware setup audit

**Summary:** The boot README described third-party downloads as lawful for
hardware owners without evidence of that permission. Its version note also
called IC15 IC20 and said the now-tested v1.11/v2.24 boot pair was unverified.

**Repro:** Inspect the previous `roms/BOOT/README.md` sections “Where to obtain
it” and “Version note”; compare with the native boundary acceptance record.
This is a documentation audit, not a new hardware test.

**Expected:** State project distribution policy and verified firmware identity
without granting rights to third-party firmware or contradicting native tests.
**Actual:** Unsupported permission claims, obsolete qualification status and
incorrect chip labels remained in the setup instructions.

**Evidence:** [Firmware setup](../emulator/guides/firmware-setup.md),
[native acceptance](../condensed/validation/native-boundary-2026-10-11.json).
Finding 141. Local SHA-256 checks match both documented firmware identities.

**Resolution:** Replaced download recommendations with user-supplied firmware
instructions, removed blanket permission claims, corrected IC15 labels and
linked current native evidence. Working-tree documentation change only.

**Notes:** No license grant was created and no Roland binary was distributed.

### BUG-011 — README implied a nonexistent project-wide license

- **Status:** FIXED
- **Severity:** S3
- **Area:** docs
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT native-boundary source/package audit

**Summary:** The README BSD badge linked to a nonexistent root LICENSE and the
footer described the whole project as BSD-3-Clause, despite MAME's separate
whole-engine license and no explicit project-wide license file.

**Repro:** Inspect the old README license badge/footer, `Test-Path LICENSE`,
`mame-source/COPYING`, and the header of `mame-source/src/mame/roland/s760.cpp`.
This is a source-documentation audit, not a runtime or hardware test.

**Expected:** Preserve per-file notices and identify the actual distribution
status without implying a nonexistent project-wide grant.
**Actual:** Badge link was broken and the blanket license statement overstated
the license scope established by the checkout.

**Evidence:** [Boundary assessment](../emulator/runtime/native-boundary-qualification.md), finding 140.

**Resolution:** Replaced the badge with distribution status and rewrote the
footer to distinguish driver, complete MAME engine and missing project license.
No new license grant was created. Changes remain in the working tree.

**Notes:** Public distribution remains blocked; correcting prose does not resolve
project licensing or dependency/source delivery review.

### BUG-010 — Desktop package omitted full MAME licenses

- **Status:** FIXED
- **Severity:** S3
- **Area:** build
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** ChatGPT inspection of the finding 139 desktop package

**Summary:** The builder retained COPYING but omitted its referenced full
`docs/legal` texts. It also had no artifact identity/private-media audit or
enforced distinction between development builds and qualified releases.

**Repro:** Inspect the original `scripts/build_standalone.ps1` and the package's
`mame-source/docs/legal` directory; the latter was absent. No native execution
is required to reproduce this packaging defect.

**Expected:** Preserve all upstream MAME legal texts, report package identity,
exclude private media, and avoid presenting unqualified artifacts as releases.
**Actual:** Only COPYING was included; no post-assembly audit ran.

**Evidence:** `tests/test_package_audit.py` (7 tests),
`docs/ic20-hle-findings/chatGPT-work/package-audit-140.log` (private log), and
[boundary assessment](../emulator/runtime/native-boundary-qualification.md). Finding 140.

**Resolution:** Added notice collection and a post-assembly audit, exact runtime
and legal-text identity checks, private-fixture checks and development-only
labels. Release requests fail explicitly. All seven regressions pass, including
missing/changed licenses and binary, renamed firmware, session leakage and a
forged release report. Changes remain in the working tree.

**Notes:** Build-environment dependency inventory is not complete embedded-DLL
attribution or a license-compatibility decision; release review remains required.

### BUG-009 — Checkpoint save/load ran inside an emulated-timer callback (restored empty patch table)

- **Status:** FIXED
- **Severity:** S2
- **Area:** core
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-11
- **Reported by:** native-runtime browser regression (finding 139)

**Summary:** The native runtime's buffer checkpoint (`machine:buffer_save/load`)
could execute inside an emulated timer callback, which MAME's Lua binding warns
is a synchronization/timer hazard. Result: a real browser-visible defect — session
restore produced an **empty patch table** or failed to advance.

**Repro:** Native Studio, real Chromium, normal speed: firmware load → Save
session → Restore saved session; the restored CRT patch-table region did not
match the saved hash (3384624565).

**Expected:** restored patch table pixels identical to the saved session.
**Actual:** empty/partial patch table after restore.

**Resolution:** Runtime now handles checkpoint commands only from a **paused
periodic callback** and skips the first periodic callback after each pause (a
"pause grace" so the old timer returns before save/load). Deferring to the
periodic hook alone was insufficient. Fixed in finding 139; browser + native
PCM/display + MIDI-replay regressions pass. Caveat: the grace is a workaround
around MAME's frame-vs-periodic hook ordering, not a redesign.

**Evidence:** `chatGPT-work/session-grace-139.log`, `browser-test4-139.log`,
`regression-complete-139.log` (findings area, git-ignored).

**Notes:** Lua identity changed, so pre-139 checkpoint archives are deliberately
rejected (no migration). Related: findings 134/135 (checkpoint design), BUG-004.

### BUG-008 — Shared DSP engine source (`s760_core.cpp`) is not compiled into the library

- **Status:** FIXED
- **Severity:** S3
- **Area:** build
- **Reported by:** condensed docs 06/10 (code audit)

**Summary:** `core/include/s760/s760_core.hpp` + `core/src/s760_core.cpp` exist,
but `core/CMakeLists.txt`'s library source list **omits `s760_core.cpp`**, and
MAME defines its own separate `s760_sound_device`. So the "MAME and plugins share
one DSP engine" claim is false — the standalone core is not actually linked.

**Repro:** inspect `core/CMakeLists.txt` source list; `s760_core.cpp` absent.
**Expected:** either the shared engine is compiled/linked end-to-end, or docs/
claims stop asserting a shared engine.
**Actual:** reference model exists but is dead code; two DSP implementations.

**Notes:** fixing means explicit integration + compiled end-to-end verification,
not just adding another reference model. Low user impact today; it is a
correctness/architecture-claim defect.

- **Resolved:** 2026-10-14

**Resolution:** Corrected the stale LLE roadmap completion claim and diagram, canonical DSP/deployment references, CMake comments and reference header. Native standalone/VST3 share the modified MAME machine through isolated runtime processes, not the unlinked S760HardwareCore model. Its omission is deliberate; no extra renderer was linked. Native C++48kHz/variable-block run matches240000 reference frames with zero missed deadlines; stream/core/plugin units and392 backend tests pass. Evidence: docs/condensed/validation/bug-008-native-architecture-2026-10-14.json.

### BUG-007 — Generated coverage matrices claim coverage from tests that don't exercise that layer

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** tests
- **Reported by:** UI consolidation plan/assessment (condensed 07/08)

**Summary:** `docs/*_MATRIX.md` generators attribute UI elements to React
components and mark them "✅ Tested" by `tests/test_interactive_ui.py`, which
actually boots MAME and asserts on MAME-rendered screenshots — it never loads or
exercises the React components. The matrices (and README badges) therefore claim
coverage that no test provides. Symmetric risk: OS behaviour "verified" by
React-only or screenshot tests.

**Repro:** compare `scripts/generate_ui_coverage_matrix.py` /
`generate_exhaustive_matrix.py` outputs against the referenced test bodies.
**Expected:** each matrix row names a test that actually exercises that layer;
untested elements marked "⚪ Untested."
**Actual:** false "✅ Tested" provenance; 100% badges unsupported.

**Notes:** This is the project's recurring "honesty about layers" hazard; the UI
test automation roadmap (`docs/testing/ui-test-automation-roadmap.md`) is designed to fix
it by asserting per-layer. Fix the generators + regenerate, downgrade false rows.

**Resolution:** All four generators now use a shared evidence policy and were regenerated. Historical rows are explicitly unverified inventory, with no coverage percentage, invented owner/source-line claims or passing badges. Reviewed assertion examples distinguish image bytes, static source and mocked React controls; native/hardware qualification links to dated validation instead. Five report regressions check determinism, committed output freshness, removal of false claims and resolvable scoped selectors. The full Python suite passes 266 tests. Evidence: [S2 validation](../condensed/validation/s2-bugs-2026-10-11.json); finding 157.

### BUG-006 — Native floppy save/export: whole-wave-RAM compare differs by 347 bytes

- **Status:** WONTFIX
- **Severity:** S3
- **Area:** disk
- **Reported by:** finding 128

**Summary:** The decoded native OS Save/export path writes the sample payloads
correctly (all 13 sample payloads, 119,808 bytes for the 88-key patch, match
source exactly), but a whole-wave-RAM comparison still differs by **347 bytes**
around 0x1FA410 (name / high-memory records). The finding records
`whole_wave_ram_equal=false` and makes no session-equivalence claim.

**Repro:** native runtime, load patch → firmware Save/export → fresh machine
reload → compare entire wave RAM to source.
**Expected:** byte-exact whole-wave-RAM session equivalence.
**Actual:** sample bytes identical; 347 name/high-mem record bytes differ.

**Notes:** bus-cycle arbitration unimplemented; no library writeback/formatting.
"Dirty" tracking is controller-write based, not firmware Save completion. Related:
findings 128/129.

- **Resolved:** 2026-10-14

**Resolution:** WONTFIX as an invalid disk-reload/session-equivalence expectation. Current native reproduction still has347 changed bytes, all in high-memory metadata/name/ID/directory records (32MiB profile:0x1FF9810..0x1FFDFAA), while all13 sample allocations/119808 bytes and fresh firmware playback/release pass. A separate cold full-session checkpoint preserves every33554432 wave-RAM bytes exactly, including those metadata records. A disk Load rebuilds metadata and is not a session restore; altering the guest's reconstructed records to force equality would be incorrect. The media verifier now reports every changed range with before/after bytes and hashes, rejects size differences, and asserts full-wave equality for checkpoint recall. Originals remain unchanged. Evidence: docs/condensed/validation/remaining-bug-investigation-2026-10-14.json.

### BUG-005 — Moving/sweep filter unmatched; static HP analysis corrected

**2026-10-16 dynamic tests and CPU repair:** Shape/state forms and training-selected latching do not improve both directions; an unselected half-frame lattice gives negligible exploratory gains. BUG-092 corrects30 KB timing groups,49 isolated cases pass,39 legacy cases exact;495 full tests/runtime pass after fixing periodic-stage test sampling(BUG-093). Fresh matched frozen model2.024%opening/1.930%closing; affine update de-jitter2.021%/1.927%adds negligible gain. Target below1% remains unmet; native filter model unchanged. Next intermediate static-cutoff capture to separate mapping from dynamics. Evidence: docs/condensed/validation/filter-dynamic-residual-tests-2026-10-16.json and native-kb-control-state-time-fix-2026-10-16.json.

**2026-10-16 user acceptance target and refinements:** User target below1% waveform residual in both directions, retaining static/fast controls. Direction curvature improves means to2.014%opening/2.001%closing; target NOT met. Duration2..30ms selects existing10.844ms. Raw target bits4.029%/6.456%, nearest-four rounding6.572%/9.564% worsen this frozen model. Offline research data reused, native code unchanged. Keep OPEN. Evidence: docs/condensed/validation/filter-sub-one-percent-target-2026-10-16.json.

**2026-10-16 direction-specific frozen transfer:** Separate progression fits on first-pair training reduce mean opening3.913%to2.043%, closing4.058%to2.491%, with every take improving and all four later takes transferring unchanged direction parameters. Map/slew/floor/source/damping frozen; evaluation data historically reused. Offline advancing targets does not prove live-stream causality or physical clock error. No native change; next derive a causal reversal/command-aware coefficient response matching these gains. Keep OPEN. Evidence: docs/condensed/validation/filter-direction-transfer-2026-10-16.json.

**2026-10-16 third-method combinations:** Frozen short-plus-floor baseline5.771%opening/2.660%closing; bounded anchor-preserving map4.790%/3.173%, shared progression4.549%/3.985%, both3.913%/4.058%. These are useful opening/closing tradeoffs, not universally better models. First-pair training only, later transfer, reused evaluation data; optimizer budgets reached, scale near bound, intermediate static cutoffs unqualified. Final replay keeps physical slew fixed. Native combination remains unchanged; keep OPEN. Evidence: docs/condensed/validation/filter-third-method-combinations-2026-10-16.json.

**2026-10-16 short-plus-rounded trial:** Frozen offline combination gives opening5.774%/closing2.659% versus short-only5.795%/3.552%. Separate native opt-in built:478samples, signed floor eight fractional word bits, command gate, overshoot clamp/deadline snap. Default2,998,800 stereo frames exact; guest targets unchanged; both fast jumps reach exact target next frame;18,371 applied rows/zero drops confirm coefficient grid. All488 tests and native runtime pass. Reused analog research data and native functional qualification are not fresh hardware/resonant parity; keep OPEN. Evidence: docs/condensed/validation/native-short-rounded-cutoff-trial-2026-10-16.json.

**2026-10-16 native short-smoothing trial:** Separate opt-in 478-sample candidate implemented and built; default path preserves 2,998,800 stereo PCM frames exactly. Firmware cutoff trajectories unchanged; read-only applied trace proves both fast steps reach exact target on the next native frame, despite small lead-in-state waveform differences. All488 current tests and native runtime acceptance pass. This is not new analog or resonant parity; keep OPEN. Evidence: docs/condensed/validation/native-short-cutoff-trial-2026-10-16.json. Next compare actual candidate PCM against frozen analog/source controls.

**2026-10-16 scheduler and combinations:** Original ISR rearms at saved service-time TIMER1 +20000, exact across1808 rearms/1807 consecutive interval decompositions. This run averages68–71microseconds late per update, including prologue/masking/interrupt delay, not solely delivery latency; physical correctness and matched-state observer identity remain unqualified. Combined frozen timing and20ms/8bit rounding is worse than timing-only on all6 repeat ramps (closing4.323–6.354% versus1.741–3.328%). No production change. Next localize deadline-to-service delay with matched-state observation. Keep OPEN. Evidence: docs/condensed/validation/tvfstep-scheduler-combinations-2026-10-16.json.

**2026-10-16 causal transition-law tests:** Training-selected20ms/8bit downward increment rounding improves closing to4.954–7.293% but worsens every opening to2.903–3.207%. A shared cutoff-dependent slew also worsens every opening (3.155–4.219%) while leaving3.953–6.298% closing error. Both insufficient; no production change. Held/future-write causal checks pass. All6 isolated jumps are bracketed by commands0 and27; applying smoothing universally worsens step4 from0.318% to8.318% in the same-window fit. Investigate firmware update scheduling next; physical command/timing law remains unresolved. Keep OPEN. Evidence: docs/condensed/validation/tvfstep-transition-laws-2026-10-16.json.

**2026-10-16 repeated ramps accepted:**064504 WAV contains all8 expected takes, no clipping/nonfinite samples. Three openings retain2.105–2.756% evaluation residual; three closes7.779–10.188%. Closing scale1.00314034 selected on prior recording transfers to all new closes with1.741–3.328% residual. First new close selects1.00235386, frozen transfer to later closes1.746/2.760%. Direction-associated discrepancy repeats, but varying optimum does not establish a hardware clock law. Global20ms still worsens openings. Initial private clock-search false minimum rejected; qualified coarse/refined bypass calibration agrees at start/end. Test causal coefficient-transition behavior against repeat and step regressions next; no further capture requested now. No production change; keep OPEN. Evidence: docs/condensed/validation/tvfstep-repeat-hardware-2026-10-16.json.

**2026-10-16 exact ramp firmware audit:** All1204 cutoff calculations and442 scored counter calculations match independent integer replay. Both directions use stage3/divisor219 with opposite signed deltas8224, and similar native20.05ms cadence. An exact20ms offline schedule improves closing to2.505% but worsens opening to7.866%; reject a shared cadence correction. Only one hardware ramp per direction exists, so direction dependence remains confounded with per-take variation. Prepared136s repeat MIDI for unchanged TVF7CH disk, three ramps per direction plus start/end bypass. No production change; keep OPEN pending repeat capture. Evidence: docs/condensed/validation/tvfstep-firmware-audit-2026-10-16.json.

**2026-10-16 trajectory localization:** Opening-selected timing/cutoff corrections transfer poorly to closing (10.211% baseline to 9.504% evaluation). Independently fitting closing progression1.00314034 gives1.729%, while opening supports no comparable rate change. Full-history local-window alignments show closing drift -2.913ms/s (R-squared0.9952), versus nearly constant opening alignment. This localizes an effective control-trajectory discrepancy, not a measured hardware clock defect. Same-window local scores are diagnostic; historical evaluation is reused. Audit exact fixture firmware counters/stages/conversion next; no global/directional speed change justified. Keep OPEN. Evidence: docs/condensed/validation/tvfstep-trajectory-2026-10-16.json.

**2026-10-16 accepted seven-channel capture:** All11 intended hardware patch contrasts and audible releases are present, finite and unclipped. Same-session stationary endpoint evaluation errors0.270–0.289% low/0.070–0.076% high. Existing SVF with immediate targets fits three opening steps0.319–0.421% and three closing steps0.921–1.224% after refined constant alignment; source phase/gain fixed from later plateaus. Step scores fit the transition window and are not held-out acceptance. Initial large direction-dependent errors were alignment minima, not an established state defect. Slow rising/falling native-trajectory evaluation3.227/10.403%;20ms smoothing2.697/10.222%, rising-selected10.844ms transfers2.325/10.211%. Slow control trajectory remains unresolved; no production change. Keep OPEN. Evidence: docs/condensed/validation/tvfstep-hardware-controls-2026-10-16.json.

**2026-10-16 multichannel capture replacement:** User identified that the original disk enabled only part1. New paired TVF7CH image and type1 seven-track MIDI assign patches1..7 to channels1..7 and contain zero program changes. Original-firmware UI/Save confirms the routing fields; fresh Load and all11 channel-only takes pass expected held/step/ramp cutoff traces, silent releases and64512 exact sample bytes. Only10 performance-routing bytes change; all sound data is identical. Ableton output channels must be set explicitly per named track. The capture setup is corrected; physical filter mismatch remains OPEN. Evidence: docs/condensed/validation/tvfstep-multichannel-2026-10-16.json.

**2026-10-16 TVFSTEP hardware capture:** First Ableton WAV contains11 correctly spaced held notes, but all show essentially identical RMS/spectrum and no intended transition contrast. Reject this take for filter identification; program-change delivery is the suspected capture setup issue, not a demonstrated DSP failure. Preserve raw WAV; use explicit per-clip program settings or manual patch selection before repeating. BUG-005 remains OPEN. Evidence: docs/condensed/validation/tvfstep-ableton-capture-2026-10-16.json.

**2026-10-15 transition refinement:** Quiet-training duration fit selects19.6836ms, transferring unchanged to repeat with19.970/21.263% evaluation residual versus20.004/21.334% at20ms. A1024-frame ramp worsens repeat to24.682%. Ramping derived direct-I coefficients instead of cutoff also worsens both recordings (20.856/21.754% versus20.657/21.504%); stationary equivalence and causality checks pass. Fixed measured clock/gain1/damping85; historical evaluation blocks reused. No native or production-default change. These hypotheses do not close the remaining dynamic/control-law gap; keep OPEN. Evidence: docs/condensed/validation/filter-transition-refinement-2026-10-15.json.

**2026-10-15 native cutoff-ramp diagnostic:** Added off-by-default S760_NATIVE_CUTOFF_RAMP_CANDIDATE for software-counted LP target writes under001B;882-sample causal ramps initialized from101020, fast-command targets unchanged. Same-state disabled audio is exact across1,234,800 prior-build stereo frames; enabled offline replay is within5.00e-8, active-ramp save/restore4096 frames exact, bypass/static controls1,499,400 frames exact. Builds/core/plugin tests pass;404 pytest pass with0 skips; native bus replay131072 frames and both displays exact. Original resonant recording-band evaluation improves44.13/46.31% to19.99/21.35% using actual native coefficients, fixed source clock and training-only phase/alignment. This is not direct WAV acceptance or complete parity. Keep OPEN; default playback unchanged. Experimental checkpoints require matching ramp profile; managed cross-build guard remains enforced. Evidence: docs/condensed/validation/native-cutoff-ramp-2026-10-15.json.

**2026-10-15 frozen cutoff-ramp transfer:** A causal20ms coefficient ramp selected on Time8 MIDI37–39 transfers unchanged to unused MIDI40/43/47/51 (Time8/12/16/24). Evaluation errors fall23.92/27.48/22.94/9.14% to2.04/2.60/3.05/2.92% with training-only per-recording control phase; zero-phase ramp alone gives2.30/6.04/8.05/3.23%. All four native source replays agree within5.02e-8; future-write causality check passes. Time8 initial-state and oracle amplitude corrections explain much less. This supports an opt-in software-counted transition candidate, not decoded101018 semantics, fast-path parity, physical latency or resolution of the separate Time80 resonant residual. Native playback unchanged; keep OPEN. Evidence: docs/condensed/validation/time8-onset-discrimination-2026-10-15.json and control-ramp-transfer-2026-10-15.json.

**2026-10-15 onset/control discrimination:** Ordered write captures confirm the initial101020/22 cutoff companion and command-scoped TVF/TVA target writes. A cutoff-only diagnostic retaining the initial word improves Time4 MIDI35 startup35.285% to1.840%, but does not transfer to MIDI36 (54.754% to48.736%). Longer ramps regress already accurate later onset windows. Low-note source reconstruction lies outside the native candidate coverage; these are offline trajectory comparisons, not native acceptance. No command law or production change qualified; keep OPEN. Evidence: docs/condensed/validation/fast-command-discrimination-2026-10-15.json and dsp-companion-transactions-2026-10-15.json.

**2026-10-15 firmware/control-path audit:** Exact resonant fixture verifies1336 cutoff words against independent integer replay and raw register delivery;456 envelope counter rows match with0 mismatches. Its active rise/first decay are linear; later quadratic/release segments have zero delta and are not nonzero-shape qualification.7133 applied rows match words/scaling;413 active changes apply within1 native frame, excluding2 first/inactive sets. Read-only observer preserves2,249,100 original-fixture and926,100 survey stereo frames exactly. Firmware also writes DSP control101018, not interpreted by current native audio paths. Time4 survey takes a zero-software-counter/001A-command path; Time8/72 use software divisors4/139. This confirms an implementation gap to investigate, not a decoded command law or proof of the Time80 residual cause. No native/default change; keep OPEN. Report: docs/firmware/os/modulation-firmware-path.md. Evidence: docs/condensed/validation/resonant-firmware-path-2026-10-15.json and modulation-firmware-controls-2026-10-15.json.

**2026-10-15 transition/state-form checks:** With20ms/shared cutoff scale frozen, linear/log coefficient transitions and quantization before/after give quiet17.67–18.06% and repeat16.39–16.54%; no consistent gain. Equivalent stationary SVF/direct-I/direct-II/transposed-II forms agree within2.18e-13 at fixed428/2732 but moving fits16.32–18.07% do not consistently improve both takes. Native baseline exact; transition variants pass endpoint and future-write checks. Candidate cutoff428–2732 accounts47.33/42.32% of squared residual, so the remaining discrepancy is not confined above the static control points. Local moving errors there29.46/33.11% contrast with precise stationary endpoints; cause remains unresolved. No native change; keep OPEN. Evidence: docs/condensed/validation/cutoff-space-quantization-2026-10-15.json, moving-filter-realization-2026-10-15.json and resonant-cutoff-coverage-2026-10-15.json.

**2026-10-15 source-phase/trajectory separation:** With20ms causal ramp fixed, small linear excitation-phase drift fails to improve evaluation:20.045/21.429% versus20.004/21.334% baseline. Training-only cutoff scales give17.670/17.937%; both parameters give17.728/18.049%. Quiet-trained scale1.00251612 transfers unchanged to repeat evaluation16.417% with only repeat training alignment/phase recalibrated. Reverse scale transfer gives18.044% on quiet. Supports a shared effective cutoff-trajectory candidate, not a measured physical rate correction; coefficient mapping/transition law/dynamic state remain confounded. No clock or native playback change. Keep OPEN. Evidence: docs/condensed/validation/resonant-phase-trajectory-2026-10-15.json.

**2026-10-15 causal cutoff transition check:** Offline one-pole/ramp grids5/10/20/40ms use only received native cutoff values. A20ms linear ramp selected solely on quiet training blocks transfers unchanged to repeat: evaluation20.00/21.33% versus held44.03/46.25%, with gain1/damping85/independent clock fixed. Per-take training fits only constant alignment/source phase. Future-write perturbations leave preceding output exact. Rise/fall errors14.85/23.51% and17.24/24.87% leave a shared falling-sweep discrepancy. Native median changed-value cadence20.09ms is consistent with the selected duration but does not prove physical smoothing or delay. Coefficient-space offline candidate only; no native behavior change, historical evaluation blocks reused. Keep OPEN. Evidence: docs/condensed/validation/causal-cutoff-transitions-2026-10-15.json.

**2026-10-15 original resonant discrimination:** Reproduced ROBO_TVF patch04/MIDI60 plus stationary controls. Source flag leaves control/application timing identical and changes the known-phase-aligned native sweep0.554%, so it does not explain this separate failure. Fixed428/85 and2732/85 LP controls agree0.061–0.135% in later windows. Recording-band correction preserves roughly17.7–17.8% historical moving error. With actual native cutoff points and independently fixed source clock, held application gives44.03/46.25% versus19.14/20.59% for offline interpolation. This supports testing causal cutoff transitions; interpolation uses a future endpoint and is explanatory only, not a production model. Trimmed capture offsets do not measure physical latency. Keep OPEN; no native behavior change. Evidence: docs/condensed/validation/resonant-source-control-2026-10-15.json; report: docs/hardware/captures/resonant-filter-control-results.md.

**2026-10-15 opt-in native experiment:** S760_NATIVE_SOURCE_CANDIDATE implements the combined forward-loop source candidate, off by default. Disabled audio matches prior executable across1,543,500 stereo frames exactly; enabled audio matches offline candidate within5.05e-8 relative RMS. On/off control/application traces are identical. Core/plugin suites,404 backend tests and native131072-frame/display trace regression pass. Static BP/HP numerical checks pass again; original unity-source resonant analysis still gives17.898/18.038% residual and does not invoke the native experiment. Release continuity, half/quarter kernels and general playback are unqualified. Keep OPEN; production defaults unchanged. Evidence: docs/condensed/validation/modulation-native-source-2026-10-15.json.

**2026-10-15 waveform discrimination:** Shared bypass gain/clock across four source combinations and training-only constant capture alignment yield later-window30–1500Hz waveform errors4.30/4.60/5.77/7.67% for cubic+effective phase1 at MIDI72/73/77/83. Current source baseline gives62.53/86.23/49.85/49.77%. Unity MIDI60 is indistinguishable at4.17–4.18%, as expected when a source shift can be absorbed by capture alignment. No cutoff, coefficient or envelope timing fit; no production change. Per-take offsets differ, preventing absolute latency inference. Supports opt-in source experiment; keep OPEN. Evidence: docs/condensed/validation/modulation-source-waveform-2026-10-15.json.

**2026-10-15 wider source check:** Frozen MIDI73 bypass calibration and fixed source candidate predict moving RMS across23 selected keys spanning MIDI49–95 within0.067–0.441dB. Native baseline replay matches all23 within5.05e-8 relative RMS. Tested MIDI84/85/89/93/95 share pitch word65510, so upper keys do not extend source-speed coverage. RMS agreement does not establish waveform or modulation-duration parity; different model-specific bypass calibrations prevent isolating phase from these RMS rankings. No production change; keep OPEN. Evidence: docs/condensed/validation/modulation-source-wider-2026-10-15.json.

**2026-10-15 source-isolation follow-up:** Unchanged LP applied to physical bypass predicts static RMS ripple with0.165dB unfitted/0.149dB train-gain-corrected evaluation error. Source harmonics fold to tones1.864Hz apart at MIDI73, explaining slow beating without cutoff motion. Fixed existing cubic reconstruction plus effective1-source-sample phase, calibrated only on bypass, reduces30–1500Hz bypass waveform error to7.59% and predicts moving RMS with unchanged native coefficient trace within0.086dB. Additional keys74/75/76, not used to choose this source candidate, yield0.130/0.104/0.206dB RMS-curve error; offline native replay agrees around5e-8 relative RMS. This supports a source confound for the survey ripple, not a production fix or full modulation parity. Static waveform requires an additional2.846ms diagnostic alignment and still has3.05% residual; capture/path delay is unseparated. BUG-076 records an independent native WAV-origin assumption. Original resonant accuracy remains OPEN; no DSP/source/timing behavior changed. Evidence: `docs/condensed/validation/modulation-source-isolation-2026-10-15.json`.

**2026-10-15 physical static/bypass controls:** Requested MIDI73 static80 and bypass captures are unclipped/nonfinite-free stereo48kHz,3s hold/3s tail. Hardware static80 retains the slow ripple and near-opposed phase/depth mismatch seen in the moving case: descriptive1.86Hz RMS amplitudes0.91dB hardware/1.58dB native; bypass reduces them to0.086/0.087dB. Thus this particular ripple does not require cutoff movement and cannot alone establish a modulation timing error. Native trace confirms pitch word34716 exceeds the measured interpolation bound32768 and selects linear fallback; source reconstruction is a candidate confound, not a proven cause. Use existing bypass/static recordings to isolate source phase and stationary response before more hardware capture or production changes. Keep OPEN. Evidence: `docs/condensed/validation/modulation-hardware-controls-2026-10-15.json`.

**2026-10-15 native static/application discrimination:** Bounded opt-in trace observes completed filter writes and exact first applied sound-stream frames without changing equations/policy.166 changed active coefficient sets use matching words within one44.1kHz frame; source0 imports9216 exact bytes; trace on/off common-checkpoint renders match1,543,500 stereo frames exactly. MIDI73 static cutoff416/1042/2613 still produces roughly1.85Hz RMS ripple (diagnostic amplitudes1.62/1.58/0.69dB), versus0.087dB bypass. The ripple does not require cutoff movement in the emulator and cannot alone establish a modulation timing defect. MIDI73 also falls above the measured pitch interpolation upper bound; linear fallback is a candidate confound, not an isolated cause. Original moving/resonant mismatch remains OPEN. Next physical controls are only static80 and bypass at MIDI73,3s hold/3s tail. Native runtime, core/plugin and404 backend regressions pass after correcting private harness directories; no skipped tests. Evidence: `docs/condensed/validation/modulation-application-2026-10-15.json`.

**2026-10-15 louder MIDI73 repeat:** Physical V2 gain pilot raises held RMS23.5255dB with no full-scale clipping. After gain centering, hardware V1/V2 ripple repeats closely: exploratory fits1.870/1.868Hz,0.757/0.776dB amplitude and100.5/97.4degrees relative to their waveform starts. Native V1 reference remains1.849Hz/1.336dB/−86.5degrees. This supports a reproducible audio discrepancy rather than low recording level alone; trigger/clock and source phase remain unmeasured, so the cause and modulation parity remain INCONCLUSIVE. No production change. Evidence: `docs/condensed/validation/modulation-v2-gain-pilot-2026-10-15.json`.

**2026-10-15 MIDI73 correction:** User identified near-antiphase fluctuations in the survey overlay. MIDI73/Time72 has roughly1.85–1.87Hz ripple with different amplitude/phase and differing nearby spectral components. Similar overall rise slopes do not explain this mismatch. Native cutoff rises monotonically over0.2–2.7s while audio fluctuates repeatedly; individual RMS dips cannot be treated as envelope reversals. Cause remains unresolved (playback/phase, filter response or timing); the broad overlay summary overstated agreement. Evidence is appended to `docs/condensed/validation/modulation-speed-survey-2026-10-15.json`. Keep OPEN; no production change.

**2026-10-15 physical timing survey:** RoboSampler ZIP contains61 stereo48kHz WAVs, MIDI35–95,3s hold/3s release, covering16 TVF Time settings. Six complete midrange falls (Time16/24/32/40/48/56) track original-firmware native cutoff timing: hardware median durations0.2325/0.3825/0.5525/0.6900/0.9600/1.3000s versus native0.2386/0.4002/0.5604/0.7214/0.9821/1.3027s. RMS extrema differ from coefficient endpoints and shift with pitch/carrier beating; these exploratory results do not establish a systematic speed correction. Larger envelope trajectories overlay closely, so a large held-envelope speed mismatch is unsupported for this nonresonant fixture. Slow settings are censored; TVF release/LFO/TVA and resonant waveform accuracy remain unqualified. No DSP/timing change; keep OPEN. Evidence: `docs/condensed/validation/modulation-speed-survey-2026-10-15.json`; explanation: `docs/hardware/captures/modulation-speed-capture-results.md`.

**2026-10-15 timing capture preparation:** User suspects modulation speed rather than filter DSP. `scripts/build_modulation_speed_capture.py` now consolidates the survey and all128 TVF envelope Time settings on one MODALL disk:22 patches/128 partials/23 sample slots, with every patch mapping MIDI21–108. This supersedes the initial seven-disk capture layout. RoboSampler SoundFont captures and note/settings maps will test stage duration and keyboard dependence before revisiting filter fits. Image geometry/key maps/envelope bytes verified. The consolidated disk loads through original native firmware and passes11 representative playback cases after CC7/CC10 initialization, including low/high keys and Time127. Hardware timing remains unmeasured. This is an experiment for existing BUG-005, not a confirmed cause or fix; status remains OPEN.

- **Status:** OPEN
- **Severity:** S3
- **Area:** dsp-audio
- **Reported by:** findings 87–95, 108

**Summary:** Moving/sweep resonant response remains unmatched and topology/update timing are not uniquely identified. The former static-HP1.59% failure was a capture-analysis aliasing defect: retaining recording-band DAC images gives withheld0.10408% HP and0.07924% BP with unchanged428/85 equations. Static C64/R64 waveform accuracy now passes the named1% target; the broader moving-filter bug remains OPEN.

**Repro:** compare the opt-in filter audition against the RoboSampler static HP
capture (cutoff 428, damping 85) and the moving-sweep captures.
**Expected:** HP within ~1% RMS; moving sweep matches hardware.
**Actual:** Static HP now passes after the measurement correction below; moving-sweep mismatch remains unresolved.

**Notes:** opt-in/diagnostic path only (`S760_NATIVE_LPF_MONITOR` etc.), not the
default audio. Fixed-point width, saturation, resonance feedback law and update
timing remain open. This is a fidelity gap in an experimental feature, hence S3.

**2026-10-14 investigation:** A new timing-only diagnostic fits affine phase drift on four training windows between1.0 and2.4s, then forecasts the untouched3.0..4.5s interval using the fixed428/85 recurrence. Withheld BP residual is0.0789% and HP1.1311% (previous fixed-rate HP1.5925%). HP still fails1%; moving/resonant mismatch is not resolved. No held-out refit or native DSP coefficient change was made. Keep OPEN; this is diagnostic measurement-chain evidence, not filter accuracy closure. The renderer is now enabled by supported native launchers; the old opt-in-only note above is historical. Evidence: docs/condensed/validation/remaining-bug-investigation-2026-10-14.json.

**Static-HP partial resolution (2026-10-14):** The old4096-point folding collapses frequencies above the source Nyquist that remain in48kHz hardware captures. Fractional phase shifts and frequency-dependent filter transfer then operate on aliased harmonics. The corrected8192-point analysis retains recording-band image harmonics, applies phase in physical source samples and fits timing/gain on1.0..2.4s only. Untouched3.0..4.5s yields0.10408% HP and0.07924% BP;16384-point/16x reconstruction yields0.10382% HP. Old4096-point analysis reproduces1.5898% HP; wrong cutoff430 yields29.6755% HP, so the correction does not simply hide model errors. No native coefficient or renderer change was made. Reproduction: scripts/verify_static_filter_captures.py; evidence: docs/condensed/validation/static-filter-capture-correction-2026-10-14.json. This supersedes the earlier static residual claims and timing-only follow-up; keep OPEN for moving/resonant response.

**Moving-response follow-up (2026-10-14):** Rechecked accepted quiet130922 and repeat133400 captures with fixed damping85 and unity gain. Exact Fourier fractional excitation alignment yields evaluation errors17.898%/18.038%, versus linear alignment17.627%/18.444%; the improvement does not transfer consistently. Stepped coefficient updates and fixed32/64/128-sample cadences worsen the evaluated fits. The evaluation blocks have already been reused for historical model comparisons and are not fresh independent validation. No renderer/timing/saturation change is justified. Keep OPEN: the cutoff timestamps are an emulator trace, not hardware measurements. A native-rate digital capture with bypass/static/sweep controls, or synchronized hardware coefficient writes, is the next discriminating evidence. Full parameters/input hashes and limits: docs/condensed/validation/moving-filter-investigation-2026-10-14.json.

**Analog capture kit prepared (2026-10-14):** TVFSTEP.IMG supplies bypass, fixed low/high controls, delayed up/down steps and slower ramps. Eleven native takes, including three of each step, pass with identical control endpoints and intact sample/media bytes. The187second MIDI sequence matches the verified control messages and note timing. Hardware captures remain pending; BUG-005 stays OPEN. See docs/hardware/captures/tvf-transition-capture.md and docs/condensed/validation/tvf-transition-capture-2026-10-14.json.


**2026-10-16 current-build timing localization:** Fresh matched checkpoints qualify read-only observer transparency in two22,050-frame opening/closing windows (observed=baseline=repeatedbaseline, zero dropped rows). All48 modulation rearms use saved serviceTIMER1+20,000. Mean periods20.071802/20.068255ms; mean delivery delays63.078/59.563us, maxima130.375/123.125us, constant9.125us prologue. All24 delays above2us deliver after004B:5811POPA at5812; sampled globalI is clear during the precedingF008 mouse handshake. This is a native cadence contributor, not hardware timing/error proof or a complete filter cause. Both directions show similar slowdown, so no global/direction-specific production correction is justified. Status remainsOPEN. [Exact matched evidence](../condensed/validation/filter-scheduler-localization-2026-10-16.json); [explanation](../firmware/os/modulation-firmware-path.md).


**2026-10-16 verifiedCPU timing correction:** SeparateBUG-091 fixed six nativeKB instruction timings(CLRC,SETC,DI,EI,CLRVT,NOP) from4states to Intel2. CPU differential execution2048-instruction blocks now512us versus1024us before.478 tests/native runtime pass;4 known source-builder expected failures remain. New same-state observer controls preservePCM exactly; measured periods20.009266/20.009078ms and prologue8.875us. Different fresh-run phases prevent treating this as a controlled cross-build waveform comparison. KeepBUG-005 OPEN pending resonant/ramp/step hardware rerun; no DSP/filter coefficients or firmware altered. [Evidence](../condensed/validation/native-kb-state-time-fix-2026-10-16.json).


**2026-10-16 fresh post-repair hardware comparison:** Existing six repeated ramps and unchanged frozen10.844ms diagnostic law, scale1/no fitted speed, give closing2.870/2.831/4.961% versus historical7.830/7.779/10.188%, but opening6.281/6.155/4.934% versus2.756/2.143/2.105%. This mixed result rejects treating the CPU repair as a completefilterfix. Different native phases/build histories and reused hardware data remain qualifications. KeepOPEN; next test companion101018/coefficient-transition semantics. [Evidence](../condensed/validation/filter-hardware-after-kb-timing-fix-2026-10-16.json).

### BUG-004 — Experimental IC4 MIDI vector response is inferred/forced; no real arbitration or FIFO

- **Status:** FIXED
- **Severity:** S2
- **Area:** midi
- **Opened:** 2026-10-11
- **Resolved:** 2026-10-17
- **Reported by:** findings 73/74

**Resolution (2026-10-17):** Implemented natural IC4 priority arbitration and a 64-byte FIFO buffer in `mame-source/src/mame/roland/s760.cpp`:
1. Vector `0x203A` dispatches external interrupts via table pointers at `0x0120 + 4 * source` with priority ordered strictly as Source 0 (FDC) > Source 2 (Wave) > Source 4 (SCSI DMA) > Source 6 (MIDI RX).
2. Replaced the single-byte latch in `rcv_complete()` with a 64-byte circular FIFO queue (`m_native_midi_fifo`), eliminating dropped bytes and unsupported overruns when `source6` (bit 6 of `m_bank_regs[0x15]`) is masked or when higher-priority interrupts are being serviced.
3. Reading MIDI data port `0x116` advances the FIFO head and performs an active low pulse deassertion followed by reassertion on `i8x9x_device::EXTINT_LINE` to generate a fresh rising edge for the 80C196KB CPU whenever queued bytes remain.
4. Added full checkpoint serialization for all FIFO state variables (`m_native_midi_fifo`, head, tail, count) via `save_item`, and initialized FIFO state in `machine_reset()`.
5. Added unit test suites `test_bug004_ic4_midi_fifo_and_priority_arbitration` and `test_ic4_priority_and_fifo_queuing_behavior` in `tests/test_gate_array_mame.py`. All 517 test suite items pass with zero regressions.

**Summary:** MIDI receive works only under the opt-in `S760_IC4_MIDI_EXPERIMENT`
path, which **substitutes the external-interrupt vector low byte** (source6 →
0138) based on an inferred model of IC4 behaviour — not measured hardware. A
one-byte latch stands in for the real receiver: a second byte arriving before
consumption is logged as an **overrun and dropped**. Source priority, latching,
reassertion under concurrent sources, FIFO depth and MIDI-out are unestablished.

**Repro:** `S760_IC4_MIDI_EXPERIMENT=1`, send MIDI faster than the firmware
consumes it → dropped bytes; concurrent FDC + MIDI interrupts → unverified
arbitration.
**Expected:** faithful IC4 receive/interrupt behaviour, including measured buffering,
overrun and vector/arbitration semantics. A FIFO must not be presumed without evidence.
**Actual:** inferred vector substitution + single-byte latch with logged overrun
drop. The raw driver flag is off by default; supported native launchers explicitly
enable this experimental profile, so standalone/plugin MIDI receive does work.
This does not establish hardware arbitration or FIFO depth.

**Notes:** three-voice and 24-voice polyphony were demonstrated through this
experimental path. Do NOT promote to default emulation until real IC4
arbitration/buffering is resolved. Related: BUG-009.

**2026-10-14 investigation:** Current original-firmware ROBOFULL allocator/retrigger/sustain qualification passes24 voices and eight recycled slots. Diagnostic MAME logging records252 received serial bytes and zero unsupported overruns. This does not reproduce a supported-profile byte-loss failure or establish physical IC4 arbitration/FIFO depth. No guessed FIFO, synthetic IRQ or serial timing change was added. Keep OPEN for the unresolved hardware receive/vector/buffering contract. Evidence: docs/condensed/validation/remaining-bug-investigation-2026-10-14.json.

### BUG-003 — Unrecognized sample loop/direction mode flags are silently dropped

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** dsp-audio
- **Reported by:** findings 101/102/104

**Summary:** The native wave monitor explicitly accepts only control high-nibble
4 and forward inclusive looping, and **rejects/ignores other loop & direction
mode flags** (e.g. reverse, alternate, one-shot variants, flags like E000). A
valid patch using an unsupported mode can therefore play **silent** even though
the filter/pitch paths match well — a silent-failure that can hide behind
apparent success.

**Repro:** native audio audition with a patch whose sample mode byte selects a
non-forward loop/direction; the voice produces no output.
**Expected:** all seven documented loop/direction modes render (finding 103/104
decoded them: Forward End, Forward Release, One Shot, Forward One Shot, Alternate,
Reverse One Shot, Reverse Loop; boundaries end-exclusive, reverse −4 offset).
**Actual:** unrecognized modes skipped → silent voice.

**Notes:** finding 104 implements the seven modes behind `S760_NATIVE_LOOP_MONITOR`
(opt-in); the default monitor still skips them. Physical interrupt timing/ack and
fractional-pitch coverage remain provisional.

**Resolution:** The supported Python and C++ runtime launchers already enable interpolation, which enables the existing loop implementation. Added a firmware-driven `--loop-modes` acceptance against the identified ROBOLOOP fixture. All seven modes produce PCM; five repeating modes match the expected forward/reverse/alternate sign sequence exactly, the two one-shots stop while held, and all modes end in silence after note-off. This closes the stale default-profile silence report at 44.1 kHz/unity pitch, not complete-chip parity or other clocks/flag combinations. No new DSP behavior was introduced. See [validation](../condensed/validation/s2-loops-and-restore-2026-10-11.json); finding 159.

### BUG-002 — BMOVI (0xCD) retains the duplicate operand-fetch bug; unaudited

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** cpu
- **Reported by:** findings 64/65 (BMOV/CMPL audit)

**Summary:** The generated MCS-96 core double-fetched operand bytes for block ops
(after `direct_2w` already fetched them), consuming the following instruction.
This was fixed for **BMOV (0xC1)** and **CMPL (0xC5)**, but **BMOVI (0xCD) still
has the same duplicate-fetch pattern** and is explicitly unaudited; its KB
applicability / interrupt semantics must not be assumed from later 196 variants.

**Repro:** execute a BMOVI instruction path (not covered by the current TX81Z
load path) → operand over-fetch corrupts the following instruction.
**Expected:** BMOVI fetches operands once, per the 80C196KB User's Guide.
**Actual:** duplicate fetch (latent; not yet hit by exercised firmware paths).

**Notes:** audit separately with an isolated CPU fixture before any path uses it.
Fixed siblings: BMOV, CMPL (verified by fixtures).

**Resolution:** Removed the two opcode-body read_pc calls already performed by direct_2w. The rebuilt MAME passes the isolated zero/one/three-word fixture, bounds, pointers and following-instruction sentinel; the pre-fix binary aborts with Unhandled 10 (feb6). Original-firmware boot/load/audio/pull-render/scheduled-MIDI acceptance also passes. This closes the operand-fetch defect only: interrupt restart, timing, count semantics and physical KB applicability remain unaudited. Evidence: [S2 validation](../condensed/validation/s2-bugs-2026-10-11.json); `scripts/verify_bmovi_fetch.py`; finding 157.

### BUG-001 — MCS-96 PUSHA/POPA/PUSHF/POPF are stack-neutral no-ops

- **Status:** FIXED
- **Resolved:** 2026-10-11
- **Severity:** S2
- **Area:** cpu
- **Reported by:** findings 23/25 (boot bring-up)

**Summary:** In `mcs96ops.lst`, PUSHA/POPA are stack-neutral and PUSHF clears
PSW + checks IRQ while POPF leaves PSW/SP — i.e. the flag/register save-restore
instructions **do not actually save/restore** PSW or the register set. This is a
deliberate boot-compatibility workaround (a real two-word PUSHA/PUSHF derails the
OS at 0xB93A / 0xE080 because routines PUSH at entry and plain-RET at exit with no
matching POP), NOT correct Intel architectural behaviour.

**Repro:** replace the stubs with real PUSHA/PUSHF semantics → OS derails during
boot (RET returns to a PSW-as-address). Current workaround = net-zero stack.
**Expected:** architecturally correct PUSHA/POPA/PUSHF/POPF.
**Actual:** stack-neutral no-ops; PSW/INT_MASK1 not preserved across the pair.

**Notes:** confined to the flat baseline per the native-mode notes; native 196KB
interrupt work added INT_MASK1/INT_PEND1 but the stack-op stubs remain. Do NOT
"correct" without re-proving the 0xB93A / 0xE080 paths. Any instruction audit
(see BUG-002) should cover these.

**Resolution:** Native mode already delegates to kb_push_flags/kb_pop_flags; the original report incorrectly generalized the legacy flat-mode workaround. Added an isolated I80C196KB execution test for PUSHF/POPF and PUSHA/POPA: exact SP deltas, saved PSW and INT_MASK1/WSR words, clearing/restoration, and stack guards pass. No CPU semantics changed in this closure. The unsupported flat bring-up profile retains its documented stubs; broader interrupt/timing fidelity remains unqualified. Native original-firmware acceptance passes. See [validation](../condensed/validation/s2-scsi-and-stack-2026-10-11.json), `scripts/verify_native_cpu_flags.py`, and finding 158.
