"""Driver-isolated preflight and lifetime management for the private 3D surface."""
import subprocess
import sys
import time
from PySide6.QtCore import QThread, QTimer, Signal, Qt, QPointF
from PySide6.QtGui import QImage,QPainter
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from .widgets import label
from .i18n import tr
from . import motion

_probe_result = None


class GraphicsProbe(QThread):
    completed=Signal(bool,str)
    def run(self):
        process=None
        try:
            process=subprocess.Popen([sys.executable,'-m','vitalux.sculpt_scene'],
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            deadline=time.monotonic()+12
            while process.poll() is None:
                if self.isInterruptionRequested() or time.monotonic()>deadline:
                    process.terminate()
                    try:process.wait(timeout=2)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
                    break
                self.msleep(25)
            output=process.communicate()[0].decode('utf-8','replace')[-1500:]
            if not self.isInterruptionRequested():self.completed.emit(process.returncode==0,output)
        except OSError as exc:
            if not self.isInterruptionRequested():self.completed.emit(False,str(exc))
        finally:
            if process is not None and process.poll() is None:process.kill();process.wait()


class SculptHost(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setMinimumSize(220,260)
        self.setMouseTracking(True)
        self.body=QVBoxLayout(self);self.body.setContentsMargins(0,0,0,0)
        self.notice=label('3D-Ansicht wird vorbereitet …','muted',wrap=True)
        self.body.addWidget(self.notice)
        self.view=None;self.worker=None;self.requested=False
        self._tool=None;self._frame=QImage()
        self.frame_timer=QTimer(self);self.frame_timer.setInterval(16)
        self.frame_timer.timeout.connect(self._render_frame)

    def enable(self,enabled):
        self.requested=bool(enabled);self.setVisible(enabled)
        if not enabled:
            if self.worker and self.worker.isRunning():self.worker.requestInterruption()
            self.release_view();return
        self._start()

    def _start(self):
        global _probe_result
        if not self.requested or self.view is not None:return
        if QApplication.platformName() in ('offscreen','minimal'):
            self._ready(False,'');return
        if _probe_result is not None:self._ready(*_probe_result);return
        if self.worker and self.worker.isRunning():return
        self.worker=GraphicsProbe(self)
        self.worker.completed.connect(self._ready)
        self.worker.finished.connect(self._restart_if_needed)
        self.worker.start()

    def _restart_if_needed(self):
        if self.requested and self.view is None and _probe_result is None:self._start()

    def _ready(self,ok,detail):
        global _probe_result
        if QApplication.platformName() not in ('offscreen','minimal'):_probe_result=(ok,detail)
        if not self.requested:return
        if ok:
            try:
                from .sculpt_scene import SculptView
                # A separate never-mapped surface leaves the app's native
                # window/backing store intact when 3D is first activated.
                # No QWidget parent: a native child can force its ancestors to
                # acquire/recreate native handles even with a Tool window flag.
                # release_view owns this surface's explicit teardown.
                self._tool=QWidget(None,Qt.Tool|Qt.FramelessWindowHint)
                self._tool.setAttribute(Qt.WA_DontShowOnScreen,True)
                self._tool.setAttribute(Qt.WA_ShowWithoutActivating,True)
                self.view=SculptView(self._tool)
                layout=QVBoxLayout(self._tool);layout.setContentsMargins(0,0,0,0)
                layout.addWidget(self.view)
                self.notice.hide()
                self._render_frame(force=True)
                QTimer.singleShot(300,self._check_surface)
                return
            except (ImportError,RuntimeError) as exc:detail=str(exc)
        self.notice.setText(tr('3D-Beschleunigung ist auf diesem System nicht verfügbar.'))
        self.notice.setToolTip(detail);self.notice.show()

    def _check_surface(self):
        if self.view is not None and self.view.isVisible() and not self.view.ready:
            detail=self.view.error;self.release_view();self._ready(False,detail)

    def release_view(self):
        self.frame_timer.stop()
        if self.view is not None:
            view,self.view=self.view,None
            view.hide();view.cleanup()
        if self._tool is not None:
            self._tool.hide();self._tool.deleteLater();self._tool=None
        self._frame=QImage();self.update()

    def _render_frame(self,force=False):
        visible=self.isVisible() and not self.window().isMinimized()
        if self.view is None or not self.requested or (not visible and not force):
            self.frame_timer.stop();return
        self._tool.setScreen(self.screen())
        self._tool.resize(self.size());self._tool.show()
        self.view.timer.stop()
        self.view.phase=(time.monotonic()-self.view.started)*(.15 if motion.level()=='reduced' else 1.) if motion.enabled() else 0.
        image=self.view.grabFramebuffer()
        self.view.timer.stop()
        if not image.isNull() and self.view.ready:
            image.setDevicePixelRatio(self.devicePixelRatioF())
            self._frame=image;self.update()
        if visible and motion.enabled():self.frame_timer.start(80 if motion.level()=='reduced' else 16)
        else:
            self.frame_timer.stop()
            if not visible:self._tool.hide()

    def paintEvent(self,event):
        if not self._frame.isNull():
            painter=QPainter(self);painter.drawImage(QPointF(0,0),self._frame);painter.end()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.view is not None and self.isVisible():self.frame_timer.start(0)

    def showEvent(self,event):
        super().showEvent(event)
        if self.view is not None:self.frame_timer.start(0)

    def hideEvent(self,event):
        self.frame_timer.stop()
        if self._tool is not None:self._tool.hide()
        super().hideEvent(event)

    def mouseMoveEvent(self,event):
        if self.view is not None and motion.level()=='smooth':
            self.view.pointer=[max(-1.,min(1.,event.position().x()/max(1,self.width())*2-1)),
                               max(-1.,min(1.,event.position().y()/max(1,self.height())*2-1))]
        super().mouseMoveEvent(event)

    def set_load(self,value):
        if self.view is not None:
            self.view.load=float(value or 0)
            if self.isVisible() and not self.window().isMinimized():self.frame_timer.start(0)

    def shutdown(self):
        self.requested=False
        if self.worker and self.worker.isRunning():self.worker.requestInterruption();return False
        self.release_view();return True
