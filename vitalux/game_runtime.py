"""Owned, portable MangoHud engine; no system package or Flatpak extension."""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
from threading import Lock

ROOT=Path(__file__).resolve().parents[1]
_INSTALL_LOCK=Lock()
_LIBRARIES=('libVitaluxMangoHud.so','libVitaluxMangoHud_opengl.so','libVitaluxMangoHud_shim.so')


def _read(path):
    with Path(path).open('rb') as stream:data=stream.read(256*1024+1)
    if len(data)>256*1024:raise ValueError('Overlay runtime manifest is too large')
    value=json.loads(data)
    if not isinstance(value,dict):raise ValueError('Invalid overlay runtime manifest')
    return value


def _digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


@lru_cache(maxsize=4)
def _descriptor(manifest, signature):
    data=_read(manifest)
    if data.get('schema')!=1 or not isinstance(data.get('bundle_id'),str):
        raise ValueError('Unsupported overlay runtime manifest')
    if set(data.get('architectures',[]))!={'x86_64','i386'}:
        raise ValueError('The overlay runtime must contain both game architectures')
    return data


def descriptor(root=None):
    root=Path(root) if root is not None else ROOT
    manifest=root/'mangohud-runtime/manifest.json'
    if not manifest.is_file():manifest=root/'portable-runtime/mangohud.json'
    info=manifest.stat()
    return _descriptor(str(manifest),(info.st_ino,info.st_mtime_ns,info.st_size))


def available(root=None):
    try:
        root=Path(root) if root is not None else ROOT
        info=descriptor(root)
        source=root/'mangohud-runtime'
        if source.is_dir():
            return (source/'run').is_file() and all((source/arch/name).is_file()
                   for arch in ('lib64','lib32') for name in _LIBRARIES)
        archive=info.get('archive','')
        return bool(archive and Path(archive).name==archive and (root/'portable-runtime'/archive).is_file())
    except (OSError,ValueError,KeyError,TypeError):return False


def validate(folder):
    """Verify each payload file before installing executable game libraries."""
    folder=Path(folder)
    info=_read(folder/'manifest.json')
    files=info.get('files')
    if not isinstance(files,dict) or not files or len(files)>512:
        raise ValueError('Invalid overlay payload inventory')
    for name,entry in files.items():
        relative=PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or not isinstance(entry,dict):
            raise ValueError('Invalid overlay payload path')
        path=folder/relative
        if path.is_symlink() or path.stat().st_size!=entry.get('bytes') or _digest(path)!=entry.get('sha256'):
            raise ValueError('Overlay runtime checksum mismatch: '+name)
    for directory in ('lib64','lib32'):
        for name in _LIBRARIES:
            key=directory+'/'+name
            if key not in files:raise ValueError('Missing game architecture: '+key)
    if 'run' not in files or 'layers/VitaluxMangoHud.json' not in files:
        raise ValueError('Overlay launch integration is missing')
    inventory=json.dumps(files,sort_keys=True,separators=(',',':')).encode()
    if hashlib.sha256(inventory).hexdigest()!=info.get('bundle_id'):
        raise ValueError('Overlay payload identity mismatch')
    return info


def materialize(destination, source_root=None):
    """Extract/copy the shipped engine, preserving no dependency on an AppImage mount."""
    source_root=Path(source_root) if source_root is not None else ROOT
    destination=Path(destination)
    info=descriptor(source_root)
    source=source_root/'mangohud-runtime'
    if source.is_dir():
        shutil.copytree(source,destination)
    else:
        archive=source_root/'portable-runtime'/info['archive']
        if Path(info['archive']).name!=info['archive'] or _digest(archive)!=info.get('sha256'):
            raise ValueError('Bundled overlay archive checksum mismatch')
        destination.mkdir(parents=True)
        with tarfile.open(archive) as stream:
            members=stream.getmembers()
            if len(members)>768 or sum(m.size for m in members)>128*1024*1024:
                raise ValueError('Overlay runtime exceeds its size limit')
            for member in members:
                name=PurePosixPath(member.name)
                if name.is_absolute() or '..' in name.parts or member.issym() or member.islnk():
                    raise ValueError('Invalid overlay archive entry')
            stream.extractall(destination,filter='data')
    result=validate(destination)
    if result['bundle_id']!=info['bundle_id']:raise ValueError('Overlay archive identity mismatch')
    (destination/'run').chmod(0o755)
    return result


def ensure(parent, source_root=None):
    """Install once into native or launcher-owned Flatpak data, never /usr."""
    source_root=Path(source_root) if source_root is not None else ROOT
    parent=Path(parent)
    info=descriptor(source_root)
    target=parent/(info['version']+'-'+info['bundle_id'][:16])
    with _INSTALL_LOCK:
        marker=target/'.complete'
        try:
            if (not target.is_symlink() and marker.read_text().strip()==info['bundle_id']
                    and (target/'run').is_file()
                    and all((target/arch/name).is_file() for arch in ('lib64','lib32') for name in _LIBRARIES)):
                return target
        except OSError:pass
        parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        temporary=Path(tempfile.mkdtemp(prefix='.overlay-install-',dir=parent))
        payload=temporary/'payload'
        try:
            materialize(payload,source_root)
            (payload/'.complete').write_text(info['bundle_id']+'\n')
            # Keep a damaged previous copy in place: an already running game
            # can still hold its mappings. Install the replacement separately.
            if target.exists() or target.is_symlink():target=parent/(target.name+'-'+temporary.name[-8:])
            os.replace(payload,target)
        finally:shutil.rmtree(temporary,ignore_errors=True)
    return target
