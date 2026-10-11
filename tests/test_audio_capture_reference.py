"""Guard against measurement aliases being mistaken for S-760 DSP behavior."""
import numpy as np
import pytest
import sys
from conftest import ROOT
sys.path.insert(0, ROOT)
from scripts.audio_capture_reference import reconstruct_capture


def test_capture_reconstruction_rejects_folded_interpolation_image():
    rate = 48000
    clock = 44100.952
    # The full-keyboard pulse capture exposed this exact image family:
    # 48k - tone folds around the comparison clock into the audible band.
    tone = 126 * clock / 257
    x = 0.5 * np.sin(2*np.pi*tone*np.arange(rate)/rate)
    t = np.arange(1000, int(clock)-1000)/clock
    y = reconstruct_capture(x, rate, t)
    image = clock - (rate - tone)
    window = np.hanning(len(t))
    amplitude = 2*abs(np.dot(y*window, np.exp(-2j*np.pi*image*t)))/window.sum()
    assert amplitude < 2e-6


@pytest.mark.parametrize("frequency", [1000, 8000, 18000])
def test_capture_reconstruction_preserves_known_waveform(frequency):
    rate = 48000
    x = 0.3*np.sin(2*np.pi*frequency*np.arange(rate)/rate)
    t = (np.arange(1000, 43000)+0.37)/44100.952
    expected = 0.3*np.sin(2*np.pi*frequency*t)
    y = reconstruct_capture(x, rate, t)
    assert np.linalg.norm(y-expected)/np.linalg.norm(expected) < 0.0025


def test_capture_reconstruction_rejects_out_of_recording_times():
    with pytest.raises(ValueError, match="beyond"):
        reconstruct_capture(np.zeros(480), 48000, [1.0])
