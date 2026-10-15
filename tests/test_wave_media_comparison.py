"""Disk reload differences must be reported, with truncation never accepted."""
import pytest
from scripts.verify_native_media import compare_wave_records

def test_reports_every_changed_range_and_original_bytes():
    before=bytes(range(32));after=bytearray(before);after[0]=255;after[12:15]=b'abc';after[-1]=0
    report=compare_wave_records(before,bytes(after))
    assert report['changed_bytes']==5 and not report['equal']
    assert [(r['first'],r['last_exclusive']) for r in report['ranges']]==[(0,1),(12,15),(31,32)]
    for r in report['ranges']:
        assert bytes.fromhex(r['before_hex'])==before[r['first']:r['last_exclusive']]
        assert bytes.fromhex(r['after_hex'])==after[r['first']:r['last_exclusive']]
    assert report['before_sha256']!=report['after_sha256']

def test_exact_wave_and_size_mismatch():
    report=compare_wave_records(b'unchanged',b'unchanged')
    assert report['equal'] and report['changed_bytes']==0 and report['ranges']==[]
    with pytest.raises(AssertionError,match='size changed'):compare_wave_records(b'abc',b'ab')
