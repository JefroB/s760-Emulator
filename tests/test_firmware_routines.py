"""Synthetic instruction fixtures; no proprietary firmware required."""
import hashlib
import importlib.util
from pathlib import Path

import pytest

pytest.importorskip('pypcode')
spec = importlib.util.spec_from_file_location('firmware_analysis', Path(__file__).parents[1] / 'scripts/analyze_firmware_routines.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(code, start=0x4000):
    data = bytes(code)
    manifest = {'sha256': hashlib.sha256(data).hexdigest(), 'payload_offset': 0,
                'regions': [{'name': 'test', 'page': 0, 'start': start, 'end': start + len(data),
                             'entries': [start], 'evidence': 'Synthetic fixture'}]}
    return data, manifest


def test_jump_skips_data_and_return_stops():
    data, manifest = fixture([0x20, 0x02, 0xff, 0xff, 0xf0])
    r = module.analyze(data, manifest)['regions'][0]
    assert [i['pc'] for i in r['instructions']] == [0x4000, 0x4004]
    assert r['undecoded_ranges'] == [[0x4002, 0x4004]]


def test_hash_rejected():
    data, manifest = fixture([0xf0])
    with pytest.raises(ValueError, match='SHA256'):
        module.analyze(data + b'X', manifest)


def rom_fixture(page=0x780):
    data = bytearray(0x8000)
    data[0x2080] = 0xf0
    manifest = {'sha256': hashlib.sha256(data).hexdigest(),
                'mapping': {'kind': 'mirrored_rom', 'mirror_size': 0x8000,
                            'physical_aperture': [0x1e0000, 0x200000]},
                'regions': [dict(name='rom', page=page, start=0x2080, end=0x2081,
                                 entries=[0x2080], evidence='Synthetic mirrored reset alias')]}
    return bytes(data), manifest


def test_rom_aliases_resolve_identical_bytes():
    for page in (0x780, 0x7a0, 0x7c0, 0x7e0):
        data, manifest = rom_fixture(page)
        row = module.analyze(data, manifest)['regions'][0]['instructions'][0]
        assert row['file_offset'] == 0x2080
        assert row['mnemonic'] == 'RET'


def test_rom_rejects_non_aperture_page():
    data, manifest = rom_fixture(0)
    with pytest.raises(ValueError, match='outside ROM aperture'):
        module.analyze(data, manifest)


def test_rom_rejects_wrap_within_region():
    data, manifest = rom_fixture(0x79f)
    manifest['regions'][0].update(start=0, end=0x1000, entries=[0])
    with pytest.raises(ValueError, match='mirror boundary'):
        module.analyze(data, manifest)


def test_rom_rejects_wrong_mirror_size():
    data, manifest = rom_fixture()
    manifest['mapping']['mirror_size'] = 0x4000
    with pytest.raises(ValueError, match='mirror size'):
        module.analyze(data, manifest)


@pytest.mark.parametrize('code', [
    [0xc3, 1, 2, 1, 0x20],  # ST RW20,0102
    [0xc7, 1, 3, 1, 0x20],  # STB R20,0103 (selector high byte)
    [0xcf, 1, 2, 1],        # POP0102
    [0xc3, 1, 1, 1, 0x20],  # Unaligned word overlaps0102
])
def test_self_selector_write_stops_without_annotation(code):
    data, manifest = fixture(code + [0xf0])
    region = module.analyze(data, manifest)['regions'][0]
    assert len(region['instructions']) == 1
    assert region['edges'] == [{'from': 0x4000, 'to': None, 'kind': 'mapping_boundary', 'resolved': False}]


def test_other_window_and_data_selector_do_not_stop():
    for selector in (0x104, 0x10a):
        data, manifest = fixture([0xc3, 1, selector & 255, selector >> 8, 0x20, 0xf0])
        region = module.analyze(data, manifest)['regions'][0]
        assert region['instructions'][-1]['mnemonic'] == 'RET'


def test_indirect_selector_like_offset_does_not_claim_absolute_write():
    assert module.fetch_mapping_write(0x4000, 'ST', 'RW20, 0x102, TABLE[RW22]') is None


def test_call_wraps_and_does_not_invent_destination_bank():
    # CB25 + 3 + 74D8 = 14000, wraps to 4000.
    data = bytes(0xb25) + bytes([0xef, 0xd8, 0x74, 0xf0])
    _, manifest = fixture([0xf0])
    manifest['sha256'] = hashlib.sha256(data).hexdigest()
    manifest['regions'][0].update(start=0xcb25, end=0xcb29, entries=[0xcb25])
    r = module.analyze(data, manifest)['regions'][0]
    assert {'from': 0xcb25, 'to': 0x4000, 'kind': 'call', 'resolved': False} in r['edges']
    assert len(r['instructions']) == 2


def test_negative_displayed_call_target_wraps():
    # 4000 + 3 - 32768 = -3FFD, a direct CPU target C003.
    data, manifest = fixture([0xef, 0x00, 0x80, 0xf0])
    r = module.analyze(data, manifest)['regions'][0]
    assert {'from': 0x4000, 'to': 0xc003, 'kind': 'call', 'resolved': False} in r['edges']


def test_branch_into_instruction_rejected():
    data, manifest = fixture([0x27, 0xff])  # signed 11-bit -1: own displacement
    with pytest.raises(ValueError, match='enters an instruction'):
        module.analyze(data, manifest)


def test_distinct_pages_keep_distinct_bytes():
    data = b'\xf0' + bytes(1023) + b'\xfd'
    _, manifest = fixture([0xf0])
    manifest['sha256'] = hashlib.sha256(data).hexdigest()
    manifest['regions'].append(dict(manifest['regions'][0], name='other', page=1))
    rs = module.analyze(data, manifest)['regions']
    assert rs[0]['instructions'][0]['bytes'] == 'f0'
    assert rs[1]['instructions'][0]['bytes'] == 'fd'


def test_annotated_indirect_keeps_unknown_values():
    data, manifest = fixture([0xe3, 0x5c, 0xf0])
    manifest['regions'][0]['indirect_targets'] = {'0x4000': {'targets': ['0x4002'], 'evidence': 'Synthetic known target'}}
    r = module.analyze(data, manifest)['regions'][0]
    assert len(r['instructions']) == 2
    assert any(e['to'] is None and not e['resolved'] for e in r['edges'])


def test_cross_window_region_rejected():
    data, manifest = fixture([0xf0, 0xf0], start=0x7fff)
    with pytest.raises(ValueError, match='fetch window'):
        module.analyze(data, manifest)


def test_views_are_deterministic(tmp_path):
    data, manifest = fixture([0xf0])
    result = module.analyze(data, manifest)
    module.write_views(result, tmp_path)
    first = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    module.write_views(module.analyze(data, manifest), tmp_path)
    assert first == {p.name: p.read_bytes() for p in tmp_path.iterdir()}


def test_basic_blocks_split_conditional_and_join():
    data, manifest = fixture([0xdf, 0x01, 0xfd, 0xf0])
    r = module.analyze(data, manifest)['regions'][0]
    assert [b['instructions'] for b in r['blocks']] == [[0x4000], [0x4002], [0x4003]]


def test_mapping_boundary_does_not_decode_old_page_fallthrough():
    data, manifest = fixture([0xfd, 0xf0])
    manifest['regions'][0]['stop_after'] = {'0x4000': 'Synthetic bank transition'}
    r = module.analyze(data, manifest)['regions'][0]
    assert len(r['instructions']) == 1
    assert r['edges'] == [{'from': 0x4000, 'to': None, 'kind': 'mapping_boundary', 'resolved': False}]


def linked_fixture():
    data = bytes([0xef, 0xfd, 0x3f, 0xf0]) + bytes(1020) + bytes([0xf0])
    _, manifest = fixture([0xf0])
    manifest['sha256'] = hashlib.sha256(data).hexdigest()
    manifest['regions'][0]['end'] = 0x4004
    manifest['regions'].append(dict(name='callee', page=1, start=0x8000, end=0x8001, entries=[0x8000], evidence='fixture'))
    manifest['bank_links'] = [dict(source='test', pc=0x4000, target='callee', destination=0x8000,
                                   evidence='fixture selector', context='selector 0104=1')]
    return data, manifest


def test_bank_link_retains_context_and_unknown_edge():
    data, manifest = linked_fixture()
    r = module.analyze(data, manifest)
    assert r['bank_links'][0]['target_page'] == 1
    assert r['bank_links'][0]['context'] == 'selector 0104=1'
    assert any(e['to'] == 0x8000 and not e['resolved'] for e in r['regions'][0]['edges'])


@pytest.mark.parametrize('change', ['destination', 'context'])
def test_bad_bank_link_rejected(change):
    data, manifest = linked_fixture()
    manifest['bank_links'][0][change] = 0x8001 if change == 'destination' else ''
    with pytest.raises(ValueError, match='Bank link'):
        module.analyze(data, manifest)


def test_skip_length_is_two_bytes():
    # SKIP #0x12 (0x00, 0x12) followed by RET (0xF0)
    data, manifest = fixture([0x00, 0x12, 0xF0])
    r = module.analyze(data, manifest)['regions'][0]
    insns = r['instructions']
    assert len(insns) == 2
    assert insns[0]['mnemonic'] == 'SKIP'
    assert len(bytes.fromhex(insns[0]['bytes'])) == 2
    assert insns[1]['pc'] == 0x4002
    assert insns[1]['mnemonic'] == 'RET'


def test_idlpd_length_is_one_byte():
    # IDLPD (0xF6) followed by RET (0xF0)
    data, manifest = fixture([0xF6, 0xF0])
    r = module.analyze(data, manifest)['regions'][0]
    insns = r['instructions']
    assert len(insns) == 2
    assert insns[0]['mnemonic'] == 'IDLPD'
    assert len(bytes.fromhex(insns[0]['bytes'])) == 1
    assert insns[1]['pc'] == 0x4001
    assert insns[1]['mnemonic'] == 'RET'


def test_global_boundary_conflict_interior_start_rejected():
    # Region 1 has LCALL (3 bytes at 0x4000: 0xef, 0xfd, 0xff) -> occupies file 0..2
    # Region 2 starts at 0x4001 (file offset 1), inside Region 1's LCALL instruction
    data = bytes([0xef, 0xfd, 0xff, 0xf0, 0xf0])
    manifest = {
        'sha256': hashlib.sha256(data).hexdigest(),
        'payload_offset': 0,
        'regions': [
            {'name': 'reg1', 'page': 0, 'start': 0x4000, 'end': 0x4004, 'entries': [0x4000], 'evidence': 'synthetic'},
            {'name': 'reg2', 'page': 0, 'start': 0x4001, 'end': 0x4005, 'entries': [0x4001], 'evidence': 'synthetic'},
        ]
    }
    with pytest.raises(ValueError, match='Global boundary conflict'):
        module.analyze(data, manifest)


def test_global_boundary_conflict_different_length_rejected():
    # Region 1 has SKIP (2 bytes: 0x00, 0xf0) at file 0
    # Region 2 mapped to the same file offset has RET (1 byte: 0xf0) at file 0
    data = bytes([0x00, 0xf0, 0xf0, 0xf0])
    manifest = {
        'sha256': hashlib.sha256(data).hexdigest(),
        'payload_offset': 0,
        'regions': [
            {'name': 'reg1', 'page': 0, 'start': 0x4000, 'end': 0x4003, 'entries': [0x4000], 'evidence': 'synthetic'},
            # Mapping page 1 offset by -1024 or same offset with different length
            {'name': 'reg2', 'page': 0, 'start': 0x4001, 'end': 0x4003, 'entries': [0x4001], 'evidence': 'synthetic'},
        ]
    }
    # reg2 starts at file 1, which overlaps reg1's second byte of SKIP
    with pytest.raises(ValueError, match='Global boundary conflict'):
        module.analyze(data, manifest)


def test_identical_instruction_boundary_at_same_offset_accepted():
    # Two regions share the same RET instruction at 0x4002
    data = bytes([0x20, 0x00, 0xf0])  # SJMP +0 at 0x4000, RET at 0x4002
    manifest = {
        'sha256': hashlib.sha256(data).hexdigest(),
        'payload_offset': 0,
        'regions': [
            {'name': 'reg1', 'page': 0, 'start': 0x4000, 'end': 0x4003, 'entries': [0x4000], 'evidence': 'synthetic'},
            {'name': 'reg2', 'page': 0, 'start': 0x4002, 'end': 0x4003, 'entries': [0x4002], 'evidence': 'synthetic'},
        ]
    }
    r = module.analyze(data, manifest)
    assert len(r['regions']) == 2
