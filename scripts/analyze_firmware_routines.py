"""Bounded, bank-qualified MCS-96 analysis. Never modifies the input image.

This is an analysis view, not an assembler or a semantic decompiler. Regions
assert a fetch mapping; cross-region targets require evidence before following.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import pypcode


def number(value):
    return int(value, 0) if isinstance(value, str) else value


def fetch_mapping_write(pc, mnemonic, operands):
    """Recognize direct absolute writes overlapping this instruction's selector.

    Indirect stores and callee effects remain unresolved. Even a possibly
    redundant write stops decoding because no register value is propagated.
    """
    if mnemonic not in ('ST', 'STB', 'POP'):
        return None
    match = re.search(r'(0x[0-9a-fA-F]+), (?:TABLE|LOOKUP)\[ZR\]$', operands)
    if not match:
        return None
    address = int(match[1], 16)
    width = 1 if mnemonic == 'STB' else 2
    selector = 0x100 + 2 * (pc >> 14)
    if address < selector + 2 and address + width > selector:
        return f'Direct {mnemonic} overlaps current fetch selector {selector:04X}; next mapping unproved'
    return None


def analyze(data, manifest):
    digest = hashlib.sha256(data).hexdigest()
    if digest != manifest['sha256'].lower():
        raise ValueError('Input SHA256 does not match manifest')
    ctx = pypcode.Context('MCS96:LE:16:default')
    mapping = manifest.get('mapping', {'kind': 'os_payload'})
    if mapping['kind'] not in ('os_payload', 'mirrored_rom'):
        raise ValueError('Unsupported fetch mapping')
    if mapping['kind'] == 'mirrored_rom':
        mirror_size = number(mapping['mirror_size'])
        aperture_start, aperture_end = map(number, mapping['physical_aperture'])
        if mirror_size <= 0 or mirror_size & (mirror_size - 1) or mirror_size != len(data):
            raise ValueError('ROM mirror size must be a power of two matching input size')
        if not 0 <= aperture_start < aperture_end or aperture_start % mirror_size or aperture_end % mirror_size:
            raise ValueError('Invalid ROM aperture')
    result = {'sha256': digest, 'decoder': 'pypcode ' + pypcode.__version__,
              'mapping': mapping,
              'scope': 'Static bounded fetch mappings; no bank-state propagation or type recovery',
              'regions': []}
    names = set()
    for region in manifest['regions']:
        name = region['name']
        if name in names or not re.fullmatch(r'[a-z0-9_]+', name):
            raise ValueError('Invalid or duplicate region name')
        names.add(name)
        page, start, end = map(number, (region['page'], region['start'], region['end']))
        if not 0 <= start < end <= 65536 or start >> 14 != (end - 1) >> 14:
            raise ValueError('Region must stay within one 16 KiB fetch window')
        base = number(manifest.get('payload_offset', 0)) + (page << 10)
        def offset(pc):
            if mapping['kind'] == 'mirrored_rom':
                physical = (page << 10) + (pc & 0x3fff)
                if not aperture_start <= physical < aperture_end:
                    raise ValueError('Fetch outside ROM aperture')
                return physical & (mirror_size - 1)
            return base + (pc & 0x3fff)
        if page < 0 or offset(start) < 0 or offset(end - 1) >= len(data):
            raise ValueError('Region outside input')
        if offset(end - 1) - offset(start) != end - start - 1:
            raise ValueError('Region crosses ROM mirror boundary; split the mapping')
        entries = list(map(number, region['entries']))
        indirect = {number(k): v for k, v in region.get('indirect_targets', {}).items()}
        stops = {number(k): v for k, v in region.get('stop_after', {}).items()}
        if not entries or any(not start <= p < end for p in entries):
            raise ValueError('Entry outside region')
        todo, rows, occupied, edges, warnings = entries[:], {}, {}, [], []
        while todo:
            pc = todo.pop(0)
            if pc in rows:
                continue
            if pc in occupied:
                raise ValueError(f'{name}: target {pc:04X} enters an instruction')
            raw = data[offset(pc):offset(pc) + min(16, end - pc)]
            try:
                ins = ctx.disassemble(raw, base_address=pc, max_instructions=1).instructions[0]
            except Exception as exc:
                warnings.append({'pc': pc, 'reason': 'Decode failed: ' + str(exc)})
                continue
            size, mnemonic, body = ins.length, ins.mnem.upper(), ins.body
            # BUG-086: Intel 80C196KB Table 3-2B instruction lengths
            # SLEIGH decodes SKIP (0x00) as 1 byte; Intel KB specifies 2 bytes (0x00 <count>).
            # SLEIGH decodes IDLPD (0xF6) as 2 bytes; Intel KB specifies 1 byte.
            if mnemonic == 'SKIP' and size == 1:
                if len(raw) >= 2:
                    size = 2
                    body = f'#{raw[1]:#x}'
            elif mnemonic == 'IDLPD' and size == 2:
                size = 1
                body = ''
            if size > end - pc or any(p in occupied for p in range(pc, pc + size)):
                raise ValueError(f'{name}: overlapping or truncated instruction at {pc:04X}')
            for p in range(pc, pc + size):
                occupied[p] = pc
            rows[pc] = {'pc': pc, 'page': page, 'file_offset': offset(pc),
                        'bytes': raw[:size].hex(), 'mnemonic': mnemonic, 'operands': body}
            successors = []
            control = mnemonic.startswith('J') or mnemonic in ('SJMP', 'LJMP', 'SCALL', 'LCALL', 'DJNZ', 'DJNZW')
            if control:
                target = re.search(r'(?:^|,\s*)(-?0x[0-9a-fA-F]+)$', body)
                if target:
                    # SLEIGH may display 0x14000 for a wrapped 16-bit LCALL.
                    successors.append(('call' if mnemonic.endswith('CALL') else 'branch', int(target[1], 16) & 0xffff))
                else:
                    edges.append({'from': pc, 'to': None, 'kind': 'indirect', 'resolved': False})
            terminal = mnemonic in ('RET', 'RETI', 'TRAP', 'RST', 'SJMP', 'LJMP', 'BR', 'JMP')
            if mnemonic == 'BR':
                annotation = indirect.get(pc)
                if annotation:
                    if not annotation.get('evidence'):
                        raise ValueError('Indirect targets require evidence')
                    successors += [('annotated_indirect', number(t)) for t in annotation['targets']]
                    rows[pc]['target_evidence'] = annotation['evidence']
                    # Keep an unknown edge: annotation is not proof of exhaustive runtime values.
                edges.append({'from': pc, 'to': None, 'kind': 'indirect_other_values', 'resolved': False})
            if not terminal:
                successors.append(('fallthrough', (pc + size) & 0xffff))
            boundary = fetch_mapping_write(pc, mnemonic, body)
            if pc in stops or boundary:
                if pc in stops and not stops[pc]:
                    raise ValueError('Mapping boundary requires evidence')
                successors = []
                rows[pc]['mapping_boundary'] = stops.get(pc, boundary)
                edges.append({'from': pc, 'to': None, 'kind': 'mapping_boundary', 'resolved': False})
            for kind, target in successors:
                resolved = start <= target < end
                edges.append({'from': pc, 'to': target, 'kind': kind, 'resolved': resolved})
                if resolved and target not in rows:
                    todo.append(target)
        unknown = []
        for p in range(start, end):
            if p not in occupied:
                if unknown and unknown[-1][1] == p:
                    unknown[-1][1] = p + 1
                else:
                    unknown.append([p, p + 1])
        result['regions'].append({'name': name, 'page': page, 'start': start, 'end': end,
                                  'evidence': region['evidence'], 'instructions': [rows[p] for p in sorted(rows)],
                                  'entries': entries, 'summary': region.get('summary', []),
                                  'edges': edges, 'undecoded_ranges': unknown, 'warnings': warnings})
    by_name = {r['name']: r for r in result['regions']}
    result['bank_links'] = []
    for link in manifest.get('bank_links', []):
        source, target = by_name[link['source']], by_name[link['target']]
        pc, dest = number(link['pc']), number(link['destination'])
        if not link.get('evidence') or not link.get('context'):
            raise ValueError('Bank links require evidence and context')
        matches = [e for e in source['edges'] if e['from'] == pc and e['to'] == dest and not e['resolved']]
        if len(matches) != 1 or not any(i['pc'] == dest for i in target['instructions']):
            raise ValueError('Bank link must connect a decoded edge to an instruction boundary')
        # Keep the original unresolved edge: this link is qualified by context,
        # not an unconditional proof for every possible invocation of a routine.
        result['bank_links'].append(dict(link, pc=pc, destination=dest, target_page=target['page']))
    for r in result['regions']:
        r['blocks'] = basic_blocks(r)
    result['data_regions'] = []
    for item in manifest.get('data_regions', []):
        start, end = number(item['file_start']), number(item['file_end'])
        if not 0 <= start < end <= len(data) or not item.get('evidence'):
            raise ValueError('Invalid evidenced data region')
        for region in result['regions']:
            for row in region['instructions']:
                a = row['file_offset']
                if a < end and a + len(bytes.fromhex(row['bytes'])) > start:
                    raise ValueError('Data region overlaps decoded instruction')
        result['data_regions'].append(dict(item, file_start=start, file_end=end,
                                           sha256=hashlib.sha256(data[start:end]).hexdigest()))
    check_global_boundaries(result['regions'])
    return result


def check_global_boundaries(regions):
    """Enforce that instruction boundaries across all regions do not conflict (BUG-087)."""
    inst_by_start = {}
    byte_owner = {}
    for region in regions:
        if region.get('warnings'):
            raise ValueError(f"Region {region['name']} has decode warnings: {region['warnings']}")
        for ins in region['instructions']:
            fo = ins['file_offset']
            sz = len(bytes.fromhex(ins['bytes']))
            b_bytes = ins['bytes']
            if fo in inst_by_start:
                prev_sz, prev_bytes, prev_r = inst_by_start[fo]
                if sz != prev_sz or b_bytes != prev_bytes:
                    raise ValueError(
                        f"Global boundary conflict at file 0x{fo:04X}: "
                        f"{region['name']} ({sz} bytes) disagrees with {prev_r} ({prev_sz} bytes)"
                    )
            else:
                if fo in byte_owner:
                    owner_fo, owner_sz, owner_r = byte_owner[fo]
                    if fo != owner_fo:
                        raise ValueError(
                            f"Global boundary conflict at file 0x{fo:04X}: "
                            f"{region['name']} starts inside {owner_r} instruction (0x{owner_fo:04X}+{owner_sz})"
                        )
                inst_by_start[fo] = (sz, b_bytes, region['name'])
                for b in range(fo, fo + sz):
                    if b in byte_owner:
                        owner_fo, owner_sz, owner_r = byte_owner[b]
                        if owner_fo != fo:
                            raise ValueError(
                                f"Global boundary conflict at file 0x{b:04X}: "
                                f"{region['name']} (0x{fo:04X}+{sz}) overlaps {owner_r} (0x{owner_fo:04X}+{owner_sz})"
                            )
                    else:
                        byte_owner[b] = (fo, sz, region['name'])


def basic_blocks(region):
    """Split at branch targets, calls and discontinuities; preserve edge kinds."""
    rows = region['instructions']
    outgoing = {}
    for edge in region['edges']:
        outgoing.setdefault(edge['from'], []).append(edge)
    leaders = set(region['entries'])
    for edge in region['edges']:
        if edge['resolved'] and edge['kind'] != 'fallthrough':
            leaders.add(edge['to'])
    blocks, current = [], []
    for row in rows:
        if current and (row['pc'] in leaders or current[-1]['pc'] + len(bytes.fromhex(current[-1]['bytes'])) != row['pc']):
            blocks.append(current)
            current = []
        current.append(row)
        edges = outgoing.get(row['pc'], [])
        if len(edges) != 1 or edges[0]['kind'] != 'fallthrough' or not edges[0]['resolved']:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return [{'start': b[0]['pc'], 'instructions': [i['pc'] for i in b],
             'exits': outgoing.get(b[-1]['pc'], [])} for b in blocks]


def write_views(result, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    lines = ['# Firmware routine analysis', '', result['scope'], '',
             'Assembly and instruction-flow views only. Register names are decoder labels, not recovered source names.',
             'Calls have assumed return edges; bank changes and data aliases require manual analysis.', '']
    lines += ['## Context-qualified bank links', '', 'These links apply only in the stated context; original unknown edges are retained.', '']
    for link in result['bank_links']:
        lines.append(f"- {link['source']}:{link['pc']:04X} → {link['target']} ({link['target_page']:04X}:{link['destination']:04X}). Context: {link['context']}. Evidence: {link['evidence']}")
    lines.append('')
    for r in result['regions']:
        if r['summary']:
            lines += ['## ' + r['name'] + ' — research summary', '', 'Maintained interpretation, not automatically decompiled source:', '']
            lines += ['- ' + item for item in r['summary']]
            lines.append('')
        lines += ['## ' + r['name'], '', r['evidence'], '', '```text']
        for i in r['instructions']:
            lines.append(f"{i['page']:04X}:{i['pc']:04X} file={i['file_offset']:06X} {i['bytes']:<16} {i['mnemonic']} {i['operands']}")
        lines += ['```', '', 'Unresolved edges (destination bank is not assumed):', '']
        for e in r['edges']:
            if not e['resolved']:
                target = 'indirect' if e['to'] is None else f"{e['to']:04X}"
                lines.append(f"- {e['from']:04X} → {target}: {e['kind']}")
        lines += ['', 'Undecoded ranges: ' + str(r['undecoded_ranges']), '', 'Warnings: ' + str(r['warnings']), '']
        dot = ['digraph routine {']
        for i in r['instructions']:
            label = f"{i['pc']:04X}: {i['mnemonic']} {i['operands']}"
            dot.append(f"n{i['pc']} [label={json.dumps(label)}];")
        for e in r['edges']:
            if e['to'] is not None:
                dot.append(f"n{e['from']} -> n{e['to']} [label={json.dumps(e['kind'])}, style={'solid' if e['resolved'] else 'dashed'}];")
        dot.append('}')
        (output / (r['name'] + '.dot')).write_text('\n'.join(dot) + '\n', encoding='utf-8')
        block_for = {pc: b['start'] for b in r['blocks'] for pc in b['instructions']}
        instructions = {i['pc']: i for i in r['instructions']}
        dot = ['digraph blocks {', 'node [shape=box];']
        for block in r['blocks']:
            label = '\n'.join(f"{pc:04X}: {instructions[pc]['mnemonic']} {instructions[pc]['operands']}" for pc in block['instructions'])
            dot.append(f"b{block['start']} [label={json.dumps(label)}];")
            for edge in block['exits']:
                if edge['to'] is not None:
                    dest = 'b' + str(block_for[edge['to']]) if edge['resolved'] else 'external_' + str(edge['to'])
                    dot.append(f"b{block['start']} -> {dest} [label={json.dumps(edge['kind'])}];")
                else:
                    dot.append(f"b{block['start']} -> unknown_{edge['from']} [style=dashed];")
        dot.append('}')
        (output / (r['name'] + '.blocks.dot')).write_text('\n'.join(dot) + '\n', encoding='utf-8')
    (output / 'routines.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Never allow generated views to replace either input.
    for source in (args.image, args.manifest):
        if source.resolve().is_relative_to(args.output.resolve()):
            raise ValueError('Output directory must not contain either input')
    result = analyze(args.image.read_bytes(), json.loads(args.manifest.read_text(encoding='utf-8')))
    write_views(result, args.output)
    print(json.dumps({r['name']: {'instructions': len(r['instructions']), 'unresolved': sum(not e['resolved'] for e in r['edges']), 'warnings': len(r['warnings'])} for r in result['regions']}, indent=2))


if __name__ == '__main__':
    main()
