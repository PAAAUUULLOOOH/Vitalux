"""Shared archive extraction preserves launchers and rejects escaping members."""
from pathlib import Path
import stat
import sys
import tempfile
from zipfile import ZipFile, ZipInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from distribution_tools import extract_release_zip


with tempfile.TemporaryDirectory(prefix='vitalux-distribution-') as folder:
    root = Path(folder)
    archive = root / 'package.zip'
    launcher = ZipInfo('Vitalux/run.sh')
    launcher.create_system = 3
    launcher.external_attr = (stat.S_IFREG | 0o755) << 16
    with ZipFile(archive, 'w') as zipped:
        zipped.writestr(launcher, '#!/bin/sh\nexit 0\n')
    target = root / 'normal'
    extract_release_zip(archive, target)
    assert (target / 'Vitalux/run.sh').read_text().endswith('exit 0\n')
    assert (target / 'Vitalux/run.sh').stat().st_mode & 0o111

    for name, symlink in (('../escaped.txt', False), ('/absolute.txt', False),
                          ('Vitalux/link', True)):
        item = ZipInfo(name)
        item.create_system = 3
        item.external_attr = ((stat.S_IFLNK if symlink else stat.S_IFREG) | 0o644) << 16
        with ZipFile(archive, 'w') as zipped:
            zipped.writestr(item, 'outside')
        try:
            extract_release_zip(archive, root / 'rejected')
        except RuntimeError:
            pass
        else:
            raise AssertionError('Unsafe release member accepted: ' + name)
    assert not (root / 'escaped.txt').exists()

print('Release extraction: executable launcher retained; path traversal, absolute paths and symlinks rejected PASS')
