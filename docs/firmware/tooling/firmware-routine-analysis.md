# Bank-qualified firmware routine analysis

Milestone 7 now has a first bounded OS analysis tool. It produces byte-linked assembly, instruction control-flow graphs and incoming/outgoing cross-references through a machine-readable edge list. It does not yet produce compilable source, recover types, rebuild firmware, or qualify the boot-ROM target.

## Generate local views

Milestone 7's separate import/build-manifest objective is complete. `scripts/firmware_manifests/os_disk.json` and `ic15_rom.json` describe distinct containers and mappings, hash-identified immutable inputs, CPU variant, entry/vector locations, known annotations, whole-image preservation layouts and fixed-layout build contracts. Unknown code/data regions and integrity fields are explicitly retained. No builder is claimed by these manifests.

Validate each locally supplied original:

```powershell
python scripts/validate_firmware_manifest.py scripts/firmware_manifests/os_disk.json S760224.IMG
python scripts/validate_firmware_manifest.py scripts/firmware_manifests/ic15_rom.json roms/BOOT/Roland_S-760_v1.11.BIN
```

Both inputs pass. Eleven manifest tests plus twelve analysis tests pass. The validator reads inputs only. OS loading maps disk 0x4800..0x1007FF to physical RAM 0..0xFBFFF, with handoff at page 0:C000. IC15 has a separate 32 KB mirrored ROM mapping, with CPU reset entry 2080. Its physical power-on selector defaults remain uncertain; the manifest explicitly distinguishes the native boot mapping from that unknown. The vector-area description is a runtime CPU address contract, not a claim that the disk's same-numbered offsets contain its live vectors. No checksum recomputation has been qualified.

Requires Python with `pypcode==4.0.0` (the version used for validation). From the repository root:

```powershell
python scripts/analyze_firmware_routines.py S760224.IMG scripts/firmware_manifests/os_filter_paths.json --output temp/firmware-routines
python -m pytest tests/test_firmware_routines.py -q
```

Open `temp/firmware-routines/routines.md` for research summaries, context-qualified bank links, assembly and unresolved edges. Each instruction lists its fetch page, CPU address, input-file offset and original bytes. `analysis.json` retains instruction, edge and basic-block records. Per-region `.dot` files can be rendered with Graphviz; `.blocks.dot` groups straight-line instructions into basic blocks. Generated firmware views stay in ignored local output directories; the checked-in manifest contains addresses and evidence, not firmware bytes.

The input SHA256 must match the manifest. The OS mapping is `file = 0x4800 + (fetch_page << 10) + (PC & 0x3fff)`. Fetch page is selected independently for each 16 KiB CPU window; data selectors are separate. A numeric destination alone does not identify its bank. The tool never resolves a cross-region destination by assuming the caller's page.

## First analysis targets

| View | Entry | Purpose |
| --- | --- | --- |
| Timer ISR | 0000:CAD1 | TIMER1 sample, service calls, normal and fallback rearm |
| Mouse handshake | 004B:57B4 | Interrupt masking and four-nibble mouse polling |
| TVF dispatcher | 002D:8000 | Eight annotated stage entries, counted and fast paths |
| Cutoff calculation | 001F:46F1 | Integer control-to-cutoff conversion |
| Initial cutoff | 002D:9270 | Companion cutoff initialization writes |
| Control service | 001F:4000 | Service entry and voice-loop calls, including TVF dispatch |
| DSP delay | 001F:46C2 | Fourteen NOPs and RET called during cutoff initialization |

These names are maintained research annotations. Decoder register names are not original source names. Bounds are analysis windows, not proof of complete function extents. The TVF indirect target list comes from the observed stage model and the dispatch expression; an unresolved edge remains for other stage values.

The timer path reads TIMER1 at CB00 and normally rearms from that saved value plus 20000. Its alternative uses current TIMER1 plus 1000. This distinguishes service-relative scheduling from deadline-relative scheduling. The mouse routine begins with PUSHA and restores flags with POPA at 5811; timing qualification still requires the CPU documentation and matched traces. The cutoff calculation has already been checked against integer replay. These views expose the instructions behind those findings; they do not establish physical filter command semantics. See [modulation evidence](../os/modulation-firmware-path.md).

## Guarantees and limitations

- Recursively follows direct control flow inside each declared mapping; stops at returns and unresolved indirect branches. Calls include an assumed return edge.
- Retains unreachable bytes as undecoded ranges. It does not silently treat them as data or code.
- Rejects input hash mismatches, overlapping instruction boundaries, invalid entry points and regions crossing fetch windows.
- Normalizes direct CPU destinations to 16 bits while retaining the decoder's original operand display.
- Does not propagate bank-register writes, infer callee effects, resolve data aliases, or lift arithmetic to high-level expressions. Declared mappings must be reviewed against native traces. A resolved edge means local static address resolution, not proof that runtime bank state remains unchanged.
- No original image, ROM, emulator or guest state is changed.

## Context-qualified call chain

The timer ISR writes fetch selectors 0102=001F and 0104=002D before calling 4000. The service routine reaches a call to 8000 at 442D. This supplies a useful path from timer service into the TVF dispatcher, conditional on intervening callees preserving those selectors. The tool records that condition explicitly; it does not claim whole-program bank propagation. TVF calls/tail branches to 46F1 link to the cutoff calculation only in the 001F fetch context. Initial-cutoff 9273 similarly links to 001F:46C2. That routine contains fourteen NOPs and RET; its name does not establish the delay's physical purpose.

Bank links require a decoded source edge, a decoded target instruction boundary, evidence and a context. They do not remove the original unresolved edge or apply automatically to other invocations. Maintained summaries are interpretation, not automatically generated high-level source.

The earlier bank-link pass covered 843 instructions in seven regions. The subsequent [filter modulation dataflow analysis](../os/filter-modulation-dataflow.md) expands this to 1121 instructions in ten regions, with 26 context-qualified links and no decoder warnings. It explains the producer of the base-cutoff word and both initial-counter branches. Wider coverage introduces more visible unknowns; it does not establish complete OS coverage. Twelve synthetic analysis tests pass, including wrapped destinations, instruction boundaries, bank separation, conditional block splitting, link validation and deterministic output; eleven additional manifest tests pass.

Next steps are bank-state propagation with conservative callee effects, richer evidence-backed data/symbol annotations, expression views, and a separately qualified IC15 import manifest. Source rebuilds and modified firmware acceptance remain later Milestone 7 gates.


## Broader mapping support

The analyzer supports explicit mirrored-ROM mappings separately from the OS payload mapping. ROM mirror size must match the input and be a power of two; the physical aperture must align to it. Regions crossing a mirror boundary are rejected. Direct absolute ST/STB/POP writes overlapping the currently executing window's fetch selector now stop recursion automatically, including high-byte and unaligned overlapping writes. Explicit manifest stop annotations remain supported. Indirect writes, propagated register values, callee preservation and interrupt effects remain unresolved.

`firmware_bank_frontier.py` inventories only adjacent decoded LD/ST/CALL sequences linked by fallthrough edges. It rejects data selectors, calls into a different window, invalid payload offsets and current-window remaps. It rejects ROM inputs outright, rather than silently applying OS file offsets. Candidate output is conditional evidence for reviewed roots, not a proof of whole-program reachability. The targeted fixture suite now has47 passing tests.
