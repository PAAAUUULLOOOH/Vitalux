#!/usr/bin/env python3
"""One AppRun owner activates its verified request after the GUI process exits."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile


def activate(request,target,source_version):
    request,target=Path(request),Path(target)
    if request.is_symlink() or target.is_symlink():raise ValueError('Symlink activation request')
    data=json.loads(request.read_text())
    if data.get('schema')!=1 or data.get('source_version')!=source_version:
        raise ValueError('Activation belongs to another running version')
    if data.get('target')!=str(target.resolve()):raise ValueError('Activation target changed')
    if data.get('action')=='restart':
        request.unlink()
        return 20
    if data.get('action') not in (None,'update'):raise ValueError('Unknown AppImage transition')
    source=Path(data['staged'])
    info=source.lstat()
    if source.is_symlink() or not stat.S_ISREG(info.st_mode) or source.parent.resolve()!=target.parent.resolve():
        raise ValueError('Unsafe prepared AppImage')
    with source.open('rb') as stream:
        header=stream.read(11);stream.seek(0)
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if not header.startswith(b'\x7fELF') or header[8:11]!=b'AI\x02' or digest!=data.get('sha256'):
        raise ValueError('Prepared AppImage verification failed')
    descriptor,temporary=tempfile.mkstemp(prefix='.vitalux-previous-',dir=target.parent)
    os.close(descriptor)
    try:
        shutil.copy2(target,temporary)
        # Both replacements use separate inodes; a mounted AppImage is never truncated.
        os.replace(temporary,str(target)+'.previous')
        os.chmod(source,info.st_mode|stat.S_IXUSR)
        os.replace(source,target)
    finally:Path(temporary).unlink(missing_ok=True)
    request.unlink()
    return 0 if data.get('relaunch') else 10


if __name__=='__main__':
    try:status=activate(*sys.argv[1:])
    except Exception as error:
        print('Vitalux: AppImage activation failed: '+str(error),file=sys.stderr,flush=True)
        raise SystemExit(1)
    raise SystemExit(status)
