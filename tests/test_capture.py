import ctypes
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import s760_capture as capture


class Device:
    def __init__(self):
        self.headers = []
        self.closed = 0

    def waveInOpen(self, handle, *args):
        if handle is not None:
            handle._obj.value = 123
        return 0

    def waveInPrepareHeader(self, handle, header, size):
        self.headers.append(header._obj)
        header._obj.flags = 2
        return 0

    def waveInAddBuffer(self, handle, header, size):
        header._obj.flags = 2
        return 0

    def waveInStart(self, handle): return 0
    def waveInReset(self, handle): return 0
    def waveInUnprepareHeader(self, *args): return 0

    def waveInClose(self, handle):
        self.closed += 1
        return 0


@pytest.fixture
def recorder(monkeypatch):
    device = Device()
    monkeypatch.setattr(capture, 'api', lambda: device)
    monkeypatch.setattr(capture, 'devices', lambda: [{'id': 'fixture', 'index': 0, 'name': 'Fixture'}])
    source = capture.WaveInput('fixture')
    yield source, device
    source.close()


def test_capture_keeps_stereo_bytes_and_recycles_only_completed_buffers(recorder):
    source, device = recorder
    expected = b'\x00\x80\xff\x7f\xff\xff\x01\x00'
    header = device.headers[0]
    ctypes.memmove(header.data, expected, len(expected))
    header.recorded = len(expected)
    header.flags |= 1
    assert source.read() == [expected]
    assert source.status()['receivedFrames'] == 2
    assert source.read() == []
    assert len(source.buffers) == 8 and all(len(b) == 8192 for b in source.buffers)


def test_capture_rejects_partial_frames(recorder):
    source, device = recorder
    device.headers[0].recorded = 3
    device.headers[0].flags |= 1
    with pytest.raises(OSError, match='incomplete stereo'):
        source.read()


def test_capture_timeout_is_visible_and_close_is_idempotent(recorder):
    source, device = recorder
    source.last_buffer -= 3
    with pytest.raises(OSError, match='stopped delivering'):
        source.read()
    source.close(); source.close()
    assert device.closed == 1


def test_capture_missing_device_rejects_before_open(monkeypatch):
    monkeypatch.setattr(capture, 'devices', lambda: [])
    with pytest.raises(ValueError, match='unavailable'):
        capture.WaveInput('missing')
