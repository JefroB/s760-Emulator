import sys,zipfile,json
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from s760_native_source_bundle import bundle
from s760_package_audit import PRIVATE_SUFFIXES


def test_source_candidate_includes_dirty_code_but_excludes_media_and_objects(tmp_path):
    repo=tmp_path/'repo';source=repo/'mame-source/src';source.mkdir(parents=True)
    (source/'driver.cpp').write_text('latest uncommitted source')
    for suffix in PRIVATE_SUFFIXES:
        (source/('private'+suffix)).write_bytes(b'private')
    (source/'old.obj').write_bytes(b'object')
    (repo/'mame-source/COPYING').write_text('license')
    output=tmp_path/'source.zip';extracted=tmp_path/'extract'
    result=bundle(repo,output,extracted)
    with zipfile.ZipFile(output) as z:
        assert z.read('mame-source/src/driver.cpp')==b'latest uncommitted source'
        assert 'mame-source/src/private.img' not in z.namelist()
        assert 'mame-source/src/old.obj' not in z.namelist()
        assert not any(Path(n).suffix.lower() in PRIVATE_SUFFIXES for n in z.namelist())
        assert not json.loads(z.read('SOURCE-MANIFEST.json'))['qualified']
    assert result['files']==2 and result['omitted']==len(PRIVATE_SUFFIXES)+1
    with pytest.raises(ValueError,match='new output'):
        bundle(repo,output,extracted)
