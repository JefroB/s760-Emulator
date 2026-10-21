# Evidence and unresolved hardware questions

Use manufacturer manuals for component identities and wiring, identified original bytes plus bank context for firmware behavior, and physical captures for measured behavior. Cite the exact page, input identity, trace or capture profile supporting a claim. Source code establishes what the emulator implements, not automatically what the chip does.

Detailed research summaries and retained validation records remain under [condensed research](../condensed/README.md). Their dated observations have the scope stated in each report. Some machine records retain historical paths or commands from the removed scratch tree; those strings identify past runs and are not current instructions or live file links. Compiler evidence relocation is recorded in the [preservation manifest](evidence/preserved-artifacts-2026-10-21.json).

Unresolved work includes custom DSP arithmetic and scheduling, moving/resonant TVF parity, full VDP mode/mask/cursor behavior, physical video timing, attribution of some peripheral windows and complete low-power CPU behavior. Do not substitute an emulation formula, screenshot estimate or successful boot for missing hardware evidence. Track actionable defects in the [backlog](../project/bug-backlog.md) and implementation acceptance in the [roadmap](../project/completion-roadmap.md).

For new work, use `temp/work/<task>/` for generated logs, recordings, binaries and experiments. Keep only reviewed explanations and the compact evidence needed to support them in maintained documentation. Do not recreate shared or agent-specific research folders under docs. User firmware, generated disk fixtures and raw recordings are not documentation; local retained fixtures live under `temp/fixtures/` and are not distribution inputs.
