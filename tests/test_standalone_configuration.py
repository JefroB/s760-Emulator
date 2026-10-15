from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import s760_standalone as app
from s760_runtime import RuntimeConfig


def test_keyboard_preference_defaults_hidden_and_persists_without_runtime_restart(configured):
    session, _ = configured
    assert session.preferences == {'showKeyboard': False}
    response = session.input({'type':'SET_STANDALONE_PREFERENCES','payload':{'showKeyboard':True}})
    assert response == {'type':'STANDALONE_PREFERENCES','preferences':{'showKeyboard':True}}
    assert session.runtime.calls == []
    reopened = app.StandaloneSession(session.runtime, session.media_dir)
    assert reopened.preferences == {'showKeyboard': True}


@pytest.mark.parametrize('payload', [{}, {'showKeyboard':1}, {'showKeyboard':'true'}, {'showKeyboard':True,'path':'file'}])
def test_invalid_keyboard_preferences_reject_before_publication(configured, payload):
    session, _ = configured
    with pytest.raises(ValueError):
        session.input({'type':'SET_STANDALONE_PREFERENCES','payload':payload})
    assert not (session.runtime.config.state_dir/'standalone-ui.json').exists()

@pytest.fixture
def configured(tmp_path,monkeypatch):
    monkeypatch.setattr(app,'midi_inputs',lambda _:[])
    exe=tmp_path/'mame.exe';exe.write_bytes(b'fixture')
    boot=tmp_path/'boot.bin';boot.write_bytes(bytes(32768))
    disk=tmp_path/'system.img';disk.write_bytes(bytes(1474560))
    media=tmp_path/'media';media.mkdir()
    class Runtime:
        config=RuntimeConfig(exe,boot,disk,tmp_path,sound=False)
        process=None
        calls=[]
        dirty=False
        def close(self): self.calls.append('close');self.process=None
        def start(self): self.calls.append('start');self.process=SimpleNamespace(poll=lambda:None)
        def media_status(self):return {'dirty':self.dirty,'busy':False}
    session=app.StandaloneSession(Runtime(),media)
    payload={'bootRom':str(boot),'systemDisk':str(disk),'mediaDirectory':str(media),'sound':False,'discard':True}
    return session,payload

def test_apply_validates_before_stopping_and_persists_only_success(configured):
    session,p=configured
    with pytest.raises(ValueError,match='Boot ROM'):
        session.input({'type':'CONFIGURE_RUNTIME','payload':{**p,'bootRom':'missing'}})
    assert not session.runtime.calls
    response=session.input({'type':'CONFIGURE_RUNTIME','payload':p})
    assert response['type']=='CONFIGURATION_APPLIED'
    assert session.runtime.calls==['close','start']
    assert app.load_settings(session.runtime.config.state_dir)['bootRom']==p['bootRom']

def test_missing_recording_device_preserves_live_runtime(configured, monkeypatch):
    session, payload = configured
    monkeypatch.setattr(app, 'recording_devices', lambda: [])
    with pytest.raises(ValueError, match='unavailable'):
        session.input({'type':'CONFIGURE_RUNTIME','payload':{**payload,'recordingDevice':'missing'}})
    assert not session.runtime.calls

def test_missing_asio_driver_preserves_live_machine(configured,monkeypatch):
    session,payload=configured
    monkeypatch.setattr(app,'asio_devices',lambda:[])
    with pytest.raises(ValueError,match='ASIO driver is unavailable'):
        session.input({'type':'CONFIGURE_RUNTIME','payload':{**payload,'audioBackend':'asio','asioDriver':'missing'}})
    assert not session.runtime.calls

def test_unavailable_asio_channels_reject_before_restart(configured,monkeypatch):
    session,payload=configured
    monkeypatch.setattr(app,'asio_devices',lambda:[{'name':'Fixture','inputs':2,'outputs':2}])
    with pytest.raises(ValueError,match='channel pair is unavailable'):
        session.input({'type':'CONFIGURE_RUNTIME','payload':{**payload,'audioBackend':'asio','asioDriver':'Fixture','asioOutputChannel':3}})
    assert not session.runtime.calls

@pytest.mark.parametrize('settings',[{'asioBufferFrames':123},{'asioOutputChannel':True},{'asioInputChannel':-1},{'asioDriver':'bad\0driver'}])
def test_invalid_asio_payload_preserves_live_machine(configured,settings):
    session,payload=configured
    with pytest.raises(ValueError):session.input({'type':'CONFIGURE_RUNTIME','payload':{**payload,**settings}})
    assert not session.runtime.calls

def test_capture_transaction_reopens_after_checkpoint_failure(configured, monkeypatch):
    session, _ = configured
    calls = []
    session.capture = SimpleNamespace(close=lambda: calls.append('close'))
    monkeypatch.setattr(session, 'start_capture', lambda: calls.append('open'))
    with pytest.raises(OSError, match='fixture'):
        with session.capture_transaction():
            assert session.capture is None
            raise OSError('fixture')
    assert calls == ['close', 'open']
    assert session.capture_discontinuities == 1

def test_live_capture_primes_bounded_fifo_before_delivering(configured):
    session, _ = configured
    delivered = []
    session.runtime.queue_input_pcm = lambda pcm, **kw: delivered.append((pcm,kw)) or {'underruns':0}
    session.capture = SimpleNamespace(read=lambda:[bytes(8192)], status=lambda:{'receivedFrames':2048}, discarded_frames=0)
    for _ in range(3):session.poll_capture()
    assert delivered == []
    session.poll_capture()
    assert len(delivered) == 4
    assert all(kw == {'live':True} for _,kw in delivered)
    assert session.capture_pending == []

def test_apply_requires_confirmation_and_rejects_dirty_runtime(configured):
    session,p=configured
    with pytest.raises(ValueError):session.input({'type':'CONFIGURE_RUNTIME','payload':{**p,'discard':False}})
    session.runtime.start();session.runtime.dirty=True;session.runtime.calls.clear()
    with pytest.raises(RuntimeError,match='Export'):
        session.input({'type':'CONFIGURE_RUNTIME','payload':p})
    assert not session.runtime.calls

def test_failed_start_leaves_configuration_ui_available(configured):
    session,p=configured
    def fail():raise RuntimeError('startup fixture failure')
    session.runtime.start=fail
    with pytest.raises(RuntimeError,match='startup fixture failure'):
        session.input({'type':'CONFIGURE_RUNTIME','payload':p})
    assert session.poll()==[]
    assert session.firmware_status['state']=='configuration'
    assert not (session.runtime.config.state_dir/'settings.json').exists()


def test_failed_reconfiguration_preserves_last_working_settings(configured):
    session,p=configured
    session.input({'type':'CONFIGURE_RUNTIME','payload':p})
    before=(session.runtime.config.state_dir/'settings.json').read_bytes()
    def fail(): raise RuntimeError('failed second launch')
    session.runtime.start=fail
    with pytest.raises(RuntimeError):
        session.input({'type':'CONFIGURE_RUNTIME','payload':{**p,'sound':True}})
    assert (session.runtime.config.state_dir/'settings.json').read_bytes()==before


def test_corrupt_settings_are_reported(tmp_path):
    (tmp_path/'settings.json').write_text('{bad',encoding='utf-8')
    with pytest.raises(ValueError): app.load_settings(tmp_path)


def test_audio_settings_survive_firmware_reconfiguration(configured):
    session, payload = configured
    session.runtime.config.audio_backend = 'wasapi'
    session.runtime.config.audio_latency_ms = 60
    session.input({'type': 'CONFIGURE_RUNTIME', 'payload': payload})
    saved = app.load_settings(session.runtime.config.state_dir)
    assert saved['audioBackend'] == 'wasapi'
    assert saved['audioLatencyMs'] == 60


def test_audio_configuration_readback_can_be_applied_again(configured):
    session, payload = configured
    payload.update(audioBackend='xaudio2', audioLatencyMs=80)
    response = session.input({'type': 'CONFIGURE_RUNTIME', 'payload': payload})
    readback = response['configuration']
    session.input({'type': 'CONFIGURE_RUNTIME', 'payload': {**readback, 'discard': True}})
    assert session.runtime.config.audio_arguments() == ['-sound', 'none', '-audio_latency', '4']


def test_invalid_audio_payload_preserves_live_machine(configured):
    session, payload = configured
    with pytest.raises(ValueError):
        session.input({'type': 'CONFIGURE_RUNTIME', 'payload': {**payload, 'audioLatencyMs': float('inf')}})
    assert not session.runtime.calls


@pytest.mark.parametrize('key,value', [('audioBackend', 'unknown'),
    ('audioLatencyMs', -1), ('audioLatencyMs', 1001),
    ('audioLatencyMs', True), ('audioLatencyMs', float('nan'))])
def test_invalid_saved_audio_settings_are_rejected(configured, key, value):
    import json
    session, payload = configured
    data = {'version': 1, **{k: v for k, v in payload.items() if k != 'discard'}, key: value}
    (session.runtime.config.state_dir / 'settings.json').write_text(json.dumps(data))
    with pytest.raises(ValueError): app.load_settings(session.runtime.config.state_dir)


def test_old_settings_default_to_automatic_audio(configured):
    session, payload = configured
    import json
    data = {'version': 1, **{k: v for k, v in payload.items() if k != 'discard'}}
    (session.runtime.config.state_dir / 'settings.json').write_text(json.dumps(data))
    saved = app.load_settings(session.runtime.config.state_dir)
    assert saved['audioBackend'] == 'auto'
    assert saved['audioLatencyMs'] == 0


def test_missing_windows_output_rejects_before_replacing_machine(configured,monkeypatch):
    session,payload=configured
    monkeypatch.setattr(app,'windows_outputs',lambda:[])
    with pytest.raises(ValueError,match='output endpoint is unavailable'):
        session.input({'type':'CONFIGURE_RUNTIME','payload':{**payload,'audioOutputDevice':'missing'}})
    assert session.runtime.calls==[]

@pytest.mark.parametrize('size',[8,16,32])
def test_wave_memory_configuration_persists(configured,size):
    session,payload=configured
    response=session.input({'type':'CONFIGURE_RUNTIME','payload':{**payload,'waveMemoryMb':size}})
    assert session.runtime.config.wave_memory_mb==size
    assert response['configuration']['waveMemoryMb']==size
    assert app.load_settings(session.runtime.config.state_dir)['waveMemoryMb']==size

@pytest.mark.parametrize('size',[2,64,True,'32'])
def test_invalid_wave_memory_preserves_machine(configured,size):
    session,payload=configured
    with pytest.raises(ValueError,match='memory'):
        session.input({'type':'CONFIGURE_RUNTIME','payload':{**payload,'waveMemoryMb':size}})
    assert not session.runtime.calls
