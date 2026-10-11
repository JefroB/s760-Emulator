"""Native boundary qualification: test-owned parent crash and paced audio runs.

Requires a built MSVC Release tree and the local firmware/ROBOFULL fixtures.
No process outside this verifier's own child tree is terminated.
"""
import argparse
import ctypes
import json
import subprocess
import time
from pathlib import Path

from s760_package_audit import digest, write_json


def alive(pid):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x100000, False, pid)  # SYNCHRONIZE only
    if not handle:
        if ctypes.get_last_error() == 87:  # process no longer exists
            return False
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        result = kernel.WaitForSingleObject(handle, 0)
        if result not in (0, 258):
            raise ctypes.WinError(ctypes.get_last_error())
        return result == 258
    finally:
        kernel.CloseHandle(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    commands = []

    def run(name, command, expected=0):
        command = [str(x) for x in command]
        print(name, flush=True)
        log = work/(name+'.log')
        with log.open('wb') as output:
            result = subprocess.run(command, cwd=root, stdout=output,
                                    stderr=subprocess.STDOUT, timeout=240,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        commands.append({'name': name, 'command': command, 'exit_code': result.returncode,
                         'log_sha256': digest(log), 'output': log.read_text(errors='replace')})
        if result.returncode != expected:
            raise RuntimeError(f'{name}: exit {result.returncode}, expected {expected}; see {log}')

    adapter = root/'build/Release/s760_native_runtime_tests.exe'
    state = work/'parent-crash'
    run('parent-crash', [adapter, root, state, '--crash-probe'], 73)
    pid = int((state/'child.pid').read_text())
    deadline = time.monotonic()+10
    while alive(pid):
        if time.monotonic() > deadline:
            raise RuntimeError('Test-owned native child survived abrupt parent exit')
        time.sleep(.05)
    run('reopen-after-crash', [adapter, root, state])
    for rate in (44100, 48000, 96000):
        run(f'paced-{rate}', [root/'build/Release/s760_native_factory_tests.exe',
                             root, work/f'audio-{rate}', '--paced-var', rate, 60])
    names = ['mame-source/mames760.exe', 'scripts/s760_runtime.lua',
             'scripts/s760_runtime.py', 'core/src/s760_native_runtime.cpp',
             'core/src/s760_vst3_plugin.cpp', 'build/Release/Roland_S760.vst3',
             'build/Release/s760_native_runtime_tests.exe',
             'build/Release/s760_native_factory_tests.exe',
             'roms/BOOT/Roland_S-760_v1.11.BIN', 'roms/System/S760224.IMG',
             'roms/FDD/ROBOFULL.IMG']
    write_json(work/'result.json', {'parent_crash_child_cleanup': True,
                                  'same_directory_reopen_after_crash': True,
                                  'commands': commands,
                                  'sha256': {name: digest(root/name) for name in names},
                                  'scope': 'Repository module harness, not actual DAW or physical device qualification'})


if __name__ == '__main__':
    main()
