# IC20 HLE — Coordination & Work Split

**Purpose:** keep Kiro and Gemini from colliding (file locks) and from
duplicating analysis. Read this first.

## Directory rules (recap)
- Kiro edits only in `../kiro-work/`. Gemini edits only in `../gemini-work/`.
- Finished docs are **moved** into this `shared/` folder by their author.
- In `shared/`, prefer adding a NEW file over editing someone else's. If you must
  amend another author's shared doc, add a dated `> NOTE (author):` block at the
  end rather than rewriting their text.

## What is established (see `01-root-cause-and-ic20-abi.md`)
- Root cause: OS calls IC20 BOOT ROM service at `0x018D` (and via the
  `0x0100-0x011D` vector table); image has no IC20 code → derail → reset loop.
- IC20 service **selector `0x4B`** is a record/segment **loader** called in a
  128-entry loop; OS validates a returned header byte `[RW4E] == 0x7F`.
- A bare `RET` stub does NOT boot (OS checks the service's data side effects).
- Driver changes already landed & verified: OS region made writable RAM
  (`m_os_ram` + `install_ram`); IC20 logging scaffold + RET stub (in
  `machine_reset`).

## Proposed split (adjust as needed)
**Kiro (driver + HLE implementation):**
- Implement the C++ IC20 HLE handler in `s760.cpp` keyed on selector `0x0104`.
- Start with selector `0x4B` (record loader): figure out the source (on-disk
  256-byte record table at file `~0xC3000`, per `docs/disk-image-format.md`) and
  populate `[RW4E]`/dest so the `0x7F` header check passes; return expected flags.
- Rebuild + re-run `run_verification()` each increment.

**Gemini (static ABI mapping + banking):**
- Enumerate ALL IC20 entry points, including indirect vectors `0x0204 / 0x02FA /
  0x0299 / 0x0400 / 0x0C01 / 0xFC33` from the reset-initialised table at
  `0x0100-0x011D`; disassemble each caller to derive its contract.
- Scan banked (non-resident) segments for additional `<0x200` call targets.
- Investigate whether any IC20 service performs **bank/overlay selection** (the
  unresolved >64 KB payload mapping). This is the highest-value unknown.

## Shared conventions
- **Address math:** file offset = runtime addr + `0x2780`
  (because file `0x4800` == runtime `0x2080`). Double-check this every time — a
  `0x2000` slip produces garbage disassembly.
- Disassemble with `.agents/scripts/mcs96_disasm.py --off <file> --base <runtime>`.
- Scan for IC20 call sites with `.agents/scripts/scan_ic20_calls.py` (reusable).
- Never modify `S760224.IMG`. Driver source of truth:
  `mame-source/src/mame/roland/s760.cpp`.

## Verification signal (definition of done for "boots")
`tests/mame_harness.py: run_verification()` → `status:pass`, i.e. at least one of
`vdpVramActive`/`sedVramActive` true AND a CRT frame with
`nonBackgroundPixels > 0`. Milestone checkpoints along the way: reach `EI`
(`0x2185`) → `LJMP 0x2831` (main init) → first VDP write at `0xD000`.
