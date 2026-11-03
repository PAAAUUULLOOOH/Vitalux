"""Isolated OpenGL preflight and reusable, never-mapped rendering surfaces."""
import importlib
import math
import subprocess
import sys
import time
from pathlib import Path
from PySide6.QtCore import QEvent,QThread,QTimer,Signal,Qt,QPointF
from PySide6.QtGui import QImage,QPainter
from PySide6.QtWidgets import QApplication,QVBoxLayout,QWidget
from .widgets import label
from .i18n import tr
from . import motion

_probe_results = {}


class GraphicsProbe(QThread):
    completed=Signal(bool,str)

    def __init__(self,module,parent):
        super().__init__(parent);self.module=module

    def run(self):
        process=None
        try:
            process=subprocess.Popen([sys.executable,'-m',self.module],
                cwd=Path(__file__).resolve().parents[1],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
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


class SceneHost(QWidget):
    frame_changed=Signal()

    def __init__(self,parent=None,*,module='vitalux.sculpt_scene',view_class='SculptView',background=False):
        super().__init__(parent)
        self.module,self.view_class,self.background=module,view_class,background
        self.owner=parent if background else self
        self.setMouseTracking(True)
        self.body=QVBoxLayout(self);self.body.setContentsMargins(0,0,0,0)
        self.notice=label('3D-Ansicht wird vorbereitet …','muted',wrap=True)
        self.body.addWidget(self.notice)
        self.view=None;self.worker=None;self.requested=False
        self._tool=None;self._frame=QImage()
        self.pointer=[0.,0.];self.target_pointer=[0.,0.];self._last_frame=time.monotonic()
        self.frame_timer=QTimer(self);self.frame_timer.setInterval(16)
        self.frame_timer.timeout.connect(self._render_frame)
        if background:
            self.hide();self.owner.installEventFilter(self)
            self.owner.window().installEventFilter(self)
            QApplication.instance().installEventFilter(self)
        else:self.setMinimumSize(220,260)

    def enable(self,enabled):
        self.requested=bool(enabled)
        if not self.background:self.setVisible(enabled)
        if not enabled:
            if self.worker and self.worker.isRunning():self.worker.requestInterruption()
            self.release_view();return
        self._start()
        if self.view is not None and self._visible():self.frame_timer.start(0)

    def _visible(self):
        return self.owner.isVisible() and not self.owner.window().isMinimized()

    def _start(self):
        if not self.requested or self.view is not None:return
        if QApplication.platformName() in ('offscreen','minimal'):
            self._ready(False,'');return
        if self.module in _probe_results:self._ready(*_probe_results[self.module]);return
        if self.worker and self.worker.isRunning():return
        worker=self.worker=GraphicsProbe(self.module,self)
        worker.completed.connect(self._ready)
        worker.finished.connect(lambda:self._finished(worker))
        worker.start()

    def _finished(self,worker):
        if self.worker is worker:self.worker=None
        worker.deleteLater()
        if self.requested and self.view is None and self.module not in _probe_results:self._start()

    def _ready(self,ok,detail):
        if QApplication.platformName() not in ('offscreen','minimal'):_probe_results[self.module]=(ok,detail)
        if not self.requested:return
        if ok:
            try:
                view_type=getattr(importlib.import_module(self.module),self.view_class)
                # A parentless, never-mapped native window preserves the main
                # window's handle and backing store when a design is activated.
                self._tool=QWidget(None,Qt.Tool|Qt.FramelessWindowHint)
                self._tool.setAttribute(Qt.WA_DontShowOnScreen,True)
                self._tool.setAttribute(Qt.WA_ShowWithoutActivating,True)
                self.view=view_type(self._tool)
                layout=QVBoxLayout(self._tool);layout.setContentsMargins(0,0,0,0)
                layout.addWidget(self.view);self.notice.hide()
                self._render_frame(force=True)
                QTimer.singleShot(300,self._check_surface)
                return
            except (ImportError,RuntimeError,AttributeError) as exc:
                detail=str(exc);self.release_view()
        self.notice.setText(tr('3D-Beschleunigung ist auf diesem System nicht verfügbar.'))
        self.notice.setToolTip(detail);self.notice.setVisible(not self.background)

    def _check_surface(self):
        if self.view is not None and not self.view.ready:
            detail=self.view.error;self.release_view();self._ready(False,detail)

    def release_view(self):
        self.frame_timer.stop()
        if self.view is not None:
            view,self.view=self.view,None
            view.hide();view.cleanup()
        if self._tool is not None:
            self._tool.hide();self._tool.deleteLater();self._tool=None
        self._frame=QImage();self.pointer=[0.,0.];self.target_pointer=[0.,0.]
        self._last_frame=time.monotonic();self.update()

    def _render_frame(self,force=False):
        visible=self._visible()
        if self.view is None or not self.requested or (not visible and not force):
            self.frame_timer.stop();return
        self._tool.setScreen(self.owner.screen())
        self._tool.resize(self.owner.size());self._tool.show();self.view.timer.stop()
        now=time.monotonic();elapsed=min(.1,now-self._last_frame);self._last_frame=now
        if self.background:
            target=self.target_pointer if motion.level()=='smooth' else (0.,0.)
            blend=1.-math.exp(-elapsed/.16)
            self.pointer=[old+(new-old)*blend for old,new in zip(self.pointer,target)]
            self.view.pointer=list(self.pointer)
        self.view.phase=(now-self.view.started)*(.15 if motion.level()=='reduced' else 1.) if motion.enabled() else 0.
        image=self.view.grabFramebuffer();self.view.timer.stop()
        if not image.isNull() and self.view.ready:
            image.setDevicePixelRatio(self.owner.devicePixelRatioF())
            self._frame=image
            if self.background:self.frame_changed.emit()
            else:self.update()
        if visible and motion.enabled():self.frame_timer.start(80 if motion.level()=='reduced' else 16)
        else:
            self.frame_timer.stop()
            if not visible:self._tool.hide()

    def paintEvent(self,event):
        if not self._frame.isNull() and not self.background:
            painter=QPainter(self);painter.drawImage(QPointF(0,0),self._frame);painter.end()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.view is not None and self._visible():self.frame_timer.start(0)

    def showEvent(self,event):
        super().showEvent(event)
        if self.view is not None:self.frame_timer.start(0)

    def hideEvent(self,event):
        self.frame_timer.stop()
        if self._tool is not None:self._tool.hide()
        super().hideEvent(event)

    def eventFilter(self,watched,event):
        if not self.background or not self.requested:return False
        kind=event.type()
        if watched in (self.owner,self.owner.window()):
            if kind in (QEvent.Hide,QEvent.WindowDeactivate):
                self.frame_timer.stop()
                if self._tool is not None:self._tool.hide()
            elif kind in (QEvent.Show,QEvent.Resize,QEvent.WindowStateChange,QEvent.WindowActivate):
                if self.view is not None and self._visible():self.frame_timer.start(0)
        if kind==QEvent.MouseMove and self.view is not None and motion.level()=='smooth':
            # Observe the native window too: labels/buttons need not enable
            # QWidget mouse tracking for the background camera to respond.
            belongs=(isinstance(watched,QWidget) and watched.window() is self.owner.window()
                     or watched is self.owner.window().windowHandle())
            if belongs:
                point=self.owner.mapFromGlobal(event.globalPosition().toPoint())
                self.target_pointer=[max(-1.,min(1.,point.x()/max(1,self.owner.width())*2-1)),
                                     max(-1.,min(1.,point.y()/max(1,self.owner.height())*2-1))]
        return False

    def mouseMoveEvent(self,event):
        if self.view is not None and motion.level()=='smooth':
            self.view.pointer=[max(-1.,min(1.,event.position().x()/max(1,self.width())*2-1)),
                               max(-1.,min(1.,event.position().y()/max(1,self.height())*2-1))]
        super().mouseMoveEvent(event)

    def set_load(self,value):
        if self.view is not None:
            self.view.load=float(value or 0)
            if self._visible():self.frame_timer.start(0)

    def shutdown(self):
        self.requested=False
        if self.worker and self.worker.isRunning():self.worker.requestInterruption();return False
        self.release_view();return True
