# Hardware & Current Emulator Memory Map

## Extension memory ownership — 2026-10-18

Read-only native stereo and HDD workflows show that apparent fill areas at
physical `0DABE4..0E435B`, `0E435E..0E7BFF`, `0E8010..0EBFFF`,
`0EC000..0ED337`, `0ED3F8..0EFFFF` and `0FC000..0FFFFF` are occupied or
initialized by existing firmware. In particular, HDD reload changes 11,060 bytes
in `0E8010..0EBFFF` with zero CPU-write tap observations: the driver's direct DMA
bypasses CPU taps. Snapshot equality or absence of CPU accesses cannot establish
free RAM. The follow-up excludes the tail `0F53D4..0FBFFF`: CRT backup uses
three slots starting at `0F0000/0F5554/0FAAA8`, each up to `5554` bytes for valid
nonzero dimensions. LCD backup uses `2200` bytes per accepted depth on pages
`03C0/03D0/03E0`; a separate conditional clear covers all of page `03F0`.
Normal LCD save rejects depth 3, despite an encoded fourth dispatch arm.
These are byte-checked storage bounds; the retained native popup exercises
only depth 1. [Screen storage contract](../firmware/os/os-screen-backup-storage.md).
The lower `003D3E..005C7F` range remains an unreserved candidate. A private
8,002-byte nonzero marker now survives boot, native Save System, cold boot of
that export, and stereo Load/playback across 11 snapshots. The original fill
is zero; only file `00853E..00A47F` is changed in the marker input. Save System
retains those bytes, so any future mutable workspace there requires explicit
boot/entry initialization. Startup clears physical `081120..08211F`, a different
data mapping. CPU data taps omit instruction fetch and direct DMA; this scoped
lifetime result does not establish absence of all users or executable safety.
[Address map and limits](../project/bluescsi-feasibility.md#lower-candidate-marker-and-save-system-follow-up),
[validation](validation/bluescsi-memory-transport-2026-10-18.json).

A private OS diagnostic now executes from fixed-low fetch page `000F`, logical
`013E..04EB` (physical `003D3E..0040EB`), entered through an ordinary CRT Save
System callback at `0181:9040`. Its code is 942 bytes; transaction/helpers occupy
576 of those bytes. Measured stack growth is 84 bytes inside the helper, 86 with
the hook call. Separate page `000F` data aliases hold the case table at `5000`
and results at `5400`. Four runs retain code/table bytes through boot and
subsequent HDD Load/playback, with unchanged complete candidate contents after
the probe. All 114 observed general-register words, target-state bytes and
unrelated bank selectors are restored, as is the caller's `010A` mapping.
This is scoped executable evidence, not full ownership or a complete-client
budget. The final sequence masks interrupts for 20.32825 ms; interrupt
cooperation remains unqualified. [Guest placement and limits](../project/bluescsi-feasibility.md#guest-transport-experiment-and-executable-placement),
[validation](validation/bluescsi-guest-transport-2026-10-18.json).

The full-buffer diagnostic extends code to physical `003D3E..004142` (1,029
bytes) and uses guarded data `000F:4800..57FF` at physical `004400..0053FF` for
4 KiB transfers. Case table `5804` and result records `5A00` remain separate.
Four snapshots retain code/table and unchanged post-probe candidate contents
through ordinary HDD Load/playback. The tested path uses 84 stack bytes including
the hook; the earlier 86-byte maximum includes an additional held-ACK nesting
path. Complete ownership and concurrent browser/importer buffer lifetimes are
still open. This diagnostic masks interrupts for 1.897658 seconds, so larger
buffer feasibility does not establish interrupt safety.
[Full-buffer evidence](validation/bluescsi-transfer-errors-2026-10-18.json).

The interrupt-cooperative follow-up expands code to 1,333 bytes at physical
`003D3E..004272` (`000F:013E..0672`). A 480-byte table at data `5804`, 640-byte
records at `5A00` and 16-byte control/context area at `5FF0` remain separate from
the guarded 4 KiB buffer. Four final snapshots preserve code/table and the
post-probe candidate through HDD Load/playback. Each service point saves 35
transport scratch words and restores the native data bank before conditionally
enabling interrupts, then restores its own bank/scratch. IRQ-owned globals
advance normally. Every observed stack write in two runs gives 180/184 bytes
including the hook; a preceding sampled path reaches 186 bytes. These are
workload observations, not maximum stack or complete memory ownership. No
vectors are patched, and fetch page `000F` remains fixed.
[Interrupt placement and measured limits](../project/bluescsi-transport-contract.md#interrupt-cooperation-follow-up),
[validation](validation/bluescsi-interrupt-cooperation-2026-10-18.json).

Ordinary Exit/drain support grows the private helper to 1,571 bytes at physical
`003D3E..004360` (`000F:013E..0760`), with 26 context bytes at data
`5FF0..6009`, physical `005BF0..005C09`. A separate initiator-stall diagnostic
uses 1,596 code bytes through physical `004379`. The guarded buffer and table/
record extents remain separate. Cancellation state is initialized on entry;
ordinary re-entry after cancellation clears it and completes the full matrix.
Snapshots preserve code/table and stable post-operation contents across HDD
Load/playback. Measured stack paths are 180/182 bytes including the hook, without
reducing the earlier 186-byte observed requirement or closing worst-case bounds.
These are placement/lifetime checks, not complete extension ownership.
[Cancellation placement and limits](../project/bluescsi-transport-contract.md#ordinary-exit-cancellation),
[validation](validation/bluescsi-cancellation-2026-10-18.json).

Seeded lifetime tests retain the helper/table and fill the other 5,951 candidate
bytes. All 24 initialized snapshots across sampling, Save, cold Load and armed
same-build session restore preserve all 8,002 bytes. A separate pre-restore
snapshot is zero, proving that the checkpoint restores the candidate in that
fresh process. Completed DMA logs overlap the candidate only in the two
normal system boots; CPU data taps alone would miss those copies. A fourth
fresh process passes the full 20-case helper from seeded state, modifying only
its declared buffer/guards, records and context, and retains all other bytes
through native HDD Load/playback. These remain scoped modeled observations.

The budget now separates 4,928 local data bytes from an unproved 512-byte extra
native stack allowance. Startup places the stack at data `0204:1120`, physical
`082120`, outside the candidate. Local accounting therefore leaves 3,074 bytes
for code/UI/constants. The 1,571-byte diagnostic, 640-byte remote SDS helper
and 160-byte local owner total 2,371 bytes, leaving 703 arithmetically; current
separate placements leave 31 gap bytes and 672 contiguous bytes after the local
helper at 000F:0A00..0AA0, physical 004600..0046A0 (end-exclusive).
The recovery helper runs at 000F:0780..0A00, physical 004380..004600
(end-exclusive). Seven remote workloads observe 182 stack bytes below caller
SP1120; this is not a worst-case bound. Combined transport/owner placement and
full-client fit remain unqualified. [Recovery evidence](validation/bluescsi-remote-recovery-2026-10-18.json). The proposed buffer at physical `004940..00593F` is not yet installed.
Full code fit, stack bounds, indirect aliases and wider UI/controller ownership
remain open. [Memory contract](../project/bluescsi-memory-contract.md),
[lifetime and initialization validation](validation/bluescsi-memory-lifecycle-2026-10-18.json).

## Current status — 2026-10-10 review

Native ROM boot now reaches a colour, mouse-interactive Perform Play screen and loads samples. The banked physical map below is the native reference; flat/HLE mappings and bring-up workarounds are separate historical paths. Peripheral timing and full CPU fidelity remain incomplete.

See the [completion roadmap](../project/completion-roadmap.md) and [native runbook](11-native-boot-and-audio-runbook.md).

## Native wave-memory configurations — 2026-10-14

Native sample RAM is configurable to8,16 or32 MiB (default32), independently of
CPU work RAM. Standalone/VST3 settings expose Wave memory, persisted as
`waveMemoryMb`; direct MAME launches use `S760_WAVE_MEMORY_MB`.
Original OS2.24 System Parameter1 reports8/16/32 Mbyte and90.8/181.8/363.8 seconds.
Native dumps contain8,388,608 /16,777,216 /33,554,432 bytes. Same-size native
checkpoint round trips pass; different-size preflight rejects before restore.
This establishes the available capacity and firmware detection, without adding
claims about physical SIMM timing or completing formatted SCSI sample loading.
[Validation](validation/milestone-5-wave-memory-2026-10-14.json).

## Technical reference and dated milestone history

Milestone labels below apply to their cited finding, not to the present project status.


At that checkpoint: finding58. The experimental IC15 ROM boot now loads all112 OS tracks
and reaches interactive Perform Play. Correct OP-760 identification and live VDP
pointer readback remove the video blockers. New native EEPROM profiles default
to Mouse+CRT at the user's request; existing profiles retain their setting.
Native LCD writes and its screen surface are restored. Rendering, mouse input,
complete chip behavior and power-on bank defaults still need work.


Previous result: finding57. Original IC15 now reads the system disk through the
native FDC/observed IC4 DMA mode, loads all112 tracks (disk4800..1007FF to
RAM0..FBFFF), and enters the disk OS without payload preloading. The ROM path
services timer interrupts and scans the panel, but its CRT remains blank.
Reset bank defaults are experimental; DMA is synchronous and CPU/peripheral
emulation remains partial. The older direct handoff still reaches Perform Play.

**Banked physical map (findings53/54/55) — the leading, schematic-verified map.
The flat "Current MAME map" table below is the superseded comparison baseline.**
Separate fetch selectors 0100..0106 and data selectors 0108..010E give
`(selector<<10)+(CPUaddress&3FFF)`. ROM4FBF loads disk cylinders1..56 (file
4800..1007FF) into physical0..FBFFF; ROM4750 clears0106 and4755 hands off at
CPU **C000** (disk payload backed by physical0), NOT the flat2080.

Device selects at external data page0400 (Service Notes p18, visually checked;
CPU gate IC4 expands A0..A19, IC17/18/19 decode the high bits):

| Device | CPU address | Candidate physical | Notes |
| --- | --- | --- | --- |
| SAMPLE host port (IC27/28 MB87422/23) | C000 | 100000 | addr C00E/C00C; C00A data; poll C000 bit0/bit1 |
| TVF (**IC29 MB87424APF**) | D000 | 101000 | CS_FILT; 101040=channel, 101030=coefficient; flagged and unflagged writes observed — reviews75/76 |
| MEQ control (**IC30 TC24SC220AF-007**) | D800 | 101800 | CS_MEQ; 24-store initialization observed; distinct per-voice registers/attenuation law unproved |
| Pan command aperture (exact chip-select coverage unresolved) | DC00 | 101C00 | 101C00=coefficient, 101C06=tag OR0200; bit9 hardware function unproved — finding76 |
| FDC (uPD72068) | E000 | 102000 | **E000=MSR/auxiliary, E002=FIFO** (not old generic765 at F040) |
| SCSI | E400 | 102400 | Native even-byte register ports at stride2 through E41E/10241E; legacy F020 mapping is separate |
| VDP (RFSC16A) | E800 | 102800 | address E804/E806, data E800/E802, cmd/status E808 |
| I/O | F000 | 103000 | |
| LCD | F800 | 103800 | |

Audio pipeline (finding68, schematic p18): SP2(IC28) → TVF(IC29) → MEQ(IC30) →
dual DAC(IC91/92). **MIDI** (finding73) is on the **CPU gate array IC4**, not the
CPU UART: IN → IC3 PC410 → IC4 RXD pin38; TXD pin37 → IC5 HC125 OUT/THRU.
Firmware byte port 0116, status 0114 bit1 = TX-ready; see document 06.

**External-interrupt stubs (findings73/74):** seven 4-byte stubs at `0120 + 4*i`.
Identified sources — 0: FDC service; 2: wave-related C000/C002/C016 service;
4: completion (sets RB3 bit0); 6: byte-receive handler (→ CD1F) = MIDI. Normal
interrupt mask 0x54 includes bit6. Exact IC4 source arbitration/vectoring is not
yet established (finding74 models source6→0138 as an inferred, opt-in response).

EEPROM (AK93C45-class, 64×16 Microwire) is wired to CPU P1.0/1/2 (CS/SK/DI) and
P2.7 (DO) per p18 — not the old gate-register model. IC15 BOOT ROM gets A0..A14
+ CS_BOOT from IC17 Y7. Opt-in `S760_BANKED_OS=1` executes these real banked
services (reaches Perform Play, finding55); full peripheral/CPU fidelity,
page-register reset defaults/mirroring, and DMA remain incomplete.

**ROM-driven loader map (finding57, `S760_ROM_BOOT`).** The IC15 v1.11 image is
mirrored over physical1E0000..1FFFFF; reset executes at2080 with initial
fetch/data page selectors0780/0790/07A0/07B0, after which the ROM programs the
banks itself. The ROM's functional disk→RAM DMA (decoded at ROM4E97..4FBE /
4FF1..5014):

| Control cell | Meaning |
| --- | --- |
| 0118 | transfer count |
| 0108..010E | destination translated through the four data selectors |
| 011A..011C | resulting 24-bit physical destination address |
| 011D | mode byte `D7` (disk→RAM); ROM4FB1 reuses the same control for track reads |

IC20 (uPD65012) port-B wiring at F002 (Service Notes p18): **PB0=disk-change
(CN5), PB1=density/mode, PB2=drive-select**. Disk-change clears on stepping with
inserted media; density currently derives from image size.

**LCD port orientation (finding58, corrected).** ROM29BC..29E7 writes SYSTEM SET
`0x40` and other commands to **F802**, writes parameters/data to **F800**, and
reads status at **F800**. The command/data ports were previously reversed; native
mode now routes them correctly and exposes the existing LCD rasterizer as a second
screen surface (previously the LCD was omitted from the MAME machine config). The
LCD renderer remains provisional.

**Front-panel scan upper bits = 00 (finding58).** OP-760-1 CN1 pins 49/50 ground
SP6/SP7 (Service Notes p14), so the native scan supplies upper bits `00` while the
low six panel inputs stay independent. ROM3C68 complements the scan; 4143..417E
recognizes complemented `C0` as board-PRESENT. The earlier raw `0x80` complemented
to `0x40` and wrongly selected board-absent (this is what left the ROM path on
Panel+LCD / blank CRT in finding57). `S760_F00A` is an explicit diagnostic
override only. FDC correction: ROM
4A92 writes **0x27** to the FDC command register (NOT START CLOCK 0x47) → the NEC
invalid-command result **0x80**; immediate one/two-byte-result commands no longer
spuriously raise INT (reading the first result byte releases FDC INT, enabling
the following SEEK edge). This DMA is synchronous/functional, not cycle-accurate
DRQ/DACK/TC; the ROM path loads+runs but leaves the CRT blank (VDP activity 0),
and the CPU-gate reset bank defaults still need independent hardware evidence.

Native CPU (findings55/57): a separate **I80C196KB** device adds SFR windows
0/14/15, common interrupt registers (INT_MASK1/INT_PEND1 at13/12), reverse SFR
access, timer writes, and separate capture storage. HSI FIFO, watchdog, full
IOC2/HSO modes, serial timing and external Timer2 remain incomplete.

Verified 2026-10-09/10 against scanned Roland S-760 Service Notes (printed pp.1,
5, 18), the Intel 80C196KB User's Guide 270651-003, the NEC FDC manual ch.4, and
`mame-source/src/mame/roland/s760.cpp`.

## Physical hardware

| Component | Correct identity | Evidence |
| --- | --- | --- |
| Main CPU | **IC1, Intel S80C196KB, 16 MHz**, 16-bit little-endian MCS-96 | Parts list p.5 |
| BOOT EPROM | **IC15, AM27C256-15D**, 256 Kbit = 32 KB | Parts list p.5 |
| CPU gate array | **IC4, HG62E33B08** | Parts list p.5 |
| I/O gate array | **IC20, uPD65012GF-473-3B9** | Parts list p.5 |
| Wave custom SP1/SP2 | IC27 MB87422PF / IC28 MB87423APF | Parts list p.5 |
| TVF | IC29 MB87424APF | Parts list p.5 |
| Mixer/MEQ | IC30 TC24SC220AF-007 | Parts list p.5 |
| FDC | IC24 uPD72068GF | Parts list p.5 |
| SCSI | IC25 MB89352A | Parts list p.5 |
| LCD controller | IC72 SED1335F0B | Parts list p.5 |
| ADC | **IC58 CS5339-K** | Parts list p.5 |
| DACs | **IC91/IC92 AK4328VS-E** | Parts list p.5 |

Specifications p.1: **24 hardware voices**, Differential Interpolation (DI),
16-bit linear sample data, 16-bit A/D, 18-bit D/A, 24-bit internal processing.
Wave memory: 2 MB standard, up to 32 MB. Sampling rates: 48, 44.1, 32, 24,
22.05, 16 kHz. Capacities: 1 volume, 64 performances, 128 patches, 255 partials,
512 samples. Outputs: two stereo pairs / four individual outputs. LCD: 160×64.

The software models allocate 32 voice slots; that is not hardware polyphony.
Earlier documents naming IC20 as either ROM or CPU, an AK5339 ADC, or eight
individual analog outputs are incorrect against this primary reference.
Historical `ic20_hle_*` names are retained only for code/path continuity.

The OP-760 video subsystem is modeled as RFSC16A with 128 KB VRAM. A complete
hardware register specification still requires evidence; see document 03.

## Current MAME map

This is the **implemented bring-up map**, not a complete physical chip-select
schematic. `machine_start()` installs resident RAM, then narrow peripheral
handlers over it.

| Address | Current backing / behavior |
| --- | --- |
| CPU operands below `0100` | Internal registers/SFRs in `AS_DATA`; external `AS_PROGRAM` is a different view |
| `0000–1FFF` program space | Work RAM with selected firmware RET read handlers |
| `0102/0104/010A/010C` | Software dispatch/parameter slots |
| `2000–207F` | Vector RAM; timer `200A → 2B51` |
| `2080–FFFF` | Resident OS RAM, overlaid by handlers below |
| `D000–D0FF` | VDP |
| `E000–E003` | LCD: E000 command/status, E002 data |
| `F000–F01F` | Gate array |
| `F020–F02F` | SCSI |
| `F040–F047` | FDC |

**File = runtime + `0x2780`** for resident `2080–FFFF` only: file
`4800–1277F`. This describes the current flat preload, not established hardware
banking. Shared38 and52 leave fetch/data selection and loaded-code backing open.
Later disk resources are not automatically mapped by this formula.

The old E000–EFF7 LCD handler consumed resident code; the four-byte window is
the correction (finding 13 and installed handlers). Historical D800 palette,
C000/C400, and D400 labels do not mean those ranges currently have installed
peripheral handlers. Disk reset sets SP=1120. MAME uses `N8097BH` with added
196 opcodes and boot workarounds; it is not yet an exact S80C196KB model.


### Early SDS cancellation rollback repair (2026-10-18)

The twenty-fourth checkpoint fixes BUG-125 in experimental firmware. A receive header immediately followed by CANCEL previously left one reserved block unreachable: idle cursor3 with only two samples, then retry at block3/cursor4. Two of three prior-image controls reproduce it; the session-start burst does not admit the receive and therefore does not test rollback. The new31-byte helper retains receive cancellation as stateFE for active1, completed-but-unpublishedFF and already-cancelledFE, while other owners keep generic0A. FE follows the existing receive rollback path; duplicate CANCEL cannot erase its ownership. Ten native cases cover ordinary/session entry bursts, duplicate cancellation, a one-packet completion/CANCEL boundary, active receive cancellation, remote cancellation/timeout and local cancellation/full completion. All end with three samples/cursor3 and exact480 received PCM bytes each; 118 sent packets match. Including controls, 181 snapshots preserve both seed descriptors and allocations. All113 focused tests and ordinary native playback/MIDI/audio pass. The helper adds no RAM or call frame; total proposed code use becomes2,402 bytes, leaving672 arithmetic bytes (641 contiguous after0ABF). Exact pre-supervisor instruction ordering remains unproved because an exploratory read tap targeted the replaced entry instruction; ownership writes prove the defect and rollback. Complete memory/stack fit, remaining timing and transactional stereo/bounded WAV writing remain open. [Early cancellation evidence](validation/bluescsi-early-cancel-2026-10-18.json).


### Combined diagnostic placement (checkpoint25, 2026-10-18)

The twenty-fifth checkpoint qualifies a combined diagnostic layout in the native emulator. The old 4 KiB transport buffer overlapped the SDS helpers by703 bytes. Relocating the buffer to physical004940, the480-byte case table to0046C0 and640-byte records to005944 removes that collision. All20 transport cases pass, including expected status/sense errors and timeout recovery. A separate panel Exit run latches cancellation after629 bytes, drains the current4096-byte read and starts no later command. Both runs subsequently load13 HDD samples with all119808 PCM bytes exact and pass playback/silent release. Eight RAM snapshots preserve all code, SDS patch spans, the case table and354 seeded gap bytes. This qualifies coexistence for these workflows; SDS cancellation/retry execution after transport remains to be tested. Retained code is2402 bytes; the production budget still leaves only672 arithmetic bytes, with browser UI, WAV parsing, stereo transactions and full stack bounds unmeasured. BS1 remains OPEN. [Evidence](validation/bluescsi-combined-layout-2026-10-18.json).


### Post-transport receive rollback (checkpoint26, 2026-10-18)

Checkpoint26 qualifies SDS receive cancellation and retry in the same native session after the combined transport diagnostic and HDD Load. One run executes all20 transport cases; another cancels the first read after629 bytes and drains it safely. A third run uses the prior SDS-only image without the diagnostic as a comparison. All three load13 samples, then show actual header admission (cursor13 to14), receive cancellation stateFE, rollback at0166:8B6B to13, and idle before retry. Cancellation-to-idle spans1.995390�1.996954 seconds in these runs. Retry reserves block13 and publishes the fourteenth live sample with160 exact received PCM bytes. All119808 existing HDD PCM bytes and13 descriptors remain exact; preceding playback/release and unchanged HDD export pass. The16 combined-image snapshots preserve all patch spans, code, case table and354 seeded gap bytes; the comparison adds seven snapshots. An initial exploratory two-second assertion caught FE after rollback but before cleanup ended; it is not an acceptance pass or evidence of a leaked allocation. The repeated traced runs establish cleanup and retry; the final cancellation run allows four seconds. No firmware repair was needed for this timing assertion. BS1 remains OPEN for full code/UI/WAV sizing, stack bounds, bounded sample writing and atomic stereo publication/rollback. [Evidence](validation/bluescsi-combined-lifecycle-2026-10-18.json).

**Latest IM1 allocation (2026-10-19):** 5408/8002 bytes,2594 free/2106 code-adjacent. Fresh-entry reset and native Save System export/cold exact Load/playback pass. Prior footprint figures below are historical. External checkpoint/reset, full stack and physical qualification remain open. [Validation](validation/bluescsi-im1-entry-state-2026-10-19.json).

**Previous help/identity IM1 allocation (2026-10-19):** Contextual CRT help/collection identity and cold-entry render fix use5393/8002 bytes, leaving2609 total and2121 directly after code. Browser physical4080..4CB7,280 string bytes5500..5618; existing224-byte page buffer57F0 and remaining descriptors/context retain their addresses. Two final-hash native workflows and exact rebuild pass. Earlier4982-byte page-window figures below are historical. Full stack/ISR, controller/LCD, Save System cold-state and physical gates remain open. [Validation](validation/bluescsi-im1-help-identity-2026-10-19.json).

## Private IM1 packed OS allocation (2026-10-19)

One measured, opt-in firmware candidate packs the mandatory v9 GB-6 browser with retained SDS repairs into the8002-byte zero-filled OS region at physical3D3E..5C7F (disk853E..A47F). This is a private linked layout, not the original OS or a global free-space reservation. GB-6 baseline sites remain separate and unchanged.

| Owned item | Physical start | Bytes | Access in this candidate |
| --- | --- | ---: | --- |
| SDS remote helper |3D3E|640|fetch000F:013E|
| SDS local owner |3FBE|160|fetch000F:03BE|
| SDS early cancel |405E|31|fetch000F:045E|
| Browser/shared callbacks/sender |4080|2278|fetch000F:8480|
| One100-row listing |49A0|4000|data000F:4DA0|
| UI resources |5940|639|data000F:5D40, alias9D40|
| Context |5BC0|92|data000F:5FC0|

Intervals do not overlap; named total7840, residual162 in gaps. Native browser/SDS sequential acceptance preserves all code. UI geometry/context is intentionally mutable. Shared callbacks use an80-byte local frame before native caller/ISR depth. Discovery and complete admission/cancellation/recovery are still excluded; this is not a complete-fit result. [Layout, sources and evidence](validation/bluescsi-im1-packed-sds-2026-10-19.json).


### IM1 compact listing and selected-target discovery successor

The next mandatory GB6-v9/browser/SDS build uses7583/8002 named bytes:831 retained SDS helpers at physical3D3E/3FBE/405E;2577 browser bytes at4080;3400 compact listing bytes at4B80 (data000F:4F80);683 resource bytes at5900 (data000F:5D00, UI9D00);92 context bytes at5BC0 (data000F:5FC0). Each40-byte D7 wire row retains index/type/all32 name bytes and discards the terminator/size, without borrowing native disk buffers. Residual419 is split3/239/56/21/100 bytes;239 after code is the largest code-adjacent gap. This supersedes the7840-byte partial census. Native exact100-row comparisons,0/1/100/101 boundaries, configured-target discovery/rejection, ISO loading/playback and receive-modal exclusion/cancel/retry preserve code and prior samples; exact exclusive rebuild passes. Callback local frame remains80 bytes, excluding full native caller/ISR depth. Complete ownership/cancellation/recovery/UI and physical timing remain open; no complete-fit GO. [Evidence](validation/bluescsi-im1-discovery-fit-2026-10-19.json).


### IM1 scoped cancellation and paced-readiness layout

The next mandatory GB6-v9/browser/discovery/SDS build supersedes the7583-byte census:7835/8002 named bytes, comprising2773 browser bytes at physical4080 (fetch000F:8480),831 unchanged SDS helper bytes,3400 listing bytes at4B80 (data000F:4F80),739 resource bytes at58D0 (data000F:5CD0/UI9CD0),92 context bytes at5BC0 (data000F:5FC0). Residual167 is split3/43/8/13/100; only43 contiguous bytes remain after code. No native buffer is borrowed. Operation cancellation resets once per action; successful command drain preserves raw status/transport and returns7 when Exit is latched. Post-D8 interruption queues no Load and requires fresh selection. Four readiness probes are paced20ms apart with timer/poll bounds. Native cancellation/retry/exact ISO Load/SDS, silent-open failure/other-target recovery and0/1/100/101 catalogs preserve all code/library bytes; exact rebuild and immutable originals pass. Callback local frame80 excludes deeper helpers/native callers/ISRs. IRQ-masked SCSI remains a production timing/ownership gate; full fit is OPEN. [Evidence](validation/bluescsi-im1-cancel-recovery-2026-10-19.json).


### IM1 conditional IRQ service and native receive admission

The next mandatory GB6-v9/discovery/browser/SDS candidate supersedes the7835-byte partial census:7876/8002 named bytes,2814 browser bytes at physical4080 (fetch000F:8480),831 SDS helpers,3400 listing bytes at4B80,739 resources at58D0 and92 context bytes at5BC0. Residual126 is split3/2/8/13/100; only2 code-adjacent bytes remain. Caller DATA1/WSR-MASK1/PSW-MASK0 are captured at stack offsets70/74/76 before dispatcher-return push. Service uses the saved I bit/masks, never unconditional EI.188 matched service pairs preserve34 scratch words and advance only RW38 by measured modulo16-bit service ticks; total elapsed/poll limits remain unchanged.128-clock and21-byte-header runs exercise2/1 service timer wraps and reach observed extra stack192 bytes below callback entry. The80-byte local frame is not the whole depth; full caller/ISR bounds remain open. Entry/post-catalog/post-mount checks of native2BBA reject newly acquired receive ownership before publication/drive/Load. Incoming header listing drains4000 bytes before Busy; post-mount claim blocks handoff, and cleanup/explicit retry loads119808 exact bytes. Static targets, code preservation and fresh exact rebuild pass. Further features require savings/repacking; full fit/hardware remain OPEN. [Evidence](validation/bluescsi-im1-irq-ownership-2026-10-19.json).

The next compact-catalog candidate retains the D7 mount index and all32 filename bytes in33 bytes, discarding the constant file-type byte on the directory-free stock CD picker. Wire input remains40 bytes/record. Moving3300-byte storage to physical4BE0 gives7776/8002 named bytes,226 free and98 contiguous after2814-byte code; mandatory v9 GB-6 and retained SDS helpers remain included. Six native workflows pass: exact0/1/100 records and101 rejection, cancellation/retry/exact Load/playback/SDS, failed mount recovery, incoming SDS during list/mount and128 MIDI clocks during D7. Exact rebuild and immutable originals pass. Full admission/UI/fit/stack/media/controller/hardware gates remain open;1FA4 is a Remote Mode session flag, not generic disk ownership. [Results](../project/bluescsi-im1-catalog33-results-2026-10-19.md), [validation](validation/bluescsi-im1-catalog33-2026-10-19.json).

BUG155 is reproduced on the prior browser: manufacturer41 Remote Mode1FA4 becomes pending while SDS2BBA stays0, yet D8 readiness commits native drive1/handoff7601. A specific shared1FA4 check at entry/catalog/mount adds10 bytes and refuses publication/Load with Busy, retaining drive8 and handoff0; both paired race tests recover after session exit. Eleven primary native cases pass:2 races,5 Remote Mode cases and4 browser regressions. Complete116-packet/9216-byte send and160-byte receive publication are exact. Complete/cancel/timeout restore40 scratch words/selectors/WSR at the caller. Deferred exit first differs in3 scratch words at the later continuation; a twelfth native run confirms isolated helper restoration and a matching continuation. Original differing rows remain; broad ISR/caller proof stays open. Mandatory GB6-v9 remains at7786/8002,216 free/88 code-adjacent; exact rebuild passes. General disk/external-session safety, full fit/stack/UI/media/controller/hardware gates remain open. [Results](../project/bluescsi-im1-session-admission-results-2026-10-19.md), [validation](validation/bluescsi-im1-session-admission-2026-10-19.json).

Native Disk options preserves all9 stock actions via0196:94D9 instead of a second menu clone (BUG156). Eight native screens and corrected Volume Dump FD warning/cancel are observed; BUG157 fixes its initial OS-Load mislabel. Browser ISO index99 -> separate private10MiB HD0 initialization/Save/export -> fresh cold Load preserves13 allocations/119808 exact bytes and playback peak. New32-byte records validate every D7 index as its ordinal before implicit storage;25700 decoded cases and native0/1/100/101/index99/cancel/SDS/Remote Mode checks pass. Current7918/8002 has84 free/68 code-adjacent, mandatory GB6-v9 and exact rebuild retained. Full persistence uses the preceding label variant; final labels change only the text table and one immediate pointer, with warning/cancel and rebuild acceptance. Malformed-index native draining, concurrent operations, full UI/fit/controller/media/stack/hardware gates remain open. [Results](../project/bluescsi-im1-disk-operations-results-2026-10-19.md), [validation](validation/bluescsi-im1-disk-operations-2026-10-19.json).

Visible-page catalog storage reclaims2936 net bytes in the same candidate:3200 ->224 data bytes for40 added code bytes. The full D7 stream and all indices are still validated, retaining seven32-byte names; Next/Previous reread DA/D7. Current4982/8002 leaves3020 free,3004 directly after code. Nine native workflows on the same hash cover all100 names forward/back, shrink clamp, failed refresh/no stale mount, boundaries, exact Load/SDS/cancel/recovery, HDD Save/export/cold Load, Remote Mode and128-clock/SDS-during-Next IRQ service. Index/window models cover25700/10000 cases; exact rebuild and originals pass. Catalog rereads measure median349.998ms from DA-end to D7-end, not physical latency. Scoped extra stack reaches194, not a full bound. Remaining UI/policy/controllers/media/concurrency/stack/hardware and full feature fit remain open; another RAM region is deferred. [Results](../project/bluescsi-im1-page-window-results-2026-10-19.md), [validation](validation/bluescsi-im1-page-window-2026-10-19.json).


## IM1 fresh-entry and Save System cold-start update - 2026-10-19

BUG-160 is fixed by clearing76 operation bytes on every browser entry, preserving16 callback-save bytes. A native stale-catalog baseline fails as expected; fresh reentry and actual Save System export/new-process cold boot rebuild Collections before commands. Saved stale page/labels remain on disk but cannot be selected; explicit new catalog/index0 Load restores119808 exact bytes with playback/release. Final-hash cancellation/SDS and rebuild pass. Footprint5408/8002,2594 free/2106 code-adjacent supersedes earlier values above. External checkpoint/device reset reconciliation, live collection mutation, controller/LCD, full stack and physical gates remain open. [Validation](validation/bluescsi-im1-entry-state-2026-10-19.json). Finding283.


## Current IM1 allocation and bounded custom stack (2026-10-20)

OS6297274d... measures6452/8002 bytes:3916 browser code,831 retained SDS helpers,739 CRT resources,312 strings,238 LCD descriptor/temporary storage,224 page buffer,92 context and100 Disk labels.1550 free/1332 contiguous after code. All custom-body paths balance; maximum166 stack bytes includes80-byte common frame and excludes native callees/IRQs.366 snapshots preserve7360 immutable/gap bytes;642 explicitly mutable bytes are excluded. Parent workflow observes216 bytes below initialSP1120; MIDI service observes192 below callback entry, a different origin. Full native stack/service-time/indirect-alias bounds remain OPEN. [Validation](validation/bluescsi-im1-closeout-2026-10-20.json).


The later current-OS analysis resolves a152-function/9181-instruction IRQ graph under recorded fetch-page and jump-table state assumptions. Timer entry14 + control36 + one non-nesting wave-end ISR12 gives a conditional62-byte contribution. This excludes the full native caller/callee chain, other Disk/FDC owners and unproved mutable-state invariants; it is not a total bound when added to166 custom bytes. MIDI parser000F:213A drains a live ring with arrivals enabled and no identified service quota, so maximum service time remains open. No allocation or OS bytes changed. [Latest analysis](../project/bluescsi-im1-final-gates-results-2026-10-20.md), [validation](validation/bluescsi-im1-final-gates-2026-10-20.json).


## IM1 dense-MIDI timing counterexample (2026-10-20)

Unchanged6297274d... preserves all7360 immutable/gap bytes across177 new native snapshots (642 mutable excluded). Allocation remains6452/8002,1550 free/1332 adjacent; complete indirect-alias and native caller/callee/ISR bounds remain open. Dense notes during D7 preserve769 MIDI bytes and188 matched service contexts; lowest observed SP1030 is not a worst-case bound. One service lasts479.111125ms: timer-read interval479039 ticks gives modulo delta20287, omitting458752 ticks/seven wraps. BUG-168 tracks bounded service and wrap-safe outer elapsed accounting. Correct modulo RW38 idle adjustment does not recover lost whole wraps in the total deadline. [Results](../project/bluescsi-im1-safety-batch-results-2026-10-20.md), [validation](validation/bluescsi-im1-safety-batch-2026-10-20.json).


### Browser parser admission and memory limits

Experimental OS367f067d... adds an89-byte native parser-admission helper at000F:1400 (physical005000, file009800), reached by the3-byte hook at000F:213A (file00A53A). Context word005BDA holds32 admissions while browser service is active;16000 timer ticks stop further admission, and masked continuation scheduling preserves pending MIDI. Outside service the original parser path is retained. Exact rebuild/disassembly and GB-6 v9/SDS checks pass. Allocation6580/8002 leaves1422 free; largest remaining code gap1191. This does not promote the experimental hash over established6297274d... .

Dense MIDI parses775 bytes exactly, has no observed overflow, preserves188 service contexts and releases notes; maximum28.006625ms and no lost whole timer wraps are observed. BUG168 remains IN-PROGRESS because the single-byte/control-ISR bound and total wall-time deadline are unproved. The helper adds8 local stack bytes; this and the earlier166-byte custom/conditional62-byte IRQ figures are not a composed native bound. All7360 immutable/gap bytes survive111 new snapshots (18 established,93 trial), with642 mutable bytes excluded; the trial hook is also preserved. Indirect aliases/DMA and native stack remain open. [Results](../project/bluescsi-im1-timing-recovery-results-2026-10-20.md), [validation](validation/bluescsi-im1-timing-recovery-2026-10-20.json).


### IM1 synchronous native-callee stack contract (2026-10-20)

The timing candidate367f067d... now has a complete synchronous-callee analysis
for its ten browser helpers:46 contextual functions,904 unique instructions,
balanced returns and no unresolved edges. Audited CE14/CDED wrappers contribute
12 saved bytes plus a two-byte synthetic return; the caller LCALL is accounted
at its actual depth. Including the80-byte common frame, action/Exit/init/update
maxima are166/90/112/166 bytes. The166-byte bound now includes synchronous native
callees. Dispatcher ancestry and IRQ nesting/state invariants remain outside it;
the conditional62-byte IRQ result cannot simply be added into a total bound.
The updated trial IRQ graph has152 functions/9212 instructions. Indirect aliases
and DMA ownership remain open.

Eleven new native cases preserve all7360 immutable/gap bytes in91 snapshots,
excluding642 declared mutable bytes. Wording-only successors ecdbd721...
(established) and79124692... (timing trial) change four native warning resources
outside the browser allocation. They retain6452/8002 and6580/8002 bytes, with1550
and1422 free respectively; the trial's largest code gap remains1191 bytes.
No additional boot-ROM space is used. The trial remains unpromoted.
[Evidence](validation/bluescsi-im1-format-fdc-stack-2026-10-20.json).


## IM1 native bounds and unchanged allocation (2026-10-20)

The four immediate init/update/exit/action dispatcher frames each use12 bytes (five saved words plus synthetic return). Observed outer prefixes28/30/62 are route observations, not global maxima. The prior166-byte synchronous and conditional62-byte IRQ figures are not an additive total proof. Parser000F:25A6..25FC has at most32 comparisons per sentinel scan and528 total across32 insertions into16 records of33 bytes, assuming no concurrent external writer. Native MIDI TX-ready001F:68A2 and wave-port-ready7118/7344 still need completion bounds.

Same-size Verify Medium repair leaves established6452/8002 and trial6580/8002 allocations unchanged. Nine accepted native cases/93 snapshots preserve7360 immutable/gap bytes with642 mutable exclusions. Simultaneous stalled-target/MIDI fails the byte check; full native timing/ownership remains open. Evidence: [validation](validation/bluescsi-im1-verify-stall-bounds-2026-10-20.json).


## IM1 repaired redraw and authored-image loading (2026-10-20)

Candidate5e5ec016... adds3 bytes to call the existing caller-qualified service between880 CRT character clears. Both actual simultaneous D7 stall/MIDI cases (byte1/3999) preserve775 reads,239616 stereo bytes and playback/release. Original dense D7, CRT/LCD cancellation/names, SDS and Remote Mode regressions pass:10 native cases/104 snapshots. BUG175 is fixed independently of BUG168, whose full service/deadline proof remains open. Allocation6583/8002 leaves1419 free; synchronous stack166 bytes unchanged, no total IRQ/ancestry proof. GB-6 v9/boot/SDS/Verify Medium/warnings retained. BUG174 fixes the minimal authored header and tests first real ROM handoff with112 tracks/all1032192 loaded bytes; no runnable-example-OS claim. Full suite1089 pass/3 skip, no failures. Physical qualification and upstream BlueSCSI defects remain separate. BUG140's abandoned descriptor experiment is WONTFIX, not repaired. [Evidence](validation/bluescsi-im1-bug-fixes-2026-10-20.json).


BUG168 native policy successor (2026-10-20): e78750c2... uses6736/8002 named bytes (1266 free), main browser4111 bytes atphysical4080..508E, existing89-byte parser helper at5100..5158,935 contiguous bytes before5500. C+30 saves native performance mode; C+31 leases action suspension. Boot and GB-6 v9 unchanged. The earlier166-byte synchronous stack bound is not a current complete bound: include native001F:4F8D and its callees. See docs/project/bluescsi-bug168-native-policy-results-2026-10-20.md and docs/condensed/validation/bluescsi-bug168-native-policy-2026-10-20.json.


Current experimental OS606e277e... (2026-10-21): browser4135 bytes atphysical004080..0050A6 (end0050A7 exclusive); parser helper005100..005158 unchanged;89-byte gap before helper,935 bytes after it before005500. Named6760/8002 bytes leaves1242 free. Owner rechecks add24 bytes without moving data/context/SDS/GB-6 regions. Conditional named-route stack envelope284 bytes assumes20/20 masks and declared native states; stack-region/alias/physical DMA ownership remains unproved. See docs/project/bluescsi-im1-owner-and-recovery-results-2026-10-21.md and docs/condensed/validation/bluescsi-im1-owner-and-recovery-2026-10-21.json.
