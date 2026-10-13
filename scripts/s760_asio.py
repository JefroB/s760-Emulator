"""Worker-only ASIO control; all device callbacks and bounded rings are native."""
import atexit
import ctypes as C
import importlib.util
from pathlib import Path
import sys
import time

ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
_api = None


class Status(C.Structure):
    _fields_ = [(n, C.c_ulonglong) for n in ('played','captured','output_underflows','input_overflows','driver_flags')] + [
        ('output_queued',C.c_uint),('input_queued',C.c_uint),('input_latency',C.c_double),
        ('output_latency',C.c_double),('rate',C.c_double),('active',C.c_int)]


def portaudio_library():
    packaged = ROOT / 'audio/portaudio-asio.dll'
    if packaged.is_file(): return packaged
    packaged=ROOT/'_internal/audio/libportaudio64bit-asio.dll'
    if packaged.is_file():return packaged
    spec = importlib.util.find_spec('_sounddevice_data')
    if spec and spec.submodule_search_locations:
        candidate = Path(next(iter(spec.submodule_search_locations))) / 'portaudio-binaries/libportaudio64bit-asio.dll'
        if candidate.is_file(): return candidate
    raise OSError('ASIO runtime is unavailable; rebuild the standalone package with its ASIO libraries')


def api():
    global _api
    if _api is not None:return _api
    if sys.platform != 'win32':raise OSError('ASIO requires Windows')
    bridge = ROOT/'audio/s760_asio.dll'
    if not bridge.is_file():bridge = ROOT/'_internal/audio/s760_asio.dll'
    if not bridge.is_file():bridge = ROOT/'build/Release/s760_asio.dll'
    if not bridge.is_file():raise OSError('Native ASIO bridge is missing; build the s760_asio target')
    d=C.CDLL(str(bridge))
    d.s760_asio_error.restype=C.c_char_p
    d.s760_windows_output.argtypes=[C.c_int,C.c_char_p,C.c_uint,C.c_char_p,C.c_uint,C.POINTER(C.c_uint),C.POINTER(C.c_uint)]
    d.s760_asio_initialize.argtypes=[C.c_wchar_p]
    d.s760_asio_device.argtypes=[C.c_int,C.c_char_p,C.c_uint,C.POINTER(C.c_int),C.POINTER(C.c_int)]
    d.s760_asio_open.argtypes=[C.c_char_p,C.c_int,C.c_int,C.c_uint,C.c_int];d.s760_asio_open.restype=C.c_void_p
    d.s760_asio_close.argtypes=[C.c_void_p]
    d.s760_asio_write.argtypes=[C.c_void_p,C.c_void_p,C.c_uint];d.s760_asio_write.restype=C.c_uint
    d.s760_asio_read.argtypes=[C.c_void_p,C.c_void_p,C.c_uint];d.s760_asio_read.restype=C.c_uint
    d.s760_asio_status.argtypes=[C.c_void_p,C.POINTER(Status)]
    if d.s760_asio_initialize(str(portaudio_library())):raise OSError(d.s760_asio_error().decode('utf-8','replace'))
    _api=d
    atexit.register(d.s760_asio_shutdown)
    return d


def checked(d,result):
    if result:raise OSError(d.s760_asio_error().decode('utf-8','replace'))


def devices():
    d=api();result=[]
    for i in range(d.s760_asio_device_count()):
        name=C.create_string_buffer(1024);inputs=C.c_int();outputs=C.c_int()
        checked(d,d.s760_asio_device(i,name,len(name),C.byref(inputs),C.byref(outputs)))
        result.append({'name':name.value.decode('utf-8','replace'),'inputs':inputs.value,'outputs':outputs.value})
    return result


def windows_outputs():
    d=api();result=[]
    for i in range(256):
        identity=C.create_string_buffer(1024);name=C.create_string_buffer(1024)
        rate=C.c_uint();channels=C.c_uint()
        if d.s760_windows_output(i,identity,len(identity),name,len(name),C.byref(rate),C.byref(channels)):
            error=d.s760_asio_error().decode('utf-8','replace')
            if error=='Windows output is unavailable':return result
            raise OSError(error)
        result.append({'id':identity.value.decode('utf-8'),'name':name.value.decode('utf-8'),'mixRate':rate.value,'channels':channels.value})
    raise OSError('Windows output inventory exceeds256 endpoints')


class AsioHost:
    def __init__(self,config):
        self.dll=api();self.config=config
        self.handle=self.dll.s760_asio_open(config.asio_driver.encode('utf-8'),config.asio_output_channel,
            config.asio_input_channel,config.asio_buffer_frames,int(config.sound))
        if not self.handle:raise OSError(self.dll.s760_asio_error().decode('utf-8','replace'))
        self.device={'name':config.asio_driver}
        self.discarded_frames=0
        self.output_discarded=0
        self.buffer=(C.c_short*4096)()
        self.last_capture=time.monotonic();self.last_received=0
        self.last_playback=time.monotonic();self.last_played=0
        self.next_output=0
        self.clock_rate=1.0
        self.closed=False
        atexit.register(self.close)

    def write(self,pcm):
        if len(pcm)%8 or len(pcm)>44100*8:raise ValueError('ASIO output requires bounded stereo float32 PCM')
        if not pcm:return
        data=C.create_string_buffer(pcm)
        accepted=self.dll.s760_asio_write(self.handle,data,len(pcm)//8)
        self.output_discarded+=len(pcm)//8-accepted
        self.next_output=time.monotonic()+.08

    def read(self):
        if not self.config.asio_input_channel:return []
        blocks=[]
        for _ in range(8):
            frames=self.dll.s760_asio_read(self.handle,self.buffer,2048)
            if not frames:break
            blocks.append(C.string_at(self.buffer,frames*4))
        return blocks

    def status(self):
        s=Status();checked(self.dll,self.dll.s760_asio_status(self.handle,C.byref(s)))
        if s.active!=1:raise OSError('ASIO driver stopped; reconnect the device and apply settings again')
        if self.config.sound:
            prime=max(8192,self.config.asio_buffer_frames*4)
            target=max(16384,self.config.asio_buffer_frames*4)
            self.clock_rate=max(.97,min(1.03,1+(target-s.output_queued)/44100*.15))
            # The normal duplex transaction drains output along with input.
            # Do not wait for its 80ms fallback when the device queue is low.
            if s.output_queued<prime:
                self.next_output=min(self.next_output,time.monotonic())
            if s.played!=self.last_played or s.output_queued<prime:
                self.last_playback=time.monotonic();self.last_played=s.played
            elif time.monotonic()-self.last_playback>2:
                raise OSError('ASIO driver stopped consuming output PCM; reconnect the device and apply settings again')
        if self.config.asio_input_channel:
            if s.captured!=self.last_received:self.last_capture=time.monotonic();self.last_received=s.captured
            elif time.monotonic()-self.last_capture>2:raise OSError('ASIO driver stopped delivering input PCM')
        return {'device':self.config.asio_driver,'backend':'asio','rate':s.rate,'channels':2,'format':'PCM16 input / float32 output',
            'receivedFrames':s.captured,'playedFrames':s.played,'discardedFrames':self.discarded_frames+s.input_overflows,
            'outputUnderruns':s.output_underflows,'outputDiscardedFrames':self.output_discarded,
            'clockPacingRate':self.clock_rate,
            'driverStatusFlags':s.driver_flags,'outputQueuedFrames':s.output_queued,
            'outputQueuedMs':s.output_queued*1000/44100,'outputTargetMs':16384*1000/44100,
            'driverInputLatencyMs':s.input_latency*1000,'driverOutputLatencyMs':s.output_latency*1000,
            'inputChannel':self.config.asio_input_channel,'outputChannel':self.config.asio_output_channel,
            'bufferFrames':self.config.asio_buffer_frames,'bufferCapacityFrames':65536,
            'driverLossMeasurement':'status flags only; latency is driver-reported'}

    def close(self):
        if not self.closed:
            self.closed=True
            self.dll.s760_asio_close(self.handle);self.handle=None
            atexit.unregister(self.close)


if __name__=='__main__':
    print(portaudio_library())
