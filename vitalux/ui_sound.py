"""Low-latency glass feedback, mixed on one reusable desktop audio stream."""
from array import array
import ctypes
from functools import lru_cache
from pathlib import Path
import queue
import struct
import threading
import time
import wave

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QComboBox,
                              QMenu, QTabBar, QWidget)
from . import settings

SOUND = Path(__file__).resolve().parents[1]/'assets/audio/glass-click.wav'
CHUNK_FRAMES = 480  # Ten milliseconds at 48 kHz; no queue of delayed notes.


@lru_cache(maxsize=12)
def _volume_pcm(pcm, volume):
    samples = struct.unpack('<'+'h'*(len(pcm)//2), pcm)
    return struct.pack('<'+'h'*len(samples), *(round(value*volume/100) for value in samples))


@lru_cache(maxsize=1)
def _clip():
    with wave.open(str(SOUND)) as source:
        if (source.getsampwidth(), source.getnchannels(), source.getframerate()) != (2, 1, 48000):
            raise ValueError('The UI sound must be mono PCM16 at 48 kHz')
        return source.readframes(source.getnframes())


@lru_cache(maxsize=12)
def _samples(volume):
    return array('h', _volume_pcm(_clip(), volume))


class _SampleSpec(ctypes.Structure):
    _fields_ = [('format', ctypes.c_int), ('rate', ctypes.c_uint32), ('channels', ctypes.c_uint8)]


class _BufferAttr(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in
                ('maxlength', 'tlength', 'prebuf', 'minreq', 'fragsize')]


class _PulseOutput:
    def __init__(self):
        self.lib = ctypes.CDLL('libpulse-simple.so.0')
        self.lib.pa_simple_new.restype = ctypes.c_void_p
        self.lib.pa_simple_new.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
            ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(_SampleSpec),
            ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
        self.lib.pa_simple_write.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.c_size_t, ctypes.POINTER(ctypes.c_int)]
        self.lib.pa_simple_free.argtypes = [ctypes.c_void_p]
        self.error = ctypes.c_int()
        spec = _SampleSpec(3, 48000, 1)  # PA_SAMPLE_S16LE
        # A positive prebuffer restarts playback automatically after underrun.
        # Zero requires an explicit pa_stream_trigger after every idle pause.
        buffering = _BufferAttr(0xffffffff, 1920, 480, 480, 0xffffffff)
        self.stream = self.lib.pa_simple_new(None, b'Vitalux', 1, None, b'Glass UI',
            ctypes.byref(spec), None, ctypes.byref(buffering), ctypes.byref(self.error))
        if not self.stream:
            raise OSError('Desktop audio is temporarily unavailable')

    def write(self, pcm):
        if self.lib.pa_simple_write(self.stream, pcm, len(pcm), ctypes.byref(self.error)) < 0:
            raise OSError('Desktop audio stream disconnected')

    def close(self):
        self.lib.pa_simple_free(self.stream)
        self.stream = None


def _mix_chunk(voices):
    """Overlap fast clicks immediately instead of playing them in sequence."""
    blocks, remaining = [], []
    for samples, offset in voices:
        block = samples[offset:offset+CHUNK_FRAMES]
        blocks.append(block)
        if offset+CHUNK_FRAMES < len(samples):
            remaining.append((samples, offset+CHUNK_FRAMES))
    if len(blocks) == 1:
        return blocks[0].tobytes(), remaining
    length = max(map(len, blocks))
    mixed = array('h', (max(-32767, min(32767, sum(block[i] for block in blocks if i < len(block))))
                        for i in range(length)))
    return mixed.tobytes(), remaining


def _pulse_worker(pending):
    """Only active notes consume CPU. An idle stream sleeps on the event queue."""
    output, voices, retry_after = None, [], 0.0
    try:
        while True:
            try:
                commands = [] if voices else [pending.get(timeout=2.0 if output is not None else None)]
            except queue.Empty:
                # A fresh stream follows the current output device after idle
                # (including PipeWire/Bluetooth route changes), without polling.
                output.close()
                output = None
                continue
            while len(commands) < 32:
                try:
                    commands.append(pending.get_nowait())
                except queue.Empty:
                    break
            if any(command is None for command in commands):
                return
            for command in commands:
                preferences = settings.get_many({'ui_sounds': True, 'ui_sound_volume': 70})
                if not preferences['ui_sounds']:
                    continue
                # Boolean commands are retained for the independent transport check.
                issued, volume = (time.monotonic(), preferences['ui_sound_volume']) if command is True else command
                if time.monotonic()-issued > .15:
                    continue
                volume = min(100, max(0, int(volume)))
                if volume:
                    voices.append((_samples(volume), 0))
                    voices = voices[-8:]
            if not voices:
                continue
            try:
                if output is None:
                    if time.monotonic() < retry_after:
                        voices.clear()
                        continue
                    output = _PulseOutput()
                pcm, voices = _mix_chunk(voices)
                output.write(pcm)
                # Do not drain after each note: some PipeWire streams reject
                # subsequent writes after a drain. Underruns resume on write.
            except OSError:
                if output is not None:
                    output.close()
                output, voices = None, []
                retry_after = time.monotonic()+.5
    except (OSError, ValueError, wave.Error):
        return
    finally:
        if output is not None:
            output.close()


def _inside_combo(widget):
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QComboBox):
            return True
        parent = parent.parentWidget()
    return False


class GlassClickSound(QObject):
    def __init__(self, app):
        super().__init__(app)
        self._pending = queue.Queue(maxsize=32)
        self._worker = None
        self._last_click = self._last_start = 0.0
        self._stopped = False
        app.aboutToQuit.connect(self.stop)

    def play(self):
        now = time.monotonic()
        preferences = settings.get_many({'ui_sounds': True, 'ui_sound_volume': 70})
        volume = min(100, max(0, int(preferences['ui_sound_volume'])))
        if self._stopped or not preferences['ui_sounds'] or not volume or now-self._last_click < .012:
            return
        self._last_click = now
        if self._worker is not None and not self._worker.is_alive():
            if now-self._last_start < .5:
                return
            self._worker = None
            self._pending = queue.Queue(maxsize=32)
        if self._worker is None:
            self._last_start = now
            self._worker = threading.Thread(target=_pulse_worker, args=(self._pending,),
                                            daemon=True, name='Vitalux UI audio')
            self._worker.start()
        try:
            self._pending.put_nowait((now, volume))
        except queue.Full:
            pass

    def stop(self):
        self._stopped = True
        while True:
            try:
                self._pending.get_nowait()
            except queue.Empty:
                break
        self._pending.put_nowait(None)

    def _connect_widget(self, widget):
        if widget.property('vitaluxSoundConnected'):
            return
        if isinstance(widget, QAbstractButton):
            signal = widget.pressed
        elif isinstance(widget, QComboBox):
            signal = widget.activated
        elif isinstance(widget, QMenu):
            signal = widget.triggered
        elif isinstance(widget, QTabBar):
            signal = widget.tabBarClicked
        elif isinstance(widget, QAbstractItemView) and not _inside_combo(widget):
            signal = widget.clicked
        else:
            return
        signal.connect(lambda *_args: self.play())
        widget.setProperty('vitaluxSoundConnected', True)

    def eventFilter(self, obj, event):
        kind = event.type()
        if kind in (QEvent.Polish, QEvent.Show) and isinstance(obj, QWidget):
            self._connect_widget(obj)
        elif (kind in (QEvent.MouseButtonPress, QEvent.KeyPress) and
              isinstance(obj, QComboBox) and obj.isEnabled() and not obj.view().isVisible()):
            if kind == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.play()
            elif kind == QEvent.KeyPress and (event.key() in (Qt.Key_Space, Qt.Key_F4)
                    or (event.key() == Qt.Key_Down and event.modifiers() & Qt.AltModifier)):
                self.play()
        return False


def install(app):
    if not hasattr(app, '_vitalux_click_sound'):
        guard = app._vitalux_click_sound = GlassClickSound(app)
        app.installEventFilter(guard)
        for widget in app.allWidgets():
            guard._connect_widget(widget)
    return app._vitalux_click_sound
