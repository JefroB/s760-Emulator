# Boot-ROM inspection views

The OS setup scripts in this directory and IC15 use different mapping contracts. To export the qualified original boot ROM:

```powershell
python scripts/ghidra/export_ic15_contexts.py --output temp/ghidra_ic15
```

This creates two16KB fetch views and one16KB resource-data view, each with its import base and SHA256 in `contexts.json`. Import each as a separate raw program with language `MCS96:LE:16:default`:

| View | CPU base | Selector |
| --- | --- | --- |
| fetch_low_0780.bin | 0000 | 0780 |
| fetch_high_0790.bin | 4000 | 0790 |
| data_resources_0798.bin | 8000 | 0798 |

The resource view includes the actual ROM mirror wrap: file6000..7FFF followed by0000..1FFF. `entries.csv` retains declared function-entry labels, file offsets and evidence. `contexts.json` preserves all manifest regions, conditional bank links and bounded data annotations. Structural roots retain their invocation uncertainty; the exporter does not disassemble gaps or assert that every entry is a function.

Keep automatic whole-image analysis off. These are inspection views, not a complete bank-aware decompiler loader. Fetch4000..7FFF is ROM while logical data4000..7FFF is work RAM through data010A=03F0. A flat import cannot correctly represent both. Follow data references using explicit selector contexts and original bytes before trusting pseudocode.

The tool checks the original ROM hash, manifest identity and output/input separation. Five focused tests cover mirror wrap, fetch bases, invalid contexts and original-input protection. See [boot-ROM progress](../../docs/firmware/boot-rom/ic15-decoding-progress.md) and [mapping audit](../../docs/firmware/boot-rom/ic15-configuration-and-mapping-audit.md).
