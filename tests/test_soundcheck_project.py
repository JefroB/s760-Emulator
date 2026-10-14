import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from soundcheck_project import read_project, write_project


def test_project_relocation_and_rejection_preserve_files(tmp_path):
    project = tmp_path / 'original'
    project.mkdir()
    (project / 'mame-source').mkdir()
    (project / 'scripts').mkdir()
    for name in ('module.vst3', 'boot.bin', 'os.img', 'mame-source/mames760.exe', 'scripts/s760_runtime.lua'):
        (project / name).write_bytes(name.encode())
    (project / 'state.bin').write_bytes(b'fixture-state' * 10)
    settings = dict(root=str(project), bootRom=str(project/'boot.bin'), systemDisk=str(project/'os.img'))
    write_project(project/'session.json', project/'state.bin', project/'module.vst3', settings)
    moved = tmp_path/'relocated'
    project.rename(moved)
    doc, state, restored = read_project(moved/'session.json', moved/'module.vst3', tmp_path/'fresh-runtime')
    assert restored['bootRom'] == str(moved/'boot.bin')
    assert state == moved/'state.bin'
    original = state.read_bytes()
    (moved/'module.vst3').write_bytes(b'changed build')
    with pytest.raises(ValueError, match='module identity'):
        read_project(moved/'session.json', moved/'module.vst3', tmp_path/'fresh-runtime')
    assert state.read_bytes() == original
    (moved/'module.vst3').write_bytes(b'module.vst3')
    state.write_bytes(b'corrupt state' * 10)
    with pytest.raises(ValueError, match='checksum'):
        read_project(moved/'session.json', moved/'module.vst3', tmp_path/'fresh-runtime')
    state.write_bytes(original)
    doc['state'] = '../outside.bin'
    (tmp_path/'outside.bin').write_bytes(original)
    (moved/'session.json').write_text(json.dumps(doc))
    with pytest.raises(ValueError, match='reference'):
        read_project(moved/'session.json', moved/'module.vst3', tmp_path/'fresh-runtime')
