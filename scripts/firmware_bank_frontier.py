"""Find locally evidenced fetch-selector/call pairs in an existing OS analysis.

This reports conditional candidates, not automatic bank propagation or reachability.
Only three consecutive decoded instructions with explicit fallthrough edges qualify.
"""
import argparse
import json
import re
from pathlib import Path


def candidates(analysis, payload_offset=0x4800, payload_end=0x100800):
    if analysis.get('mapping', {}).get('kind', 'os_payload') != 'os_payload':
        raise ValueError('Bank frontier currently requires OS payload mapping')
    results = []
    for region in analysis['regions']:
        rows = {row['pc']: row for row in region['instructions']}
        falls = {(e['from'], e['to']) for e in region['edges']
                 if e['kind'] == 'fallthrough' and e['resolved']}
        for pc, load in sorted(rows.items()):
            if load['mnemonic'] != 'LD':
                continue
            match = re.fullmatch(r'(RW[0-9A-F]+), #(-?0x[0-9a-fA-F]+)', load['operands'])
            if not match:
                continue
            register, page_text = match.groups()
            page = int(page_text, 16) & 0xffff
            store_pc = pc + len(bytes.fromhex(load['bytes']))
            store = rows.get(store_pc)
            if not store or (pc, store_pc) not in falls or store['mnemonic'] != 'ST':
                continue
            match = re.fullmatch(re.escape(register) + r', (0x[0-9a-fA-F]+), TABLE\[ZR\]', store['operands'])
            if not match:
                continue
            selector = int(match[1], 16)
            if selector not in (0x100, 0x102, 0x104, 0x106):
                continue
            window = (selector - 0x100) // 2
            # A current-window remap invalidates the next instruction's old bytes.
            if window == pc >> 14 and page != region['page']:
                continue
            call_pc = store_pc + len(bytes.fromhex(store['bytes']))
            call = rows.get(call_pc)
            if not call or (store_pc, call_pc) not in falls or call['mnemonic'] not in ('LCALL', 'SCALL'):
                continue
            if not re.fullmatch(r'-?0x[0-9a-fA-F]+', call['operands']):
                continue
            target = int(call['operands'], 16) & 0xffff
            if target >> 14 != window:
                continue
            offset = payload_offset + (page << 10) + (target & 0x3fff)
            if not payload_offset <= offset < payload_end:
                continue
            known = [r['name'] for r in analysis['regions'] if r['page'] == page
                     and any(i['pc'] == target for i in r['instructions'])]
            results.append({'source_region': region['name'], 'source_page': region['page'],
                            'load_pc': pc, 'selector_pc': store_pc, 'call_pc': call_pc,
                            'selector': selector, 'destination_page': page,
                            'destination_pc': target, 'destination_file_offset': offset,
                            'already_decoded_in': known,
                            'evidence': [load, store, call]})
    return {'input_sha256': analysis['sha256'], 'candidates': results,
            'qualification': 'Conditional on execution of the adjacent LD/ST/CALL path; '
            'not exhaustive invocation states, callee preservation, or runtime reachability. '
            'Self-window remaps to a different page are excluded. No manifest changes.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('analysis', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = candidates(json.loads(args.analysis.read_text(encoding='utf-8')))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'candidate_calls': len(result['candidates']),
                      'new_destination_pairs': len({(r['destination_page'], r['destination_pc'])
                          for r in result['candidates'] if not r['already_decoded_in']})}))


if __name__ == '__main__':
    main()
