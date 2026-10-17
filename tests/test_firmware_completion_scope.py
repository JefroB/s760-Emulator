"""Guard OS scope coverage and the combined gate denominator."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('firmware_completion', ROOT / 'scripts/report_firmware_completion.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture(autouse=True)
def synthetic_inputs(synthetic_completion_root, monkeypatch):
    from functools import partial
    monkeypatch.setattr(module, 'assess_os', partial(module.assess_os, root=synthetic_completion_root))
    monkeypatch.setattr(module, 'OS_SCOPE',
                        synthetic_completion_root / 'docs/condensed/validation/os-completion-scope-v1.json')


def scope():
    return json.loads(module.OS_SCOPE.read_text(encoding='utf-8'))


def test_unmapped_family_cannot_be_dropped_from_denominator():
    value = scope()
    value['paths'] = [p for p in value['paths'] if p['id'] != 'sampling_editing']
    with pytest.raises(ValueError, match='versioned amendment'):
        module.assess_os(value)


def test_unknown_payload_cannot_be_marked_complete_while_bytes_are_unknown():
    value = scope()
    next(p for p in value['paths'] if p['id'] == 'unknown_payload')['gates']['layout']['status'] = 'passed'
    with pytest.raises(ValueError, match='Unclassified payload'):
        module.assess_os(value)


def test_combined_score_counts_gates_instead_of_averaging_percentages():
    score = module.combine(dict(passed_gates=5, total_gates=6), dict(passed_gates=1, total_gates=10))
    assert score['passed_gates'] == 6 and score['total_gates'] == 16
    assert score['percent'] == 37.5
