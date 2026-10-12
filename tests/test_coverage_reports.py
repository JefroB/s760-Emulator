"""Published reports must not turn a catalogue or a model test into parity."""
import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPORTS = [
    ('generate_coverage_matrix', 'OUTPUT_MD_PATH'),
    ('generate_exhaustive_matrix', 'OUTPUT_PATH'),
    ('generate_ui_coverage_matrix', 'OUTPUT_PATH'),
    ('generate_manual_coverage_matrix', 'OUTPUT_PATH'),
]


@pytest.mark.parametrize('module,output', REPORTS)
def test_reports_do_not_promote_legacy_claims(module, output, tmp_path, monkeypatch):
    generator = importlib.import_module('scripts.' + module)
    published = ROOT / getattr(generator, output)
    destination = tmp_path / 'report.md'
    monkeypatch.setattr(generator, output, str(destination))
    generator.generate_markdown()
    text = destination.read_text(encoding='utf-8')
    assert text == published.read_text(encoding='utf-8'), 'Regenerate the committed report'
    assert 'Unverified inventory' in text
    assert 'No coverage percentage' in text
    for claim in ('✅ Tested', '100.0%', '53 / 53', 'no automated test tooling yet',
                  'fully automated', 'Pixel-Perfect VDP Layout Parity'):
        assert claim not in text
    assert 'Image bytes' in text
    assert 'Static source' in text
    assert 'React component' in text
    assert 'mocked transport' in text
    # Output must be deterministic and never silently consult a local passing run.
    generator.generate_markdown()
    assert destination.read_text(encoding='utf-8') == text


def test_evidence_references_resolve_and_describe_scope():
    from scripts.coverage_report import EVIDENCE
    for layer, reference, assertion, limitation in EVIDENCE:
        path, selector = reference.split('::', 1)
        assert (ROOT / path).is_file()
        assert selector in (ROOT / path).read_text(encoding='utf-8')
        assert layer and assertion and limitation
