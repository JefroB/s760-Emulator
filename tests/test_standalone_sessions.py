from types import SimpleNamespace
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import s760_standalone as standalone


@pytest.fixture
def session(tmp_path, monkeypatch):
    monkeypatch.setattr(standalone, 'midi_inputs', lambda _: [])
    class Runtime:
        config = SimpleNamespace(state_dir=tmp_path, executable='mame')
        alive = True
        dirty = False
        busy = False
        state = 'running'
        calls = []
        def __init__(self): self.process = SimpleNamespace(poll=lambda: None if self.alive else 1)
        def request(self, op, **kw):
            self.calls.append(op)
            if op == 'pause': self.state = 'paused'
            if op == 'resume': self.state = 'running'
            return {'state': self.state}, []
        def media_status(self): return {'dirty': self.dirty, 'busy': self.busy}
        def save_checkpoint(self, target): target.write_bytes(b'checkpoint')
        def validate_checkpoint(self, target):
            self.calls.append('validate')
            if target.read_bytes() != b'checkpoint': raise ValueError('Invalid checkpoint')
        def load_checkpoint(self, target): self.calls.append('load')
        def close(self): self.calls.append('close'); self.alive = False
        def start(self): self.calls.append('start'); self.alive = True
    return standalone.StandaloneSession(Runtime(), tmp_path)


def message(kind, **payload): return {'type': kind, 'payload': payload}


def test_save_resumes_and_restore_after_crash(session):
    assert session.input(message('SAVE_SESSION'))['type'] == 'SESSION_SAVED'
    assert session.runtime.state == 'running'
    session.runtime.alive = False
    result = session.input(message('RESTORE_SESSION', discard=True))
    assert result['type'] == 'SESSION_RESTORED'
    assert session.runtime.calls.index('validate') < session.runtime.calls.index('close')
    assert session.runtime.state == 'running'


@pytest.mark.parametrize('flag', ['dirty', 'busy'])
def test_restore_protects_live_media(session, flag):
    session.input(message('SAVE_SESSION'))
    setattr(session.runtime, flag, True)
    with pytest.raises(RuntimeError): session.input(message('RESTORE_SESSION', discard=True))
    assert 'load' not in session.runtime.calls


def test_bad_archive_does_not_stop_live_runtime(session):
    session.input(message('SAVE_SESSION'))
    session.session_path.write_bytes(b'bad')
    with pytest.raises(ValueError): session.input(message('RESTORE_SESSION', discard=True))
    assert 'load' not in session.runtime.calls and 'close' not in session.runtime.calls
    assert session.runtime.state == 'running'


def test_failed_save_preserves_running_state(session, monkeypatch):
    def fail(_): raise RuntimeError('Disconnect external MIDI first')
    monkeypatch.setattr(session.runtime, 'save_checkpoint', fail)
    with pytest.raises(RuntimeError): session.input(message('SAVE_SESSION'))
    assert session.runtime.state == 'running'


@pytest.mark.parametrize('kind,payload', [('SAVE_SESSION', {'path':'x'}), ('RESTORE_SESSION', {}), ('RESTORE_SESSION', {'discard':False}), ('RESTORE_SESSION', {'discard':True,'path':'x'})])
def test_session_commands_reject_untrusted_paths_and_missing_confirmation(kind,payload):
    with pytest.raises(ValueError): standalone.validate_input(message(kind,**payload))
