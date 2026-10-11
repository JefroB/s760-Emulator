"""Checkpoint archive validation; native replay is a separate acceptance runner."""
import hashlib
import json
from pathlib import Path
import struct
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from s760_runtime import NativeRuntime, RuntimeConfig


def client(tmp_path, monkeypatch):
    runtime = NativeRuntime(RuntimeConfig(Path('mame'), Path('boot'), Path('system'), tmp_path))
    monkeypatch.setattr(runtime, '_checkpoint_identity', lambda: {'test': 'identity'})
    return runtime


@pytest.mark.parametrize('change', ['magic', 'manifest_size', 'version', 'identity', 'bytes', 'sha256', 'truncated'])
def test_bad_checkpoint_never_calls_native(tmp_path, monkeypatch, change):
    runtime = client(tmp_path, monkeypatch)
    def unexpected(*args, **kwargs):
        pytest.fail('Invalid archive reached native state mutation')
    monkeypatch.setattr(runtime, 'request', unexpected)
    blob = b'native snapshot'
    meta = {'version': 2, 'identity': {'test': 'identity'}, 'bytes': len(blob),
            'sha256': hashlib.sha256(blob).hexdigest()}
    if change in meta: meta[change] = 'wrong'
    encoded = json.dumps(meta).encode()
    archive = b'S760CKP2'+struct.pack('<I', len(encoded))+encoded+blob
    if change == 'magic': archive = b'BADMAGIC'+archive[8:]
    if change == 'manifest_size': archive = archive[:8]+struct.pack('<I', 999999)+archive[12:]
    if change == 'truncated': archive = archive[:-1]
    path = tmp_path/'bad.state'; path.write_bytes(archive)
    with pytest.raises(ValueError): runtime.load_checkpoint(path)
    assert not (tmp_path/'runtime-checkpoint.bin').exists()


def test_failed_save_preserves_existing_checkpoint(tmp_path, monkeypatch):
    runtime = client(tmp_path, monkeypatch)
    path = tmp_path/'existing.state'; path.write_bytes(b'previous checkpoint')
    def fail(*args, **kwargs): raise RuntimeError('Pending MIDI')
    monkeypatch.setattr(runtime, 'request', fail)
    with pytest.raises(RuntimeError): runtime.save_checkpoint(path)
    assert path.read_bytes() == b'previous checkpoint'
    assert not list(tmp_path.glob('*.tmp'))


def test_scsi_identity_tracks_backing_files_and_rejects_changes(tmp_path, monkeypatch):
    import s760_runtime
    for name in ('mame', 'boot', 'system'):
        (tmp_path/name).write_bytes(name.encode())
    (tmp_path/'scripts').mkdir();(tmp_path/'scripts/s760_runtime.lua').write_bytes(b'protocol')
    monkeypatch.setattr(s760_runtime, 'application_root', lambda: tmp_path)
    runtime=NativeRuntime(RuntimeConfig(tmp_path/'mame',tmp_path/'boot',tmp_path/'system',tmp_path))
    media=tmp_path/'roms/SCSI';media.mkdir(parents=True)
    image=media/'HD00_512.img';image.write_bytes(bytes(range(256))*2)
    runtime.scsi_identity=runtime._scsi_identity()
    assert runtime._checkpoint_identity()['scsi']==runtime.scsi_identity
    image.write_bytes(bytes(512))
    with pytest.raises(ValueError,match='changed since'):
        runtime._checkpoint_identity()
    image.unlink()
    with pytest.raises(ValueError,match='changed since'):
        runtime._checkpoint_identity()


def test_scsi_snapshot_profile_bounds_external_images(tmp_path):
    runtime=NativeRuntime(RuntimeConfig(Path('mame'),Path('boot'),Path('system'),tmp_path))
    media=tmp_path/'roms/SCSI';media.mkdir(parents=True)
    with (media/'HD00_512.img').open('wb') as file:
        file.truncate(64*1024*1024+1)
    with pytest.raises(ValueError,match='64 MiB'):
        runtime._scsi_identity()
