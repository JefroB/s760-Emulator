import struct
from scripts.build_sample_disk import _write_partial,OFF_PARTIAL_RECORD

def test_explicit_tvf_times_and_levels_match_firmware_fields():
    original=bytes(OFF_PARTIAL_RECORD+128);disk=bytearray(original)
    _write_partial(disk,original,0,{'tvf_env':{'rates':[11,22,33,44],'levels':[55,66,77,88],'depth':63}})
    assert disk[OFF_PARTIAL_RECORD+0x52:OFF_PARTIAL_RECORD+0x56]==bytes([55,66,77,88])
    assert disk[OFF_PARTIAL_RECORD+0x56:OFF_PARTIAL_RECORD+0x5a]==bytes([11,22,33,44])
