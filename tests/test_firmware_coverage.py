import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('coverage_inventory', Path(__file__).parents[1] / 'scripts/firmware_coverage.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    row = dict(file_offset=12, bytes='aabb', mnemonic='NOP', operands='')
    return dict(sha256='fixture', regions=[dict(name='a', page=0, instructions=[row], edges=[]),
                                         dict(name='b', page=1, instructions=[dict(row)], edges=[])])


def test_aliases_count_once_and_unknown_ranges_partition():
    result = module.inventory(fixture(), 10, 20)
    assert result['decoded_unique_bytes'] == 2
    assert result['unique_instruction_encodings'] == 1
    assert result['unclassified_ranges'] == [[10, 12], [14, 20]]
    assert result['unclassified_bytes'] == 8


def test_does_not_assign_callers_bank_to_unknown_destination():
    data = fixture()
    data['regions'][0]['edges'] = [dict(resolved=False, to=0x8000, kind='call')]
    assert module.inventory(data, 10, 20)['unresolved_edges'][0]['destination_page'] is None


def test_out_of_payload_is_rejected():
    with pytest.raises(ValueError, match='outside payload'):
        module.inventory(fixture(), 13, 20)


def test_evidenced_data_is_counted_separately():
    data = fixture()
    data['data_regions'] = [dict(file_start=16, file_end=18)]
    result = module.inventory(data, 10, 20)
    assert result['identified_data_bytes'] == 2
    assert result['unclassified_bytes'] == 6


def test_code_data_conflict_is_rejected():
    data = fixture()
    data['data_regions'] = [dict(file_start=12, file_end=14)]
    with pytest.raises(ValueError, match='conflict'):
        module.inventory(data, 10, 20)
