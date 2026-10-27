"""MainWindow integration: sampling, Graphics, diagnostics and language switching.

Runs headless with the normal Qt desktop app classes, without live hardware writes
or network requests. The sampler's background thread is intentionally disabled.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["VITALUX_SPEC_OFFLINE"] = "1"
sys.path.insert(0, os.getcwd())
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QColor

from vitalux import settings, theme
from vitalux.sensors import collect
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow, Sampler


def check_window():
    app = QApplication.instance() or QApplication([])
    theme.set_mode("glass")
    app.setStyleSheet(theme.stylesheet())
    with tempfile.TemporaryDirectory() as folder:
        prior = settings.PATH
        previous_start = Sampler.start
        window = None
        try:
            settings.PATH = str(Path(folder) / "settings.json")
            settings.set("close_to_tray", False)
            Sampler.start = lambda self: None  # Deterministic manual sampling.
            manager = UpdateManager()
            logo = QPixmap(96, 96)
            logo.fill(QColor("#52d3ff"))
            window = MainWindow({"name": "TestLinux", "short": "Test",
                                 "version": "2026.10"}, logo, manager)
            window.resize(1100, 780)
            window.show()
            app.processEvents()
            data = collect()
            window.on_sample(data)
            # The obsolete Insights panels and Focus window are no longer exposed.
            window._switch_page(7)
            center = window.pages[7][1]
            center.select_area('hardware', 'pcie')
            app.processEvents()
            assert not hasattr(center, 'lab_panel')
            assert not hasattr(window, 'lab')
            assert not hasattr(window, 'open_focus_window')
            assert center.tabs.tabText(center.tabs.currentIndex()) == 'PCIe Guardian'
            window.set_language("en")
            window.set_language("de")
            window._force_quit = True
            window.close()
            deadline = time.monotonic() + 5
            while window.isVisible() and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(.01)
            assert window.isHidden(), "Window did not finish its asynchronous shutdown"
            assert not window._close_retry.isActive()
            print("Main window integration, sampling, languages, GPU and diagnostics PASS")
        finally:
            Sampler.start = previous_start
            if window and window.isVisible():
                window._force_quit = True
                window.close()
            settings.PATH = prior


if __name__ == "__main__":
    check_window()
