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


def test_audio_buffer_target_converts_milliseconds_without_changing_pcm_rate(tmp_path):
    config = RuntimeConfig(None, None, None, tmp_path, audio_backend='wasapi', audio_latency_ms=60)
    assert config.audio_arguments() == ['-sound', 'wasapi', '-audio_latency', '3']
    config.sound = False
    assert config.audio_arguments() == ['-sound', 'none', '-audio_latency', '3']


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


@pytest.mark.parametrize('pcm,rate,channels', [
    (b'', 44100, 2), (bytes(3), 44100, 2), (bytes(8196), 44100, 2),
    (bytes(4), 48000, 2), (bytes(4), 44100, 1), (bytes(4), 44100.0, 2),
    ([0, 0], 44100, 2),
], ids=['empty', 'partial', 'oversize', 'rate', 'mono', 'float-rate', 'list'])
def test_input_pcm_rejects_unsupported_blocks_before_transport(pcm, rate, channels):
    from s760_runtime import NativeRuntime
    runtime = NativeRuntime(None)
    runtime.request = lambda *a, **kw: pytest.fail('Invalid input reached transport')
    with pytest.raises(ValueError): runtime.queue_input_pcm(pcm, rate, channels)


def test_input_pcm_preserves_signed_stereo_channel_order():
    from s760_runtime import NativeRuntime
    runtime = NativeRuntime(None)
    def request(op, **values):
        assert op == 'input_audio'
        assert values == {'rate': 44100, 'channels': 2, 'samples': [-32768, 32767, -1, 1]}
        return {'queued': 2, 'underruns': 0}, []
    runtime.request = request
    assert runtime.queue_input_pcm(struct.pack('<hhhh', -32768, 32767, -1, 1))['queued'] == 2

def test_live_duplex_pcm_requests_output_in_same_native_transaction():
    from s760_runtime import NativeRuntime
    runtime=NativeRuntime(None)
    def request(op,**values):
        assert op=='input_audio' and values['live'] is True and values['output'] is True
        return {'queued':1,'underruns':0,'pcm':bytes(8),'audio':{'frames':1}},[]
    runtime.request=request
    assert runtime.queue_input_pcm(bytes(4),live=True,duplex=True)['pcm']==bytes(8)
    with pytest.raises(ValueError,match='requires live'):runtime.queue_input_pcm(bytes(4),duplex=True)

def test_asio_owns_output_and_requires_explicit_driver():
    cfg=RuntimeConfig(None,None,None,None,audio_backend='asio',asio_driver='MOTU')
    assert cfg.audio_arguments()[:2]==['-sound','none']
    cfg.asio_driver=''
    with pytest.raises(ValueError,match='Select an ASIO driver'):cfg.audio_arguments()


def test_device_clock_feedback_is_bounded_before_transport():
    from s760_runtime import NativeRuntime
    runtime=NativeRuntime(None)
    runtime.request=lambda op,**kw: ({'audio':{},'pcm':b'','clock_rate':kw['clock_rate']},[])
    assert runtime.read_audio(clock_rate=1.01)[0]=={}
    for invalid in (True,float('nan'),float('inf'),.9,1.1,'1'):
        with pytest.raises(ValueError):runtime.read_audio(clock_rate=invalid)


def test_windows_output_mapping_is_stereo_escaped_and_resettable(tmp_path):
    import xml.etree.ElementTree as ET
    from s760_runtime import stage_audio_mapping
    cfg=RuntimeConfig(None,None,None,tmp_path,audio_output_device='endpoint&<identity>')
    stage_audio_mapping(cfg)
    root=ET.parse(tmp_path/'cfg/s760.cfg').getroot()
    maps=root.findall('system/mixer/sound_map/channel_mapping')
    # MAME audio_info::node_info::name() prefixes render endpoint IDs with o:.
    assert [m.get('node') for m in maps]==['o:endpoint&<identity>']*2
    assert [m.get('node_channel') for m in maps]==['0','1']
    assert cfg.audio_arguments()[:2]==['-sound','wasapi']
    cfg.audio_output_device='';stage_audio_mapping(cfg)
    assert not ET.parse(tmp_path/'cfg/s760.cfg').findall('system/mixer/sound_map')


def test_binary_input_keeps_newlines_nuls_and_signed_stereo_bytes():
    from s760_runtime import NativeRuntime
    runtime=NativeRuntime(None)
    pcm=b'\x0a\x00\x00\x80\xff\x7f\x0a\x0a'
    def request(op,**kwargs):
        assert op=='input_audio_binary'
        assert kwargs=={'rate':44100,'channels':2,'frames':2,'_pcm':pcm,'live':True}
        return {'queued':2},[]
    runtime.request=request
    assert runtime.queue_input_pcm(pcm,live=True,binary=True)=={'queued':2}


def test_malformed_binary_frame_never_reaches_a_socket():
    from s760_runtime import NativeRuntime
    runtime=NativeRuntime(None)
    for kwargs in ({'frames':1},{'frames':2,'_pcm':bytes(4)},{'frames':True,'_pcm':bytes(4)}):
        with pytest.raises(ValueError):runtime.request('input_audio_binary',**kwargs)



def test_experimental_input_profile_is_bound_to_checkpoint_identity(tmp_path):
    from s760_runtime import NativeRuntime
    fixture = tmp_path / 'identity.bin'
    fixture.write_bytes(b'identity fixture')
    config = RuntimeConfig(fixture, fixture, fixture, tmp_path)
    runtime = NativeRuntime(config)
    disabled = runtime._checkpoint_identity()
    assert 'experimental_adc' not in disabled
    config.experimental_adc = True
    enabled = runtime._checkpoint_identity()
    assert enabled.pop('experimental_adc') == 'pcm16-stereo-44100-v1'
    assert enabled == disabled
