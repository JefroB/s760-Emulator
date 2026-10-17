import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('bank_frontier', Path(__file__).parents[1] / 'scripts/firmware_bank_frontier.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(selector=0x104, target='0x87b5', page=0x166):
    rows = [dict(pc=0xc869, bytes='a166011c', mnemonic='LD', operands=f'RW1C, #{page:#x}'),
            dict(pc=0xc86d, bytes='c30104011c', mnemonic='ST', operands=f'RW1C, {selector:#x}, TABLE[ZR]'),
            dict(pc=0xc872, bytes='ef40bf', mnemonic='LCALL', operands=target)]
    edges = [dict(kind='fallthrough', resolved=True, **{'from': a, 'to': b})
             for a, b in [(0xc869, 0xc86d), (0xc86d, 0xc872)]]
    return dict(sha256='synthetic', regions=[dict(name='source', page=0, instructions=rows, edges=edges)])


def test_matches_mapping_and_distinguishes_known_target():
    data = fixture()
    row = module.candidates(data)['candidates'][0]
    assert (row['destination_page'], row['destination_pc'], row['destination_file_offset']) == (0x166, 0x87b5, 0x5e7b5)
    assert row['already_decoded_in'] == []
    data['regions'].append(dict(name='destination', page=0x166,
                               instructions=[dict(pc=0x87b5, bytes='f0', mnemonic='RET', operands='')], edges=[]))
    assert module.candidates(data)['candidates'][0]['already_decoded_in'] == ['destination']


def test_data_selector_and_other_fetch_window_do_not_qualify():
    assert not module.candidates(fixture(selector=0x10c))['candidates']
    assert not module.candidates(fixture(selector=0x102))['candidates']


def test_self_remap_does_not_follow_stale_call_bytes():
    assert not module.candidates(fixture(selector=0x106, target='0xce14'))['candidates']


def test_missing_fallthrough_or_different_register_rejected():
    data = fixture()
    data['regions'][0]['edges'].pop()
    assert not module.candidates(data)['candidates']
    data = fixture()
    data['regions'][0]['instructions'][1]['operands'] = 'RW20, 0x104, TABLE[ZR]'
    assert not module.candidates(data)['candidates']


def test_signed_or_wrapped_destination_normalized():
    for target in ('-0x784b', '0x187b5'):
        assert module.candidates(fixture(target=target))['candidates'][0]['destination_pc'] == 0x87b5


def test_outside_payload_rejected():
    assert not module.candidates(fixture(page=0xffff))['candidates']


def test_rom_input_does_not_silently_use_os_formula():
    data = fixture()
    data['mapping'] = {'kind': 'mirrored_rom'}
    with pytest.raises(ValueError, match='OS payload mapping'):
        module.candidates(data)
