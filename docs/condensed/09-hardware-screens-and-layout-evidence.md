# Hardware Screens & Layout Evidence

Condensed from all ten public files in `real-hardware-ui-analysis/`, checked
against the screenshot index and current extractor source. This summarizes
documented observations; photos remain the visual reference, and heuristic
reconstructions remain candidates rather than exact runtime specifications.

## Photographed screen catalog

The index enumerates **37 photographs**, by source filename:

| Mode | Files | Screens |
| --- | --- | --- |
| Disk | DISK-1/2 | Load; loading/scanning modal |
| Perform | perform-1…5 | Play 1; Mark; Jump; Command; Perform menu |
| Patch | patch-1…4 | Common; Split; Control; Q-Sampling |
| Partial | partial-1…6 | Common; SMT; TVF; TVA; LFO; Q-Sampling |
| Sample | sample-1…15 | Sampling; Loop&Smoothing; Auto Trun/Norm; Time Stretch; D.Filter; Comp/Expand; Rate Convert; Bit Convert; Truncate; Cut & Splice; Area Erase; Insert; Mixing; Combine parameters; Combine waveform |
| System | system-1…5 | Parameter 1; SCSI; MIDI; Volume ID; Load/Save System PRM |

Detailed source docs retain per-screen wireframes, labels, and example values.
Example values are the captured state, not defaults or allowed ranges. The
system photos document this unit's 32 MB expansion and SCSI host ID 7.

## Common visual structure

Six persistent tabs: Perform, Patch, Partial, Sample, Disk, System. Above them
is the global volume/device/context banner; below them is screen title and
mode/Mark/Jump/Com controls. The workspace contains parameter tables, keyboard
zones, envelopes, waveforms, and modal overlays. Bottom actions are contextual
softkeys/status; screen softkeys and physical F1–F6 are not interchangeable.

The documented appearance uses blue workspace, green global banner, white
active tab with orange/red text, gray inactive tabs, cyan labels/action areas,
yellow section headings, white values/waveforms, and red slider triangles.
Mark/Jump popups are described with yellow borders, Command with red, and
Perform menu with green. Photo-derived hex values and approximate pixel zones
are visual estimates, not measured palette/DAC specifications.

Reusable structures: horizontal sliders with triangle markers; time/level
envelopes; waveform overview + full view + splice zoom; keyboard range bars;
contextual action/checkbox strip. Preserve the photo's actual labels/order when
implementing a screen rather than importing unrelated parameter ranges from
older manual matrices.

## What the extractor actually establishes

`.agents/scripts/extract_screen_layout.py` supplies a known-offset lookup and
candidate decoder. It searches magic `28 16 F0 C0 00 FF`, scans plausible
`x,y,attribute,NUL-terminated ASCII` records, and uses a regex after FF for up to
six candidate softkeys. It has fallback byte scanning and a fixed 1,200-byte
chunk. It does **not** decode the claimed seven-byte input-field bindings.

Therefore the source supports candidate static labels/coordinates and text
wireframes. It does not establish universal 17-byte headers, exact color
semantics, full parameter bindings, dynamic widgets, or “100% screen fidelity.”
Those claims were removed from the condensed specification and requested as
evidence in shared notes.

Useful candidate **file offsets**, from the extractor:

| Screen group | Offsets |
| --- | --- |
| Perform Play 1–6 | A707A, A7B1E, A86FA, A8CFE, A9272, A9BDE |
| EQ / MIDI Filter / Module Monitor / MIDI Monitor | 92026 / 924FC / 92E74 / 92F74 |
| Disk Load/Save/Copy/Delete/Utility/Save System | 9569C / 95CA4 / 95D8C / 95F82 / 9674E / 9763A |
| Patch Common/Split / Partial Template | 98410 / 98680 / 9B348 |
| System PRM1/2 / Volume Info / SCSI / MIDI | A3866 / A3A6C / A4216 / A43C0 / A481C |

These are resource anchors; they are not resident PCs. Different occurrences
of a screen title in the string catalog need not be the descriptor start.
`VDP_LAYOUT_DESCRIPTORS.json` preserves extracted candidate data; retain its
provenance rather than treating JSON output as independent validation.

## Capture priorities

The inventory's headline “58 screens, 16 inferred, 53 documented” conflicts with
its **65 numbered rows** and inconsistent per-mode totals. The reliable count
here is the 37-photo index; an exhaustive total requires deduplication and a
definition of screen versus popup/view. No percentage is asserted.

Remaining useful captures: Module Monitor while notes play; Perform Part Map;
Disk Save and overwrite dialogs; Disk Utility/format/park dialogs; another mode
dropdown to compare styling. These are priorities, not proof that only five
photos would establish complete OS coverage. Dynamic state and input behavior
need recordings/traces in addition to stills.
