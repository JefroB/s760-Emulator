"""Host reference for BS1 WAV validation; not guest firmware or an importer.

The reader takes (absolute offset, byte count) and returns exact bytes or raises.
Inspect before reserving native sample memory. PCM stays interleaved here; native
deinterleaving, bounded wave writes and atomic publication need separate proof.
"""
from dataclasses import dataclass
import struct


RATES = (48000, 44100, 24000, 22050, 30000, 15000, 32000, 16000)
MAX_READ = 4096
MAX_FILE = 0xFFFFFFFF


class WavError(ValueError):
    pass


@dataclass(frozen=True)
class WavInfo:
    channels: int
    rate: int
    rate_code: int
    frames: int
    data_offset: int
    data_bytes: int
    riff_end: int


def _read(reader, offset, count, limit, cancelled):
    if cancelled():
        raise WavError('cancelled')
    # Subtraction form is also safe in the intended unsigned 32-bit guest port.
    if not 0 < count <= MAX_READ or not 0 <= offset <= limit or count > limit-offset:
        raise WavError('read outside declared extent')
    data = reader(offset, count)
    if len(data) != count:
        raise WavError('short read')
    return data


def inspect_wav(reader, file_size, *, cancelled=lambda: False):
    """Validate all RIFF chunks without reading PCM or unknown chunk payloads.

    Accept one fmt and one nonempty data chunk in either order. Unknown chunks
    (including optional loop/root metadata) are skipped with RIFF odd-byte pad.
    Bytes beyond the RIFF extent are ignored. Only PCM format1 is accepted;
    extra format bytes are ignored after validating its first16 bytes.
    """
    if not 12 <= file_size <= MAX_FILE:
        raise WavError('file size outside 32-bit profile')
    head = _read(reader, 0, 12, file_size, cancelled)
    if head[:4] != b'RIFF' or head[8:] != b'WAVE':
        raise WavError('expected little-endian RIFF/WAVE')
    size = struct.unpack_from('<I', head, 4)[0]
    if size < 4 or size > file_size-8:
        raise WavError('invalid RIFF extent')
    end = size+8
    position = 12
    format_fields = payload = None
    while position < end:
        header = _read(reader, position, 8, end, cancelled)
        tag, size = struct.unpack('<4sI', header)
        position += 8
        if size > end-position or (size & 1) > end-position-size:
            raise WavError('chunk or pad outside RIFF extent')
        if tag == b'fmt ':
            if format_fields is not None or size < 16:
                raise WavError('duplicate or short fmt chunk')
            encoding, channels, rate, byte_rate, align, bits = struct.unpack(
                '<HHIIHH', _read(reader, position, 16, end, cancelled))
            if encoding != 1 or channels not in (1, 2) or bits != 16 or rate not in RATES:
                raise WavError('unsupported PCM format')
            if align != channels*2 or byte_rate != rate*align:
                raise WavError('inconsistent PCM frame size or byte rate')
            format_fields = channels, rate, align
        elif tag == b'data':
            if payload is not None:
                raise WavError('duplicate data chunk')
            payload = position, size
        position += size+(size & 1)
    if format_fields is None or payload is None:
        raise WavError('missing fmt or data chunk')
    channels, rate, align = format_fields
    offset, size = payload
    if not size or size % align:
        raise WavError('empty or incomplete PCM frames')
    return WavInfo(channels, rate, RATES.index(rate), size//align, offset, size, end)


def pcm_blocks(reader, info, *, cancelled=lambda: False):
    """Yield at most4096 bytes per read, never beyond data or across half a frame.

    Callers must not retain blocks if they need the one-buffer memory profile.
    The reader must refer to the same stable file used by inspect_wav.
    """
    position = info.data_offset
    remaining = info.data_bytes
    end = position+remaining
    while remaining:
        count = min(MAX_READ, remaining)
        yield _read(reader, position, count, end, cancelled)
        position += count
        remaining -= count
