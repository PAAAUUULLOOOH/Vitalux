"""Regression for reorganized native navigation, search, and diagnostics."""
import os
import sys
import tempfile
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())

from PySide6.QtGui import QPixmap
import time
from PySide6.QtWidgets import QApplication
from vitalux import settings, theme
from vitalux.window import MainWindow, Sampler


def qwait(milliseconds):
    """Pump the real Qt event loop without requiring the optional QtTest wheel."""
    deadline = time.monotonic() + milliseconds / 1000.0
    while time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(.01)



from vitalux.update_manager import UpdateManager

class DummyManager(UpdateManager):
    def check(self): pass


def main():
    app = QApplication.instance() or QApplication([])
    original = settings.PATH
    original_start = Sampler.start
    window = None
    with tempfile.TemporaryDirectory(prefix="vitalux-navigation-") as root:
        settings.PATH = str(Path(root) / "settings.json")
        try:
            settings.set_many({'theme': 'glass', 'accent': '#4f8cff',
                               'close_to_tray': False, 'render_backend': 'software'})
            theme.set_mode('glass')
            app.setStyleSheet(theme.stylesheet())
            Sampler.start = lambda self: None
            window = MainWindow(
                {'name':'TestLinux', 'short':'Test', 'version':'2026.10',
                 'color':'#4f8cff'}, QPixmap(96,96), DummyManager())
            window.resize(1280, 780)
            window.show()
            app.processEvents()
            assert len(window.pages) == 12
            pref = next(page for title,page in window.pages if title == 'Einstellungen')
            diag = next(page for title,page in window.pages if title == 'Diagnostic Center')
            gpu = next(page for title,page in window.pages if title == 'Grafik')
            assert not hasattr(window, 'nav_footer')
            assert not hasattr(window, 'nav_headers')
            assert all(window.nav_host.layout().indexOf(b) >= 0 for b in window.nav_buttons)
            assert not hasattr(pref, 'section_nav')
            assert not hasattr(diag, 'nav')
            assert pref.SEARCH_CATEGORIES['general'] == 'Allgemein'
            appearance = pref._settings_cards['appearance'][0]
            hud = pref._settings_cards['hud'][0]
            assert appearance.mapTo(pref, appearance.rect().topLeft()).y() < hud.mapTo(pref, hud.rect().topLeft()).y()
            assert not hasattr(pref, 'language_combo')
            assert not pref._settings_cards['general']
            assert pref.content.indexOf(pref.advanced) == pref.content.count()-1
            assert pref.advanced.isAncestorOf(pref._settings_cards['render'][0])
            assert pref.advanced.isAncestorOf(pref._maintenance_card)
            assert not hasattr(gpu, 'diagnostic_shortcut')
            assert not hasattr(gpu, 'lab_panel')
            assert not hasattr(diag, 'lab_panel')
            assert pref.hud_on is not None
            assert not hasattr(pref, 'hud_top')
            assert set(diag.texts) == {key for key,_,_ in diag.SECTIONS}
            assert diag.tabs.count() == len(diag.SECTIONS)
            assert diag.report_source.count() == len(diag.SECTIONS)
            window.nav_buttons[9].click()
            app.processEvents()
            assert pref.search_overlay.parentWidget() is window.stack.currentWidget().viewport()
            assert pref.search_home.isVisible()
            assert not pref.search_overlay.expanded
            pref.search_home.click()
            qwait(320)
            pref.search.setText('Vulk')
            pref.search_settings('Vulk')
            assert pref.search_overlay.expanded
            assert pref.search_results.count() >= 1
            pref.choose_search_result(pref.search_results.item(0))
            qwait(550)
            assert pref.render_combo.hasFocus()
            assert window.stack.currentWidget().verticalScrollBar().value() > 0
            qwait(320)
            assert pref.search.text() == 'Vulk'
            assert pref.search_overlay.expanded
            assert pref.advanced.expanded
            assert pref.background_performance_note.isHidden()
            diag.select_area('hardware', 'pcie')
            assert diag.tabs.tabText(diag.tabs.currentIndex()) == 'PCIe Guardian'
            assert not hasattr(diag, 'lab_panel')
            assert diag.worker is None
            print('Original sidebar, searchable settings, diagnostic tabs and GPU safe: OK')
        finally:
            Sampler.start = original_start
            if window:
                window._force_quit = True
                window.sampler.requestInterruption()
                window.close()
            settings.PATH = original


if __name__ == '__main__':
    main()
