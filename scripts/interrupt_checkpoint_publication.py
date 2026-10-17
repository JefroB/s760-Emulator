"""Windows QA: terminate only a supplied test process tree on pending-file creation.

The writer is unmodified. Result records the observed pending archive and its
size after termination; callers must reject a missed/inapplicable interruption.
"""
import argparse
import ctypes
from ctypes import wintypes
import json
import hashlib
import os
from pathlib import Path
import struct
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--deny-replace', action='store_true', help='Hold archive read-only without delete sharing until .release exists')
    args = parser.parse_args()
    if os.name != 'nt':
        raise RuntimeError('Windows package QA only')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    if args.deny_replace:
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                      ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE
        handle = kernel.CreateFileW(str(args.archive.resolve()), 0x80000000, 1, None, 3, 0x80, None)
        if handle == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            args.result.with_suffix('.ready').write_text('Archive held without delete sharing')
            deadline = time.monotonic()+30
            while not args.result.with_suffix('.release').exists():
                if time.monotonic() >= deadline:
                    raise TimeoutError('No release marker')
                time.sleep(.01)
        finally:
            kernel.CloseHandle(handle)
        args.result.write_text(json.dumps(dict(passed=True, phase='Destination replacement denied by Windows sharing handle; handle released')))
        return

    class ProcessEntry(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG),
                    ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR*260)]

    for name in ('Process32FirstW', 'Process32NextW'):
        getattr(kernel, name).argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    parents = {}
    try:
        entry = ProcessEntry(); entry.dwSize = ctypes.sizeof(entry)
        ok = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            parents[entry.th32ProcessID] = entry.th32ParentProcessID
            ok = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    owned = {args.pid}
    while True:
        children = {pid for pid, parent in parents.items() if parent in owned}
        updated = owned | children
        if updated == owned:
            break
        owned = updated
    assert len(owned) > 1, 'Expected a test service with a native child'
    handles = {}
    try:
        for pid in owned:
            handle = kernel.OpenProcess(0x100001, False, pid)  # synchronize + terminate
            if not handle:
                raise ctypes.WinError(ctypes.get_last_error())
            handles[pid] = handle
        assert not list(args.archive.parent.glob(args.archive.name+'.*.tmp')), 'Use a fresh pending-file directory'
        args.result.with_suffix('.ready').write_text(json.dumps(sorted(owned)))
        deadline = time.monotonic()+30
        while time.monotonic() < deadline:
            pending = list(args.archive.parent.glob(args.archive.name+'.*.tmp'))
            if pending:
                observed = pending[0]
                observed_size = observed.stat().st_size
                # Open handles bind to these exact processes, avoiding PID reuse.
                for pid in [args.pid]+sorted(owned-{args.pid}):
                    if not kernel.TerminateProcess(handles[pid], 77):
                        raise ctypes.WinError(ctypes.get_last_error())
                for handle in handles.values():
                    assert kernel.WaitForSingleObject(handle, 10000) == 0
                assert observed.is_file(), 'Publication completed before interruption'
                raw = observed.read_bytes()
                complete = False
                if len(raw) >= 12 and raw[:8] == b'S760CKP2':
                    length = struct.unpack('<I', raw[8:12])[0]
                    if len(raw) >= 12+length:
                        metadata = json.loads(raw[12:12+length])
                        body = raw[12+length:]
                        complete = (len(body) == metadata['bytes'] and
                                    hashlib.sha256(body).hexdigest() == metadata['sha256'])
                assert not complete, 'Writer finished staging; not an incomplete-publication trial'
                result = dict(passed=True, service_pid=args.pid, terminated_pids=sorted(owned),
                              pending_name=observed.name, observed_bytes=observed_size,
                              retained_bytes=observed.stat().st_size,
                              incomplete_archive=True,
                              phase='Incomplete pending archive exists; replacement has not been published')
                args.result.write_text(json.dumps(result, indent=2)+'\n')
                return
            time.sleep(.001)
        raise TimeoutError('No pending archive observed')
    finally:
        for handle in handles.values():
            kernel.CloseHandle(handle)


if __name__ == '__main__':
    main()
