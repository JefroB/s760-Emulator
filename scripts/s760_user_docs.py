"""Install a self-contained, offline user documentation set in a standalone tree."""
import argparse
from pathlib import Path
import re
import shutil


def install_user_docs(repo, package):
    repo, package = Path(repo), Path(package)
    guides = repo / 'docs/emulator/guides'
    docs = package / 'docs'
    docs.mkdir(parents=True, exist_ok=True)
    for source, destination in (
        ('standalone-quick-start.md', 'quick-start.md'),
        ('standalone-controls.md', 'controls.md'),
        ('standalone-troubleshooting.md', 'troubleshooting.md'),
    ):
        shutil.copyfile(guides / source, docs / destination)
    text = (guides / 'standalone-package-readme.md').read_text(encoding='utf-8')
    def rebase(match):
        target = match[1]
        if '://' in target or target.startswith('#'):
            return match[0]
        return '](' + ('../' + target) + ')'
    text = re.sub(r'\]\(([^)]+)\)', rebase, text)
    (docs / 'user-guide.md').write_text(text.replace('# S760Studio Windows development package', '# S760Studio user guide', 1), encoding='utf-8')
    (docs / 'README.md').write_text('# S760Studio documentation\n\n'
        '- [Quick Start](quick-start.md)\n- [User guide](user-guide.md)\n'
        '- [Controls](controls.md)\n- [Troubleshooting](troubleshooting.md)\n\n'
        'Documentation only: runtime profiles, firmware staging and logs live outside this directory.\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    install_user_docs(args.repo, args.package)
