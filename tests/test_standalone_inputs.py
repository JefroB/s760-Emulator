import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from s760_standalone import validate_input


@pytest.mark.parametrize('id', ['ALPHA', 'VOLUME'])
def test_native_dials_accept_bounded_signed_steps(id):
    for delta in (-32, -1, 0, 1, 32):
        assert validate_input({'type': 'DIAL_DELTA', 'payload': {'id': id, 'delta': delta}})[0] == 'DIAL_DELTA'


@pytest.mark.parametrize('payload', [
    {'id': 'UNKNOWN', 'delta': 1}, {'id': 'ALPHA', 'delta': True},
    {'id': 'ALPHA', 'delta': 1.5}, {'id': 'VOLUME', 'delta': 33},
    {'id': 'ALPHA', 'delta': -33}, {'id': 'ALPHA'},
])
def test_native_dials_reject_unknown_or_unbounded_input(payload):
    with pytest.raises(ValueError):
        validate_input({'type': 'DIAL_DELTA', 'payload': payload})


def test_missing_midi_backend_keeps_audition_available(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import subprocess
    import s760_standalone as standalone
    def unavailable(_):
        raise subprocess.CalledProcessError(1, 'mame -listmidi')
    monkeypatch.setattr(standalone, 'midi_inputs', unavailable)
    runtime = SimpleNamespace(config=SimpleNamespace(executable='mame',state_dir=tmp_path))
    session = standalone.StandaloneSession(runtime, tmp_path)
    assert session.midi_devices == []
    assert session.midi_warning
    assert not session.stop.is_set()


@pytest.mark.parametrize('payload', [{'x': float('nan'), 'y': 0}, {'x': 0, 'y': 2}, {'x': True, 'y': 0}])
def test_reject_invalid_pointer(payload):
    with pytest.raises(ValueError):
        validate_input({'type': 'MOUSE_MOVE', 'payload': payload})


@pytest.mark.parametrize('message', [None, {}, {'type': 'QUIT', 'payload': {}},
    {'type': 'NOTE_ON', 'payload': {'note': 128, 'velocity': 100}},
    {'type': 'NOTE_ON', 'payload': {'note': 60, 'velocity': 1.5}},
    {'type': 'BUTTON_PRESS', 'payload': {'id': 'GUESSED_BUTTON'}},
    {'type': 'MOUSE_BUTTON', 'payload': {'button': 0, 'down': 1}}])
def test_reject_invalid_control(message):
    with pytest.raises(ValueError):
        validate_input(message)


def test_accept_note_off_and_right_mouse_release():
    assert validate_input({'type': 'NOTE_OFF', 'payload': {'note': 60, 'velocity': 0}})[0] == 'NOTE_OFF'
    assert validate_input({'type': 'MOUSE_BUTTON', 'payload': {'button': 2, 'down': False}})[0] == 'MOUSE_BUTTON'


def test_export_has_no_client_supplied_output_path():
    assert validate_input({'type': 'EXPORT_DISK', 'payload': {}})[0] == 'EXPORT_DISK'
    with pytest.raises(ValueError):
        validate_input({'type': 'EXPORT_DISK', 'payload': {'path': 'library.img'}})



def test_input_level_is_a_bounded_native_rack_dial():
    message = {'type': 'DIAL_DELTA', 'payload': {'id': 'INPUT', 'delta': -20}}
    assert validate_input(message) == ('DIAL_DELTA', message['payload'])
    for delta in (33, -33, True, 0.5):
        with pytest.raises(ValueError):
            validate_input({'type': 'DIAL_DELTA', 'payload': {'id': 'INPUT', 'delta': delta}})
