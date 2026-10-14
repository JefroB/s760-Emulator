"""Versioned project documents for the S-760 private SoundCheck SDK adapter.

Documents reference a sibling component-state file; firmware is user supplied.
Opening validates the document and identities before starting a host. It returns
project-local settings for S760_PLUGIN_CONFIG, without editing global settings.
"""
import hashlib
import json
import os
from pathlib import Path


def digest(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def write_project(path, state, module, settings, rate=44100, block=512):
    path, state, module = map(lambda p: Path(p).resolve(), (path, state, module))
    if state.parent != path.parent:
        raise ValueError('Component state must be a sibling of the project document')
    if rate not in (44100, 48000, 96000) or not 1 <= block <= 1024:
        raise ValueError('Unsupported host profile')
    relative = {}
    for key in ('root', 'bootRom', 'systemDisk', 'mediaDirectory'):
        if key in settings:
            relative[key] = os.path.relpath(settings[key], path.parent)
    identities = {key: digest(settings[key]) for key in ('bootRom', 'systemDisk')}
    identities['runtime'] = digest(Path(settings['root']) / 'mame-source/mames760.exe')
    identities['protocol'] = digest(Path(settings['root']) / 'scripts/s760_runtime.lua')
    document = dict(format='SoundCheck-S760-project', version=1,
                    moduleSha256=digest(module), state=state.name,
                    stateSha256=digest(state), sampleRate=rate, maxBlock=block,
                    configuration=relative, identities=identities)
    # Exclusive creation prevents accidentally replacing a user's project.
    with path.open('x', encoding='utf-8') as target:
        json.dump(document, target, indent=2)
    return document


def read_project(path, module, state_root):
    path = Path(path).resolve()
    if path.stat().st_size > 32768:
        raise ValueError('Project document exceeds 32KB')
    document = json.loads(path.read_text(encoding='utf-8'))
    if document.get('format') != 'SoundCheck-S760-project' or document.get('version') != 1:
        raise ValueError('Unsupported project document')
    if document['sampleRate'] not in (44100, 48000, 96000) or type(document['maxBlock']) is not int or not 1 <= document['maxBlock'] <= 1024:
        raise ValueError('Unsupported host profile')
    state = (path.parent / document['state']).resolve()
    if state.parent != path.parent or not 44 <= state.stat().st_size <= 266 * 1024 * 1024 + 4:
        raise ValueError('Invalid component-state reference')
    if digest(module) != document['moduleSha256']:
        raise ValueError('Project module identity mismatch; cross-build migration unsupported')
    if digest(state) != document['stateSha256']:
        raise ValueError('Project component-state checksum mismatch')
    settings = dict(version=1, stateRoot=str(Path(state_root).resolve()))
    for key in ('root', 'bootRom', 'systemDisk', 'mediaDirectory'):
        if key in document['configuration']:
            settings[key] = str((path.parent / document['configuration'][key]).resolve())
    expected = document['identities']
    for key in ('bootRom', 'systemDisk'):
        if digest(settings[key]) != expected[key]:
            raise ValueError(f'Project {key} identity mismatch')
    for key, relative in (('runtime', 'mame-source/mames760.exe'), ('protocol', 'scripts/s760_runtime.lua')):
        if digest(Path(settings['root']) / relative) != expected[key]:
            raise ValueError(f'Project {key} identity mismatch; migration unsupported')
    return document, state, settings
