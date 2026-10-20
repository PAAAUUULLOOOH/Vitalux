import os

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from . import updater, profiles
from .i18n import tr


class _CheckThread(QThread):
    done = Signal(object)

    def __init__(self, parent, channel):
        super().__init__(parent)
        self.channel=channel

    def run(self):
        try:
            self.done.emit(updater.check(self.channel))
        except Exception as exc:
            self.done.emit({"ok": False, "error": str(exc)})


class _InstallThread(QThread):
    progress = Signal(float)
    done = Signal(str)          # leer = Erfolg, sonst Fehlertext

    def __init__(self, url, sha256, parent):
        super().__init__(parent)
        self.url, self.sha256 = url, sha256
        self.pending_path = None
        self.channel=parent.channel

    def run(self):
        try:
            if self.channel!=profiles.installed():
                profiles.backup('stable');profiles.backup('unstable')
            self.pending_path = updater.install(self.url, sha256=self.sha256, progress=self.progress.emit)
            profiles.select(self.channel)
            self.done.emit("")
        except Exception as exc:
            self.done.emit(f"{tr('Installation fehlgeschlagen:')} {exc}")


class _RestoreThread(QThread):
    done = Signal(str)

    def run(self):
        try:
            updater.restore_previous()
            self.done.emit('')
        except Exception as exc:
            self.done.emit(str(exc))


class UpdateManager(QObject):
    """Hält den Update-Status. Bleibt bestehen, auch wenn die Oberfläche (z. B. bei Sprachwechsel) neu aufgebaut wird."""
    changed = Signal()
    progress = Signal(float)
    restart = Signal()

    def __init__(self):
        super().__init__()
        self.status = 'preview' if os.environ.get('VITALUX_LOCAL_PREVIEW') == '1' else 'idle'
        self.latest = self.notes = self.url = self.error = self.sha256 = ""
        self.pending_path = None
        self.channel=profiles.selected()
        self._shutting_down = False
        self._thread = None
        self._active_threads = []  # Do not destroy Qt threads while queued signals are still finishing.
        self._timer = QTimer(self)
        self._timer.setInterval(6 * 3600 * 1000)       # alle 6 Stunden prüfen
        self._timer.timeout.connect(self.check)
        if self.status != 'preview':
            self._timer.start()

    @property
    def available(self):
        return self.status == "available"

    def set_channel(self,channel):
        if channel not in ('stable','unstable') or channel==self.channel:return
        if self.status in ('checking','installing','installed'):return
        try:profiles.select(channel)
        except OSError as exc:
            self.status='error';self.error=str(exc);self.changed.emit();return
        self.channel=channel
        self.latest=self.notes=self.url=self.error=self.sha256=''
        self.status='preview' if os.environ.get('VITALUX_LOCAL_PREVIEW')=='1' else 'idle'
        self.changed.emit()
        self.check()

    def _start_worker(self, worker):
        self._thread = worker
        self._active_threads.append(worker)
        worker.finished.connect(lambda w=worker: self._active_threads.remove(w)
                                if w in self._active_threads else None)
        worker.start()

    def check(self):
        if self._shutting_down or os.environ.get('VITALUX_LOCAL_PREVIEW') == '1':
            return
        if self.status in ("checking", "installing"):
            return
        self.status = "checking"
        self.error = ""
        self.changed.emit()
        thread = _CheckThread(self,self.channel)
        thread.done.connect(self._on_checked)
        self._start_worker(thread)

    def _on_checked(self, res):
        if res.get("ok"):
            self.latest, self.notes, self.url, self.sha256 = res["latest"], res["notes"], res["url"], res["sha256"]
            self.status = "available" if res["newer"] else "uptodate"
        else:
            self.latest = self.notes = self.url = self.sha256 = ""
            self.status, self.error = "error", res.get("error", "Updateprüfung fehlgeschlagen")
        self.changed.emit()

    def install(self):
        if self._shutting_down or os.environ.get('VITALUX_LOCAL_PREVIEW') == '1':
            return
        if self.status != "available" or not self.url:
            return
        self.status = "installing"
        self.changed.emit()
        thread = _InstallThread(self.url, self.sha256, self)
        thread.progress.connect(self.progress)
        thread.done.connect(self._on_installed)
        self._start_worker(thread)

    def _on_installed(self, err):
        if err:
            self.status, self.error = "error", err
            self.changed.emit()
            return
        self.pending_path = getattr(self._thread, 'pending_path', None)
        self.status = "installed"
        self.changed.emit()
        if not self._shutting_down:
            QTimer.singleShot(900, self._restart)

    def rollback(self):
        if updater.appimage_path() or self.status in ('checking', 'installing') or not updater.backup_available():
            return
        self.status = 'installing'
        self.changed.emit()
        thread = _RestoreThread(self)
        thread.done.connect(self._on_installed)
        self._start_worker(thread)

    def _restart(self):
        if self._shutting_down:
            return
        if self.pending_path:
            try:
                updater.activate_appimage_update(self.pending_path)
            except Exception as exc:
                self.status, self.error = 'error', str(exc)
                self.changed.emit()
                return
        self.restart.emit()

    def shutdown(self):
        """Stop scheduling work; let the GUI await workers without blocking."""
        self._shutting_down = True
        self._timer.stop()
        return not any(thread.isRunning() for thread in self._active_threads)

    def resume_after_shutdown(self):
        self._shutting_down = False
        if self.status != 'preview':
            self._timer.start()
