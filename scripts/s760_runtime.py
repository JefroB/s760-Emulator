"""One isolated native MAME machine. No React or audio-device ownership here.

The request/response protocol is deliberately independent of the browser wire
protocol. A future native/plugin client can use the same machine boundary.
Live PCM can be drained from MAME; sample-clocked plugin audio is not implemented.
"""
from dataclasses import dataclass
import json
import math
import hashlib
import os
from pathlib import Path
import secrets
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET


def application_root():
    return Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]


def midi_inputs(executable):
    result = subprocess.run([str(executable), '-listmidi'], capture_output=True, text=True,
                            timeout=10, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), check=True)
    names, reading = [], False
    for line in result.stdout.splitlines():
        if line == 'MIDI input ports:':
            reading = True
        elif line == 'MIDI output ports:':
            break
        elif reading and line.strip():
            names.append(line.removesuffix(' (default)'))
    return names


def stage_audio_mapping(config):
    """Own only this standalone's private MAME speaker endpoint mappings."""
    path=config.state_dir/'cfg/s760.cfg'
    selected=config.audio_output_device if config.audio_backend in ('auto','wasapi') else ''
    if not selected and not path.exists():return
    tree=ET.parse(path) if path.exists() else ET.ElementTree(ET.Element('mameconfig',version='10'))
    root=tree.getroot();system=root.find("system[@name='s760']")
    if system is None:system=ET.SubElement(root,'system',name='s760')
    mixer=system.find('mixer')
    if mixer is None:mixer=ET.SubElement(system,'mixer')
    for mapping in list(mixer.findall('sound_map')):
        if mapping.get('tag') in (':lspeaker',':rspeaker'):mixer.remove(mapping)
    if selected:
        for channel,tag in enumerate((':lspeaker',':rspeaker')):
            mapping=ET.SubElement(mixer,'sound_map',tag=tag)
            ET.SubElement(mapping,'channel_mapping',guest_channel='0',node='o:'+selected,node_channel=str(channel),db='0')
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.cfg.tmp');tree.write(temporary,encoding='utf-8',xml_declaration=True)
    os.replace(temporary,path)


def read_exact(connection, size):
    data = bytearray()
    while len(data) < size:
        chunk = connection.recv(size - len(data))
        if not chunk:
            raise ConnectionError('MAME runtime disconnected')
        data.extend(chunk)
    return bytes(data)


def surface_frame(surface, width, height, pixels):
    expected = {0: (640, 240), 1: (160, 64)}
    if expected.get(surface) != (width, height) or len(pixels) != width * height * 4:
        raise ValueError('Invalid native display geometry or payload')
    if surface == 0:
        rgba = bytearray(len(pixels))
        rgba[0::4], rgba[1::4], rgba[2::4] = pixels[2::4], pixels[1::4], pixels[0::4]
        rgba[3::4] = b'\xff' * (width * height)
        rows = [rgba[y * width * 4:(y + 1) * width * 4] for y in range(height)]
        return struct.pack('<BHHB', 0, width, height * 2, 0) + b''.join(row * 2 for row in rows)
    packed = bytearray(width * height // 8)
    for i in range(width * height):
        if any(pixels[i * 4:i * 4 + 3]):
            packed[i // 8] |= 0x80 >> (i % 8)
    return struct.pack('<BHHB', 1, width, height, 1) + packed


def audio_payload_size(descriptor):
    frames = descriptor.get('frames')
    if (type(frames) is not int or not 0 <= frames <= 44100
            or descriptor.get('channels') != 2 or descriptor.get('rate') != 44100):
        raise ValueError('Invalid native PCM descriptor')
    return frames * 8  # Interleaved stereo IEEE float32, little endian.


@dataclass
class RuntimeConfig:
    executable: Path
    boot_rom: Path
    system_disk: Path
    state_dir: Path
    sample_disk: Path | None = None
    sound: bool = True
    throttle: bool = True
    wav_output: Path | None = None
    wave_dump: Path | None = None
    audio_backend: str = 'auto'
    audio_latency_ms: float = 0
    audio_output_device: str = ''
    experimental_adc: bool = False
    recording_device: str = ''
    asio_driver: str = ''
    asio_output_channel: int = 1
    asio_input_channel: int = 0
    asio_buffer_frames: int = 512

    def audio_arguments(self):
        """OSD buffer target only; native transport stays stereo 44100 Hz."""
        if self.audio_backend not in ('auto', 'wasapi', 'xaudio2', 'asio'):
            raise ValueError('Audio backend must be auto, wasapi, xaudio2 or asio')
        if not isinstance(self.audio_output_device,str) or len(self.audio_output_device)>256 or '\0' in self.audio_output_device:
            raise ValueError('Invalid Windows output endpoint')
        if not isinstance(self.asio_driver,str) or len(self.asio_driver)>256 or '\0' in self.asio_driver:
            raise ValueError('Invalid ASIO driver')
        for channel, minimum in ((self.asio_output_channel,1),(self.asio_input_channel,0)):
            if type(channel) is not int or not minimum<=channel<=255:
                raise ValueError('Invalid ASIO stereo channel pair')
        if type(self.asio_buffer_frames) is not int or self.asio_buffer_frames not in (64,128,256,512,1024,2048):
            raise ValueError('Invalid ASIO buffer size')
        if self.audio_backend=='asio' and not self.asio_driver.strip():
            raise ValueError('Select an ASIO driver')
        latency = self.audio_latency_ms
        if (type(latency) not in (int, float) or not math.isfinite(latency)
                or not 0 <= latency <= 1000):
            raise ValueError('Audio buffer target must be finite and between 0 and 1000 ms')
        backend='wasapi' if self.audio_output_device and self.audio_backend=='auto' else self.audio_backend
        return ['-sound', backend if self.sound and backend!='asio' else 'none',
                '-audio_latency', format(latency / 20, 'g')]

    def validate(self):
        self.audio_arguments()
        if not isinstance(self.recording_device, str) or len(self.recording_device)>256 or '\0' in self.recording_device:
            raise ValueError('Invalid recording device')
        if (self.recording_device or self.audio_backend=='asio') and not self.throttle:
            raise ValueError('Live recording requires normal-speed emulation; disable --fast')
        for path in (self.executable, self.boot_rom, self.system_disk, self.sample_disk):
            if path is not None and not path.is_file():
                raise FileNotFoundError(path)
        if self.system_disk.stat().st_size != 1474560:
            raise ValueError('Expected a 1.44MB S-760 system disk')


class NativeRuntime:
    """Own process, connection and per-instance state. Calls are serialized."""
    def __init__(self, config):
        self.config = config
        self.process = None
        self.scsi_identity = None
        self.media_lock = threading.Lock()
        self.connection = None
        self.midi_connection = None
        self.log = None
        self.state_lock = None
        self.lock = threading.Lock()

    def start(self, timeout=30):
        if self.process is not None:
            raise RuntimeError('Runtime is already started')
        try:
            self._start(timeout)
        except BaseException:
            self.close()
            raise

    def _start(self, timeout):
        self.config.validate()
        cfg = self.config
        if cfg.audio_output_device and cfg.audio_backend in ('auto','wasapi'):
            from s760_asio import windows_outputs
            if not any(d['id']==cfg.audio_output_device for d in windows_outputs()):
                raise ValueError('Selected Windows output endpoint is unavailable; refresh outputs and select it again')
        self.scsi_identity = self._scsi_identity()
        cfg.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_lock = (cfg.state_dir / 'runtime.lock').open('a+b')
        if self.state_lock.tell() == 0:
            self.state_lock.write(b'\0')
            self.state_lock.flush()
        self.state_lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.state_lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.state_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.state_lock.close()
            self.state_lock = None
            raise RuntimeError('State directory is in use; choose a different --state-dir') from None
        root = application_root()
        # MAME's ROM definition expects this exact set/name. Stage the selected
        # user image privately so packaged launches don't rely on a repo ROM tree.
        rom_dir = cfg.state_dir / 'roms' / 's760'
        rom_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cfg.system_disk, rom_dir / 's760224.img')
        env = {k: v for k, v in os.environ.items() if not k.startswith('S760_')}
        token = secrets.token_hex(24)
        with socket.socket() as listener, socket.socket() as midi_listener:
            listener.bind(('127.0.0.1', 0))
            listener.listen(1)
            listener.settimeout(0.25)
            midi_listener.bind(('127.0.0.1', 0))
            midi_listener.listen(1)
            midi_listener.settimeout(.25)
            env.update(S760_ROM_BOOT=str(cfg.boot_rom.resolve()), S760_FLOPPY=str(cfg.system_disk.resolve()),
                       S760_MEDIA_EXPORT=str((cfg.state_dir / 'media-export.img').resolve()),
                       S760_MEDIA_STATUS=str((cfg.state_dir / 'media-status.json').resolve()),
                       S760_F00A='00', S760_IC4_MIDI_EXPERIMENT='1', S760_NATIVE_INTERPOLATION_MONITOR='1',
                       S760_NATIVE_VALUE_ENCODER='1',
                       S760_RUNTIME_PORT=str(listener.getsockname()[1]), S760_RUNTIME_TOKEN=token,
                       S760_RUNTIME_MIDI_PORT=str(midi_listener.getsockname()[1]))
            slot = cfg.state_dir / 'inserted-floppy.img'
            if cfg.sample_disk and cfg.sample_disk.resolve() != slot.resolve():
                shutil.copyfile(cfg.sample_disk, slot)
            env['S760_SAMPLE_FLOPPY'] = str(slot.resolve())
            if cfg.experimental_adc or cfg.recording_device or (cfg.audio_backend=='asio' and cfg.asio_input_channel):
                env['S760_NATIVE_ADC'] = '1'
            if cfg.audio_backend=='asio':
                env['S760_ASIO_CLOCK'] = '1'
            if cfg.wave_dump:
                env['S760_VDP_TRACE'] = '1'  # Existing exit observer, no guest writes.
                env['S760_WAVE_DUMP'] = str(cfg.wave_dump.resolve())
            stage_audio_mapping(cfg)
            command = [str(cfg.executable.resolve()), 's760', '-rompath',
                       str(rom_dir.parent.resolve()),
                       '-pluginspath', str(root / 'mame-source/plugins'),
                       '-nvram_directory', str((cfg.state_dir / 'nvram').resolve()),
                       '-cfg_directory', str((cfg.state_dir / 'cfg').resolve()),
                       '-snapshot_directory', str(cfg.state_dir.resolve()),
                       '-autoboot_delay', '0', '-autoboot_script', str(root / 'scripts/s760_runtime.lua'),
                       '-video', 'none', '-window', '-skip_gameinfo', '-samplerate', '44100',
                       '-throttle' if cfg.throttle else '-nothrottle']
            command += cfg.audio_arguments()
            if cfg.wav_output:
                command += ['-wavwrite', str(cfg.wav_output.resolve())]
            self.log = (cfg.state_dir / 'runtime.log').open('wb')
            try:
                self.process = subprocess.Popen(command, cwd=cfg.state_dir.resolve(), env=env,
                    stdout=self.log, stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                deadline = time.monotonic() + timeout
                while self.midi_connection is None:
                    if self.process.poll() is not None:
                        raise RuntimeError(f'MAME exited {self.process.returncode}; see {cfg.state_dir / "runtime.log"}')
                    if time.monotonic() >= deadline:
                        raise TimeoutError('MAME MIDI startup timed out')
                    try:
                        self.midi_connection, _ = midi_listener.accept()
                    except socket.timeout:
                        continue
                self.midi_connection.settimeout(5)
                if read_exact(self.midi_connection, len(token)) != token.encode():
                    raise ConnectionError('Invalid MIDI runtime handshake')
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    if self.process.poll() is not None:
                        raise RuntimeError(f'MAME exited {self.process.returncode}; see {cfg.state_dir / "runtime.log"}')
                    try:
                        self.connection, _ = listener.accept()
                        self.connection.settimeout(5)
                        hello = self._receive()
                        if hello != {'protocol': 1, 'token': token}:
                            raise ConnectionError('Invalid runtime handshake')
                        return
                    except socket.timeout:
                        if self.connection is not None:
                            raise TimeoutError('MAME handshake timed out')
                raise TimeoutError('MAME startup timed out')
            except BaseException:
                self.close()
                raise

    def _receive(self):
        length, = struct.unpack('<I', read_exact(self.connection, 4))
        if length > 65536:
            raise ValueError('Oversized runtime response')
        return json.loads(read_exact(self.connection, length))

    def request(self, operation, **kwargs):
        pcm=kwargs.pop('_pcm',None)
        if operation=='input_audio_binary' and pcm is None:raise ValueError('Missing binary PCM frame')
        if pcm is not None and (operation!='input_audio_binary' or not isinstance(pcm,(bytes,bytearray))
                or not 4<=len(pcm)<=8192 or len(pcm)%4 or type(kwargs.get('frames')) is not int or kwargs['frames']!=len(pcm)//4):
            raise ValueError('Invalid binary PCM frame')
        with self.lock:
            if self.connection is None or self.process.poll() is not None:
                raise ConnectionError('MAME is not running')
            if operation == 'midi':
                packet = kwargs.get('bytes', [])
                if not 1 <= len(packet) <= 256 or any(type(b) is not int or not 0 <= b <= 255 for b in packet):
                    raise ValueError('Invalid MIDI packet')
                self.midi_connection.sendall(bytes(packet))
                return {'ok': True}, []
            self.connection.sendall((json.dumps({'op': operation, **kwargs}) + '\n').encode()+(pcm or b''))
            response = self._receive()
            if not response.get('ok'):
                raise RuntimeError(response.get('error', 'Runtime command failed'))
            if 'audio' in response:
                response['pcm'] = read_exact(self.connection, audio_payload_size(response['audio']))
            frames = []
            for descriptor in response.get('surfaces', []):
                surface, width, height = descriptor
                if (surface, width, height) not in ((0, 640, 240), (1, 160, 64)):
                    raise ValueError('Invalid runtime surface')
                frames.append(surface_frame(surface, width, height,
                                           read_exact(self.connection, width * height * 4)))
            return response, frames

    @staticmethod
    def _clock_arguments(clock_rate):
        if clock_rate is None:
            return {}
        if type(clock_rate) not in (int,float) or not math.isfinite(clock_rate) or not .97<=clock_rate<=1.03:
            raise ValueError('Device clock pacing must be finite and between0.97 and1.03')
        return {'clock_rate':clock_rate}

    def read_audio(self, clock_rate=None):
        """Drain bounded native PCM on a worker; never call from a DAW callback."""
        response, _ = self.request('audio', **self._clock_arguments(clock_rate))
        return response['audio'], response['pcm']

    def queue_input_pcm(self, pcm, rate=44100, channels=2, live=False, duplex=False, clock_rate=None, binary=False):
        """Queue interleaved little-endian PCM16 on the opt-in native ADC.

        Worker/offline only; each atomic submission contains 1-2048 frames.
        Live mode accepts running input and discards input while paused.
        Unsupported formats and malformed blocks fail before transport.
        """
        if type(rate) is not int or rate != 44100 or type(channels) is not int or channels != 2:
            raise ValueError('Input requires 44100Hz stereo PCM16')
        if not isinstance(pcm, (bytes, bytearray)) or not 4 <= len(pcm) <= 8192 or len(pcm) % 4:
            raise ValueError('Expected 1 to 2048 complete stereo PCM16 frames')
        if type(binary) is not bool:raise ValueError('Binary PCM mode must be boolean')
        if type(live) is not bool:
            raise ValueError('Live input mode must be boolean')
        if type(duplex) is not bool or (duplex and not live):
            raise ValueError('Duplex input requires live mode')
        arguments = dict(rate=rate, channels=channels, **self._clock_arguments(clock_rate))
        if binary:arguments.update(frames=len(pcm)//4,_pcm=bytes(pcm))
        else:arguments['samples']=list(struct.unpack('<'+'h'*(len(pcm)//2),pcm))
        if live:
            arguments['live'] = True
        if duplex:
            arguments['output'] = True
        response, _ = self.request('input_audio_binary' if binary else 'input_audio', **arguments)
        return response

    def render_audio(self, frames):
        """Worker/offline pull. MAME must be paused with capture enabled."""
        if type(frames) is not int or not 1 <= frames <= 8192:
            raise ValueError('Render frame count must be an integer from 1 to 8192')
        response, _ = self.request('render', frames=frames)
        if response['audio']['frames'] != frames:
            raise ValueError('Incomplete native render block')
        return response['audio'], response['pcm']

    def schedule_midi(self, events):
        """Submit absolute 44100Hz emulated-time events while paused.

        Timestamp denotes transmitter enqueue time, not audible onset. The
        machine rejects past events rather than silently quantizing them.
        """
        response, _ = self.request('schedule_midi', events=events)
        return response['accepted']

    def _scsi_identity(self):
        result = {}
        total = 0
        for path in sorted((self.config.state_dir/'roms/SCSI').glob('*')):
            if not path.is_file() or path.is_symlink():
                raise ValueError('SCSI snapshot profile requires regular image files')
            total += path.stat().st_size
            if total > 64*1024*1024:
                raise ValueError('SCSI snapshot profile supports at most 64 MiB of external images')
            result[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        return result

    def _checkpoint_identity(self):
        cfg = self.config
        scsi = self._scsi_identity()
        if self.scsi_identity is not None and scsi != self.scsi_identity:
            raise ValueError('SCSI backing files changed since runtime startup')
        identity = {}
        for name, path in {'mame': cfg.executable, 'boot': cfg.boot_rom, 'system': cfg.system_disk,
                           'protocol': application_root()/'scripts/s760_runtime.lua'}.items():
            try:
                identity[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            except FileNotFoundError:
                raise ValueError(f'Session prerequisite missing: {path}. Correct the paths in Runtime settings; saved sample media is contained in the session.') from None
        identity['scsi'] = scsi
        if cfg.experimental_adc or cfg.recording_device or (cfg.audio_backend=='asio' and cfg.asio_input_channel):
            identity['experimental_adc'] = 'pcm16-stereo-44100-v1'
        return identity

    def save_checkpoint(self, destination):
        """Worker/control thread only; caller pauses and quiesces MIDI first."""
        destination = Path(destination)
        with self.media_lock:
            identity = self._checkpoint_identity()
            reply, _ = self.request('checkpoint_save')
            data = (self.config.state_dir/'runtime-checkpoint.bin').read_bytes()
            if len(data) != reply['bytes'] or len(data) > 257*1024*1024:
                raise ValueError('Invalid native checkpoint size')
            metadata = json.dumps({'version': 2, 'identity': identity, 'bytes': len(data),
                                   'sha256': hashlib.sha256(data).hexdigest()}).encode()
            pending = destination.with_name(destination.name+'.'+secrets.token_hex(8)+'.tmp')
            try:
                with pending.open('xb') as output:
                    output.write(b'S760CKP2'+struct.pack('<I', len(metadata))+metadata+data)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(pending, destination)
            finally:
                pending.unlink(missing_ok=True)

    def validate_checkpoint(self, source):
        """Read-only preflight usable even after the native child has crashed."""
        with self.media_lock:
            self._read_checkpoint(source)

    def _read_checkpoint(self, source):
        # Caller holds media_lock across validation and any subsequent load.
        source = Path(source)
        try:
            if source.stat().st_size > 258*1024*1024:
                raise ValueError('Checkpoint exceeds size limit')
            data = source.read_bytes()
        except FileNotFoundError:
            raise ValueError('No saved session was found. Reopen the original state directory or save a new session; current sampler memory has not been replaced.') from None
        if data[:8] == b'S760CKP1':
            raise ValueError('Session format version 1 is unsupported. Use the matching older application to export media; session migration is not available.')
        if len(data) < 12 or data[:8] != b'S760CKP2':
            raise ValueError('Session header is invalid or damaged. Restore a known-good backup; current sampler memory has not been replaced.')
        size, = struct.unpack_from('<I', data, 8)
        if size > 65536 or len(data) < 12+size:
            raise ValueError('Invalid checkpoint manifest size')
        try:
            meta = json.loads(data[12:12+size])
        except (ValueError, UnicodeDecodeError):
            raise ValueError('Session manifest is damaged. Restore a known-good backup; current sampler memory has not been replaced.') from None
        blob = data[12+size:]
        if not isinstance(meta, dict) or meta.get('version') != 2:
            raise ValueError('Session format version is unsupported. Reopen with the matching application; session migration is not available.')
        if meta.get('bytes') != len(blob) or meta.get('sha256') != hashlib.sha256(blob).hexdigest():
            raise ValueError('Session integrity check failed. Restore a known-good backup; current sampler memory has not been replaced.')
        expected = self._checkpoint_identity()
        saved = meta.get('identity')
        if saved != expected:
            labels = {'mame':'MAME build', 'boot':'boot ROM', 'system':'system disk',
                      'protocol':'runtime protocol', 'scsi':'SCSI backing media'}
            differences = [labels.get(key, key) for key in expected
                           if not isinstance(saved, dict) or saved.get(key) != expected[key]]
            description = ', '.join(differences) or 'identity manifest'
            action = 'Use the matching application build and firmware, then retry.'
            if 'SCSI backing media' in differences:
                action += f' Restore SCSI files with the saved names/content under {self.config.state_dir / "roms/SCSI"}.'
            raise ValueError(f'Session identity mismatch: {description}. {action} Current sampler memory has not been replaced.')
        return blob

    def load_checkpoint(self, source):
        """Validate identity and integrity before asking MAME to change state."""
        with self.media_lock:
            blob = self._read_checkpoint(source)
            slot = self.config.state_dir/'runtime-checkpoint.bin'
            slot.write_bytes(blob)
            return self.request('checkpoint_load')[0]

    def _media_control(self, name):
        status = self.config.state_dir / 'media-status.json'
        status.unlink(missing_ok=True)
        try:
            self.request('button', port=':NATIVE_MEDIA', name=name, down=True)
        finally:
            self.request('button', port=':NATIVE_MEDIA', name=name, down=False)
        deadline = time.monotonic() + 5
        while not status.exists():
            if time.monotonic() >= deadline:
                raise TimeoutError('No media acknowledgement from MAME')
            time.sleep(.01)
        result = json.loads(status.read_text())
        if result.get('ok') is not True:
            raise RuntimeError(result.get('error', 'Media operation rejected'))
        return result

    def media_status(self):
        with self.media_lock:
            return self._media_control('Floppy Media Status')

    def insert_media(self, source):
        data = Path(source).read_bytes()
        if len(data) not in (737280, 1474560):
            raise ValueError('Only 720KB/1.44MB raw floppy images are supported')
        with self.media_lock:
            status = self._media_control('Floppy Media Status')
            if status['dirty'] or status['busy']:
                raise RuntimeError('Disk is busy or has unexported changes; finish saving and export first')
            slot = self.config.state_dir / 'inserted-floppy.img'
            pending = slot.with_suffix('.pending')
            try:
                pending.write_bytes(data)
                pending.replace(slot)
            finally:
                pending.unlink(missing_ok=True)
            return self._media_control('Insert Sample Floppy')

    def eject_media(self):
        with self.media_lock:
            return self._media_control('Eject Sample Floppy')

    def set_media_write_protect(self, enabled):
        if type(enabled) is not bool:
            raise ValueError('Write protection must be a boolean')
        with self.media_lock:
            return self._media_control('Protect Sample Floppy' if enabled else 'Unprotect Sample Floppy')

    def export_media(self, destination):
        """Export real controller bytes to a new image, never replace a library file."""
        destination = Path(destination)
        with self.media_lock:
            if destination.exists():
                raise FileExistsError(destination)
            spool = self.config.state_dir / 'media-export.img'
            status = self.config.state_dir / 'media-export.img.status'
            status.unlink(missing_ok=True)
            spool.unlink(missing_ok=True)
            try:
                self.request('button', port=':NATIVE_MEDIA', name='Export Sample Floppy', down=True)
            finally:
                self.request('button', port=':NATIVE_MEDIA', name='Export Sample Floppy', down=False)
            deadline = time.monotonic() + 5
            while not status.exists():
                if time.monotonic() >= deadline:
                    raise TimeoutError('No media export acknowledgement from MAME')
                time.sleep(.01)
            result = status.read_text().strip()
            if result != 'ok':
                raise RuntimeError(result)
            data = spool.read_bytes()
            if len(data) not in (737280, 1474560):
                raise ValueError('Incomplete exported floppy image')
            pending = destination.with_name(destination.name + '.' + secrets.token_hex(8) + '.pending')
            try:
                with pending.open('xb') as output:
                    output.write(data)
                    output.flush()
                    os.fsync(output.fileno())
                # Atomic, no-clobber publication on the destination filesystem.
                # If unsupported, fail with the controller/spool copy retained.
                os.link(pending, destination)
            finally:
                pending.unlink(missing_ok=True)
            try:
                self._media_control('Acknowledge Floppy Export')
            except (OSError, ValueError, RuntimeError) as error:
                raise RuntimeError(f'Image saved to {destination}, but controller acknowledgement failed: {error}') from error
            return destination

    def close(self):
        if self.connection is not None:
            try:
                self.request('quit')
            except (OSError, ValueError, RuntimeError):
                pass
            self.connection.close()
            self.connection = None
        if self.process is not None:
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=5)
            self.process = None
        if self.midi_connection is not None:
            self.midi_connection.close()
            self.midi_connection = None
        if self.log is not None:
            self.log.close()
            self.log = None
        if self.state_lock is not None:
            self.state_lock.close()
            self.state_lock = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.close()
