import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import s760_readiness as readiness

def test_connection_is_not_boot_and_timeout_does_not_become_ready(monkeypatch):
    now=[0.0]; monitor=readiness.FirmwareReadiness(clock=lambda:now[0])
    assert monitor.observe(b'',0)['state']=='booting'
    now[0]=61
    assert monitor.observe(b'',1)['state']=='timeout'

def test_boot_load_and_idle_are_distinct_and_unknown_is_not_success(monkeypatch):
    monkeypatch.setattr(readiness,'labels',lambda frame:frame)
    monitor=readiness.FirmwareReadiness()
    assert monitor.observe({'perform'},1)['state']=='ready'
    assert monitor.observe({'disk','load'},2)['state']=='loading'
    assert monitor.observe({'disk','working'},3)['state']=='loading'
    assert monitor.observe(set(),4)['state']=='unknown'
    assert monitor.observe({'disk','idle'},5)['state']=='disk_ready'

def test_unsupported_profile_and_stalled_clock(monkeypatch):
    now=[0.0]; monitor=readiness.FirmwareReadiness(False,clock=lambda:now[0])
    assert monitor.observe(b'',0)['state']=='unknown'
    now[0]=16
    assert monitor.observe(b'',0)['state']=='stalled'
    assert monitor.observe(b'',0,paused=True)['state']=='unknown'

def test_load_timeout_and_restart_clear_observation(monkeypatch):
    monkeypatch.setattr(readiness,'labels',lambda frame:frame)
    now=[0.0]; monitor=readiness.FirmwareReadiness(clock=lambda:now[0])
    assert monitor.observe({'disk','load'},0)['state']=='loading'
    now[0]=121
    assert monitor.observe({'disk','load'},1)['state']=='timeout'
    replacement=readiness.FirmwareReadiness(clock=lambda:now[0])
    assert replacement.observe(set(),0)['state']=='booting'

def test_restart_requires_confirmation_and_protects_dirty_media(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    import s760_standalone as standalone
    import pytest
    monkeypatch.setattr(standalone,'midi_inputs',lambda _: [])
    r=SimpleNamespace(config=SimpleNamespace(executable='mame'),process=Mock(),close=Mock(),start=Mock(),media_status=Mock(return_value={'dirty':True,'busy':False}))
    r.process.poll.return_value=None
    session=standalone.StandaloneSession(r,tmp_path)
    with pytest.raises(ValueError): session.input({'type':'RESTART_RUNTIME','payload':{}})
    with pytest.raises(RuntimeError): session.input({'type':'RESTART_RUNTIME','payload':{'discard':True}})
    r.close.assert_not_called()
    r.media_status.return_value={'dirty':False,'busy':False}
    assert session.input({'type':'RESTART_RUNTIME','payload':{'discard':True}})['state']=='booting'
    r.close.assert_called_once();r.start.assert_called_once()

def test_dead_child_restart_does_not_require_a_dead_transport(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    import s760_standalone as standalone
    monkeypatch.setattr(standalone,'midi_inputs',lambda _: [])
    r=SimpleNamespace(config=SimpleNamespace(executable='mame'),process=Mock(),close=Mock(),start=Mock(),media_status=Mock())
    r.process.poll.return_value=1
    session=standalone.StandaloneSession(r,tmp_path)
    assert session.input({'type':'RESTART_RUNTIME','payload':{'discard':True}})['state']=='booting'
    r.media_status.assert_not_called()

def test_restart_confirmation_is_literal_true():
    import pytest
    from s760_standalone import validate_input
    for payload in ({}, {'discard':False}, {'discard':1}, {'discard':'yes'}, {'discard':True,'extra':True}):
        with pytest.raises(ValueError): validate_input({'type':'RESTART_RUNTIME','payload':payload})
