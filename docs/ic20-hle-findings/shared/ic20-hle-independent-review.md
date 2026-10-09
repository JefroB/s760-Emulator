# IC20 HLE Findings — Independent Technical Review

## Purpose

This review is intended as a handoff to the coding agent working on the Roland S-760 emulator. It focuses on the current IC20 HLE findings, the MCS-96 boot path, and the most likely next debugging steps toward getting the S-760 OS to boot reliably and eventually produce display output.

## Executive Summary

The IC20 HLE work appears to have crossed an important threshold: several previously blocking service-call and CPU-core problems have been identified well enough for execution to progress substantially farther into the resident OS. The next major risk is no longer simply “missing IC20 selectors.” The evidence points toward the **interrupt/vector path and CPU semantic fidelity** as the highest-value area to investigate next.

The strongest recommendation is to instrument the first interrupt accepted after `EI` and prove the exact vector-fetch mechanism before adding more behavioral guesses to the HLE. In parallel, the recently added `PUSHA`/`POPA` handling should be verified against the actual 80C196-family semantics rather than retained as a stack-neutral compatibility workaround without stronger evidence.

Several IC20 selector implementations are useful bootstrapping shims but should be explicitly classified as such. In particular, selector `0x4B` currently manufactures a successful record marker rather than implementing record enumeration, and selector `0x3B` contains a modulo-sector assumption that can silently turn an invalid CHS request into a different valid sector. These can move execution forward while simultaneously obscuring the real contract.

---

## 1. Highest-Priority Finding: Prove the Interrupt/Vector Path

The current machine implementation has a 60 Hz timer that calls `trigger_irq(IRQ_TIMER_60HZ)`. The machine IRQ mask begins with the timer source enabled, and `check_irq_state()` asserts the MCS-96 external interrupt line when a pending enabled source exists.

This creates a particularly important boot-time scenario:

1. The 60 Hz timer can become pending while CPU interrupts are still disabled.
2. The OS eventually executes `EI`.
3. A previously pending interrupt may then be accepted immediately.
4. If vector-table initialization, vector decoding, interrupt acknowledgement, or the emulated CPU's interrupt semantics are wrong, execution can derail immediately after otherwise-correct initialization.

The documentation already identifies `0x2185` (`EI`) and `0x2831` as useful boot milestones. The next trace milestone should therefore be **the first interrupt actually accepted after EI**, not merely another PC checkpoint.

### Recommended instrumentation

For every IRQ assertion and every CPU interrupt acceptance, log:

- emulated timestamp / cycle count;
- current PC;
- PSW;
- S-760 IRQ source;
- `m_irq_pending`;
- `m_irq_mask`;
- CPU interrupt-mask state;
- vector number/source selected by the MCS-96 core;
- exact address read for the vector;
- raw vector word/bytes;
- resulting destination PC;
- stack pointer before and after interrupt entry.

Do not assign meaning to a suspected ISR target until this trace proves how the core obtained it.

### Important distinction

The S-760 driver's `m_irq_mask` and the MCS-96 CPU's own interrupt mask/register state are different layers. Trace output showing something such as `INT_MASK = 0x24` should not be interpreted as the driver's `m_irq_mask`. Logging should name these separately to prevent false conclusions.

---

## 2. Vector RAM Needs a Contract, Not Just an Address Range

`machine_start()` installs `m_vec_ram` at `0x2000–0x207F` and initializes it from the loaded CPU image. The current findings indicate that the initial contents are effectively `0x0F` fill.

The important unanswered question is not simply whether this region exists, but **what the OS and CPU expect it to represent**.

The coding agent should establish:

- whether the 80C196 variant fetches interrupt vectors directly from this address range;
- whether the S-760 firmware copies or constructs vectors there during initialization;
- whether vectors are addresses, jump instructions, table indexes, or another format;
- whether byte ordering matches the current memory mapping;
- whether vector writes happen before or after the first enabled interrupt;
- whether any vector source remains uninitialized when the first interrupt fires.

A watchpoint on writes to `0x2000–0x207F`, combined with the interrupt-acceptance trace above, should answer this much faster than inferring vector destinations from later crashes.

---

## 3. The AS_DATA/Register-File Fix Looks Architecturally Sound

The MCS-96 core distinguishes program and data address spaces. Its low-address handling routes accesses below `0x100` to the internal register file rather than ordinary program memory. The documented fix that respects this distinction is consistent with the architecture of the existing MAME core.

This is an important result because earlier HLE behavior could appear correct at the call level while reading or writing the wrong backing storage for register-file operands.

### Recommendation

Keep a small regression test around this behavior. A selector test should intentionally read/write operands in the `< 0x100` range and prove that they affect the MCS-96 register file rather than the external/program memory image. This protects against future HLE refactors accidentally bypassing `any_r8`, `any_w8`, or equivalent register-aware paths.

---

## 4. `PUSHA` / `POPA`: Treat the Current Fix as Unverified

The current MCS-96 opcode table includes `PUSHA` (`0xF4`) and `POPA` (`0xF5`) along with other extended instructions. The implementation comments indicate that `PUSHA`/`POPA` were made stack-neutral because the observed routine near `0xB93A` appeared to execute `PUSHA` and later return without an obvious balancing `POPA`.

That is useful as a diagnostic experiment, but it is not yet a safe architectural conclusion.

A missing `POPA` in one apparent linear trace can have several explanations:

- the instruction's semantics differ from the assumed push-all-registers model;
- control flow was decoded incorrectly;
- the matching restore occurs on another path;
- the routine is entered at a different boundary than assumed;
- the CPU variant has behavior not represented by the current implementation;
- the disassembly is being affected by an earlier state error.

### Recommended action

Verify `PUSHA` and `POPA` against authoritative 80C196KB/compatible documentation and then create isolated CPU-core tests that assert:

- registers affected;
- push order;
- stack growth direction;
- resulting SP;
- flags/PSW effects;
- behavior of `PUSHA -> RET` versus `PUSHA -> POPA -> RET`.

If the no-op implementation remains necessary to boot, label it as a temporary compatibility shim and log every execution. A CPU semantic workaround should not silently become part of the emulator's permanent model.

---

## 5. Selector `0x4B` Is a Control-Flow Shim, Not Record Enumeration

The current selector `0x4B` behavior synthesizes a `0x7F` marker in the scratch/result buffer for record requests. This is valuable because it proves that the caller's control flow depends on seeing a successful/recognized record result.

However, it does **not** prove the actual selector contract.

Returning a success marker regardless of record type, index, or disk contents can cause later code to believe records exist that do not exist. That can corrupt downstream assumptions about:

- record counts;
- offsets;
- linked structures;
- device geometry;
- file/directory state;
- memory allocation or table population.

### Recommendation

Keep the synthetic implementation only as an explicitly named bootstrapping mode. Add trace fields for the requested record type/index and the synthetic result. Then implement real record extraction once the disk structures needed by the boot path are understood.

At minimum, selector tests should eventually cover:

- known valid record;
- missing record;
- end-of-enumeration;
- malformed record;
- multiple sequential records.

---

## 6. Selector `0x3B`: The Sector-20 Modulo Assumption Is Dangerous

The documented implementation computes an LBA similar to:

```text
LBA = ((cylinder * 2) + head) * 18 + ((sector - 1) % 18)
```

An observed caller value of `RF0 = 0x14` (20) motivated wrapping the sector number into the nominal 1–18 range.

This is not enough evidence to conclude that modulo wrapping is correct.

If the medium is being treated as a standard 1.44 MB floppy geometry, sector 20 is invalid. Silently mapping it to sector 2 can return plausible-looking but incorrect data and move execution deeper into a false state.

### Questions to resolve

Determine whether the field currently called `sector` is actually:

- a 1-based CHS sector;
- a 0-based sector index;
- a linear sector within a track pair;
- part of a device-specific logical address;
- a packed or transformed value.

Trace the values at the caller and compare the resulting requested bytes against known locations in the disk image. Until the semantics are proven, invalid CHS should preferably fail loudly rather than wrap.

---

## 7. Selector `0x1F`: Harden Address Arithmetic

The current selector `0x1F` combines `RW4A:RW48` into a 32-bit LBA, multiplies by 512, and copies `RW4C * 512` bytes.

The implementation should be hardened even if current boot inputs are small.

Potential failure cases include:

- `lba * 512` overflowing 32-bit arithmetic;
- `offset + length` overflowing;
- a transfer extending beyond the image;
- destination pointer plus length wrapping around 64 KiB;
- unexpectedly large sector counts.

### Recommendation

Use wider intermediate arithmetic and explicit bounds checks before any copy. Validate both source and destination ranges as complete ranges rather than validating individual wrapped addresses during the loop.

For example, conceptually validate:

```text
byte_offset = uint64(lba) * 512
byte_length = uint64(count) * 512
byte_offset + byte_length <= image_size
bufptr + byte_length <= addressable_destination_limit
```

Then perform the transfer only after all checks pass.

---

## 8. Broad RET Stubs Can Hide the Next Real Contract

`ic20_hle_install()` currently installs RET-style handlers for a collection of low-memory IC20 entry points, returning `0xF0F0` at the patched locations.

This is a useful discovery scaffold, but broad stubbing has two risks.

First, every stubbed entry point is implicitly being declared “safe to return immediately,” which may suppress initialization or state changes the OS expects.

Second, odd-address entry points deserve special scrutiny if a word-sized read handler is installed around them. Ensure that the handler's address granularity does not unintentionally alter the preceding byte or neighboring instruction/data behavior.

### Recommendation

Maintain an explicit table for each intercepted entry point containing:

- address;
- known callers;
- input registers/memory;
- observed outputs;
- side effects;
- current implementation status;
- confidence level;
- trace count during boot.

A useful status vocabulary would be:

- **Observed** — directly established by trace or image contents;
- **Derived** — follows strongly from observed behavior;
- **Hypothesis** — plausible but unverified interpretation;
- **Temporary shim** — deliberately fabricated behavior used to advance execution.

This prevents a successful boot experiment from being mistaken for a reverse-engineered specification.

---

## 9. Reconcile the IC20 Entry-Point Inventory

The findings appear to contain two different pictures of the low-memory call surface: one discussion describes a larger set of IC20 entry points discovered by scanning, while another emphasizes a very small number of direct low-address calls on the currently observed path.

These are not necessarily contradictory, but the scan methodology should be documented precisely.

Separate the inventory into categories such as:

- statically discovered direct `LCALL` targets;
- dispatch-table targets;
- indirect/vector calls;
- dynamically observed calls during boot;
- candidate addresses found only by byte-pattern scanning.

This matters because raw binary scanning can classify embedded data or alternate instruction alignments as calls. Dynamic execution evidence should carry more weight when prioritizing HLE implementation.

---

## 10. Define Display Milestones More Precisely

The current display path has more than one meaningful milestone. A generic statement such as “first VDP write” is too broad for determining how close the OS is to visible output.

Track these separately:

1. first VDP register access;
2. first VDP VRAM-data write;
3. first SED1335 command/register write;
4. first SED1335 display-memory write;
5. first frame whose pixels differ from the emulator's background/default state.

In the current driver, the VDP VRAM-active flag is tied specifically to the VRAM data-write path rather than every register write. Preserve that distinction in logs and documentation.

This makes it possible to tell whether the boot path has reached device initialization, actual framebuffer population, or genuine visible rendering.

---

## 11. Suggested Debugging Order

The following order minimizes the chance of adding more HLE guesses on top of a CPU/interrupt error:

1. **Instrument the first accepted interrupt after `EI`.** Capture source, PC, PSW, stack, mask state, vector address, vector contents, and target.
2. **Establish the vector-table contract.** Watch `0x2000–0x207F` writes and correlate them with the first interrupt.
3. **Verify MCS-96 `PUSHA`/`POPA` semantics.** Replace diagnostic behavior with architecture-correct behavior or explicitly document why a compatibility shim is still required.
4. **Re-run the boot trace through `0x2185`, `0x2831`, and the first interrupt.** Determine whether the post-`0x2831` derail is an interrupt problem or ordinary control flow.
5. **Harden selector `0x1F`.** Add checked wide arithmetic and source/destination range validation.
6. **Resolve selector `0x3B` addressing semantics.** Remove modulo wrapping unless evidence proves it.
7. **Keep `0x4B` synthetic behavior isolated and visible.** Replace it with actual record enumeration when enough disk-format evidence exists.
8. **Audit every IC20 RET stub.** Classify each as observed, derived, hypothesis, or temporary shim.
9. **Trace display milestones independently.** Distinguish device register initialization from actual VRAM/display-memory writes and rendered pixels.
10. **Run the existing verification suite after each semantic change.** CPU-core fixes and HLE changes should not be bundled into one untraceable experiment.

---

## 12. Proposed Trace Gates

A compact set of deterministic gates would make collaboration between agents much easier:

| Gate | Meaning |
|---|---|
| G1 | OS reaches `0x2185` and executes `EI` |
| G2 | OS reaches `0x2831` |
| G3 | First interrupt is accepted and its vector fetch is fully logged |
| G4 | Interrupt handler returns to a sane caller path |
| G5 | First VDP register write |
| G6 | First VDP VRAM-data write |
| G7 | First SED1335 command/data write |
| G8 | First non-background rendered frame |
| G9 | Existing automated verification passes |

Each experimental patch should report which gate changed. This is much more informative than “boots farther.”

---

## 13. Tests Worth Adding Now

A few focused tests would greatly reduce regression risk:

### CPU tests

- AS_DATA access below `0x100` hits register file.
- AS_PROGRAM fetch remains program-space behavior.
- `PUSHA` architectural state transition.
- `POPA` architectural state transition.
- interrupt entry stack/vector behavior.

### IC20 tests

- selector `0x1F`: valid one-sector read;
- selector `0x1F`: end-of-image boundary;
- selector `0x1F`: overflowing LBA/count;
- selector `0x1F`: destination wrap attempt;
- selector `0x3B`: first/last valid sector;
- selector `0x3B`: sector 0;
- selector `0x3B`: sector 19/20 without silent modulo remapping;
- selector `0x4B`: valid/missing/end record once the real contract is implemented.

### Boot-path regression

Record a short deterministic trace signature containing:

- PCs at G1/G2;
- first IRQ source;
- vector-fetch address;
- vector value;
- handler PC;
- return PC;
- first display-device write addresses.

This will immediately reveal whether a future change fixes one subsystem while breaking another.

---

## 14. Documentation Recommendation

The findings are useful, but some sections should avoid language such as “complete specification” while key behaviors are still inferred from boot-progress experiments.

For every reverse-engineered contract, explicitly separate:

```text
Observed:
Derived:
Hypothesis:
Temporary behavior:
Evidence needed to promote confidence:
```

This is especially important for IC20 HLE because a fabricated return value can be extremely effective at advancing execution while being completely wrong as a hardware model.

---

## Bottom Line

The current work has likely progressed far enough that **more selector guessing is no longer the best first move**. The next decisive experiment is to prove exactly what happens when the first pending interrupt is accepted after the OS enables interrupts.

If the vector fetch and interrupt entry are correct, attention can return to the next IC20/device contract with much higher confidence. If they are wrong, fixing that path may eliminate several downstream crashes that currently look like unrelated firmware or HLE problems.

The coding agent should therefore prioritize:

**interrupt/vector proof -> CPU opcode fidelity -> selector hardening -> faithful record enumeration -> display-path milestones.**
