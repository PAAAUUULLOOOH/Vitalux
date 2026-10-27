#!/usr/bin/env python3
"""Lock a built portable overlay payload for ZIP, AppImage and offline source use."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.8.4'
SOURCE_URL='https://github.com/flightlessmango/MangoHud/releases/download/v0.8.4/MangoHud-v0.8.4-Source.tar.xz'
SOURCE_SHA='bbe5a2b976313c53f21dc24b98bbed03226589460a0cce20d923cb2c36c9d8b0'


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('payload',type=Path)
    args=parser.parse_args();payload=args.payload.resolve()
    shutil.copy2(ROOT/'packaging/mangohud-launch.sh',payload/'run')
    (payload/'run').chmod(0o755)
    layer=dict(file_format_version='1.0.0',layer=dict(
        name='VK_LAYER_VITALUX_MANGOHUD_overlay',type='GLOBAL',api_version='1.3.0',
        library_path='libVitaluxMangoHud.so',implementation_version='1',
        description='Vitalux bundled MangoHud '+VERSION,
        functions=dict(vkNegotiateLoaderLayerInterfaceVersion='vkNegotiateLoaderLayerInterfaceVersion')))
    (payload/'layers').mkdir(exist_ok=True)
    (payload/'layers/VitaluxMangoHud.json').write_text(json.dumps(layer,indent=2)+'\n')
    for notice in ('embedded-fonts.txt','CC0-1.0.txt','ProggyFonts-MIT.txt'):
        shutil.copy2(ROOT/'licenses/mangohud'/notice,payload/'licenses'/notice)
    files={str(p.relative_to(payload)):dict(bytes=p.stat().st_size,sha256=digest(p))
           for p in sorted(payload.rglob('*')) if p.is_file() and p.name!='manifest.json'}
    identifier=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    metadata=dict(schema=1,version=VERSION,bundle_id=identifier,architectures=['x86_64','i386'],
                  minimum_glibc='2.31',source_url=SOURCE_URL,source_sha256=SOURCE_SHA,files=files)
    (payload/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
    archive=ROOT/'portable-runtime'/('mangohud-'+VERSION+'-linux-x86.tar.xz')
    with tarfile.open(archive,'w:xz',preset=6) as stream:
        for path in sorted(payload.rglob('*')):
            if path.is_symlink():raise ValueError('No symlinks in the portable overlay payload')
            info=stream.gettarinfo(str(path),arcname=str(path.relative_to(payload)))
            info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
            info.mode=0o755 if path.is_dir() or path.name=='run' else 0o644
            if path.is_file():
                with path.open('rb') as source:stream.addfile(info,source)
            else:stream.addfile(info)
    lock={key:value for key,value in metadata.items() if key!='files'}
    lock.update(archive=archive.name,sha256=digest(archive),bytes=archive.stat().st_size)
    (ROOT/'portable-runtime/mangohud.json').write_text(json.dumps(lock,indent=2)+'\n')
    notices=ROOT/'licenses/mangohud'
    shutil.copytree(payload/'licenses',notices,dirs_exist_ok=True)
    (notices/'build-packages.txt').write_bytes((payload/'build-packages.txt').read_bytes())
    print(json.dumps(dict(version=VERSION,bundle_id=identifier,bytes=lock['bytes'],sha256=lock['sha256'])))


if __name__=='__main__':main()
