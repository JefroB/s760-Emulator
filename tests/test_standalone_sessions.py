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


def test_recovery_preserves_manual_save_and_dirty_media(session):
    session.input(message('SAVE_SESSION'))
    session.runtime.dirty = True
    assert session.save_recovery()['available']
    assert session.recovery_path.read_bytes() == b'checkpoint'
    assert session.session_path.read_bytes() == b'checkpoint'
    assert session.runtime.dirty and session.runtime.state == 'running'


def test_failed_recovery_preserves_previous_archive_and_running_state(session):
    session.save_recovery()
    def fail(_): raise OSError('Disk full')
    session.runtime.save_checkpoint = fail
    with pytest.raises(OSError, match='Disk full'):session.save_recovery()
    assert session.recovery_path.read_bytes() == b'checkpoint'
    assert session.runtime.state == 'running'
    assert session.prepare_close() is False


def test_recovery_restore_after_child_crash(session):
    session.save_recovery()
    session.runtime.alive = False
    assert session.input(message('RESTORE_RECOVERY', discard=True))['type'] == 'RECOVERY_RESTORED'
    assert session.runtime.state == 'running'


def test_restart_does_not_autosave_empty_boot_over_previous_recovery(session):
    session.save_recovery();saved=session.recovery_path.read_bytes()
    session.input(message('RESTART_RUNTIME',discard=True))
    assert session.recovery_pending
    session.next_recovery=0;session.firmware_status={'booted':True};session.automatic_recovery()
    assert session.recovery_path.read_bytes()==saved


def test_explicit_quit_keeps_prior_recovery_without_saving_dirty_memory(session):
    session.save_recovery();saved=session.recovery_path.read_bytes()
    session.runtime.dirty=True
    assert session.input(message('QUIT_WITHOUT_RECOVERY',discard=True))['type']=='CLOSING'
    assert session.prepare_close() is True and session.stop.is_set()
    assert session.recovery_path.read_bytes()==saved
    with pytest.raises(ValueError):standalone.validate_input(message('QUIT_WITHOUT_RECOVERY'))


def test_existing_recovery_is_not_overwritten_on_startup(session):
    session.recovery_path.parent.mkdir(exist_ok=True)
    session.recovery_path.write_bytes(b'old')
    other = standalone.StandaloneSession(session.runtime, session.media_dir)
    assert other.recovery_pending
    assert other.prepare_close() is False
    assert other.recovery_path.read_bytes() == b'old'
    other.input(message('START_RECOVERY', discard=True))
    assert not other.recovery_pending
    assert other.recovery_path.read_bytes() == b'checkpoint'


def test_busy_recovery_refuses_without_pausing_or_clearing_dirty(session):
    session.runtime.busy = True
    session.runtime.dirty = True
    with pytest.raises(RuntimeError, match='busy'):session.save_recovery()
    assert 'pause' not in session.runtime.calls
    assert session.runtime.dirty


def test_automatic_recovery_obeys_deadline_and_boot_readiness(session, monkeypatch):
    monkeypatch.setattr(standalone.time, 'monotonic', lambda:100)
    session.next_recovery=101
    session.firmware_status={'booted':True}
    session.automatic_recovery();assert not session.recovery_path.exists()
    session.next_recovery=99;session.firmware_status={'booted':False}
    session.automatic_recovery();assert not session.recovery_path.exists()
    session.firmware_status={'booted':True};session.automatic_recovery()
    assert session.recovery_path.is_file() and session.next_recovery==160


def test_failed_new_history_preserves_pending_choice(session):
    session.recovery_pending=True
    session.recovery_path.parent.mkdir(exist_ok=True);session.recovery_path.write_bytes(b'old')
    def fail(_):raise OSError('Disk full')
    session.runtime.save_checkpoint=fail
    with pytest.raises(OSError):session.input(message('START_RECOVERY',discard=True))
    assert session.recovery_pending and session.recovery_path.read_bytes()==b'old'


@pytest.mark.parametrize('kind,payload', [('RESTORE_RECOVERY',{}),('START_RECOVERY',{}),
    ('RESTORE_RECOVERY',{'discard':True,'path':'x'}),('SAVE_RECOVERY',{'path':'x'})])
def test_recovery_commands_require_fixed_paths_and_explicit_replacement(kind,payload):
    with pytest.raises(ValueError):standalone.validate_input(message(kind,**payload))


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


def test_restore_after_failed_start_does_not_require_source_sample_disk(session):
    from s760_runtime import RuntimeConfig
    session.input(message('SAVE_SESSION'))
    session.runtime.alive = False
    session.startup_error = 'Source sample disk is missing'
    session.runtime.config = RuntimeConfig(Path('mame'), Path('boot'), Path('system'),
                                           session.session_path.parents[1], Path('missing-sample.img'))
    original_start = session.runtime.start
    def start():
        assert session.runtime.config.sample_disk is None
        original_start()
    session.runtime.start = start
    assert session.input(message('RESTORE_SESSION', discard=True))['type'] == 'SESSION_RESTORED'
    assert session.startup_error is None


def test_eject_reports_success_only_after_controller_acknowledgement(session):
    session.runtime.eject_media = lambda: {'inserted': False}
    assert session.input(message('EJECT_DISK')) == {'type': 'MEDIA_EJECTED'}
    def fail(): raise RuntimeError('Disk is busy')
    session.runtime.eject_media = fail
    with pytest.raises(RuntimeError, match='busy'): session.input(message('EJECT_DISK'))


def test_eject_accepts_no_client_paths():
    with pytest.raises(ValueError): standalone.validate_input(message('EJECT_DISK', path='x'))


def test_media_status_preserves_pause_and_reports_native_protection(session):
    session.runtime.state = 'paused'
    session.runtime.media_status = lambda: {'inserted': True, 'writeProtected': True}
    assert session.input(message('MEDIA_STATUS'))['mediaStatus']['writeProtected'] is True
    assert session.runtime.state == 'paused'


def test_protection_does_not_report_success_when_controller_rejects(session):
    def reject(enabled): raise RuntimeError('Floppy controller is busy')
    session.runtime.set_media_write_protect = reject
    with pytest.raises(RuntimeError, match='busy'):
        session.input(message('MEDIA_WRITE_PROTECT', enabled=True))


@pytest.mark.parametrize('payload', [{}, {'enabled':1}, {'enabled':'true'}, {'enabled':True,'path':'x'}])
def test_write_protection_rejects_invalid_payloads(payload):
    with pytest.raises(ValueError): standalone.validate_input(message('MEDIA_WRITE_PROTECT', **payload))


@pytest.mark.parametrize('kind,payload', [('SAVE_SESSION', {'path':'x'}), ('RESTORE_SESSION', {}), ('RESTORE_SESSION', {'discard':False}), ('RESTORE_SESSION', {'discard':True,'path':'x'})])
def test_session_commands_reject_untrusted_paths_and_missing_confirmation(kind,payload):
    with pytest.raises(ValueError): standalone.validate_input(message(kind,**payload))
