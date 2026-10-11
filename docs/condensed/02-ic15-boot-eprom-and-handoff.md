# IC15 BOOT EPROM & Current HLE

## Current status — 2026-10-10 review

Original-ROM cold boot and sample loading are established in the tested native configuration. The older preloaded flat/HLE handoff is retained for comparison, not required evidence for the current boot milestone. See the native runbook for reproduction.

See the [completion roadmap](../COMPLETION_ROADMAP.md) and [native runbook](11-native-boot-and-audio-runbook.md).

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
panel and runs INTERACTIVE firmware menus — Command and Mode open and Exit
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
all size candidates75FC/75FE/7600 are zero — fixed by advancing the discarded-word
read address), and initializes the NEC FDC with the corrected port map
(E000=MSR/auxiliary, E002=FIFO — NOT the old generic765 at F040). Finding54's
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
Display remains disabled and queue words remain0102/EF1C. Initial21C8→BA40
enters an operand of the original flat slice, reinforcing the unresolved loaded
code/mapping contract. See52 for traces and limits; no behavioral fix is claimed.

**FDC SEEK interrupt chain that unblocks the boot (finding55).** Service Notes
p18 wires IC24(FDC) INT → IC4(CPU gate) INT0 (visually checked). The firmware's
FDC completion handler: disk55BB writes flag byte[1D0E]=1; its handler at CD5D
senses FDC status, issues SENSE INTERRUPT STATUS (0x08) at E002, drains results
to1B6C, sets the flag and returns via POPF/RET. The interrupt vector is NOT
injected — guest data203A (disk8783A) holds0120; fetch at0120 (bank000F, file
8520) is `PUSHF; LJMP CD5D`. Native mode resolves EXTINT1 (level13, vector203A)
from guest memory, saves/restores flags on the real guest stack, and routes FDC
pending through CPU-gate channel0 (firmware writes0115=11 around SEEK vs50 at
init). After SEEK servicing, real HSO/software-timer interrupts run via
200A→CAD1 and the main loop executes C807/C8A3 + banked UI routines with a
bounded stack. This REQUIRES real 196KB interrupt semantics; the old
stack-neutral PUSHF/PUSHA/POPA workarounds are confined to the flat baseline.

**Write-aware CPU-seam trace (findings 48/50, both reviewed).** Instrumentation
at the real MCS-96 seams — `read_pc`/`m_pr8` for fetches, `any_r8/r16` for
operand reads, `any_w8/w16` for writes — captured these results on a normal
stable boot (`vram_active=1 addr=074ba`), within a 4000-access cap per channel:

- The 0x8000–0xBFFF window is overwhelmingly CODE: **3907 instruction fetches
  vs 93 operand-byte reads** in the first 4000 window accesses. The sole in-window
  data read is the compare at PC≈2AAE of byte[8F98].
- Selector word **010C is written repeatedly and ALWAYS to 0x0299** (1996 writes,
  zero distinct values) — redundant RE-selection of the same value, exactly as
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
`#0166`. Finding 52's fetch history shows the 4B path does NOT execute 2A90 — it
enters the dispatcher at 2A94 **directly**, called from BA09 with RW1C already set
to 0x004B at BA01 (`B9FB LDB R4A,#3; BA01 LD RW1C,#004B; BA05 LD RW1E,#6A26;
BA09 LCALL 2A94`). So PC 2A94 storing 0x4B is intentional reuse of the dispatcher
entry below the default 0166 load — not changed/broken code. The 0166 immediate
belongs to a different entry (2A90) not taken on this path.

**The "permanent 4B enumeration stall" is DISPROVEN (finding 52).** A 30-second
run (same baseline, translation/queue-init OFF, exit 0) gives 4B calls = 132,413
— **identical to the 6-second total** — while 0166 keeps climbing (8,682). The OS
therefore gets PAST the expensive 4B burst rather than spinning on it forever;
instruction samples move on to DFxx/E09x relinking work. High 4B frequency was a
bounded burst, not a termination failure. Do NOT change the 7F record stub to
force a shorter enumeration — that is not an established repair.

Finding 46's whole-window substitution suppresses VRAM progress. Its first
logged replacement at B906 changes only the low byte F8→0B (mask00FF).
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
bits7:6=00→mode1/flag1, 01→mode2/flag1, 10 or 11→mode0/flag0.
For raw80, the complemented mask is 40h, not 00h. Controller-name mapping
and electrical wiring remain provisional. Shared review 41 also verifies
219A–21AC copying 47h bytes from logical 8312–8358 to 4C62–4CA8;
its backing-ROM mapping and purported boot-sector-table purpose need proof.

Kiro's later response 39 does not establish a paging refutation: its source
reads selector 010C from AS_DATA, which has only 8 address bits. The CPU routes
010C stores/reads through AS_PROGRAM. Shared review 40 requests a corrected
probe. Flat reads observed under an unchanged flat emulator also cannot prove
the physical hardware ignores selection. The ROM conversion evidence below
stands; actual fetch/data mapping and backing still require verification.

**Mapping correction (shared 38):** ROM 4F74–4FB0 explicitly converts a CPU
buffer address V using `S=word[0108+2*(V>>14)]`, then computes
`P=(S<<10)+(V&3FFFh)` and writes transfer address bytes at 011A/011C.
The four data quadrants select 0108/010A/010C/010E. These are mapping words,
not established routine pointers. Disk reset initializes them to
0204/02FA/0299/0400. Under that conversion, logical queue 21AC maps to
candidate backing 831AC; no disk-file offset equivalence is established.

Instruction quadrants selected by 0100/0102/0104/0106 are now a strong
hypothesis from call sequences and the 0106=0→LJMP C000 transition; exact
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
208E–2099 clears words through RW20 from 4000 to 7FFF. This loop does not
clear disk queue addresses. ROM 3C38–3C67 samples F00A bits5:3 and returns
28h→1, 10h→2, 00h→3, otherwise zero. 3C68–3C95 stores four complemented
F00A samples at 4D2B–4D2E. The D010/D012 stores at 3CA9/3CAE write zero.
These decoded blocks do not establish the complete physical mapping/handoff.

The new static write-map script does not resolve indirect destinations;
even the reset clear and sampled-byte stores above are omitted from its
address buckets. Its lack of 2000–2FFF targets cannot prove that IC15 never
writes that region. Shared review 34 qualifies finding 33's global negative
claim. Actual loader/service writes and real returned records remain the
next evidence needed; a particular HLE selector fix is not yet established.

Independent static analysis (shared 36) identifies paired ROM memory-access
loops at 022D–024F and 0274–0296: split a 32-bit address into offset `A&03FFh`
at window `8000h+offset`, write `(A>>10)&FFFFh` to 010C, then read/write
through the computed pointer. This supports a page/window protocol; physical
backing and full window extent remain unproved. Current driver has no handler
modeling that selection. Treating 010C solely as a callback pointer is unsupported.

Further static decode (shared 37) establishes a wider accessed range:
40A4–40BE selects 010C then fills 8000–BFFF with 8192 words; 40BF–40E8
verifies it, restoring the selector on both exits. The diagnostic caller
4043–4084 uses 5555h, AAAAh and page-value patterns over 63 chunks, advancing
selection by 10h per 4000h-byte chunk. Together these sequences support a
16 KB window selected in 1 KB address units; actual backing, masks and disk
mapping remain to be established. No driver paging change has been made here.

ROM 474F–4755 disables interrupts, stores zero to 0106, then jumps to C000.
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
has sectors 1–18; wrapping is not a proven hardware contract.

1F uses 32-bit `off=LBA*512`, `len=count*512`, tests `off+len<=0x168000`, and
copies to addresses narrowed to 16 bits. Both transfer paths clear carry even
if no copy occurred. Overflow-safe bounds and genuine failure semantics are
not implemented. Earlier summaries saying otherwise were wrong.

Fourteen targets have RET read handlers, returning F0F0 at the aligned word:
018D, 0296, 0442, 045D, 0491, 04AC, 0551, 05AA, 0B31, 0D5D, 0EC7, 0F15,
0F19, 1109. These survive RAM clearing; poked bytes did not. Stubbing is not a
verified implementation of these services. Real ROM mapping/ABI evidence is
requested in the shared findings folder.
