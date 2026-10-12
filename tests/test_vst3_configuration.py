import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from configure_vst3 import save_config, validate


def fixture(tmp_path):
    root = tmp_path / 'runtime with spaces'
    for name, size in [('mame-source/mames760.exe', 1), ('scripts/s760_runtime.lua', 1),
                       ('google-ui/dist/index.html', 1), ('boot.bin', 32768), ('system.img', 1474560)]:
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(bytes(size))
    return dict(version=1, root=str(root), stateRoot=str(tmp_path / 'sessions'),
                bootRom=str(root / 'boot.bin'), systemDisk=str(root / 'system.img'))


def test_valid_configuration_round_trip_without_rom_copy(tmp_path):
    settings = fixture(tmp_path)
    path = tmp_path / 'settings.json'
    save_config(path, settings)
    assert json.loads(path.read_text(encoding='utf-8')) == settings
    assert path.stat().st_size < 32768
    assert not list(tmp_path.glob('settings.json.*.tmp'))
    assert not Path(settings['stateRoot']).exists()


@pytest.mark.parametrize('key,value', [('version', 2), ('bootRom', 'relative.bin'),
                                     ('root', 'bad\0path'), ('stateRoot', 42)])
def test_invalid_update_preserves_settings(tmp_path, key, value):
    settings = fixture(tmp_path)
    path = tmp_path / 'settings.json'
    save_config(path, settings)
    original = path.read_bytes()
    with pytest.raises(ValueError):
        save_config(path, {**settings, key: value})
    assert path.read_bytes() == original


def test_wrong_firmware_size_is_actionable(tmp_path):
    settings = fixture(tmp_path)
    Path(settings['bootRom']).write_bytes(b'bad')
    with pytest.raises(ValueError, match='32768-byte'):
        validate(settings)


def test_settings_cannot_overwrite_firmware(tmp_path):
    settings = fixture(tmp_path)
    boot = Path(settings['bootRom'])
    original = boot.read_bytes()
    with pytest.raises(ValueError, match='must not overwrite'):
        save_config(boot, settings)
    assert boot.read_bytes() == original
