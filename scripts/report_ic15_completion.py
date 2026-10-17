"""Generate reproducible acceptance metrics from the versioned IC15 scope."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / 'docs/condensed/validation/ic15-completion-scope-v1.json'
V1_PATH_IDS = {'reset', 'floppy_load', 'floppy_failure', 'scsi_command', 'scsi_payload',
               'setup', 'eeprom', 'display', 'audio', 'ram_diagnostic', 'monitor',
               'fdc_irq', 'aux_irq', 'residual_helpers', 'resource_ownership'}


def assess(scope, root=ROOT):
    gates = scope['gates']
    if gates != ['context', 'layout', 'behavior', 'execution']:
        raise ValueError('Unexpected rubric gates; version the rubric explicitly')
    if not scope['paths'] or len({p['id'] for p in scope['paths']}) != len(scope['paths']):
        raise ValueError('Scope must contain nonempty, uniquely identified paths')
    if scope['rubric_version'] != 'ic15-native-decoding-v1' or {p['id'] for p in scope['paths']} != V1_PATH_IDS:
        raise ValueError('Changing v1 scope requires an explicit versioned rubric amendment')
    rom = (root / 'roms/BOOT/Roland_S-760_v1.11.BIN').read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest != scope['input_sha256']:
        raise ValueError('ROM identity differs from scored scope')
    counts = {g: 0 for g in gates}
    evidence_hashes = {}
    for path in scope['paths']:
        if set(path['gates']) != set(gates) or not path.get('scope') or not path.get('evidence'):
            raise ValueError('Every path requires all gates, scope and evidence')
        for relative in path['evidence']:
            source = (root / relative).resolve()
            if not source.is_relative_to(root.resolve()) or not source.is_file():
                raise ValueError('Missing or out-of-workspace evidence: ' + relative)
            raw = source.read_bytes()
            json.loads(raw)
            evidence_hashes[relative] = hashlib.sha256(raw).hexdigest()
        for gate in gates:
            record = path['gates'][gate]
            if record['status'] not in ('passed', 'open', 'blocked') or not record.get('acceptance'):
                raise ValueError('Gate requires a binary status and explicit acceptance criterion')
            counts[gate] += record['status'] == 'passed'
    metrics = {}
    for target, filename in [('boot_rom', 'ic15'), ('os', 'os')]:
        inventory = json.loads((root / f'docs/condensed/validation/{filename}-exploration-coverage-2026-10-16.json').read_text())
        total = inventory['payload_end'] - inventory['payload_start']
        classified = inventory['decoded_unique_bytes'] + inventory['identified_data_bytes']
        if not 0 <= classified <= total:
            raise ValueError('Invalid inventory denominator')
        metrics[target] = dict(classified_bytes=classified, total_bytes=total,
                               percent=100 * classified / total, input_sha256=inventory['input_sha256'])
        if target == 'boot_rom':
            if inventory['input_sha256'] != digest or total != len(rom):
                raise ValueError('ROM inventory identity/extent differs')
            unknown = [i for start, end in inventory['unclassified_ranges'] for i in range(start, end)]
            unused = sum(rom[i] == 255 for i in unknown)
            if scope['assumptions'][0]['bytes'] != unused:
                raise ValueError('Presumed unused-space assumption differs from current inventory')
            metrics[target].update(presumed_unused_bytes=unused,
                                   accounted_including_assumption_bytes=classified + unused,
                                   unresolved_other_bytes=len(unknown) - unused)
    earned, possible = sum(counts.values()), len(scope['paths']) * len(gates)
    return dict(rubric_version=scope['rubric_version'], score_name=scope['score_name'],
                passed_gates=earned, total_gates=possible, percent=100 * earned / possible,
                gate_counts=counts, path_count=len(scope['paths']), metrics=metrics,
                scope_sha256=hashlib.sha256(json.dumps(scope, sort_keys=True).encode()).hexdigest(),
                evidence_sha256=evidence_hashes,
                overall_firmware_decoding_completion='not yet quantifiable',
                limitation='Acceptance against this fixed boot-ROM scope; not effort remaining, overall firmware completion, hardware fidelity or rebuild acceptance.')


def markdown(scope, result):
    lines = ['# Boot-ROM completion scope and score', '',
             f"**{result['score_name']}: {result['passed_gates']}/{result['total_gates']} gates = {result['percent']:.2f}%.**",
             '', 'This measures acceptance against the published IC15 v1 functional scope. It is not a percentage of effort completed or time remaining. Each of15 paths has four binary gates; open or blocked gates earn zero. Evidence is assessed manually against explicit criteria, then totals are generated. A linked report alone does not mechanically prove a gate.', '',
             '| Gate | Acceptance rule | Passed |', '| --- | --- | --- |']
    for gate in scope['gates']:
        lines.append(f"| {gate.title()} | {scope['gate_definitions'][gate]} | {result['gate_counts'][gate]}/{result['path_count']} |")
    lines += ['', '| Functional path | Context | Layout | Behavior | Execution |', '| --- | --- | --- | --- | --- |']
    for path in scope['paths']:
        source = path['evidence'][0].removeprefix('docs/')
        statuses = ['Pass' if path['gates'][g]['status'] == 'passed' else 'Open' for g in scope['gates']]
        lines.append(f"| [{path['title']}]({source}) | " + ' | '.join(statuses) + ' |')
    lines += ['', '## What remains', '']
    for path in scope['paths']:
        remaining = [path['gates'][g]['acceptance'] for g in scope['gates'] if path['gates'][g]['status'] != 'passed']
        if remaining:
            lines.append(f"- **{path['title']}:** " + ' '.join(remaining))
    lines += ['', '## Byte accounting and separate acceptance gates', '']
    for name, label in [('boot_rom', 'Boot ROM'), ('os', 'OS')]:
        m = result['metrics'][name]
        lines.append(f"{label} evidence-backed classified-byte coverage: **{m['classified_bytes']:,}/{m['total_bytes']:,} = {m['percent']:.2f}%**. This scoring pass adds no bytes (+0.00 percentage points).")
        lines.append('')
    rom = result['metrics']['boot_rom']
    lines += [f"User-accepted presumed unused FF space: {rom['presumed_unused_bytes']:,} bytes. Including that assumption accounts for {rom['accounted_including_assumption_bytes']:,}/{rom['total_bytes']:,} bytes; {rom['unresolved_other_bytes']} other byte remains provisional. The FF assumption does not prove padding, and preserving those bytes remains required.", '',
              '**Overall OS-plus-ROM decoding completion: not yet quantifiable.** The OS needs its own subsystem scope before a combined measure is defensible. No averaging the ROM score with OS byte coverage.', '',
              'The following are outside this score and remain independently required for their respective claims:', '']
    lines.extend('- ' + item for item in scope['separate_unscored_requirements'])
    lines += ['', '## Stable updates', '', scope['scope_change_policy'], '',
              'A gate changes to Pass only when its stated acceptance criterion is met with evidence and limitations recorded. Regressions can reopen passed gates. Preserve previous score snapshots and report deltas against the same rubric version. At100% this means all60 v1 gates passed, not that physical parity or the editable toolchain is complete.', '',
              '[Machine-readable criteria, statuses and evidence](condensed/validation/ic15-completion-scope-v1.json) · [Generated score and evidence hashes](condensed/validation/ic15-completion-score-v1-2026-10-16.json)', '',
              'Reproduce: `python scripts/report_ic15_completion.py`. It verifies input identity, current byte inventories, scope shape and evidence-file existence/JSON before generating totals. It does not independently re-prove the semantic conclusions in those evidence files.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate and compare generated outputs without writing')
    args = parser.parse_args()
    scope = json.loads(SCOPE.read_text(encoding='utf-8'))
    result = assess(scope)
    outputs = {ROOT / 'docs/firmware/boot-rom/ic15-completion-matrix.md': markdown(scope, result),
               ROOT / 'docs/condensed/validation/ic15-completion-score-v1-2026-10-16.json': json.dumps(result, indent=2) + '\n'}
    for path, text in outputs.items():
        if args.check:
            if path.read_text(encoding='utf-8') != text:
                raise ValueError('Generated report is stale: ' + str(path))
        else:
            path.write_text(text, encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['rubric_version', 'passed_gates', 'total_gates', 'percent', 'gate_counts']}))


if __name__ == '__main__':
    main()
