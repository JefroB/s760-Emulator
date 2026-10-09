# IC20 BOOT ROM HLE — Findings Area

This folder holds the collaborative reverse-engineering effort to high-level
emulate (HLE) the Roland S-760's **IC20 BOOT ROM** so the MAME `s760` driver can
actually boot the OS. The IC20 is a flat-pack part that **cannot be cleanly
dumped**, so the only path to booting is to reconstruct its service ABI from how
the OS calls into it, and reimplement those services in the driver.

## Why this exists (root cause, confirmed)
The OS (loaded from `S760224.IMG`) makes hardcoded calls into low memory
(`0x0000-0x01FF`) expecting Roland-proprietary IC20 ROM service routines there.
The disk image contains **no** IC20 code, so those calls land in zeroed RAM, the
CPU derails, and the OS resets forever (observed: ~170-243 reset passes, `EI`
never reached, VDP/SED never driven → black CRT). This IC20 ABI is precisely the
proprietary layer that differentiates the real hardware.

## Directory layout (collision-free collaboration)

| Directory | Owner | Purpose | Who writes | Who reads |
| :-- | :-- | :-- | :-- | :-- |
| `docs/ic20-hle-findings/kiro-work/`   | **Kiro** | Kiro's private drafts & scratch | Kiro only | Kiro only |
| `docs/ic20-hle-findings/gemini-work/` | **Gemini** | Gemini's private drafts & scratch | Gemini only | Gemini only |
| `docs/ic20-hle-findings/shared/`      | **Shared** | Completed, reviewed findings | Author moves finished docs in | Everyone |

**Rule to avoid file locks:** each agent edits ONLY inside its own `*-work/`
directory. When a document is complete, the author **moves** (not copies) it into
`shared/`. Never edit a file that lives in another agent's work dir. Treat
`shared/` as append-mostly: prefer adding a new file over editing someone else's.

## Status
- See `shared/` for finalized findings.
- Kiro's in-progress notes live in `kiro-work/`.
