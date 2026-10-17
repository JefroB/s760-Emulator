# RoboSampler modulation capture contract

Use RoboSampler ZIPs in the same format as `s760_01 Survey_20261015_161418.zip`: original WAVs, SFZ, metadata.json and metadata.txt. Analyze raw WAVs; treat SFZ as playback metadata rather than applying its gain/release adjustments. Numeric MIDI notes from metadata.json are authoritative. Stereo recordings are accepted; preserve both channels even when only one is analyzed.

Use3 seconds held and3 seconds release, velocity127, one layer, channel1. Initialize CC7=127, CC10=64, sustain off, mod wheel0 and centered bend. Keep unprocessed recordings and fixed sampler/interface gain within each session. Include output connection, recording gain and sample rate when known. Record any gain change between versions. No full-keyboard/all-patch capture or five-take batch is requested automatically.

## Louder V2

MODV2.IMG raises the exact existing source PCM by15x (+23.52dB). Original noise sample values are multiplied; noise is not regenerated from different RNG bounds. Patch maps, envelopes, filters and partial/sample routing are unchanged. Only PCM and version labels differ from V1. Both builds remain preserved.

The first gain pilot is patch01 SURVEY at numeric MIDI73, velocity127,3s hold/3s release: one WAV plus normal RoboSampler metadata. This is a level check, not a request to repeat the previous survey. Verify the hardware recording is unclipped; the native headroom check cannot establish interface headroom.

Original-firmware native Load and11 representative notes pass with no clipped/nonfinite audio. Exact PCM scaling and reproducible image hashes pass. See [volume validation](../../condensed/validation/modulation-v2-volume-2026-10-15.json).

This louder image remains a TVF-only survey. It does not implement or qualify the full envelope/LFO matrix, spectral controls, repeated hardware takes or independent validation in the proposed plan. The MIDI73 periodic mismatch remains unresolved.

## Hardware gain pilot received

The supplied MIDI73 V2 ZIP passes the gain pilot:23.5255dB held-RMS increase relative to V1, peak−25.4348dBFS, no full-scale clipping or nonfinite samples. Stereo48kHz, velocity127 and3s hold/3s release metadata match the request. No gain-only recapture is needed. The existing periodic audio discrepancy remains reproducible and unresolved; see [pilot validation](../../condensed/validation/modulation-v2-gain-pilot-2026-10-15.json).
