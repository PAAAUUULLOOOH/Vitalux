"""Real Qt offscreen smoke for integrated Vitalux Insights and focus window."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
try:
    from PySide6.QtTest import QTest
except ImportError:
    # Portable runtime ships the Qt desktop widgets, but not QtTest.
    QTest = None
from vitalux import theme
from vitalux.insight_engine import MonitoringLab
from vitalux.insight_ui import FocusWindow, MonitoringLabPanel
from vitalux.pages import GpuPage


def sample(gpu_usage=40, ram_usage=48):
    return {"cpu": {"model": "i5-14600KF", "usage": 55, "temp": 62},
            "ram": {"percent": ram_usage, "total": 32000000000, "used": 16000000000},
            "gpus": [{"name": "Radeon RX 9070 XT", "driver": "amdgpu", "vendor": "AMD",
                      "usage": gpu_usage, "clock": 2100, "clock_mem": 1250,
                      "temp": 51, "hotspot": 65, "voltage": 900, "power": 160,
                      "vram_total": 16000000000, "vram_used": 5000000000,
                      "pcie_current": "16.0 GT/s · x16"}],
            "disks": [{"mount": "/", "percent": 54}],
            "session_extrema": {}}


def check_lab_panel():
    app = QApplication.instance() or QApplication([])
    theme.set_mode("glass")
    app.setStyleSheet(theme.stylesheet())
    lab = MonitoringLab()
    focus_requests = []
    panel = MonitoringLabPanel(lab, lambda: focus_requests.append("open"))
    panel.resize(1000, 800)
    panel.show()
    for value in (30, 40, 60):
        data = sample(value)
        lab.ingest(data)
    panel.refresh(data)
    app.processEvents()
    assert not panel.record_group.isVisible()
    assert not hasattr(panel, "timeline")
    assert not hasattr(panel, "hardware_group")
    assert not hasattr(panel, "compare_group")
    panel.focus.click()
    assert focus_requests == ["open"]
    panel.show_advanced.click()
    app.processEvents()
    assert panel.record_group.isVisible()
    assert panel.trend_group.isVisible()
    assert panel.trend_chart.graph.mode == "percent"

    panel.session_name.setText("Cyberpunk")
    panel.begin.click()
    assert lab.started is not None
    for value in (70, 90, 99):
        data = sample(value)
        lab.ingest(data)
        panel.refresh(data)
    panel.end.click()
    assert lab.last_session and lab.last_session["samples"] == 3
    assert "Cyberpunk" in panel.session_report.text()

    focus = FocusWindow()
    focus.show()
    focus.update_sample(sample(55))
    app.processEvents()
    assert "55.0" in focus.entries[0][1].text()
    focus.entries[0][0].setCurrentIndex(focus.entries[0][0].findData("cpu_temp"))
    focus.update_sample(sample(55))
    assert "62.0" in focus.entries[0][1].text()
    from vitalux import i18n
    i18n.set_lang("en")
    panel.retranslate()
    focus.retranslate()
    assert "Focus mode" in focus.windowTitle()
    i18n.set_lang("de")
    panel.retranslate()
    focus.retranslate()
    focus.close()
    panel.close()
    app.processEvents()
    print("Native Insights without removed timeline, comparison and hardware map: PASS")


if __name__ == "__main__":
    check_lab_panel()
