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


@pytest.mark.parametrize('operation', ['fsync', 'replace'])
def test_publication_io_failure_retains_previous_archive_and_removes_pending(tmp_path, monkeypatch, operation):
    import s760_runtime
    runtime = client(tmp_path, monkeypatch)
    destination = tmp_path/'recovery.s760state'
    previous = b'previous durable archive'
    destination.write_bytes(previous)
    blob = b'new native checkpoint bytes'
    (tmp_path/'runtime-checkpoint.bin').write_bytes(blob)
    monkeypatch.setattr(runtime, 'request', lambda *args: ({'bytes': len(blob)}, []))
    def fail(*args):
        raise OSError('Injected publication '+operation+' failure')
    monkeypatch.setattr(s760_runtime.os, operation, fail)
    with pytest.raises(OSError, match='publication '+operation):
        runtime.save_checkpoint(destination)
    assert destination.read_bytes() == previous
    assert not list(tmp_path.glob('recovery.s760state.*.tmp'))


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


def test_diagnostic_combined_audio_cannot_share_normal_checkpoint_identity(tmp_path, monkeypatch):
    import s760_runtime
    for name in ('mame', 'boot', 'system'):
        (tmp_path/name).write_bytes(name.encode())
    (tmp_path/'scripts').mkdir(); (tmp_path/'scripts/s760_runtime.lua').write_bytes(b'protocol')
    monkeypatch.setattr(s760_runtime, 'application_root', lambda: tmp_path)
    config = RuntimeConfig(tmp_path/'mame', tmp_path/'boot', tmp_path/'system', tmp_path)
    runtime = NativeRuntime(config)
    normal = runtime._checkpoint_identity()
    assert normal['audio_profile'] == 'native-stereo-filter-interpolation-44100-v2'
    assert 'diagnostic_combined_audio' not in normal
    config.diagnostic_combined_audio = True
    diagnostic = runtime._checkpoint_identity()
    assert diagnostic != normal
    assert diagnostic.pop('diagnostic_combined_audio') == 'stereo-filter-44100-v1'
    assert diagnostic == normal


def test_scsi_snapshot_profile_bounds_external_images(tmp_path):
    runtime=NativeRuntime(RuntimeConfig(Path('mame'),Path('boot'),Path('system'),tmp_path))
    media=tmp_path/'roms/SCSI';media.mkdir(parents=True)
    with (media/'HD00_512.img').open('wb') as file:
        file.truncate(64*1024*1024+1)
    with pytest.raises(ValueError,match='64 MiB'):
        runtime._scsi_identity()


@pytest.mark.parametrize('field,label', [('mame','MAME build'), ('boot','boot ROM'),
    ('system','system disk'), ('protocol','runtime protocol'), ('scsi','SCSI backing media')])
def test_checkpoint_mismatch_identifies_repair_action(tmp_path, monkeypatch, field, label):
    runtime = client(tmp_path, monkeypatch)
    identities = {key:'original' for key in ('mame','boot','system','protocol','scsi')}
    monkeypatch.setattr(runtime, '_checkpoint_identity', lambda: {**identities, field:'changed'})
    blob = b'snapshot'
    meta = {'version':2,'identity':identities,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}
    encoded = json.dumps(meta).encode()
    path = tmp_path/'mismatch.state'
    path.write_bytes(b'S760CKP2'+struct.pack('<I',len(encoded))+encoded+blob)
    with pytest.raises(ValueError, match=label): runtime.validate_checkpoint(path)
    assert not (tmp_path/'runtime-checkpoint.bin').exists()


def test_checkpoint_missing_slot_has_recovery_message(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match='No saved session'):
        client(tmp_path, monkeypatch).validate_checkpoint(tmp_path/'missing.state')


def test_version_one_session_reports_no_migration(tmp_path, monkeypatch):
    path = tmp_path/'old.state'; path.write_bytes(b'S760CKP1' + bytes(4))
    with pytest.raises(ValueError, match='migration is not available'):
        client(tmp_path, monkeypatch).validate_checkpoint(path)

def test_large_readonly_cd_is_stream_hashed_separately_from_writable_limit(tmp_path,monkeypatch):
    runtime=NativeRuntime(RuntimeConfig(Path('mame'),Path('boot'),Path('system'),tmp_path))
    folder=tmp_path/'roms/SCSI';folder.mkdir(parents=True);cd=folder/'CD10_2048.iso'
    with cd.open('wb') as f:f.truncate(65*1024*1024)
    original=Path.read_bytes
    def bounded(path):
        if path==cd:pytest.fail('Large CD read into a temporary bytes object')
        return original(path)
    monkeypatch.setattr(Path,'read_bytes',bounded)
    before=runtime._scsi_identity()
    with cd.open('r+b') as f:f.seek(-1,2);f.write(b'1')
    assert before!=runtime._scsi_identity()
