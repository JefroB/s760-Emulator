# S-760 documentation

Guides and technical references for the Roland S-760 native emulator, standalone
player, VST3 instrument and firmware research.

## Start with your task

| I want toâ€¦ | Read this |
| --- | --- |
| Install firmware and run the sampler | [Firmware setup](emulator/guides/firmware-setup.md), then [standalone player](emulator/guides/standalone-player.md) or [VST3 configuration](emulator/guides/native-plugin-configuration.md) |
| Use a packaged Windows build | [Packaged setup guide](emulator/guides/standalone-package-readme.md) |
| Load media, sample or restore a session | [Media library](emulator/guides/native-media-library.md), [sampling](emulator/guides/native-sampling.md), [sessions and recovery](emulator/guides/native-sessions.md) |
| Build the native engine and host | [Native boot and audio runbook](condensed/11-native-boot-and-audio-runbook.md), [C++ runtime](emulator/runtime/native-cpp-runtime.md) |
| Run tests or review qualification | [Testing](testing/testing.md), [SoundCheck projects](testing/soundcheck-projects.md), [release qualification](testing/distribution-qualification.md) |
| Check priorities and known defects | [Completion roadmap](project/completion-roadmap.md), [bug backlog](project/bug-backlog.md) |
| Understand the hardware and firmware | [Condensed reference](condensed/README.md), [firmware decoding index](firmware/README.md) |

## Browse by subject

| Folder | Covers |
| --- | --- |
| [emulator/](emulator/README.md) | Our software: setup and usage, native runtime, standalone/VST3 integration and interface |
| [hardware/](hardware/README.md) | Roland's physical machine: chips, displays, controls, hardware captures and screen evidence |
| [firmware/](firmware/README.md) | Roland's OS and IC15 boot ROM, subsystem decoding and firmware analysis tooling |
| [testing/](testing/README.md) | Test instructions, coverage inventories and dated acceptance reports |
| [project/](project/README.md) | Roadmaps, bugs, licensing, proposals and early investigation history |
| [condensed/](condensed/README.md) | Consolidated references spanning hardware, firmware and emulator behavior |
| [distribution/](distribution/README.md) | Upstream notices, provenance and reviewed package manifests |

Documentation filenames use lowercase kebab-case, with `README.md` reserved for
directory entry points. Numbered reference prefixes retain their reading order.
Each subject folder has an index; links may cross subjects when the evidence does.

## Reference collections

- [Condensed technical reference](condensed/README.md): consolidated hardware,
  firmware and implementation conclusions, with scope limits and evidence.
- [Condensed source map](condensed/source-map.md): provenance for those conclusions.
- [Real hardware UI analysis](hardware/screens/index.md): screen families,
  layouts and capture evidence.
- [React interface development](../google-ui/README.md): frontend setup and tooling.
- [Project overview](../README.md): supported product profiles and quick start.

## Reading status and evidence

Use the completion roadmap for project gates and the named acceptance reports for
qualified workflows. Dated research results and test counts describe their recorded
profile; they are not blanket claims of hardware parity or release readiness.

The numbered `01`â€“`05` investigation notes and chronological findings log are
historical records. Their early CPU hypotheses are superseded by the consolidated
[hardware and memory map](condensed/01-hardware-and-memory-map.md), which identifies
the Intel 80C196KB CPU.

Maintained hardware documentation lives in [hardware/](hardware/README.md), including reviewed results from the former findings tree. Validation artifacts remain in `condensed/validation/` and explicitly indexed evidence directories. Generated runs belong under `temp/work/`; private fixtures under `temp/fixtures/`. The old findings tree and its shared/working archives were removed during the [2026-10-21 consolidation](hardware/documentation-cleanup-2026-10-21.md).
