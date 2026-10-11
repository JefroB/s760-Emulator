"""Read-only OS 2.24 display observations, never guest readiness flags.

Signatures cover fixed firmware labels in the native 640x480 RGBA surface.
Unknown/occluded screens remain unknown. Disk idle is not proof of load success.
"""
import hashlib
import time

SYSTEM_SHA256 = '3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd'
SIGNATURES = {
    'perform': ((16,48,240,64), '40ebee098ea2b92bfba2d7da412f2fd3c39b5a08cf56822c0a9b880f3bef7f36'),
    'disk': ((16,48,160,64), 'a6cc231f6cf7582bfb82229c3a3e5c365a7fccd356b269dfc802d37cd7303656'),
    'load': ((16,64,144,80), '9b7bf714631a660e3e863138e2f5b449cd8f3061a7a3db25cc8840accc2b2457'),
    'working': ((32,32,224,48), '959bd14b37057bc8be93ff3f0d9927a7e4896b8b948b56752828593824e0cf65'),
    'idle': ((16,64,144,80), 'ca4debcf4c6d755535ff093bd4a4042f690b76c866d9acd6e0dc846d47f0c69b'),
}

def labels(frame):
    if len(frame) != 6+640*480*4 or frame[:6] != bytes((0,128,2,224,1,0)):
        return set()
    pixels=memoryview(frame)[6:]
    found=set()
    for name,((x,y,right,bottom),digest) in SIGNATURES.items():
        rgb=bytearray()
        for row in range(y,bottom):
            rgba=bytes(pixels[(row*640+x)*4:(row*640+right)*4])
            strip=bytearray((right-x)*3)
            strip[0::3],strip[1::3],strip[2::3]=rgba[0::4],rgba[1::4],rgba[2::4]
            rgb.extend(strip)
        if hashlib.sha256(rgb).hexdigest()==digest: found.add(name)
    return found

class FirmwareReadiness:
    def __init__(self, supported=True, clock=time.monotonic):
        self.clock=clock
        self.started=clock()
        self.supported=supported
        self.booted=False
        self.loading_since=None
        self.last_seconds=None
        self.advanced_at=clock()

    def observe(self, frame, seconds, paused=False):
        now=self.clock()
        if seconds!=self.last_seconds:
            self.last_seconds=seconds; self.advanced_at=now
        seen=labels(frame) if self.supported else set()
        if 'perform' in seen or 'disk' in seen: self.booted=True
        if not paused and now-self.advanced_at>15:
            state,message='stalled','Emulator clock stalled. Reconnect or restart the sampler.'
        elif not self.supported:
            state,message='unknown','Firmware profile unrecognized. Check the sampler display.'
        elif 'load' in seen or 'working' in seen:
            if self.loading_since is None: self.loading_since=now
            if now-self.loading_since>120:
                state,message='timeout','Disk operation is taking longer than expected. Check the display; Exit can cancel.'
            else:
                state,message='loading','Firmware disk operation in progress.'
        elif 'disk' in seen and 'idle' in seen:
            self.loading_since=None
            state,message='disk_ready','Disk Load ready. Check the firmware display for the operation result.'
        elif 'perform' in seen:
            self.loading_since=None
            state,message='ready','OS ready — Perform Play.'
        elif not self.booted and now-self.started>60:
            state,message='timeout','OS boot not confirmed. Check the firmware display or restart the sampler.'
        elif not self.booted:
            state,message='booting','Booting firmware…'
        else:
            state,message='unknown','OS boot confirmed; current operation unrecognized. Check the sampler display.'
        return {'type':'FIRMWARE_STATUS','state':state,'message':message,'booted':self.booted}
