#!/usr/bin/env python3
"""Fail packaging if runtime cleanup, license notices or executable bits are lost."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def check(root):
    import sys
    sys.path.insert(0,str(root))
    from vitalux.game_runtime import validate
    overlay=validate(root/'mangohud-runtime')
    assert set(overlay['architectures'])=={'x86_64','i386'}
    required = ('README.md', 'USER-GUIDE.md', 'THIRD-PARTY.md', 'LICENSE-NOTICE.md',
                'packaging/logging.sh', 'vitalux/logfiles.py',
                'third_party/sources.lock.json', 'licenses/README.md', 'licenses/GPL-2.0.txt',
                'licenses/GPL-3.0.txt', 'licenses/LGPL-2.1.txt', 'licenses/LGPL-3.0.txt',
                'licenses/runtime/Python-3.12.7.txt', 'licenses/runtime/psutil-7.2.2.txt',
                'licenses/upstream/type2-runtime/LICENSE', 'licenses/upstream/pyside-setup/LICENSES/LGPL-3.0-only.txt',
                'licenses/source/fio-3.43-build-source.tar.gz')
    for name in required:
        assert (root/name).is_file(), 'Missing distribution notice: '+name
    for document in ('README.md', 'THIRD-PARTY.md', 'LICENSE-NOTICE.md', 'licenses/README.md'):
        path = root/document
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if '://' in target or target.startswith('#'):
                continue
            target = target.split('#')[0]
            assert (path.parent/target).exists(), f'Broken documentation link: {document}: {target}'
    source_records = json.loads((root/'third_party/sources.lock.json').read_text())
    for entry in source_records:
        assert re.fullmatch('[0-9a-f]{64}', entry['sha256'])
        if 'local_path' in entry:
            with (root/entry['local_path']).open('rb') as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256']
    qt = root/'runtime/lib/python3.12/site-packages/PySide6/Qt'
    for pattern in ('libQt6Lottie*', 'libQt6QmlCompiler*', 'libQt6QuickVector*', 'libQt6QuickTimeline*'):
        assert not list((qt/'lib').glob(pattern)), 'Unused runtime component: '+pattern
    assert not (qt/'plugins/imageformats/libqpdf.so').exists()
    for name in ('run.sh', 'runtime/bin/python3.12', 'bin/fio.real'):
        assert (root/name).stat().st_mode & 0o111, 'Missing executable bits: '+name
    print('Distribution: complete license/source notices, valid links, cleaned runtime and executable bits PASS', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    check(parser.parse_args().root.resolve())
