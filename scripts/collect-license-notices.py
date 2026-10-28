#!/usr/bin/env python3
"""Collect verbatim upstream notices, including Qt attribution-file references."""
import argparse
import json
import posixpath
from pathlib import Path
import tarfile
from zipfile import ZipFile


def interesting(name):
    path = Path(name)
    if path.name.casefold().startswith('licensewizard') or path.name.casefold()=='license_check.py':return False
    # A name such as licensewizard.png or license_check.py is example/tool
    # code, not a notice. Referenced attribution files are added separately.
    return '/LICENSES/' in name or 'qt_attribution' in path.name or path.name.lower().startswith(
        ('license', 'licence', 'copying', 'copyright', 'notice', 'lgpl', 'gpl'))


def references(data):
    if isinstance(data, dict):
        value = data.get('LicenseFile', [])
        if isinstance(value, str):
            yield value
        elif isinstance(value, list):
            yield from (entry for entry in value if isinstance(entry, str))
        for value in data.values():
            yield from references(value)
    elif isinstance(data, list):
        for value in data:
            yield from references(value)


def collect(records, cache, output):
    for entry in records:
        archive = cache/entry['filename']
        if 'local_path' in entry:
            continue  # fio's complete source and COPYING are in the runtime.
        destination = output/entry['name']
        if archive.suffix == '.zip':
            with ZipFile(archive) as source:
                names = set(source.namelist())
                selected = {name for name in names if not name.endswith('/') and interesting(name)}
                for name in list(selected):
                    if 'qt_attribution' in name and name.endswith('.json'):
                        for relative in references(json.loads(source.read(name), strict=False)):
                            target = posixpath.normpath(posixpath.join(posixpath.dirname(name), relative))
                            if target in names:
                                selected.add(target)
                for name in sorted(selected):
                    path = destination/Path(*Path(name).parts[1:])
                    if not path.resolve().is_relative_to(destination.resolve()):
                        raise RuntimeError('Unsafe notice path')
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(source.read(name))
        else:
            with tarfile.open(archive) as source:
                for member in source.getmembers():
                    if member.isfile() and interesting(member.name):
                        path = destination/Path(*Path(member.name).parts[1:])
                        if not path.resolve().is_relative_to(destination.resolve()):
                            raise RuntimeError('Unsafe notice path')
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(source.extractfile(member).read())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('licenses/upstream'))
    args = parser.parse_args()
    collect(json.loads(Path('third_party/sources.lock.json').read_text()), args.cache, args.output)
