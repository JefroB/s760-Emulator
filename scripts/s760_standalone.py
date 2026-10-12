"""Launch built React assets and a native MAME runtime on loopback only.

Usage: python scripts/s760_standalone.py
Dependencies: websockets>=14,<17. Build google-ui first (npm run build).
"""
import argparse
from contextlib import closing
from dataclasses import replace
import hashlib
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import subprocess
import queue
import threading
import time
from urllib.parse import parse_qs, urlsplit
import webbrowser

from websockets.sync.server import serve
from websockets.exceptions import ConnectionClosed
from s760_runtime import NativeRuntime, RuntimeConfig, application_root, midi_inputs

from s760_readiness import FirmwareReadiness, SYSTEM_SHA256

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
        if p.get('id') not in ('ALPHA', 'VOLUME') or type(p.get('delta')) is not int or abs(p['delta']) > 32:
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
    elif kind == 'CONFIGURE_RUNTIME':
        if set(p) != {'bootRom','systemDisk','mediaDirectory','sound','discard'} or p.get('discard') is not True:
            raise ValueError('Confirm replacement of the current sampler before applying settings')
        for key in ('bootRom','systemDisk','mediaDirectory'):
            if not isinstance(p[key],str) or not p[key].strip() or len(p[key])>2048 or '\0' in p[key]:
                raise ValueError(f'Invalid path: {key}')
        if type(p['sound']) is not bool: raise ValueError('Sound must be a boolean')
    elif kind in ('RESTART_RUNTIME', 'RESTORE_SESSION'):
        if set(p) != {'discard'} or p['discard'] is not True:
            raise ValueError('Restart requires explicit discard confirmation')
    elif kind in ('EXPORT_DISK', 'SAVE_SESSION'):
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
        self.readiness = None
        self.firmware_status = {'type':'FIRMWARE_STATUS','state':'booting','message':'Connected; checking firmware…'}
        self.midi_warning = None
        try:
            self.midi_devices = midi_inputs(runtime.config.executable)
        except (OSError, subprocess.SubprocessError) as error:
            self.midi_devices = []
            self.midi_warning = f'MIDI input discovery failed; on-screen audition is available. {error}'

    def configuration(self):
        cfg = self.runtime.config
        return {'bootRom':str(cfg.boot_rom),'systemDisk':str(cfg.system_disk),
                'mediaDirectory':str(self.media_dir),'sound':cfg.sound}

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
                            sample_disk=slot if slot.exists() else disk)
        candidate.validate()
        if r.process is not None and r.process.poll() is None:
            status = r.media_status()
            if status['dirty'] or status['busy']:
                raise RuntimeError('Export disk writes and wait for disk activity before applying settings')
        r.close()
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

    def input(self, message):
        with self.runtime_lock:
            return self._input(message)

    def _input(self, message):
        kind, p = validate_input(message)
        r = self.runtime
        if kind == 'CONFIGURE_RUNTIME': return self.configure(p)
        if self.startup_error:
            raise RuntimeError('Open Runtime settings, correct the paths, and apply to start the sampler')
        if kind == 'SAVE_SESSION':
            running = r.request('status')[0]['state'] == 'running'
            r.request('pause')
            try:
                self.session_path.parent.mkdir(parents=True, exist_ok=True)
                r.save_checkpoint(self.session_path)
            finally:
                if running: r.request('resume')
            return {'type':'SESSION_SAVED', 'path':str(self.session_path.resolve())}
        if kind == 'RESTORE_SESSION':
            # Validate before pausing/closing any live machine. The native load
            # validates again before mutation; no client-supplied path is used.
            r.validate_checkpoint(self.session_path)
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
                r.start()
            r.request('pause')
            # If native application fails, leave execution paused for diagnosis.
            r.load_checkpoint(self.session_path)
            self.readiness = None
            if running: r.request('resume')
            self.firmware_status = {'type':'FIRMWARE_STATUS','state':'booting','message':'Session restored; checking firmware…'}
            return {'type':'SESSION_RESTORED','path':str(self.session_path.resolve())}
        if kind == 'RESTART_RUNTIME':
            if r.process is not None and r.process.poll() is None:
                status = r.media_status()
                if status['dirty'] or status['busy']:
                    raise RuntimeError('Export disk writes and wait for the disk operation before restarting')
            r.close()
            self.readiness = None
            self.firmware_status = {'type':'FIRMWARE_STATUS','state':'booting','message':'Restarting firmware…'}
            try:
                r.start()
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
        elif kind == 'MOUNT_DISK':
            source = self.media.get(p['diskPath'])
            if source is None:
                raise ValueError('Disk is not in the configured media library')
            r.insert_media(source)
            return {'type': 'MEDIA_INSERTED', 'name': source.name}
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
                                        'midiDevices': self.midi_devices, 'warning': self.midi_warning,
                                        'configuration':self.configuration(), 'needsConfiguration':bool(self.startup_error),
                                        'savedSession': self.session_path.is_file(),
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
                    self.runtime.request('midi', bytes=[0xb0, 123, 0])
                    for port, name in BUTTONS.values():
                        self.runtime.request('button', port=port, name=name, down=False)
                    for name in ('Mouse Left', 'Mouse Right'):
                        self.runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name=name, down=False)
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
    args.boot_rom = args.boot_rom or Path(settings.get('bootRom',ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN'))
    args.system_disk = args.system_disk or Path(settings.get('systemDisk',ROOT/'roms/System/S760224.IMG'))
    args.media_dir = args.media_dir or Path(settings.get('mediaDirectory',ROOT/'roms/FDD'))
    media_slot = args.state_dir / 'inserted-floppy.img'
    cfg = RuntimeConfig(ROOT / 'mame-source/mames760.exe', args.boot_rom, args.system_disk,
                        args.state_dir, media_slot if media_slot.exists() else args.system_disk,
                        False if args.no_sound else settings.get('sound',True), not args.fast)
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
                       (http.serve_forever, ws.serve_forever, session.stream)]
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
                session.stop.set()
                ws.shutdown()
                http.shutdown()
                threads[2].join(timeout=6)
                http.server_close()
            if session.failure:
                raise RuntimeError(session.failure)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        import sys
        if getattr(sys, 'frozen', False) and '--no-browser' not in sys.argv and '--verify-desktop' not in sys.argv:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, str(error), 'S-760 could not start', 0x10)
        raise
