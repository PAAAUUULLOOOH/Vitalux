"""Regression for reorganized native navigation, search, and diagnostics."""
import os
import sys
import tempfile
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication
from vitalux import i18n, settings, theme
from vitalux.window import MainWindow, Sampler


class DummyManager(QObject):
    changed = Signal()
    progress = Signal(object)
    restart = Signal()
    status = "idle"
    error = ""
    notes = ""
    available = False
    latest = ""
    def shutdown(self): pass
    def check(self): pass
    def install(self): pass


def main():
    app = QApplication.instance() or QApplication([])
    original = settings.PATH
    start = Sampler.start
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
                 'color':'#4f8cff'},
                QPixmap(96,96), DummyManager())
            window.show()
            app.processEvents()
            assert len(window.pages) == 12
            pref = next(page for title,page in window.pages if title == 'Einstellungen')
            diag = next(page for title,page in window.pages if title == 'Diagnostic Center')
            gpu = next(page for title,page in window.pages if title == 'Grafik')
            assert window.nav_footer.layout().indexOf(window.nav_buttons[9]) >= 0
            assert window.nav_footer.layout().indexOf(window.nav_buttons[10]) >= 0
            assert window.nav_footer.layout().indexOf(window.nav_buttons[11]) >= 0
            assert pref.section_nav.keys == [
                'appearance','hud','monitoring','energy','general','render']
            assert diag.nav.keys == [
                'quick','hardware','system','performance','history','reports']
            assert not hasattr(pref, 'render_advanced_toggle')
            assert not hasattr(gpu, 'lab_panel') or gpu.lab_panel is None
            assert diag.lab_panel is not None
            assert set(diag.texts) == {key for key,_,_ in diag.SECTIONS}
            pref.search.setText('Vulkan')
            assert pref.search_results.count() >= 1
            pref.choose_search_result(pref.search_results.item(0))
            assert pref.section_nav.current_key() == 'render'
            pref.section_nav.select('general')
            assert pref.language_combo.currentData() in ('de','en')
            assert settings.get('settings_section') == 'general'
            window._switch_page(2)
            gpu.diagnostic_shortcut.click()
            assert window.pages[window.stack.currentIndex()][0] == 'Diagnostic Center'
            assert diag.nav.current_key() == 'hardware'
            assert diag.category_tabs['hardware'].tabText(
                diag.category_tabs['hardware'].currentIndex()) == 'PCIe Guardian'
            diag.select_area('performance')
            assert diag.lab_panel is not None
            assert diag.lab_panel.focus.text()
            diag.select_area('reports')
            assert diag.report_source.count() == len(diag.SECTIONS)
            assert not diag.worker
            diag.nav.select('history')
            assert 'Ereignis-Timeline' in [
                widget.title() for widget in diag.nav.stack.currentWidget().findChildren(
                    __import__('PySide6.QtWidgets',fromlist=['QGroupBox']).QGroupBox)]
            print('Navigation categories, search, pinned footer and Insights relocation: OK')
        finally:
            Sampler.start = start
            if window:
                window._force_quit = True
                window.close()
            settings.PATH = original


if __name__ == '__main__':
    main()
