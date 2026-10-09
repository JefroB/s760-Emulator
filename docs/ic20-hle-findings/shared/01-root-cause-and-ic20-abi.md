# Finding 01 — Root Cause of the MAME Boot Failure + IC20 ABI (initial)

**Author:** Kiro
**Status:** SHARED / FINAL (first pass). Evidence-backed; open questions in §4.
**Date:** 2026-10-09
**Driver:** `mame-source/src/mame/roland/s760.cpp`
**Image:** `S760224.IMG` (S-760 System Disk Ver. 2.24), resident segment file
`0x4800` == runtime `0x2080`.

---

## 1. Summary

The MAME `s760` driver does not boot the OS. Instruction-level tracing proves the
OS reaches its main init routine, calls a **Roland-proprietary IC20 BOOT ROM
service** at runtime address `0x018D`, and — because the disk image contains no
IC20 code — the call lands in zeroed RAM. The CPU derails and the OS resets in a
loop (observed ~170–243 reset passes in a few seconds; `EI` at `0x2185` is never
reached; the RFSC16A VDP at `0xD000` and Epson SED1335 LCD at `0xE000` are never
driven, so the CRT stays black).

**This IC20 ABI is the proprietary layer that cannot be dumped** (flat-pack IC,
no clean pull). The only viable path to boot is to **HLE the IC20 services** by
reconstructing their contract from how the OS calls them.

> The CRT "screens" documented previously in `docs/real-hardware-ui-analysis/`
> that were attributed to emulator output were in fact produced by the **removed
> mock C++ fallback renderer** (the invented `render_*_mode` chrome deleted in
> the `ui-consolidation` work), NOT by real OS execution. Getting past `0x018D`
> is the prerequisite for any genuine OS-driven display.

---

## 2. Evidence trail (how this was established)

All via the MAME debugger instruction trace (`-debug -debugscript`, `trace`
command) and the Lua/Python harness (`tests/mame_harness.py`).

1. **OS boot verification fails:** `run_verification()` → `status:fail`,
   `vdpVramActive:false`, `sedVramActive:false`, `nonBackgroundPixels:0`
   (black frame), gap finding "signals still false after duration".
2. **Reset completes, main init entered:** the reset routine runs cleanly
   `0x2080 → 0x2183` (RAM clear, SFR/interrupt init, full `0xF000` gate-array
   handshake with delay loops), then `SCALL 0x219e` into the init subroutine.
3. **The derail point:** inside init,
   ```
   21C8: lcall ba40        ; table-processing init
     ... BA09: lcall 2a94  ; dispatcher
   2A94: st  RW1C, 0x0104  ; stash selector/arg in RAM slot 0x0104
   2A99: lcall 018d        ; <-- CALL INTO IC20 BOOT ROM
   018D: skip #00          ; executing ZEROS (blank RAM) — derail
   018F: skip #00
   ...                     ; runs off into zeroed low RAM, eventually resets
   ```
4. **Reset loop confirmed:** in one bounded run, `scall 219e` executed **243**
   times and `lcall 018d` **170** times; the return address `0x2A9C` was reached
   **0** times (the IC20 call never returns on real-code-less RAM).
5. **The image has no IC20 code at `0x018D`:** file byte at the mapped location
   is `0x00`/`0xFF` fill (floppy boot-sector banner region), not CPU code.

---

## 3. The IC20 service ABI (reconstructed so far)

### 3a. The direct dispatcher at `0x2A94`
```
2A94: ST   RW1C, 0x0104     ; selector word -> RAM slot 0x0104
2A99: LCALL 0x018D          ; invoke IC20 service entry
2A9C: ...                   ; return point (OS inspects results here)
```

### 3a-bis. The authoritative caller + return contract (`0xB9FB` loop)
Disassembled at the correct offset (file = runtime + 0x2780; runtime `0xB9FB` =
file `0xE17B`):
```
B9FB: LDB R4A, #0x03         ; R4A = 3        (service "type"/mode input)
B9FE: LD  RW4C, RW2C         ; RW4C = index   (loop counter 0..0x7F)
BA01: LD  RW1C, #0x4B        ; RW1C = 0x4B    (SELECTOR -> stored at 0x0104)
BA05: LD  RW1E, #0x6A26      ; RW1E = 0x6A26  (POINTER arg)
BA09: LCALL 0x12A94          ; dispatcher -> 0x2A94 -> LCALL 0x018D (IC20)
---- after return ----
BA0C: LDB RDA, [RW4E]        ; read a RESULT byte via pointer RW4E
BA0F: CMPB RDA, #0x7F        ; compare result byte to 0x7F
BA12: JNE 0xBA1D             ; branch on the comparison
BA14/BA1D: ADD RW28, #0x0D / #0x216 ; advance a dest pointer by record stride
BA24: INC RW2C               ; next index
BA26: CMP RW2C, #0x80        ; loop over 128 (0x80) entries
BA2A: JNE 0xB9FB
```

**Interpretation (high confidence):** selector **`0x4B`** is an IC20 service the
OS calls in a **128-iteration loop** (`index 0..0x7F`), passing:
- `R4A = 3` (type/mode),
- `RW4C = index`,
- `RW1C = 0x4B` (selector, stored at `0x0104`),
- `RW1E = 0x6A26` (pointer argument).

On return the OS reads a **result byte via `[RW4E]`** and compares it to `0x7F`.
`0x7F` is the known **record-header byte** of the on-disk 256-byte record table
(see `docs/disk-image-format.md`: record header `7F 20 20 3A ...`). So selector
`0x4B` is almost certainly a **preset/parameter record load-or-locate service**:
it brings a record (or its header) into memory where the OS then validates the
`0x7F` header and advances its destination pointer by a per-record stride
(`0x0D` or `0x216`). This is a **data-loading responsibility of IC20**, not a
trivial helper — which is exactly why a bare `RET` cannot satisfy it (the OS
reads `[RW4E]` and would see stale/zero data, failing the `0x7F` check and
stalling/looping).

A second, adjacent call uses `R4A = 4` / selector `0x4B` (at `0xBA2E`), i.e. the
same service invoked with a different "type" — more evidence `0x4B` is a general
record/segment loader parameterised by `R4A`.

### 3b. The IC20 vector table at `0x0100-0x011D` (set up by reset)
The reset routine (`0x2080`) initializes a pointer/parameter table in low RAM.
These are IC20 service vectors / parameters the OS calls indirectly:

| RAM addr | Value set at reset | Note |
| :-- | :-- | :-- |
| `0x0100` | `0x000F` | param/flags |
| `0x0104` | (set per-call) | **service selector / arg** (written by `0x2A94`) |
| `0x0108` | `0x0204` | IC20 routine pointer (low addr) |
| `0x010A` | `0x02FA` | IC20 routine pointer (low addr) |
| `0x010C` | `0x0299` | IC20 routine pointer (low addr) |
| `0x010E` | `0x0400` | pointer |
| `0x0110` | `0x0C01` | pointer |
| `0x0112` | `0xFC33` | pointer |

Targets `0x0204`, `0x02FA`, `0x0299` are all `< 0x2080` (i.e. in the IC20 ROM
address window), consistent with them being additional IC20 entry points reached
indirectly through this table.

### 3c. Direct IC20 call sites in the resident 64KB segment
A static scan (`temp/scan_ic20.py`) of the resident segment (file `0x4800..`,
runtime `0x2080..0xDFFF`) for `LCALL` (opcode `0xEF`, rel16) with target `<0x200`
found exactly **one** direct entry point:

| IC20 entry | Call sites |
| :-- | :-- |
| `0x018D` | `0x2A99` (1 site) |

NOTE: the full OS payload is ~520 KB and banked; additional IC20 entry points may
exist in non-resident (banked) segments and are not yet scanned. The indirect
vectors in §3b (`0x0204/0x02FA/0x0299/...`) are the next ones to characterise.

---

## 4. What a fix must do (and what does NOT work)

- **A bare `RET` (0xF0) stub at `0x018D` is NOT sufficient.** The OS inspects the
  result of the IC20 service after return; a no-op return does not satisfy it and
  boot still stalls (verified: `pc_max` stays `0x21AF`, `EI` never reached).
- The real HLE must **perform the service's effect** (the first call, selector
  `0x004B` with pointer `0x6A26`, happens during OS segment/overlay init — likely
  a copy/load or a table lookup the OS depends on) and return the expected status
  (carry flag / register / memory side effect) that the OS validates at `0x2A9C`.

### Open ABI questions (to be answered by further tracing)
1. Full semantics of selector `0x004B` — what does the service compute/move, and
   what does the caller at `0x2A9C`/`0xBA06` check on return?
   (Trace shows `BA06: CMP ... 0x2A[RW4E]` and branches — the return contract is
   a value the OS compares; capture it.)
2. The indirect vectors `0x0204 / 0x02FA / 0x0299` — their individual contracts.
3. Whether any IC20 service performs **bank/overlay selection** (the unresolved
   >64 KB banking mechanism) — this is the most likely "big" IC20 responsibility.
4. Interrupt vectors `0x2000-0x201F` are empty/unmapped (reads `0x00`); once the
   OS enables interrupts in main init they will mis-vector. This is a *separate*
   latent bug behind the IC20 one; record it so it is not forgotten.

---

## 5. Changes already made to the driver (verified, keep)

These are correct, independently-verified fixes that unblock earlier stalls and
are prerequisites for the IC20 work:

1. **OS region made writable RAM.** `0x2080-0xCFFF` was mapped read-only `.rom()`
   but the OS executes-from and writes-to that window (docs model: "loaded into
   RAM and executed"). Now a RAM shadow pre-loaded from the image
   (`install_ram` + `m_os_ram` in `machine_start`); `0xD100-0xDFFF` stays ROM;
   `0xD000-0xD0FF` remains the VDP. Verified writable at runtime.
2. **IC20 HLE scaffolding added** (`ic20_hle_install()`): a `logerror` write-tap
   on selector slot `0x0104`, and a RET stub poke at `0x018D` placed in
   `machine_reset()` (NOT `machine_start()`, because the generic `0x0000-0x1FFF`
   `.ram()` backing is cleared by the core after `machine_start`, which wiped an
   earlier poke — verified `mem[0x018D]` read back `0x00`).
   NOTE: even with the stub reliably in place, a bare RET does not boot (see §4);
   the stub is a logging/observation scaffold, not the fix.

---

## 6. Next actions (proposed)
1. Capture the live return-contract at `0x2A9C`/`0xBA06`: what register/flag/mem
   the OS compares after the IC20 call (debugger register dump at the call).
2. Characterise selector `0x004B` behaviour on real hardware behaviour-by-inference
   (what the OS *expects* to have happened), then implement it in a C++ HLE
   handler keyed on the `0x0104` selector.
3. Enumerate indirect IC20 vectors (`0x0204/0x02FA/0x0299`) and banked-segment
   call sites.
4. Re-run `run_verification()` after each increment; success = `EI` reached →
   `0x2831` main init → genuine VDP/SED writes → non-black CRT frame.
