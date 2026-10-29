"""One-use restart handoff, independent of Qt and its native teardown status."""
import hmac
import json
import os
from pathlib import Path
import secrets
import stat
import tempfile


def _read(path):
    path=Path(path);info=path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077:
        raise RuntimeError('Unsafe restart handoff')
    if info.st_size>4096:raise RuntimeError('Restart handoff exceeds its size limit')
    return json.loads(path.read_text())


def _write(path,data):
    descriptor,temporary=tempfile.mkstemp(prefix='.restart-',dir=Path(path).parent)
    try:
        with os.fdopen(descriptor,'w') as stream:
            json.dump(data,stream);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:Path(temporary).unlink(missing_ok=True)


def initialize(path,root,launcher,version):
    _read_info=Path(path).lstat()
    if Path(path).is_symlink() or _read_info.st_uid!=os.getuid() or _read_info.st_mode&0o077:
        raise RuntimeError('Unsafe restart handoff')
    token=secrets.token_hex(24)
    _write(path,dict(schema=1,root=str(Path(root).resolve()),launcher=int(launcher),version=version,token=token,phase='running'))
    return token


def _validated(path,root,launcher,version,token):
    data=_read(path)
    if (data.get('schema')!=1 or data.get('root')!=str(Path(root).resolve()) or
            data.get('launcher')!=int(launcher) or data.get('version')!=version or
            not hmac.compare_digest(str(data.get('token','')),token)):
        raise RuntimeError('Restart handoff belongs to another launch')
    return data


def ready():
    path=os.environ.get('VITALUX_RESTART_REQUEST_FILE')
    if not path:return False
    data=_validated(path,os.environ['VITALUX_LAUNCH_ROOT'],os.environ['VITALUX_LAUNCHER_PID'],
                    os.environ['VITALUX_LAUNCH_VERSION'],os.environ['VITALUX_RESTART_TOKEN'])
    data.update(phase='restart',gui_pid=os.getpid())
    _write(path,data)
    return True


def requested(path,root,launcher,version,token):
    data=_validated(path,root,launcher,version,token)
    return data.get('phase')=='restart' and type(data.get('gui_pid')) is int and data['gui_pid']>0
