"""Export immutable IC15 views and context-qualified annotations for Ghidra.

Separate raw programs are inspection views, not a fetch/data-aware decompiler
loader. No arbitrary gap disassembly or inferred functions are introduced.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROM_SHA256 = 'ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6'
VIEWS = (("fetch_low_0780", 0x780, 0x0000, "fetch"),
         ("fetch_high_0790", 0x790, 0x4000, "fetch"),
         ("data_resources_0798", 0x798, 0x8000, "data"))


def view_bytes(rom, page, cpu_base):
    if len(rom) != 0x8000:
        raise ValueError('IC15 must contain exactly32768 bytes')
    if cpu_base not in (0, 0x4000, 0x8000, 0xc000):
        raise ValueError('View must begin at a16KB CPU window')
    if not 0x1e0000 <= page << 10 < 0x200000:
        raise ValueError('Selector is outside the established ROM aperture')
    return bytes(rom[((page << 10) + ((cpu_base + i) & 0x3fff)) & 0x7fff]
                 for i in range(0x4000))


def export(rom_path, manifest_path, output):
    rom_path, manifest_path, output = map(lambda p: Path(p).resolve(), (rom_path, manifest_path, output))
    if any(p.is_relative_to(output) for p in (rom_path, manifest_path)):
        raise ValueError('Output directory must not contain either input')
    rom = rom_path.read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest != ROM_SHA256:
        raise ValueError('Input does not match the qualified original IC15 ROM')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['sha256'] != digest or manifest['mapping']['kind'] != 'mirrored_rom':
        raise ValueError('Manifest identity or mapping mismatch')
    output.mkdir(parents=True, exist_ok=True)
    index = {'input_sha256': digest, 'language': 'MCS96:LE:16:default',
             'qualification': 'Separate fetch/data inspection programs. Do not merge into a flat default RAM map or trust automatic decompiler data references. Labels retain manifest evidence; roots are not universally invoked.',
             'mapping': 'file=((page<<10)+(cpu&0x3fff))&0x7fff', 'views': [],
             'regions': manifest['regions'], 'bank_links': manifest.get('bank_links', []),
             'data_regions': manifest.get('data_regions', [])}
    number = lambda x: int(x, 0) if isinstance(x, str) else x
    with (output / 'entries.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['view', 'cpu_address', 'file_offset', 'label', 'qualification'])
        for name, page, cpu_base, kind in VIEWS:
            data = view_bytes(rom, page, cpu_base)
            filename = name + '.bin'
            (output / filename).write_bytes(data)
            index['views'].append({'file': filename, 'selector': page, 'cpu_base': cpu_base,
                                   'kind': kind, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
            if kind != 'fetch':
                continue
            for region in manifest['regions']:
                if number(region['page']) != page:
                    continue
                for entry in region['entries']:
                    entry = number(entry)
                    if not cpu_base <= entry < cpu_base + 0x4000:
                        raise ValueError('Declared entry outside its fetch inspection view')
                    offset = ((page << 10) + (entry & 0x3fff)) & 0x7fff
                    writer.writerow([name, f'0x{entry:04X}', f'0x{offset:04X}', region['name'], region.get('evidence', '')])
    (output / 'contexts.json').write_text(json.dumps(index, indent=2) + '\n', encoding='utf-8')
    (output / 'README.txt').write_text(
        'Import each BIN as a separate raw program using MCS96:LE:16:default and the cpu_base in contexts.json.\n'
        'Keep automatic whole-image analysis off; entries.csv supplies only declared contextual roots.\n'
        'The resource view is DATA, including the mirrored wrap; do not analyze it as code.\n'
        'Fetch4000..7FFF is ROM, while logical data4000..7FFF is work RAM under010A=03F0.\n'
        'These views do not implement that split for the decompiler. Follow data references with explicit selectors.\n'
        'Bank links, structural-only entry qualifications and data evidence are retained in contexts.json.\n', encoding='utf-8')
    return index


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=Path('roms/BOOT/Roland_S-760_v1.11.BIN'))
    parser.add_argument('--manifest', type=Path, default=Path('scripts/firmware_manifests/ic15_exploration.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = export(args.rom, args.manifest, args.output)
    print(json.dumps({'input_sha256': result['input_sha256'], 'views': result['views']}, indent=2))
