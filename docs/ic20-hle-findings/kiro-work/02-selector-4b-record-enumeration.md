# Finding 02 — IC20 Selector 0x4B is a Record-Enumeration/Lookup Service

**Author:** Kiro
**Status:** DRAFT (kiro-work). Move to shared when the HLE increment is verified.
**Date:** 2026-10-09

## Dispatcher resolution (important address note)
`LCALL` is 16-bit; the disassembler prints the *unwrapped* target. The caller
`B9AB: EF E6 70` computes next(0xB9AE)+0x70E6 = `0x12A94`, but the MCS-96 wraps to
**`0x2A94`** (= `0x12A94 & 0xFFFF`). So "lcall 2a94" in the trace is correct; the
real dispatcher is at runtime `0x2A94` (file `0x5214`):
```
2A94: ST   RW1C, 0x0104    ; selector -> slot 0x0104
2A99: LCALL 0x018D         ; IC20 service
2A9C: ...                  ; return; OS resumes
```

## Selector 0x4B call pattern (runtime 0xB99A..0xB9F9, file +0x2780)
The OS enumerates resource records by **type** (`R4A`) and **index** (`RW4C`),
always passing scratch pointer `RW1E = 0x6A26`, selector `RW1C = 0x4B`:

```
R4A=1, RW4C=0        single lookup;  stride +0x0D (hdr==0x7F) else +0x2B
R4A=2, RW4C=0..0x3F  64-entry loop;  stride +0x0D (hdr==0x7F) else +0x321
R4A=3, RW4C=0..0x7F  128-entry loop; stride +0x0D (hdr==0x7F) else +0x216
R4A=4, ...           (further types)
```
After each call the OS does:
```
LDB RDA, [RW4E]      ; read result byte via output pointer RW4E
CMPB RDA, #0x7F      ; 0x7F == valid record header marker
JNE ...              ; branch: present vs. absent -> advance dest ptr RW28
```

### Interpretation
- `R4A` = resource **type** (1..4 ≈ Performance / Patch / Partial / Sample — the
  S-760's four object classes; exact mapping TBD).
- `RW4C` = record **index** within the type (counts 0x40=64 or 0x80=128 — plausible
  per-type slot counts).
- `RW1E = 0x6A26` = a zeroed RAM **scratch/destination buffer** the service fills.
- **Output:** the service sets register **`RW4E`** to point at the located record
  and ensures `[RW4E]` is the header byte (`0x7F` for a valid/present record).
- The OS uses the `0x7F` test to size each record (stride `0x0D` present vs. a
  larger per-type stride absent) while building an in-RAM directory at `RW28`.
- `0x7F` is the known on-disk 256-byte record header marker
  (`docs/disk-image-format.md`: `7F 20 20 3A ...` at file ~0xC3000+).

### Required HLE contract for 0x4B
Given (`R4A`=type, `RW4C`=index, `RW1E`=dest buffer), the service must:
1. locate record (type,index) in the on-disk record table,
2. place it (or at least a valid header) where **`RW4E`** points, with the first
   byte = `0x7F` when the record is present,
3. return (flags/registers) so the OS's post-call `CMPB [RW4E],#0x7F` works.

A bare RET fails because `[RW4E]` stays 0 (never 0x7F) → OS treats every record as
absent and later init diverges / resets.

## HLE implementation plan (incremental, observable)
- **Increment A (minimal):** on the `0x018D` fetch, if selector(`0x0104`)==0x4B,
  set `RW4E` to the scratch buffer `RW1E` and write `0x7F` at `[RW4E]`. Observe
  how much further boot gets (expect: the enumeration loops complete; next stall
  reveals the following dependency). This proves the mechanism end-to-end.
- **Increment B:** actually map (type,index) -> on-disk record and copy real
  record bytes into the buffer, so downstream code that reads record *fields*
  (not just the header) works.
- Keep selector-dispatch generic so other selectors can be added as Gemini maps
  them.
