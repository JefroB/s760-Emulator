"""Transport/colour tests; live-machine checks are in the standalone smoke runner."""
import socket
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from s760_runtime import RuntimeConfig, read_exact, surface_frame


def test_native_crt_channel_order_and_line_doubling():
    # MAME pixels are native little-endian 0xAARRGGBB, not wire RGBA.
    pixels = bytes([0x33, 0x22, 0x11, 0]) * (640 * 240)
    result = surface_frame(0, 640, 240, pixels)
    assert result[:6] == struct.pack('<BHHB', 0, 640, 480, 0)
    assert result[6:] == bytes([0x11, 0x22, 0x33, 255]) * (640 * 480)


def test_lcd_pixels_pack_msb_first():
    pixels = bytearray(160 * 64 * 4)
    pixels[0:4] = bytes([255, 255, 255, 255])
    pixels[7 * 4:8 * 4] = bytes([255, 255, 255, 255])
    result = surface_frame(1, 160, 64, pixels)
    assert result[:7] == struct.pack('<BHHB', 1, 160, 64, 1) + b'\x81'
    assert len(result) == 1286


@pytest.mark.parametrize('surface,w,h,data', [(0, 1, 1, b'1234'), (0, 640, 240, b''), (2, 160, 64, b'')])
def test_invalid_frame_rejected(surface, w, h, data):
    with pytest.raises(ValueError):
        surface_frame(surface, w, h, data)


def test_socket_eof_does_not_spin():
    a, b = socket.socketpair()
    with a, b:
        b.sendall(b'ab')
        b.shutdown(socket.SHUT_WR)
        with pytest.raises(ConnectionError):
            read_exact(a, 3)


def test_missing_firmware_fails_before_spawn(tmp_path):
    config = RuntimeConfig(Path('missing.exe'), Path('missing.bin'), Path('missing.img'), tmp_path)
    with pytest.raises(FileNotFoundError):
        config.validate()


def test_launch_failure_releases_state_directory(tmp_path, monkeypatch):
    import s760_runtime
    executable, boot, disk = (tmp_path / name for name in ('mame.exe', 'boot.bin', 'system.img'))
    executable.write_bytes(b'placeholder')
    boot.write_bytes(b'placeholder')
    disk.write_bytes(bytes(1474560))
    def fail(*args, **kwargs):
        raise OSError('Launch failure fixture')
    monkeypatch.setattr(s760_runtime.subprocess, 'Popen', fail)
    config = RuntimeConfig(executable, boot, disk, tmp_path / 'state')
    for _ in range(2):
        runtime = s760_runtime.NativeRuntime(config)
        with pytest.raises(OSError, match='Launch failure fixture'):
            runtime.start()
        assert runtime.state_lock is None
        assert runtime.process is None


@pytest.mark.parametrize('descriptor', [
    {'frames': -1, 'channels': 2, 'rate': 44100},
    {'frames': 44101, 'channels': 2, 'rate': 44100},
    {'frames': True, 'channels': 2, 'rate': 44100},
    {'frames': 1, 'channels': 1, 'rate': 44100},
    {'frames': 1, 'channels': 2, 'rate': 48000},
])
def test_invalid_audio_descriptor_rejected(descriptor):
    from s760_runtime import audio_payload_size
    with pytest.raises(ValueError): audio_payload_size(descriptor)


def test_native_audio_contract_is_stereo_float32():
    from s760_runtime import audio_payload_size
    assert audio_payload_size({'frames': 735, 'channels': 2, 'rate': 44100}) == 5880
    assert audio_payload_size({'frames': 0, 'channels': 2, 'rate': 44100}) == 0


@pytest.mark.parametrize('frames', [0, -1, 8193, True, 1.5])
def test_render_rejects_bad_counts_before_transport(frames):
    from s760_runtime import NativeRuntime
    runtime = NativeRuntime(None)
    with pytest.raises(ValueError): runtime.render_audio(frames)


def test_render_rejects_short_native_block():
    from s760_runtime import NativeRuntime
    runtime = NativeRuntime(None)
    runtime.request = lambda *a, **kw: ({'audio': {'frames': 2}, 'pcm': bytes(16)}, [])
    with pytest.raises(ValueError, match='Incomplete'): runtime.render_audio(3)
