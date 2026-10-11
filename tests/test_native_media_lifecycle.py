import json
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from s760_runtime import NativeRuntime


def machine(tmp_path, *, dirty=False, busy=False, reject_insert=False):
    r = NativeRuntime(SimpleNamespace(state_dir=tmp_path))
    state = {'ok': True, 'inserted': True, 'dirty': dirty, 'busy': busy, 'generation': 1, 'revision': 1 if dirty else 0}
    def request(op, **p):
        if not p.get('down'): return {}, []
        result = dict(state)
        name = p['name']
        if name in ('Insert Sample Floppy', 'Eject Sample Floppy'):
            if busy or dirty or reject_insert:
                result.update(ok=False, error='Media change rejected')
            else:
                state['inserted'] = name == 'Insert Sample Floppy'
                result = dict(state)
        (tmp_path / 'media-status.json').write_text(json.dumps(result))
        return {}, []
    r.request = request
    return r


@pytest.mark.parametrize('flag', ['dirty', 'busy'])
def test_protected_insert_keeps_staged_media(tmp_path, flag):
    r = machine(tmp_path, **{flag: True})
    slot = tmp_path / 'inserted-floppy.img'
    slot.write_bytes(b'current')
    source = tmp_path / 'library.img'; source.write_bytes(b'x' * 737280)
    with pytest.raises(RuntimeError): r.insert_media(source)
    assert slot.read_bytes() == b'current'
    assert source.read_bytes() == b'x' * 737280


def test_rejected_native_insert_is_not_success(tmp_path):
    r = machine(tmp_path, reject_insert=True)
    source = tmp_path / 'library.img'; source.write_bytes(b'x' * 737280)
    with pytest.raises(RuntimeError, match='rejected'): r.insert_media(source)


def test_eject_returns_native_state(tmp_path):
    r = machine(tmp_path)
    assert r.eject_media()['inserted'] is False


def test_dirty_eject_rejected(tmp_path):
    r = machine(tmp_path, dirty=True)
    with pytest.raises(RuntimeError): r.eject_media()


def test_invalid_disk_never_reaches_controller(tmp_path):
    r = machine(tmp_path)
    source = tmp_path / 'invalid.img'; source.write_bytes(b'bad')
    with pytest.raises(ValueError): r.insert_media(source)
    assert not (tmp_path / 'media-status.json').exists()
