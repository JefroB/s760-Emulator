"""Captured PCM frame positions, not status timestamps, own WAV alignment."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_modulation_application import render_with_origin


class Capture:
    def __init__(self, change=None):
        self.position = 0
        self.change = change

    def render_audio(self, frames):
        meta = dict(frames=frames, rate=44100, channels=2, dropped_frames=0,
                    first_sample=500+self.position, stream_first_sample=3500659+self.position,
                    stream_contiguous=True)
        if self.change:
            self.change(meta, self.position)
        self.position += frames
        return meta, bytes(frames*8)


def test_observed_origin_retains_the_reported_881_frame_offset():
    pcm, origin = render_with_origin(Capture(), 9000, block_frames=4096)
    assert len(pcm) == 9000 * 8
    # The archived exact-replay source starts at global stream frame 3508142.
    # Its WAV index is 7483, whereas the old status-origin calculation gave 6602.
    assert 3508142 - origin['stream_first_sample'] == 7483
    assert 7483 - 6602 == 881
    assert [b['wav_frame'] for b in origin['blocks']] == [0, 4096, 8192]
    assert origin['capture_first_sample'] == 500


@pytest.mark.parametrize('change', [
    lambda m, p: m.pop('stream_first_sample'),
    lambda m, p: m.update(stream_contiguous=False),
    lambda m, p: m.update(stream_first_sample=True),
    lambda m, p: m.update(stream_first_sample=m['stream_first_sample'] + (1 if p else 0)),
    lambda m, p: m.update(first_sample=m['first_sample'] + (1 if p else 0)),
    lambda m, p: m.update(dropped_frames=1),
])
def test_unqualified_or_discontinuous_origin_is_rejected(change):
    with pytest.raises(ValueError, match='PCM'):
        render_with_origin(Capture(change), 9000)
