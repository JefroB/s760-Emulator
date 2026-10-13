"""Attribute actual PyInstaller inputs. Evidence collection is not release permission."""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def rows(build, name, index):
    value=ast.literal_eval((build/name).read_text(encoding='utf-8'))[index]
    if not isinstance(value,list): raise ValueError('Invalid build records')
    for row in value:
        if not isinstance(row,tuple) or len(row)!=3 or not all(isinstance(x,str) for x in row):
            raise ValueError('Invalid build row')
    return value


def destination(package, name, kind):
    name=name.replace('\\','/')
    path=PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or ':' in name:
        raise ValueError('Unsafe package destination')
    target=package/path if kind=='EXECUTABLE' else package/'_internal'/path
    if not target.resolve().is_relative_to(package.resolve()):
        raise ValueError('Unsafe package destination')
    return target


def externalize_windows_runtime(package, build):
    """Remove only checked, root-level generated package copies; never source DLLs."""
    package=Path(package).resolve();build=Path(build).resolve();omitted={}
    for name,source,kind in rows(build,'COLLECT-00.toc',0):
        normal=name.replace('\\','/').lower()
        if '/' in normal or not (normal in ('ucrtbase.dll','vcruntime140.dll','vcruntime140_1.dll') or normal.startswith('api-ms-win-')):
            continue
        if kind!='BINARY': raise ValueError('Unexpected runtime input kind')
        target=destination(package,name,kind);original=Path(source)
        checksum=digest(original)
        if target.is_file():
            if digest(target)!=checksum: raise ValueError('Runtime DLL identity mismatch')
            target.unlink()
        omitted[target.relative_to(package).as_posix()]=checksum
    (package/'SYSTEM-PREREQUISITES.json').write_text(json.dumps({'schema':1,'platform':'Windows 10/11 x64 with Microsoft Visual C++ v14 x64 runtime installed','excluded_files':omitted},indent=2)+'\n',encoding='utf-8')
    return omitted


def inventory(package, build, search_paths=None):
    package,build=Path(package).resolve(),Path(build).resolve()
    prerequisites=package/'SYSTEM-PREREQUISITES.json'
    omitted=json.loads(prerequisites.read_text(encoding='utf-8'))['excluded_files'] if prerequisites.is_file() else {}
    owners={}; distributions={}
    for dist in metadata.distributions(path=search_paths or sys.path):
        name=dist.metadata.get('Name','unknown');key=re.sub(r'[^a-z0-9_.-]','-',name.lower())
        distributions[key]=dist
        for file in dist.files or []:
            owners[os.path.abspath(dist.locate_file(file)).casefold()]=key
    components={}; inputs=[]; errors=[];mapped=set()
    def component(source):
        key=owners.get(str(source.resolve()).casefold())
        low=source.name.lower()
        if source.is_relative_to(Path(__file__).resolve().parent): key='s760-project'
        if source==Path(__file__).resolve().parents[1]/'build/Release/s760_asio.dll': key='s760-project'
        if low=='base_library.zip' and source.parent==build: key='cpython-and-vendored-libraries'
        if 'webview2' in low: key='microsoft-webview2-sdk'
        elif low.startswith(('api-ms-win-','vcruntime','ucrtbase')): key='microsoft-windows-runtime'
        elif key is None and source.is_relative_to(Path(sys.base_prefix).resolve()) and 'site-packages' not in source.parts:
            key='cpython-and-vendored-libraries'
        if key is None: key='unattributed'
        if key not in components:
            dist=distributions.get(key)
            record={'version':dist.version if dist else None,'declared_license':(dist.metadata.get('License-Expression') or dist.metadata.get('License')) if dist else None,'notices':[], 'rights_status':'review_required'}
            if dist:
                for file in dist.files or []:
                    if file.name.lower().startswith(('license','copying','notice','authors')):
                        original=Path(dist.locate_file(file))
                        if original.is_file():
                            target=package/'notices/bundled'/key/(digest(original)[:12]+'-'+original.name)
                            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,target)
                            record['notices'].append(target.relative_to(package).as_posix())
            if key=='cpython-and-vendored-libraries':
                original=Path(sys.base_prefix)/'LICENSE.txt'
                if original.is_file():
                    target=package/'notices/bundled'/key/'Python-LICENSE.txt';target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,target)
                    record['notices'].append(target.relative_to(package).as_posix())
                record['version']=sys.version.split()[0]
            if key=='s760-project':record['declared_license']='BSD-3-Clause'
            components[key]=record
        return key
    for name,source,kind in rows(build,'COLLECT-00.toc',0):
        target=destination(package,name,kind);source=Path(source).resolve()
        key='s760-launcher-and-pyinstaller-bootloader' if kind=='EXECUTABLE' else component(source)
        relative=target.relative_to(package).as_posix();mapped.add(relative)
        record={'path':relative,'kind':kind,'component':key}
        if relative in omitted and key=='microsoft-windows-runtime' and not target.exists() and source.is_file() and digest(source)==omitted[relative]:
            record['disposition']='external_system_prerequisite'
            record['source_sha256']=omitted[relative]
            components[key]['rights_status']='not_distributed_prerequisite'
        elif not target.is_file() or not source.is_file(): errors.append('Missing collected file: '+relative)
        else:
            record['sha256']=digest(target)
            if record['sha256']!=digest(source):errors.append('Identity mismatch: '+relative)
        inputs.append(record)
    modules=[]
    for name,source,kind in rows(build,'PYZ-00.toc',1):
        source=Path(source).resolve()
        if kind=='PYMODULE' and source.name=='-':
            modules.append({'module':name,'kind':kind,'component':'namespace-package','source_sha256':None});continue
        if not source.is_file(): errors.append('Missing module source: '+name);continue
        modules.append({'module':name,'kind':kind,'component':component(source),'source_sha256':digest(source)})
    vendor_root=Path(__file__).resolve().parents[1]/'docs/distribution'
    if 'cffi' in components and components['cffi']['version']=='1.17.1':
        original=vendor_root/'cffi-1.17.1-libffi-notices.txt'
        target=package/'notices/bundled/cffi'/original.name
        shutil.copyfile(original,target)
        components['cffi']['notices'].append(target.relative_to(package).as_posix())
    provenance=vendor_root/'webview2-provenance.json'
    if 'microsoft-webview2-sdk' in components and provenance.is_file():
        vendor=json.loads(provenance.read_text(encoding='utf-8'))
        allowed={f['sha256'] for f in vendor['files'].values()}
        dlls=[r for r in inputs if r['component']=='microsoft-webview2-sdk']
        if all(r.get('sha256') in allowed for r in dlls):
            original=vendor_root/vendor['license'];target=package/'notices/bundled/microsoft-webview2-sdk'/original.name
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,target)
            components['microsoft-webview2-sdk'].update(version=vendor['version'],notices=[target.relative_to(package).as_posix()],rights_status='upstream_binary_identity_and_BSD_notice_verified',source=vendor['source'])
        else: errors.append('WebView2 binary differs from reviewed upstream package')
    if 'proxy_tools' in components:
        proof=json.loads((vendor_root/'proxy-tools-provenance.json').read_text(encoding='utf-8'))
        matched=[r for r in modules if r['module']=='proxy_tools' and r['source_sha256']==proof['source_sha256']]
        if matched and proof['exact_source_match']:
            target=package/'notices/bundled/proxy_tools/proxy_tools-LICENSE.txt';target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(vendor_root/'proxy_tools-LICENSE.txt',target)
            components['proxy_tools'].update(notices=[target.relative_to(package).as_posix()],declared_license='BSD-3-Clause (source/upstream; package metadata incorrectly says MIT)',rights_status='upstream_source_and_notice_verified')
        else:errors.append('proxy_tools source differs from reviewed upstream')
    if 'cpython-and-vendored-libraries' in components:
        proof=json.loads((vendor_root/'cpython-provenance.json').read_text(encoding='utf-8'))
        for r in inputs:
            if r['component']=='cpython-and-vendored-libraries' and r['path'].endswith(('.dll','.pyd')):
                if proof['files'].get(r['path'],{}).get('sha256')!=r.get('sha256'):errors.append('Python binary differs from reviewed upstream: '+r['path'])
        for name in ('OpenSSL-3.0.15-LICENSE.txt','CPython-3.13.0-expat-COPYING.txt','XZ-5.2.5-COPYING.txt','zlib-1.3.1-LICENSE.txt'):
            target=package/'notices/bundled/cpython-and-vendored-libraries'/name
            shutil.copyfile(vendor_root/name,target)
            components['cpython-and-vendored-libraries']['notices'].append(target.relative_to(package).as_posix())
    unmapped=[p.relative_to(package).as_posix() for p in sorted(package.rglob('*'))
              if p.is_file() and p.suffix.lower() in ('.exe','.dll','.pyd') and p.relative_to(package).as_posix() not in mapped]
    # MAME is reviewed separately with its full source/license inventory.
    unmapped=[p for p in unmapped if p!='mame-source/mames760.exe']
    return {'schema':1,'scope':'COLLECT file identity and PYZ input source attribution; build records are not a clean rebuild proof',
            'release_ready':False,'components':components,'collected_files':inputs,'frozen_modules':modules,
            'unmapped_binaries':unmapped,'errors':errors,
            'build_records':{n:digest(build/n) for n in ('COLLECT-00.toc','PYZ-00.toc')},
            'limits':['Nested vendor rights require separate review; parent package metadata does not grant rights to every included DLL.',
                      'Frozen module attribution uses build inputs; independent corresponding-source rebuild remains required.',
                      'React bundle and MAME source are audited separately.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True);parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--external-windows-runtime',action='store_true')
    args=parser.parse_args()
    if args.external_windows_runtime:externalize_windows_runtime(args.package,args.build)
    result=inventory(args.package,args.build)
    (args.package/'BUNDLED-INPUTS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'components':{k:{'version':v['version'],'notices':len(v['notices'])} for k,v in result['components'].items()},'collected_files':len(result['collected_files']),'frozen_modules':len(result['frozen_modules']),'unmapped_binaries':result['unmapped_binaries'],'errors':result['errors']},indent=2))
    return bool(result['errors'] or result['unmapped_binaries'])
if __name__=='__main__':raise SystemExit(main())
