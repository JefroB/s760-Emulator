"""Actual frozen inputs, not installed-package counts, drive attribution."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from s760_distribution_inventory import inventory


def fixture(tmp_path):
    package=tmp_path/'package';build=tmp_path/'build';deps=tmp_path/'deps'
    package.mkdir();build.mkdir();deps.mkdir()
    (deps/'example.py').write_bytes(b'example source')
    info=deps/'example-1.2.dist-info';info.mkdir()
    (info/'METADATA').write_text('Name: example\nVersion: 1.2\nLicense: MIT\n')
    (info/'LICENSE').write_text('example license')
    (info/'RECORD').write_text('example.py,,\nexample-1.2.dist-info/LICENSE,,\nexample-1.2.dist-info/METADATA,,\n')
    (package/'S760Studio.exe').write_bytes(b'launcher')
    (build/'S760Studio.exe').write_bytes(b'launcher')
    (build/'COLLECT-00.toc').write_text(repr(([('S760Studio.exe',str(build/'S760Studio.exe'),'EXECUTABLE')],)))
    (build/'PYZ-00.toc').write_text(repr(('PYZ.pyz',[('example',str(deps/'example.py'),'PYMODULE')])))
    return package,build,deps


def test_bundled_module_discovers_its_notice(tmp_path):
    package,build,deps=fixture(tmp_path)
    result=inventory(package,build,[str(deps)])
    assert result['components']['example']['version']=='1.2'
    assert result['components']['example']['notices']
    assert not result['errors']
    assert result['release_ready'] is False


def test_changed_binary_rejects_correspondence(tmp_path):
    package,build,deps=fixture(tmp_path)
    (package/'S760Studio.exe').write_bytes(b'changed')
    assert any('Identity mismatch' in e for e in inventory(package,build,[str(deps)])['errors'])


def test_build_destination_cannot_escape_package(tmp_path):
    package,build,deps=fixture(tmp_path)
    (build/'COLLECT-00.toc').write_text(repr(([('../escape.dll',str(deps/'example.py'),'BINARY')],)))
    with pytest.raises(ValueError,match='Unsafe'):
        inventory(package,build,[str(deps)])


def test_unattributed_binary_is_explicit(tmp_path):
    package,build,deps=fixture(tmp_path)
    (package/'mystery.dll').write_bytes(b'unknown')
    assert 'mystery.dll' in inventory(package,build,[str(deps)])['unmapped_binaries']


def test_namespace_package_is_not_missing_source(tmp_path):
    package,build,deps=fixture(tmp_path)
    (build/'PYZ-00.toc').write_text(repr(('PYZ.pyz',[('example.namespace','-','PYMODULE')])))
    result=inventory(package,build,[str(deps)])
    assert not result['errors']
    assert result['frozen_modules'][0]['component']=='namespace-package'


def test_collected_unknown_binary_fails_even_when_mapped(tmp_path):
    package,build,deps=fixture(tmp_path)
    source=deps/'mystery.dll';source.write_bytes(b'unknown')
    (package/'_internal').mkdir()
    (package/'_internal/mystery.dll').write_bytes(source.read_bytes())
    (build/'COLLECT-00.toc').write_text(repr(([('mystery.dll',str(source),'BINARY')],)))
    assert any('Unattributed collected input' in e for e in inventory(package,build,[str(deps)])['errors'])


def test_component_version_comes_from_actual_source_distribution(tmp_path):
    package,build,deps=fixture(tmp_path)
    other=tmp_path/'other';other.mkdir()
    info=other/'example-9.9.dist-info';info.mkdir()
    (info/'METADATA').write_text('Name: example\nVersion: 9.9\n')
    (info/'RECORD').write_text('example.py,,\n')
    result=inventory(package,build,[str(deps),str(other)])
    assert result['components']['example']['version']=='1.2'


def test_msvcp_is_external_prerequisite(tmp_path):
    from s760_distribution_inventory import externalize_windows_runtime
    package,build,deps=fixture(tmp_path)
    source=deps/'MSVCP140.dll';source.write_bytes(b'original runtime')
    (package/'_internal').mkdir()
    (package/'_internal/MSVCP140.dll').write_bytes(source.read_bytes())
    (build/'COLLECT-00.toc').write_text(repr(([('MSVCP140.dll',str(source),'BINARY')],)))
    externalize_windows_runtime(package,build)
    result=inventory(package,build,[str(deps)])
    assert not result['errors']
    assert result['collected_files'][0]['disposition']=='external_system_prerequisite'


def test_windows_prerequisite_removes_only_matching_package_copy(tmp_path):
    from s760_distribution_inventory import externalize_windows_runtime
    package,build,deps=fixture(tmp_path)
    source=deps/'ucrtbase.dll';source.write_bytes(b'original system library')
    (package/'_internal').mkdir();target=package/'_internal/ucrtbase.dll';target.write_bytes(source.read_bytes())
    (build/'COLLECT-00.toc').write_text(repr(([('ucrtbase.dll',str(source),'BINARY')],)))
    externalize_windows_runtime(package,build)
    assert source.exists() and not target.exists()
    result=inventory(package,build,[str(deps)])
    assert not result['errors']
    assert result['collected_files'][0]['disposition']=='external_system_prerequisite'
