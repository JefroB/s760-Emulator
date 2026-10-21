"""Host reference acceptance for the proposed guest WAV parser, not firmware tests."""
import struct
import pytest
from scripts.bluescsi_wav_contract import inspect_wav, pcm_blocks, WavError


def chunk(tag, data):
    return tag + struct.pack('<I', len(data)) + data + (b'\0' if len(data) & 1 else b'')


def fmt(channels=2, rate=44100, tag=1, bits=16, align=None, byte_rate=None):
    align = channels * 2 if align is None else align
    return struct.pack('<HHIIHH', tag, channels, rate,
                       rate * align if byte_rate is None else byte_rate, align, bits)


def riff(*chunks):
    body = b'WAVE' + b''.join(chunks)
    return b'RIFF' + struct.pack('<I', len(body)) + body


class Source:
    def __init__(self, data):
        self.data = data
        self.reads = []

    def __call__(self, offset, size):
        assert 0 <= offset <= len(self.data) and 0 < size <= 4096
        assert offset + size <= len(self.data)
        self.reads.append((offset, size))
        return self.data[offset:offset + size]


@pytest.mark.parametrize('channels', [1, 2])
@pytest.mark.parametrize('rate', [48000, 44100, 24000, 22050, 30000, 15000, 32000, 16000])
def test_exact_pcm_across_buffer_boundary(channels, rate):
    pcm = struct.pack('<2050h', *range(-1025, 1025))
    source = Source(riff(chunk(b'JUNK', b'abc'), chunk(b'fmt ', fmt(channels, rate)), chunk(b'data', pcm)))
    info = inspect_wav(source, len(source.data))
    assert (info.channels, info.rate, info.frames) == (channels, rate, len(pcm) // (channels * 2))
    blocks = list(pcm_blocks(source, info))
    assert b''.join(blocks) == pcm
    assert all(len(b) % (channels * 2) == 0 for b in blocks)
    if channels == 2:
        assert struct.unpack('<2050h', b''.join(blocks))[::2] == tuple(range(-1025, 1025, 2))


@pytest.mark.parametrize('format_bytes', [fmt(tag=3), fmt(tag=65534), fmt(channels=3), fmt(bits=24), fmt(rate=96000), fmt(align=2), fmt(byte_rate=1), b'\0'*15])
def test_reject_unsupported_or_inconsistent_format(format_bytes):
    source = Source(riff(chunk(b'fmt ', format_bytes), chunk(b'data', b'\0'*8)))
    with pytest.raises(WavError):
        inspect_wav(source, len(source.data))


@pytest.mark.parametrize('chunks', [[], [chunk(b'fmt ', fmt())], [chunk(b'data', b'1234')],
    [chunk(b'fmt ', fmt()), chunk(b'fmt ', fmt()), chunk(b'data', b'1234')],
    [chunk(b'fmt ', fmt()), chunk(b'data', b'1234'), chunk(b'data', b'5678')],
    [chunk(b'fmt ', fmt()), chunk(b'data', b'')],
    [chunk(b'fmt ', fmt()), chunk(b'data', b'123')],
    [chunk(b'fmt ', fmt()), b'JUNK'+struct.pack('<I', 0xffffffff)]])
def test_reject_malformed_structure(chunks):
    source = Source(riff(*chunks))
    with pytest.raises(WavError):
        inspect_wav(source, len(source.data))


def test_data_before_fmt_and_unknown_chunks_are_scanned_without_payload_reads():
    pcm = b'\1\2\3\4'*1025
    source = Source(riff(chunk(b'data', pcm), chunk(b'JUNK', b'x'*10001), chunk(b'fmt ', fmt()) + b'abc'))
    # Incomplete trailing chunk header is an error even after a valid format/data.
    with pytest.raises(WavError):
        inspect_wav(source, len(source.data))
    source = Source(riff(chunk(b'data', pcm), chunk(b'JUNK', b'x'*10001), chunk(b'fmt ', fmt())))
    info = inspect_wav(source, len(source.data))
    assert max(n for _, n in source.reads) == 16
    assert b''.join(pcm_blocks(source, info)) == pcm


def test_every_truncation_rejects():
    data = riff(chunk(b'fmt ', fmt()), chunk(b'JUNK', b'abc'), chunk(b'data', b'12345678'))
    for size in range(len(data)):
        with pytest.raises(WavError):
            inspect_wav(Source(data[:size]), size)


def test_missing_odd_chunk_pad_rejects():
    data = riff(chunk(b'fmt ', fmt()), chunk(b'data', b'1234'), b'JUNK'+struct.pack('<I', 1)+b'x')
    with pytest.raises(WavError):
        inspect_wav(Source(data), len(data))


def test_short_read_and_cancel_propagate():
    data = riff(chunk(b'fmt ', fmt()), chunk(b'data', b'1234'))
    with pytest.raises(WavError, match='short read'):
        inspect_wav(lambda o,n: data[o:o+n-1], len(data))
    source = Source(data)
    with pytest.raises(WavError, match='cancelled'):
        inspect_wav(source, len(data), cancelled=lambda: True)
    assert not source.reads
    info = inspect_wav(source, len(data))
    with pytest.raises(WavError, match='cancelled'):
        list(pcm_blocks(source, info, cancelled=lambda: True))


def test_outer_size_trailing_bytes_and_extended_pcm_format():
    data = riff(chunk(b'fmt ', fmt()+b'\0\0'), chunk(b'data', b'1234')) + b'outside-riff'
    source = Source(data)
    assert b''.join(pcm_blocks(source, inspect_wav(source, len(data)))) == b'1234'
    for bad in [b'RF64'+data[4:], b'RIFX'+data[4:], data[:4]+struct.pack('<I', 0xffffffff)+data[8:]]:
        with pytest.raises(WavError):
            inspect_wav(Source(bad), len(bad))


def test_sparse_near_32_bit_extent_without_large_allocation():
    end = 0xfffffffe
    headers = {0: b'RIFF'+struct.pack('<I', end-8)+b'WAVE',
               12: b'fmt '+struct.pack('<I', 16), 20: fmt(),
               36: b'data'+struct.pack('<I', 4),
               48: b'JUNK'+struct.pack('<I', end-56)}
    reads = []
    def reader(offset, count):
        reads.append((offset, count))
        assert len(headers[offset]) == count
        return headers[offset]
    info = inspect_wav(reader, end)
    assert info.frames == 1 and info.riff_end == end
    assert len(reads) == 5


def test_failure_between_pcm_blocks_cannot_yield_extra_data():
    data = riff(chunk(b'fmt ', fmt()), chunk(b'data', b'x'*4100))
    source = Source(data)
    info = inspect_wav(source, len(data))
    def reader(offset, count):
        if offset >= info.data_offset+4096:
            raise OSError('target disconnected')
        return source(offset, count)
    blocks = pcm_blocks(reader, info)
    assert next(blocks) == b'x'*4096
    with pytest.raises(OSError, match='disconnected'):
        next(blocks)
