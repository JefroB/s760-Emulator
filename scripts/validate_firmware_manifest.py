"""Validate a versioned firmware import/build contract without writing firmware."""
import argparse
import hashlib
import json
from pathlib import Path


def validate(manifest, data):
    if manifest['schema_version'] != 1:
        raise ValueError('Unsupported schema version')
    if manifest['cpu'] != 'Intel S80C196KB':
        raise ValueError('Unsupported CPU variant')
    if manifest['target'] not in ('os_disk', 'ic15_rom'):
        raise ValueError('Unsupported target')
    identity = manifest['input']
    if len(data) != identity['size'] or hashlib.sha256(data).hexdigest() != identity['sha256']:
        raise ValueError('Input identity mismatch')
    end = 0
    for region in manifest['layout']:
        if region['start'] != end or not end < region['end'] <= len(data):
            raise ValueError('Layout must partition every input byte without overlaps or gaps')
        if region['policy'] != 'preserve_exactly':
            raise ValueError('Unqualified layout mutation policy')
        end = region['end']
    if end != len(data):
        raise ValueError('Layout does not cover input')
    for region in manifest['annotations']:
        if not 0 <= region['file_start'] < region['file_end'] <= len(data) or not region['evidence']:
            raise ValueError('Invalid annotation')
    for entry in manifest['entry_points']:
        if not 0 <= entry['cpu_address'] <= 65535 or not 0 <= entry['file_offset'] < len(data):
            raise ValueError('Invalid entry point')
        if not entry['evidence']:
            raise ValueError('Entry requires evidence')
    mapping = manifest['mapping']
    if mapping['kind'] == 'os_banked_payload':
        if manifest['target'] != 'os_disk' or not 0 <= mapping['file_start'] < mapping['file_end'] <= len(data):
            raise ValueError('Invalid OS mapping')
        for entry in manifest['entry_points']:
            expected = mapping['file_start'] + (entry['fetch_page'] << 10) + (entry['cpu_address'] & 0x3fff)
            if expected != entry['file_offset'] or not mapping['file_start'] <= expected < mapping['file_end']:
                raise ValueError('Entry disagrees with OS mapping')
    elif mapping['kind'] == 'mirrored_rom':
        if manifest['target'] != 'ic15_rom' or mapping['mirror_size'] != len(data):
            raise ValueError('Invalid ROM mapping')
        for entry in manifest['entry_points']:
            if entry['physical_address'] % mapping['mirror_size'] != entry['file_offset']:
                raise ValueError('Entry disagrees with ROM mapping')
    else:
        raise ValueError('Unknown mapping kind')
    if not manifest['vectors']['evidence'] or not manifest['unknowns']:
        raise ValueError('Missing vector evidence or uncertainty inventory')
    build = manifest['build_contract']
    if build['implemented'] or build['relocation'] != 'unsupported' or build['output_size'] != len(data):
        raise ValueError('This schema qualifies fixed-layout metadata only, not a builder')
    if any(field['policy'] != 'preserve_exactly' for field in manifest['derived_fields']):
        raise ValueError('Unverified derived-field computation')
    return {'target': manifest['target'], 'sha256': identity['sha256'], 'size': len(data),
            'layout_bytes_covered': end, 'annotations': len(manifest['annotations']),
            'entry_points': len(manifest['entry_points']), 'build_implemented': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=Path)
    p.add_argument('input', type=Path)
    args = p.parse_args()
    print(json.dumps(validate(json.loads(args.manifest.read_text(encoding='utf-8')), args.input.read_bytes()), indent=2))


if __name__ == '__main__':
    main()
