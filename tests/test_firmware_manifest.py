"""Contract checks use synthetic bytes, not distributed firmware."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('manifest_validator', ROOT / 'scripts/validate_firmware_manifest.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(target):
    manifest = json.loads((ROOT / f'scripts/firmware_manifests/{target}.json').read_text())
    data = bytes(manifest['input']['size'])
    manifest['input']['sha256'] = hashlib.sha256(data).hexdigest()
    return manifest, data


@pytest.mark.parametrize('target', ['os_disk', 'ic15_rom'])
def test_complete_layout(target):
    manifest, data = fixture(target)
    assert module.validate(manifest, data)['layout_bytes_covered'] == len(data)


@pytest.mark.parametrize('fault', ['identity', 'gap', 'overlap', 'mapping', 'entry', 'schema', 'checksum', 'build'])
def test_invalid_contract_rejected(fault):
    manifest, data = fixture('os_disk')
    if fault == 'identity':
        data = b'X' + data[1:]
    elif fault == 'gap':
        manifest['layout'][1]['start'] += 1
    elif fault == 'overlap':
        manifest['layout'][1]['start'] -= 1
    elif fault == 'mapping':
        manifest['entry_points'][0]['fetch_page'] += 1
    elif fault == 'entry':
        manifest['entry_points'][0]['file_offset'] = len(data)
    elif fault == 'schema':
        manifest['schema_version'] = 99
    elif fault == 'checksum':
        manifest['derived_fields'][0]['policy'] = 'guess'
    elif fault == 'build':
        manifest['build_contract']['implemented'] = True
    with pytest.raises(ValueError):
        module.validate(manifest, data)


def test_rom_mirror_mismatch():
    manifest, data = fixture('ic15_rom')
    manifest['entry_points'][0]['physical_address'] += 1
    with pytest.raises(ValueError, match='ROM mapping'):
        module.validate(manifest, data)
