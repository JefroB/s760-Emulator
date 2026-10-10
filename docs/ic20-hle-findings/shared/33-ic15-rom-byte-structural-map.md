# Finding 33 (Kiro) — IC15 BOOT/OS EPROM byte-by-byte structural map + the decisive negative result: IC15 NEVER initializes 0x2000-0x2FFF

**Author:** Kiro
**Status:** SHARED / FINAL
**Date:** 2026-10-09
**Artifact:** `roms/BOOT/Roland_S-760_v1.11.BIN` (32768 bytes, 27C256, v1.11).
**Tools (new, reusable):** `.agents/scripts/ic15_rommap.py` (segments / entropy /
entry-point hit counts / MMIO reference scan) and
`.agents/scripts/ic15_init_trace.py` (recursive-descent write-target map of the
reset/init path). File offset == runtime address for this ROM (reset at 0x2080).

## 1. Segment map (fill vs content)
```
00000-0011F  fill-FF   (288)      reset/service vectors live just below here
00120-00307  content   (488)   <- IC15 SERVICE routines (0x018D, 0x0204, 0x0299, 0x02FA)
00308-007FF  fill-FF
00800-018FC  content (sparse)    <- low service/LCD(SED1335) routines, 0x00-gapped
018FD-01C01  fill-00
01C02-01DFC  content   (507)
01FA0-01FEE  content   (79)
02000-02013 / 02030-0203F content  (small tables)
02080-03CB8  content  (7225)  <- RESET (0x2080) + MAIN INIT (0x4140 via LJMP) + board detect
03CB9-03FFF  fill-FF
04000-05D59  content  (7514)  <- main init body, display/LCD setup, disk path
05D5A-05FFF  fill-FF
06000-0730C  content (sparse,3.2KB) <- tables + more routines
0730D-07FFF  fill-FF   (3315)
```

## 2. Most-called routine entries (resolves the "mid-instruction" ambiguity)
Call-target hit counts (LCALL/LJMP/SCALL scan). These are REAL entries (a byte
reached by many calls is a genuine routine start — not a straight-sweep artifact):
```
2F66:21  48ED:19  2D64:18  02C4:10  23EA:10  5487:10  5475:9  2302:8
3C68:8 (F00A board-detect)  4906:8  243C:7  24AD:7  3088:7  2410:6 ...
018D service entry region (00120-00307) + 0218A delay stub (4 calls)
```

## 3. MMIO reference map (what hardware IC15 drives)
```
F00A: 4 refs   <- board/controller config read (the detect, see §4)
F000:47 F001:31 F002:23 F010:9 F017:11 F028:13  <- gate-array/SIMM/strobes
C000:25 C001:5 C071:13 D000:17 D071:26          <- gate array + VDP companion
D010: 1 ref  D012: 1 ref                        <- VDP display enable (ONE write)
E000:66 E002:19 (+ E0xx many)                   <- SED1335 LCD (dominant display path)
F020:9 F028:13 ... F048/F04C/F054/F058          <- SCSI + FDC (disk load)
```
Note: IC15's display path is overwhelmingly the **SED1335 LCD** (E000/E002, 85
refs). The VDP/CRT (D010) is written only ONCE in the whole ROM — IC15 does NOT
heavily drive the OP-760 CRT; that is the disk OS's job once it runs.

## 4. The F00A controller/board detect (the long-sought logic) lives at 0x3C38 / 0x3C68
All 4 F00A refs are in a ~0x80-byte block (file/runtime 0x3C3C/0x3C41/0x3C6E/0x3C76):
- **0x3C38**: `CLRB RDA; STB RDA,0xF00A; LDB RDA,0xF00A; ANDB RDA,#0x38; CMPB
  #0x28 -> ret 1; #0x10 -> ret 2; #0x00 -> ret 3; else 0`. => controller TYPE is
  **bits 5:3** of F00A (0x28/0x10/0x00 are the three valid straps).
- **0x3C68**: writes 0 to F00A then reads it **4 times**, NOT-ing each into
  0x4D2B..0x4D2E (IC15 RAM), which the main init at 0x4140 branches on to set the
  display-present flag 0x4D2F / mode 0x4D34. IC15 caches at **0x4D2B (its OWN
  RAM), NOT 0x2085** — consistent with finding 28 (the disk-OS 0x2085 cache path
  0x2496 is never even executed on our boot).

## 5. DECISIVE NEGATIVE RESULT — IC15 never writes the disk-OS work-RAM 0x2000-0x2FFF
Recursive write-target map of the IC15 reset/init (4669 instructions from 0x2080,
following all call/branch edges):
```
WRITE buckets: 0100,0110 (ptr table) | 4820,4C40-4E30,4D30 (IC15 OWN work RAM)
               C000,D010 | DC00,E000-E810 (LCD) | F000-F810 (gate array/SIMM)
NOTHING in 0x2000-0x2FFF.
```
IC15's reset clears only **0x4000-0x7FFF** (its own RAM, SP=0x4800) and writes the
pointer table at 0x0100-0x011F — it **never touches 0x2000-0x2FFF**. Combined with
the disk-OS reset clearing only **0x0120-0x111F**, this proves:

**NEITHER the BOOT ROM NOR the disk-OS reset zero-initializes the 0x2000-0x2FFF
work-RAM window.** So the earlier "the BOOT ROM leaves the queue zeroed" hypothesis
(my finding 29 / the fix in finding 31) is **DISPROVEN by the ROM itself.**

## 6. What this means (re-frames the whole display-enable question)
The queue pointers (0x21AC/0x21AE), the dispatch table (0x2184), and the display
shadows (0x2A8C/0x2A94) are all inside the loaded disk-OS image region (file
0x4800+) and start as disk-OS CODE/data bytes — on real hardware too. They are NOT
set to a clean state by any reset. Therefore the disk OS MUST initialize them
through its OWN normal execution — and the fact that our boot leaves them as raw
image bytes means **we are not completing the disk-OS initialization path that
builds them**, NOT that a BOOT-ROM precondition is missing.

Corollary: the real question moves from "what pre-zeroes the queue" to **"which
disk-OS init routine builds the 0x2184 dispatch table + zeroes the queue + sets up
the 0x2A8C display shadows, and why isn't our boot reaching it?"** That init is
almost certainly gated behind one of the IC20-service selectors our HLE answers
incompletely (0x4B/0x3B/0x1F resource enumeration, which populates these tables
from on-disk records). The HLE's selector 0x4B currently just writes a 0x7F
header stub (finding 03) rather than returning real records — so the OS's table-
build loop may complete with empty/garbage data and never populate 0x2184/0x21AC.

## 7. Recommended next step
Trace the disk-OS resource-enumeration loop (0xBA40/0xB9FB, selector 0x4B/0x3B)
that runs right after reset, and watch what it writes to 0x2180-0x21FF and
0x2A8C/0x2A94. If it depends on the HLE returning REAL on-disk records (not the
0x7F stub), then **completing the 0x4B/0x3B/0x1F HLE to return genuine records
from S760224.IMG is the faithful fix** — it lets the OS build its own tables/queue
exactly as it would with the real BOOT ROM + disk. This supersedes the queue-zero
diagnostic (finding 31) and matches ChatGPT's "find the real loader/service
contract" directive (shared/30, 32).

## Repro
```
python .agents/scripts/ic15_rommap.py   roms/BOOT/Roland_S-760_v1.11.BIN --section all
python .agents/scripts/ic15_init_trace.py roms/BOOT/Roland_S-760_v1.11.BIN --entry 0x2080 --max 40000
```
