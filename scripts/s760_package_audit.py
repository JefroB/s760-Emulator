"""Audit development builds and verify an explicitly reviewed distribution tree.

Only the repository's reviewed artifact manifest can qualify an exact package.
Dependency metadata and package-supplied audit JSON cannot grant release status.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path, PureWindowsPath
import re
import shutil
import sys
from urllib.parse import unquote, urlsplit

PRIVATE_SUFFIXES = {'.bin', '.rom', '.hex', '.img', '.out', '.iso', '.chd', '.hda',
                    '.dsk', '.raw', '.hfe', '.wav', '.aiff', '.s760state'}
QUALIFICATION = 'docs/distribution/windows-standalone-2026-10-11.json'
PYTHON_COMPONENTS = ('pywebview', 'websockets', 'pythonnet', 'clr_loader',
                     'cffi', 'pycparser', 'proxy_tools', 'bottle',
                     'typing_extensions', 'packaging', 'pyinstaller', 'sounddevice')


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path: Path, value) -> None:
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True)+'\n').encode())


def copy_notice(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def readme_errors(package: Path) -> list[str]:
    """Check first-party setup links without rewriting upstream license texts."""
    readme = package/'README.md'
    if not readme.is_file():
        return ['Missing required file: README.md']
    try:
        text = readme.read_text(encoding='utf-8')
    except UnicodeError:
        return ['README.md is not UTF-8']
    text = re.sub(r'```.*?```|~~~.*?~~~', '', text, flags=re.S)
    errors = []
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
        target = target.strip().strip('<>')
        if target.startswith('#'):
            continue
        parsed = urlsplit(target)
        if parsed.scheme in ('http', 'https', 'mailto'):
            continue
        name = unquote(parsed.path)
        path = (package/name).resolve()
        if parsed.scheme or PureWindowsPath(name).is_absolute() or not path.is_relative_to(package.resolve()):
            errors.append(f'README.md link escapes package: {target}')
        elif not path.is_file() and name != 'PACKAGE-AUDIT.json':
            # The audit CLI publishes this very report after collecting errors.
            errors.append(f'README.md broken local link: {target}')
    return errors


def prepare_notices(repo: Path, package: Path) -> None:
    """Copy complete upstream notices, without assigning a project license."""
    copy_notice(repo/'mame-source/COPYING', package/'MAME-COPYING.txt')
    copy_notice(repo/'mame-source/COPYING', package/'mame-source/COPYING')
    legal = repo/'mame-source/docs/legal'
    for source in legal.rglob('*'):
        if source.is_file():
            copy_notice(source, package/'mame-source/docs/legal'/source.relative_to(legal))
    if (repo/'LICENSE').is_file():
        copy_notice(repo/'LICENSE', package/'LICENSE.txt')

    # A conservative build-environment inventory, not a claim that every listed
    # dependency is embedded or that every embedded DLL has been attributed.
    inventory = {'scope': 'build-environment notice superset; actual inputs are in BUNDLED-INPUTS.json and release status requires the reviewed artifact manifest',
                 'python': [], 'npm': []}
    for name in PYTHON_COMPONENTS:
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            inventory['python'].append({'name': name, 'metadata_missing': True})
            continue
        record = {'name': name, 'version': dist.version, 'notices': []}
        for item in dist.files or []:
            if item.name.lower().startswith(('license', 'copying', 'notice')):
                source = Path(dist.locate_file(item))
                if source.is_file():
                    # Do not trust metadata paths as output destinations.
                    target = package/'notices/python'/name/(digest(source)[:12]+'-'+source.name)
                    copy_notice(source, target)
                    record['notices'].append(target.relative_to(package).as_posix())
        inventory['python'].append(record)
    python_license = Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.is_file():
        copy_notice(python_license, package/'notices/python/Python-LICENSE.txt')
    lock = repo/'google-ui/package-lock.json'
    if lock.is_file():
        for location, info in json.loads(lock.read_text(encoding='utf-8'))['packages'].items():
            if not location.startswith('node_modules/'):
                continue
            source_dir = (repo/'google-ui'/location).resolve()
            if not source_dir.is_relative_to((repo/'google-ui/node_modules').resolve()):
                raise ValueError('Dependency path escapes node_modules')
            record = {'path': location, 'version': info.get('version'),
                      'declared_license': info.get('license'), 'notices': []}
            for source in source_dir.glob('*'):
                if source.is_file() and source.name.lower().startswith(('license', 'copying', 'notice')):
                    target = package/'notices/npm'/Path(location).relative_to('node_modules')/source.name
                    copy_notice(source, target)
                    record['notices'].append(target.relative_to(package).as_posix())
            inventory['npm'].append(record)
    write_json(package/'DEPENDENCY-INVENTORY.json', inventory)
    (package/'DEVELOPMENT-ONLY.txt').write_bytes(
        b'Local development artifact. Public distribution has NOT been qualified.\n'
        b'See README.md and PACKAGE-AUDIT.json in this package.\n'
        b'No Roland firmware, samples or saved sessions are supplied.\n'
        b'License text presence does not establish license compatibility or corresponding source.\n')


def audit_package(repo: Path, package: Path) -> dict:
    errors = readme_errors(package)
    files = {}
    private = {}
    for source in (repo/'roms').rglob('*'):
        if source.is_file() and source.suffix.lower() in PRIVATE_SUFFIXES:
            private[digest(source)] = source.relative_to(repo).as_posix()
    for source in sorted(package.rglob('*')):
        if source.is_dir() and source.name.casefold() == 'ic20-hle-findings':
            errors.append(f'Research folder in distribution: {source.relative_to(package)}')
        if source.is_symlink():
            errors.append(f'Unexpected symlink: {source.relative_to(package)}')
            continue
        if not source.is_file() or source == package/'PACKAGE-AUDIT.json':
            continue
        if source.relative_to(package).parts[0] == 'docs' and source.suffix.lower() in {'.exe', '.dll', '.pyd', '.py', '.ps1', '.lua'}:
            errors.append(f'Executable content in documentation: {source.relative_to(package)}')
        name = source.relative_to(package).as_posix()
        checksum = digest(source)
        files[name] = {'sha256': checksum, 'bytes': source.stat().st_size}
        if source.suffix.lower() in PRIVATE_SUFFIXES:
            errors.append(f'Private-media extension: {name}')
        if checksum in private:
            errors.append(f'Private fixture content: {name} matches {private[checksum]}')
    # Dated reviews are immutable history. Only manifests in this trusted
    # repository directory can authorize a tree; package-local reports cannot.
    policies = [(p, json.loads(p.read_text(encoding='utf-8')))
                for p in sorted((repo/'docs/distribution').glob('windows-standalone-*.json'))]
    matching = next((p for p, policy in policies
                     if policy.get('schema') == 1 and policy.get('decision') == 'qualified'
                     and policy.get('files') == files), None)
    reviewed = matching is not None
    expected = [('mame-source/mames760.exe', 'mame-source/mames760.exe'),
                ('scripts/s760_runtime.lua', 'scripts/s760_runtime.lua'),
                ('mame-source/COPYING', 'MAME-COPYING.txt'),
                ('mame-source/COPYING', 'mame-source/COPYING')]
    expected += [(p.relative_to(repo).as_posix(), p.relative_to(repo).as_posix())
                 for p in (repo/'mame-source/docs/legal').rglob('*') if p.is_file()]
    if not reviewed and not (repo/'mame-source/docs/legal/GPL-2.0').is_file():
        errors.append('Missing source MAME GPL-2.0 license')
    # A reviewed tree carries its own source/legal/runtime snapshot. Comparing
    # it with today's working checkout would invalidate historical artifacts
    # whenever the Lua protocol or upstream notices change.
    for source, destination in ([] if reviewed else expected):
        if not (repo/source).is_file() or not (package/destination).is_file():
            errors.append(f'Missing required file: {destination}')
        elif digest(repo/source) != digest(package/destination):
            errors.append(f'Identity mismatch: {destination}')
    for name in ('S760Studio.exe', 'DEPENDENCY-INVENTORY.json',
                 'DISTRIBUTION.md' if reviewed else 'DEVELOPMENT-ONLY.txt'):
        if not (package/name).is_file():
            errors.append(f'Missing required file: {name}')
    blockers = ['corresponding_source_not_qualified', 'bundled_dependency_rights_not_qualified']
    if not (repo/'LICENSE').is_file():
        blockers.insert(0, 'project_license_missing')
    else:
        # Presence alone cannot establish rights for all contributors/files.
        blockers.insert(0, 'project_license_scope_not_reviewed')
    if reviewed:
        blockers = []
    elif policies:
        blockers.append('artifact_differs_from_reviewed_distribution')
    return {'schema': 1, 'development_package_ok': not errors,
            'reviewed_distribution': matching.relative_to(repo).as_posix() if matching else None,
            'release_ready': reviewed and not errors, 'release_blockers': blockers, 'errors': errors,
            'files': files,
            'limitations': ['Hash scan detects exact local ROM/media files and forbidden extensions; it is not a general secret or transformed-content detector.',
                            'Dependency inventory is a build-environment superset; release review is recorded separately in docs/testing/distribution-qualification.md.' if reviewed else
                            'Attribution of bundled DLLs and source correspondence require release review.']}


def require_release(result: dict, *, repo: Path | None = None, package: Path | None = None) -> None:
    # Re-read bytes and trusted repository policy; never trust a supplied report.
    if repo is not None and package is not None:
        current = audit_package(repo, package)
        if current['release_ready']:
            return
        result = current
    raise ValueError('Public distribution is not qualified: '+', '.join(result.get('release_blockers', [])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--require-release', action='store_true')
    args = parser.parse_args()
    repo, package = args.repo.resolve(), args.package.resolve()
    if not package.is_dir() or package == repo:
        parser.error('An existing package directory distinct from the source root is required')
    if args.prepare:
        prepare_notices(repo, package)
    result = audit_package(repo, package)
    write_json(package/'PACKAGE-AUDIT.json', result)
    print(json.dumps({key: value for key, value in result.items() if key != 'files'}, indent=2))
    if args.require_release:
        try:
            require_release(result, repo=repo, package=package)
        except ValueError as error:
            parser.exit(2, str(error)+'\n')
    return 0 if result['development_package_ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
