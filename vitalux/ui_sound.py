"""A short original glass chime; audio work never blocks the Qt UI thread."""
import ctypes
import queue
import threading
import time
import wave
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QAbstractSlider,
                              QComboBox, QMenu, QTabBar, QWidget)
from . import settings

SOUND = Path(__file__).resolve().parents[1]/'assets/audio/glass-click.wav'


class _SampleSpec(ctypes.Structure):
    _fields_ = [('format', ctypes.c_int), ('rate', ctypes.c_uint32),
                ('channels', ctypes.c_uint8)]


class _BufferAttr(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in
                ('maxlength', 'tlength', 'prebuf', 'minreq', 'fragsize')]


def _pulse_worker(pending):
    """One reusable PulseAudio/PipeWire stream and at most one queued click."""
    stream = None
    try:
        lib = ctypes.CDLL('libpulse-simple.so.0')
        lib.pa_simple_new.restype = ctypes.c_void_p
        lib.pa_simple_new.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
            ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(_SampleSpec),
            ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
        lib.pa_simple_write.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.c_size_t, ctypes.POINTER(ctypes.c_int)]
        lib.pa_simple_drain.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
        lib.pa_simple_free.argtypes = [ctypes.c_void_p]
        with wave.open(str(SOUND)) as source:
            assert source.getsampwidth() == 2 and source.getnchannels() == 1
            spec = _SampleSpec(3, source.getframerate(), 1)  # PA_SAMPLE_S16LE
            pcm = source.readframes(source.getnframes())
        error = ctypes.c_int()
        # Start the small sound promptly instead of using a music-sized buffer.
        buffering = _BufferAttr(0xffffffff, 3840, 0, 960, 0xffffffff)
        while pending.get() is not None:
            if not settings.get('ui_sounds', True):
                continue
            if stream is None:
                stream = lib.pa_simple_new(None, b'Vitalux', 1, None,
                    b'Glass UI', ctypes.byref(spec), None, ctypes.byref(buffering), ctypes.byref(error))
                if not stream:
                    # A missing desktop audio server must not delay startup or
                    # create an endless sequence of connection attempts.
                    return
            if lib.pa_simple_write(stream, pcm, len(pcm), ctypes.byref(error)) < 0:
                return
            if lib.pa_simple_drain(stream, ctypes.byref(error)) < 0:
                return
    except (OSError, ValueError, wave.Error):
        return
    finally:
        if stream:
            lib.pa_simple_free(stream)


class GlassClickSound(QObject):
    def __init__(self, app):
        super().__init__(app)
        self._pending = queue.Queue(maxsize=1)
        self._worker = None
        self._last_click = 0.0
        self._last_start = 0.0
        self._stopped = False
        app.aboutToQuit.connect(self.stop)

    def play(self):
        now = time.monotonic()
        if self._stopped or not settings.get('ui_sounds', True) or now-self._last_click < .075:
            return
        self._last_click = now
        if self._worker is not None and not self._worker.is_alive():
            if now-self._last_start < 5:
                return
            self._worker = None
            self._pending = queue.Queue(maxsize=1)
        if self._worker is None:
            self._last_start = now
            self._worker = threading.Thread(target=_pulse_worker,
                args=(self._pending,), daemon=True, name='Vitalux UI audio')
            self._worker.start()
        if self._worker.is_alive():
            try:
                self._pending.put_nowait(True)
            except queue.Full:
                pass

    def stop(self):
        self._stopped = True
        try:
            self._pending.get_nowait()
        except queue.Empty:
            pass
        try:
            self._pending.put_nowait(None)
        except queue.Full:
            pass

    def eventFilter(self, obj, event):
        kind = event.type()
        if kind == QEvent.KeyRelease and event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            if isinstance(obj, QAbstractButton) and obj.isEnabled() and not event.isAutoRepeat():
                self.play()
        elif kind == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton and isinstance(obj, QWidget) and obj.isEnabled():
            point = event.position().toPoint()
            if not obj.rect().contains(point):
                return False
            if isinstance(obj, (QAbstractButton, QComboBox, QAbstractSlider, QTabBar)):
                self.play()
            elif isinstance(obj, QMenu):
                action = obj.actionAt(point)
                if action and action.isEnabled() and not action.isSeparator():
                    self.play()
            elif isinstance(obj.parentWidget(), QAbstractItemView):
                if obj.parentWidget().indexAt(point).isValid():
                    self.play()
        return False


def install(app):
    if not hasattr(app, '_vitalux_click_sound'):
        app._vitalux_click_sound = GlassClickSound(app)
        app.installEventFilter(app._vitalux_click_sound)
    return app._vitalux_click_sound
