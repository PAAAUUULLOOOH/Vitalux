#!/usr/bin/env python3
"""Remove development tools from a staged package after validation finishes."""
import argparse
from pathlib import Path
import shutil


def finalize(root):
    root = root.resolve()
    if ((root / '.git').exists() or not (root / 'runtime/bin/python3.12').is_file()
            or not (root / 'vitalux/__main__.py').is_file()):
        raise ValueError('Expected a staged Vitalux runtime, not a source checkout')
    removed = []

    def remove(path):
        if not path.exists() and not path.is_symlink():
            return
        removed.append(str(path.relative_to(root)))
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()

    for relative in (
            'tests', 'requirements-dev.txt', 'packaging/build-appimage.sh',
            'packaging/runtime', 'runtime/lib/python3.12/unittest',
            'runtime/lib/python3.12/site-packages/PySide6/QtTest.abi3.so',
            'runtime/lib/python3.12/site-packages/PySide6/Qt/lib/libQt6Test.so.6'):
        remove(root / relative)
    for script in (root / 'scripts').iterdir():
        if script.name != 'ensure-runtime.sh':
            remove(script)
    for cache in root.rglob('__pycache__'):
        remove(cache)
    return removed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    for name in finalize(parser.parse_args().root):
        print('Removed development payload:', name)
