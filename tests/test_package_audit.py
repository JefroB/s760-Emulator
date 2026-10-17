"""Distribution gate: development builds must not masquerade as releases."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from s760_package_audit import prepare_notices, audit_package, require_release
from s760_package_audit import QUALIFICATION


def test_shipped_readme_links_are_relative_to_package_root():
    """This template is copied to package/README.md, not served from docs/."""
    import re
    source = Path(__file__).resolve().parents[1] / 'docs/emulator/guides/standalone-package-readme.md'
    targets = re.findall(r'\]\(([^)]+)\)', source.read_text(encoding='utf-8'))
    assert targets
    for target in targets:
        if '://' not in target and not target.startswith('#'):
            assert not target.startswith(('../', '/')), target


def test_historical_artifact_names_are_not_rewritten_by_document_moves():
    import hashlib
    root=Path(__file__).resolve().parents[1]
    files=json.loads((root/QUALIFICATION).read_text(encoding='utf-8'))['files']
    encoded=json.dumps(files,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(encoded).hexdigest()=='f6dd8fdc80d82b431ad3add808153760fdaee09ada7810f26b4d6d30d71aaacd'


@pytest.fixture
def package(tmp_path):
    repo, package = tmp_path/'repo', tmp_path/'package'
    for root in (repo, package):
        (root/'mame-source').mkdir(parents=True)
        (root/'scripts').mkdir()
        (root/'mame-source/mames760.exe').write_bytes(b'test engine')
        (root/'scripts/s760_runtime.lua').write_text('test runtime')
    (repo/'mame-source/docs/legal').mkdir(parents=True)
    (repo/'mame-source/docs/legal/GPL-2.0').write_text('test GPL text')
    (repo/'mame-source/COPYING').write_text('test MAME copyright')
    (repo/'roms').mkdir()
    (repo/'roms/boot.bin').write_bytes(b'private test firmware')
    (package/'S760Studio.exe').write_bytes(b'test launcher')
    (package/'README.md').write_text('Standalone setup')
    return repo, package


def test_prepare_preserves_full_license_and_identifies_exact_artifact(package):
    repo, root = package
    prepare_notices(repo, root)
    assert (root/'mame-source/docs/legal/GPL-2.0').read_bytes() == (repo/'mame-source/docs/legal/GPL-2.0').read_bytes()
    result = audit_package(repo, root)
    assert result['development_package_ok']
    assert not result['release_ready']
    assert 'project_license_missing' in result['release_blockers']
    assert 'mame-source/mames760.exe' in result['files']
    with pytest.raises(ValueError, match='not qualified'):
        require_release(result)


@pytest.mark.parametrize('path', ['hidden.img', 'session.s760state', 'renamed.dat'])
def test_private_media_cannot_leak_even_when_renamed(package, path):
    repo, root = package
    prepare_notices(repo, root)
    (root/path).write_bytes((repo/'roms/boot.bin').read_bytes())
    result = audit_package(repo, root)
    assert not result['development_package_ok']
    assert any(path in error for error in result['errors'])


def test_engine_drift_and_license_loss_fail_closed(package):
    repo, root = package
    prepare_notices(repo, root)
    (root/'mame-source/mames760.exe').write_bytes(b'wrong engine')
    (root/'mame-source/docs/legal/GPL-2.0').unlink()
    result = audit_package(repo, root)
    assert not result['development_package_ok']
    assert any('mames760.exe' in error for error in result['errors'])
    assert any('GPL-2.0' in error for error in result['errors'])


def test_license_file_alone_does_not_claim_dependency_or_source_clearance(package):
    repo, root = package
    (repo/'LICENSE').write_text('owner license')
    prepare_notices(repo, root)
    result = audit_package(repo, root)
    assert 'project_license_missing' not in result['release_blockers']
    assert 'corresponding_source_not_qualified' in result['release_blockers']
    assert 'bundled_dependency_rights_not_qualified' in result['release_blockers']
    assert not result['release_ready']


def test_packaged_readme_cannot_link_to_missing_source_checkout_docs(package):
    repo, root = package
    prepare_notices(repo, root)
    (root/'README.md').write_text('[Firmware setup](firmware-setup.md)')
    result = audit_package(repo, root)
    assert not result['development_package_ok']
    assert any('firmware-setup.md' in error for error in result['errors'])


@pytest.mark.parametrize('target', ['../outside.md', 'C:/checkout/guide.md', '%2e%2e/outside.md', 'file:///C:/guide.md'])
def test_packaged_readme_rejects_checkout_paths(package, target):
    repo, root = package
    prepare_notices(repo, root)
    (root/'README.md').write_text(f'[Setup]({target})')
    assert any('escapes package' in error for error in audit_package(repo, root)['errors'])


def test_packaged_readme_valid_local_links_and_command_examples(package):
    repo, root = package
    prepare_notices(repo, root)
    (root/'guide with spaces.md').write_text('Help')
    (root/'README.md').write_text('[Help](guide%20with%20spaces.md#setup)\n[Website](https://example.com)\n[Top](#setup)\n```text\n[example](not-a-real-file.md)\n```')
    assert audit_package(repo, root)['development_package_ok']


def test_packaged_readme_is_required(package):
    repo, root = package
    prepare_notices(repo, root)
    (root/'README.md').unlink()
    assert 'Missing required file: README.md' in audit_package(repo, root)['errors']


def test_existing_json_cannot_forge_release_status(package):
    repo, root = package
    prepare_notices(repo, root)
    (root/'PACKAGE-AUDIT.json').write_text(json.dumps({'release_ready': True}))
    assert not audit_package(repo, root)['release_ready']
    with pytest.raises(ValueError, match='not qualified'):
        require_release({'release_ready': True, 'release_blockers': []})


def test_new_dated_review_preserves_history_and_rejects_package_local_policy(package):
    repo, root = package
    prepare_notices(repo, root)
    (root/'DISTRIBUTION.md').write_text('Reviewed distribution contents only')
    old=repo/QUALIFICATION;old.parent.mkdir(parents=True)
    old.write_text(json.dumps({'schema':1,'decision':'qualified','files':{}}))
    review={'schema':1,'decision':'qualified','files':audit_package(repo,root)['files']}
    (root/'windows-standalone-2099-01-01.json').write_text(json.dumps(review))
    assert not audit_package(repo,root)['release_ready']
    (root/'windows-standalone-2099-01-01.json').unlink()
    current=old.with_name('windows-standalone-2099-01-01.json')
    current.write_text(json.dumps(review))
    assert audit_package(repo,root)['release_ready']
    assert json.loads(old.read_text())['files']=={}
    (root/'S760Studio.exe').write_bytes(b'drift')
    assert not audit_package(repo,root)['release_ready']


def test_reviewed_source_snapshot_survives_worktree_changes(package):
    repo, root = package
    prepare_notices(repo, root)
    (root/'DISTRIBUTION.md').write_text('Reviewed source snapshot')
    policy=repo/QUALIFICATION;policy.parent.mkdir(parents=True)
    policy.write_text(json.dumps({'schema':1,'decision':'qualified','files':audit_package(repo,root)['files']}))
    (repo/'scripts/s760_runtime.lua').write_text('new development protocol')
    (repo/'mame-source/docs/legal/GPL-2.0').unlink()
    assert audit_package(repo,root)['release_ready']
    (root/'scripts/s760_runtime.lua').write_text('unreviewed package protocol')
    assert not audit_package(repo,root)['release_ready']


@pytest.mark.parametrize('changed', ['mame-source/mames760.exe', 'MAME-COPYING.txt',
                                    'corresponding-source/mame-source.zip', 'extra.txt',
                                    'scripts/PACKAGE-AUDIT.json'])
def test_reviewed_tree_requires_exact_bytes_and_no_added_files(package, changed):
    repo, root = package
    prepare_notices(repo, root)
    (root/'DISTRIBUTION.md').write_text('reviewed test profile')
    (root/'corresponding-source').mkdir()
    (root/'corresponding-source/mame-source.zip').write_bytes(b'test source')
    policy = repo/QUALIFICATION
    policy.parent.mkdir(parents=True)
    policy.write_text(json.dumps({'schema': 1, 'decision': 'qualified',
                                 'files': audit_package(repo, root)['files']}))
    result = audit_package(repo, root)
    assert result['release_ready']
    require_release(result, repo=repo, package=root)
    (root/changed).write_bytes(b'changed after review')
    assert not audit_package(repo, root)['release_ready']
    with pytest.raises(ValueError, match='not qualified'):
        require_release(result, repo=repo, package=root)
