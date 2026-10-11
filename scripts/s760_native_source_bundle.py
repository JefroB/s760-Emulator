"""Create a native-source rebuild candidate, excluding local ROMs and build products.
A candidate is not qualified corresponding source until its clean rebuild passes.
"""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROOTS=('src','3rdparty','scripts','plugins','docs/legal','build/generated','build/projects/windows/mames760/vs2022')
EXCLUDED={'.exe','.dll','.pdb','.lib','.exp','.obj','.pyc','.bin','.rom','.hex',
          '.img','.iso','.chd','.hda','.dsk','.raw','.hfe','.wav','.aiff','.s760state'}

def bundle(repo, output, extracted):
    repo=Path(repo).resolve();output=Path(output).resolve();extracted=Path(extracted).resolve()
    if output.exists() or extracted.exists():raise ValueError('Use new output and extraction paths')
    native=repo/'mame-source';manifest={};omitted=[];files=set()
    for name in ROOTS:
        files.update(p for p in (native/name).rglob('*') if p.is_file())
    files.update(native/n for n in ('COPYING','makefile','README.md','uismall.bdf') if (native/n).is_file())
    output.parent.mkdir(parents=True,exist_ok=True);extracted.mkdir(parents=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
        for file in sorted(files):
            rel=file.relative_to(repo).as_posix()
            if file.is_symlink() or not file.resolve().is_relative_to(native):raise ValueError('Unsafe source path')
            if file.suffix.lower() in EXCLUDED or '__pycache__' in file.parts:
                omitted.append(rel);continue
            data=file.read_bytes()
            # Generated projects must not depend on the developer's Python install.
            if file.suffix=='.vcxproj':
                data=re.sub(rb'C:\\Users\\[^\r\n<>]*?\\python.exe',b'python',data)
            target=extracted/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
            archive.writestr(rel,data);manifest[rel]=hashlib.sha256(data).hexdigest()
        report={'schema':1,'qualified':False,'files':manifest,'omitted':omitted,'limitations':['Generated projects normalized to Python on PATH. Rebuild required; no cached objects or ROMs included.','Third-party example binaries and test audio excluded; build coverage must be checked.']}
        encoded=(json.dumps(report,indent=2)+'\n').encode();archive.writestr('SOURCE-MANIFEST.json',encoded);(extracted/'SOURCE-MANIFEST.json').write_bytes(encoded)
    with output.open('rb') as stream:
        checksum=hashlib.file_digest(stream,'sha256').hexdigest()
    return {'files':len(manifest),'omitted':len(omitted),'archive_sha256':checksum}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=ROOT);p.add_argument('--output',type=Path,required=True);p.add_argument('--extract',type=Path,required=True);a=p.parse_args();print(json.dumps(bundle(a.repo,a.output,a.extract),indent=2))
if __name__=='__main__':main()
