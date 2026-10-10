# IC15 BOOT EPROM & Current HLE

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
