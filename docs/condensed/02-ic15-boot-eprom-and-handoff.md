# IC15 BOOT EPROM & Current HLE

## Current status â€” 2026-10-10 review

Original-ROM cold boot and sample loading are established in the tested native configuration. The older preloaded flat/HLE handoff is retained for comparison, not required evidence for the current boot milestone. See the native runbook for reproduction.

See the [completion roadmap](../project/completion-roadmap.md) and [native runbook](11-native-boot-and-audio-runbook.md).

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

Historical finding56: the opt-in banked native handoff now scans the 13-switch front
panel and runs INTERACTIVE firmware menus â€” Command and Mode open and Exit
returns to Perform Play (host keys via the real scan port; see document 07 for
the SC/SP matrix). Finding55 before it: documented KB extended interrupts and
real flag-stack operations let firmware service the FDC SEEK and reach its main
loop, writing the Perform Play screen to guest VRAM (MAME renders it through a
diagnostic ASCII raster). This is the reconstructed disk handoff, not a full ROM
cold boot or complete CPU/peripheral/IC20 emulation. See
finding55
and finding56
for evidence and the complete-chip implementation gaps.

**Banked handoff map (findings53/54) supersedes the flat placement below.** ROM4FBF
loads disk cylinders1..56 (file4800..1007FF) to physical0..FBFFF;
ROM4750 clears0106 and4755 jumpsC000. Separate instruction/data selectors
resolve native EEPROM services and remove the former operand-entry conflict.
Opt-in banked execution skips HLE service stubs, passes a provisional sample
RAM test (producer6FE1 tests three F000 bank configs; fatal spin at003B:7193 if
all size candidates75FC/75FE/7600 are zero â€” fixed by advancing the discarded-word
read address), and initializes the NEC FDC with the corrected port map
(E000=MSR/auxiliary, E002=FIFO â€” NOT the old generic765 at F040). Finding54's
SEEK-completion stop at005A:5DEB (flag[1D0E]) is now superseded by finding55's
interrupt servicing. The N8097BH core lacked the196KB SFR12/13 interrupt
registers; native mode adds INT_MASK1/INT_PEND1. No completed/validated OS boot
is claimed. See
finding54.

Independent native trace52 resolves review51: BA01 loads004B and BA09 calls
2A94 directly, intentionally skipping the default0166 load at2A90. Live bytes
are unchanged. A30-second run has the same132413 calls to4B as finding50's
six-second run, while0166 increases to8682; enumeration is not a permanent
stall. Later execution samples are predominantly DFxx/E09x relinking work.
Display remains disabled and queue words remain0102/EF1C. Initial21C8â†’BA40
enters an operand of the original flat slice, reinforcing the unresolved loaded
code/mapping contract. See52 for traces and limits; no behavioral fix is claimed.

**FDC SEEK interrupt chain that unblocks the boot (finding55).** Service Notes
p18 wires IC24(FDC) INT â†’ IC4(CPU gate) INT0 (visually checked). The firmware's
FDC completion handler: disk55BB writes flag byte[1D0E]=1; its handler at CD5D
senses FDC status, issues SENSE INTERRUPT STATUS (0x08) at E002, drains results
to1B6C, sets the flag and returns via POPF/RET. The interrupt vector is NOT
injected â€” guest data203A (disk8783A) holds0120; fetch at0120 (bank000F, file
8520) is `PUSHF; LJMP CD5D`. Native mode resolves EXTINT1 (level13, vector203A)
from guest memory, saves/restores flags on the real guest stack, and routes FDC
pending through CPU-gate channel0 (firmware writes0115=11 around SEEK vs50 at
init). After SEEK servicing, real HSO/software-timer interrupts run via
200Aâ†’CAD1 and the main loop executes C807/C8A3 + banked UI routines with a
bounded stack. This REQUIRES real 196KB interrupt semantics; the old
stack-neutral PUSHF/PUSHA/POPA workarounds are confined to the flat baseline.

**Write-aware CPU-seam trace (findings 48/50, both reviewed).** Instrumentation
at the real MCS-96 seams â€” `read_pc`/`m_pr8` for fetches, `any_r8/r16` for
operand reads, `any_w8/w16` for writes â€” captured these results on a normal
stable boot (`vram_active=1 addr=074ba`), within a 4000-access cap per channel:

- The 0x8000â€“0xBFFF window is overwhelmingly CODE: **3907 instruction fetches
  vs 93 operand-byte reads** in the first 4000 window accesses. The sole in-window
  data read is the compare at PCâ‰ˆ2AAE of byte[8F98].
- Selector word **010C is written repeatedly and ALWAYS to 0x0299** (1996 writes,
  zero distinct values) â€” redundant RE-selection of the same value, exactly as
  review 49 predicted from the disk bytes `PUSH[010C]; LD RW1C,#0299; ST[010C]`.
  The other three data selectors 0108/010A/010E are written once at init only.
  This corrects finding 48's earlier "no runtime selector banking" wording: a
  constant re-selected value is compatible with a fixed-value bank; mapping stays
  open, but there IS active selection.
- The routine at ~2AAE is a **conditional one-shot edge-detector, not a wait
  loop**: byte[8F98] is written exactly once (first pass), after which
  byte[23A0]==byte[8F98] and the equal-branch is always taken.
- IC20 selector **00B1 dispatches once** in the run (right after that single
  8F98 write); the executive then spins almost entirely on selector **4B**
  (uncapped dispatch count 132,413 of 132,859).

Sampling qualification (reviews 49/51): "once" means once within the capped
trace / that bounded run, not provably once for all inputs or forever.

**Live-vs-image discrepancy RESOLVED (finding 52, native fetch trace).** Finding
50 attributed the 0104=4B store to PC 2A94, while the image slice there loads
`#0166`. Finding 52's fetch history shows the 4B path does NOT execute 2A90 â€” it
enters the dispatcher at 2A94 **directly**, called from BA09 with RW1C already set
to 0x004B at BA01 (`B9FB LDB R4A,#3; BA01 LD RW1C,#004B; BA05 LD RW1E,#6A26;
BA09 LCALL 2A94`). So PC 2A94 storing 0x4B is intentional reuse of the dispatcher
entry below the default 0166 load â€” not changed/broken code. The 0166 immediate
belongs to a different entry (2A90) not taken on this path.

**The "permanent 4B enumeration stall" is DISPROVEN (finding 52).** A 30-second
run (same baseline, translation/queue-init OFF, exit 0) gives 4B calls = 132,413
â€” **identical to the 6-second total** â€” while 0166 keeps climbing (8,682). The OS
therefore gets PAST the expensive 4B burst rather than spinning on it forever;
instruction samples move on to DFxx/E09x relinking work. High 4B frequency was a
bounded burst, not a termination failure. Do NOT change the 7F record stub to
force a shorter enumeration â€” that is not an established repair.

Finding 46's whole-window substitution suppresses VRAM progress. Its first
logged replacement at B906 changes only the low byte F8â†’0B (mask00FF).
This rejects the combined implementation: data selection applied to all reads
plus assumed physical-to-image backing. It does not disprove hardware paging.
Kiro's appended correction accepts review 47 and withdraws the PC-based access
classifier and earlier claims that queue/record hypotheses were ruled out.
Explicit CPU fetch/data tracing with substitution off is the next experiment;
fetch selection and physical backing remain open.

Kiro's corrected probe (42) reports steady 010C=0299, agreeing with reset
initialization; the wrong-space issue described below was fixed for that run.
Its flat-byte match percentages describe an unchanged flat emulator. They
cannot refute physical paging or prove raw IMG-offset placement. Shared
response 43 separates those hypotheses; hardware mapping remains open.

Gemini's ROM strap report (39) matches the numeric 4140 branches: raw F00A
bits7:6=00â†’mode1/flag1, 01â†’mode2/flag1, 10 or 11â†’mode0/flag0.
For raw80, the complemented mask is 40h, not 00h. Controller-name mapping
and electrical wiring remain provisional. Shared review 41 also verifies
219Aâ€“21AC copying 47h bytes from logical 8312â€“8358 to 4C62â€“4CA8;
its backing-ROM mapping and purported boot-sector-table purpose need proof.

Kiro's later response 39 does not establish a paging refutation: its source
reads selector 010C from AS_DATA, which has only 8 address bits. The CPU routes
010C stores/reads through AS_PROGRAM. Shared review 40 requests a corrected
probe. Flat reads observed under an unchanged flat emulator also cannot prove
the physical hardware ignores selection. The ROM conversion evidence below
stands; actual fetch/data mapping and backing still require verification.

**Mapping correction (shared 38):** ROM 4F74â€“4FB0 explicitly converts a CPU
buffer address V using `S=word[0108+2*(V>>14)]`, then computes
`P=(S<<10)+(V&3FFFh)` and writes transfer address bytes at 011A/011C.
The four data quadrants select 0108/010A/010C/010E. These are mapping words,
not established routine pointers. Disk reset initializes them to
0204/02FA/0299/0400. Under that conversion, logical queue 21AC maps to
candidate backing 831AC; no disk-file offset equivalence is established.

Instruction quadrants selected by 0100/0102/0104/0106 are now a strong
hypothesis from call sequences and the 0106=0â†’LJMP C000 transition; exact
fetch translation remains to be verified. The flat preload can conflate code
and data at the same logical address. Earlier claims that live queue/shadow
initialization necessarily overwrites physical startup code are withdrawn.
Likewise immediate HLE service dispatch on 0104 writes is current emulator
behavior, not a proven hardware service ABI. The constant file=runtime+2780
describes decoding the preloaded slice, not a universal bank mapping.

**IC15 = BOOT EPROM, IC1 = CPU, IC20 = I/O gate array** (service parts list p.5).
The HLE functions/directory retain the old IC20 name for continuity.

## ROM versus current boot path

Local `roms/BOOT/Roland_S-760_v1.11.BIN` is 32,768 bytes, with a HEX companion.
Finding 22 records coherent MCS-96 code, reset at 2080, and service code including
018D. It is v1.11; the disk is v2.24. Complete native mapping, loader handoff,
and ABI compatibility have not been established, so no native cold-boot sequence
is presented as fact here.

Finding 33's ROM reset block is byte-verified: 208A sets SP=4800;
208Eâ€“2099 clears words through RW20 from 4000 to 7FFF. This loop does not
clear disk queue addresses. ROM 3C38â€“3C67 samples F00A bits5:3 and returns
28hâ†’1, 10hâ†’2, 00hâ†’3, otherwise zero. 3C68â€“3C95 stores four complemented
F00A samples at 4D2Bâ€“4D2E. The D010/D012 stores at 3CA9/3CAE write zero.
These decoded blocks do not establish the complete physical mapping/handoff.

The new static write-map script does not resolve indirect destinations;
even the reset clear and sampled-byte stores above are omitted from its
address buckets. Its lack of 2000â€“2FFF targets cannot prove that IC15 never
writes that region. Shared review 34 qualifies finding 33's global negative
claim. Actual loader/service writes and real returned records remain the
next evidence needed; a particular HLE selector fix is not yet established.

Independent static analysis (shared 36) identifies paired ROM memory-access
loops at 022Dâ€“024F and 0274â€“0296: split a 32-bit address into offset `A&03FFh`
at window `8000h+offset`, write `(A>>10)&FFFFh` to 010C, then read/write
through the computed pointer. This supports a page/window protocol; physical
backing and full window extent remain unproved. Current driver has no handler
modeling that selection. Treating 010C solely as a callback pointer is unsupported.

Further static decode (shared 37) establishes a wider accessed range:
40A4â€“40BE selects 010C then fills 8000â€“BFFF with 8192 words; 40BFâ€“40E8
verifies it, restoring the selector on both exits. The diagnostic caller
4043â€“4084 uses 5555h, AAAAh and page-value patterns over 63 chunks, advancing
selection by 10h per 4000h-byte chunk. Together these sequences support a
16 KB window selected in 1 KB address units; actual backing, masks and disk
mapping remain to be established. No driver paging change has been made here.

ROM 474Fâ€“4755 disables interrupts, stores zero to 0106, then jumps to C000.
Several main-init paths target 474F. Actual execution, mapping after 0106,
and whether this is the successful disk handoff require a native trace; the
preload's C000 peripheral interpretation cannot establish the ROM contract.

Finding 35's sampled C7000+i*100h headers are independently verified: 128/128
are 7F. That supports matching first-byte branch decisions only if those records
are proved to map to the queried type/index. Full records differ, and multiple
resource types/counts are queried; complete 4B equivalence remains unproved.

Current MAME preloads the disk resident slice into RAM and executes disk reset
at 2080. It does not execute IC15 cold boot. The original image is preserved.

## Actual HLE implementation

`ic20_hle_install()` watches writes to selector word 0104 and performs side
effects immediately; installed RET read handlers let subsequent low calls return.
Other parameter/context slots include 0102, 010A, 010C; their writes alone do
not prove full service contracts.

| Selector | Inputs and current behavior | Classification |
| --- | --- | --- |
| 4B | R4A type, RW4C index, RW1E buffer; sets RW4E=buffer and writes 7F | Synthetic validity shim; no real enumeration |
| 3B | RF0 sector, RF1 cylinder, RF2 bit0 head, RW1E destination; copies 512 bytes | Approximate CHS read |
| 1F | RW4C count, RW48/RW4A LBA low/high, RW1E destination | Approximate bulk read |
| Others | Sets RW4E=buffer when nonzero | Side effects otherwise unmodeled |

Registers below 100 use **AS_DATA**; buffers/parameter slots use **AS_PROGRAM**.
That separation fixed the RW4E register-file bug.

Actual 3B formula: `(cyl*2+(head&1))*18 + (sec>0 ? (sec-1)%18 : 0)`.
It wraps invalid sectors and treats zero as the first sector. Standard geometry
has sectors 1â€“18; wrapping is not a proven hardware contract.

1F uses 32-bit `off=LBA*512`, `len=count*512`, tests `off+len<=0x168000`, and
copies to addresses narrowed to 16 bits. Both transfer paths clear carry even
if no copy occurred. Overflow-safe bounds and genuine failure semantics are
not implemented. Earlier summaries saying otherwise were wrong.

Fourteen targets have RET read handlers, returning F0F0 at the aligned word:
018D, 0296, 0442, 045D, 0491, 04AC, 0551, 05AA, 0B31, 0D5D, 0EC7, 0F15,
0F19, 1109. These survive RAM clearing; poked bytes did not. Stubbing is not a
verified implementation of these services. Real ROM mapping/ABI evidence is
requested in the shared findings folder.


## Static mirrored-ROM decoding (2026-10-16)

The versioned IC15 exploration now decodes4,720 instructions spanning13,870 unique bytes, with185 separately bounded data bytes. Reset establishes0790 for the4000 fetch window; the low window uses the native reset alias0780, whose physical power-on value remains unqualified. Firmware4F74 derives DMA physical addresses from the data selector and pointer offset. The loader's56 cylinders/two heads/2400-byte transfers match theFC000-byte OS payload. Initial vector words and a direct error-path branch expose the low serial monitor and FDC interrupt routine. The monitor was decoded but never executed by this work. [Detailed scope](../firmware/boot-rom/ic15-decoding-progress.md), [semantic evidence](validation/ic15-decoding-2026-10-16.json), and [separate ROM coverage](validation/ic15-exploration-coverage-2026-10-16.json). This does not complete decompilation, source rebuilding or physical validation.


### Static v1.11 resource and service qualification (2026-10-16)

The separate [boot-ROM decoding inventory](../firmware/boot-rom/ic15-decoding-progress.md) now classifies13,870 code bytes and10,951 referenced data bytes;7,947 bytes remain unclassified. These are static counts under the mirrored-ROM/native-reset mapping, not semantic-completion or physical-reset claims. Referenced resources include2,048 display row bytes,19 dual-display messages, bounded disk/configuration identities and2,404 audio table bytes. [Resource evidence](validation/ic15-display-resource-2026-10-16.json), [loader/recovery evidence](validation/ic15-loader-recovery-2026-10-16.json) and [EEPROM/audio evidence](validation/ic15-eeprom-audio-2026-10-16.json) preserve bytes and hashes.

The loader's recovery saves requested cylinder/head/sector, optionally seeks cylinder0A whenRCF bit4 is set, recalibrates with command07, then restores requested coordinates before retry. Destination cursor advances only after success. EEPROM532D/5350 use64-word read/write and reread verification over4CAA..4D29; failures retry without a local bound. Audio54E5/550E load400 command pairs and400 coefficients, with distinctDC06 index ranges0..018F and0200..038F. These contracts do not establish native error-path acceptance or physical timing.

Setup labels independently identify Self SCSI ID, Boot Drive, Controller and signed LCD Contrast(-50..50, IOS2=80hex+2*value modulo256). [Menu evidence](validation/ic15-setup-menu-2026-10-16.json) carries valid-state bounds. Four consumer-bounded bitmap resources add734 bytes; decoded pixels include Roland DIGITAL SAMPLER andS760 artwork. [Bitmap evidence](validation/ic15-boot-bitmaps-2026-10-16.json) does not claim physical display parity.

The [pixel/upload analysis](../firmware/boot-rom/ic15-decoding-progress.md) qualifies LCD pixel address32*y+x/6, bounds192x64, and high-six-bit masks. It conditionally classifies4,096 VDP upload bytes under the current native driver's word-counter contract; this is static model-qualified evidence, without a new execution trace or physical counter validation. [Evidence](validation/ic15-pixel-upload-contract-2026-10-16.json) records that source identity and retained mapping. The displayed byte coverage includes this conditional resource; semantic completion remains open.

The extendedsetup5941 branch adds a fifthTVSystemfield (4CB5),withNTSC/PALlabelsandvalid-state0..1 edits. [Static evidence](validation/ic15-tv-system-2026-10-16.json) distinguishes it fromthefour-fieldmenu. Thepreviouslyconditional4096-byteVDPuploadnowhas[ordinarynativeexecution evidence](validation/ic15-native-upload-2026-10-16.json):2048 destinationwords0000..07FFand4096 bytewritesexactlymatch originalROM1000..1FFF for thehash-identifiedexistingbinary. No firmware/gueststatepatcheswereused;physicalcounter/timingparity andfullOS-readyacceptance remainunqualified.


[Native panel-mode evidence](validation/ic15-native-panel-modes-2026-10-16.json) now confirms idle F00A inversion and display/setup selection for virtual high-bit configurations00/40/80/C0. The four cases match static ROM3C68/4140 behavior using passthrough observers and fresh private state. This adds runtime qualification, not ROM byte coverage or physical option-board acceptance.


Native loader handoff is now locally observed with an ordinary60-second boot: selector0106 write at postinstruction PC4755 precedes sustained OS execution. See [qualified trace](validation/ic15-native-handoff-2026-10-16.json). Extra interrupt stubs and two residual bypassed bodies are classified as static-only; invocation remains unresolved. The [remaining-range audit](validation/ic15-remaining-range-audit-2026-10-16.json) preserves uniform FF usage as unknown. Full ROM decoding remains incomplete.


### Residual-code and native initialization audit

The final declared ROM inventory contains15,060 code bytes and11,041 referenced data bytes (79.65% classified). Structural-only roots explain additional fill, storage, display, EEPROM and delay helpers; they do not prove invocation. See the [residual contract report](../firmware/boot-rom/ic15-residual-helpers.md).6,667 bytes remain unresolved:6,488 in uniformFF intervals plus179 other bytes, mostly unreferenced self-check text. A complete scan of decoded word-pointer candidates adds no active reference into these gaps;8359 is only an exclusive copy-end comparison. Numeric matches and FF appearance do not justify padding/resource claims.

The [native loader DMA trace](validation/ic15-native-loader-dma-2026-10-16.json) observes one512-byte header read and112 contiguous9216-byte payload reads from disk004800..1007FF intoRAM000000..0FBFFF before handoff. [Invalid-signature media](validation/ic15-native-invalid-media-2026-10-16.json) reaches statusesFF/FE and the error loop without handoff in30 emulated seconds. [Native audio initialization](validation/ic15-native-audio-init-2026-10-16.json) matches2,789 word writes, including128 cleared slots,400 command pairs,400 coefficients and two control words, to the original bytes and exact index ranges. These are ordinary read-only-observed execution claims, not physical parity. A deliberately short720KB system disk unexpectedly repeats handoff/reset (BUG-079); retry/recovery qualification stays open. Full ROM semantic completion and source/rebuild acceptance remain incomplete.

[Setup save/reboot](validation/ic15-native-setup-eeprom-2026-10-16.json) now matches all64 EEPROM words through read, save, verification, firmware restart and independent process reboot using only ordinary input fields and private NVRAM. The contrast byte changes0â†’FD(-3); the other63 words are identical. The menu initially selects contrast field3. [Extended TV setup](validation/ic15-native-tv-menu-2026-10-16.json) moves to field4, changes0â†’1, saves/verifies, then observes F002 changeDCâ†’FC (bit5), under existing virtual board straps40. Physical EEPROM and television timing remain unqualified.

The71-byte command template comprises nine length-prefixed CDB records, including the mutable ten-byte opcode28 record atRAM4C9E.26AE patches its32-bit block address and16-bit count most-significant byte first; SPC transfer count is24 bits, whereas IC4 receives only the low16-bit count. Loader2705 reads0400 blocks atLBA4 then03E0 at15AC intoRAM0/080000;273A reads07E0 blocks atLBA4 intoRAM0. Both totalFC000 bytes. [Static records and transfer evidence](validation/ic15-scsi-records-and-transfer-2026-10-16.json) preserves exact bytes and qualification. Native BootDrive2 selection reaches the six-byte command transfer but pollsSSTS81 where ROM25A3 requires high nibbleB0 (BUG-080); [ordinary input](validation/ic15-native-scsi-boot-2026-10-16.json) and [status polling](validation/ic15-native-scsi-poll-2026-10-16.json) identify the backend blocker without patching firmware or forcing status. Large zero-low-count IC4 transfers remain an additional unqualified dependency.


### Configuration and decoder cross-check, 2026-10-16

[Configuration/mapping audit](../firmware/boot-rom/ic15-configuration-and-mapping-audit.md) distinguishes valid-state menu bounds from EEPROM startup checks, accounts for14 direct selector operations and46 indirect memory stores, and qualifies both limits of all five setup fields through ordinary native input. The independent MAME decoder agrees on5,172 lengths/mnemonics and1,365 direct targets ([evidence](validation/ic15-independent-mame-decoder-2026-10-16.json)). Root-reached13,870 code bytes and structural-only1,190 bytes remain distinct. No new bytes are classified; ROM79.65%, OS6.07%, overall completion not yet quantifiable. BUG-081 qualifies earlier contrast-input attribution; the existing HD fixture requires a different boot header before eventual SCSI acceptance. Physical and transport gates remain open.


### SCSI command transport, 2026-10-16

BUG-080 is fixed: native command transfers now consume counts and report active/completion states, qualified by unchanged-ROM ordinary input. All452 tests and native runtime boot/playback/release pass. [Transport report](../firmware/boot-rom/ic15-scsi-boot-transport.md) and [validation](validation/ic15-scsi-transport-validation-2026-10-16.json). A private valid-header fixture exposes separate payload DMA BUG-082 (269D, IC4 count0000, SPC080000). Service Notes wiring confirms INT1 and DREQ/DACK0; internal IC4 vector/full-count semantics remain open. No full SCSI boot or physical parity is claimed. Classified-byte coverage remains ROM79.65%, OS6.07%; overall not yet quantifiable.


### Stack and monitor frame audit, 2026-10-16

[Stack/monitor report](../firmware/boot-rom/ic15-stack-and-monitor.md) reconciles171 actual FDC IRQ return-word writes, observed47D6 stack low and handoffSP47FE containing4338. The nonreturning loader leaves one caller word; monitorg/G consumes a manually built16-byte frame. CPU BUG-083 is fixed with an independently supportedWSR-low/mask-high frame and retainedWSR.457 full regressions, a new CPU pytest and native runtime pass. Installed SLEIGH semantic issue BUG-084 does not negate instruction decoding agreement. [Exact evidence](validation/ic15-stack-cpu-validation-2026-10-16.json). Classified bytes unchanged:ROM79.65%,OS6.08%; overall not yet quantifiable. Physical and native dormant-path gates remain open.


## User-directed unused-space assumption (2026-10-16)

For continued boot-ROM work, treat the 6,488 bytes in wholly FF unclassified intervals as **presumed unused space unless contrary evidence appears**, as explicitly directed by the user. This is an operational assumption, not a remaining prerequisite for boot-ROM decoding completion. The 179 other bytes remain unresolved. Reopen a presumed-unused interval if credible code/data references, copy or checksum requirements, or runtime evidence establish use. Preserve the original FF bytes in exports and rebuilds.

This accounts for **32,589/32,768 bytes (99.45%) including the assumption**; it does not measure semantic completion. Strict evidence-backed classified-byte coverage remains **26,101/32,768 (79.65%; +0.00 percentage points)**. OS classified coverage remains **62,736/1,032,192 (6.08%; +0.00 points)**. Overall decoding completion: not yet quantifiable; remaining behavioral questions include IC4 SCSI DMA/interrupt handling and dormant monitor invocation. [Assumption inventory](validation/ic15-presumed-unused-space-2026-10-16.json) records the hash-checked intervals and reopening rule.


## Residual text classification (2026-10-16)

Structural classification adds176 data bytes: four NUL-terminated self-check messages at file2918..29BB, nine-question-mark placeholder63CC..63D5, the -128 terminator6004 and leading Controller-label space6369. These are recognizable resource contents; no caller or diagnostic invocation is claimed. Regenerated analysis has zero decoder warnings.

Strict ROM classified-byte coverage is now **26,277/32,768 = 80.19% (+0.54 percentage points)**. Of the remaining6,491 bytes,6,490 are FF and presumed unused under the user's direction (including the newly separated2917/6005); the sole other byte is **file6903 = 08**, adjacent to the FDC SPECIFY template. Including presumed unused space accounts for **32,767/32,768 bytes = 99.997%**; rounded100.00% would conceal the remaining byte and is deliberately avoided. This is byte accounting, not behavioral completion. OS remains62,736/1,032,192 =6.08% (+0.00 points). Overall decoding completion: not yet quantifiable. [Exact inventory and qualifications](validation/ic15-residual-text-classification-2026-10-16.json).

Next operation: investigate file6903's possible template-prefix role without assigning meaning from adjacency alone, then qualify remaining diagnostic invocation and IC4 transport contracts. Original ROM remains unchanged.


[Boot-ROM completion rubric](../firmware/boot-rom/ic15-completion-matrix.md) now quantifies acceptance against15 named native-decoding paths and60 fixed binary gates. Initial46/60=76.67%; context11/15,layout15/15,behavior12/15,execution8/15. It is not effort remaining, physical parity or editable-toolchain acceptance. The user accepts6,490FF bytes as presumed unused;6903 remains provisional. Current strict classified bytesROM26,277/32,768=80.19%,OS77,680/1,032,192=7.53%; no byte growth in scoring. Combined OS-plus-ROM completion remains unquantifiable pending a comparable OS scope. [Criteria/evidence](validation/ic15-completion-scope-v1.json) and [generated score](validation/ic15-completion-score-v1-2026-10-16.json).


## IM1 repaired redraw and authored-image loading (2026-10-20)

Candidate5e5ec016... adds3 bytes to call the existing caller-qualified service between880 CRT character clears. Both actual simultaneous D7 stall/MIDI cases (byte1/3999) preserve775 reads,239616 stereo bytes and playback/release. Original dense D7, CRT/LCD cancellation/names, SDS and Remote Mode regressions pass:10 native cases/104 snapshots. BUG175 is fixed independently of BUG168, whose full service/deadline proof remains open. Allocation6583/8002 leaves1419 free; synchronous stack166 bytes unchanged, no total IRQ/ancestry proof. GB-6 v9/boot/SDS/Verify Medium/warnings retained. BUG174 fixes the minimal authored header and tests first real ROM handoff with112 tracks/all1032192 loaded bytes; no runnable-example-OS claim. Full suite1089 pass/3 skip, no failures. Physical qualification and upstream BlueSCSI defects remain separate. BUG140's abandoned descriptor experiment is WONTFIX, not repaired. [Evidence](validation/bluescsi-im1-bug-fixes-2026-10-20.json).
