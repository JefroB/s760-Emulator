"""Protect the published completion denominator and evidence requirements."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ic15_completion', ROOT / 'scripts/report_ic15_completion.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture(autouse=True)
def synthetic_inputs(synthetic_completion_root, monkeypatch):
    from functools import partial
    monkeypatch.setattr(module, 'assess', partial(module.assess, root=synthetic_completion_root))
    monkeypatch.setattr(module, 'SCOPE',
                        synthetic_completion_root / 'docs/condensed/validation/ic15-completion-scope-v1.json')


def scope():
    return json.loads(module.SCOPE.read_text(encoding='utf-8'))


def test_cannot_improve_score_by_removing_unfinished_path():
    value = scope()
    value['paths'] = [p for p in value['paths'] if p['id'] != 'scsi_payload']
    with pytest.raises(ValueError, match='versioned rubric'):
        module.assess(value)


def test_missing_evidence_cannot_support_passed_path():
    value = scope()
    value['paths'][0]['evidence'] = ['docs/condensed/validation/nonexistent-completion-evidence.json']
    with pytest.raises(ValueError, match='Missing or out-of-workspace evidence'):
        module.assess(value)


def test_partial_credit_is_rejected_and_blocking_does_not_change_score():
    value = scope()
    entry = next(p for p in value['paths'] if p['id'] == 'scsi_payload')
    invalid = copy.deepcopy(value)
    next(p for p in invalid['paths'] if p['id'] == 'scsi_payload')['gates']['execution']['status'] = 'half'
    with pytest.raises(ValueError, match='binary status'):
        module.assess(invalid)
    before = module.assess(value)
    entry['gates']['execution']['status'] = 'blocked'
    after = module.assess(value)
    assert (before['passed_gates'], before['total_gates']) == (after['passed_gates'], after['total_gates'])
