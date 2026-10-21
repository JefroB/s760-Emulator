"""Native sample rate and loop mode are independent descriptor fields."""
import pytest
import struct
from scripts.build_sample_disk import _write_sample, IMAGE_SIZE, OFF_SAMPLE_SECTOR


def descriptor(spec):
    original=bytes(IMAGE_SIZE);disk=bytearray(original)
    _write_sample(disk,original,0,spec)
    return disk[OFF_SAMPLE_SECTOR:OFF_SAMPLE_SECTOR+48]


@pytest.mark.parametrize('rate,code',[(48000,0),(44100,1),(24000,2),(22050,3),
                                     (30000,4),(15000,5),(32000,6),(16000,7)])
def test_explicit_sample_rates_match_original_firmware_codes(rate,code):
    result=descriptor({'sample_rate':rate,'loop_mode':'one_shot'})
    assert result[0x2c]==code
    assert result[0x24]==2


def test_loop_mode_changes_without_changing_rate_or_addresses():
    forward=descriptor({'sample_rate':44100,'loop_mode':'forward'})
    once=descriptor({'sample_rate':44100,'loop_mode':'one_shot'})
    assert [i for i,(a,b) in enumerate(zip(forward,once)) if a!=b]==[0x24]
    assert forward[0x24]==0 and once[0x24]==2


@pytest.mark.parametrize('legacy',[0,1,2,7,255])
def test_legacy_rate_alias_preserves_existing_fixture_bytes(legacy):
    record=descriptor({'loop_enable':legacy})
    assert record[0x24:0x28]==bytes(4) and record[0x2c]==legacy


@pytest.mark.parametrize('spec',[{'sample_rate':96000},{'sample_rate':44100,'loop_enable':1},
                               {'sample_rate':44100.5},{'loop_mode':'infinite'},
                               {'loop_mode':True}])
def test_invalid_or_ambiguous_metadata_is_rejected(spec):
    with pytest.raises(ValueError):descriptor(spec)


def test_explicit_sample_points_match_native_screen_order():
    points = dict(start=5, loop_start=17, loop_end=3000,
                  release_start=3500, release_end=4000)
    result = descriptor({'sample_points': points})
    assert struct.unpack_from('<5I', result, 0x10) == tuple(
        value << 8 for value in points.values())


def test_legacy_address_fields_preserve_historical_fixture_bytes():
    result = descriptor(dict(start=5, loop_start=17, loop_end=3000, end=4000))
    assert struct.unpack_from('<5I', result, 0x10) == (0, 5 << 8, 17 << 8, 3000 << 8, 4000 << 8)


@pytest.mark.parametrize('bad', [-1, 4608, True, 1.5])
def test_explicit_points_reject_values_outside_fixed_pcm_slot(bad):
    points = dict(start=bad, loop_start=0, loop_end=4095,
                  release_start=4096, release_end=4607)
    with pytest.raises(ValueError): descriptor({'sample_points': points})


@pytest.mark.parametrize('spec', [
    {'sample_points': {}},
    {'sample_points': dict(start=0, loop_start=0, loop_end=4095,
                          release_start=4096, release_end=4607), 'start': 0},
])
def test_incomplete_or_mixed_point_schemas_are_rejected(spec):
    with pytest.raises(ValueError): descriptor(spec)
