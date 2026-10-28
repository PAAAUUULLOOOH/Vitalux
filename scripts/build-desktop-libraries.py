#!/usr/bin/env python3
"""Reproduce the minimal shared-library supplement from locked Ubuntu packages."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from desktop_runtime import manifest

ROOT=Path(__file__).resolve().parents[1]


def build(output,cache):
    metadata=manifest(ROOT);cache.mkdir(parents=True,exist_ok=True)
    def download(entry):
        path=cache/entry['filename']
        if not path.exists():
            temporary=path.with_suffix('.part')
            with urllib.request.urlopen(entry['url'],timeout=60) as stream,temporary.open('wb') as dest:
                shutil.copyfileobj(stream,dest)
            temporary.replace(path)
        with path.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=entry['sha256']:
                raise ValueError('Binary package checksum mismatch: '+path.name)
        return path
    with ThreadPoolExecutor(max_workers=4) as pool:packages=list(pool.map(download,metadata['packages']))
    with tempfile.TemporaryDirectory(prefix='vitalux-desktop-build-') as folder:
        source=Path(folder)/'packages';source.mkdir()
        payload=Path(folder)/'payload';(payload/'lib').mkdir(parents=True)
        notices=payload/'licenses/system-libraries';notices.mkdir(parents=True)
        for package in packages:subprocess.run(['dpkg-deb','--extract',str(package),str(source)],check=True)
        for entry in metadata['libraries']:
            target=payload/entry.get('path','lib/'+entry['name']);target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source/entry['file'],target)
            if hashlib.sha256(target.read_bytes()).hexdigest()!=entry['sha256']:
                raise ValueError('Extracted library checksum mismatch: '+target.name)
            package=entry['package'].split(':')[0]
            shutil.copyfile(source/'usr/share/doc'/package/'copyright',notices/(package+'.copyright.txt'))
        output.parent.mkdir(parents=True,exist_ok=True)
        with tarfile.open(output,'w:xz',preset=9) as tar:
            for path in sorted(payload.rglob('*')):
                if not path.is_file():continue
                info=tarfile.TarInfo(str(path.relative_to(payload)));info.mode=0o644;info.size=path.stat().st_size
                with path.open('rb') as stream:tar.addfile(info,stream)
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    if digest!=metadata['sha256']:raise ValueError('Rebuilt archive differs from the locked payload: '+digest)
    print('Reproducible desktop libraries:',digest)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cache',type=Path,default=ROOT/'build/desktop-library-packages')
    args=parser.parse_args();build(args.output.resolve(),args.cache.resolve())
