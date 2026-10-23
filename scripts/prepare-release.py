#!/usr/bin/env python3
"""Assemble current source with the checksum-locked portable runtime."""
import argparse
from pathlib import Path
import shutil
import sys
import sysconfig
import hashlib
import tarfile


def prepare(target):
    import PySide6
    from vitalux import __version__
    if sys.version_info[:2] != (3, 12) or PySide6.__version__ != '6.12.0':
        raise RuntimeError('Use Python 3.12 and PySide6==6.12.0')
    source = Path(__file__).resolve().parents[1]
    if target.exists():
        raise FileExistsError(target)
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo')
    target.mkdir(parents=True)
    archive = source/'portable-runtime/vitalux-linux-x86_64.tar.xz'
    expected = (source/'portable-runtime/SHA256SUMS').read_text().split()[0]
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
            raise RuntimeError('Checked-in runtime SHA-256 mismatch')
    with tarfile.open(archive) as bundled:
        bundled.extractall(target, filter='data')
    shutil.copytree(source/'licenses', target/'licenses', dirs_exist_ok=True, ignore=ignore)
    for folder in ('vitalux', 'assets', 'scripts', 'tests', 'packaging', 'third_party'):
        shutil.rmtree(target/folder, ignore_errors=True)
        shutil.copytree(source/folder, target/folder, ignore=ignore)
    for name in ('run.sh', 'Portable-pruefen.sh', 'README.md', 'USER-GUIDE.md',
                 'CHANGELOG.md', 'CHANGELOG.en.md', 'Designs-testen.sh',
                 'Obsidian-Gold.sh', 'Quantum-Core.sh',
                 'DESIGN-VORSCHAU.md', 'requirements-dev.txt',
                 'LICENSE-NOTICE.md', 'THIRD-PARTY.md'):
        shutil.copy2(source/name, target/name)
    shutil.copy2(source/'bin/fio', target/'bin/fio')
    # Matching development modules allow the exact shipped interpreter to run
    # the complete regression suite; users need no system Python or pip.
    stdlib = target/'runtime/lib/python3.12'
    shutil.copytree(Path(sysconfig.get_path('stdlib'))/'unittest', stdlib/'unittest',
                    dirs_exist_ok=True, ignore=ignore)
    qt = Path(PySide6.__file__).parent
    bundled = stdlib/'site-packages/PySide6'
    shutil.copy2(qt/'QtTest.abi3.so', bundled/'QtTest.abi3.so')
    shutil.copy2(qt/'Qt/lib/libQt6Test.so.6', bundled/'Qt/lib/libQt6Test.so.6')
    for script in target.glob('*.sh'):
        script.chmod(0o755)
    for name in ('runtime/bin/python3.12', 'bin/fio', 'bin/fio.real'):
        (target/name).chmod(0o755)
    assert (target/'vitalux/__init__.py').read_text().startswith(f'__version__ = "{__version__}"')
    print(f'Assembled stable Vitalux {__version__}: {target}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    prepare(args.target.resolve())
