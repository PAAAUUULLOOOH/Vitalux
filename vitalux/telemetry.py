"""Sensor acquisition and bounded histories, independent of window layout."""
from collections import deque
from threading import Event
import time
from PySide6.QtCore import QThread, Signal
from . import eco, sensors
from .sample_clock import sampling_gap
from .diagnostics import log_exception
from .monitoring import GpuHistory, SessionExtrema


class Sampler(QThread):
    sample = Signal(object)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.interval = eco.interval()
        self._last_error = None
        self._stopped = Event()
        self._sample_clock = None
        self._missed = False

    def start(self, *args):
        self._stopped.clear()
        super().start(*args)

    def stop(self):
        self.requestInterruption()
        self._stopped.set()

    def run(self):
        while not self.isInterruptionRequested():
            try:
                gap = sampling_gap(self._sample_clock, (time.time(), time.monotonic()), self.interval)
                if gap:
                    sensors.prime()
                data = sensors.collect()
                self._sample_clock = (time.time(), time.monotonic())
                data['timestamp'] = self._sample_clock[0]
                data['_gap_before'] = gap or self._missed
                self._missed = False
                if not self.isInterruptionRequested():
                    self.sample.emit(data)
                self._last_error = None
            except Exception as exc:
                self._missed = True
                self.failed.emit(str(exc))
                # Retain one timestamped, versioned traceback per distinct
                # failure instead of flooding logs at one-second intervals.
                error = (type(exc), str(exc))
                if error != self._last_error:
                    log_exception(type(exc), exc, exc.__traceback__)
                    self._last_error = error
            self._stopped.wait(max(1, self.interval))


class HistoryStore:
    def __init__(self):
        self.series = {key: deque(maxlen=900) for key in (
            "cpu", "ram", "gpu", "net_down", "net_up", "io_read", "io_write",
            "cpu_temp", "cpu_clock", "time")}
        self.gpu_history = GpuHistory()
        self.extrema = SessionExtrema()
        self.primary = None
        self.network_source = None

    def append(self, d, interval):
        h = self.series
        source = d['net'].get('source')
        if source != self.network_source:
            h['net_down'].clear();h['net_up'].clear()
            self.network_source = source
        stamp = d.get('timestamp', time.time())
        if d.get('_gap_before') and h['time']:
            missing = min(stamp-.001, h['time'][-1]+max(1, interval))
            for key, history in h.items():
                history.append(missing if key == 'time' else None)
        h['time'].append(stamp)
        g = d["gpus"][0] if d["gpus"] else None
        h["cpu"].append(d["cpu"]["usage"])
        h["ram"].append(d["ram"]["percent"])
        h["gpu"].append(g.get("usage") if g else None)
        h["cpu_temp"].append(d.get("cpu", {}).get("temp"))
        h['cpu_clock'].append(d['cpu'].get('freq'))
        h["net_down"].append(d["net"]["down"])
        h["net_up"].append(d["net"]["up"])
        h['io_read'].append(d['io']['read'])
        h['io_write'].append(d['io']['write'])
        self.gpu_history.update(d['gpus'],gap=bool(d.get('_gap_before')))
        primary = self.gpu_history.identity(g) if g else ''
        if primary != self.primary:
            self.primary = primary
            h['gpu'].clear()
            h['gpu'].extend((self.gpu_history.get(g) or {}).get('gpu', ()) if g else ())
