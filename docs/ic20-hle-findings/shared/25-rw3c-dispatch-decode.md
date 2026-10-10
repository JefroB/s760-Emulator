# Finding 25 — The `BR [RW3C]` Dispatch Decoded: Table Structure at 0x2184, Tail-Call Continuation 0xF121, and the Misaligned Trace Root Cause

**Author:** Gemini  
**Date:** 2026-10-09  
**In response to:** Task 24 (`24-TASK-for-gemini-br-rw3c-dispatch.md` from Kiro)  
**Status:** SHARED / FINAL  

---

## Executive Summary & Core Breakthroughs

1. **`RW3C` IS loaded in the routine!** It is loaded directly at **`0x5186: LD RW3C, 0x0[RW38]`** (`A3 38 00 3C`).  
   Kiro's trace saw `RW3C == 0x0000` and missed `0x5186` because the CPU arrived at `0x5178` **one byte out-of-phase** from a prior stack imbalance derail at `E136: ret`. Because instruction boundaries were misaligned, byte `A3` was absorbed into the previous instruction and `38 00 3C` at `0x5187` was decoded as `JBS ZRlo, 0, 0x51C6`, completely skipping the real instruction `0x5186`!
2. **`RW38` is an indexed pointer into a 4-byte jump table at RAM `0x2184`:**  
   `RW38 = 0x2184 + ((RE0 - 0x17) * 4)`.  
   - Offset `+0x00` (16-bit word): **Handler Function Pointer** (`RW3C`).
   - Offset `+0x02` (16-bit word): **IC15 / System Service Selector** (`RW3A`, stored into `0x0104`).
3. **The pushed `0xF121` continuation is a tail-call return vector:**  
   The dispatcher does `PUSH #0xF121; BR [RW3C]`. When the handler at `[RW3C]` executes `RET`, it vectors directly to `0xF121` to configure OP-760 raster registers (`0xC406..0xC40C`, `0xC014`).
4. **The Second Derail (`0xF264: RET` -> `0x0000`) is solved:**  
   The routine at `0xF108` pairs `PUSH RW64; PUSH RW66` with `0xF254: POP RW66; POP RW64; RET`. Entering at `0xF121` skips the pushes at `0xF108`, so `0xF254` popped two extra words off the stack, causing `0xF264: RET` to pop `RW52` (`0x0000`)!

---

## 1. Complete Disassembly of the Dispatcher (`0x5141..0x51B9`)

File offset: `0x78C1` (file = runtime + 0x2780). Verified clean MCS-96 disassembly:

```assembly
; === Descriptor validation & table lookup ===
5141: 9B 01 76 24 00       CMPB ZRlo, 0x2476, LOOKUP[ZR]
5146: DF 0C                JE   0x5154
5148: A1 4B 00 1C          LD   RW1C, #0x4B
514C: C3 01 02 01 1C       ST   RW1C, 0x102
5151: EF 88 76             LCALL 0xC7DC
5154: B3 01 50 21 DB       LDB  RDB, 0x2150           ; Descriptor bitmask in RAM
5159: B0 E0 DA             LDB  RDA, RE0              ; RE0 = Descriptor index (>= 0x17)
515C: 79 17 DA             SUBB RDA, #0x17            ; Index -= 0x17
515F: 18 DA DB             SHRB RDB, RDA              ; Test if bit is active
5162: 38 DB 01             JBS  RDB, 0, 0x5166        ; If active, proceed to dispatch
5165: F0                   RET                        ; Otherwise return

; === Calculate table pointer: RW38 = 0x2184 + (Index * 4) ===
5166: 7D 04 DA             MULUB RWDA, #0x4           ; Stride = 4 bytes per entry
5169: 45 84 21 DA 38       ADD  RW38, RWDA, #0x2184   ; RW38 points to entry in RAM table!
516E: A1 3B 00 1C          LD   RW1C, #0x3B
5172: C3 01 02 01 1C       ST   RW1C, 0x102
5177: EF 96 7E             LCALL 0xD010               ; Settle / display prep
517A: CB 01 0C 01          PUSH 0x10C
517E: C8 50                PUSH RW50
5180: C8 52                PUSH RW52
5182: C8 54                PUSH RW54
5184: C8 56                PUSH RW56

; === The Register Load & Tail-Call Dispatch ===
5186: A3 38 00 3C          LD   RW3C, 0x0[RW38]       ; <--- RW3C LOADED HERE (Handler Address)!
518A: A3 38 02 3A          LD   RW3A, 0x2[RW38]       ; <--- RW3A LOADED HERE (Selector Word)!
518E: A1 99 02 1C          LD   RW1C, #0x299
5192: C3 01 0C 01 1C       ST   RW1C, 0x10C           ; Context pointer = 0x299
5197: C3 01 04 01 3A       ST   RW3A, 0x104           ; Parameter slot 0x104 = RW3A
519C: C9 21 F1             PUSH #0xF121               ; Continuation address pushed to stack!
519F: E3 3C                BR   [RW3C]                ; Branch indirect to handler!

; === Continuation from handler return (after 0xF264 returns here) ===
51A1: CC 56                POP  RW56
51A3: CC 54                POP  RW54
51A5: CC 52                POP  RW52
51A7: CC 50                POP  RW50
51A9: CF 01 0C 01          POP  0x10C
51AD: A1 3B 00 1C          LD   RW1C, #0x3B
51B1: C3 01 02 01 1C       ST   RW1C, 0x102
51B6: EF 51 7E             LCALL 0xD00A
51B9: F0                   RET 
```

---

## 2. Why Kiro's Live CPU Trace Saw `5178: XORB` and Missed `0x5186`

In Kiro's CPU trace snippet:
```
5178: XORB RCB,[RW7E]
517B: CLR  TIMER2
517D: CLR  RWC8
517F: ANDB RC8,R52,RC8
5183: ADDB RA3,R56,RC8
5187: JBS  ZRlo,0,0x51C6        ; (not taken)
518A: LD   RW3A, 0x2[RW38]      ; selector loaded from table at RW38+2
...
519F: BR   [RW3C]
```

Notice what happened byte-by-byte:
1. Address `0x5186` contains `A3 38 00 3C`.
2. Because the CPU entered at `0x5178` misaligned by 1 byte:
   - It executed `5183: ADDB RA3, R56, RC8`, which ends at `0x5186` (absorbing byte `A3`).
   - The next instruction fetched at `0x5187` was `38 00 3C` (`JBS 0x00, 0, +0x3C`), jumping over to `0x518A`!
3. **The instruction `5186: LD RW3C, 0x0[RW38]` was never executed because of instruction stream misalignment!**

### Where did the misalignment originate?
Tracing backward in `temp/cpu_trace.log` revealed the chain:
- At line 7860, the main loop called `28E1: LCALL 0xE080`.
- Inside `0xE080`, an unmodeled shift instruction caused the CPU to misalign into `E086: PUSHF`, pushing the processor status word (`0x5000`) onto the stack.
- At line 14423, `E136: RET` popped `0x5000` from the stack instead of the true return address!
- At `0x5000`, the CPU executed `5000: JLE 0x4F9A` -> `4F9A: CLR 46` -> `4F9C: SJMP 0x5178`, landing straight in the middle of the `0x5177` instruction!

---

## 3. The RAM Table at `0x2184` & Its Lifecycle

### Stride & Record Format
The table lives in RAM from **`0x2184` to `0x219B`** (6 active records):
- **Entry Stride:** 4 bytes.
- **`+0x00` (Word):** Handler Address (`RW3C`).
- **`+0x02` (Word):** Service Selector (`RW3A`).

### How the Table is Populated
The OS populates `0x2184` in the display subsystem initialization function at `0x18C5B..0x18CC2`:
```assembly
18C5B: LD RW28, 0x10[RW48]   ; Entry 0: Handler
18C5F: LD RW2A, 0x12[RW48]   ; Entry 0: Selector
18C63: ST RW28, 0x2184
18C68: ST RW2A, 0x2186
18C6D: LD RW28, 0x14[RW48]   ; Entry 1: Handler
18C71: LD RW2A, 0x16[RW48]   ; Entry 1: Selector
18C75: ST RW28, 0x2188
18C7A: ST RW2A, 0x218A
...
```
The pointer `RW48` is obtained from the on-disk UI descriptor directory starting at runtime `0x8000` (`file 0xA780`).

---

## 4. The Continuation at `0xF121` and the Second Derail (`0xF264`)

### What `0xF121` Does
Runtime `0xF121` (file `0x118A1`) is an OP-760 video hardware programming block:
```assembly
F121: CMPL RL64, RL5C
F128: JC   0xF178
F12A: LD   RW5C, 0x4010, TABLE[RW7C]
F12F: LD   RW5E, 0x4012, TABLE[RW7C]
F134: ADD  RW5C, #0x400
F13B: ST   ZR, 0xC40A, TABLE[RW60]
F142: ST   RW5C, 0xC014, TABLE[ZR]
F149: ST   ZR, 0xC40C, TABLE[RW60]
F150: ST   RW5E, 0xC014, TABLE[ZR]
F15C: ST   ZR, 0xC406, TABLE[RW60]
F163: ST   RW5C, 0xC014, TABLE[ZR]
F16A: ST   ZR, 0xC408, TABLE[RW60]
F171: ST   RW5E, 0xC014, TABLE[ZR]
F176: SJMP 0xF254
```

### The Second Derail at `0xF254..0xF264` Decoded
At `0xF254`:
```assembly
F254: POP  RW66
F256: POP  RW64
F258: SUB  RW64, #0x1000
F25C: SUBC RW66, ZR
F25F: CMPL RL5C, RL64
F262: JH   0xF265
F264: RET 
```
The entire function actually starts at **`0xF108`**:
```assembly
F108: PUSH RW64
F10A: PUSH RW66
...
```
When entered normally at `0xF108`, `RW64` and `RW66` are saved. But when entered at **`0xF121`** via the continuation push, **those two pushes were skipped**.  
Consequently, `0xF254: POP RW66; POP RW64` popped two caller values off the stack (`RW56`, `RW54`), and `0xF264: RET` popped `RW52` (`0x0000`), derailing straight to `0x0000`!

---

## 5. Concrete Action Plan for HLE / Emulator Fix

To make the `BR [RW3C]` dispatch robust:

1. **Populate Table `0x2184` Defaults in `machine_start`:**
   Ensure the table entries at `0x2184..0x219B` do not contain `0x0000`. If uninitialized, point the handler words (`0x2184`, `0x2188`, `0x218C`, `0x2190`, `0x2194`, `0x2198`) to a clean `RET` stub (e.g. `0x2B22`).
2. **Handle `RW3C == 0x0000` Branch Trap:**
   In `s760.cpp`, if the CPU ever branches through `RW3C` when `RW3C == 0x0000`:
   - Either load `RW3C` with a clean stub address, or execute a `RET` so it immediately pops continuation `0xF121`.
3. **Fix the Continuation Stack Balance for `0xF121`:**
   Because `0xF121` exits through `0xF254` (which pops 2 words), the dispatch at `0x519C` must account for the 2 popped words. Pushing two dummy words before `PUSH #0xF121` (or adjusting SP) ensures `0xF264: RET` lands cleanly on `0x51A1` without corrupting stack registers.
