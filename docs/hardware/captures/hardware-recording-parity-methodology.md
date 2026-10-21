# Hardware recording and comparison method

Define the comparison before capture: firmware version, sample image and PCM identity, performance/patch/partial settings, MIDI events, output routing, recorder rate and gain. Record the physical output used, cabling, interface and any processing. Keep original recordings unchanged; report clipping, noise and channel differences.

Use a stationary control alongside a changing stimulus. Preserve leading silence and complete note/release tails. Disable DAW effects, normalization, warping and unintended MIDI bank/program changes. Repeat relevant cases to distinguish a repeatable device response from clock drift, setup variation or capture alignment.

Separate raw timing from analysis alignment. State every fitted gain, offset, resampling or clock correction, and report the comparison before and after it. A correlation-fitted start is not an independently measured source origin. Prefer native sample-origin metadata and application traces when available. Choose error metrics and acceptance tolerances for the stated experiment; there is no universal 60 dB null criterion establishing S-760 hardware parity.

Static frequency agreement cannot establish modulation behavior, resonance transients, hardware interpolation arithmetic or a particular filter topology. The ADC identified in the service notes is CS5339-K, and the instrument has 24-voice polyphony. Native interpolation/filter algorithms remain software models unless independently demonstrated against the relevant hardware conditions.

Use the [TVFSTEP kit](tvf-transition-capture.md) for its documented step/ramp profile and the [RoboSampler contract](modulation-robosampler-capture.md) for its separate modulation profile. See the [dated comparisons](README.md) for measured conclusions and limits. Store raw run output under `temp/work/`; promote compact validation and a reproducible explanation only after review.
