"""Primary GPU monitoring shares the global timeline; missing data remains missing."""
import os
import sys
from collections import deque

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())

from PySide6.QtWidgets import QApplication
from vitalux import theme
from vitalux.pages import GpuCard
from vitalux.monitoring import GpuHistory


def gpu(**changes):
    data = {
        "name": "AMD Radeon RX 9070 XT", "vendor": "AMD", "driver": "amdgpu",
        "usage": 44.0, "vram_used": 5_000_000_000, "vram_total": 16_000_000_000,
        "temp": 55, "hotspot": 65, "power": 150, "fan": 32,
        "fan_rpm": 900, "clock": 2200, "clock_mem": 1300,
    }
    data.update(changes)
    return data


def check_gpu_history():
    app = QApplication.instance() or QApplication([])
    theme.set_mode("glass")
    app.setStyleSheet(theme.stylesheet())
    card = GpuCard()
    h = {"gpu": deque([12.0, 44.0], maxlen=900),
         "vram": deque([22.0, 31.25], maxlen=900)}
    card.refresh(gpu(), h)
    assert card.graph._source[0][0] is h["gpu"], "Primary GPU history must be shared"
    assert card.graph._source[1][0] is h["vram"], "VRAM history must be shared"
    assert len(card.h_use) == 0 and len(card.h_vram) == 0
    card.refresh(gpu(usage=72.0, vram_used=8_000_000_000), None)
    assert list(card.h_use) == [72.0]
    assert list(card.h_vram) == [50.0]
    card.refresh(gpu(usage=None, vram_used=None), None)
    assert list(card.h_use)[-1] is None
    assert list(card.h_vram)[-1] is None
    assert len(h["gpu"]) == 2 and len(h["vram"]) == 2
    tracker=GpuHistory(maxlen=4)
    first=gpu(id='A');second=gpu(id='B',usage=10)
    tracker.update([first,second]);tracker.update([dict(second,usage=20),dict(first,usage=60)])
    assert list(tracker.get(first)['gpu'])==[44,60],'History follows identity when GPU order changes'
    assert list(tracker.get(second)['gpu'])==[10,20]
    tracker.update([dict(first,usage=None)],gap=True)
    assert list(tracker.get(first)['gpu'])==[44,60,None,None]
    assert list(tracker.get(second)['gpu'])==[10,20,None,None]
    assert len(tracker.get(first)['gpu_temp'])==4
    tracker.update([dict(first,usage=0,vram_used=0,temp=0,clock=0)])
    assert all(values[-1]==0 for values in tracker.get(first).values()),'Real zeroes are retained'
    tracker.update([first]);assert tracker.get(second) is None,'Disconnected-device histories expire'
    assert all(len(values)==4 for values in tracker.get(first).values())
    card.close()
    app.processEvents()
    print("GPU history sharing and missing-data behavior: PASS")


if __name__ == "__main__":
    check_gpu_history()
