# Hardware documentation consolidation — 2026-10-21

The maintained hardware reference is [docs/hardware](README.md). The former `ic20-hle-findings` name conflated IC20, an I/O gate array, with the external boot EPROM at IC15. No replacement `hardware-findings`, shared log or per-agent working hierarchy is needed.

## Retained material

- Manufacturer manuals and the service-note OCR remain in their existing locations. OCR is explicitly a search aid, not authoritative component spelling.
- Hardware identity, banking/boot, DSP evidence limits, CRT/LCD and physical controls are consolidated into the topic pages linked from the hardware index.
- All 37 existing physical CRT photographs remain under `screenshots/`. The screen catalog links directly to those originals. Unsupported wireframes, calibrated palettes, timing claims and inferred SIMM geometry have been removed.
- Bounded filter/modulation reports and the current TVFSTEP stimulus recipe remain under `captures/`. Superseded deployment instructions and capture chronology have been removed.
- Existing condensed summaries, firmware analysis, acceptance reports and validation remain in their maintained topic directories. Ninety-four top-level shared JSON records were byte-identical to retained condensed validation. The other eighteen are retained as ten [hardware observations](evidence/historical-validation/README.md) and eight [product/runtime observations](../testing/evidence/historical-research/README.md), without promoting them into new hardware claims. Their relocation hashes are in the preservation manifest.
- Twenty-six compiler evidence files and local fixture files were copied and hash-checked before cleanup. The [preservation manifest](evidence/preserved-artifacts-2026-10-21.json) records source/destination, size and SHA-256. Compiler test XML/log/JSON evidence is under `docs/testing/evidence/toolchain/`; three private fixtures are under ignored `temp/fixtures/`. Qualification records now resolve their retained JUnit evidence at the new paths. Original historical commands and pinned baseline bytes remain unchanged.

## Corrections

Removed unsupported claims include a hidden IC20 boot ROM, an unconditional flat OS address map, stack-neutral PUSHA/POPA as hardware semantics, 32 physical voices, eight individual outputs, an AK5339 ADC, exact Hermite/ZDF hardware algorithms, a fabricated DSP register map, a proposed flat D000 VDP map and an E000 LCD map. Current pages distinguish primary hardware facts, contextual firmware observations and native implementation.

Agent skills and always-on hardware/boot rules now use the maintained references and `temp/work/` rather than reproducing the obsolete findings workflow. Verification defaults and the native PCM-origin test use the relocated paths. Package auditing intentionally continues to reject the legacy findings directory in distributions.

## Cleanup scope and limits

The initial inventory counted 814,991 files with 438,660,103,136 bytes of logical content in the old tree. Most were generated work/build copies. These figures are file sizes, not measured physical disk space reclaimed. The inventory and audit scripts remain private under `temp/work/hardware-findings-cleanup/`.

After preservation, the working/shared output and the explicitly user-approved top-level archive were deleted. The obsolete `docs/ic20-hle-findings/` directory is gone. Automatic approval review initially required clarification for archive deletion; the user supplied it before that deletion proceeded.

## Verification

The final full backend run passed **1,235 tests**, with **2 pre-existing from-scratch boot-observer/property skips**, in 245.83 seconds. The relocated native MODDIAG fixture ran without introducing another skip. All 44 retained artifact identities match the preservation manifest, hardware/evidence local Markdown links resolve, and the old tree is absent. Both compiler `target-contract` and `baseline` qualification gates pass with relocated evidence. The [verification record](../testing/evidence/hardware-consolidation-2026-10-21/verification.json), [JUnit results](../testing/evidence/hardware-consolidation-2026-10-21/suite-results.xml) and [test log](../testing/evidence/hardware-consolidation-2026-10-21/suite.log) retain the checks and their scope. No native source or binary was changed by this consolidation.

This consolidation checks retained claims against manuals, existing bounded evidence and current source; it does not independently requalify every custom-chip behavior or every old experiment. Historical machine records can contain retired paths as provenance. New experiments must regenerate output from maintained tools and must not depend on deleted scratch files. See [evidence limits and open questions](evidence-and-open-questions.md).
