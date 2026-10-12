from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import s760_standalone as app
from s760_runtime import RuntimeConfig

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
