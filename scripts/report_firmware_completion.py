"""Generate OS and combined functional-scope acceptance, separate from bytes."""
from pathlib import Path
import argparse
import hashlib
import json
from report_ic15_completion import assess as assess_rom, SCOPE as ROM_SCOPE

ROOT = Path(__file__).resolve().parents[1]
OS_SCOPE = ROOT / 'docs/condensed/validation/os-completion-scope-v1.json'
OS_IDS = {'startup', 'kernel_dispatch', 'midi_parser', 'voice_lifecycle', 'controllers',
          'sysex_framing', 'transfer_lifecycle', 'field_packing', 'sample_transfer_helpers',
          'scsi_session', 'scsi_target', 'fdc_startup', 'media_persistence', 'eeprom',
          'audio_init', 'synthesis', 'ui_event_ring', 'screen_loader', 'selection_callbacks',
          'display_screens', 'input_devices', 'object_hierarchy', 'sampling_editing', 'unknown_payload'}


def assess_os(scope, root=ROOT):
    gates = ['context', 'layout', 'behavior', 'execution']
    paths = scope['paths']
    if (scope['rubric_version'] != 's760-os-decoding-v1' or scope['gates'] != gates
            or len(paths) != len(OS_IDS) or {p['id'] for p in paths} != OS_IDS):
        raise ValueError('OS v1 scope change requires a versioned amendment')
    digest = hashlib.sha256((root / 'S760224.IMG').read_bytes()).hexdigest()
    if digest != scope['input_sha256']:
        raise ValueError('OS input identity differs')
    coverage = json.loads((root / 'docs/condensed/validation/os-exploration-coverage-2026-10-16.json').read_text())
    if coverage['input_sha256'] != digest:
        raise ValueError('OS inventory identity differs')
    counts, hashes = dict.fromkeys(gates, 0), {}
    for path in paths:
        if set(path['gates']) != set(gates) or not path.get('scope') or not path.get('evidence'):
            raise ValueError('Each OS path requires criteria and evidence')
        for relative in path['evidence']:
            source = (root / relative).resolve()
            if not source.is_relative_to(root.resolve()) or not source.is_file():
                raise ValueError('Missing or invalid evidence: ' + relative)
            raw = source.read_bytes()
            json.loads(raw)
            hashes[relative] = hashlib.sha256(raw).hexdigest()
        for gate in gates:
            record = path['gates'][gate]
            if record['status'] not in ('passed', 'open', 'blocked') or not record.get('acceptance'):
                raise ValueError('OS gates require binary status and criteria')
            counts[gate] += record['status'] == 'passed'
        if path['id'] == 'unknown_payload' and coverage['unclassified_bytes']:
            if any(g['status'] == 'passed' for g in path['gates'].values()):
                raise ValueError('Unclassified payload cannot earn catch-all completion credit')
    earned, total = sum(counts.values()), len(paths) * len(gates)
    return dict(rubric_version=scope['rubric_version'], passed_gates=earned, total_gates=total,
                percent=100 * earned / total, gate_counts=counts, path_count=len(paths),
                evidence_sha256=hashes,
                scope_sha256=hashlib.sha256(json.dumps(scope, sort_keys=True).encode()).hexdigest())


def combine(rom, os):
    earned, total = rom['passed_gates'] + os['passed_gates'], rom['total_gates'] + os['total_gates']
    return dict(rubric_version='s760-functional-acceptance-v1', passed_gates=earned, total_gates=total,
                percent=100 * earned / total,
                formula='(ROM passed gates + OS passed gates) / (ROM gates + OS gates); not an average of percentages or byte coverage',
                limitation='Published scope acceptance only. Equal gates do not weight code size, effort, uncertainty or hardware fidelity.')


def report(scope, rom, os, combined):
    lines = ['# Firmware functional-scope acceptance', '',
             f"**Combined checklist: {combined['passed_gates']}/{combined['total_gates']} = {combined['percent']:.2f}%.**",
             f"Boot ROM: {rom['passed_gates']}/{rom['total_gates']} = {rom['percent']:.2f}%. OS: {os['passed_gates']}/{os['total_gates']} = {os['percent']:.2f}%.", '',
             'These are binary acceptance gates against versioned scopes, not estimates of effort remaining or percentage of source understood. The combination counts gates directly; it does not average byte coverage or give every subsystem an assumed share of engineering cost.', '',
             'The OS scope has24 bounded contracts/families, including broad unmapped families and an explicit catch-all for every unclassified region or unassigned function. Passing a local MIDI parser does not pass the whole MIDI/voice system. Native playback, UI tests, physical captures and ROM tests do not automatically qualify unrelated OS routines. The historical81/33-row catalogues remain unverified; their addresses and badges were not credited.', '',
             '| OS contract/family | Context | Layout | Behavior | Execution |', '| --- | --- | --- | --- | --- |']
    for path in scope['paths']:
        source = path['evidence'][0].removeprefix('docs/')
        states = ['Pass' if path['gates'][g]['status'] == 'passed' else 'Open' for g in scope['gates']]
        lines.append(f"| [{path['title']}]({source}) | " + ' | '.join(states) + ' |')
    lines += ['', '## Open acceptance work', '']
    lines.extend(f"- **{p['title']}:** {p['remaining']}" for p in scope['paths'] if any(g['status'] != 'passed' for g in p['gates'].values()))
    lines += ['', '## Interpretation and stable updates', '', scope['scope_change_policy'], '',
              'The unknown-payload family cannot earn credit while unclassified bytes remain. Newly discovered behavior is assigned explicitly; it is never silently omitted to preserve a high score. The current scope is a reviewable v1 functional plan, not a proven exhaustive feature taxonomy. A fuller feature inventory can require a versioned amendment. Hardware parity and source/rebuild acceptance stay separate.', '',
              '**Overall semantic decoding completion or effort remaining: not yet quantifiable.** The checklists now give a reproducible, narrower acceptance measure; they do not supply defensible effort weights or establish that all runtime roots are known.', '',
              '[Boot-ROM matrix](ic15-completion-matrix.md) · [OS criteria and evidence](condensed/validation/os-completion-scope-v1.json) · [Generated scores](condensed/validation/firmware-completion-score-v1-2026-10-16.json)', '',
              'Reproduce: `python scripts/report_firmware_completion.py --check`. The script verifies scope shape, input identities, inventory/evidence files and arithmetic; evidence judgments remain explicit manual assessments.', '']
    for target, label in [('os', 'OS'), ('boot_rom', 'ROM')]:
        m = rom['metrics'][target]
        lines.append(f"{label} classified-byte coverage: **{m['classified_bytes']:,}/{m['total_bytes']:,} = {m['percent']:.2f}%** (+0.00 percentage points in this scoring pass).")
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    scope = json.loads(OS_SCOPE.read_text(encoding='utf-8'))
    rom = assess_rom(json.loads(ROM_SCOPE.read_text(encoding='utf-8')))
    os = assess_os(scope)
    combined = combine(rom, os)
    result = dict(rom=rom, os=os, combined=combined, initial_baseline=True,
                  overall_semantic_decoding_completion='not yet quantifiable',
                  initial_score_delta=None, byte_coverage_percentage_point_change=dict(os=0, boot_rom=0))
    outputs = {ROOT / 'docs/firmware/firmware-completion-matrix.md': report(scope, rom, os, combined),
               ROOT / 'docs/condensed/validation/firmware-completion-score-v1-2026-10-16.json': json.dumps(result, indent=2) + '\n'}
    for path, text in outputs.items():
        if args.check:
            if path.read_text(encoding='utf-8') != text:
                raise ValueError('Generated firmware score is stale: ' + str(path))
        else:
            path.write_text(text, encoding='utf-8')
    print(json.dumps(dict(rom=rom['percent'], os=os['percent'], combined=combined)))


if __name__ == '__main__':
    main()
