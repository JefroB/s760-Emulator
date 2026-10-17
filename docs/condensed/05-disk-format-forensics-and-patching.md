# Disk Format, Forensics & Patching

## Full native Roland SCSI performance Load — 2026-10-14

The complete606,709,760-byte JMD S760 freeware CD now boots as an external CD1
profile, reports Formatted, lists all10 volumes and loads K4 :KAWAI K4 through
normal Disk/Load. The firmware restores its native performance/patch/partial
hierarchy; no Akai conversion or host-generated sample injection is involved.
All79 K4 sample allocations/6,054,912 bytes match independent source FAT-chain
reads exactly. Three channel1 drum notes and channel2 note60 produce bounded
finite audio and release to a full silent second. Two cold processes replay
65536 stereo frames exactly; changed-CD preflight rejects before native restore.

BUG-070 separated immutable CD identity from mutable state: both managed
launchers stream-hash recognized CD filenames, allowing1 GiB aggregate read-only
CD content, while writable SCSI media retain64 MiB aggregate checkpoint storage.
CD contents are excluded from native machine state; the imported session is
171,072,219 bytes. Mounted CD writes still fail before DATA OUT. External CD
filename/content are required on recall; this guard belongs to managed launchers.
Older-build checkpoints reject by build identity; no migration is qualified.

BUG-071 implements observed SCSI-to-wave DMA84. Native code page003B:7CD0..7D29
programs wave address and gate count then waits for SPC completion. The gate
carries the low16 bits of the full24-bit SPC length; treating a118,784-byte
request as53,248 leaves65,536 bytes pending and freezes firmware controls.
Bounded36/65,536/118,784-byte regressions, counter/address advancement, invalid
bounds and CD write rejection pass. Prior RAM47/PIO/register contracts remain
qualified;389 backend tests, core/plugin units, full-CD C++ host playback and
writable-SCSI checkpoint recall pass. All changed artifacts build successfully.

The qualified scope is this CD1/2048-sector image and first K4 performance at
32 MB RAM. Other volumes/libraries, SCSI Save, hot-plug, physical arbitration and
final packaged interface repetition remain separate work.
[Exact identities, commands, source samples and limits](validation/milestone-5-roland-scsi-load-2026-10-14.json).

## Genuine Akai S1000 SCSI Convert Load — 2026-10-14

Original IC15/OS2.24 imports the first volume of the supplied String.Ensembles CD
through CD1,2048-byte sectors and32 MB wave RAM. Convert Load produces the
VI LONG FF patch and30 samples, totaling13,568,196 PCM bytes. The imported patch
is then assigned to performance part1 through the firmware's Value control.

A bounded independent reader follows the fingerprinted volume directory/FAT and
150-byte S1000 sample headers. Every source PCM word matches native wave RAM
except107 words in the four-word regions after aligned loop boundaries.
A read-only native wave-port observer records240 writes without drops: source
values are first transferred correctly, then the original firmware rewrites
those regions. Converted values match those writes exactly. The complete32 MiB
wave dump is byte-identical to an unobserved fresh conversion. This is observed
firmware conversion behavior, not proof of physical loop/DSP equivalence.

MIDI55/72/96 produce finite bounded output and release to a full silent second.
The source and private CD backing hashes remain unchanged. Two fresh processes
restore the imported session and produce65536 identical stereo frames, then
release silently. Backend388 regressions pass. Failed exploratory probes
included an insufficient45-second conversion wait, audition before assigning
an imported patch, and overbroad diagnostic capture; these are not product fixes.

This qualifies one genuine Akai CD/volume/program through native firmware;
at that checkpoint native Roland-format Load was still pending. The later full
Roland qualification is above. Other Akai CDs/device profiles, SCSI Save/writeback,
hot-plug and final packaged media selection remain unqualified.
[Exact fixture/artifact identities, command and results](validation/milestone-5-akai-scsi-load-2026-10-14.json).

## Native SCSI prerequisite correction — 2026-10-14

Original IC15 initialization accesses the SPC registers at E400/E402/E404/E408,
physical102400/02/04/08. Native decoding now uses a two-byte stride through the
16-register address window; TEMP and transfer-counter ports are accessible.
Native SELECT uses command20 and reports command-done10 or absent-target timeout04;
INTS reads preserve pending status until explicit write acknowledgement. Controller
reset uses SCTL40, bus reset SCMD10. These definitions agree with the
[original NetBSD MB89352 register header](https://raw.githubusercontent.com/NetBSD/src/trunk/sys/dev/ic/mb89352reg.h)
and the isolated native register fixture. Synthetic blank targets0/1 are retained
only for the legacy flat/HLE device fixture; native targets require supplied files.

Native SSTS now reports idle empty-data/zero-counter as 0x05 rather than the
incorrect constant 0x28 (busy/reset). TC-zero follows the programmed counter;
reset follows SCMD assertion/deassertion. The failing-before/passing-after native
fixture also checks idle recovery after absent selection. BUG-065 is fixed for
this direct-data status contract; this does not add an asynchronous FIFO engine.
[Status regression and native/state evidence](validation/milestone-5-scsi-status-2026-10-14.json).

## Native SCSI discovery and unsupported-media recovery — 2026-10-14

Native BDID reads now expose1<<ID and ignore upper write bits. SELECT uses TEMP,
excludes the initiator bit, and times out on empty/initiator-only masks without
reusing an old target. Original firmware page003B:75FE..7634 writes command bytes
through TEMP and handshakes SET ACK E4 / RESET ACK C4; the native controller now
drops/reasserts REQ accordingly. Programmed-input reads decrease the SPC counter,
and status/message ACKs release the bus.

Observed firmware DMA47 (page003B:7724..778C) now transfers bounded SPC input into
RAM, advances destination and exhausts gate/SPC counters. Oversized and out-of-RAM
fixture requests leave data/counters unchanged. This implementation is synchronous;
other controls, output DMA, zero-count conventions, native IRQ priority and exact
hardware timing remain unqualified. Legacy flat behavior stays separate.

Original IC15/OS2.24 now identifies a private HD0/512-byte-sector target rather
than listing every supplied device as No Drive. Three fresh-machine cases qualify
absence, a zero-filled10MiB image and a truncated1024-byte image. Absent target
shows No Drive; both unsupported images show Unformatted and emit Not Formatted
on selection. Each case returns to a real floppy Load, verifies all119808 sample
bytes, plays/releases to a full silent second, and preserves both source/backing
images with idle/clean media. Firmware-issued512-byte DMA completions are logged
for present targets. Command traces are bounded and drop rows in present cases;
no exhaustive bus/arbitration claim is made. Late absent-case trace has no commands,
so no claim is made that every absent ID is actively reselected by that UI action.

Isolated before/after regressions cover eight initiator IDs, seven present-target
INQUIRY selections, command/PIO and DMA/bounds. Original-firmware native audio/MIDI,
131072 exact cold stereo frames/refreshed displays, legacy transfer/state and363
backend tests pass on the complete fix. Intermediate BDID-only and PIO-only builds
exposed two firmware stalls; both are resolved rather than accepted as regressions.
BUG-066/068/069 are fixed for this bounded contract.

At this discovery checkpoint, genuine formatted SCSI sample Load was unqualified.
The later Akai Convert Load subset is qualified above; native Roland performance
Load and SCSI Save remain separate pending work.
[Exact identities, commands, failures, firmware cases and limits](validation/milestone-5-scsi-discovery-2026-10-14.json).

The owner manual Advanced3-104 (PDF page128) states that System LoadPRM/SavePRM
transfer settings between internal and System Backup memory. This is not a disk
operation and cannot establish concurrent disk/MIDI/voice coverage. Earlier local
screen notes incorrectly described disk storage; BUG-067 corrects those notes.
Advanced5-15 (PDF page153) describes the drive Scan action. The firmware verifier
uses the actual Scan widget and panel action; screenshots identify reviewed OS2.24
labels, not generalized OCR.

## Native persistence checkpoint — 2026-10-11

Firmware Save now completes observed IC4 DMA modes FA (RAM to floppy) and E2
(wave memory to floppy). Original OS bytes at file01DC41 onward program the
wave address at C00C/C00E, count1200 and controlE2; the runtime trace confirms
the subsequent WRITE DATA45. These are bounded synchronous transfers, not proof
of exact controller timing or complete FDC behavior.

The standalone exports actual controller media to a new image after firmware
Save. A fresh-machine reload preserves all13 generated sample payloads used by
the88-key ROBOFULL fixture:119808 bytes, with note60 playback and silent release
verified. High wave-memory records differ across save/reload, so full session
state equivalence is not claimed. Library originals remain unchanged.
See [reproducible evidence](validation/native-media-2026-10-11.json) and
[the player runbook](../emulator/guides/standalone-player.md). Busy or dirty controller media
now rejects replacement/ejection. Export acknowledges only its captured revision
after host publication; subsequent writes remain dirty. Native regression covers
134 writes, rejected changes, export, ejection/reinsertion and fresh reload.
OS 2.24 empty-drive behavior is now qualified: Disk/Load requests insertion,
emulated time advances, empty export fails, and reinsertion loads ROBOFULL.
Standalone Eject waits for controller acknowledgement and preserves busy/dirty
protection. Loaded sample playback/release survives ejection. The supported
same-build standalone session profile restores embedded floppy/sample memory
after source-library removal and firmware-path relocation, with 131072 exact
stereo frames and refreshed CRT/LCD bytes. Browser version/build diagnostics
preserve the live patch on rejection. See
[current media/session evidence](validation/standalone-media-session-2026-10-12.json).
Standalone now also maintains a separate automatic recovery checkpoint every60
host seconds after observed boot, plus a checkpoint on normal desktop close.
Dirty media and sampler RAM are retained independently of manual saves/exports.
Startup/restart hold existing recovery until explicit restore or replacement;
save failure cancels normal close and retains the old archive. Native dirty
revision134 child-failure/close replay reproduces131072 stereo frames/both
displays and exact disk bytes. Production timer/restore/explicit quit and desktop
close pass in the updated package. Recovery ends at the last successful
checkpoint; later edits, forced termination, physical-MIDI/busy/error delays,
broader formatting profiles and firmware SCSI saves remain limitations. See
[automatic recovery evidence](validation/standalone-auto-recovery-2026-10-12.json).
External SCSI backing filenames/content remain prerequisites.

Floppy write protection is now controller state: ST3 WP is reported, protected
WRITE DATA/FORMAT returns ST0 abnormal termination with ST1 not-writable, and
absent-media writes return not-ready. Host protection changes reject busy/empty
controllers; insert/eject resets protection. The bit is serialized in native
checkpoints. OS 2.24 Save visibly reports Write Protected, with an exact unchanged
export and revision zero. Cold process recall preserves protection. Turning it
off permits 134 write revisions, export, fresh reload of all 119808 sample bytes
and native note60 playback/release. The actual packaged browser verifies control
acknowledgement, reconnect, reset and recalled protection. This is a Windows
development/OS 2.24 qualification, not physical FDC timing or a clean-machine
release. See [write-protection evidence](validation/standalone-write-protection-2026-10-12.json).
BUG-041 is now fixed for OS 2.24 standard 720KB native formatting. Firmware at
physical0188E4 supplies 4D with SC09, fill0F and FA RAM DMA count0024 from083E0E.
The driver validates a complete CHRN descriptor set (cylinder/head, unique sector
IDs, size, source/count and media bounds) before filling a track and advancing
DMA. Unsupported transfers return an error without mutation; PIO and nonstandard
sector layouts are unsupported. All160 tracks plus the firmware header write
produce revision161. Protected Format leaves the original bytes unchanged;
dirty formatted bytes/revision recall exactly in a fresh process. The exported
formatted image contains the firmware's S-760 Formatted Disk Ver. 2.24 header
and733184 verified fill bytes beyond the first4096 bytes. Save afterward reaches
revision295, then export/fresh reload preserves all13 sample payloads and audio.
The actual packaged browser verifies Format/export fill and retained sampler
memory before reconnect/restart/recall. HD/foreign media and physical FDC timing
remain unqualified. See [format evidence](validation/standalone-formatting-2026-10-12.json).

## SCSI device write contract

WRITE(6)/WRITE(10) commit a complete payload to private target memory at the
requested LBA. The original library image is unchanged. Incomplete or reset
transfers leave sectors unchanged. CD-ROM writes reject with DATA PROTECT
(7/27); out-of-range reads/writes reject with ILLEGAL REQUEST (5/21). Sense is
per-target and included in checkpoints. Zero count in a ten-byte command
completes immediately; WRITE(6) count zero transfers 256 blocks.

The generated-media device probe verifies readback, neighboring sectors,
protection, range failures, reset interruption, and warm/cold recovery of a
partial nonzero-LBA write. This fixes BUG-015's discarded-payload defect, not
firmware SCSI Save/reload or host-file export qualification. Those workflows
remain open. See [validation](validation/s2-scsi-and-stack-2026-10-11.json).

## Earlier format research

Updated mapping evidence (findings53/54): ROM loader copies file4800..1007FF
to physical0..FBFFF and jumps CPUC000. Banked fetch/data addresses use separate
selector sets. The runtime+2780 relation below applies only to the old flat
preload; it does not describe the real loader handoff or prove banking unnecessary.

Condensed 2026-10-09 from the original overview, disk map, CPU investigation,
manuals guide, emulation specification, findings log, and string/forensics catalogs.
See [source map](source-map.md) for the complete input list. Offsets below are
**disk file offsets** unless explicitly marked runtime.

## Artifact and layout

`S760224.IMG` is 1,474,560 bytes (`0x168000`): 80 cylinders × 2 heads ×
18 sectors × 512 bytes. Sector 0 contains `S770 MR25A`,
`S-760 System Disk    Ver. 2.24`, and the Roland copyright banner. It is a
proprietary Roland system disk, not a FAT boot volume. An embedded x86 DOS
formatting template is data used for interchange; it does not identify the CPU.

| File range | Interpretation | Confidence / limitation |
| --- | --- | --- |
| `0x000000–0x0001FF` | Volume/banner sector | Directly identified |
| `0x000200–0x0047FF` | Solid `0x0F` fill | Allocation/free sentinel interpretation remains provisional |
| `0x004800–~0x085FFF` | Executable payload and data | Not one contiguous runtime address window |
| `~0x086000–0x0AFFFF` | UI/resources mixed with other data | Text and descriptor locations overlap this broad classification |
| `~0x087000–0x089000` | UI/MIDI text and DOS template area | Original region boundaries are approximate |
| `~0x0C3000–0x0DDFFF` | Repeating `0x100`-byte records | Preset/parameter role is inferred |
| `0x0DE000–0x0EFFFF` | Zero fill | Reserved/unused interpretation |
| `0x0F0000–0x0F9FFF` | Sparse tables | Directory/secondary-table role unresolved |
| `0x0FA000–0x0FFFFF` | Zero fill | — |
| `0x100000–0x167FFF` | Solid `0x0F` tail | Apparently unallocated |

For resident runtime addresses `0x2080–0xFFFF`, use **file = runtime + `0x2780`**.
The resident slice is file `0x4800–0x1277F`. Later disk content needs its own
loading/mapping evidence; do not apply the formula to arbitrary resources or
interpret file offsets above 64 KB as resident PCs. No resident code banking is
needed to execute the upper `0xE000–0xFFFF` routines.

## CPU identification and inspection

The service notes and coherent reset disassembly establish Intel **S80C196KB**,
16-bit little-endian MCS-96. Earlier i960, 68000, and x86 interpretations are
superseded. Payload entropy around 6.3–6.8 bits/byte supports structured,
uncompressed code/data, but does not classify every byte as executable.

Use the existing pypcode/Ghidra SLEIGH wrapper:

```powershell
python .agents/scripts/mcs96_disasm.py S760224.IMG --off 0x4800 --len 0x200 --base 0x2080
```

Older notes use the `.kiro/scripts/` mirror. Confirm instruction boundaries,
relative-target math, and callers before treating a raw opcode-pattern match as
code. Low register operands belong to `AS_DATA`; external buffers use
`AS_PROGRAM` in the emulator. This established emulator distinction does not
by itself prove the historical hypothesis about physical low-ROM fetch decoding.

## Hardware patch experiments worth retaining

| Experiment | Recorded result | What it establishes |
| --- | --- | --- |
| M1/M1b version-string edits | Modified disks booted; main display eventually showed `9.99` | Gotek round trip and these patches accepted; not a universal proof that no checksum exists anywhere |
| B0 reset-tail delay | Delay then normal hardware boot | Injected code executed and rejoined initialization |
| B1 repeated calls to `0x218E` | Delay then normal boot | Resident call/return from injected code worked |
| Save System output comparison | 344/360 4 KB blocks identical; 993 bytes differed | SaveSys includes live resident patches and some configuration differences |
| Four 8-byte sentinel markers | Survived SaveSys | Those markers/locations survived that experiment; not proof every larger write is safe |
| Low-memory copy probes | Some froze; later probes saved zero-filled captures | Data-copy approach did not recover firmware; physical code/data split remained an interpretation |

The reset-tail hook was runtime `0x218B` / file `0x490B`; original bytes
`E7 A3 06` jump to `0x2831`. Historical scratch entry `0x5DBE` / file `0x853E`
lies in an approximately 8 KB gap ending at runtime `0x7D00`. Later copy
destination `0x5E00` corresponds to file `0x8580`. These are experiment anchors,
not standing permission to overwrite them: current HLE uses other former gaps,
including the `0x9B42/51/71` delay entries.

Always patch a copy, retain exact size and sector alignment, check original hook
bytes, round-trip assembled code through the decoder, record the diff, and retain
a known-good hardware boot image. Keep this team's scratch in the author's work
folder. Never alter `S760224.IMG` in place.

## Resource catalogs and limits

`os-string-catalog.md` and `06-ui-string-map.txt` preserve exact strings and file
offsets. Useful anchors include Patch Common `0x09446A`, Partial TVF `0x09A1DC`,
TVA `0x09A872`, and LFO `0x09ACA0`. These locate labels/descriptors; they are not
automatically executable function entries or C++ structure offsets.

The short forensics deep dive also lists SCSI tape, foreign-format conversion,
and RC-100-related labels. Its raw `F0 41` byte matches include ASCII strings
such as `Auto Trun/Norm`; they do **not** establish SysEx messages or a complete
protocol. Use the MIDI implementation manual for protocol confirmation.

Manual sources are `ROLAND_S-760_SERVICE_NOTES.pdf` (24 scanned pages),
`S-760_OM.pdf`, and `S-760_MI.pdf` (14 pages). Service-note OCR is retained in
`service-notes-ocr.txt`; schematic wiring and noisy IC labels need visual
confirmation. Visually checked parts list p.5 establishes **IC15 = BOOT EPROM,
IC1 = CPU, IC20 = I/O gate array**; finding 22's CPU designation was incorrect.
Directory/catalog structure, allocation units, full record semantics, and checks
outside the tested boot patches remain open.


### Native HD0 writes (2026-10-14)

Original firmware quick initialization and performance Save now use bounded RAM78/waveA0 output DMA with native SPC counter completion. Writes modify the instance's controller image; source files remain unchanged. Python `NativeRuntime.export_scsi_hd0(new_path)` requests an idle HD0 snapshot through the native media port, validates its byte count and publishes a new output without replacing an existing destination. Busy/missing/read-only targets reject; export failures preserve controller data. The emulator must be running for the input callback. This export is a Python QA operation; the packaged GUI/VST export action has not been qualified for SCSI.

`verify_native_scsi_save.py` qualifies the private10 MiB HD00_512.img / HD0 /512-byte-sector profile: initialize, Save ROBOFULL performance, export and fresh firmware Load without a sample floppy. All13 sample allocations/119808 bytes are exact; playback level/spectrum and release survive. No low-level physical format/timing or arbitrary-media acceptance is claimed. [Validation](validation/milestone-5-scsi-save-2026-10-14.json).


### Supported disk/MIDI/voice contract (2026-10-14)

Owner's manual Advanced1-3 (S-760_OM.pdf page11) explicitly excludes sound output in Disk, Quick Load and Sampling displays and while commands such as Copy execute. Searching for a supported ongoing-voice disk operation was an incorrect roadmap requirement. This resolves the remaining Milestone5 gate through documented restriction/recovery, without claiming three-source arbitration.

Current native ROBOFULL Save clears four active notes, completes under240 incoming scheduled MIDI events (166 observed overlapping FDC writes), remains exactly silent over1543500 frames, and returns to Perform without stuck notes. Fresh Load preserves13 allocations/119808 bytes and matching recovered peak/release; original media/firmware hashes remain unchanged. The positive Save trace drops378 rows and cannot prove exhaustive handling or absence of every event. Three current Load-directory trials have complete traces and zero restricted completion overlap; their Perform control observes12 source2 requests. [Evidence and commands](validation/milestone-5-concurrent-recovery-2026-10-14.json).


### Disk Load versus full-session identity (BUG-006,2026-10-14)

The historical347-byte wave-RAM mismatch reproduces in the32MiB profile at high-memory metadata/name/ID/directory records, while13 sample allocations/119808 bytes remain exact through Save/export/fresh firmware Load. A separate cold checkpoint preserves all33554432 wave-RAM bytes exactly. Disk Load reconstructs records and must not be required to reproduce an entire session. BUG-006 is closed WONTFIX for its erroneous whole-session expectation; no guest metadata was patched. `verify_native_media.py --checkpoint --state-dir <fresh-private-directory>` now records every changed range and asserts full-wave identity specifically for checkpoint recall. [Evidence](validation/remaining-bug-investigation-2026-10-14.json).


### Explicit TVF envelope fields corrected (BUG-073,2026-10-14)

The original firmware TVF screen confirms partial+0x52..0x55 holds the four Level values and+0x56..0x59 the four Time values. The historical local builder labelled/wrote these in reverse for explicit specs. The canonical tracked scripts/build_sample_disk.py corrects explicit JSON levels/rates(time); the local .agents entry point delegates to it. Implicit legacy preset bytes remain unchanged. The controlled TVFSTEP capture disk is737280 bytes, loads64512 sample bytes exactly and produces the measured up/down steps and static endpoints through unmodified firmware. [Capture instructions](../hardware/captures/tvf-transition-capture.md), [native evidence](validation/tvf-transition-capture-2026-10-14.json). Generated images and their proprietary template stay outside source distributions.


### OS transfer supervisor (static, 2026-10-16)

OS 2.24 reserves sample space in units of 0x1200 before searching its 512 descriptor slots. Startup C869/C86D/C872 explicitly maps fetch page 0166 and calls 87B5; recursive analysis reaches higher-level rollback at 8B5F. That helper restores cursor 3616 from saved 1FA0 and refreshes page 0299 allocation mirrors. The supervisor's receive loop resets a 16-bit stall counter when the packet counter changes; cancellation or counter wrap takes an error path through rollback, while success takes a staged 0x30-byte copy path. External callee preservation, descriptor ownership and native cleanup acceptance remain open. These are static original-byte observations, not a measured timeout or physical transfer validation. [Lifecycle analysis](../firmware/os/os-transfer-lifecycle.md) and [byte evidence](validation/os-transfer-lifecycle-2026-10-16.json).


### Original OS startup device identification

[Static device-probe decoding](../firmware/os/os-device-probe-and-numeric-fields.md) followsstartup0129:8000 overeight targets0..7. Commandrecordsunder02CC:5F4E/5F55 are count6 plus03/12 commandbytes withrequested0A/23-byte responses. Counted comparisons identifyvendor/productprefixes,includingJVC/OMTI,CD-ROMfamilies,SonySMO-C,SyQuestandIomega. [Original-byte evidence](validation/os-device-probe-and-numeric-2026-10-16.json) preserves boundedresources;these firmwarebranchesdo notestablishnewphysicaldevicecompatibility.
