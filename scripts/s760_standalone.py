"""Launch built React assets and a native MAME runtime on loopback only.

Usage: python scripts/s760_standalone.py
Dependencies: websockets>=14,<17. Build google-ui first (npm run build).
"""
import argparse
from contextlib import closing, contextmanager
from dataclasses import replace
import hashlib
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import subprocess
import sys
import queue
import threading
import time
from urllib.parse import parse_qs, urlsplit
import webbrowser

from websockets.sync.server import serve
from websockets.exceptions import ConnectionClosed
from s760_runtime import NativeRuntime, RuntimeConfig, application_root, midi_inputs

from s760_readiness import FirmwareReadiness, SYSTEM_SHA256
from s760_capture import WaveInput, devices as recording_devices
from s760_asio import AsioHost, devices as asio_devices, windows_outputs
from s760_media_paths import default_media_paths

ASIO_SETTINGS = {'asioDriver':'asio_driver','asioOutputChannel':'asio_output_channel',
                 'asioInputChannel':'asio_input_channel','asioBufferFrames':'asio_buffer_frames'}

ROOT = application_root()


class AssetHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        # Windowed packages have no stderr; don't log session tokens in URLs.
        pass
BUTTONS = {
    'COMMAND': (':PANEL0', 'Command'), 'EXIT': (':PANEL1', 'Exit'),
    'MODE': (':PANEL1', 'Mode'), 'UP': (':PANEL1', 'Panel Up'),
    'DOWN': (':PANEL3', 'Panel Down'), 'LEFT': (':PANEL2', 'Panel Left'),
    'RIGHT': (':PANEL0', 'Panel Right'), 'F1': (':PANEL2', 'Panel F1'),
    'F2': (':PANEL3', 'Panel F2'), 'F3': (':PANEL2', 'Panel F3'),
    'S1': (':PANEL0', 'S1'), 'S2': (':PANEL0', 'S2'),
    'SHIFT': (':PANEL3', 'Panel Shift'),
    'MENU': (':PANEL0', 'Value Menu'),
}


def validate_input(message):
    """Validate before any hardware input; never convert arbitrary JSON to Lua."""
    if not isinstance(message, dict):
        raise ValueError('Expected an input object')
    kind, p = message.get('type'), message.get('payload')
    if not isinstance(p, dict):
        raise ValueError('Expected input payload')
    if kind in ('BUTTON_PRESS', 'BUTTON_RELEASE'):
        if p.get('id') not in BUTTONS:
            raise ValueError('Unsupported panel button')
    elif kind == 'DIAL_DELTA':
        if p.get('id') not in ('ALPHA', 'VOLUME', 'INPUT') or type(p.get('delta')) is not int or abs(p['delta']) > 32:
            raise ValueError('Invalid native dial input')
    elif kind == 'MOUSE_MOVE':
        if any(type(p.get(k)) not in (int, float) or not 0 <= p[k] <= 1 for k in ('x', 'y')):
            raise ValueError('Pointer coordinates must be normalized')
    elif kind == 'MOUSE_BUTTON':
        if type(p.get('button')) is not int or p['button'] not in (0, 2) or type(p.get('down')) is not bool:
            raise ValueError('Invalid mouse button')
    elif kind in ('NOTE_ON', 'NOTE_OFF'):
        if any(type(p.get(k)) is not int or not 0 <= p[k] <= 127 for k in ('note', 'velocity')):
            raise ValueError('Invalid MIDI note or velocity')
    elif kind == 'MOUNT_DISK':
        if not isinstance(p.get('diskPath'), str):
            raise ValueError('Expected media name')
    elif kind == 'MIDI_DEVICE':
        if not isinstance(p.get('name'), str):
            raise ValueError('Expected MIDI device name')
    elif kind == 'SET_STANDALONE_PREFERENCES':
        if set(p) != {'showKeyboard'} or type(p['showKeyboard']) is not bool:
            raise ValueError('Expected boolean showKeyboard preference')
    elif kind == 'MEDIA_WRITE_PROTECT':
        if set(p) != {'enabled'} or type(p['enabled']) is not bool:
            raise ValueError('Write protection requires a boolean enabled value')
    elif kind == 'CONFIGURE_RUNTIME':
        required = {'bootRom','systemDisk','mediaDirectory','sound','discard'}
        if not required <= set(p) or set(p) - required - {'audioBackend','audioLatencyMs','audioOutputDevice','recordingDevice','waveMemoryMb'} - set(ASIO_SETTINGS) or p.get('discard') is not True:
            raise ValueError('Confirm replacement of the current sampler before applying settings')
        for key in ('bootRom','systemDisk','mediaDirectory'):
            if not isinstance(p[key],str) or not p[key].strip() or len(p[key])>2048 or '\0' in p[key]:
                raise ValueError(f'Invalid path: {key}')
        if type(p['sound']) is not bool: raise ValueError('Sound must be a boolean')
        if 'recordingDevice' in p and (not isinstance(p['recordingDevice'],str) or len(p['recordingDevice'])>256 or '\0' in p['recordingDevice']):
            raise ValueError('Invalid recording device')
        RuntimeConfig(None, None, None, None, wave_memory_mb=p.get('waveMemoryMb',32), audio_backend=p.get('audioBackend', 'auto'),
                      audio_latency_ms=p.get('audioLatencyMs', 0),
                      audio_output_device=p.get('audioOutputDevice',''),
                      **{field:p[key] for key,field in ASIO_SETTINGS.items() if key in p}).audio_arguments()
    elif kind in ('RESTART_RUNTIME', 'RESTORE_SESSION', 'RESTORE_RECOVERY', 'START_RECOVERY', 'QUIT_WITHOUT_RECOVERY'):
        if set(p) != {'discard'} or p['discard'] is not True:
            raise ValueError('Restart requires explicit discard confirmation')
    elif kind in ('EXPORT_DISK', 'SAVE_SESSION', 'EJECT_DISK', 'MEDIA_STATUS', 'SAVE_RECOVERY', 'RECORDING_DEVICES', 'ASIO_DEVICES','AUDIO_OUTPUT_DEVICES','REOPEN_AUDIO'):
        if p:
            raise ValueError('Export does not accept a client output path')
    else:
        raise ValueError('Unsupported input')
    return kind, p


def load_settings(state_dir):
    path = state_dir / 'settings.json'
    if not path.exists(): return {}
    if path.stat().st_size > 16384: raise ValueError('Settings file is too large')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('version') != 1:
        raise ValueError('Unsupported settings format')
    for key in ('bootRom', 'systemDisk', 'mediaDirectory'):
        if not isinstance(data.get(key), str): raise ValueError(f'Invalid setting: {key}')
    if type(data.get('sound')) is not bool: raise ValueError('Invalid sound setting')
    data.setdefault('audioBackend', 'auto')
    data.setdefault('audioLatencyMs', 0)
    if not isinstance(data.get('recordingDevice',''),str) or len(data.get('recordingDevice',''))>256:
        raise ValueError('Invalid recording device setting')
    RuntimeConfig(None, None, None, state_dir, wave_memory_mb=data.get('waveMemoryMb',32), audio_backend=data['audioBackend'],
                  audio_latency_ms=data['audioLatencyMs'],
                  audio_output_device=data.get('audioOutputDevice',''),
                  **{field:data[key] for key,field in ASIO_SETTINGS.items() if key in data}).audio_arguments()
    return data


def media_index(folder):
    if not folder.is_dir(): raise ValueError(f'Media directory does not exist: {folder}')
    return {p.name: p.resolve() for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in ('.img', '.dsk')}


class StandaloneSession:
    def __init__(self, runtime, media_dir, startup_error=None):
        self.runtime = runtime
        self.media_dir = media_dir
        self.startup_error = startup_error
        self.media = media_index(media_dir) if media_dir.is_dir() else {}
        self.clients = {}
        self.client_lock = threading.Lock()
        self.stop = threading.Event()
        self.failure = None
        self.runtime_lock = threading.RLock()
        self.recovery_pending = self.recovery_path.is_file()
        self.recovery_message = 'Existing recovery preserved. Restore it or start a new recovery history.' if self.recovery_pending else 'Automatic recovery every 60 seconds and on normal close; saving briefly pauses audio.'
        self.next_recovery = time.monotonic() + 60
        self.closing = False
        self.readiness = None
        self.firmware_status = {'type':'FIRMWARE_STATUS','state':'booting','message':'Connected; checking firmware…'}
        self.midi_warning = None
        self.midi_input = ''
        self.capture = None
        self.capture_status = {'state':'disabled','message':'No recording device selected.'}
        self.capture_discontinuities = 0
        self.asio_devices = []
        self.audio_output_devices = []
        try:
            self.recording_devices = recording_devices()
        except OSError:
            self.recording_devices = []
        if not startup_error:
            self.start_capture()
        self.preferences = {'showKeyboard': False}
        preference_path = runtime.config.state_dir / 'standalone-ui.json'
        try:
            if preference_path.is_file():
                if preference_path.stat().st_size > 1024:
                    raise ValueError('Standalone preferences are too large')
                stored = json.loads(preference_path.read_text(encoding='utf-8'))
                if not isinstance(stored, dict) or type(stored.get('showKeyboard')) is not bool:
                    raise ValueError('Invalid standalone preferences')
                self.preferences = {'showKeyboard': stored['showKeyboard']}
        except (OSError, ValueError) as error:
            self.midi_warning = f'Could not read standalone preferences; keyboard hidden. {error}'
        try:
            self.midi_devices = midi_inputs(runtime.config.executable)
        except (OSError, subprocess.SubprocessError) as error:
            self.midi_devices = []
            self.midi_warning = f'MIDI input discovery failed; on-screen audition is available. {error}'

    def configuration(self):
        cfg = self.runtime.config
        return {'bootRom':str(cfg.boot_rom),'systemDisk':str(cfg.system_disk),
                'mediaDirectory':str(self.media_dir),'sound':cfg.sound,'waveMemoryMb':getattr(cfg,'wave_memory_mb',32),
                'audioBackend':cfg.audio_backend,'audioLatencyMs':cfg.audio_latency_ms,
                'audioOutputDevice':getattr(cfg,'audio_output_device',''),
                'recordingDevice':getattr(cfg,'recording_device',''),
                **{key:getattr(cfg,field,getattr(RuntimeConfig,field)) for key,field in ASIO_SETTINGS.items()}}

    def close_capture(self):
        if self.capture is not None:
            asio=isinstance(self.capture,AsioHost)
            self.capture.close()
            self.capture = None
            if asio:
                try:self.runtime.request('device_clock',clock_rate=1.0)
                except (OSError,RuntimeError):pass

    @contextmanager
    def capture_transaction(self):
        """Device buffers belong to wall time and cannot survive a checkpoint pause."""
        active = self.capture is not None
        if active:
            self.close_capture()
            self.capture_discontinuities += 1
        try:
            yield
        finally:
            if active:
                self.start_capture()

    def capture_worker(self):
        while not self.stop.is_set():
            with self.runtime_lock:
                self.poll_capture()
            self.stop.wait(.005)

    def start_capture(self):
        self.close_capture()
        self.capture_pending = []
        self.capture_primed = False
        device = getattr(self.runtime.config, 'recording_device', '')
        if not device and getattr(self.runtime.config,'audio_backend','auto')!='asio':
            self.capture_status = {'state':'disabled','message':'No recording device selected.'}
            return
        try:
            cfg=self.runtime.config
            if getattr(cfg,'audio_backend','auto')=='asio':
                self.capture = AsioHost(cfg)
                self.runtime.request('audio_capture',enabled=cfg.sound)
                message=f'ASIO: {cfg.asio_driver} — 44.1 kHz stereo. Output {cfg.asio_output_channel}/{cfg.asio_output_channel+1}; input '+(f'{cfg.asio_input_channel}/{cfg.asio_input_channel+1}.' if cfg.asio_input_channel else 'disabled.')
            else:
                self.capture = WaveInput(device)
                message=f"Recording: {self.capture.device['name']} — 44.1 kHz stereo PCM16."
            self.capture_status = {'state':'active','message':message, **self.capture.status()}
        except (OSError, ValueError) as error:
            self.capture_status = {'state':'failed','message':f'Recording unavailable: {error}'}

    def poll_capture(self):
        source = self.capture
        if source is None:
            return
        try:
            duplex=isinstance(source,AsioHost) and self.runtime.config.sound
            if duplex and time.monotonic()>=source.next_output:
                meta,pcm=self.runtime.read_audio(clock_rate=source.clock_rate)
                source.write(pcm)
                self.capture_status['nativeOutputDroppedFrames']=meta['dropped_frames']
            blocks = source.read()
            if not self.capture_primed:
                self.capture_pending.extend(blocks)
                if sum(map(len, self.capture_pending)) < 8192 * 4:
                    self.capture_status.update(source.status(), discontinuities=self.capture_discontinuities)
                    return
                blocks = self.capture_pending
                self.capture_pending = []
                self.capture_primed = True
            for pcm in blocks:
                try:
                    clock={'clock_rate':source.clock_rate,'binary':True} if isinstance(source,AsioHost) else {}
                    reply = self.runtime.queue_input_pcm(pcm, live=True, **({'duplex':True} if duplex else {}),**clock)
                    if isinstance(source,AsioHost) and not duplex:
                        source.clock_rate=max(.97,min(1.03,1+(reply.get('queued',8192)-8192)/44100*.15))
                    if duplex and 'pcm' in reply:
                        source.write(reply['pcm'])
                        self.capture_status['nativeOutputDroppedFrames']=reply['audio']['dropped_frames']
                    source.discarded_frames += reply.get('discarded', 0)
                    if 'underruns' in reply:
                        self.capture_status['nativeUnderruns'] = reply['underruns']
                except RuntimeError as error:
                    if 'queue is full' not in str(error):
                        raise
                    source.discarded_frames += len(pcm)//4
            self.capture_status.update(source.status(), discontinuities=self.capture_discontinuities)
        except (OSError, RuntimeError, ValueError) as error:
            self.close_capture()
            try:
                self.runtime.request('pause')
                message=f'Audio device unavailable: {error}. Sampler paused; reconnect and choose Reopen audio.'
            except (OSError,RuntimeError):
                message=f'Audio device unavailable: {error}. Emulator could not be paused; restart or restore recovery.'
            self.capture_status = {**self.capture_status,'state':'failed','message':message}

    def reopen_audio(self):
        """Recover hardware without replacing native RAM, media or controls."""
        with self.runtime_lock:
            if self.capture_status.get('state')!='failed':raise ValueError('Audio is not in a failed state')
            self.runtime.request('pause')
            self.capture_discontinuities+=1
            self.start_capture()
            if self.capture is None:raise RuntimeError(self.capture_status['message'])
            source=self.capture
            try:
                has_input=bool(source.config.asio_input_channel) if isinstance(source,AsioHost) else bool(self.runtime.config.recording_device)
                if has_input:
                    queued=self.runtime.request('input_status')[0]['queued']
                    received=0;deadline=time.monotonic()+2
                    while received<8192:
                        source.status()
                        for pcm in source.read():
                            frames=len(pcm)//4;received+=frames
                            if queued+frames<=16384:
                                reply=self.runtime.queue_input_pcm(pcm,binary=True) if isinstance(source,AsioHost) else self.runtime.queue_input_pcm(pcm)
                                queued=reply['queued']
                            else:source.discarded_frames+=frames
                        if time.monotonic()>deadline:raise OSError('Audio input did not re-prime; sampler remains paused')
                        if received<8192:time.sleep(.005)
                    self.capture_pending=[];self.capture_primed=True
                self.runtime.request('resume')
                self.capture_status.update(discontinuities=self.capture_discontinuities)
                return {'type':'AUDIO_REOPENED','recordingStatus':dict(self.capture_status)}
            except (OSError,RuntimeError,ValueError) as error:
                self.close_capture()
                self.capture_status={'state':'failed','message':f'Audio reopen failed: {error}. Sampler remains paused.'}
                raise RuntimeError(self.capture_status['message']) from error

    def configure(self, payload):
        r = self.runtime
        boot, disk, folder = (Path(payload[key]).expanduser().resolve()
                              for key in ('bootRom','systemDisk','mediaDirectory'))
        if not boot.is_file() or boot.stat().st_size != 32768:
            raise ValueError('Boot ROM must be a readable 32KB IC15 image')
        if not disk.is_file() or disk.stat().st_size != 1474560:
            raise ValueError('System disk must be a readable 1.44MB image')
        media = media_index(folder)
        slot = r.config.state_dir/'inserted-floppy.img'
        candidate = replace(r.config, boot_rom=boot, system_disk=disk, sound=payload['sound'],
                            wave_memory_mb=payload.get('waveMemoryMb',getattr(r.config,'wave_memory_mb',32)),
                            audio_backend=payload.get('audioBackend', r.config.audio_backend),
                            audio_latency_ms=payload.get('audioLatencyMs', r.config.audio_latency_ms),
                            audio_output_device=payload.get('audioOutputDevice',getattr(r.config,'audio_output_device','')),
                            recording_device=payload.get('recordingDevice',getattr(r.config,'recording_device','')),
                            sample_disk=slot if slot.exists() else disk)
        candidate = replace(candidate, **{field:payload[key] for key,field in ASIO_SETTINGS.items() if key in payload})
        candidate.validate()
        if candidate.audio_backend in ('auto','wasapi') and candidate.audio_output_device:
            if not any(d['id']==candidate.audio_output_device for d in windows_outputs()):
                raise ValueError('Selected Windows output endpoint is unavailable')
        if candidate.audio_backend=='asio':
            inventory=asio_devices()
            driver=next((d for d in inventory if d['name']==candidate.asio_driver),None)
            if not driver:raise ValueError('Selected ASIO driver is unavailable')
            if candidate.asio_output_channel+1>driver['outputs'] or (candidate.asio_input_channel and candidate.asio_input_channel+1>driver['inputs']):
                raise ValueError('Selected ASIO stereo channel pair is unavailable')
        elif candidate.recording_device and not any(d['id']==candidate.recording_device for d in recording_devices()):
            raise ValueError('Recording device is unavailable; refresh devices and select it again')
        if r.process is not None and r.process.poll() is None:
            status = r.media_status()
            if status['dirty'] or status['busy']:
                raise RuntimeError('Export disk writes and wait for disk activity before applying settings')
        self.close_capture()
        r.close()
        self.midi_input = ''
        r.config = candidate
        self.media_dir = folder
        self.media = media
        self.readiness = None
        try:
            r.start()
        except (OSError, RuntimeError, ValueError) as error:
            self.startup_error = str(error)
            raise
        self.startup_error = None
        self.start_capture()
        self.hold_recovery()
        self.firmware_status = {'type':'FIRMWARE_STATUS','state':'booting','message':'Settings applied; booting firmware…'}
        # Publish only after successful native startup; preserve the previous file on failure.
        settings = {'version':1, **self.configuration()}
        target = r.config.state_dir/'settings.json'
        temporary = target.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(settings,indent=2),encoding='utf-8')
        temporary.replace(target)
        return {'type':'CONFIGURATION_APPLIED','configuration':self.configuration(),'media':sorted(media)}

    @property
    def session_path(self):
        return self.runtime.config.state_dir/'sessions'/'latest.s760state'

    @property
    def recovery_path(self):
        return self.runtime.config.state_dir/'sessions'/'recovery.s760state'

    def recovery_status(self):
        path = self.recovery_path
        return {'available':path.is_file(), 'pending':self.recovery_pending,
                'savedAt':path.stat().st_mtime if path.is_file() else None,
                'message':self.recovery_message}

    def hold_recovery(self):
        if self.recovery_path.is_file():
            self.recovery_pending = True
            self.recovery_message = 'Existing recovery preserved. Restore it or start a new recovery history.'

    def save_recovery(self):
        with self.runtime_lock:
            if self.recovery_pending:
                raise RuntimeError('Existing recovery preserved. Restore it or start a new recovery history first.')
            r = self.runtime
            running = r.request('status')[0]['state'] == 'running'
            if not running: r.request('resume')
            try:
                if r.media_status()['busy']:
                    raise RuntimeError('Floppy controller is busy; recovery deferred until the disk operation finishes')
            finally:
                if not running: r.request('pause')
            with self.capture_transaction():
                r.request('pause')
                try:
                    self.recovery_path.parent.mkdir(parents=True, exist_ok=True)
                    r.save_checkpoint(self.recovery_path)
                finally:
                    if running: r.request('resume')
            self.recovery_message = 'Recovery saved. Changes after this checkpoint can still be lost on failure.'
            self.next_recovery = time.monotonic() + 60
            return self.recovery_status()

    def automatic_recovery(self):
        with self.runtime_lock:
            if self.recovery_pending or self.startup_error or self.closing or not self.firmware_status.get('booted') or time.monotonic() < self.next_recovery:
                return
            self.next_recovery = time.monotonic() + 60
            try:
                self.save_recovery()
            except (OSError, RuntimeError, ValueError) as error:
                self.recovery_message = f'Recovery not saved: {error}. Previous recovery retained; save or export work before closing.'

    def prepare_close(self):
        with self.runtime_lock:
            if self.closing: return True
            r = self.runtime
            if self.startup_error or r.process is None or r.process.poll() is not None:
                return True # A dead/unstarted child cannot produce a newer checkpoint.
            try:
                if self.recovery_pending:
                    raise RuntimeError('Restore existing recovery or start a new recovery history first')
                self.release_controls()
                self.save_recovery()
            except (OSError, RuntimeError, ValueError) as error:
                self.recovery_message = f'Close cancelled: recovery not saved: {error}. Resolve this before closing.'
                return False
            self.closing = True
            self.stop.set()
            return True

    def release_controls(self):
        self.runtime.request('midi', bytes=[0xb0, 123, 0])
        for port, name in BUTTONS.values():
            self.runtime.request('button', port=port, name=name, down=False)
        for name in ('Mouse Left', 'Mouse Right'):
            self.runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name=name, down=False)

    def input(self, message):
        with self.runtime_lock:
            return self._input(message)

    def _input(self, message):
        kind, p = validate_input(message)
        if self.closing: raise RuntimeError('Sampler is closing')
        if kind == 'RECORDING_DEVICES':
            self.recording_devices = recording_devices()
            return {'type':'RECORDING_DEVICES','recordingDevices':self.recording_devices}
        if kind == 'ASIO_DEVICES':
            self.asio_devices=asio_devices()
            return {'type':'ASIO_DEVICES','asioDevices':self.asio_devices}
        if kind == 'AUDIO_OUTPUT_DEVICES':
            self.audio_output_devices=windows_outputs()
            return {'type':'AUDIO_OUTPUT_DEVICES','audioOutputDevices':self.audio_output_devices}
        if kind == 'REOPEN_AUDIO':return self.reopen_audio()
        r = self.runtime
        if kind == 'QUIT_WITHOUT_RECOVERY':
            self.closing = True
            self.stop.set()
            return {'type':'CLOSING'}
        if kind == 'CONFIGURE_RUNTIME': return self.configure(p)
        if kind == 'SET_STANDALONE_PREFERENCES':
            path = r.config.state_dir / 'standalone-ui.json'
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix('.tmp')
            temporary.write_text(json.dumps(p), encoding='utf-8')
            temporary.replace(path)
            self.preferences = dict(p)
            return {'type':'STANDALONE_PREFERENCES', 'preferences':self.preferences}
        if self.startup_error and kind not in ('RESTORE_SESSION', 'RESTORE_RECOVERY'):
            raise RuntimeError('Open Runtime settings, correct the paths, and apply to start the sampler')
        if kind == 'SAVE_SESSION':
            running = r.request('status')[0]['state'] == 'running'
            with self.capture_transaction():
                r.request('pause')
                try:
                    self.session_path.parent.mkdir(parents=True, exist_ok=True)
                    r.save_checkpoint(self.session_path)
                finally:
                    if running: r.request('resume')
            return {'type':'SESSION_SAVED', 'path':str(self.session_path.resolve())}
        if kind in ('SAVE_RECOVERY', 'START_RECOVERY'):
            pending = self.recovery_pending
            if kind == 'START_RECOVERY': self.recovery_pending = False
            try:
                result = self.save_recovery()
            except (OSError, RuntimeError, ValueError):
                self.recovery_pending = pending
                raise
            return {'type':'RECOVERY_STATUS','recovery':result}
        if kind in ('RESTORE_SESSION', 'RESTORE_RECOVERY'):
            source = self.recovery_path if kind == 'RESTORE_RECOVERY' else self.session_path
            # Validate before pausing/closing any live machine. The native load
            # validates again before mutation; no client-supplied path is used.
            r.validate_checkpoint(source)
            alive = r.process is not None and r.process.poll() is None
            running = True
            if alive:
                running = r.request('status')[0]['state'] == 'running'
                # Media acknowledgement is delivered by normal input polling.
                # A paused runtime must run briefly for that request to finish.
                if not running: r.request('resume')
                try:
                    media = r.media_status()
                finally:
                    if not running: r.request('pause')
                if media['dirty'] or media['busy']:
                    raise RuntimeError('Export disk writes and wait for the disk operation before restoring')
            else:
                r.close()
                # The checkpoint owns floppy bytes; a missing/relocated source
                # image must not prevent launching the replacement machine.
                if getattr(r.config, 'sample_disk', None) is not None:
                    r.config = replace(r.config, sample_disk=None)
                r.start()
            with self.capture_transaction():
                r.request('pause')
                # If native application fails, leave execution paused for diagnosis.
                r.load_checkpoint(source)
            if kind == 'RESTORE_RECOVERY':
                self.recovery_pending = False
                self.recovery_message = 'Recovery restored. Automatic recovery resumes in 60 seconds.'
                self.next_recovery = time.monotonic() + 60
            else:
                self.hold_recovery()
            self.startup_error = None
            self.readiness = None
            if running: r.request('resume')
            self.firmware_status = {'type':'FIRMWARE_STATUS','state':'booting','message':'Session restored; checking firmware…'}
            return {'type':'RECOVERY_RESTORED' if kind == 'RESTORE_RECOVERY' else 'SESSION_RESTORED',
                    'path':str(source.resolve()), 'recovery':self.recovery_status()}
        if kind == 'RESTART_RUNTIME':
            if r.process is not None and r.process.poll() is None:
                status = r.media_status()
                if status['dirty'] or status['busy']:
                    raise RuntimeError('Export disk writes and wait for the disk operation before restarting')
            self.close_capture()
            self.capture_discontinuities += 1
            r.close()
            self.midi_input = ''
            self.readiness = None
            self.firmware_status = {'type':'FIRMWARE_STATUS','state':'booting','message':'Restarting firmware…','midiInput':''}
            try:
                r.start()
                self.start_capture()
                self.hold_recovery()
            except Exception as error:
                self.firmware_status = {'type':'FIRMWARE_STATUS','state':'failed','message':f'Restart failed: {error}'}
                raise
            return self.firmware_status
        if kind in ('BUTTON_PRESS', 'BUTTON_RELEASE'):
            port, name = BUTTONS[p['id']]
            r.request('button', port=port, name=name, down=kind == 'BUTTON_PRESS')
        elif kind == 'DIAL_DELTA':
            r.request('dial', id=p['id'], delta=p['delta'])
        elif kind == 'MOUSE_MOVE':
            # Default firmware mouse scale; live smoke tests cover this mapping.
            r.request('pointer', x=round(p['x'] * 159), y=round(p['y'] * 119))
        elif kind == 'MOUSE_BUTTON':
            r.request('button', port=':NATIVE_MOUSE_BUTTONS',
                      name='Mouse Left' if p['button'] == 0 else 'Mouse Right', down=p['down'])
        elif kind in ('NOTE_ON', 'NOTE_OFF'):
            r.request('midi', bytes=[0x90 if kind == 'NOTE_ON' else 0x80, p['note'], p['velocity']])
        elif kind == 'MIDI_DEVICE':
            if p['name'] and p['name'] not in self.midi_devices:
                raise ValueError('MIDI device is not in the available input list')
            r.request('midi_device', name=p['name'])
            self.midi_input = p['name']
            return {'type':'MIDI_DEVICE_SELECTED', 'name':self.midi_input}
        elif kind == 'MOUNT_DISK':
            source = self.media.get(p['diskPath'])
            if source is None:
                raise ValueError('Disk is not in the configured media library')
            media = r.insert_media(source)
            return {'type': 'MEDIA_INSERTED', 'name': source.name, 'mediaStatus': media}
        elif kind == 'MEDIA_STATUS':
            running = r.request('status')[0]['state'] == 'running'
            if not running: r.request('resume')
            try:
                media = r.media_status()
            finally:
                if not running: r.request('pause')
            return {'type': 'MEDIA_STATUS', 'mediaStatus': media}
        elif kind == 'MEDIA_WRITE_PROTECT':
            return {'type': 'MEDIA_PROTECTION', 'mediaStatus': r.set_media_write_protect(p['enabled'])}
        elif kind == 'EJECT_DISK':
            r.eject_media()
            return {'type': 'MEDIA_EJECTED'}
        elif kind == 'EXPORT_DISK':
            folder = r.config.state_dir / 'exports'
            folder.mkdir(exist_ok=True)
            target = folder / f's760-{time.strftime("%Y%m%d-%H%M%S")}-{secrets.token_hex(4)}.img'
            r.export_media(target)
            return {'type': 'MEDIA_EXPORTED', 'path': str(target.resolve())}

    def poll(self):
        with self.runtime_lock:
            if self.startup_error:
                self.firmware_status = {'type':'FIRMWARE_STATUS','state':'configuration',
                    'message':f'Sampler needs configuration: {self.startup_error}. Open Runtime settings to retry.'}
                return []
            try:
                info, frames = self.runtime.request('frames')
                if self.readiness is None:
                    supported = hashlib.sha256(self.runtime.config.system_disk.read_bytes()).hexdigest() == SYSTEM_SHA256
                    self.readiness = FirmwareReadiness(supported)
                self.firmware_status = self.readiness.observe(frames[0], info['seconds'], info.get('paused',False))
                self.firmware_status['outputLevel'] = info.get('output_level', 100)
                self.firmware_status['inputLevel'] = info.get('input_level', 100)
                self.firmware_status['recordingStatus'] = dict(self.capture_status)
                return frames
            except (OSError, RuntimeError) as error:
                self.firmware_status = {'type':'FIRMWARE_STATUS','state':'failed',
                    'message':f'Emulator unavailable: {error}. Restore a saved session or restart; changes since the last save may be lost.'}
                return []

    def stream(self):
        while not self.stop.is_set():
            start = time.monotonic()
            with self.runtime_lock:
                frames = self.poll()
                self.automatic_recovery()
                self.firmware_status['recovery'] = self.recovery_status()
                update = (frames, dict(self.firmware_status))
            with self.client_lock:
                clients = list(self.clients.values())
            for pending in clients:
                try:
                    pending.put_nowait(update)
                except queue.Full:
                    try: pending.get_nowait()
                    except queue.Empty: pass
                    try: pending.put_nowait(update)
                    except queue.Full: pass
            self.stop.wait(max(0, 1 / 15 - (time.monotonic() - start)))

    def connect(self, connection):
        pending = queue.Queue(maxsize=1)
        disconnected = threading.Event()
        with self.client_lock:
            self.clients[connection] = pending
        def display_sender():
            while not disconnected.is_set() and not self.stop.is_set():
                try:
                    frames, status = pending.get(timeout=.2)
                    connection.send(json.dumps(status))
                    for frame in frames:
                        connection.send(frame)
                except queue.Empty:
                    continue
                except ConnectionClosed:
                    return
        sender = threading.Thread(target=display_sender, daemon=True)
        sender.start()
        try:
            connection.send(json.dumps({'type': 'SESSION', 'media': sorted(self.media),
                                        'midiDevices': self.midi_devices, 'recordingDevices':self.recording_devices, 'asioDevices':self.asio_devices, 'audioOutputDevices':self.audio_output_devices,'warning': self.midi_warning,
                                        'midiInput':self.midi_input, 'preferences':self.preferences,
                                        'configuration':self.configuration(), 'needsConfiguration':bool(self.startup_error),
                                        'savedSession': self.session_path.is_file(),
                                        'recovery':self.recovery_status(),
                                        'status': 'running', 'audio': 'MAME output'}))
            for raw in connection:
                try:
                    if not isinstance(raw, str):
                        raise ValueError('Expected JSON input')
                    result = self.input(json.loads(raw))
                    if result is not None:
                        connection.send(json.dumps(result))
                except (ValueError, RuntimeError, OSError) as error:
                    connection.send(json.dumps({'type': 'ERROR', 'message': str(error)}))
        except ConnectionClosed:
            pass
        finally:
            disconnected.set()
            with self.client_lock:
                self.clients.pop(connection, None)
            # Avoid stuck notes and panel/mouse buttons when a browser closes.
            with self.runtime_lock:
                try:
                    self.release_controls()
                except (OSError, RuntimeError):
                    pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', type=Path, default=ROOT / 'docs/ic20-hle-findings/chatGPT-work/standalone-state')
    parser.add_argument('--media-dir', type=Path, default=None)
    parser.add_argument('--boot-rom', type=Path, default=None)
    parser.add_argument('--system-disk', type=Path, default=None)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--browser', action='store_true', help='Use an external browser instead of the desktop window')
    parser.add_argument('--no-sound', action='store_true')
    parser.add_argument('--recording-device',default=None,help='Exact Windows recording device ID from Configuration')
    parser.add_argument('--wave-memory-mb',type=int,choices=(8,16,32))
    parser.add_argument('--audio-backend', choices=('auto', 'wasapi', 'xaudio2', 'asio'),
                        help='Windows MAME output backend (default: saved setting or auto)')
    parser.add_argument('--audio-latency-ms', type=float,
                        help='Output buffer target, 0 for backend default, up to 1000 ms; not measured latency')
    parser.add_argument('--asio-driver')
    parser.add_argument('--asio-output-channel',type=int)
    parser.add_argument('--asio-input-channel',type=int)
    parser.add_argument('--asio-buffer-frames',type=int)
    parser.add_argument('--fast', action='store_true', help='Unthrottled integration testing only')
    parser.add_argument('--seconds', type=float, default=0, help='Stop after a bounded test duration')
    parser.add_argument('--verify-desktop', action='store_true', help='Record live WebView canvas evidence, then exit')
    args = parser.parse_args()
    assets = ROOT / 'google-ui/dist'
    if not (assets / 'index.html').is_file():
        parser.error('Build the React UI first: cd google-ui; npm run build')
    args.state_dir.mkdir(parents=True, exist_ok=True)
    settings_warning = None
    try:
        settings = load_settings(args.state_dir)
    except (OSError, ValueError) as error:
        settings, settings_warning = {}, f'Could not read saved settings: {error}'
    defaults = default_media_paths(ROOT)
    args.boot_rom = args.boot_rom or Path(settings.get('bootRom', defaults['bootRom']))
    args.system_disk = args.system_disk or Path(settings.get('systemDisk', defaults['systemDisk']))
    args.media_dir = args.media_dir or Path(settings.get('mediaDirectory', defaults['mediaDirectory']))
    media_slot = args.state_dir / 'inserted-floppy.img'
    cfg = RuntimeConfig(ROOT / 'mame-source/mames760.exe', args.boot_rom, args.system_disk,
                        args.state_dir, media_slot if media_slot.exists() else args.system_disk,
                        False if args.no_sound else settings.get('sound',True), not args.fast,
                        wave_memory_mb=args.wave_memory_mb or settings.get('waveMemoryMb',32),
                        audio_backend=args.audio_backend or settings.get('audioBackend', 'auto'),
                        audio_output_device=settings.get('audioOutputDevice',''),
                        audio_latency_ms=args.audio_latency_ms if args.audio_latency_ms is not None
                            else settings.get('audioLatencyMs', 0),
                        recording_device=args.recording_device if args.recording_device is not None else settings.get('recordingDevice',''),
                        scsi_library=ROOT/'roms/SCSI' if getattr(sys, 'frozen', False) else None)
    cfg=replace(cfg,**{field:settings[key] for key,field in ASIO_SETTINGS.items() if key in settings})
    cfg=replace(cfg,**{field:getattr(args,field) for field in ASIO_SETTINGS.values() if getattr(args,field) is not None})
    try:
        cfg.audio_arguments()
    except ValueError as error:
        parser.error(str(error))
    token = secrets.token_urlsafe(32)
    http = ThreadingHTTPServer(('127.0.0.1', 0), partial(AssetHandler, directory=str(assets)))
    origin = f'http://127.0.0.1:{http.server_port}'
    def authorize(connection, request):
        if parse_qs(urlsplit(request.path).query).get('token') != [token]:
            return connection.respond(403, 'Invalid session token\n')
    with closing(NativeRuntime(cfg)) as runtime:
        startup_error = settings_warning
        try:
            if startup_error: raise ValueError(startup_error)
            media_index(args.media_dir)
            runtime.start()
        except (OSError, RuntimeError, ValueError) as error:
            startup_error = str(error)
        session = StandaloneSession(runtime, args.media_dir, startup_error)
        with serve(session.connect, '127.0.0.1', 0, origins=[origin], process_request=authorize,
                   max_size=4096, max_queue=16, compression=None) as ws:
            port = ws.socket.getsockname()[1]
            url = f'{origin}/?native=1&port={port}&token={token}'
            threads = [threading.Thread(target=target, daemon=True) for target in
                       (http.serve_forever, ws.serve_forever, session.stream, session.capture_worker)]
            for thread in threads:
                thread.start()
            print(url, flush=True)
            (args.state_dir / 'session.json').write_text(json.dumps({'url': url}), encoding='utf-8')
            try:
                if args.no_browser or args.browser:
                    if args.browser:
                        webbrowser.open(url)
                    session.stop.wait(args.seconds if args.seconds > 0 else None)
                else:
                    import webview
                    window = webview.create_window('Roland S-760', url, width=1100, height=1050,
                                                   min_size=(760, 700), background_color='#0a0c0f')
                    window.events.closing += session.prepare_close
                    def watch_window():
                        if args.verify_desktop:
                            try:
                                if not window.events.loaded.wait(20):
                                    raise RuntimeError('Desktop page did not load')
                                deadline = time.monotonic() + 25
                                while time.monotonic() < deadline:
                                    result = window.evaluate_js('''(() => {
                                      const c=document.querySelector('canvas[aria-label="Native CRT"]');
                                      if(!c) return null;
                                      const pixels=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
                                      let nonzero=0;for(let i=0;i<pixels.length;i+=4) if(pixels[i]||pixels[i+1]||pixels[i+2])nonzero++;
                                      return {status:document.querySelector('[role="status"]')?.textContent,
                                              width:c.width,height:c.height,nonzero};
                                    })()''')
                                    if result and result['nonzero'] > 1000 and result['status'] == 'OS ready — Perform Play.':
                                        (args.state_dir / 'desktop-verification.json').write_text(json.dumps(result, indent=2))
                                        break
                                    time.sleep(.2)
                                else:
                                    raise RuntimeError('No live desktop pixels received')
                            except Exception as error:
                                session.failure = str(error)
                            session.stop.set()
                        session.stop.wait(args.seconds if args.seconds > 0 else None)
                        window.destroy()
                    webview.start(watch_window, gui='edgechromium',
                                  storage_path=str((args.state_dir / 'webview').resolve()))
            except KeyboardInterrupt:
                pass
            finally:
                if not session.prepare_close():
                    session.failure = session.recovery_message
                session.stop.set()
                ws.shutdown()
                http.shutdown()
                threads[2].join(timeout=6)
                threads[3].join(timeout=6)
                with session.runtime_lock:
                    session.close_capture()
                http.server_close()
            if session.failure:
                raise RuntimeError(session.failure)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        import sys
        if getattr(sys,'frozen',False):
            import traceback
            try:
                position=sys.argv.index('--state-dir')
                diagnostic=Path(sys.argv[position+1])/'startup-error.log'
                diagnostic.parent.mkdir(parents=True,exist_ok=True)
                diagnostic.write_text(traceback.format_exc(),encoding='utf-8')
            except (ValueError,IndexError,OSError):
                pass
        if getattr(sys, 'frozen', False) and '--no-browser' not in sys.argv and '--verify-desktop' not in sys.argv:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, str(error), 'S-760 could not start', 0x10)
        raise
