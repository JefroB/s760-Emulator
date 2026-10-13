from types import SimpleNamespace
import pytest
from test_standalone_configuration import configured


def test_device_failure_pauses_sampler_and_preserves_memory(configured):
    session,_=configured
    calls=[]
    session.runtime.request=lambda op,**kw:(calls.append(op) or ({},[]))
    def lost():raise OSError('fixture device lost')
    session.capture=SimpleNamespace(read=lost,close=lambda:None)
    session.capture_status={'state':'active','outputUnderruns':128,'discardedFrames':2048}
    session.poll_capture()
    assert calls==['pause']
    assert session.capture_status['state']=='failed'
    assert 'paused' in session.capture_status['message']
    assert session.capture_status['outputUnderruns']==128
    assert session.capture_status['discardedFrames']==2048
    assert session.runtime.calls==[]


def test_reopen_audio_resumes_same_machine_without_restart(configured,monkeypatch):
    session,_=configured
    calls=[]
    session.runtime.request=lambda op,**kw:(calls.append(op) or ({},[]))
    session.capture_status={'state':'failed','message':'lost'}
    def opened():
        session.capture=SimpleNamespace(close=lambda:None)
        session.capture_status={'state':'active','message':'reopened'}
    monkeypatch.setattr(session,'start_capture',opened)
    reply=session.input({'type':'REOPEN_AUDIO','payload':{}})
    assert reply['type']=='AUDIO_REOPENED'
    assert calls==['pause','resume']
    assert session.runtime.calls==[]
    assert session.capture_discontinuities==1


def test_failed_audio_reopen_keeps_sampler_paused(configured,monkeypatch):
    session,_=configured
    calls=[]
    session.runtime.request=lambda op,**kw:(calls.append(op) or ({},[]))
    session.capture_status={'state':'failed','message':'lost'}
    monkeypatch.setattr(session,'start_capture',lambda:None)
    with pytest.raises(RuntimeError):session.input({'type':'REOPEN_AUDIO','payload':{}})
    assert calls==['pause']


def test_reopen_preserves_existing_input_and_reprimes_before_resume(configured,monkeypatch):
    session,_=configured
    session.runtime.config.recording_device='fixture input'
    session.capture_status={'state':'failed','message':'lost'}
    calls=[];queued=[4096]
    def request(op,**kw):
        calls.append(op)
        return {'queued':queued[0]},[]
    def queue(pcm,**kw):
        assert 'resume' not in calls
        queued[0]+=len(pcm)//4
        return {'queued':queued[0]}
    session.runtime.request=request
    session.runtime.queue_input_pcm=queue
    def opened():
        session.capture=SimpleNamespace(close=lambda:None,status=lambda:{},read=lambda:[bytes(8192)],discarded_frames=0)
        session.capture_status={'state':'active','message':'reopened'}
    monkeypatch.setattr(session,'start_capture',opened)
    session.reopen_audio()
    assert queued[0]==12288
    assert calls==['pause','input_status','resume']
    assert session.capture_primed
    assert session.runtime.calls==[]
