"""DAC-image harmonics retain physical source phase at higher analysis resolutions."""
import numpy as np
import pytest
from scripts.verify_static_filter_captures import periodic_shift

@pytest.mark.parametrize('points',[8192,16384])
def test_fractional_source_delay_retains_recording_band_image_phase(points):
    coordinate=np.arange(points)/points
    delay=.317
    # Harmonic2200 is above source Nyquist2048, within the48kHz recording band.
    harmonics=[60,1450,2200];amplitudes=[.2,.3,.4];phases=[.7,-.2,1.3]
    original=sum(a*np.cos(2*np.pi*k*coordinate+p) for k,a,p in zip(harmonics,amplitudes,phases))
    expected=sum(a*np.cos(2*np.pi*k*(coordinate-delay/4096)+p) for k,a,p in zip(harmonics,amplitudes,phases))
    np.testing.assert_allclose(periodic_shift(original,delay),expected,atol=2e-12,rtol=0)
    np.testing.assert_allclose(periodic_shift(periodic_shift(original,delay),-delay),original,atol=2e-12,rtol=0)
