# Independent review of Gemini cumulative batch L

The saved batchL represents substantial candidate exploration, but its raw totals cannot yet be promoted as verified OS code. Original image bytes and file mapping match throughout; the maintained baseline is retained; all33,184 direct targets agree independently; no declared code/data conflicts were found.

The snapshot contains7,157 regions and129,491 unique instruction encodings, covering377,306 candidate code bytes plus3,405 data bytes (36.88% of the loaded payload). Independent checks examine163,961 PC/file locations, including aliases:138,103 agree in length/mnemonic and25,858 disagree. These location counts are distinct from the unique-encoding metric.

## Confirmed problems

Installed SLEIGH decodes SKIP as one byte and IDLPD as two. Intel's KB instruction table specifies SKIP2 and IDLPD1; both independently compiled MAME decoders agree. This accounts for25,837 disagreements. BUG-086 records the source identity and tiny reproducible probes. The other21 disagreements involve indexedXCH/XCHB orTIJMP and retain processor-variant/support qualifications. No installed processor package was changed.

The global byte-ownership check finds1,360 distinct directed boundary-conflict pairs (not1,360 unique bad functions). For example, candidate page0000:416D starts at file496D, inside the established three-byteLCALL at file496B. New pipelines scan rawRET/F0 bytes and decode following bytes; anF0 inside data or an operand is not a justified function boundary. BUG-087 records this acceptance gap. All original bank links remain79; thousands of candidates add no qualified mapping links.

Conservative whole-region triage flags1,504 regions for decoder/variant or boundary review;5,653 are clear of those particular checks. Clear does not establish actual entry, preserved bank selectors, runtime reachability or recovered behavior. Do not subtract flagged byte counts from the raw total and call the remainder verified; overlapping and dependency effects require reanalysis.

## Reproducibility and next steps

[Summary and source evidence](../../condensed/validation/os-batch-l-review-summary-2026-10-16.json), [all independent comparisons/conflicts](../../condensed/validation/os-batch-l-independent-196-review-2026-10-16.json), and [per-region triage](../../condensed/validation/os-batch-l-review-triage-2026-10-16.json) are durable. Frozen inputs and review/build scripts are retained privately. The review preserves original ROM/OS, Gemini scripts/exports and the maintained exploration manifest.

Correct the KB decoder lengths in a separately controlled decoder, regenerate affected candidates, reject unexplained global boundary conflicts, and promote entries from justified references with explicit fetch contexts. Candidate counts remain separate from behavioral acceptance. Earlier round4's independent agreement remains valid for its tested encodings.

Maintained OS classified-byte coverage:62,736/1,032,192 =6.08% (+0.00 points). Boot ROM:26,277/32,768 =80.19% (+0.00 points). Overall decoding completion: not yet quantifiable. No new candidate bytes promoted by this review.
