"""Verified desktop-library supplement, shared by packaging and offline startup."""
import hashlib
import json
from pathlib import Path
import tarfile


def manifest(source):
    path=Path(source)/'licenses/system-libraries/desktop-libraries.json'
    return json.loads(path.read_text())


def check(target,source):
    metadata=manifest(source)
    for entry in metadata['libraries']:
        path=Path(target)/entry.get('path','lib/'+entry['name'])
        with path.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=entry['sha256']:
                raise ValueError('Desktop library checksum mismatch: '+entry['name'])
    return metadata


def materialize(target,source):
    metadata=manifest(source)
    archive=Path(source)/'portable-runtime'/metadata['archive']
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=metadata['sha256']:
            raise ValueError('Desktop library archive checksum mismatch')
    with tarfile.open(archive) as tar:
        tar.extractall(target,filter='data')
    for entry in metadata['libraries']:
        if 'path' in entry:(Path(target)/'lib'/entry['name']).unlink(missing_ok=True)
    notice=Path(target)/'licenses/system-libraries/desktop-libraries.json'
    notice.parent.mkdir(parents=True,exist_ok=True)
    notice.write_text(json.dumps(metadata,indent=2)+'\n')
    return check(target,source)
