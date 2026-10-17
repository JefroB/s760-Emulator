"""Unit tests for standalone and VST3 release artifact qualification."""
import hashlib
from pathlib import Path
import struct
import pytest

ROOT = Path(__file__).resolve().parents[1]
from scripts.verify_release_artifacts import (
    verify_pe_x64,
    audit_standalone_package,
    audit_vst3_artifact,
    qualify_matrix,
    FORBIDDEN_EXTENSIONS,
)


def test_vst3_binary_architecture():
    """Verify that Roland_S760.vst3 is an AMD64/x64 PE dynamic link library."""
    vst3_path = ROOT / 'build/Release/Roland_S760.vst3'
    if not vst3_path.is_file():
        pytest.skip('VST3 binary not built')
    info = verify_pe_x64(vst3_path)
    assert info['is_dll'] is True
    assert 'AMD64' in info['machine']
    assert info['size_bytes'] > 100000


def test_mame_binary_architecture():
    """Verify that mames760.exe is an AMD64/x64 PE executable."""
    mame_path = ROOT / 'mame-source/mames760.exe'
    if not mame_path.is_file():
        pytest.skip('Native MAME artifact is not provisioned')
    info = verify_pe_x64(mame_path)
    assert info['is_dll'] is False
    assert 'AMD64' in info['machine']
    assert info['size_bytes'] > 20000000


@pytest.fixture
def vst3_audit_fixture(tmp_path, monkeypatch):
    """Invented runtime files for configuration validation, never guest execution."""
    from scripts import verify_release_artifacts as audit
    runtime = tmp_path / 'runtime with spaces'
    for name, size in (
        ('mame-source/mames760.exe', 1), ('scripts/s760_runtime.lua', 1),
        ('google-ui/dist/index.html', 1), ('roms/BOOT/Roland_S-760_v1.11.BIN', 32768),
        ('roms/System/S760224.IMG', 1474560),
    ):
        path = runtime / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes(size))
    # Minimal invented PE header: the real built binary is checked separately.
    data = bytearray(1024)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 0x3C, 0x80)
    data[0x80:0x84] = b'PE\0\0'
    struct.pack_into('<H', data, 0x84, 0x8664)
    struct.pack_into('<H', data, 0x96, 0x2000)
    binary = runtime / 'fixture.vst3'
    binary.write_bytes(data)
    monkeypatch.setattr(audit, 'ROOT', runtime)
    return binary


def test_vst3_audit_contract(vst3_audit_fixture):
    """Configuration contract checks need no installed private runtime."""
    report = audit_vst3_artifact(vst3_audit_fixture)
    assert report['passed'] is True
    assert report['configuration_contract']['path_decoupling_verified'] is True
    assert report['embedded_proprietary_data'] is None
    assert report['private_asset_exclusion_qualified'] is False


def test_vst3_audit_still_rejects_missing_runtime(vst3_audit_fixture):
    (vst3_audit_fixture.parent / 'mame-source/mames760.exe').unlink()
    with pytest.raises(ValueError, match='Missing runtime/editor file'):
        audit_vst3_artifact(vst3_audit_fixture)


def test_built_vst3_audit_with_independent_configuration(vst3_audit_fixture):
    binary = ROOT / 'build/Release/Roland_S760.vst3'
    if not binary.is_file():
        pytest.skip('VST3 binary not built')
    report = audit_vst3_artifact(binary)
    assert report['pe_info']['is_dll']
    assert report['known_private_hash_literals_absent']
    assert report['configuration_contract']['path_decoupling_verified']


def test_clean_machine_matrix_completeness():
    """Verify the clean-machine OS and runtime prerequisites matrix."""
    matrix = qualify_matrix()
    os_names = [item['name'] for item in matrix['supported_os']]
    assert any('Windows 10' in name for name in os_names)
    assert any('Windows 11' in name for name in os_names)

    prereq_names = [item['name'] for item in matrix['runtime_prerequisites']]
    assert any('Visual C++' in name for name in prereq_names)
    assert any('WebView2' in name for name in prereq_names)

    hosts = [item['host'] for item in matrix['vst3_daw_host_matrix']]
    assert 'SoundCheck' in hosts
    assert 'REAPER' in hosts
    assert 'Ableton Live' in hosts
    assert matrix['status']=='NOT_RUN'
    assert matrix['clean_machine_accepted'] is False
    assert matrix['product_release_accepted'] is False
    assert not any(item['qualified'] for item in matrix['vst3_daw_host_matrix'])


def test_forbidden_extensions_comprehensive():
    """Verify that forbidden extension list covers all proprietary disk and state formats."""
    expected = {'.bin', '.rom', '.img', '.s760state', '.wav', '.raw'}
    assert expected.issubset(FORBIDDEN_EXTENSIONS)


def test_passing_static_audits_cannot_complete_acceptance(tmp_path,monkeypatch):
    import json
    import sys
    from scripts import verify_release_artifacts as audit
    monkeypatch.setattr(audit,'audit_standalone_package',lambda _: {'files_inspected':1})
    monkeypatch.setattr(audit,'audit_vst3_artifact',lambda _: {'artifact':'fixture','pe_info':{'size_bytes':512}})
    out=tmp_path/'report.json'
    monkeypatch.setattr(sys,'argv',['audit','--package',str(tmp_path),'--out',str(out)])
    audit.main()
    result=json.loads(out.read_text())
    assert result['static_audit_passed'] is True
    assert result['status']=='INCOMPLETE_ACCEPTANCE'
    assert not result['gate_complete']
    assert not result['clean_machine_accepted']
    assert not result['product_release_accepted']
