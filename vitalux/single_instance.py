"""A per-user, process-lifetime lock shared by every Vitalux package/channel."""
import errno
import fcntl
import os
import stat
from pathlib import Path


class InstanceGuard:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else Path('/tmp') / f'vitalux-{os.getuid()}'
        self._fd = None

    def acquire(self):
        if self._fd is not None:
            return True
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = self.directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise PermissionError('Unsafe Vitalux instance-lock directory')
        fd = os.open(self.directory / 'instance.lock', os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise PermissionError('Unsafe Vitalux instance-lock file')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                return False
            self._fd, fd = fd, None
            return True
        finally:
            if fd is not None:
                os.close(fd)

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        # Never unlink: waiting starters must all lock the same inode.


def already_running():
    """Show a localized notice without initializing a profile or GPU backend."""
    from PySide6.QtWidgets import QApplication, QMessageBox
    from . import APP_NAME, i18n, settings
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    i18n.set_lang(settings.get('lang') or ('de' if os.environ.get('LANG', '').lower().startswith('de') else 'en'))
    QMessageBox.information(None, APP_NAME, i18n.tr('Vitalux läuft bereits.'))
    return 0
