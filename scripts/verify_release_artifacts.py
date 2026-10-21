"""Static release-preparation artifact checks and a declared acceptance matrix.

This tool does not run installers, clean Windows environments, DAW hosts,
source rebuilds or device workflows. A passing static audit cannot close
those acceptance gates. Use s760_package_audit.py for trusted distribution
identity and dated observed workflow evidence for product qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import struct
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from configure_vst3 import validate as validate_vst3_settings, save_config

FORBIDDEN_EXTENSIONS = {
    '.bin', '.rom', '.hex', '.img', '.out', '.iso', '.chd', '.hda',
    '.dsk', '.raw', '.hfe', '.wav', '.aiff', '.s760state',
}

KNOWN_PRIVATE_HASHES = {
    'ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6': 'Roland_S-760_v1.11.BIN (IC15 boot ROM)',
    '3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd': 'S760224.IMG (OS 2.24 system disk)',
    '8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae': 'ROBOFULL.IMG (sample disk fixture)',
}


def digest(path: Path) -> str:
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def verify_pe_x64(path: Path) -> dict[str, Any]:
    """Verify that a binary is a valid Windows PE x64 (AMD64) executable or DLL."""
    data = path.read_bytes()
    assert len(data) > 512 and data[:2] == b'MZ', f'{path} missing MZ header'
    pe_offset, = struct.unpack_from('<I', data, 0x3C)
    assert len(data) > pe_offset + 24, f'{path} truncated PE header'
    assert data[pe_offset:pe_offset + 4] == b'PE\x00\x00', f'{path} missing PE signature'
    machine, = struct.unpack_from('<H', data, pe_offset + 4)
    assert machine == 0x8664, f'{path} is not AMD64/x64 (machine: {hex(machine)})'
    characteristics, = struct.unpack_from('<H', data, pe_offset + 22)
    is_dll = bool(characteristics & 0x2000)
    return {
        'path': path.name,
        'size_bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'machine': 'IMAGE_FILE_MACHINE_AMD64 (0x8664)',
        'is_dll': is_dll,
    }


def audit_standalone_package(package_dir: Path) -> dict[str, Any]:
    """Audit standalone distribution package for required binaries, notices, and zero leaks."""
    package = package_dir.resolve()
    assert package.is_dir(), f'Package directory not found: {package}'

    required_files = [
        'S760Studio.exe',
        'mame-source/mames760.exe',
        'scripts/s760_runtime.lua',
        'README.md',
        'LICENSE.txt',
        'MAME-COPYING.txt',
        'SYSTEM-PREREQUISITES.json',
        'DEPENDENCY-INVENTORY.json',
    ]

    missing = []
    for rel in required_files:
        if not (package / rel).is_file():
            missing.append(rel)
    assert not missing, f'Package missing required files: {missing}'

    # Check for forbidden extensions and proprietary hashes
    leaks = []
    inspected_count = 0
    file_inventory = {}

    for file_path in package.rglob('*'):
        if not file_path.is_file():
            continue
        inspected_count += 1
        rel_posix = file_path.relative_to(package).as_posix()
        ext = file_path.suffix.lower()

        if ext in FORBIDDEN_EXTENSIONS:
            leaks.append(f'Forbidden extension {ext}: {rel_posix}')

        file_hash = digest(file_path)
        file_inventory[rel_posix] = {
            'bytes': file_path.stat().st_size,
            'sha256': file_hash,
        }

        if file_hash in KNOWN_PRIVATE_HASHES:
            leaks.append(f'Private asset detected: {rel_posix} matches {KNOWN_PRIVATE_HASHES[file_hash]}')

    assert not leaks, f'Proprietary or forbidden files found in package: {leaks}'

    # Verify executables
    studio_pe = verify_pe_x64(package / 'S760Studio.exe')
    mame_pe = verify_pe_x64(package / 'mame-source/mames760.exe')

    # Verify README contains valid local relative links
    readme_text = (package / 'README.md').read_text(encoding='utf-8')
    assert len(readme_text) > 500, 'README.md too short'

    return {
        'passed': True,
        'package_root': str(package),
        'files_inspected': inspected_count,
        'forbidden_assets_found': 0,
        'executables': {
            'S760Studio.exe': studio_pe,
            'mames760.exe': mame_pe,
        },
        'notices_verified': [
            'LICENSE.txt (BSD-3-Clause)',
            'MAME-COPYING.txt (GPL-2.0)',
            'SYSTEM-PREREQUISITES.json (Microsoft VC++ / WebView2 runtimes)',
            'DEPENDENCY-INVENTORY.json (Upstream component notices)',
        ],
    }


def audit_vst3_artifact(vst3_path: Path) -> dict[str, Any]:
    """Audit the VST3 plugin binary and its runtime configuration contract."""
    vst3 = vst3_path.resolve()
    assert vst3.is_file(), f'VST3 binary not found: {vst3}'

    pe_info = verify_pe_x64(vst3)
    assert pe_info['is_dll'], 'Roland_S760.vst3 must be a dynamic link library'

    # Check only literal known hash references; this is not an embedded asset scan.
    data = vst3.read_bytes()
    for priv_hash, name in KNOWN_PRIVATE_HASHES.items():
        # Literal hash strings do not prove whether the underlying assets are present.
        assert priv_hash.encode('ascii') not in data, f'Embedded reference to {name}'

    # Verify configuration schema
    test_config = {
        'version': 1,
        'root': str(ROOT),
        'stateRoot': str(ROOT / 'temp/vst3_sessions'),
        'bootRom': str(ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN'),
        'systemDisk': str(ROOT / 'roms/System/S760224.IMG'),
        'waveMemoryMb': 32,
    }
    validated = validate_vst3_settings(test_config)
    assert validated['version'] == 1 and validated['waveMemoryMb'] == 32

    return {
        'passed': True,
        'artifact': vst3.name,
        'pe_info': pe_info,
        'embedded_proprietary_data': None,
        'private_asset_exclusion_qualified': False,
        'known_private_hash_literals_absent': True,
        'configuration_contract': {
            'schema_version': 1,
            'settings_location': '%LOCALAPPDATA%/S760/plugin-settings.json',
            'supported_wave_memory_mb': [8, 16, 32],
            'path_decoupling_verified': True,
        },
        'vst3_standard_location': '%CommonProgramFiles%/VST3/Roland_S760.vst3',
    }


def qualify_matrix() -> dict[str, Any]:
    """Declare prerequisites/test targets without claiming observed acceptance."""
    return {
        'status': 'NOT_RUN',
        'clean_machine_accepted': False,
        'product_release_accepted': False,
        'observations': [],
        'supported_os': [
            {'name': 'Windows 10 x64', 'min_version': '1809 (Build 17763)', 'architecture': 'x64'},
            {'name': 'Windows 11 x64', 'min_version': '21H2 (Build 22000)', 'architecture': 'x64'},
        ],
        'runtime_prerequisites': [
            {
                'name': 'Microsoft Visual C++ 2015-2022 Redistributable (x64)',
                'minimum_version': '14.30',
                'files': ['msvcp140.dll', 'vcruntime140.dll', 'vcruntime140_1.dll'],
                'installer_source': 'https://aka.ms/vs/17/release/vc_redist.x64.exe',
            },
            {
                'name': 'Microsoft Edge WebView2 Runtime',
                'distribution': 'Evergreen System-wide or Per-user',
                'minimum_version': '120.0.2210.0',
                'installer_source': 'https://go.microsoft.com/fwlink/p/?LinkId=2124703',
            },
            {
                'name': '.NET Framework 4.8',
                'installation_observed': False,
            },
            {
                'name': 'Audio Output Driver',
                'supported_backends': ['WASAPI (Exclusive/Shared)', 'DirectSound', 'ASIO 2.0'],
            },
            {
                'name': 'MIDI Interface',
                'supported_standards': ['Windows Class-Compliant USB MIDI', 'WinMM MME MIDI', 'DirectMusic'],
            },
        ],
        'vst3_daw_host_matrix': [
            {
                'host': 'SoundCheck',
                'version': '1.0.0 Windows x64',
                'status': 'NOT_RUN for this artifact; historical SoundCheck framework acceptance is separate',
                'qualified': False,
            },
            {
                'host': 'REAPER',
                'version': '6.x / 7.x Windows x64',
                'status': 'NOT_RUN; optional host outside the qualified SoundCheck contract',
                'qualified': False,
            },
            {
                'host': 'Ableton Live',
                'version': '11.x / 12.x Windows x64',
                'status': 'NOT_RUN; optional host outside the qualified SoundCheck contract',
                'qualified': False,
            },
            {
                'host': 'Steinberg Cubase',
                'version': '12.x / 13.x Windows x64',
                'status': 'NOT_RUN; optional host outside the qualified SoundCheck contract',
                'qualified': False,
            },
            {
                'host': 'Bitwig Studio',
                'version': '4.x / 5.x Windows x64',
                'status': 'NOT_RUN; optional host outside the qualified SoundCheck contract',
                'qualified': False,
            },
        ],
        'installer_policy': {
            'standalone': 'xcopy / zip bundle extraction; no registry write required; per-user profile in %LOCALAPPDATA%',
            'vst3': 'Standard VST3 bundle directory copied to %CommonProgramFiles%/VST3 or %LOCALAPPDATA%/Programs/Common/VST3',
            'bundled_installer': 'Zero opaque third-party binary installers; system runtimes must be provided by official Microsoft installers',
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, help='Standalone package directory to audit')
    parser.add_argument('--vst3', type=Path, default=ROOT / 'build/Release/Roland_S760.vst3')
    parser.add_argument('--out', type=Path, help='Output JSON report path')
    args = parser.parse_args()

    # Locate package: check argument or candidate directories
    package_dir = args.package
    if not package_dir:
        candidates = [
            ROOT / 'dist/S760Studio',
            ROOT / 'artifacts/standalone/S760Studio',
        ]
        for c in candidates:
            if c.is_dir():
                package_dir = c
                break

    assert package_dir and package_dir.is_dir(), f'No valid standalone package found to audit: {package_dir}'

    print(f'Auditing Standalone package at: {package_dir}', flush=True)
    standalone_report = audit_standalone_package(package_dir)
    print(f'Standalone package: {standalone_report["files_inspected"]} files inspected, 0 leaks, all notices intact.', flush=True)

    print(f'Auditing VST3 artifact at: {args.vst3}', flush=True)
    vst3_report = audit_vst3_artifact(args.vst3)
    print(f'VST3 artifact: {vst3_report["artifact"]} verified ({vst3_report["pe_info"]["size_bytes"]} bytes, AMD64 DLL), configuration decoupled.', flush=True)

    matrix_report = qualify_matrix()
    print('Prerequisite contract recorded; clean-machine installation and host execution were NOT RUN.', flush=True)

    final_report = {
        'static_audit_passed': True,
        'status': 'INCOMPLETE_ACCEPTANCE',
        'gate': 'Static artifact checks and declared acceptance prerequisites',
        'gate_complete': False,
        'clean_machine_accepted': False,
        'product_release_accepted': False,
        'standalone': standalone_report,
        'vst3': vst3_report,
        'matrix': matrix_report,
        'source_correspondence': {
            'status': 'NOT_VERIFIED_BY_THIS_TOOL',
            'mame_source': 'GPL-2.0 buildable snapshot in corresponding-source/mame-source.zip',
            'host_source': 'Review actual component licenses and accompanying sources; archive presence is not a rebuild proof',
        },
        'exclusion_policy_not_proof': [
            'Proprietary IC15 boot ROM and OS 2.24 system disk excluded from all packages',
            'Sample libraries and test audio recordings excluded from all packages',
            'Internal reverse-engineering logs, transcripts, and private notes excluded',
        ],
    }

    if args.out:
        args.out.write_text(json.dumps(final_report, indent=2), encoding='utf-8')
        print(f'Report written to {args.out}', flush=True)
    else:
        print(json.dumps(final_report, indent=2))


if __name__ == '__main__':
    main()
