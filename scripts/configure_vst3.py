"""Validate and persist user-supplied S-760 VST3 runtime paths.

Run before loading the plugin. No Roland data is copied into this settings file.
The plugin reads it on creation; reload an existing instance after a change.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile


def default_config():
    if os.environ.get('S760_PLUGIN_CONFIG'):
        return Path(os.environ['S760_PLUGIN_CONFIG'])
    if os.environ.get('LOCALAPPDATA'):
        return Path(os.environ['LOCALAPPDATA']) / 'S760' / 'plugin-settings.json'
    raise ValueError('Specify --config with an absolute settings filename')


def validate(settings):
    if not isinstance(settings, dict) or type(settings.get('version')) is not int or settings['version'] != 1:
        raise ValueError('Unsupported settings version')
    if type(settings.get('waveMemoryMb',32)) is not int or settings.get('waveMemoryMb',32) not in (8,16,32):
        raise ValueError('Wave memory must be 8, 16 or 32 MB')
    paths = {}
    for key in ('root', 'stateRoot', 'bootRom', 'systemDisk'):
        value = settings.get(key)
        if not isinstance(value, str) or '\0' in value or len(value.encode('utf-8')) > 4096:
            raise ValueError(f'Invalid {key}')
        path = Path(value)
        if not path.is_absolute():
            raise ValueError(f'{key} must be absolute')
        paths[key] = path
    for path in (paths['root'] / 'mame-source/mames760.exe',
                 paths['root'] / 'scripts/s760_runtime.lua',
                 paths['root'] / 'google-ui/dist/index.html'):
        if not path.is_file():
            raise ValueError(f'Missing runtime/editor file: {path}')
    for key, size in (('bootRom', 32768), ('systemDisk', 1474560)):
        if not paths[key].is_file() or paths[key].stat().st_size != size:
            raise ValueError(f'{key} must name a readable {size}-byte file: {paths[key]}')
        with paths[key].open('rb') as file:
            file.read(1)
    if paths['stateRoot'].exists() and not paths['stateRoot'].is_dir():
        raise ValueError('stateRoot must be a directory')
    return settings


def save_config(path, settings):
    if not path.is_absolute():
        raise ValueError('Settings filename must be absolute')
    validate(settings)  # A rejected change must preserve the previous settings.
    protected = [Path(settings[key]) for key in ('bootRom', 'systemDisk')]
    protected += [Path(settings['root']) / name for name in
                  ('mame-source/mames760.exe', 'scripts/s760_runtime.lua', 'google-ui/dist/index.html')]
    if any(path.resolve() == source.resolve() for source in protected):
        raise ValueError('Settings filename must not overwrite firmware or runtime files')
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix=path.name + '.', suffix='.tmp', delete=False) as file:
            pending = Path(file.name)
            json.dump(settings, file, indent=2, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(pending, path)
    finally:
        if pending and pending.exists():
            pending.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, help='Defaults to LOCALAPPDATA/S760/plugin-settings.json; custom locations also need S760_PLUGIN_CONFIG in the host environment')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--state-root', type=Path)
    parser.add_argument('--boot-rom', type=Path)
    parser.add_argument('--system-disk', type=Path)
    parser.add_argument('--wave-memory-mb',type=int,choices=(8,16,32),default=32)
    parser.add_argument('--check', action='store_true', help='Validate existing settings without changing them')
    parser.add_argument('--diagnose', action='store_true', help='Show the last factory failure, then validate settings')
    args = parser.parse_args()
    try:
        path = args.config or default_config()
        if not path.is_absolute():
            raise ValueError('Settings filename must be absolute')
        if args.diagnose:
            diagnostic = Path(str(path) + '.last-error.txt')
            print(diagnostic.read_text(encoding='utf-8') if diagnostic.exists() else 'No saved startup failure.')
        if args.check or args.diagnose:
            if path.stat().st_size > 32768:
                raise ValueError('Settings exceed 32KB')
            validate(json.loads(path.read_text(encoding='utf-8')))
            print(f'Valid settings: {path}')
        else:
            if not all((args.state_root, args.boot_rom, args.system_disk)):
                parser.error('--state-root, --boot-rom and --system-disk are required')
            settings = {'version': 1, 'waveMemoryMb': args.wave_memory_mb, 'root': str(args.root.resolve()),
                        'stateRoot': str(args.state_root.resolve()),
                        'bootRom': str(args.boot_rom.resolve()), 'systemDisk': str(args.system_disk.resolve())}
            save_config(path, settings)
            print(f'Saved {path}. Reload the plugin to apply. Roland binaries remain user-supplied.')
        return 0
    except (OSError, ValueError) as error:
        print(f'S-760 configuration failed: {error}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
