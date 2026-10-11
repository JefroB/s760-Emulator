from pathlib import Path
import json
from types import SimpleNamespace
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from s760_runtime import NativeRuntime


def runtime(tmp_path, status='ok', image=b'\x5a' * 737280):
    cfg = SimpleNamespace(state_dir=tmp_path)
    machine = NativeRuntime(cfg)
    machine.acknowledgements = []
    def request(op, **kwargs):
        if kwargs.get('down'):
            if kwargs['name'] == 'Acknowledge Floppy Export':
                machine.acknowledgements.append(True)
                (tmp_path / 'media-status.json').write_text(json.dumps({'ok': True}))
                return {'ok': True}, []
            (tmp_path / 'media-export.img').write_bytes(image)
            (tmp_path / 'media-export.img.status').write_text(status)
        return {'ok': True}, []
    machine.request = request
    return machine


def test_export_persists_exact_controller_bytes(tmp_path):
    machine = runtime(tmp_path)
    target = tmp_path / 'saved.img'
    machine.export_media(target)
    assert target.read_bytes() == b'\x5a' * 737280
    assert machine.acknowledgements == [True]


def test_export_never_overwrites_existing_library_file(tmp_path):
    machine = runtime(tmp_path)
    target = tmp_path / 'original.img'
    target.write_bytes(b'original')
    with pytest.raises(FileExistsError):
        machine.export_media(target)
    assert target.read_bytes() == b'original'


@pytest.mark.parametrize('status,image', [('Floppy controller is busy', b'x' * 737280), ('ok', b'partial')], ids=['busy', 'truncated'])
def test_failed_export_leaves_no_destination(tmp_path, status, image):
    machine = runtime(tmp_path, status, image)
    with pytest.raises((RuntimeError, ValueError)):
        machine.export_media(tmp_path / 'failed.img')
    assert not (tmp_path / 'failed.img').exists()


def test_export_commit_failure_preserves_previous_media(tmp_path, monkeypatch):
    import s760_runtime
    machine = runtime(tmp_path)
    def fail(*_): raise OSError('Read-only destination')
    monkeypatch.setattr(s760_runtime.os, 'link', fail)
    with pytest.raises(OSError): machine.export_media(tmp_path / 'readonly.img')
    assert not (tmp_path / 'readonly.img').exists()
    assert not list(tmp_path.glob('*.pending'))
    assert machine.acknowledgements == []
