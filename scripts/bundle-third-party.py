#!/usr/bin/env python3
"""Build a separate, checksum-locked third-party source download for releases."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import urllib.request
from zipfile import ZipFile, ZIP_STORED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def materialize(entry, cache, runtime_root):
    path = cache/entry['filename']
    if not path.exists():
        temporary = path.with_suffix(path.suffix+'.part')
        if 'local_path' in entry:
            shutil.copyfile(runtime_root/entry['local_path'], temporary)
        else:
            with urllib.request.urlopen(entry['url'], timeout=90) as source, temporary.open('wb') as output:
                shutil.copyfileobj(source, output)
        temporary.replace(path)
    if digest(path) != entry['sha256']:
        raise RuntimeError('Third-party source checksum mismatch: '+entry['filename'])
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT/'build/third-party-sources')
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT/'dist')
    args = parser.parse_args()
    cache, output = args.cache.resolve(), args.output.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    records = json.loads((ROOT/'third_party/sources.lock.json').read_text())
    with ThreadPoolExecutor(max_workers=3) as pool:
        sources = list(pool.map(lambda entry: materialize(entry, cache, args.runtime_root.resolve()), records))
    from vitalux import __version__
    name = f'Vitalux-v{__version__}-ThirdPartySources'
    archive = output/(name+'.zip')
    # Inputs are already compressed; storing them avoids wasted CPU and memory.
    with ZipFile(archive, 'w', ZIP_STORED, allowZip64=True) as zipped:
        for source in sources:
            zipped.write(source, name+'/sources/'+source.name)
        for source in (ROOT/'third_party/sources.lock.json', ROOT/'THIRD-PARTY.md',
                       ROOT/'licenses/README.md'):
            zipped.write(source, name+'/'+source.name)
    with ZipFile(archive) as zipped:
        assert zipped.testzip() is None
    print(f'Verified third-party source package: {archive.name} ({archive.stat().st_size:,} bytes)', flush=True)


if __name__ == '__main__':
    main()
