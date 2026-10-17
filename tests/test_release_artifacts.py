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


def test_vst3_audit_contract():
    """Verify that audit_vst3_artifact validates configuration contract."""
    vst3_path = ROOT / 'build/Release/Roland_S760.vst3'
    if not vst3_path.is_file():
        pytest.skip('VST3 binary not built')
    report = audit_vst3_artifact(vst3_path)
    assert report['passed'] is True
    assert report['configuration_contract']['path_decoupling_verified'] is True
    assert report['embedded_proprietary_data'] is None
    assert report['private_asset_exclusion_qualified'] is False


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
