"""The downloadable ZIP must retain empty portable ROM/media directories."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile


def test_empty_media_directories_survive_acceptance_zip(tmp_path):
    package = tmp_path / 'package'
    package.mkdir()
    (package / 'payload.txt').write_bytes(b'fixture')
    for name in ('BOOT', 'System', 'FDD', 'SCSI'):
        (package / 'roms' / name).mkdir(parents=True)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'files': {'payload.txt': {
        'bytes': 7, 'sha256': hashlib.sha256(b'fixture').hexdigest()}}}))
    output = tmp_path / 'Acceptance kit'
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(root / 'scripts/prepare_standalone_acceptance_kit.py'),
                             '--package', str(package), '--manifest', str(manifest), '--output', str(output)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    with zipfile.ZipFile(output.with_suffix('.zip')) as archive:
        for name in ('BOOT', 'System', 'FDD', 'SCSI'):
            assert archive.getinfo(f'Acceptance kit/S760Studio/roms/{name}/').is_dir()
