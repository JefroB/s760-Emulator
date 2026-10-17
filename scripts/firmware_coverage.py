"""Inventory distinct decoded file bytes and unresolved OS exploration edges.

Counts are decoding coverage, never semantic understanding or hardware parity.
"""
import argparse
import json
from pathlib import Path


def inventory(analysis, start, end):
    if not 0 <= start < end:
        raise ValueError('Invalid payload bounds')
    covered, instructions, frontier, selectors = set(), set(), [], []
    for region in analysis['regions']:
        for row in region['instructions']:
            offset = row['file_offset']
            raw = bytes.fromhex(row['bytes'])
            if not start <= offset < offset + len(raw) <= end:
                raise ValueError('Decoded instruction outside payload')
            covered.update(range(offset, offset + len(raw)))
            instructions.add((offset, row['bytes']))
            # These are review candidates, not a register/dataflow analysis.
            if row['mnemonic'] in ('ST', 'STB') and any(f'0x{x:x},' in row['operands'] for x in range(0x100, 0x110)):
                selectors.append({'region': region['name'], **row})
        for edge in region['edges']:
            if not edge['resolved']:
                frontier.append({'region': region['name'], 'source_page': region['page'], **edge,
                                 'destination_page': None})
    data_bytes = set()
    for region in analysis.get('data_regions', []):
        if not start <= region['file_start'] < region['file_end'] <= end:
            raise ValueError('Data region outside payload')
        data_bytes.update(range(region['file_start'], region['file_end']))
    if covered & data_bytes:
        raise ValueError('Code and data classification conflict')
    classified = covered | data_bytes
    gaps, cursor = [], start
    for offset in sorted(classified):
        if offset > cursor:
            gaps.append([cursor, offset])
        cursor = offset + 1
    if cursor < end:
        gaps.append([cursor, end])
    return {'input_sha256': analysis['sha256'], 'payload_start': start, 'payload_end': end,
            'decoded_unique_bytes': len(covered), 'unique_instruction_encodings': len(instructions),
            'identified_data_bytes': len(data_bytes),
            'unclassified_bytes': end - start - len(classified), 'unclassified_ranges': gaps,
            'unresolved_edges': frontier, 'selector_write_review_candidates': selectors,
            'qualification': 'Static decoding under declared mappings; unclassified bytes may be code, data or padding. Selector writes and callee effects require review.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('analysis', type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--payload-start', type=lambda x: int(x, 0), default=0x4800)
    p.add_argument('--payload-end', type=lambda x: int(x, 0), default=0x100800)
    args = p.parse_args()
    result = inventory(json.loads(args.analysis.read_text(encoding='utf-8')), args.payload_start, args.payload_end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('unclassified_ranges', 'unresolved_edges', 'selector_write_review_candidates')}, indent=2))


if __name__ == '__main__':
    main()
