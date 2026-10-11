"""Band-limited reconstruction of recorded audio for clock-aligned comparisons.

Requires NumPy and SciPy. Keep this measurement operation separate from the
emulator's interpolation: a short reconstruction filter can introduce images
that alias into the comparison band and falsely look like hardware DSP error.
"""
import numpy as np
from scipy import signal


def reconstruct_capture(samples, sample_rate, times):
    """Evaluate mono PCM at times in seconds without gain normalization.

    Uses 16x reconstruction with a 256-input-sample Kaiser FIR, followed by
    linear lookup. Intended for the S-760's 100 Hz--18 kHz comparison band
    from 48 kHz captures. This is not an arbitrary downsampling API: the
    caller must band-limit before decimating below twice the signal bandwidth.
    Exclude the first/last 128 input samples from precision comparisons.
    """
    samples = np.asarray(samples, dtype=np.float64)
    times = np.asarray(times, dtype=np.float64)
    if samples.ndim != 1 or not len(samples) or not np.isfinite(samples).all():
        raise ValueError("samples must be nonempty, finite mono PCM")
    if not np.isfinite(sample_rate) or sample_rate <= 0:
        raise ValueError("sample_rate must be positive and finite")
    if times.ndim != 1 or not np.isfinite(times).all():
        raise ValueError("times must be a finite vector")
    if len(times) and (times.min() < 0 or times.max() > (len(samples)-1)/sample_rate):
        raise ValueError("requested times extend beyond the recording")
    up = 16
    kernel = signal.firwin(256 * up + 1, 1 / up, window=("kaiser", 12))
    reconstructed = signal.resample_poly(samples, up, 1, window=kernel)
    return np.interp(times * sample_rate * up, np.arange(len(reconstructed)), reconstructed)
