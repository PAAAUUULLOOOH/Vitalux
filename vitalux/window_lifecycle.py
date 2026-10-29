"""Tray, update restart and orderly worker shutdown for the main window."""
import time

from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from . import APP_NAME, settings, motion, eco
from .i18n import tr
from .storage_page import DiskPage
from .system_pages import NetworkPage
from .control import PreferencesPage
from .diagnostics import log_exception
from .diagnostic_center import DiagnosticCenter


class WindowLifecycle:
    def _on_tray_activated(self, reason):
        """Plasma uses Trigger for a single left click, Context for right click."""
        if reason == QSystemTrayIcon.Trigger:
            self._tray_click_timer.start()
        elif reason == QSystemTrayIcon.DoubleClick:
            self._tray_click_timer.stop()
            self.show_from_tray()
        # Context is handled by QSystemTrayIcon's persistent QMenu itself.


    def _toggle_tray_window(self):
        if self.isVisible() and not self.isMinimized():
            self._hide_to_tray()
        else:
            self.show_from_tray()

    def _hide_to_tray(self):
        """Only hide when a real system tray is available to reopen the app."""
        if not (self._tray and self._tray.isVisible() and
                QSystemTrayIcon.isSystemTrayAvailable()):
            return False
        self._tray_was_maximized = self.isMaximized()
        self.hide()
        return True

    def show_from_tray(self):
        self._tray_click_timer.stop()
        if self._tray_was_maximized or self.isMaximized():
            self.showMaximized()
        else:
            self.showNormal()
        if eco.enabled():
            self._refresh_visible_page()  # Bring cached data up to date on restore.
        self.raise_()
        self.activateWindow()

    def restart_for_renderer(self, commit=None):
        """Defer reset commits until workers have stopped and a restart is safe."""
        if getattr(self.manager,'pending_restart',False):
            if commit is not None:return False
            self.manager._restart()
            return True
        if self.restart_requested:
            return True
        if getattr(self.manager, 'status', '') == 'installing':
            return False
        for _title, page in self.pages:
            worker = (page.benchmark.thread if isinstance(page, DiskPage) else
                      page.worker if isinstance(page, DiagnosticCenter) else None)
            if worker is not None and worker.isRunning():
                return False
        self._tray_click_timer.stop()
        self._force_quit = True
        self.restart_requested = True
        self._reset_commit = commit
        self._shutdown_not_before = time.monotonic()+motion.duration(260)/1000 if commit else 0
        if self.close() or self._close_retry.isActive():
            return True
        self.restart_requested = self._force_quit = False
        self._reset_commit = None
        return False

    def _restart_after_update(self):
        # AppImages have an external atomic activation helper. ZIP editions
        # restart through the launcher only after this process exits cleanly.
        self.restart_requested = not bool(getattr(self.manager, 'pending_path', None))
        self._force_quit = True
        self.close()

    def _cancel_shutdown(self,message):
        self._shutdown_pending = self.restart_requested = self._force_quit = False
        self.centralWidget().setEnabled(True)
        if not self.sampler.isRunning():self.sampler.start()
        for _title,page in self.pages:
            if isinstance(page,NetworkPage):page.watcher.resume_after_shutdown()
            elif hasattr(page,'service') and hasattr(page,'resume_after_shutdown'):page.resume_after_shutdown()
        self.manager.resume_after_shutdown()
        from .lifecycle import resume_product_workers
        resume_product_workers()
        for _title,page in self.pages:
            if isinstance(page,PreferencesPage):page._refresh_restore_button()
        self.statusBar().showMessage(tr(message),8000)

    def quit_from_tray(self):
        self._tray_click_timer.stop()
        self._force_quit = True
        if not self.close() and not self._close_retry.isActive():
            # An active benchmark may refuse to close until its worker stops.
            self._force_quit = False

    def _inform_missing_tray(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, APP_NAME, tr('Die KDE-Systemleiste ist momentan nicht verfügbar. Vitalux bleibt geöffnet. Um es vollständig zu beenden, deaktiviere die Tray-Funktion unter Einstellungen.'))


    def closeEvent(self, event):
        if not self._force_quit and settings.get('close_to_tray', True):
            if self._hide_to_tray():
                event.ignore()
                return
            # On systems without an available system tray, do not silently
            # terminate the process when the user expects X to hide the app.
            # Remain accessible until the user changes the setting or a host
            # is available. Never hide a window that cannot be reopened.
            event.ignore()
            if not getattr(self, '_tray_missing_notice', False):
                self._tray_missing_notice = True
                QTimer.singleShot(0, self._inform_missing_tray)
            return
        if not self._shutdown_pending:
            # Save edits before a reset transaction is committed, never after it.
            if self.pages and hasattr(self.pages[0][1], 'board') and self.pages[0][1].board.editing:
                self.pages[0][1].save_editor()
            self._shutdown_pending = True
            self.sampler.stop()
            self.manager.shutdown()
            for _title, page in self.pages:
                if hasattr(page,'service') and hasattr(page,'shutdown'):
                    page.shutdown()
                if isinstance(page,NetworkPage):
                    page.shutdown()
                if isinstance(page, DiskPage):
                    worker = page.benchmark.thread
                    if worker is not None and worker.isRunning():
                        worker.stop()
            self.centralWidget().setEnabled(False)
            self.statusBar().showMessage(tr('Vitalux wird neu gestartet …' if self.restart_requested else 'Vitalux wird beendet …'))
        workers_running = any(worker.isRunning() for worker in self.findChildren(QThread))
        network_ready=all(page.shutdown() for _title,page in self.pages if isinstance(page,NetworkPage))
        manager_ready = self.manager.shutdown() is not False
        from .lifecycle import stop_product_workers
        products_ready=stop_product_workers()
        if workers_running or not network_ready or not manager_ready or not products_ready or time.monotonic() < self._shutdown_not_before:
            event.ignore()
            self._close_retry.start(25)
            return
        self._close_retry.stop()
        if self._reset_commit is not None:
            commit, self._reset_commit = self._reset_commit, None
            try:
                committed = commit() is not False
            except Exception as exc:
                log_exception(type(exc), exc, exc.__traceback__)
                committed = False
            if not committed:
                event.ignore()
                self._cancel_shutdown('Einstellungen konnten nicht zurückgesetzt werden.')
                return
        if (getattr(self.manager,'_restart_requested',False)
                and not self.manager.prepare_exit()):
            event.ignore()
            self._cancel_shutdown('Neustart wird automatisch erneut vorbereitet …' if self.manager.restart_retrying
                                  else 'Neustart fehlgeschlagen. Bitte unter Updates erneut versuchen.')
            return
        if self.restart_requested:
            try:
                from .updater import queue_appimage_restart
                queue_appimage_restart()
                from .restart_protocol import ready
                ready()
            except (OSError,RuntimeError):
                event.ignore()
                self._cancel_shutdown('Neustart fehlgeschlagen. Bitte unter Updates erneut versuchen.')
                return
        from .lifecycle import stop_gui_activity
        stop_gui_activity(self)
        self._tray_click_timer.stop()
        self._tray_glow.stop()
        self._mini_hud.hide()
        if self._tray is not None:
            self._tray.hide()
        self.manager.shutdown()
        super().closeEvent(event)
        # quitOnLastWindowClosed(False) keeps the event loop alive when hidden
        # in the tray. An intentional close must end the process explicitly.
        if event.isAccepted():
            QTimer.singleShot(0, QApplication.instance().quit)
