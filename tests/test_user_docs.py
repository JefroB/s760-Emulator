from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from s760_user_docs import install_user_docs


def test_shipped_docs_are_complete_and_all_links_work_offline(tmp_path):
    root = Path(__file__).resolve().parents[1]
    package = tmp_path / 'package'
    package.mkdir()
    install_user_docs(root, package)
    for name in ('SYSTEM-PREREQUISITES.json', 'PACKAGE-AUDIT.json', 'BUNDLED-INPUTS.json',
                 'DEPENDENCY-INVENTORY.json', 'LICENSE.txt', 'MAME-COPYING.txt'):
        (package / name).write_text('fixture')
    assert {p.name for p in (package / 'docs').iterdir()} == {
        'README.md', 'quick-start.md', 'user-guide.md', 'controls.md', 'troubleshooting.md'}
    for document in (package / 'docs').glob('*.md'):
        text = document.read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if '://' in target or target.startswith('#'):
                continue
            destination = (document.parent / target.split('#')[0]).resolve()
            assert destination.is_relative_to(package.resolve())
            assert destination.is_file(), (document, target)
