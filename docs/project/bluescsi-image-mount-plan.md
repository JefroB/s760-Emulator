# BlueSCSI folder browser and image mounting plan

**Updated:** 2026-10-21  
**Status:** IM1 IN PROGRESS. BUG-176 transition ownership is fixed in606e277e...;16 final-image native workflows pass, plus1123 backend tests/3 skips on the rebuilt diagnostic-capable emulator. A controlled hardware-test candidate is ready. Broader native state/alias and physical gates remain open.
**Hardware:** Roland S-760, BlueSCSI V2; user confirms the very latest firmware. Exact installed build and configuration still need capture.
**RC-100 scope (user decision, 2026-10-20):** Treat the untouched RC-100 implementation as assumed compatible. The user has no RC-100; its input testing is waived as an IM1 release gate. Preserve its code/selection path. This is an accepted assumption, not verified remote-input compatibility.  
**Next action:** Run the controlled hardware test using the [OS image/setup guide](bluescsi-hardware-test-guide.md), while retaining the open broader native-state/alias and target-fault proofs. The user confirms BlueSCSI is attached to the S-760 and is unavailable to this computer. Current606e277e... uses6760/8002 bytes (1242 free), retains GB-6 v9 and the existing boot ROM. [Current batch](bluescsi-im1-owner-and-recovery-results-2026-10-21.md). Full IM1 GO is not claimed.

This plan replaces direct WAV import as the first delivery objective. It carries forward the useful evidence from the [Files/Folders research roadmap](bluescsi-files-roadmap.md) without inheriting its unfinished sample-construction design. Earlier checkpoints remain historical evidence; their BS milestone numbers are not reused here. The old SD library-image proposal is also historical, not an implementation contract.

## Mount-command research result

The [source-backed mount/eject research](bluescsi-image-mount-protocol.md) confirms `DA`/`D7`/`D8` for image count/list/switch and `1B` for virtual eject/load in both reviewed stock revisions. It also establishes a constraint: the picker is hardwired to `CD<target ID>` and skips subfolders; `D9/02` does not redirect it, and `ImgDir` only controls a separate cycling path. Multiple target folders are supported within available IDs; arbitrary collection-folder switching on one target is not exposed by the reviewed SCSI interface. IM1 must resolve that collection mapping explicitly. Compatible IMG selection through the generic switcher is a source-supported test route, still requiring device-class/geometry and native qualification. No runtime implementation or mount acceptance is claimed by this source inspection.

See the [first IM1 batch results](bluescsi-im1-results-2026-10-19.md) and [native browser results](bluescsi-im1-ui-results-2026-10-19.md) for source, host-harness, guest-command and UI/load/playback evidence. These evidence classes remain separate.

## BlueSCSI filename source repairs (2026-10-20)

BUG145/146 are fixed in supplied local BlueSCSI firmware source patches: unified pre-display filename filtering/indexing, bounded terminated switch paths and explicit D8 errors. Both reviewed upstream revisions pass patch application and host execution (21 tests/10,002 assertions); the full backend suite passes1,110 tests with3 skips. [Patch package](../../patches/bluescsi-v2/filename-fixes/README.md), [results](bluescsi-filename-fixes-results-2026-10-20.md).

These patches are not installed on the user's BlueSCSI. The S-760 candidate, GB-6 v9 and32-byte/preflight profile remain unchanged. Actual-board firmware build/installation and device qualification remain separate gates; current stock-firmware limitations must still be observed. Full IM1 remains open; the later native BUG168 repair is recorded below.

## BlueSCSI failed-switch source repair (2026-10-20)

BUG137 is now closed as a source defect. The same filename patch already checks the D8 switch result; dedicated tests prove invalid-index/missing-directory/open failures return an error and explicit retry recovers the requested image.33 focused tests,36 error cases/36 retries and1,122 backend passes (3 skipped) qualify the local source patch. The two patch files are unchanged; an existing application already includes137/145/146. [Results](bluescsi-switch-error-fix-results-2026-10-20.md).

Source-defect closure does not close the installed-board/native recovery gates. Actual backing-open failure still follows upstream close-before-open, so the client must treat failed D8 media as uncertain and reselect explicitly. Physical build/installation/configuration and full IM1 safety qualification remain open; native BUG168 repair is recorded below.

## Intended workflow

Open **Image Library** from the native Disk interface, select a collection folder, select an image, mount it on an explicitly selected compatible library target, and enter the ordinary S-760 Disk Load workflow. The existing OS interprets the mounted media and loads its volumes, performances, patches, partials and samples. Mono and stereo content follows the native loader.

The collection contains hundreds of ISO images spread across multiple folders and one dedicated folder for IMG images. Supporting multiple folders is a first-release requirement. A single flat 100-image collection does not meet it. Browsing and switching must work without rearranging files or editing configuration for every selection.

Only images containing a format the S-760 can read qualify. An `.iso` or `.img` suffix alone does not establish filesystem, sector geometry, device class or compatibility. This feature does not expand sample RAM or add a new image-filesystem decoder.

## Required folder structure

The following is the **logical library layout**. Physical paths, BlueSCSI target-directory names and configuration are to be frozen by IM1; this example is not a claim that arbitrary paths can already be mounted.

```text
SD root/
    bluescsi.ini
    Existing boot and writable save images
    Library/
        IMG/
            Library01.img
            Library02.img
            ... up to 100 image files
        ISO_A/
            Disc001.iso
            ... up to 100 image files
        ISO_B/
            Disc101.iso
            ... up to 100 image files
        ISO_C/
            Disc201.iso
            ... up to 100 image files
```

- One dedicated `IMG` collection; as many ISO collection folders as needed within the qualified folder-index/path limits. There is no collection-wide 100-image limit.
- Each leaf folder holds at most **100 image files** and no subfolders. The user confirms the BlueSCSI per-folder maximum is 100; this plan accepts that fixed limit. Capacity grows by adding collection folders. Folder-only intermediate levels permit further grouping if the library root would otherwise exceed 100 entries.
- Allow at most **100 returned entries per directory total**, including folders and unsupported files. Apply the limit before filtering; 100 images plus an extra file would exceed it. Keep leaf folders restricted to their intended images. Parent/back navigation is a UI action and must not consume an SD directory entry.
- The first workflow requires root-to-collection navigation and back. General deeper traversal must have explicit path/depth bounds; no unbounded recursive catalog is proposed. Freeze and test those bounds in IM1 rather than implying unlimited nesting.
- Preserve actual protocol indices for selection; the packed candidate first validates all D7 indices as0..count-1 and retains them implicitly only if every record matches; displayed sorting/filtering must not turn row numbers into file indices. Re-enumeration invalidates cached indices. Duplicate names in different folders must remain distinguishable by full path.
- Show enough of the folder/image identity to distinguish truncated names. D7 returns32 name bytes including extension; the current screen shows32 printable ASCII characters (28 before `.iso`/`.img`). First-profile names should fit that visible bound. A59-byte full name is a bounded mount candidate in `CD<id>` folders, not an unconditional promise; see BUG-145/146 and the filename section of the protocol contract. Qualify prefix collisions, filter equivalence, SD preflight and actionable naming errors; D7 cannot return the hidden tail for scrolling.
- A directory above 100 entries must give an explicit error rather than silently hiding entries. Determine how overflow can be detected from the actual protocol; never mount a different file after truncation.

**The stock capacity question is resolved within available target IDs:** one flat `CD<id>` folder per configured target, up to100 images each. The concrete candidate below provides300 ISOs plus100 IMGs on four targets. The earlier preference for many arbitrary folders on one target is not exposed by the reviewed stock interface; it would require a different design. Native paging does not increase the per-folder cap, and the possible126-entry native widget limit does not change it. Physical available IDs still determine the usable collection maximum.

## Architecture and the critical protocol question

The preferred design uses stock BlueSCSI firmware to switch the backing image, followed by the native S-760 SCSI/media loader. New S-760 code handles discovery, bounded directory/image selection, the mount transaction and media refresh.

The [official Toolbox developer documentation](https://bluescsi.com/docs/Toolbox-Developer-Docs) describes two distinct interfaces:

| Interface | Documented purpose | What remains to prove |
| --- | --- | --- |
| `D0` / `D2`, with `D9/02` working-directory selection | Browse/count files in a chosen shared directory | Browsing a file does not establish a way to mount it |
| `D7` / `DA` / `D8` | List/count/select CD images for a selected target's CD directory, such as `CD3` | Whether and how the selected folder changes the mount source; exact switching/eject behavior |
| Discovery and `D9/00` device listing | Identify BlueSCSI and its emulated targets | Compatible CD/removable/fixed-disk target selection and multiple-device routing |

**Do not assume `D9/02` redirects the CD changer.** Do not pass a `D0` index to `D8` without proving both refer to the same enumerator, directory and current target. Confirm behavior against pinned upstream source and the installed firmware, including errors and reset behavior.

IM1 must separately establish:

1. ISO switching across at least two collection folders on stock firmware.
2. IMG switching from the dedicated folder, with a compatible device class and sector geometry. CD changer support alone does not prove general hard-disk IMG switching.
3. A layout that meets the collection size within available SCSI target IDs. One folder per target can cover hundreds of images; its maximum is bounded by the remaining IDs. Arbitrary folder switching on one target remains a separate architecture question.

If stock commands cannot meet these requirements, record **REVISE** with concrete alternatives and costs. Evaluate existing configuration-supported switching first. A D1-backed virtual block-device adapter would require intercepting native reads, translating sector offsets, capacity handling and recovery; it is a separate, potentially larger architecture. A custom BlueSCSI firmware extension is another explicit scope change. Neither is an automatic fallback or an approved assumption. An ISO-only prototype is useful evidence but does not complete the ISO-plus-IMG plan.

## Stock target-folder candidate established during IM1

The source-backed fixture and actual guest command runs qualify this bounded mapping:

| Logical collection | Physical SD folder required by the stock picker | Target in the native diagnostic | Sector size |
| --- | --- | --- | --- |
| ISO collection A | `/CD1` | ID 1, optical | 2,048 bytes |
| ISO collection B | `/CD3` | ID 3, optical | 2,048 bytes |
| ISO collection C | `/CD6` | ID 6, optical | 2,048 bytes |
| Dedicated IMG collection | `/CD2` | ID 2, fixed disk in the diagnostic | 512 bytes |

Each folder holds up to 100 images: this example covers 300 ISOs plus 100 IMGs. The original logical `/Library/ISO_A` etc. diagram describes the desired grouping; it is not the physical stock layout. The browser can present collection labels while selecting their targets. Writable save/boot media stay on separate targets; verify the user's available IDs before physical qualification. No SD files have been moved or renamed by this work.

On physical BlueSCSI, the IMG target needs an explicit compatible type/block-size configuration, with `ImgDir` set to the same `CD2` path if configured cycling is used. Otherwise automatic directory detection or cycling can select a different type/path. This configuration is source-supported, not yet tested on the user's device. **User clarification, 2026-10-20: FDD and SCSI IMG disks are writable; ISO/CD media are read-only.** Respect intentional write protection, but do not require a read-only attribute on IMG collections. Native Save, Delete, Copy, Initialize and Optimize remain available on a mounted writable IMG. Earlier fixture evidence that forced all library images read-only is historical, not the delivery policy.

This target-per-folder candidate is a concrete first route, not unlimited folder support. Additional collections beyond free target IDs still require a different mechanism. Do not present the stock command set as an arbitrary-path mounter.

## Research to retain

| Existing result | Reuse in this plan | Limit |
| --- | --- | --- |
| Exact-byte six-/ten-byte SCSI sender; raw status/sense, short transfers, cooperative waits, cancellation and retry | Foundation for listing and mount commands | Normal native CDB helpers modify fields and contain unbounded waits; direct reuse is not automatically safe |
| Extended INQUIRY/API and vendor MODE SENSE discovery; scanning IDs 0–6 | Find and qualify Toolbox devices | Installed firmware identity and multiple-device behavior still need capture |
| 100-entry mixed-directory guest diagnostic retaining one 40-byte row | Bounded enumeration and index handling | Fixed `/Files/Keys` and automatic eight-file selection were diagnostic constants; no general folder browser exists |
| Native Disk menu clone and custom callback through ordinary input | Reuse native rendering, input dispatch and screen services | The 268-byte resource plus four-byte index is a menu experiment, not a complete scrolling browser; writable fields need private storage |
| Original native HDD/CD load, mono/stereo hierarchy, playback, Save and cold Load reference workflows | Native media-loader acceptance oracles | Scoped ISO/IMG browser handoff and repeat IMG pass; general cache/geometry, stereo media and browser-to-Save/cold-Load remain open |
| Candidate 8,002-byte loaded RAM region and scoped lifetime/Save System tests | Starting point for placement and footprint measurement | It is not reserved free space; aliases, interrupts, DMA, screen lifetimes and controller modes still matter |
| 745 backend tests, ordinary runtime checks and fixture-disabled 32MiB wave equivalence | Prior regression baseline | These tests predate an image-switching implementation and cannot qualify it |
| Error-path and SDS ownership repairs discovered during research | Retain applicable corrections in the chosen patch baseline | Decide dependencies explicitly; image mounting removes WAV transaction work but does not erase existing defects |

Reference contracts: [transport](bluescsi-transport-contract.md), [menu reuse](bluescsi-ui-reuse.md), [memory](bluescsi-memory-contract.md), [native loader research](bluescsi-loader-reuse.md), [fixture limits](bluescsi-toolbox-fixture.md), and [integrated evidence](../condensed/validation/bluescsi-integrated-client-2026-10-19.json).

Remove WAV parsing, PCM deinterleaving, new sample allocations/descriptors, import naming/loop policy and importer publication/rollback from the first delivery. Retain the previous research for a possible later importer. The old 4,507-byte client and conservative 6,009-byte tally include WAV-specific work and diagnostic overhead; neither is the image browser's footprint. Expected savings are a hypothesis until the complete new client is linked and measured. Recompute the buffer layout and code ceiling instead of inheriting the old 5,634-byte split.

## Boot ROM and GB-6 coexistence

**Required delivery baseline:** The resulting image-selection OS patch must include the existing selectable **v9 GB-6 implementation (X4/Y4)**. V8 is excluded from the delivery baseline. A browser-only OS image is a diagnostic artifact and does not meet the user’s delivery requirement. Preserve Panel+LCD, Mouse+CRT and RC-100 while retaining GB-6 as controller3. Build, fit and test the combined OS; keep its existing compatible GB-6-selectable boot ROM.

The scoped image browser needs no additional IC15 Boot ROM modification: its passing native runs use the original32KB ROM, and all new code/resources are in the OS disk-loaded RAM region. The8,002-byte candidate is OS space, not boot-ROM space. Keep the existing GB-6-selectable ROM for controller mode3; this feature does not replace or revert it.

A static audit of both selectable GB-6 v8/v9 builders finds zero overlapping changed OS bytes with the current browser. All220 GB-6 changes survive an in-memory composition, browser changes survive, and the10 GB-6 code spans disassemble. The entire browser reservation at file0x853E..0xA47F is untouched by those GB-6 patches; the legacy mouse-replacement patch is separate too. Browser drive selection uses0299:8F7D, distinct from the controller byte0299:8F7C. See [coexistence evidence](../condensed/validation/bluescsi-gb6-coexistence-2026-10-19.json).

The later mandatory **v9** combined candidate passes native Setup selection/clamping, EEPROM cold-reboot persistence, no-CRT fallback, Panel/Mouse/RC-100 selection/boot, Mouse movement, and GB-6 browser ISO/IMG loading/playback/Exit. V8 is not used in these runtime candidates. A compact packed successor also links the retained SDS repairs and passes ISO browser loading plus subsequent SDS receive cancellation/rollback/retry/publication. These are scoped emulator results, not all controller paths or hardware acceptance. See [combined results](bluescsi-im1-gb6-results-2026-10-19.md), [GB-6 native evidence](../condensed/validation/bluescsi-im1-gb6-native-2026-10-19.json) and [packed SDS evidence](../condensed/validation/bluescsi-im1-packed-sds-2026-10-19.json). Original firmware remains unchanged.

## Mount transaction and native handoff

The browser owns target, folder, listing generation, selected wire index, image identity and pending-operation state. Keep image selection and the native save destination explicit: the selected writable IMG may itself be the save destination. A compatible target and its geometry/device class must be established before selection is offered.

For each mount: finish pending transfers; validate current folder/index identity; perform the qualified switch sequence; inspect status and sense; complete any required eject/load/readiness exchange; invalidate old media capacity, directory and format caches through qualified native mechanisms; re-read the new media; then enter native Disk Load. Do not force RAM/PC state to simulate media refresh.

Reject or defer switching while a native disk load/save/format or another conflicting operation is active. Preserve sampler memory and completed disk writes across image switches. ISO/CD targets stay read-only; FDD and compatible SCSI IMG targets support native writes unless deliberately protected. Qualify Save to a browser-mounted IMG, switching away/back, cold Load, and isolation of the other images. Do not switch media partway through an active write operation.

Cancellation before switching leaves the mounted image alone. After a switch command may have completed, do not promise rollback: reconcile actual media identity and report the result before further loading. Unknown outcome, absent target, CHECK CONDITION, not-ready, malformed image and interrupted refresh require bounded recovery and a safe return to the Disk interface. Do not reset unrelated targets to conceal an error. External media selection must be reconciled after emulator checkpoint restore or physical device reset.

## Milestones

| ID | Milestone | Status | Exit evidence |
| --- | --- | --- | --- |
| IM1 | Feasibility gate | OPEN | Stock protocol/layout, ISO and IMG switching, native refresh/load, UI/ownership contracts and complete measured fit support a concrete implementation |
| IM2 | Image-switching emulator fixture and transport | IN PROGRESS - opt-in profile, synthetic boundaries and native guest matrices pass | Source-backed count/list/switch behavior, realistic media-change/status/sense behavior, default-disabled equivalence and ordinary SCSI regressions |
| IM3 | Native folder and image browser | NOT STARTED | Multiple collections, up/back, 100 entries, paging/selection identity, clear errors and CRT/LCD/controller qualification |
| IM4 | Mount and native Disk Load integration | IN PROGRESS - ISO/IMG browser handoff/load/playback and same-session automatic IMG B-to-A reload pass; general refresh/recovery open | Correct image selected, old caches invalidated, native mono/stereo content loads/plays, repeat switches and recovery pass |
| IM5 | Compatibility and hardware qualification | NOT STARTED | Hundreds-image layout, ISO/IMG matrix, writable-save isolation, controller patch integration and physical S-760/BlueSCSI acceptance |

IM1 is a small end-to-end diagnostic plus design evidence. IM2–IM4 may be prototyped to resolve IM1 questions; that does not close their full product gates. No byte-saving or schedule estimate is committed before the fit and protocol questions are resolved.

### Acceptance evidence by tested candidate

Established acceptance predecessor `6297274dd5c33b0b37409d3cddcd53e40b8af6140f2c416fc0213181cd3ba628`, mandatory GB-6 v9 and unchanged selectable boot ROM. Its wording-only successor is `ecdbd721543bfbdc0cffe095f28b64185931d9583c3e5aaa3a99e6c26dbc0c36`; four warning resources change, with exact delta audit and native CRT/LCD No checks. Allocation remains **6,452/8,002**, **1,550 free / 1,332 code-adjacent**. Earlier acceptance retains its original binary identity; the latest operation cases explicitly use the timing predecessor below.

| Area | Current status | Evidence / remaining scope |
| --- | --- | --- |
| CRT native parent contexts | PASS, BUG-165 FIXED | Mouse System and26 GB-6 cycles across13 screens preserve active mode ancestry, code, PCM and playback. |
| LCD names/collections/IMG/errors | PASS, named native cases |32-byte shared-prefix identity, Back/held-key no mount, all4 catalogs, HD2 IMG exact Load, bounded failure and independent-target recovery. |
| Current LCD paging and saved-system cold boot | PASS, native | All100 full32-byte names forward/back, final Next/Previous and Collections; native Save System/export/fresh boot clears76 context bytes and explicitly loads119808 exact bytes. Browser/LCD/SDS/GB-6 v9 retained. |
| Full Roland CD | PASS, native |606709760-byte JMD image;79 allocations/6054912 exact bytes,4 notes/2 MIDI channels, release and browser Exit. |
| Writable mounted IMG | PASS, native; BUG-167 FIXED | Native Save, verified CD2 index0/1 reselection, fresh-process Load with119808 exact bytes and playback; other IMG/ISO unchanged. FDD and SCSI IMG are writable by policy. |
| Copy Yes/No and fragmented Optimize | PASS, native | No preserves destination; Yes replaces exact PCM. Both Optimize options reorder directory while preserving name/PCM mapping; fresh Load/playback passes. Optimize is not a data-defrag command. |
| Current Akai stereo | PASS, native |30 samples/15 L/R pairs,13568196 exact converted bytes; three notes/release and playback after browser Exit. |
| Roland stereo and larger writable IMG | PASS, native | Native FDD stereo Load,32MiB512-sector IMG Initialize/Save and cold browser Sample Load reproduce26 clusters/239616 exact bytes; distinct L/R audition, release and browser Exit pass. |
| Populated Volume Dump FD | PASS, matching-source native case | Native whole-Volume HDD Save/reload,720KB dump Save and fresh-process restore with the matching HDD recover13 clusters/119808 exact bytes and playback. Not a standalone sample backup claim. |
| Cancellation, SDS and Remote Mode | PASS, scoped native | D7/D8 cancel/retry, incoming receive and manufacturer41 list/mount races,128 clocks during D7, exact119808-byte Load and160-byte SDS publication. |
| Cold/active-D7, completed-D8 and partial-D8 checkpoint | PASS, scoped fixture; BUG-170 FIXED | Three first-D8-byte recalls now refuse stale handoff, including changed catalog; explicit fresh selection loads exact replacement media. Twelve SPC cases cover0/1/5/9 CDB bytes on optical/IMG/ordinary targets. Other transaction phases remain separate. |
| Machine soft-reset boundaries | PASS, native emulator | Reset during D7, first D8 CDB byte and completed D8 before readiness; fresh cleared Collections, no automatic command, explicit exact Load/playback. Physical resets remain separate. |
| Native operation input exclusion | PASS, named native conflicts | Earlier Save/Load/quick Initialize/Copy/Delete cases plus trial367f067d... Akai conversion, full Format option (Verify No/Yes), FDD Load/Save/Format. Actual commands overlap input without Toolbox commands; exact PCM/cold Load or valid media checked. This is scoped input exclusion, not universal ownership proof. |
| Native disk warning | PASS, BUG-172 FIXED | Both wording successors show “All existing data on this Disk will be lost.” on CRT/LCD, preserve dynamic labels, and pass native No/media preservation. Four resource replacements, zero growth. |
| FORMAT UNIT / Verify Medium | BUG-171 and BUG-173 FIXED | Same-size inherited-loop repair on both successors. Native Verify covers all65,536 and65,537 sectors once, including the last LBA and16-bit borrow boundary, before initialization. |
| Current mounted-IMG Delete/cold scan | PASS, native | Preconfirmation file unchanged; confirmed performance/hierarchy Delete persists counts1/22/88/13 to0/0/0/0. Independent reader and fresh browser/native list are empty; original source unchanged. |
| Dense MIDI / deadline | PASS native, BUG-168 retained | Final606e277e... suspends performance during actions;9003 preserved service pairs and236 commands/891942 exact elapsed samples pass, with playback/release afterward. Prior lowered-budget diagnostic is separate. |
| Resident allocation and lifetime | PASS, linked and observed |6452 named bytes; all7360 immutable/gap bytes preserved in366 earlier plus177 safety-batch plus18 current snapshots;642 mutable bytes explicitly accounted for. Not a universal alias proof. |
| Custom and synchronous native-callee stack | PASS, current scoped static bound | Current graph resolves11 helper roots through54 contextual functions/1211 instructions, including001F:4F8D suspend/restore. Composed maximum166 bytes including80-byte common frame; transition path112. Native dispatcher ancestry and IRQ assumptions remain excluded. [Results](bluescsi-im1-current-stack-results-2026-10-21.md). |
| Full native safety contract | OPEN | Native dispatcher/IRQ depth, maximum service duration, indirect aliases/DMA and broader recovery/reset contracts still need closure. |
| RC-100 | ASSUMED, user waiver | Untouched path; no remote-input acceptance claim. |
| Physical BlueSCSI/configuration/library | OPEN, separate hardware qualification | Installed identity/configuration/available IDs, actual library/IMG attributes and hardware timing. |

Earlier `19448d85...` evidence remains scoped to its exact binary. Full LCD paging, Save System/cold boot and complete Volume Dump restore now have independent established6297274d... acceptance. The [safety batch](bluescsi-im1-safety-batch-results-2026-10-20.md) used7c994e86... . The [latest batch](bluescsi-im1-timing-recovery-results-2026-10-20.md) records old/new executable identities per case; BUG-170 recovery and Copy/Delete exclusion use4cf1cfab... .959 backend tests and fixture-disabled32MiB wave equivalence pass.

### Experimental timing candidate (not promoted)

Trial367f067d... adds32-byte/16000-tick parser admission only during browser service and schedules pending work after masked return. Dense MIDI passes exact775-byte parsing, no overflow,188 preserved service pairs, maximum28.006625ms, no lost whole timer wraps, exact resident PCM and note release. Seven additional CRT/LCD cancellation, SDS and Remote Mode regressions pass. BUG-169 is fixed in this revision; BUG-168 still requires single-byte/control-ISR bounds and a proven total deadline.

The trial rebuilds exactly, retains GB-6 v9/SDS and uses6580/8002 bytes:1422 free,1191 in its largest code gap. Its93 snapshots preserve7360 immutable/gap bytes and the native parser hook. The helper's8 local stack bytes do not close the native stack gate. Remaining established compatibility cases must be checked before this hash replaces6297274d... . [Results and limitations](bluescsi-im1-timing-recovery-results-2026-10-20.md).

Its wording-only successor is `791246920fff404e39dd0dc7fbb0305eee53439adfad86e2b40396f0f0f26f0c`, with unchanged code/allocation. The latest batch adds seven operation cases on367f067d... plus four CRT/LCD wording cases across both successors,91 snapshots and the synchronous-callee composition. Emulator57e45eaf... repairs fixture FORMAT UNIT;1,067 tests pass,3 skip, and all32MiB default-disabled wave bytes match the predecessor. [Exact scopes and results](bluescsi-im1-format-fdc-stack-results-2026-10-20.md).

### Latest extent-repair and fault qualification

The established successor `0be06d4d11a921a0d0b4a25829ee1441c1266d4c07be0633d04968985865a00e` and timing successor `5581ee53a84ea5395ee0bb554fc2b31128bb5740835789b335c83b4c9a548f94` repair the inherited Verify Medium loop in its original48 bytes. GB-6 v9, SDS, warning resources and allocations are retained. Nine accepted cases cover full native verification, LCD names/Load, CRT/LCD cancellation and four D7 fault/retry paths;93 snapshots pass. Earlier evidence keeps its original binary scope.

The required simultaneous-MIDI fault run is **not accepted**:323 MIDI reads overlap the withheld-REQ interval, but only585 of775 expected reads appear. Bus release occurs after113.279125ms; browser error/retry succeeds. This is a concrete BUG-168 recovery blocker. The accepted dense cases have zero MIDI reads during the actual stall and must not be used as simultaneous-traffic evidence.

Immediate init/update/exit/action frames are12 bytes each; observed outer ancestry is not a universal bound. The sentinel scan has a conditional32-comparison/528-total bound. Native MIDI TX-ready and wave-port-ready loops still need completion contracts. [Results and full identities](bluescsi-im1-verify-stall-bounds-results-2026-10-20.md), [validation](../condensed/validation/bluescsi-im1-verify-stall-bounds-2026-10-20.json).

### Predecessor redraw repair (historical)

Candidate `5e5ec01692ca7218f0a39e01aaff6ed0c45237cfd94af5f8f227dd86d0d19064` adds three bytes to service MIDI between CRT character clears. The earlier5581ee53... failed-overlap result above remains historical; both new byte1/3999 overlap cases pass with775 exact reads and resident stereo content/playback/release. BUG175 is fixed, while BUG168's broader timing requirement remains open. Ten native cases/104 snapshots and1089 backend tests pass (3 skipped). BUG174's minimal-image header and native LOAD-only test are fixed. Allocation6583/8002,1419 free; synchronous stack maximum remains166 bytes. [Results](bluescsi-im1-bug-fixes-results-2026-10-20.md).

### Performance-policy predecessor (2026-10-20)

Currente78750c2... reuses native001F:4F8D around admitted browser actions. It preserves idle MIDI while eliminating live note-parser/control work during active SCSI commands. Busy-time complete SDS/Remote Mode requests are ignored; fresh idle requests retain native ownership/exclusion and cleanup. Earlier concurrent receive races above describe the predecessor policy.

Ten native cases/101 snapshots,9003 preserved suspended-service pairs and145 commands/502771 exact elapsed samples pass. The separate one-wrap diagnostic expires at65789 ticks and explicitly recovers; production keeps the32-wrap limit. Byte-identical rebuild/65536 permission cases pass. Allocation6736/8002 leaves1266 free. Boot ROM and GB-6 v9 are retained. This supersedes the earlier BUG168 timing-open conclusions for the native command-service path; stack/ownership and physical qualification remain open. [Results](bluescsi-bug168-native-policy-results-2026-10-20.md), [validation](../condensed/validation/bluescsi-bug168-native-policy-2026-10-20.json).

### Current ownership/recovery candidate (2026-10-21)

Final606e277e... adds three owner rechecks after performance transitions (BUG-176),24 bytes total. Decoded owner/transition2040 cases and65536 permission cases pass; synchronous maximum166 remains. Ten native production cases/101 snapshots pass with9003 preserved service pairs and236 commands/891942 independently checked elapsed samples. Six more final-image workflows cover CRT/LCD/IRQ ancestry and resets after1/511/1023 of1024 WRITE bytes, followed by explicit recovery. The rebuilt emulator passes1123 backend tests/3skips.6760/8002 bytes leaves1242 free. This supersedes e78750c2... for hardware testing; broader state/alias, fault-model and physical gates remain open. [Results](bluescsi-im1-owner-and-recovery-results-2026-10-21.md), [evidence](../condensed/validation/bluescsi-im1-owner-and-recovery-2026-10-21.json).

### Remaining work, without repeating completed checks

- [x] **BUG-168 / bounded timing, native profile:** native performance suspension removes parser/control waits from active commands.145 commands/502771 elapsed samples,9003 service pairs and separate total-timeout recovery pass. Busy-time MIDI is ignored through the native reset; fresh idle SDS/Remote Mode still works. [Current proof](bluescsi-bug168-native-policy-results-2026-10-20.md).
- [x] **Predecessor synchronous native callees:**10 browser helpers/far wrappers had a166-byte composed maximum. This remains historical evidence for the predecessor.
- [x] **Immediate dispatcher frames and bounded scan:** four12-byte dispatcher frames proven; parser sentinel scan bounded at32 comparisons per scan/528 total, conditional on no concurrent writer.
- [x] **Named stalled-target recovery:** first/last-byte D7 faults report an error, release bus and permit explicit retry/Load; before/after-stall MIDI cases preserve resident stereo. The later BUG175 repair also passes actual simultaneous MIDI at byte1/3999, with exact byte/content/release checks.
- [x] **Current synchronous native callees:** include001F:4F8D suspend/restore and its eight-function closure. Current54-function/1211-instruction graph and callback composition retain166-byte maximum (transition112); all native returns balance and bytes match the original OS. Current IRQ graph152 functions/9212 instructions also closes conditionally. [Results](bluescsi-im1-current-stack-results-2026-10-21.md).
- [x] **Named CRT/GB-6 ancestry:**15309 native callbacks return with restored SP and no nested callbacks; every saved return chain matches audited update28/action30/open62/exit62-byte entry prefixes. CF7F/D3A8 retries are tail jumps. Closed current native/declared-domain IRQ graphs do not reach browser dispatchers/callbacks. [Results](bluescsi-im1-ancestry-results-2026-10-21.md).
- [x] **Current LCD/modal and IRQ profile:**50345 LCD callbacks (paging, confirmation/back, Exit and native Load) restore SP without nesting. Current CRT15387 and IRQ-workflow15154 callbacks also pass.2677 native IRQ pairs include nine MIDI-in-timer nestings. The20/20 mask profile gives a conditional56-byte IRQ contribution and284-byte named-route envelope; observed depths are not maxima. [Current proof](bluescsi-im1-owner-and-recovery-results-2026-10-21.md).
- [ ] **Complete current native stack/state contract:** close native caller/state invariants beyond named routes and20/20 masks, including declared jump-table domains and stack-region ownership. The conditional284-byte envelope is not a universal native/hardware bound.
- [x] **BUG-176 / transition ownership:** masked owner rechecks after suspension and both pre-handoff restores;2040 decoded transition/owner combinations reject new owners before SCSI or native handoff. Final native regression matrix passes.
- [x] **Named operation conflicts:** Save/Load/quick Initialize/Copy/Delete plus full Format option, Akai conversion and FDD Load/Save/Format input exclusion pass within their recorded input/operation scopes.
- [ ] **Indirect ownership:** close resource aliases, DMA ownership and any additional operation classes indicated by the call/state analysis.
- [x] **BUG-173 / Verify Medium coverage:** inherited48-byte loop repaired without growth; native complete65,536/65,537-sector censuses and12 decoded-loop tests pass on the two successors.
- [x] **Native incomplete-write fixture recovery:** final-image reset after1/511/1023 of1024 bytes leaves the unfinished buffered command uncommitted; explicit remount/reinitialize succeeds to one identical final hash. Default-disabled diagnostic hook, one-shot tests and1123 backend passes/3skips. This replaces the excluded completed-before-pause probes.
- [ ] **Remaining recovery contract:** other transaction phases, broader target faults and physical/partial-sector write persistence. The active COMMAND-phase fixture rejects stale CDBs after recall (BUG-170); earlier completed-D8 catalog mutation and three emulator reset boundaries also pass. The fixture's command-buffer model is not physical write atomicity.
- [ ] **Physical qualification:** confirm available target IDs/configuration, run the existing SD preflight on the actual library, verify writable IMG and protected ISO behavior, and test on S-760/BlueSCSI. No hardware result is inferred from the fixture.

### IM1 checkpoints, in working order

- **IM1.1 — Baseline**
  - [x] Record original firmware, emulator and diagnostic identities; user confirms BlueSCSI V2 and very latest firmware.
  - [x] Static coexistence audit: no additional browser boot-ROM change, zero overlapping OS patch bytes for selectable GB-6 v8/v9, all220 GB-6 changes retained and10 spans disassembled in memory. Legacy GB-6 replacement sites are disjoint too.
  - [x] Mandatory selectable v9 GB-6/browser native baseline: Setup0,0,1,2,3,3, cold-reboot mode3 persistence, no-CRT fallback, other modes0/1/2 selection/boot and original Mouse movement pass. GB-6 ISO/IMG browser workflows pass.
  - [x] User confirms on real S-760 hardware (2026-10-19) that front-panel GB-6 selection with the patched boot ROM works and is retained after restarting. This confirms selection/persistence; full trackball/browser behavior and the installed binary identity are not established by that report. Main README updated.
  - [x] Packed v9 GB-6/browser/SDS successor passes native ISO browser load/playback/Exit, retained code preservation, and post-load SDS receive cancellation/rollback/retry/publication.
  - [ ] Read installed version/configuration/target map and qualify physical controller/browser behavior. Named current-image Panel+LCD, Mouse+CRT and GB-6 workflows pass; RC-100 input is user-waived. Any subsequent timing repair must retain the existing controller/SDS regression matrix.
- [x] **IM1.2 — Reviewed source contract:** pin release/main implementations, command bytes, enumeration, error behavior, directory sources and configuration differences. Host execution of upstream code supports the contract. This closes inspection for those revisions, not physical parity.
  - [x] Link selected configured-target INQUIRY/API plus complete vendor MODE SENSE page31 signature validation into the mandatory v9/browser/SDS candidate. All four configured IDs pass; an ordinary target's36-byte INQUIRY is refused before any Toolbox command. This is per-selection qualification, not dynamic target-map discovery or installed-version capture. BUG-148 fixes initial six-byte command dispatch.
- **IM1.3 — Folder layout**
  - [x] Qualify three 100-image ISO target folders plus one 100-image IMG target folder in the host harness and native guest fixture.
  - [ ] Qualify physical configuration/available IDs and decide the supported collection maximum. Arbitrary folders on one target are not exposed by the reviewed stock picker.
- **IM1.4 — Switch and identify**
  - [x] Actual guest commands select entries 0/99 on IDs 1/2/3/6, read exact sectors/capacities, distinguish repeated names across folders and repeat successfully in the same process.
  - [x] Execute14 upstream filename-boundary assertions: ordinary31/32/33/59-byte names mount;32-byte display truncation, list/count/index filtering disagreement and the64-byte full-path termination risk are recorded (BUG-145/146).
  - [x] Implement read-only first-profile SD preflight:32-byte printable ASCII, intended-extension-only leaves, distinct visible names, conservative100-entry limit, no nested/link entries, no numeric block-size override and basic sector alignment. Eighteen tests and810 upstream-code host assertions cover400 exact displayed-name/index mounts. [Policy and usage](bluescsi-library-preflight.md).
  - [ ] Qualify physical images/geometries, actual target configuration and representative large user libraries; firmware cannot enforce full SD preflight or detect every equal-count filter mismatch outside the supported naming policy.
- **IM1.5 — Native refresh/load**
  - [x] Current native Delete on browser-mounted writable10MiB HD2 IMG: preconfirmation no-write, confirmed performance/related-hierarchy removal, counts1/22/88/13 to0/0/0/0 and fresh-process empty native list/zero samples. This replaces predecessor-only Delete evidence for the named profile; concurrent Delete/reset is separate.
  - [x] On6297274d..., native Save to browser-mounted writable HD2 IMG persists119808 exact sample bytes; verified CD2 index0/1 reselection and fresh-process Load/playback pass. Copy overwrite Yes/No and both Optimize options on deliberately fragmented media pass with fresh native Load/playback. Current Akai Convert Load reproduces30 samples/13568196 bytes and stereo playback. [Latest results](bluescsi-im1-final-gates-results-2026-10-20.md).
  - [x] Complete populated Volume Dump FD restore using a native-saved whole Volume as the matching HDD source. Private720KB dump Save and fresh-process restore recover13 clusters/119808 exact bytes plus playback/release. This resolves the earlier source-fixture gap without claiming a standalone sample backup. [Safety-batch evidence](bluescsi-im1-safety-batch-results-2026-10-20.md).
  - [x] Qualify a distinct native-recorded Roland44.1kHz stereo pair on32MiB512-sector writable IMG: native FDD Load, browser Initialize/Save, fresh Sample Load26 clusters/239616 exact bytes and distinct L/R playback/release. This extends the named media profile, not arbitrary geometry support.
  - [x] Fix fixture BUG-166 and mount a full606709760-byte Roland JMD CD through the repaired browser:79 exact allocations/6054912 bytes, four notes/two MIDI channels and release. Fixture ceiling1GiB is separate from hardware limits;6 synthetic fixture tests and769 backend tests pass. [Closeout evidence](bluescsi-im1-closeout-results-2026-10-20.md).
  - [x] Mount distinct valid Roland IMG variants; ordinary native Scan/Load/Perform restores 13 sample allocations and 119,808 exact bytes per independent run, with playback/release.
  - [x] Mount a compatible Roland ISO through a CD target, then native CD Scan/Load/Perform with the same exact sample oracle.
  - [x] Current candidate mounts the supplied Akai CD through the browser, reuses Convert Load, and reproduces30 converted samples/13,568,196 PCM bytes exactly against original-firmware hashes. Three notes produce distinct active stereo channels and release; browser Exit preserves playback. This is one Akai volume with15 L/R pairs, not arbitrary Roland stereo/geometry qualification. [Batch evidence](bluescsi-im1-multi-gates-results-2026-10-20.md).
  - [x] Same-session B-to-A mount, native rescan and reload pass after the normal clear-memory confirmation; final sample bytes match and playback peaks track the two source variants.
  - [x] First browser-to-native ISO handoff passes without manual Scan: select protocol index99 through the UI, load13 allocations/119,808 exact sample bytes, enter Perform, play and release.
  - [x] Mandatory v9 GB-6/browser build mounts IMG index99 on HD2 without manual Scan, then native loads13 allocations/119,808 exact bytes and plays/releases before/after Exit.
  - [x] Same-session automatic IMG B-to-A browser switching (99 to0), native clear-memory confirmation and reload pass with119,808 exact bytes per variant and playback ratio1.999979. No manual Scan. These IMG results use the first v9/browser candidate; the repacked SDS successor directly qualifies ISO so far.
  - [ ] Complete the native call/state contract and remaining fault/geometry boundaries within the supported profile. Named10MiB/32MiB Roland IMG, full Roland CD, Akai stereo and distinct Roland stereo are qualified; physical media/configuration and arbitrary geometries are separate.
  - [x] Browser ISO index99 -> native Utility quick initialization of separate private HD0 -> native Save/export -> fresh cold HDD Load passes with13 allocations/119,808 exact bytes and matching playback peak. No library file changes. [Disk operations results](bluescsi-im1-disk-operations-results-2026-10-19.md).
- **IM1.6 — Browser reuse**
  - [x] Reuse ordinary native callback entry/return for the new command diagnostic; retain prior menu-clone/callback evidence.
  - [x] Private CRT mouse prototype presents four collections (IDs1/2/3/6), fetches100 entries each, pages ISO A through15 screens, selects actual index99 and returns to collections. Native field/highlight/text/graphics services are reused; keyboard graphics are cleared and the body is blue.
  - [x] Mount invalidates the shared listing before native handoff; ordinary reopening starts at collections and fetches fresh catalogs (BUG-141). Page redraw no longer reopens popup contexts (BUG-142).
  - [x] Fix native Exit visual restoration (BUG-144): native parent reload restores empty/loaded Perform with stable repeated menu depth and preserved playback; Disk Load before/after matches307,200 RGB pixels. The native popup backup refuses areas over620 cells, explaining the original40x20 failure.
  - [x] Select a59-byte ASCII filename at index99 through15 pages, native load13 allocations/119,808 exact bytes, and play/release before and after repeated Exit; displayed prefix remains32 bytes. This is one qualified long-name case, not a general policy or hardware proof.
  - [x] Native v9 GB-6 CRT browser entry,15-page navigation, exact index99 selection, all four catalogs, mount and Exit pass. BUG-147 fixes only private test coordinates to reachable native text rows; no decoder/sensitivity change.
  - [x] Owned32-byte collection status row visibly presents Cancelled, SCSI error and Mount uncertain; select again. Native screenshots and bounded row bytes qualify these messages; complete footer/help/image identity and richer error policy remain open.
  - [x] Fix BUG-156/157: Disk options reuses the stock nine-action dispatcher; eight native screens plus final Volume Dump FD warning/cancel are observed. Label variants and hashes remain separate. Native Save/Utility/Format access is restored without another menu clone.
  - [x] Seven-name page streaming keeps all100 entries accessible through15 pages, with every32-byte name verified forward/back. Count shrink clamps to page0; failed refresh hides stale choices and explicit retry recovers. All current transport/Load/Save/SDS/Remote Mode acceptance above is repeated on the page-window hash.
  - [x] Remove inherited parent softkey labels and supply native Image Library identity with zero allocation growth. Two exact-hash native workflows, screenshot pixel checks, Exit visual review and rebuild pass; see [owned footer results](bluescsi-im1-owned-footer-results-2026-10-19.md). Dedicated help and LCD/controller qualification remain open.
  - [x] Add contextual CRT instructions and active collection/target-ID titles while retaining complete32-byte names. Qualify all4 collections, paging, Disk options, Exit/reopen, exact Load/playback and retained SDS on the final hash. BUG-159 fixes invisible cold-entry Disk options via init render. [Help/identity results](bluescsi-im1-help-identity-results-2026-10-19.md).
  - [x] Current-hash Mouse+CRT: genuinely saved mode1, all4 collection titles/paging/help/Disk options/Exit/fresh reopen, exact119808-byte native Load/playback, D7/D8 cancellation/retry and retained SDS pass. Mode0 stock Mode->Disk LoadF7/Command is observed separately; LCD F5/F7 resource neighborhoods are unchanged. [Controller results](bluescsi-im1-controller-results-2026-10-19.md).
  - [x] Scoped native Panel+LCD prototype: separateF5 descriptor, native seven-row scrolling,100-entry ISO catalog, Next to7, fresh reopen and index0 mount toF7/native Load with119808 exact bytes/playback. Shares protocol/admission helpers; final trial also passes GB-6 CRT cancellation/Load/SDS. Trial6141/8002,1861 free; full LCD/long-name qualification remains open. [LCD results](bluescsi-im1-lcd-results-2026-10-19.md).
  - [x] LCD full-name confirmation shows all32 returned ASCII filename bytes as two16-byte lines, with a dedicated CD identifier. Native shared21-byte-prefix fixtures, preview/Back/held-key noD8, one explicit index1 mount and exact119808-byte Load/playback pass.256 decoded printable-filter cases pass; BUG162/163 fixed. Same-hash GB-6 CRT cancellation/SDS passes; candidate6487/8002,1515 free. [Name-view results](bluescsi-im1-lcd-name-results-2026-10-19.md).
  - [x] Current-hash Mouse+CRT cancellation/index99 exact Load/playback and retained SDS cancel/retry pass. Current GB-6 parent matrix completes26 browser/catalog/Exit cycles across13 distinct screen IDs with preserved PCM/code and final native Mode→Perform playback. [Batch evidence](bluescsi-im1-multi-gates-results-2026-10-20.md).
  - [x] **Fix BUG-165:** native event0B redraw preserves nested ancestry. Mouse System depth3/ancestor8120 and26 GB-6 cycles across13 screens pass; Disk handoff, LCD names/IMG/errors and cancellation are regressed on6297274d... . [Closeout evidence](bluescsi-im1-closeout-results-2026-10-20.md).
  - [x] Qualify the bounded CRT/LCD browser profile: clear error/uncertain/Busy labels,13 CRT parents,32-byte LCD identity and all4 collections. RC-100 remains assumed under the user waiver. The selected oversized-popup design does not require the unused full-screen descriptor alternative (BUG-140, WONTFIX/retired).
  - [x] Repeat full100-name LCD paging and native LCD Save System/export/new-process cold boot on6297274d... . Cleared76-byte context, no implicit command, exact119808-byte explicit Load/playback and retained browser/LCD/SDS/GB-6 v9 pass. External reset scope is tracked under IM1.7; RC-100 stays user-waived.
- **IM1.7 — Safety and recovery**
  - [x] Current OS: native machine soft reset during active D7, first D8 CDB byte and completed D8 before readiness; each clears operation state and requires explicit fresh selection before exact Load/playback. These are emulator-machine resets, not physical target/cable/power resets.
  - [x] Current OS:3 completed-D8/pre-readiness checkpoint restores, including private catalog rename/content replacement, reject stale handoff and issue no automatic D8. Explicit fresh selection loads the replacement's exact119808 bytes and plays. Active COMMAND-phase partial replay is now covered by BUG-170; other phases remain separate.
  - [x] Current OS: verified Disk-header mouse click plus Mode while native mounted-IMG Save is writing issue no Toolbox command; all119808 saved bytes remain exact. Owner word0 is observed, so native UI serialization is established for this case, not a general owner-word interlock.
  - [x] Dense-note diagnostic receives769 exact MIDI bytes within188 service windows during a complete4000-byte D7;34 scratch words plus modulo RW38 adjustment, selectors/caller/SP, resident samples and subsequent playback pass. This is a data/context check, not timing acceptance.
  - [x] **Fix BUG-168, native profile:** reuse stock performance suspension for active browser actions; bounded parser-free service, exact total accounting, cancellation/stalled targets, playback afterward and fresh idle SDS/Remote Mode pass on currente78750c2... .
  - [x] **Match stock disk performance policy:** suspend performance processing during admitted actions, retain raw receive interrupts, discard complete busy-time traffic through native reset and restore normal processing afterward. Idle browser MIDI, cancellation and playback/release after return pass. Broad clock-hook trials remain rejected.
  - [x] On6297274d..., fresh-process stale-load refusal and explicit exact B recovery pass;3 active-D7 checkpoint recalls drain without automatic D8 and recover via explicit index99 Load. Current MIDI128-clock, receive list/mount, Remote Mode list/mount and cancellation/SDS regressions pass. These are scoped fixture cases, not D8/physical-reset proof. [Closeout evidence](bluescsi-im1-closeout-results-2026-10-20.md).
  - [x] Host-source and synthetic SPC checks cover empty/101-entry counts, list truncation, invalid selection, open failure, readiness/sense transitions, repeated eject, follow-on selection and protected writes. Actual guest runs cover not-ready/unit-attention recovery and repeated selection; library files stay unchanged.
  - [x] Relocated retained SDS repairs coexist sequentially after packed-browser load: cancel settles at cursor13/owner0, retry reserves14/1 then publishes14/0 with160 exact new PCM bytes, all13 loaded descriptors and119,808 bytes unchanged. All code/repair spans remain intact.
  - [x] On the compact discovery candidate, a genuine SDS header while the browser is open brings up native Sample Dump Receiving; collection clicks leave92 context bytes,3,400 listing bytes and SCSI command stream unchanged. Cancel/cleanup and retry/publication pass with exact prior/new PCM and code preservation. BUG-149 corrects the test's callback assumption. This qualifies native receive-modal exclusion; the linked2BBA busy guard itself is not dynamically exercised and full native-operation ownership remains open.
  - [x] Scoped browser cancellation on the paced successor: physical Exit during D7 drains4,000 bytes, preserves raw status/transport and stops before switching; Exit after D8 starts drains that command, shows uncertainty and queues no Load/follow-on command. Explicit fresh selection then loads13 samples/119,808 exact bytes and plays; subsequent SDS cancel/retry preserves prior samples/code and publishes160 exact bytes. BUG-150/151 fixed. This is masked-callback emulator evidence, not full IRQ/hardware qualification.
  - [x] Source-modeled silent D8 open failure is detected through four paced TUR/sense attempts, with visible uncertainty and no native handoff. Same-target catalog retry and independent-target exact ISO load/playback recover without reset/unrelated mount. Ordinary-target/overflow errors are visible. [Cancellation/recovery results](bluescsi-im1-cancel-recovery-results-2026-10-19.md).
  - [x] Conditional IRQ service captures caller masks/data mapping and permits all128 realtime-clock bytes during D7.188 matched service pairs preserve34 scratch words and exactly account service ticks in RW38; native timer/MIDI vectors run without observed ISR SPC writes. Timer wraps are exercised. Observed extra stack is192 bytes, not a worst-case bound.
  - [x] Genuine incoming SDS headers during listing and switching are qualified on the final hash. Listing drains4,000 bytes then rejects publication with Busy; post-mount ownership blocks native drive/Load commit, and receive cleanup plus explicit selection loads119,808 exact bytes and plays. BUG-153 fixes the late-claim race; BUG-154 excludes35ms native service from the idle watchdog while retaining total deadlines. [IRQ/ownership results](bluescsi-im1-irq-ownership-results-2026-10-19.md).
  - [x] Qualify relocated remote/local senders on the compact candidate: cancellation and no-click control, both complete116-packet sends with9216 exact allocation bytes each, and outgoing requests during D7 and D8/readiness. Late owner checks prevent publication/Load commitment; cleanup re-admits the browser. Seven native workflows pass with unchanged footprint. [Sender admission results](bluescsi-im1-sender-admission-results-2026-10-19.md).
  - [x] Fix BUG-155: independent manufacturer41 Remote Mode can become pending while SDS is idle. Shared entry/catalog/mount checks now refuse publication/Load. Paired list/mount races, five native Remote Mode sender/receive/timeout/exit cases and four scoped regressions pass on the new hash; exact rebuild and mandatory v9 preserved. [Session admission results](bluescsi-im1-session-admission-results-2026-10-19.md).
  - [x] Fix BUG-160: every browser entry invalidates catalog/operation metadata while preserving callback CPU saves. Negative stale-catalog baseline, fresh reentry after generated-library replacement, actual native Save System/export/new-process cold boot and exact119808-byte Load/playback pass. Export retains stale page/label bytes, but cold entry rebuilds Collections and sends no command before explicit selection. [Entry-state results](bluescsi-im1-entry-state-results-2026-10-19.md).
  - [x] Current-hash same-process checkpoint recovery after selecting/loading a different image: the fixture invalidates media, native stale Load attempts allocate nothing, traced TUR returns CHECK CONDITION02, and explicit reselection restores119808 exact B bytes/playback. This does not qualify physical resets, cold checkpoint recall or active transactions. [Batch evidence](bluescsi-im1-multi-gates-results-2026-10-20.md).
  - [x] BUG-167 fixture regression: completed writable IMG writes survive selection; interrupted DATA OUT leaves backing unchanged. Protected IMG/optical, missing/resized backing and invalid ranges produce actual status/sense errors. Ten synthetic SPC cases and773 full backend tests pass; native mounted Save/cold Load is qualified separately.
  - [x] Extend conflict coverage with native Load, quick Initialize, Copy and Delete input-exclusion cases. Native reads/writes overlap attempted input, no Toolbox command, exact PCM/final-directory checks pass.
  - [x] Fix BUG-170 active COMMAND-phase recall:12 SPC cases and3 native first-D8-byte restores, changed catalog, explicit exact Load/playback;959 backend tests.
  - [x] Trial367f067d... native full Format option (Verify No/Yes), Akai conversion, FDD Load/Save/Format input-exclusion cases pass; independent FDD cold Load recovers239616 exact stereo bytes. BUG-171 fixture FORMAT UNIT fixed. This historical run omitted the last sector; BUG-173 is repaired and independently qualified on the newer successors below. No physical surface-erase claim is made.
  - [ ] Qualify indirect ownership/DMA, broader target faults and other transaction phases/native-write resets. Latest reset probes did not isolate an in-progress DMA transfer and are excluded. Physical write protection/reset/timing remain separate.
- **IM1.8 — Fit**
  - [x] Decode152-function/9181-instruction native IRQ graph with recorded jump-table state assumptions. Conditional timer/control/wave contribution62 bytes; caller/callee composition, other interrupt owners and mutable-state invariants remain outside this bound. MIDI parser213A has no identified per-service quota. [Analysis and limitations](bluescsi-im1-final-gates-results-2026-10-20.md).
  - [x] Link/disassemble the guest command diagnostic: 1,451 code bytes, with a 6,585-byte inventory of named diagnostic code/data in the 8,002-byte candidate. Local prologue stack is 76 bytes; full stack/ISR bounds remain open.
  - [x] Stream each40-byte D7 wire entry into34 retained bytes (index, type, all32 filename bytes). Native0/1/100-entry catalogs and exact100-record RAM comparisons pass;101-entry DA returns CHECK CONDITION without D7. No native disk buffer is borrowed. Linked discovery/guard candidate measures7,583/8,002 bytes, leaving419 split bytes; exact rebuild and callback/direct-target audits pass. See [discovery/fit evidence](../condensed/validation/bluescsi-im1-discovery-fit-2026-10-19.json).
  - [x] Earlier browser partial census was7,328 bytes. Shared callback entry/exit saves319 code bytes (2,597 to2,278); relocating/repacking831 retained SDS helper bytes yields7,840/8,002 named bytes:2,278 browser code +831 SDS helpers +639 resource +4,000 listing +92 context. Native ISO load/playback/Exit and sequential SDS lifecycle preserve all packed code.
  - [x] Link scoped cancellation, timer/poll-bounded20ms readiness pacing and visible error/interruption labels with mandatory v9/discovery/SDS:7,835/8,002 named bytes (2,773 browser code,831 SDS,739 resources,3,400 listing,92 context). All0/1/100/101 boundaries, cancellation/explicit retry/SDS, silent mount failure/other-target load, static target checks and exact rebuild pass. [Evidence](../condensed/validation/bluescsi-im1-cancel-recovery-2026-10-19.json).
  - [x] Add conditional IRQ service, measured idle-clock accounting and shared owner checks at entry/catalog/mount; remove unused diagnostic snapshots/dead stores. Final partial census7,876/8,002:2,814 code+831 SDS+739 resources+3,400 list+92 context. Six native cases, both IRQ analyses, static targets and exact rebuild pass. [Evidence](../condensed/validation/bluescsi-im1-irq-ownership-2026-10-19.json).
  - [x] Retain mount index+all32 filename bytes in33-byte records; move catalog96 bytes later. Reclaim100 bytes total and96 contiguous code bytes without growing code. Current7776/8002,226 free/98 code-adjacent. Six native workflows, boundary records, exact load, incoming SDS,128 MIDI clocks and exact rebuild pass. [Catalog fit results](bluescsi-im1-catalog33-results-2026-10-19.md).
  - [x] Add specific Remote Mode guard in10 bytes: current7,786/8,002 with216 free/88 code-adjacent. Both session races, five session cases, four browser regressions and exact rebuild pass.
  - [x] Add native Disk actions for100 code+100 data bytes, then reclaim100 catalog bytes by requiring every D7 index to match its ordinal before implicit storage.25700 decoded index cases and native boundaries/index99 pass. Current7918/8002:2956 code+831 SDS+739 resources+3200 names+92 context+100 Disk labels;84 free/68 code-adjacent. [Evidence](../condensed/validation/bluescsi-im1-disk-operations-2026-10-19.json).
  - [x] Resolve immediate space pressure with a224-byte visible-page buffer: retain seven full32-byte names, reread/validate the full catalog on page changes and clamp an invalid origin after refresh. Reclaim2976 data bytes for40 extra code bytes, net2936. Current4,982/8,002,3,020 free/3,004 code-adjacent. Nine native cases, both IRQ analyses,25700 index cases,10000 window cases and exact rebuild pass. [Page-window results](bluescsi-im1-page-window-results-2026-10-19.md).
  - [x] Complete linked census and exact rebuild for the bounded configured-target profile:6452/8002,1550 free/1332 code-adjacent.166-byte custom stack bound, balanced body returns,366 snapshots preserving7360 immutable/gap bytes; mandatory GB-6 v9/SDS retained. [Closeout evidence](bluescsi-im1-closeout-results-2026-10-20.md).
  - [x] Extend the same-image lifetime census with177 snapshots across Volume Dump, stereo, LCD persistence/paging, resets/checkpoints, Save exclusion, mounted Delete and dense MIDI. All7360 immutable/gap bytes remain intact, with642 mutable bytes excluded. This remains observed coverage, not universal alias proof.
  - [x] Trial367f067d... rebuild/disassembly and93-snapshot census pass:6580/8002,1422 free/1191 largest code gap; bounded parser admission and eight native compatibility cases. Trial is not promoted; full timing remains open.
  - [x] Resolve all10 synchronous native callees via46 contextual functions/904 instructions and audited CE14/CDED wrappers. Composed browser/callee maximum166 bytes; updated trial IRQ graph152 functions/9212 instructions retains its conditional62-byte scope.
  - [x] Correct four native CRT/LCD warning resources without growth (BUG-172), preserving GB-6 v9/SDS/browser code in both wording successors. Eleven native cases add91 snapshots preserving all7360 immutable/gap bytes;642 mutable bytes excluded.
  - [x] Current synchronous166-byte bound, qualified CRT/LCD ancestry and20/20-mask IRQ56-byte contribution give a conditional284-byte named-route envelope. BUG168 timing and BUG176 transition admission pass.
  - [ ] Finish broader native caller/state, stack-region and indirect alias/DMA ownership proofs. Fixed1/2/3/6 target mapping and physical ID/configuration qualification remain separate.1242 bytes are free; no extra memory region is currently required.
- [ ] **IM1.9 — Final decision:** the stock target-folder mechanism and named UI/media/IRQ/recovery workflows support a controlled hardware-test candidate. A complete feature-level GO still requires broader native state/stack/alias contracts and remaining target-fault/persistence boundaries. BUG168/176 and BUG173 coverage are fixed in their recorded scopes. Keep arbitrary-folder-on-one-target limits explicit and physical qualification separate.

**GO:** a concrete complete design meets multiple-folder ISO/IMG requirements and fits, with native switching/loading and bounded recovery evidence; physical release qualification may still remain. **REVISE:** an identified protocol/layout/fit constraint requires a specific alternative to be proven. **NO-GO:** tested alternatives cannot meet the mandatory constraints within the accepted scope. Merely listing folders or successfully mounting one CD is insufficient.

## Acceptance collection

Use at least 300 distinct compatible ISO images across three 100-file folders, plus a separate IMG folder, for baseline scale qualification. Use a 101-entry directory only as an overflow negative case. Scale by adding folders, keeping each valid leaf at or below 100 images. Lightweight distinct images can exercise enumeration; include representative real library images for native content compatibility and keep those evidence classes separate. Exercise positions 1, 99 and 100, duplicate basenames across folders, long names, empty folders, an overfull folder, unsupported content, and repeated back-and-forth switching without cumulative RAM growth. Qualify a 100-entry folder index synthetically and freeze deeper-layout limits if needed. Test navigation between many collection folders and prove that mounting uses the selected folder, without whole-library buffer growth.

Native acceptance uses ordinary UI/MIDI input with read-only observers. Synthetic command fixtures test protocol behavior separately. Verify exact selected-media identity and loaded sample bytes plus playback/release, not just a nonblank screen or generic audio level. Confirm saving to the selected writable IMG and cold-loading it again, while unrelated images and read-only ISO media stay unchanged. Test Mouse/CRT and the intended LCD/GB-6 baseline explicitly. Final hardware acceptance uses the user's real BlueSCSI configuration.

For each checkpoint, record source and binary hashes, command, fixture identities, observed result, limitations and durable validation JSON. Keep large private logs/builds in the established research work directory. Preserve original firmware and image libraries; do not overwrite earlier failed experiments or relabel old WAV results as image-mounting evidence.

## First research batch

Start with IM1.1–IM1.3: resolve the directory-to-mount link and compatible IMG route before building a full browser. Then use a minimal native callback to switch a known image and return through native Disk refresh/load. Once those paths work, measure the smaller complete design and implement the folder UI around the established contracts.
