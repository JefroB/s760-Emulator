# Milestone 5 supported-workflow acceptance matrix

Updated 2026-10-14. **Milestone5 is complete for the documented development profiles.**
This matrix records bounded development-profile evidence,
not final-package or complete hardware qualification. The
[roadmap](../project/completion-roadmap.md) controls scope; pending rows are not advertised
as qualified. Each linked validation record identifies its tested artifacts,
fixtures, prerequisites, commands and limits. Changed artifacts need requalification.

| Workflow/domain | Evidence and observable result | Status/limits |
| --- | --- | --- |
| Native MIDI/controllers/panic | [SoundCheck controller record](../condensed/validation/milestone-4-controller-semantics-2026-10-13.json), [current repeat](../condensed/validation/milestone-4-controller-requalification-2026-10-13.json): measured configured effects, routing and release/reset sequences | Qualified named firmware profile; raw CC120/121 unsupported; BUG-060 functional-QA contract corrected; realtime deadlines remain separate |
| Standard 720 KB media | [Format](../condensed/validation/standalone-formatting-2026-10-12.json), [write protection](../condensed/validation/standalone-write-protection-2026-10-12.json): firmware operations, protected rejection and fresh reload | Native runtime; broader floppy formats deferred |
| Standalone recording/Save/Load | [Physical recording](../condensed/validation/native-physical-sampling-2026-10-12.json): 65,514 exact frames/channel and saved allocation bytes survive fresh firmware Load | Physical device capture plus native persistence; supported 44.1 kHz stereo profile, not analog calibration or alternate ADC clocks |
| Plugin recording/Save/Load | [SoundCheck input](../condensed/validation/milestone-4-host-sampling-2026-10-13.json): 45,649 exact frames/channel and all 184,320 allocation bytes survive fresh Load | Actual SDK/native QA host; optional 44.1 kHz stereo input only |
| Loop modes/short samples | [Seven modes and retrigger](../condensed/validation/milestone-5-loop-modes-2026-10-14.json): exact repeating sign/direction sequences, one-shot completion, silent release, 1,058,400 exact checkpoint replay frames | Native 44.1 kHz/unity pitch; named octave transitions qualified separately below; no new physical fidelity claim |
| Polyphony/allocator | [Allocation trace](../condensed/validation/milestone-5-polyphony-2026-10-14.json): 24 counted voices, eight recycled slots, original note-offs preserve replacement voices, retrigger/sustain release clears slots and audio | Native ROBOFULL fixture; no exact steal-priority or arbitrary layered-patch matrix claim |
| Session/project recall | [Standalone session](../condensed/validation/standalone-media-session-2026-10-12.json), [SoundCheck project](../condensed/validation/milestone-4-soundcheck-project-2026-10-14.json): cold exact replay and supported media/configuration restoration | Same-build documented profiles; cross-build/rate/maximum migration unsupported |
| Native SCSI prerequisites | [Native address/selection/absence](../condensed/validation/milestone-5-scsi-prerequisites-2026-10-14.json): stride2/full address window, absent-target timeout, INTS read preservation/write acknowledgement; source-backed targets only | Qualified isolated contract; legacy semantics kept separate; no firmware discovery/Load claim |
| Native SCSI idle status | [Status correction](../condensed/validation/milestone-5-scsi-status-2026-10-14.json): idle, counter-zero, asserted/deasserted reset and absent-selection recovery | Isolated contract passes; native audio/MIDI and cold state pass; discovery remains open |
| Original-firmware SCSI discovery/recovery | [Native firmware evidence](../condensed/validation/milestone-5-scsi-discovery-2026-10-14.json): No Drive/Unformatted labels, Not Formatted rejection; three cases recover119808 exact floppy sample bytes and release silently; source images unchanged | Qualified native HD0/512-byte-sector development profile; partial traces, synchronous input DMA; no formatted SCSI Load or physical timing claim |
| Akai S1000 SCSI Convert Load | [Native genuine-CD evidence](../condensed/validation/milestone-5-akai-scsi-load-2026-10-14.json):30 samples/13,568,196 PCM bytes, observed firmware tail adjustments, imported patch assignment, three-key playback/release, unchanged CD and65536 exact cold stereo frames | Qualified first String.Ensembles volume, CD1/2048-byte sectors,32 MB; no arbitrary CD, Save, hot-plug or physical timing claim |
| Native Roland SCSI performance Load | [Full JMD CD evidence](../condensed/validation/milestone-5-roland-scsi-load-2026-10-14.json): K4 performance/patches,79 allocations/6,054,912 exact bytes, mapped drums/melodic playback, silent release and65536 exact cold frames | Qualified first K4 performance, CD1/2048 sectors,32 MB; immutable CD remains external/hashed; other libraries and Save unqualified |
| Native HD0 initialization/Save/export/Load | [SCSI writes](../condensed/validation/milestone-5-scsi-save-2026-10-14.json): firmware initializes a private10MiB HD00_512.img, saves a performance and fresh-loads13 allocations/119808 exact bytes with matching playback | Qualified HD0/512 sectors; explicit Python export only, source preserved; automatic library overwrite and packaged GUI/VST export unqualified |
| Patch editing/Save/fresh Load | [Native patch edit](../condensed/validation/milestone-5-patch-edit-2026-10-14.json): Bend Up/Down0 to12 via firmware Value controls, audible changes and identical measured frequencies/peaks after separate-process Load | Qualified named patch operation; native controls, not final shipped-interface acceptance |
| Performance editing/Save/fresh Load | [Native part-level edit](../condensed/validation/milestone-5-perform-edit-2026-10-14.json): part1 Level127 to64, measured gain0.503743, unchanged pitch, matching edited/cold-loaded peaks and silent release | Qualified named part-level operation; master level and broader performance operations unqualified |
| Partial editing/Save/fresh Load | [Native coarse-tune edit](../condensed/validation/milestone-5-partial-edit-2026-10-14.json): Coarse Tune0 to12, measured248Hz to495Hz at1Hz FFT resolution; matching edited/cold-loaded frequency/peak and silent release | Qualified named coarse-tune operation; broader partial parameters unqualified |
| Destructive sample editing/Save/fresh Load | [Native Area Erase](../condensed/validation/milestone-5-sample-erase-2026-10-14.json): whole-range sample1, zero fade;8192 zero source-body bytes, silent playback,9216 exact cold-loaded allocation bytes and110592 unchanged neighboring bytes | Qualified named Area Erase case; subranges/fades, Truncate, Cut/Splice, Normalize and other commands unqualified |
| Floppy Load under MIDI | [Native Load/MIDI](../condensed/validation/milestone-5-disk-midi-2026-10-14.json): 240 serial events, 152 observed overlapping FDC writes, 119,808 exact sample bytes and post-load silent release after cleanup | Qualified bounded native workload; trace truncation explicit, no guest event-preservation claim |
| Disk/Load note restriction and recovery | [Native control/three trials](../condensed/validation/milestone-5-disk-voice-restriction-2026-10-14.json):12 source2 status slots in Perform; directory mode clears voices and suppresses allocations despite serial notes; complete FDC/wave traces, post-mode release and byte-exact clean media | Qualified named restriction; return to Perform before audition; no note-preservation or musical-continuity guarantee in this workflow |
| Disk/MIDI/voice restriction and recovery | [Manual and native Save/recovery](../condensed/validation/milestone-5-concurrent-recovery-2026-10-14.json): four active notes cleared,240 MIDI events,166 observed overlapping disk writes,1543500 silent Disk-mode frames,119808 exact fresh-loaded sample bytes and recovered playback/release; current three-trial Load restriction repeat passes | Qualified supported restriction/recovery. Manual Advanced1-3 excludes sound in Disk/Quick Load/Sampling and during Copy; prior ongoing-voices requirement corrected. No simultaneous three-source arbitration, musical continuity or event-preservation claim; Save trace is partial |
| Loop pitch/overlapping transitions | [Native octave matrix](../condensed/validation/milestone-5-loop-pitch-2026-10-14.json): seven modes at -12/0/+12 semitones, expected pitch words, >0.99 loop recurrence, scaled one-shots, 42 overlapping notes and silent release | Qualified named key/partial changes at44.1kHz; arbitrary ratios, continuous glide, click-free transitions and new physical parity not claimed |
| Diagnostic combined audio | [Native72-case matrix](../condensed/validation/milestone-5-combined-audio-2026-10-14.json): eight named patches, three pitches and three pans; finite bounded PCM, cutoff/sweep effects, forward loops and silent release | Qualified explicit diagnostic profile only; BUG-005 physical fidelity remains open; BUG-061 normal standalone stereo fixed in the later normal-profile record |
| Normal stereo defaults | [Normal-profile evidence](../condensed/validation/milestone-5-normal-stereo-2026-10-14.json): stereo pan, load/release, variable PCM and scheduled cold recall; recording remains opt-in; this dated record predates normal filter promotion below | Qualified native subset; old mono checkpoints reject by changed audio identity |
| Normal filter defaults | [Normal-profile record](../condensed/validation/milestone-5-normal-filter-2026-10-14.json):72 native cases, nine actual SoundCheck cases,220500 exact fresh-instance/variable-block frames,65536 exact active-filter cold frames and firmware Save/fresh Load | Qualified named LP/BP/HP coefficient profiles; raw fallback exclusions documented; BUG-005 physical fidelity remains open; BUG-060 functional-QA contract corrected; final-package repetition pending |

The minimal editing acceptance set is performance part1 Level, patch Bend Up/Down,
partial Coarse Tune and whole-range sample Area Erase with zero fade. This set
qualifies a representative edit at each hierarchy level; it does not imply all
firmware editing commands work. Broader editing combinations remain unqualified;
Milestone6 repeats the named complete workflow on final shipped artifacts.

Reproduce the new native scenarios from the repository root:

```powershell
python scripts/verify_native_disk_concurrency.py --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/disk-concurrency-new
python scripts/verify_native_scsi_save.py --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/scsi-save-new
python scripts/verify_native_roland_load.py --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/roland-load-new
python scripts/verify_native_akai_load.py --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/akai-load-new
python scripts/verify_native_scsi_discovery.py --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/scsi-discovery-new
python scripts/verify_native_scsi_identity.py --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/scsi-identity-new
python scripts/verify_native_scsi_pio.py --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/scsi-pio-new
python scripts/verify_native_scsi_dma.py --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/scsi-dma-new
python scripts/verify_native_runtime.py --combined-audio --combined-normal --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/normal-filter-new
python scripts/verify_native_checkpoint.py --filter-state --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/filter-state-new
python scripts/verify_native_scsi_registers.py --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/scsi-registers-new
python scripts/verify_native_runtime.py --disk-voice-stress --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/disk-voice-new
python scripts/verify_native_runtime.py --combined-audio --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/combined-new
python scripts/verify_native_patch_edit.py --sample-erase --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/sample-erase-new
python scripts/verify_native_patch_edit.py --partial-tune --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/partial-edit-new
python scripts/verify_native_patch_edit.py --perform-level --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/perform-edit-new
python scripts/verify_native_patch_edit.py --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/patch-edit-new
python scripts/verify_native_runtime.py --pitch-loops --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/loop-pitch-new
python scripts/verify_native_disk_midi.py --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/disk-midi-new
python scripts/verify_native_runtime.py --polyphony --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/polyphony-new
python scripts/verify_native_runtime.py --loop-modes --loop-stress --sample-disk D:/S-760/roms/FDD/ROBOLOOP.IMG --state-dir D:/S-760/docs/ic20-hle-findings/chatGPT-work/loops-new
```

Use fresh private absolute state paths and supply the local firmware/native binary.
These tests load samples through original firmware and send serialized MIDI;
polyphony observation uses read-only bus taps. They run headless and unthrottled,
so they do not measure physical output timing or driver losses. Slot counts
establish allocation state, not a spectral proof of every mixed voice.

Physical comparisons retain their original measurement-chain limits. Model
agreement, native functional acceptance, physical capture and packaged-product
validation are separate evidence classes; none substitutes for the others.
Track product defects in [the backlog](../project/bug-backlog.md), and repeat the complete
workflow on final shipped artifacts under Milestone 6.
