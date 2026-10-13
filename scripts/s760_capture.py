"""Windows MME capture. OS fills fixed buffers; only a worker polls/copies PCM.

The granted interface is PCM16 stereo at 44100 Hz. Windows/driver conversion
may precede it; this is not a claim about the physical converter's clock.
"""
import ctypes as C
from ctypes import wintypes as W
import sys
import time


class Caps(C.Structure):
    _fields_ = [('mid', W.WORD), ('pid', W.WORD), ('version', W.DWORD),
                ('name', W.WCHAR * 32), ('formats', W.DWORD),
                ('channels', W.WORD), ('reserved', W.WORD)]


class Format(C.Structure):
    _pack_ = 2
    _fields_ = [('tag', W.WORD), ('channels', W.WORD), ('rate', W.DWORD),
                ('bytes_sec', W.DWORD), ('alignment', W.WORD),
                ('bits', W.WORD), ('extra', W.WORD)]


class Header(C.Structure):
    _fields_ = [('data', C.c_void_p), ('length', W.DWORD), ('recorded', W.DWORD),
                ('user', C.c_size_t), ('flags', W.DWORD), ('loops', W.DWORD),
                ('next', C.c_void_p), ('reserved', C.c_size_t)]


def api():
    if sys.platform != 'win32':
        raise OSError('Windows MME recording is unavailable on this platform')
    dll = C.WinDLL('winmm')
    dll.waveInGetNumDevs.restype = W.UINT
    dll.waveInGetDevCapsW.argtypes = [C.c_size_t, C.POINTER(Caps), W.UINT]
    dll.waveInOpen.argtypes = [C.POINTER(C.c_void_p), W.UINT,
                              C.POINTER(Format), C.c_size_t, C.c_size_t, W.DWORD]
    for name in ('waveInPrepareHeader', 'waveInUnprepareHeader', 'waveInAddBuffer'):
        getattr(dll, name).argtypes = [C.c_void_p, C.POINTER(Header), W.UINT]
    for name in ('waveInStart', 'waveInStop', 'waveInReset', 'waveInClose'):
        getattr(dll, name).argtypes = [C.c_void_p]
    return dll


def checked(code, action):
    if code:
        raise OSError(f'{action} failed (Windows MME error {code})')


def devices():
    if sys.platform != 'win32':
        return []
    dll = api()
    result = []
    for index in range(dll.waveInGetNumDevs()):
        caps = Caps()
        checked(dll.waveInGetDevCapsW(index, C.byref(caps), C.sizeof(caps)), 'Recording-device discovery')
        result.append({'id': f'{index}:{caps.name}', 'name': caps.name,
                       'index': index, 'channels': caps.channels})
    return result


class WaveInput:
    """Eight preallocated 2048-frame buffers, no Python audio callback.

    Call from one serialized worker. A stalled client has bounded storage;
    missing buffers/driver timing are not inferred to be lossless capture.
    """
    frames_per_buffer = 2048
    buffer_count = 8

    def __init__(self, device_id):
        selected = next((d for d in devices() if d['id'] == device_id), None)
        if selected is None:
            raise ValueError('Recording device is unavailable; refresh devices and select it again')
        self.dll = api()
        self.handle = C.c_void_p()
        self.buffers = []
        self.headers = []
        self.next_buffer = 0
        self.received_frames = 0
        self.discarded_frames = 0
        self.last_buffer = time.monotonic()
        self.device = selected
        self.format = Format(1, 2, 44100, 176400, 4, 16, 0)
        # Ask explicitly before opening; do not silently change the interface.
        checked(self.dll.waveInOpen(None, selected['index'], C.byref(self.format), 0, 0, 1),
                '44100 Hz stereo PCM16 format negotiation')
        checked(self.dll.waveInOpen(C.byref(self.handle), selected['index'], C.byref(self.format), 0, 0, 0),
                'Recording-device open')
        try:
            for _ in range(self.buffer_count):
                buffer = C.create_string_buffer(self.frames_per_buffer * 4)
                header = Header(data=C.addressof(buffer), length=len(buffer))
                self.buffers.append(buffer)
                self.headers.append(header)
                checked(self.dll.waveInPrepareHeader(self.handle, C.byref(header), C.sizeof(header)), 'Capture buffer preparation')
                checked(self.dll.waveInAddBuffer(self.handle, C.byref(header), C.sizeof(header)), 'Capture buffer submission')
            checked(self.dll.waveInStart(self.handle), 'Recording-device start')
        except Exception:
            self.close()
            raise

    def read(self):
        """Return at most eight completed blocks and immediately recycle them."""
        if not self.handle:
            raise OSError('Recording device is closed')
        blocks = []
        for _ in range(self.buffer_count):
            header = self.headers[self.next_buffer]
            if not header.flags & 1:  # WHDR_DONE; OS owns incomplete buffers.
                break
            size = int(header.recorded)
            if size > header.length or size % 4:
                raise OSError('Recording device returned an incomplete stereo PCM frame')
            if size:
                blocks.append(C.string_at(header.data, size))
                self.received_frames += size // 4
                self.last_buffer = time.monotonic()
            header.recorded = 0
            checked(self.dll.waveInAddBuffer(self.handle, C.byref(header), C.sizeof(header)), 'Capture buffer recycling')
            self.next_buffer = (self.next_buffer + 1) % self.buffer_count
        if time.monotonic() - self.last_buffer > 2:
            raise OSError('Recording device stopped delivering PCM; reconnect it and apply settings again')
        return blocks

    def status(self):
        return {'device': self.device['name'], 'rate': 44100, 'channels': 2,
                'format': 'PCM16', 'receivedFrames': self.received_frames,
                'discardedFrames': self.discarded_frames,
                'bufferCapacityFrames': self.buffer_count * self.frames_per_buffer,
                'driverLossMeasurement': 'unavailable'}

    def close(self):
        if self.handle:
            self.dll.waveInReset(self.handle)
            for header in self.headers:
                if header.flags & 2:
                    self.dll.waveInUnprepareHeader(self.handle, C.byref(header), C.sizeof(header))
            self.dll.waveInClose(self.handle)
            self.handle = C.c_void_p()
