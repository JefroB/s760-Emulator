import ctypes as C
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import s760_asio as asio
from s760_runtime import RuntimeConfig


@pytest.fixture
def host(monkeypatch):
    state=SimpleNamespace(active=1,closed=0,blocks=1,played=0,queued=0)
    def status(handle,result):
        result._obj.active=state.active;result._obj.rate=44100;result._obj.captured=2048
        result._obj.played=state.played;result._obj.output_queued=state.queued
        return 0
    def read(handle,buffer,frames):
        assert frames==2048
        if not state.blocks:return 0
        state.blocks-=1;buffer[0]=-32768;buffer[1]=32767
        return 2048
    def close(_):state.closed+=1
    d=SimpleNamespace(s760_asio_open=lambda *a:123,s760_asio_close=close,
        s760_asio_write=lambda handle,pcm,frames:frames//2,s760_asio_read=read,
        s760_asio_status=status,s760_asio_error=lambda:b'fixture driver error')
    monkeypatch.setattr(asio,'api',lambda:d)
    h=asio.AsioHost(RuntimeConfig(None,None,None,None,audio_backend='asio',asio_driver='Fixture',asio_input_channel=1))
    yield h,state
    h.close()


def test_asio_input_keeps_signed_pcm_and_bounds_worker_blocks(host):
    h,_=host;blocks=h.read()
    assert len(blocks)==1 and len(blocks[0])==8192
    assert blocks[0][:4]==b'\x00\x80\xff\x7f'


def test_asio_output_reports_every_unaccepted_frame(host):
    h,_=host;h.write(bytes(32))
    assert h.status()['outputDiscardedFrames']==2
    with pytest.raises(ValueError):h.write(bytes(7))


def test_asio_driver_stop_is_visible_and_close_is_idempotent(host):
    h,state=host;state.active=0
    with pytest.raises(OSError,match='driver stopped'):h.status()
    h.close();h.close();assert state.closed==1


def test_asio_open_error_does_not_fall_back(monkeypatch):
    d=SimpleNamespace(s760_asio_open=lambda *a:None,s760_asio_error=lambda:b'unsupported buffer')
    monkeypatch.setattr(asio,'api',lambda:d)
    with pytest.raises(OSError,match='unsupported buffer'):asio.AsioHost(RuntimeConfig(None,None,None,None))


def test_output_only_driver_stall_is_visible_even_if_driver_reports_active(host,monkeypatch):
    h,state=host;h.config.asio_input_channel=0
    clock=[100.0];monkeypatch.setattr(asio.time,'monotonic',lambda:clock[0])
    state.queued=8192;state.played=512
    h.status()
    clock[0]+=2.1
    with pytest.raises(OSError,match='stopped consuming output PCM'):h.status()


def test_empty_or_progressing_output_does_not_report_stall(host,monkeypatch):
    h,state=host;h.config.asio_input_channel=0
    clock=[100.0];monkeypatch.setattr(asio.time,'monotonic',lambda:clock[0])
    h.status();clock[0]+=3;h.status()
    state.queued=8192;state.played=512;h.status()
    clock[0]+=3;state.played+=512;h.status()


def test_low_output_queue_requests_an_early_native_drain(host,monkeypatch):
    h,state=host
    monkeypatch.setattr(asio.time,'monotonic',lambda:100.0)
    h.next_output=100.08;state.queued=2048
    h.status()
    assert h.next_output<=100.0


def test_device_clock_feedback_replenishes_low_queue_and_bounds_pacing(host):
    h,state=host
    state.queued=0;h.status();assert 1<h.clock_rate<=1.03
    state.queued=65536;h.status();assert .97<=h.clock_rate<1
    state.queued=16384;h.status();assert h.clock_rate==1
