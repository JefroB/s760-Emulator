# OS decoding work queue

Latest boot-ROM acceptance (2026-10-16): BUG-080 command-phase transfer is fixed and qualified with ordinary original-ROM input;452 tests and native runtime verification pass. A private valid-header fixture now reaches payload DMA269D with IC4 count0000/SPC080000, exposing separate BUG-082. Service Notes confirms SCSI INT1 and DREQ/DACK0 wiring; internal IC4 DMA extent/vector/acknowledgment semantics remain unresolved. See [transport report](../boot-rom/ic15-scsi-boot-transport.md). Current classified bytes: ROM26,101/32,768 (79.65%; +0.00 points), OS62,736/1,032,192 (6.08%; +0.01); overall not yet quantifiable. Gemini's additional OS candidates in temp/os-exploration-round3 are being independently reviewed; their raw totals are not yet promoted into maintained coverage.

Scope: systematic OS understanding, independently of filter relevance. Source-language identification is optional. Full Milestone 7 rebuild/modified-firmware acceptance is separately tracked in the completion roadmap.

Statuses: queued, active, static-qualified, runtime-qualified, blocked, done. Acceptance belongs to each item; static-qualified does not mean runtime-qualified. Existing completed reports remain linked from os-decoding-progress.md.

| ID | Status | Work item | Acceptance condition |
| --- | --- | --- | --- |
| OS-001 | active | Transfer allocation and cleanup | Trace slot selection through sample-memory allocation, success publication, out-of-memory rejection and abort cleanup; identify owners of allocated state and validate ordinary native success/failure where feasible. |
| OS-002 | active | Packet/response state machine | Explain sequence counters, response selection, completion, retransmission and cancellation; separate protocol paths and verify transitions with native traces. |
| OS-003 | active | Parameter-state initialization | Identify initialization and reset writers of 91AB/91BB/91CB, including bulk/indirect writes; test whether stale data-entry flags can persist across selection changes. |
| OS-004 | queued | Controller destination consumers | Connect assigned-controller output fields to their consumers using the correct voice indices and data banks; attach supported names and units. |
| OS-005 | active | Storage and UI call mappings | Establish selector context for startup/resident calls into storage/UI; recover bounded entry points and meaningful end-to-end operations. |
| OS-006 | active | Bank-transition analysis | Support safe state tracking or explicitly qualified transitions across selector writes and calls; reject stale-map decoding with meaningful tests. |
| OS-007 | active | Boot-ROM decoding | Extend beyond reset metadata into loader, hardware setup and OS handoff using the separate IC15 mapping; explain relevant data tables and error paths. |
| OS-008 | queued | Whole-image classification | Expand classified code/data/resources from evidence, deduplicate aliases, and maintain an uncertainty inventory covering the full input. No guessed padding or code classification. |

## Resume checkpoint

Latest investigation: `docs/firmware/os/os-transfer-lifecycle.md` explains reservation/publication ordering, receive counts, sequence handling, retry branches and partial-send zero padding. Evidence is `docs/condensed/validation/os-transfer-lifecycle-2026-10-16.json` (596 packet/allocation anchors plus 301 supervisor/entry anchors). OS-001/002 remain active: static local semantics are explained, but ownership and runtime acceptance are incomplete.

Start OS-001 at instruction page 001F:6FBF and follow descriptor preparation and subsequent memory allocation/error exits. Review OS-002 alongside it at 001F:6D10 onward and response entries 7481/748B/7495. Existing decoded views cover much of this region; prioritize semantics and missing callees, not redundant disassembly.

Inputs/tools: `scripts/firmware_manifests/os_exploration.json`, `scripts/analyze_firmware_routines.py`, `scripts/firmware_coverage.py`. Generate fresh analysis under a unique directory in `docs/ic20-hle-findings/chatGPT-work/`. Durable current coverage is `docs/condensed/validation/os-exploration-coverage-2026-10-16.json`. Inspect hashes/current files rather than assuming the checkpoint counts are current.

No external input currently blocks static work. Hardware transfer behavior remains unvalidated. The rollback mapping is now established conditionally through 0000:C869/C86D/C872 -> 0166:87B5 -> 8B5F; the earlier 0160 alias was discarded. The manifest now includes this supervisor (298 instructions, 988 bytes).

Next operation: qualify page 004B:675C (called by 0166:87E1) and page 003B:6F90 (87D5) for preservation of R30 and fetch selector 0104. Then follow page 004B:6A26 (8B4B) to establish the destination of the success copy, and determine whether descriptor +2A is staging or final storage during cancellation. Decode from these explicit selector/call pairs, stop on current-window mapping changes, and keep other banks unresolved. If callee analysis stalls, switch to OS-003 bulk initialization writers.

Reproduce: `python scripts/analyze_firmware_routines.py S760224.IMG scripts/firmware_manifests/os_exploration.json --output <fresh-private-output>` followed by `python scripts/firmware_coverage.py <fresh-private-output>/analysis.json --output <coverage-output>`. Latest scratch is `docs/ic20-hle-findings/chatGPT-work/os-lifecycle-2026-10-16/final`. Thirty targeted firmware tests passed using a workspace-local pytest basetemp after the default sandbox temp directory failed to allocate.

Active iteration acceptance: trace reservation at 001F:6F11-6F88, staging descriptor writes at7150-7161 and final publication at0166:8B55-8B5B, and explicit abort restoration; then explain packet acceptance ordering and bounded buffer counts. Static qualification and runtime validation remain separate.

Remaining OS-002 checks: establish upstream format/checksum guards; qualify supervisor stall-counter timing and cleanup; exercise sequence 127/128 because outgoing numbers are masked but 6DB2 compares an unmasked counter byte; verify malformed-format, final-block and cancellation behavior in ordinary native execution. Sender 757E reads 40 words even when packing fewer, then zero-pads the 120-byte payload. Do not infer a defect from static anomalies without qualifying reachability.

OS-003 active acceptance: qualify the three16-byte zeroing loops through startup entry001F:4F7F, distinguish reset invocation conditions from selection-handler flags, and audit indirect writers before claiming an exhaustive reset contract.


Continuation checkpoint (active work, not a stopping condition): skill persistence update installed and validated. OS-001 descriptor staging/final publication is corrected (BUG-078);003B:6F90 preserves R30 and fetch selectors, but004B:675C invokes further routines throughCE14, so full preservation is open. OS-003 startup reset loops qualified statically; exhaustive indirect writers and native CC sequences remain open. OS-005 EEPROM config closure adds257 instructions with no outgoing unresolved calls. OS-006 adjacent selector-call candidate reporting implemented and tested, not full state propagation.

Current generated analysis: `docs/ic20-hle-findings/chatGPT-work/os-startup-services-2026-10-16/final/analysis.json`. Next useful operations: follow003B:6244/4919 and004B:4D38 from the CE14 invocation operands to qualify UI preservation; characterize EEPROM default blocks and startup validation gates; or follow remaining51 candidate destination pairs from `scripts/firmware_bank_frontier.py`. Regenerate frontier after manifest growth; older candidate counts become stale. Full OS completion criteria remain unmet and unblocked work remains.


OS-007 iteration: explicit mirrored-ROM mapping implemented with validation; reset and loader closure plus initial vector/serial-monitor entries decoded. Stable manifest `scripts/firmware_manifests/ic15_exploration.json`, analysis `docs/ic20-hle-findings/chatGPT-work/rom-decoding-2026-10-16/final`, report `docs/firmware/boot-rom/ic15-decoding-progress.md`. ROM coverage remains separate. Native reset aliases are supported by current driver source; physical power-on values remain unqualified. No native execution or monitor writes performed.

ROM next operations: inspect resource-consumer bounds and loader recovery semantics; derive additional roots only from calls/vectors/copies, not gap sweeps. OS next operations remain independent and runnable: UI callee preservation through003B:6244/4919 and004B:4D38, indirect parameter-state writers, and45 distinct unclassified selector/call targets in the latest frontier. The earlier51 count predates EEPROM root classification.


## Current completion matrix

| Criterion | State | Remaining evidence |
| --- | --- | --- |
| Whole OS payload classification | Incomplete | Most payload bytes remain unclassified; expand only from justified code/data references. |
| Boot-ROM classification | Incomplete | Mirrored mapping, loader and monitor covered; remaining code/data/resources unresolved. |
| Banked control flow and dispatch | Incomplete | Explicit wrappers qualified; indirect invocations, callee side effects and interrupt contexts remain. |
| Referenced data and resources | Incomplete | Several bounded tables/defaults/labels qualified; broad dictionaries and object layouts remain. |
| Major subsystem semantics | Incomplete | MIDI, transfer, EEPROM, UI and storage partial; no whole-OS equivalence claim. |
| Native end-to-end validation | Incomplete | New static paths need ordinary execution evidence; physical parity needs physical captures. |
| Source/rebuild acceptance | Separate open gates | Milestone7 manifest gate alone does not establish decompilation or byte-exact rebuild. |

Latest checkpoint: UI preservation closures,40 fixed label bytes, SCSI session service and CDED wrapper qualified statically. Page01C7 notification/display closure contributes337 instructions. Coverage is regenerated at `os-scsi-services-2026-10-16/final`; durable generated inventory is authoritative.47 tooling tests passed. Next operation follows0139:B418 from the explicit CDED invocation at0166:8CD9, then request-field producers and005A:4A1A. No external input blocks these operations.


Current iteration:0139:B418 and005A:4A1A closures decoded; descriptor publication and incoming request producers are documented in os-scsi-transfer-and-delete.md and os-scsi-session-decoding.md. CEC8/CEF8 and DMA helper73C1 are qualified statically. Next operation: page007F refresh callees488D/40CB/4AB2/438B from explicit01C7 call sites, followed by bounded resources and conditional transitions they expose. Generated inventory at os-dma-wrapper-2026-10-16/final is the last completed coverage checkpoint. No hardware actions performed.


Latest continuation: page007F stereo/preview selection, copy display hook, universal7E send initialization and0166 startup audio command tables are documented. Current coverage generated at os-startup-audio-2026-10-16/final; input hash unchanged. The next operation is005A:42E8 object initialization from startupC337, followed by bounded configuration producers needed by the audio tables. No newly requested hardware capture is needed for static continuation.


Latest checkpoint:005A42E8 is the screen descriptor loader, not sampler-object initialization. One index0130 and referenced fixed resources are classified; layout table bounds remain open. UI masks and mouse/serial control paths decoded;005A5C83 is FDC initialization and its1D0E wait now links to0000CD5D ISR. Last generated analysis:os-panel-fdc-2026-10-16/out. Next investigate the cached descriptor handler-pair consumers and remaining startup resident dispatch; retain unknown pointer bounds.


Active iteration: bound IC15 display resource via29BC/2BAC..2BE4 and retained native data0108=0780; verify all instruction anchors and classify only the referenced0800..1000 bytes. Follow OS resident2080 from startupC476 under retained fetch000F; acceptance is bounded decode, selector audit and explanation of outgoing dependencies. Cached handler-pair search in the current decoded inventory found only loader stores; indirect/base-register consumers remain unresolved, so switch to the explicit startup entry rather than guessing a bank.

Next active acceptance: trace event-ring producer000F:2080..2138 to a consumer using same-window page0000 callsC807->F468 andC811->DE9C. Mapping is conditional on retained fetch0106=0; stop at remaps and retain indirect dispatch uncertainty.


Latest continuation: UI callback slots0..9 now have consumers and guarded events17..1C bound six slots; initial0171:8000 callback is RET. OS event-ring producer/consumer and68 contiguous page0 CDC6 wrapper sites are qualified statically. Current analysis:os-resident-init-2026-10-16/closure. OriginalC000..D000 analysis boundary truncatedCFFE when followingCF82; widened only the declared same-page window to10000, then followed evidenced roots to fixed point. No gap sweep.

OS coverage:15,207 distinct instruction encodings,49,304 code bytes,2,009 data bytes,980,879 unclassified. ROM coverage:4,720 encodings,13,870 code bytes,5,979 data bytes,12,919 unclassified. Both input hashes unchanged; zero decoder warnings. Reportsos-ui-event-dispatch.md andic15-decoding-progress.md link durable validation. OS-005/007 remain active; new static contracts do not meet native completion criteria.

Next operations: trace all writers of cached callbacks2174..219B and descriptor selection indices before bounding mutable target sets; follow01EC:876C/87A5 fromF690/F557 with explicit fetch0104 setup; trace event0C carry-set exit and cursor ownership under ordinary execution. ROM next: bound the four consecutive strings beginning92A8 consumed by55D2..55E4; inspect setup menu tables5656/567D/5741 and their input bounds. No external input blocks static work. Reproduce with standard analyzer/coverage commands and manifests; scratch wrapper follower/validator are underos-resident-init-2026-10-16, durable anchors undercondensed/validation.


Current exact resume checkpoint: OS analysisos-resident-init-2026-10-16/fields contains15,285 instruction encodings,49,573 code bytes,2,012 data bytes,980,607 unclassified. ROM analysisrom-display-2026-10-16/final contains4,720 encodings,13,870 code bytes,6,799 data bytes,12,099 unclassified.47 targeted tooling tests passed; later edits only add analyzer-validated resource metadata and original-byte-checked semantics. All ten callback consumers, seven-byte field records, initial empty field list and6B2E RW30-preservation are statically qualified. ROM setup labels, EEPROM, audio tables,734 bitmap bytes and local logo rendering are qualified with retained-map caveats.

Unfinished next operation: trace0000:F651 incomingRW4C and01EC:878A indirect pointer producers; qualify mutable descriptors and callback target sets. Follow explicit004B:5217 from01EC:8808 for field rendering, preserving data010C conditions; no broad rebuild required. ROM: inspect3632/30B0 pixel units and3684/3746 hardware-counted font transfer; static source bound currently unresolved. Continue independent remaining ROM roots or OS bank-frontier candidates if native tracing is unavailable. Original inputs remain immutable. Reports and durable JSON are linked from the progress documents.


Final turn checkpoint (execution budget; full decoding remains incomplete): field-border004B:5217 now qualified from01EC:8808 and documented. Current OS analysisos-resident-init-2026-10-16/render: 15356 encodings,49840 code bytes,2012 data bytes,980340 unclassified. ROM final remains13,870 code/6,799 data/12,099 unclassified. All changed metadata analyzed successfully;47 tests passed and original hashes unchanged. No native/emulator behavior changes.

Exact next operation: follow incoming callback pointerRW4C in0000:F651 and01EC:878A, inspect tuple producer/descriptor writers, then qualify bounded callback target sets. Regenerate bank-frontier candidates fromrender/analysis.json if this path stalls. ROM independent next operation: qualify the hardware-counted3684/3746 source extent with a read-only ordinary native trace or leave it unresolved and follow another consumer. Current inputs permit static continuation; no background work or completion claim. Standard analyzer/coverage commands remain at top ofos-decoding-progress.md.


Active pointer-producer iteration: explain page0000 screen selection and writes through cached2172 atD060/D080 andD8AD/D8CD; determine callback-table origin and preserve mutable descriptor caveats. Boot-ROM acceptance: explain LCD pixel bounds/address/mask from30B0, then follow a consumer-bounded remaining resource. Baseline inventories saved at os-pointer-producers-2026-10-16/baseline.json (OS51,852/1,032,192;ROM20,669/32,768 classified bytes).


## Current completion percentages (2026-10-16)

| Target | Classified-byte coverage | Classified / total bytes | Change from prior run |
| --- | --- | --- | --- |
| OS loaded payload | 5.20% | 53,664 / 1,032,192 | +0.18 percentage points |
| IC15 boot ROM | 75.68% | 24,799 / 32,768 | +12.60 percentage points |

These are generated classified-byte metrics, not overall semantic completion. The ROM total includes4,096 upload bytes qualified conditionally against the native VDP device model; ordinary execution and physical counter behavior are unvalidated. Overall decoding completion: not yet quantifiable. Complete region/root inventory, mutable dispatch and native end-to-end acceptance remain open; assembler/rebuild gates are separate. Input hashes, exact denominators and previous-run baselines are in[completion validation](../../condensed/validation/decoding-completion-2026-10-16.json).


Execution-budget checkpoint: OS-005/007 advanced statically; full completion remains open. OS outputos-pointer-producers-2026-10-16/final has15,843 unique encodings,51,376 code bytes,2,288 data bytes; ROM outputrom-final has4,720 encodings,13,870 code bytes,10,929 data bytes. New fixed011E/011F descriptor roots, callback event production, numeric metadata loads and temporary status rows are documented inos-ui-selection-callbacks.md; ROM pixel/upload qualification is inic15-decoding-progress.md. Durable evidenceos-fixed-screen-callbacks-2026-10-16.json andic15-pixel-upload-contract-2026-10-16.json includes original-byte checks and mapping caveats.47 tests passed. No firmware, guest state or native behavior changed.

Exact next operation: inspect writer candidates for mutable data02DB:48AA/48B6 from startup/object-service closures; trace a concrete type3 metadata pointer before resolving01EC:8061/879C indirect targets. The fixed011E/011F descriptors have type2 fields and do not by themselves bound numeric type3 handlers. If writers remain unclassified, usefrontier-final.json to select a justified outgoing call into the relevant initialization path; no gap sweep. Independently, qualify the ROM VDP upload contract with a read-only ordinary native trace before claiming runtime behavior, or continue other referenced resource/control consumers. Current static operations remain unblocked.

Reproduce: python scripts/analyze_firmware_routines.py S760224.IMG scripts/firmware_manifests/os_exploration.json --output <fresh>; python scripts/firmware_coverage.py <fresh>/analysis.json --output <coverage>. ROM usesroms/BOOT/Roland_S-760_v1.11.BIN,ic15_exploration.json andcoverage --payload-start 0 --payload-end 0x8000. Scratch validation script andbaseline.json reside inos-pointer-producers-2026-10-16; durable completion baseline includes the input identities. A saved checkpoint is not completion and no background run is scheduled.


Active menu-initialization acceptance: follow explicitstartup0129:8000 fromC677 and0196:88B4 fromC82A forwriters ofmutable submenu tables02DB:48AA/48B6; preservefetch/data mappings andclassifyonlyreferencedboundedresources. Baseline53,664 OS and24,799 ROMclassifiedbytes. No directwriters found inpreviousinventory; switch tojustifiedinitializationroots.


## Current run completion metrics

| Target | Classified-byte coverage | Classified /total bytes | Change |
| --- | --- | --- | --- |
| OS loaded payload | 5.99% | 61,813 /1,032,192 | +0.79 percentage points |
| Boot ROM | 75.75% | 24,821 /32,768 | +0.07 percentage points |

Overall decoding completion: not yet quantifiable. Full root/region inventory,mutableinvocationbounds andnativeend-to-end acceptance remainopen; rebuildgates areseparate. Prior-run baselines53,664 OS/24,799 ROMbytes andinputidentities arestoredin[completion evidence](../../condensed/validation/decoding-completion-device-probe-2026-10-16.json). The ROMupload's4,096 bytes nowhaveobservednativequalification, withoutphysicalparity.47 toolingtests passed.


Execution-budget checkpoint: currentOSanalysisos-menu-init-2026-10-16/final has18,365 distinctencodings,58,869 codebytes,2,944 databytes,970,379 unclassified. ROManalysisos-menu-init-2026-10-16/rom has4,720 encodings,13,870 codebytes,10,951 databytes,7,947 unclassified. Updatedmanifestsareos_exploration.json/ic15_exploration.json. New durable evidence:os-device-probe-and-numeric-2026-10-16.json,ic15-tv-system-2026-10-16.json,ic15-native-upload-2026-10-16.json. Native2-second unthrottledbootusedprivatecopiesandfreshstate;source/stagedOSimagesmatch. ConsoleWMI/XInputandmissingknownSED1330dumpwarningsarepreserved;nativequalificationisrestrictedtotheobservedupload.

Acceptance progression: initial48AA tablefiveindicesqualifiedfor011Evalidfieldselection,notanexhaustiveruntimebound. Initialindex2 leads012F andsixconcretemetadatarecords;81BD confirmsclampsemantics,while01D1postprocessingnestedcalleepreservationandactualnumericUIeditingremainopen. OS-005 remainsactive. OS-007'slocaluploadacceptanceisnative-qualified;entireROMdecodingisstillincomplete. Application0129startupwasidentifiedasan8-targetdeviceprobe,notamenu-tablewriter. No knownexternalinputblocksremainingstaticwork.

Exactnextoperation: qualify01D1:9ED0 frompostprocess9FDF'sA016/A01A->A01E CDEDpair beforeclaimingRC8preservedthroughnumericstore. FollowA036 andthepaired-parameterwritehelperA0A2 exposes;keepdata010A restorationandobject-selectionbounds explicit. Inspectfurther012Ffieldrecordsusingtype-dependenttuplewidth(2/4/6),notuniformsix-byteparsing. Thefirstsixrecordsaretype3;laterrecordsincludeother types. Trace runtimewritersof48AA/48B6 beforeclaiminginitialtableimmutability. Independently,continueROMsetup/input paths orqualifyanothercriticalordinarynativepath;uploadisnowdone locallyandneednotbererun.

ReproduceOS/ROMstandardanalyzercommandswithfreshoutputs;coverageROMuses--payload-start0 --payload-end0x8000. Scratchbaseline/resources/numeric-metadata/native-font livesinos-menu-init-2026-10-16. Nativecommand,binaryhash,rawmatchedrowsandinputhashesaredurable. Context/turncheckpointisnotcompletion,andnobackgroundworkisscheduled.


Latest readable resume summary: the OS inventory is 18,365 unique instruction encodings, 58,869 code bytes and 2,944 data bytes. The ROM inventory is 4,720 encodings, 13,870 code bytes and 10,951 data bytes. Coverage is 5.99% OS and 75.75% ROM; overall semantic completion is not yet quantifiable.

Next, decode 01D1:9ED0 from the explicit CDED argument pair at A016/A01A/A01E in the numeric postprocessor. Check RC8 preservation before claiming the clamped value survives to the final byte store. Continue the A036 object propagation path, recording data-bank changes and bounds. The first six fields in initial screen 012F are type 3, but later fields mix types; advance tuple offsets by the observed 2/4/6-byte rules. Initial table values do not establish runtime immutability.

The local ROM upload check is complete for the recorded native binary: 4,096 writes match the original 2,048 words. Physical parity and full boot acceptance remain open. Do not repeat this successful trace without a new reason. All 47 tooling tests passed; original firmware hashes and the private staged OS copy remain unchanged. Stop here is due to this turn's execution budget, not scope completion. Unblocked static work remains.


Active postprocess iteration: close 01D1:9ED0 and object-selection callee dependencies for RC8 preservation; explain propagation source/destination banks and bounds. Separately trace ROM input/display mode detection through3C68/3C96 and its boot consumers. Static and native qualification remain separate.


Current classified-byte coverage: OS6.07% (62,649/1,032,192; +0.08 percentage points), ROM75.75% (24,821/32,768; +0.00 points). Overall decoding completion remains not yet quantifiable. Previous baselines, identities and exact denominators are in [completion evidence](../../condensed/validation/decoding-completion-postprocess-2026-10-16.json). Four native ROM mode cases add qualification without byte-count growth;47 tooling tests pass.


Execution-budget checkpoint: current OS outputos-postprocess-2026-10-16/final has18,488 encodings,59,244 code bytes,3,405 data bytes and969,543 unclassified bytes. ROM coverage unchanged. Static postprocess closure now includes9ED0; bounded object offsets preserve the numeric value, while arbitrary aliases/interrupt effects remain open. Initial012F has40 fields/238 tuple bytes and eight distinct metadata records. ROM panel observers qualified four mode cases; first two setup attempts failed before accepted evidence and are documented.

Next operation: trace writers of23A8 and2A2C before bounding indexed-byte and dynamic-word edits. Follow the type2 tuple at012F field index6 independently from type3 metadata. Use explicit callback target/page values and consumer widths; preserve unknown runtime states. Exercise one bounded numeric field with ordinary native input if feasible; no forced guest state or invented events. Otherwise continue another justified bank-frontier destination. Source inputs and private staged copies remain unchanged;47 tests passed. Static work remains unblocked. A turn checkpoint is not completion.

Reproduce standard OS analyzer/coverage commands using the maintained manifest and fresh outputs. ROM static inventory remainsos-menu-init-2026-10-16/rom. Native commands and the exact passthrough observer are preserved in ic15-native-panel-modes-2026-10-16.json; private logs are underos-postprocess-2026-10-16/native-panel*. Do not rerun successful cases without a new reason. No background work is scheduled.


Scope narrowed by user: prioritize boot-ROM completion. Active acceptance: inventory allremainingIC15ranges; distinguish referencedresources, reachablecode, unreferencedcandidatecode anduniformerasedcontent withoutguessingpadding. Auditroots/selectors/lowvectors andclosecriticalnativeboot/handoff andfailurepaths wherefeasible. Baseline24,821/32,768classifiedROMbytes(75.75%);OSscopepausedbyfocus,notagoalstatuschange.


### Boot-ROM completion audit, 2026-10-16

ROM classified-byte coverage is 76.79% (25,162/32,768; +1.04 percentage points from 24,821). The generated inventory has 14,137 code bytes, 11,025 identified data bytes and 7,606 unresolved bytes. OS coverage remains 6.07% (62,649/1,032,192; +0.00 points). Overall decoding completion is not yet quantifiable. Assembly/rebuild acceptance is separate.

The contiguous low interrupt-stub structure now includes 0124..013D and its explicit 0131 branch target 02E0..0307. These extra stubs have no proven delivery. At 02E0, RB3 bit0 is set; bit7 gates preservation of RW20, an F000 read/OR3/write/clear-bit1/write sequence and a read of 011D. POPF/RET completes both paths. This is static behavior; register and hardware meaning remains qualified.

The 219A copy establishes exactly 71 resource bytes at file6312..6358, copied to RAM4C62 under data010C=0798. File6359 is the exclusive-end comparison value, not another consumed byte. The 4B09/4B1A/4B1D..4B32 loop consumes exactly three bytes at file6904..6906 (03 BF02) for the FDC SPECIFY command.

Residual bodies2768..2797 and3AC6..3B5E are coherent static code following established return bypass stubs, with invocation unresolved. The first calls the established storage command helpers with copied records4C69 and data buffer4826. The second checks display4D2F, then repeatedly transfers two E800/E802 pairs using VDP command0A at sourceRW20 and command08 at destinationRW22, polling E808 bit1. Source begins0C00, destination4A80, both increment by one until source4A80. Device address units and practical invocation remain unqualified. These are explicitly structural roots, not newly proven reachable routines.

An ordinary native 60-second boot with original ROM, private unchanged OS disk and fresh state observed one fetch0106=0 write at postinstruction PC4755, followed by sustained OS execution. Frame480 still samples ROM loader4A61 with selector07B0; frame540 samples68DF with selector0000. Subsequent OS CDD9/CDEC writes are separately counted, not confused with ROM handoff. This qualifies handoff for the recorded binary, not physical parity or complete OS functionality. Read-only observers return nil and never force guest state. Existing missing SED1330 dump and WMI/XInput warnings remain.

Durable evidence: [handoff](../../condensed/validation/ic15-native-handoff-2026-10-16.json), [remaining ranges](../../condensed/validation/ic15-remaining-range-audit-2026-10-16.json), [coverage](../../condensed/validation/ic15-exploration-coverage-2026-10-16.json), [percentages](../../condensed/validation/decoding-completion-rom-audit-2026-10-16.json). There are 6,487 bytes in entirely FF unresolved ranges and 1,119 bytes in nonuniform unresolved ranges. FF content is observed, not classified as unused padding.

Resume operation: audit the remaining diagnostic bodies2274,245E,25F8,280A and helper52D1 through justified callers or explicit structural evidence; retain invocation uncertainty. Trace failure/retry execution using ordinary private media with a documented readable failure condition. Audit reset/vector defaults, mutable invocation and uniform-FF usage before claiming full ROM completion. No external input currently blocks static work. Reproduce analyzer with ic15_exploration.json; coverage extent0..8000. Scratch directory rom-completion-2026-10-16 holds observer, native command and generated analysis. This is an incomplete checkpoint at the response execution limit, not completion.


## Boot-ROM residual closure and native qualification (2026-10-16)

Current generated classified-byte coverage is **79.65% ROM (26,101/32,768; +2.87 percentage points)** and **6.07% OS (62,649/1,032,192; +0.00 points)**. ROM contains5,172 instruction encodings/15,060 code bytes and11,041 identified data bytes. There are6,667 unresolved bytes, including6,488 in uniformFF intervals and179 in nonuniform intervals. These are classification metrics, not overall completion. Overall decoding completion: not yet quantifiable. [Metrics and identities](../../condensed/validation/decoding-completion-rom-followup-2026-10-16.json) preserve the immediately preceding25,162-byte ROM baseline and regenerated OS denominator.

[Residual helper report](../boot-rom/ic15-residual-helpers.md) explains bounded fill, storage phase waits, command bodies, positioned counted text, geometry/frame helpers, single-word EEPROM read, delay loops and redundant transfer stubs. Invocation remains unresolved for structural-only roots. All instruction bytes match the original, zero decoder warnings,47 existing firmware tests pass. The16-byte hexadecimal table now has independently bounded nibble consumers.

Ordinary native evidence now qualifies original-media112*9216-byte payload transfer, invalid-signature rejection without handoff, and2,789 exact audio-initialization writes against original tables and indices. The short720KB-media experiment instead exposed repeated handoff/restart (BUG-079); it does not qualify retries. Original ROM/OS inputs remain unchanged. Physical timing and reset defaults remain open; assembler/rebuild gates are separate.

### Boot-ROM completion matrix and exact continuation

User scope remains boot ROM; broad OS work is outside this focused continuation. OS-007 remains active and incomplete.

| ROM criterion | Current state | Remaining condition |
| --- | --- | --- |
| Bounded static code and direct frontier | Static-qualified |5,172 encodings/15,060 code bytes; all98 raw cross-region edges retain conditional links except deliberate external4755→C000. Structural roots lack invocation proof. |
| Referenced resources | Static-qualified for maintained consumers |11,041 data bytes, including nine complete counted command records and16 hex digits. Remaining179 nonuniform bytes have no justified active reference. |
| Erased-looking ranges | Unresolved |6,488 bytes in uniformFF intervals. Need usage/nonusage evidence; appearance alone cannot establish padding. |
| Normal floppy boot and signature failure | Runtime-qualified within recorded binary |112 contiguous payload DMAs and handoff; invalid signature remains in ROM. Transport retries need a genuine error-capable model or physical trace. |
| Startup audio, EEPROM and menus | Runtime-qualified for recorded cases |2,789 audio writes; all64 EEPROM words save/verify/reread across process reboot; extended TV0→1 changes F002 bit5. Both limits of all five valid-state menu fields now qualify through ordinary native input; malformed persisted-state defaults and physical parity remain separate. |
| SCSI boot | Blocked by BUG-080 |Ordinary menu selection reaches command phase; SSTS81 cannot satisfyB0 wait. No forced status bypass. Large DMA also programs IC4 low count0; semantics need independent qualification. |
| Low monitor/extra IRQ/residual invocation | Unresolved |No justified entry to most residual roots. Diagnostic gate group0bit5 is not exposed as an ordinary native button; monitor input/delivery and physical reset defaults remain unqualified. |
| Source/rebuild | Separate, out of this decoding acceptance |Milestone7 assembler/rebuild work is not satisfied by decoding. |

New durable evidence: ic15-native-eeprom, ic15-native-setup-eeprom, ic15-native-tv-menu, ic15-native-scsi-boot, ic15-native-scsi-poll and ic15-scsi-records-and-transfer (all2026-10-16 undercondensed/validation). Static reportic15-residual-helpers.md contains exact SCSI record layouts,24-bit SPC versus16-bit IC4 counts, two loader variants, and status/message failure codes. Short-media follow-up observes densityDB, RCFbit1 payload bypass and header-only handoff, not an eight-retry path.

Current scratch: docs/ic20-hle-findings/chatGPT-work/rom-completion-followup-2026-10-16. Current analysisfinal/analysis.json; regenerated OS inventoryos-current/analysis.json. Reproduce checks withverify_final.py andverify_eeprom.py in that private directory; durable evidence carries commands/source/hashes without relying on scratch links. Standard reproduction: `python scripts/analyze_firmware_routines.py roms/BOOT/Roland_S-760_v1.11.BIN scripts/firmware_manifests/ic15_exploration.json --output <fresh-output>` then `python scripts/firmware_coverage.py <fresh-output>/analysis.json --payload-start 0 --payload-end 0x8000 --output <coverage>`.

Failed approaches: initial invalid-media launch lacked required audited OS file; first loader trace lacked-log; short media bypassed payload rather than causing transport errors; first menu input ended before sampling; first SCSI snapshot used unavailable Lua data space; first poll script used unavailable stop callback. Corrected evidence is explicitly distinguished. Do not repeat unchanged successful runs or force guest state to bypass failures.

Next evidence-producing operation for SCSI acceptance is independent native SPC command-transfer repair/qualification against BUG-080, then rerun the saved ordinary BootDrive2 configuration and inspect actual CDB/data/status transactions. That implementation change is separate from this firmware-only research. For byte classification, obtain a justified computed reference/alternate firmware or hardware entry into2918..29BB/remaining isolated bytes, or physical evidence for reserved/erased regions; current decoded direct/word-pointer frontier supplies none. For retry semantics, use an ordinary transport fault that the backend can represent or a physical capture, not raw content corruption (which tests only signature failure). Physical reset selector/IRQ delivery evidence remains missing. No full-ROM completion or physical parity is claimed.

Current measured percentages remain OS6.07% (62,649/1,032,192; +0.00 points) and ROM79.65% (26,101/32,768; +2.87 points from immediately preceding25,162 baseline). Overall decoding completion: not yet quantifiable. Static frontier for the remaining bytes is exhausted under the declared mappings; native SCSI qualification has a reproduced backend blocker. A checkpoint is not completion; no background work is scheduled.


Latest reference-audit checkpoint: docs/ic20-hle-findings/chatGPT-work/rom-reference-audit-2026-10-16 contains reference_audit.py, root_and_hex_audit.py, selector_audit.py, native menu/baseline probes and independent_decode.py. Durable source/commands/hashes are embedded in their validation JSON files; reports do not depend on scratch links. ROM and OS inventories were freshly regenerated by checkpoint.py. verify_publication.py passes unchanged original input/executable identities, all public local links and decoder comparisons. No production runtime/analyzer implementation changes were made. Initial standalone compiler attempts lacked the VS environment, then used C++17 against C++20 utility headers, then lacked BIT in the minimal host; the successful recorded build uses vcvars64, C++20 and a one-bit helper with original decoder sources unchanged.

The reference and selector acceptance at the top is complete only under retained contexts. Root-qualified code is13870 bytes;1190 additional code bytes remain structural-only. All147 raw pointer matches have already-classified sources; no new entry into the179 nonuniform unknown bytes was justified. The latest run baseline is26101 ROM bytes, not25162; both current deltas are+0.00 percentage points. Metrics/identities: condensed/validation/decoding-completion-rom-reference-audit-2026-10-16.json. The earlier+2.87-point record remains historical.

Remaining evidence-producing operations: an independently justified BUG-080 transport repair with command/data/status tests, then an appropriate SCSI boot fixture whose first16 bytes satisfy the ROM's0000000053373730204D523235410040 requirement; the current HD fixture does not. Raw media content corruption cannot supply a genuine transport retry. Missing external evidence remains physical reset/IRQ/dormant diagnostic entry and use or reserved status of the unresolved bytes. A bank-aware Ghidra project could organize established semantics, but a flat import would confuse logical code and work-RAM addresses. No Ghidra/IDA package was installed. Firmware decoding is incomplete; all unknown bytes and invocation qualifications remain explicit.


Latest continuation checkpoint: BUG-080 fixed; native command contract observes9 active/completed transfers,452 full tests pass and native runtime playback/release passes. Independent IC4 count/interrupt gap is BUG-082. Native private valid-header fixture remains269D with encoded0000/SPC080000. Service Notes page18 INT1 and DREQ/DACK0 wiring is verified; no internal DMA vector or physical zero-count rule is inferred. Current scratch rom-scsi-contract-2026-10-16 preserves builds, probes and native checks. Publication encoding failure affected only IC15 progress index; it was restored from durable reports/evidence, local links checked, and subsequent writes use encoded temporary files plus backup before replacement.

Gemini round4 reviewed from frozen private snapshot os-round4-review-2026-10-16: all27844 independent decoder comparisons and7282 targets agree, no original-byte/mapping/boundary/data conflicts. Candidate count is92421/1032192 (8.95%), not maintained coverage. Two exact caller-qualified roots4F28/4F5E promoted with87 code bytes and explicit context links. Current maintainedOS62736/1032192=6.08% (+0.01 points from62649);ROM26101/32768=79.65% (+0.00). Overall not yet quantifiable. Metrics: condensed/validation/decoding-completion-ghidra-review-2026-10-16.json.

Exact next static operation: qualify remaining strict LD/ST/fallthrough-call frontier roots from Gemini round4 against the maintained manifest, then inspect wrapper candidates for branch/clobber/selector preservation before promotion. Do not adopt all142 candidate regions as semantic/runtime closure. Boot-ROM native progress separately requires IC4 DMA extent and real interrupt/vector/acknowledgment evidence, beyond the page18 wiring. No event/vector/guest mutation is authorized as a shortcut. The new scripts/ghidra/export_ic15_contexts.py exports distinct0780/0790 fetch and0798 resource views; five tests pass. Existing Gemini scripts are unchanged.


Latest stack run: BUG-083 fixed (native flag-frame byte order andWSR retention),457 full-suite tests plus new CPU regression pass; native runtime passes. Installed SLEIGH semantic defect is separately OPEN BUG-084. Stack/monitor reportic15-stack-and-monitor.md and validationic15-stack-cpu-validation-2026-10-16.json preserve171 matched IRQ writes, observed42-byte stack depth, handoff4338 caller word, isolated CPU before/after and Intel source. No firmware mutation, fabricated event or monitor execution is claimed. Initial six-second probes were partial; accepted20-second fresh probes reach handoff.

Current metrics:OS62736/1032192=6.08% (+0.00 this run),ROM26101/32768=79.65% (+0.00); overall not yet quantifiable. Baselines/identities incondensed/validation/decoding-completion-rom-stack-2026-10-16.json. Next boot-ROM evidence path remains IC4 control47 transfer extent plus real internal DMA vector/acknowledgment contract; external wiring and inferred MIDI routing do not supply it. Static monitor frames and local stack paths are now accounted for; physical/native invocation of diagnostic/monitor paths and unresolved-byte use remain missing. Separate unblocked OS work: continue strict frontier qualification from the frozen Gemini round4 review, retaining callee/selector qualifications. Scratchrom-stack-audit-2026-10-16 containsstatic_balance.py,probe.py,manual_cpu.py,publish.py and isolated/native logs. No background work is scheduled.


## User-directed unused-space assumption (2026-10-16)

For continued boot-ROM work, treat the 6,488 bytes in wholly FF unclassified intervals as **presumed unused space unless contrary evidence appears**, as explicitly directed by the user. This is an operational assumption, not a remaining prerequisite for boot-ROM decoding completion. The 179 other bytes remain unresolved. Reopen a presumed-unused interval if credible code/data references, copy or checksum requirements, or runtime evidence establish use. Preserve the original FF bytes in exports and rebuilds.

This accounts for **32,589/32,768 bytes (99.45%) including the assumption**; it does not measure semantic completion. Strict evidence-backed classified-byte coverage remains **26,101/32,768 (79.65%; +0.00 percentage points)**. OS classified coverage remains **62,736/1,032,192 (6.08%; +0.00 points)**. Overall decoding completion: not yet quantifiable; remaining behavioral questions include IC4 SCSI DMA/interrupt handling and dormant monitor invocation. [Assumption inventory](../../condensed/validation/ic15-presumed-unused-space-2026-10-16.json) records the hash-checked intervals and reopening rule.


## Residual text classification (2026-10-16)

Structural classification adds176 data bytes: four NUL-terminated self-check messages at file2918..29BB, nine-question-mark placeholder63CC..63D5, the -128 terminator6004 and leading Controller-label space6369. These are recognizable resource contents; no caller or diagnostic invocation is claimed. Regenerated analysis has zero decoder warnings.

Strict ROM classified-byte coverage is now **26,277/32,768 = 80.19% (+0.54 percentage points)**. Of the remaining6,491 bytes,6,490 are FF and presumed unused under the user's direction (including the newly separated2917/6005); the sole other byte is **file6903 = 08**, adjacent to the FDC SPECIFY template. Including presumed unused space accounts for **32,767/32,768 bytes = 99.997%**; rounded100.00% would conceal the remaining byte and is deliberately avoided. This is byte accounting, not behavioral completion. OS remains62,736/1,032,192 =6.08% (+0.00 points). Overall decoding completion: not yet quantifiable. [Exact inventory and qualifications](../../condensed/validation/ic15-residual-text-classification-2026-10-16.json).

Next operation: investigate file6903's possible template-prefix role without assigning meaning from adjacency alone, then qualify remaining diagnostic invocation and IC4 transport contracts. Original ROM remains unchanged.


The final08 byte is **not consumed by the established FDC SPECIFY loop**:4B09 starts8904,4B1A sets count3 and4B1D/4B32 read only8904..8906 (file6904..6906,03 BF02). Adjacency does not identify6903's role. Native diagnostic entry is separately constrained:4285 requires panel group0 bit5, but current nativePANEL0 marks that bit unused (maskE0). The subsequent gates areR4A bit0 ->4917, otherwiseR4B bit0 ->4000, otherwiseR4A bit1 ->4028. No physical service-button identity, synthetic input, guest-state mutation or invocation is claimed. Remaining boot-ROM paths need a justified reference/alternate-ROM comparison for6903, supported service-input mapping, or independent IC4 DMA/interrupt evidence; existing static reference searches and ordinary modeled-input paths do not resolve them.


Final-byte investigation: [file6903 assessment](../boot-rom/ic15-final-residual-byte.md) identifies a plausible unused FDC Sense Interrupt Status08 constant next to SPECIFY. The active routine0197/019A uses immediate08, qualified during ordinary boot; read-only boot/setup probes never read resource8903. Both adjacent consumers exclude it. This supports a leftover constant hypothesis, not original-author intent or all dormant contexts. Preserve the byte; semantic status remains provisional. Coverage unchanged: ROM26,277/32,768=80.19% (+0.00 points this run), OS62,736/1,032,192=6.08% (+0.00); overall not yet quantifiable. Next decisive evidence would be an alternate original ROM/symbol listing or justified dormant consumer; repeated baseline probes cannot prove historical intent.


## Full floppy OS retrieval trace (2026-10-16)

A fresh original-ROM boot monitors all64 possible logical data aliases for file6903, using the actual per-window data selectors and physical ROM-aperture/mirror filtering. Passthrough taps remain active until actual4755 handoff. The matched DMA log proves a512-byte header read, followed by112 contiguous9,216-byte payload transfers from disk004800..1007FF into RAM000000..0FBFFF (1,032,192 bytes), then OS handoff. **Zero accesses read stored byte6903 through any monitored data alias.** The immediate08 routine issues58 Sense Interrupt command writes during the same run. [Trace, observer, identities and checked totals](../../condensed/validation/ic15-byte6903-floppy-load-trace-2026-10-16.json). This establishes non-use on successful ordinary native floppy OS loading; physical hardware, failure/retry paths and dormant diagnostics remain distinct. Coverage unchanged:ROM26,277/32,768=80.19% (+0.00 points),OS62,736/1,032,192=6.08% (+0.00 points); overall not yet quantifiable.


## Read-event watchpoint with history (2026-10-16)

A reusable observer in `scripts/trace_ic15_residual_byte.py` records exact read events, CURPC/post-PC, CPU state, all bank selectors and32 recent instruction addresses. A known-used neighboring FDC template is the positive control. Seven30-second native cases pass with **zero reads of file6903**: successful floppy boot, Mode setup, invalid floppy signature, short floppy (only through first handoff), absent SCSI target with floppy fallback, bad SCSI header with floppy fallback, and valid SCSI header reaching the known269D DMA stall. No unsupported diagnostic input or guest mutation was used.

The debugger's raw disassembly uses the wrong banked data view (BUG-085); all32 positive-control history addresses were matched to original-ROM encodings under the observed0790 fetch context. [Full observer source, events, identities and history](../../condensed/validation/ic15-residual-byte-history-2026-10-16.json). This demonstrates the event logger works and bounds the negative finding to exercised paths; it does not prove no possible caller exists. No target-read event occurred from which to infer a use. Classified coverage unchanged:ROM26,277/32,768=80.19% (+0.00 points),OS62,736/1,032,192=6.08% (+0.00); overall not yet quantifiable.


Gemini batchL independent review (2026-10-16): [review and acceptance limits](os-gemini-batch-l-review.md). Raw candidate coverage36.88%; zero original-byte/mapping or direct-target disagreements, but1,360 boundary-conflict pairs and25,858 length/mnemonic mismatches. Intel-supportedSKIP/IDLPD decoder defects account for25,837;21 need variant/support review. Triage flags1,504 regions;5,653 pass those checks only. BUG-086/087 logged. MaintainedOS62,736/1,032,192=6.08% (+0.00 points),ROM26,277/32,768=80.19% (+0.00); overall not yet quantifiable. Next operation: controlled KB decoder correction and regeneration, then reference-qualified/global-conflict-filtered candidate promotion. No Gemini-owned files or installed libraries changed.


## Independently accepted reconciled frontier (2026-10-16)

Gemini's65 ->119 ->126 region progression is independently reproduced:92 call sites/54 new destinations, then9 sites/7 destinations, then0 new destinations. All23,134 instruction locations and6,089 direct targets agree with the independent MAME decoder; original bytes/mapping match, warnings and global boundary conflicts are zero. The maintained manifest now includes61 new conditional roots plus101 explicit contextual links recording the original adjacent LD/ST/CALL evidence. Existing links and unknown control edges remain.57 focused tests pass; initial3 sandbox temp-directory errors disappear with workspace --basetemp.

Current OS classified-byte coverage: **77,680/1,032,192 =7.53% (+1.45 percentage points)**, including74,275 code bytes and3,405 data bytes. Boot ROM: **26,277/32,768 =80.19% (+0.00 points)**. Overall decoding completion: not yet quantifiable. [Promotion/evidence](../../condensed/validation/os-reconciled-frontier-promotion-2026-10-16.json), [independent checks](../../condensed/validation/os-reconciled-independent-review-2026-10-16.json), [metrics/baseline](../../condensed/validation/decoding-completion-reconciled-frontier-2026-10-16.json).

Convergence applies only to the strict adjacent-selector/direct-call frontier, not all OS control flow. Callee preservation/return context, interrupt clobbers, indirect/trampoline/nonadjacent setup and physical invocation remain separate gates. The discovery script does not itself enforce global code ownership or explicitly reject warning lists; those checks were supplied independently and pass for this final result. The installed SLEIGH length defect remains upstream; the analyzer's documented workaround is independently checked for this inventory. Candidate batchL's broader36.88% is not promoted wholesale. Next work: annotate new callee selector effects and return contexts, then expand justified nonadjacent/trampoline/indirect paths rather than rescan arbitraryRET bytes.


## Quantified boot-ROM functional scope (2026-10-16)

[Boot-ROM completion matrix](../boot-rom/ic15-completion-matrix.md) establishes rubric `ic15-native-decoding-v1`:15 named paths, four equal binary gates each (entry/context, layout, behavior, native execution). Initial acceptance is **46/60 =76.67%**:context11/15,layout15/15,behavior12/15,execution8/15. This is completion against the published scope, not a percentage of effort, full hardware fidelity or OS-plus-ROM completion. No partial credit; failed/blocked paths remain in the denominator. Scope changes require a versioned amendment and a comparable old/new denominator.

Unfinished gates cover genuine floppy recovery, SCSI DMA delivery/completion, original diagnostic/monitor invocation, auxiliary interrupt routing, structural-only helpers and unreferenced resource ownership. The user-accepted6,490FF bytes do not block this scope; the final08 byte remains provisional. Physical parity and Milestone7 source/rebuild acceptance are separate unscored requirements. All gate criteria and citations are in the machine-readable scope; a generator verifies evidence-file existence/JSON, input identity, byte accounting and arithmetic rather than pretending to re-prove semantics automatically. Three guard tests pass; deterministic --check passes.

Byte coverage unchanged this scoring pass:ROM26,277/32,768=80.19% (+0.00 points),OS77,680/1,032,192=7.53% (+0.00 points). Combined overall decoding completion remains not yet quantifiable until an OS subsystem scope is published. Reproduce with `python scripts/report_ic15_completion.py --check`. Next evidence work should target one named open gate and update it only against its criterion; retain this initial score as baseline.


## OS and combined functional-scope acceptance (2026-10-16)

[Published firmware matrix](../firmware-completion-matrix.md) addsOS rubric `s760-os-decoding-v1`:24 contracts/families and96 binary gates. InitialOS acceptance is **36/96 =37.50%**. Combined with ROM46/60, the explicit gate checklist is **82/156 =52.56%**; this sums gates rather than averaging percentages. It is not a source-understanding, effort-remaining or physical-fidelity estimate.

Unmapped scheduler/interrupt-wide behavior, voice lifecycle, filesystem/persistence, synthesis, remaining screens/inputs, object hierarchy and sampling/editing remain open. The remaining-payload family explicitly covers all unclassified bytes, overlays and unassigned functions; it cannot receive completion credit while unexplained bytes remain. Historical81/33-row catalogues were not used as verified addresses/status. Every scope row has criteria and evidence, with conditional contexts preserved. OS-side execution is credited only to the narrow original-ROM-to-running-OS handoff; unrelated native tests and ROM EEPROM tests do not count as OS routine execution.

Six scope/arithmetic guard tests pass. Both generators' deterministic --check passes. Scope changes require a versioned denominator amendment; initial scope/score snapshots are retained. Reproduce with `python scripts/report_firmware_completion.py --check`. Combined overall semantic decoding completion remains unquantifiable; **published functional-scope acceptance** is now measurable and reproducible. Physical parity and Milestone7 source/rebuild gates remain separate.

Byte coverage unchanged:OS77,680/1,032,192=7.53% (+0.00 points);ROM26,277/32,768=80.19% (+0.00). Next quantitative update must change a named gate against its acceptance criterion, not convert candidate-byte growth into semantic credit. Near-term targets include native parser/event-ring contracts and remaining callee preservation, alongside still-open boot-ROM SCSI/retry/diagnostic gates.


OS source toolchain review2026-10-16: [findings and next acceptance steps](os-source-toolchain-review.md). Fresh no-change byte reconstruction independently passes, but instruction text is ignored, aliases overwrite and offsets are not bounded. BUG-088/089/090 logged;4 original tests pass plus4 strict expected failures. No source-assembler or modified-firmware gate closed. Existing decoding scores/byte coverage unchanged. Next toolchain operation is a real instruction encoder with text-only edit/invalid-syntax acceptance, canonical alias ownership and strict layout validation; do not edit hex comments and label it assembly.


Filter timing follow-up2026-10-16: current-build paired native observations now localize variable timer delivery to004B:57B4..5811 mouse-handshake masking;all24 delayed intervals among48 deliver at5812 afterPOPA. OriginalTIMER1+20,000 service-time rearm explains accumulating delay. ExactPCM controls pass; no production change/physical timing claim. [Evidence](../../condensed/validation/filter-scheduler-localization-2026-10-16.json). BUG-005 remainsOPEN; next causal work is physical cadence discrimination and101018 command/transition semantics against existing controls. BytecoverageunchangedOS77,680/1,032,192=7.53%(+0.00),ROM26,277/32,768=80.19%(+0.00);functional-scope acceptanceunchanged82/156=52.56%;overall semantic completion remainsunquantifiable.


Timing repair2026-10-16:BUG-091 FIXED native six-op2-state timing;478 full tests pass,4 known builderxfails;native runtime and paired observations pass. BUG-005 staysOPEN. [Evidence](../../condensed/validation/native-kb-state-time-fix-2026-10-16.json). Exact next operation: regenerate original TVFSTEP/resonant native trajectories on current engine, then apply frozen hardware comparisons (no reused old-build checkpoints/timing rows). Cadence observed20.009266/20.009078ms after correction; cross-build phases differ. UnchangedOS77,680/1,032,192=7.53%(+0.00),ROM26,277/32,768=80.19%(+0.00);functionalchecklist82/156=52.56%;overall semantic completion unquantifiable.


Post-CPU-repair acceptance follow-up completed: [fresh hardware diagnostic comparison](../../condensed/validation/filter-hardware-after-kb-timing-fix-2026-10-16.json) is mixed (closingbetter,openingworse);no speedfit. BUG-005 remainsOPEN. Next unknown is companion101018 transition/command semantics; original instructions/CPU cycles are not a replacement for the ASIC law. Workspace emulator rebuilt; package artifacts unchanged. No byte classification or functional-scope gate changed.


Native short-filter trial implemented2026-10-16: [qualified opt-in trial](../../condensed/validation/native-short-cutoff-trial-2026-10-16.json). Default PCM exact over2,998,800 stereo frames; fast jumps apply exact target next frame;488 current tests and native runtime pass. BUG-005 remainsOPEN; next qualify actual native trial against frozen analog and resonant/static controls. OS77,680/1,032,192=7.53%(+0.00points),ROM26,277/32,768=80.19%(+0.00points);no functional gate or overall semantic-completion claim changed.


Short-plus-rounded native trial2026-10-16: [evidence](../../condensed/validation/native-short-rounded-cutoff-trial-2026-10-16.json). Offline opening5.774%/closing2.659%;native default PCM exact, fast commands immediate,488 tests/runtime pass. BUG-005 remainsOPEN; next actual-native analog/static/resonant qualification, with diagnostic flags off by default. No classified-byte or functional gate changes:OS77,680/1,032,192=7.53%(+0.00points),ROM26,277/32,768=80.19%(+0.00points);overall semantic completion unquantifiable.


Direction-specific offline transfer2026-10-16: [results](../../condensed/validation/filter-direction-transfer-2026-10-16.json), opening2.043%/closing2.491%, all six takes improve versus shared scale; later four transfer frozen direction parameters. Next causal native coefficient response covering reversals/commands, not CPU retiming or future-write access. BUG-005 OPEN; native code unchanged. Coverage unchangedOS77,680/1,032,192=7.53%(+0.00points),ROM26,277/32,768=80.19%(+0.00points);no functional-scope gate credit;overall semantic completion unquantifiable.


User filter acceptance target2026-10-16: below1% waveform residual each direction with static/fast controls. [Curvature/duration/precision experiments](../../condensed/validation/filter-sub-one-percent-target-2026-10-16.json) reach2.014%opening/2.001%closing offline; target not met. Curvature transfers; duration unchanged; raw/nearest target precision regresses. Next residual/update-latch localization and causal dynamic coefficient response. Native code unchanged; BUG-005 OPEN. OS77,680/1,032,192=7.53%(+0.00points),ROM26,277/32,768=80.19%(+0.00points);no gate credit/overall semantic completion claim changed.


2026-10-16 continuation: BUG-092/093 FIXED (30 CPU groups;49 timing cases,39 legacy cases exact;495 tests/runtime pass). [CPU evidence](../../condensed/validation/native-kb-control-state-time-fix-2026-10-16.json). Shape/state/latch/jitter checks do not approach1%; fresh frozen comparison2.024%opening/1.930%closing. [Dynamic tests](../../condensed/validation/filter-dynamic-residual-tests-2026-10-16.json). Next consume the prepared257second physical TVFGRID recording: [reproducible14-part midpoint stimulus and native validation](../../condensed/validation/filter-midpoint-capture-2026-10-16.json); no physical capture received yet. BUG-005 OPEN. Auxiliary observer disconnect BUG-094 OPEN; normal protocol passes all14 cases. Coverage unchangedOS77,680/1,032,192=7.53%(+0.00points),ROM26,277/32,768=80.19%(+0.00points);no functional-scope gate or overall semantic completion claim changed.
