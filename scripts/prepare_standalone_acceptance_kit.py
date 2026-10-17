"""Assemble a private clean-machine handoff from a hash-frozen standalone package."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True,help='Fresh output folder; adjacent .zip must also be new')
    args=parser.parse_args()
    package=args.package.resolve();output=args.output.resolve();archive=output.parent/(output.name+'.zip')
    assert not output.exists() and not archive.exists(),'Existing artifacts are preserved; choose a fresh output'
    manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    expected=manifest['files']
    actual={p.relative_to(package).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
            for p in sorted(package.rglob('*')) if p.is_file()}
    assert actual==expected,'Candidate differs from the frozen manifest'
    output.mkdir(parents=True)
    shutil.copytree(package,output/'S760Studio')
    shutil.copyfile(args.manifest,output/'PACKAGE-MANIFEST.json')
    for source,name in [('scripts/start_standalone_acceptance.ps1','Start-Acceptance.ps1'),
                        ('scripts/complete_standalone_acceptance.ps1','Complete-Acceptance.ps1'),
                        ('docs/testing/standalone-clean-machine-handoff.md','README-ACCEPTANCE.md')]:
        shutil.copyfile(ROOT/source,output/name)
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as zipped:
        for path in sorted(output.rglob('*')):
            if path.is_file():zipped.write(path,output.name+'/'+path.relative_to(output).as_posix())
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest+' *'+archive.name+'\n',encoding='ascii')
    print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':digest,
                      'package_files':len(actual),'clean_machine_acceptance':'pending',
                      'distribution_qualification_claimed':bool(manifest.get('release_qualified')),
                      'product_release_accepted':False},indent=2))


if __name__=='__main__':main()
