"""Shipped engines survive AppImage removal and install without external tools."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux import game_runtime


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


with tempfile.TemporaryDirectory(prefix='vitalux-overlay-') as folder:
    root=Path(folder);source=root/'portable app';(source/'portable-runtime').mkdir(parents=True)
    payload=root/'payload';payload.mkdir()
    for directory in ('lib64','lib32'):
        (payload/directory).mkdir()
        for name in game_runtime._LIBRARIES:(payload/directory/name).write_text(directory+' fixture')
    (payload/'run').write_text('#!/bin/sh\nexec "$@"\n');(payload/'run').chmod(0o755)
    (payload/'layers').mkdir();(payload/'layers/VitaluxMangoHud.json').write_text('{}')
    files={str(p.relative_to(payload)):dict(bytes=p.stat().st_size,sha256=digest(p))
           for p in sorted(payload.rglob('*')) if p.is_file()}
    identifier=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    metadata=dict(schema=1,version='test',architectures=['x86_64','i386'],bundle_id=identifier,files=files)
    (payload/'manifest.json').write_text(json.dumps(metadata))
    archive=source/'portable-runtime/test.tar.xz'
    with tarfile.open(archive,'w:xz') as output:
        for p in payload.rglob('*'):output.add(p,arcname=str(p.relative_to(payload)),recursive=False)
    lock=dict(metadata,archive=archive.name,sha256=digest(archive));lock.pop('files')
    (source/'portable-runtime/mangohud.json').write_text(json.dumps(lock))
    assert game_runtime.available(source)
    native=root/'owned user data'
    runtime=game_runtime.ensure(native,source)
    assert game_runtime.ensure(native,source)==runtime
    assert game_runtime.validate(runtime)['bundle_id']==identifier
    stamp=(runtime/'run').stat().st_mtime_ns
    assert game_runtime.ensure(native,source)==runtime and (runtime/'run').stat().st_mtime_ns==stamp
    # A mounted/extracted AppImage can disappear while a connected game remains usable.
    extracted=root/'AppImage mount';game_runtime.materialize(extracted,source)
    staged=root/'staged';staged.mkdir();shutil.move(str(extracted),staged/'mangohud-runtime')
    another=game_runtime.ensure(root/'flatpak own data',staged)
    shutil.rmtree(source);shutil.rmtree(staged)
    assert subprocess.run([str(another/'run'),'/bin/true'],env=dict(os.environ,PATH='/nonexistent'),timeout=5).returncode==0
    # Integrity failures must never be accepted as an executable engine.
    (runtime/'lib64'/game_runtime._LIBRARIES[0]).write_text('corrupt')
    try:game_runtime.validate(runtime)
    except ValueError:pass
    else:raise AssertionError('Accepted a corrupted game library')
print('Offline source/archive and AppImage payloads, owned Flatpak data, cache reuse, mount-independent lifetime and verified engine integrity PASS')
