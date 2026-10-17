# Milestone 6 historical coverage-claim audit

Reviewed 2026-10-15 against source revision
`d8ff83ad1b5da2d157c1d323baf1d1d14fc1cc41` plus the working-tree documentation
corrections identified in the linked validation record. This closes the historical
claim audit subset only. Final setup instructions still require execution against
the final standalone/VST3 artifacts on clean machines.

| Reviewed surface | Disposition |
| --- | --- |
| README and completion roadmap | Scoped development acceptance; final release remains open |
| OS, exhaustive-code, UI and manual generated matrices | Unverified inventories; no measured coverage percentage; deterministic regeneration checked |
| testing.md | Historical totals and feature descriptions explicitly separated from current results and native product acceptance |
| LLE fidelity assessment | Exhaustive CPU/peripheral completion withdrawn; old DONE labels and register maps labelled historical |
| VDP architecture proposal | Authority and full hardware-accuracy claims withdrawn; current condensed reference linked |
| Screen inventory and inferred layouts | Inference no longer promises complete parameter/visual fidelity; proposed counts do not establish coverage; five captures are initial suggestions |
| Next-generation OS feasibility | Historical speculative estimates explicitly excluded from release acceptance and cycle-accuracy claims |
| Hardware recording methodology | Measurement target expressed in signals/settings/tolerances rather than universal bit/analog accuracy |
| Condensed testing/deployment references | Current development scope precedes dated checkpoints; model/native/physical/package evidence remains distinct |

The audit searched tracked Markdown documentation for percentage, full-coverage,
complete-testing and parity claims, then read the affected contexts. Parameter
values (for example gain100%), quoted withdrawn claims, historical results,
research proposals and actual measured errors are not whole-project coverage.
Historical technical proposals remain available for context; their labels and
addresses must not be used as current hardware specifications.

Validation: `python -m pytest tests/test_coverage_reports.py -q` with private
scratch paths passed **5 tests**. Four tests regenerate each report twice and
compare with committed output, reject unsupported badges and require scope
warnings. The fifth resolves reviewed selectors and checks their assertion/limit
descriptions. No firmware, runtime, GUI, physical hardware or packaged-product
tests were executed for this documentation audit. No new bug closure is claimed;
the catalog policy preserves the existing BUG-007 correction.

[Validation identities and command](../condensed/validation/milestone-6-coverage-audit-2026-10-15.json).
