"""Windows download trust/extraction boundaries for the frozen acceptance helper."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'artifacts/standalone/install-acceptance.ps1'
PIN = 'b1dd036c9331058fb2db0dde75d038e985fc75d5919c19040766460f5cdb08f9'
pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows attachment metadata and PowerShell')


def run_script(script, *args):
    # A parent PowerShell 7 module path hides Windows PowerShell 5.1 modules.
    env = {key: value for key, value in os.environ.items() if key.upper() != 'PSMODULEPATH'}
    return subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                           '-File', str(script), *map(str, args)], capture_output=True,
                          text=True, timeout=60, env=env)


def test_untrusted_zip_is_rejected_without_removing_download_mark(tmp_path):
    archive = tmp_path / 'untrusted.zip'
    archive.write_bytes(b'not the frozen archive')
    Path(str(archive) + ':Zone.Identifier').write_text('[ZoneTransfer]\nZoneId=3\n')
    destination = tmp_path / 'must not exist'
    result = run_script(SCRIPT, '-Archive', archive, '-Destination', destination)
    assert result.returncode != 0
    assert 'checksum mismatch' in result.stderr
    assert not destination.exists()
    assert 'ZoneId=3' in Path(str(archive) + ':Zone.Identifier').read_text()


@pytest.mark.parametrize('bad_manifest', [False, True])
def test_verified_fixture_extracts_or_rejects_manifest_mismatch(tmp_path, bad_manifest):
    payload = b'synthetic package; no proprietary firmware'
    digest = hashlib.sha256(payload).hexdigest()
    manifest = {'files': {'payload.txt': {'sha256': '0' * 64 if bad_manifest else digest}}}
    archive = tmp_path / 'fixture.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('Fixture kit/PACKAGE-MANIFEST.json', json.dumps(manifest))
        z.writestr('Fixture kit/S760Studio/payload.txt', payload)
    Path(str(archive) + ':Zone.Identifier').write_text('[ZoneTransfer]\nZoneId=3\n')
    # Pin the invented fixture only in a temporary copy; production pin is fixed.
    script = tmp_path / 'installer.ps1'
    script.write_text(SCRIPT.read_text(encoding='utf-8').replace(
        PIN, hashlib.sha256(archive.read_bytes()).hexdigest()), encoding='utf-8')
    destination = tmp_path / 'fresh extraction'
    result = run_script(script, '-Archive', archive, '-Destination', destination)
    if bad_manifest:
        assert result.returncode != 0
        assert 'Package file mismatch' in result.stderr
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert (destination / 'Fixture kit/S760Studio/payload.txt').read_bytes() == payload
        assert not Path(str(archive) + ':Zone.Identifier').exists()
        again = run_script(script, '-Archive', archive, '-Destination', destination)
        assert again.returncode != 0 and 'new destination folder' in again.stderr
        assert (destination / 'Fixture kit/S760Studio/payload.txt').read_bytes() == payload
