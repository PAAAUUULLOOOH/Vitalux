"""Regression tests for the animated settings overlay and scope-aware reset buttons."""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())

from PySide6.QtCore import Qt
import time
from PySide6.QtWidgets import QApplication, QScrollArea, QWidget
from vitalux import i18n, settings, theme
from vitalux.control import PreferencesPage


def qwait(milliseconds):
    """Pump the real Qt event loop without requiring the optional QtTest wheel."""
    deadline = time.monotonic() + milliseconds / 1000.0
    while time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(.01)



class Host(QWidget):
    _tray = object()
    render_backend_active = 'software'

    def __init__(self):
        super().__init__()
        self.hud_refreshes = 0
        self.interval = None

    def apply_appearance(self):
        theme.set_mode(settings.get('theme', 'glass'))
        theme.set_accent(settings.get('accent', '#4f8cff'))

    def set_interval(self, value):
        self.interval = value

    def set_mini_hud_enabled(self, on):
        settings.set('mini_hud_enabled', bool(on))

    def refresh_mini_hud(self):
        self.hud_refreshes += 1


def check():
    app = QApplication.instance() or QApplication([])
    previous_path, previous_language = settings.PATH, i18n.lang()
    with tempfile.TemporaryDirectory(prefix='vitalux-search-reset-') as folder:
        scroll = None
        try:
            settings.PATH = str(Path(folder) / 'settings.json')
            i18n.set_lang('de')
            theme.set_mode('glass')
            theme.set_accent('#4f8cff')
            host = Host()
            page = PreferencesPage(host)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            scroll.resize(900, 600)
            page.install_search_overlay(scroll)
            scroll.show()
            app.processEvents()
            floating = page.search_overlay
            assert floating.parentWidget() is scroll.viewport()
            assert not floating.expanded
            assert all(button.isHidden() for button in page._reset_buttons.values())
            assert page.restore_button.isHidden()

            # Resting icon belongs to page content; open overlay floats above viewport.
            assert page.search_home.isVisible()
            assert floating.isHidden()
            page.search_home.click()
            qwait(330)
            assert floating.expanded and floating.field.isVisible()
            first_width = floating.width()
            assert first_width >= 145
            floating.field.setText('vulk')
            page.search_settings('vulk')
            assert page.search_results.count() > 0
            floating.field.setText('grafikrendering backend wayland vulkan')
            app.processEvents()
            qwait(330)
            assert floating.width() > first_width
            assert abs((floating.x() + floating.width() / 2) - scroll.viewport().width() / 2) <= 2

            # The floating widget does not move with the settings content.
            y = floating.y()
            scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
            app.processEvents()
            assert floating.y() == y
            assert floating.expanded

            # Selecting a suggested setting scrolls to its actual control.
            floating.field.setText('vulk')
            page.search_settings('vulk')
            page.choose_search_result(page.search_results.item(0))
            qwait(330)
            assert not floating.expanded and not floating.field.text()
            assert page.render_combo.hasFocus()
            scroll.verticalScrollBar().setValue(0)
            app.processEvents()
            page.search_home.click()
            qwait(330)
            floating.close_search()
            qwait(330)
            assert not floating.expanded and floating.width() == 32
            assert floating.isHidden()

            # Exactly three groups have their own reset and only when changed.
            settings.set('custom_backgrounds', [{'file':'preserve.png','name':'Do not delete'}])
            settings.set('dashboard_layout', {'keep':'yes'})
            page.mode.setCurrentIndex(page.mode.findData('dark'))
            app.processEvents()
            assert page._reset_buttons['appearance'].isVisible()
            assert not page._reset_buttons['alerts'].isVisible()
            assert not page._reset_buttons['hud'].isVisible()
            page.reset_category('appearance')
            assert settings.get('theme') == 'glass'
            assert not page._reset_buttons['appearance'].isVisible()

            page.alert_boxes['cpu_temp'].setValue(97)
            app.processEvents()
            assert page._reset_buttons['alerts'].isVisible()
            page.reset_category('alerts')
            assert settings.get('cpu_temp') == 90
            assert not page._reset_buttons['alerts'].isVisible()

            page.hud_size.setCurrentIndex(page.hud_size.findData('extended'))
            app.processEvents()
            assert page._reset_buttons['hud'].isVisible()
            page.reset_category('hud')
            assert settings.get('mini_hud_layout') == 'compact'
            assert not page._reset_buttons['hud'].isVisible()
            assert not page.restore_button.isVisible()
            assert settings.get('custom_backgrounds')[0]['file'] == 'preserve.png'
            assert settings.get('dashboard_layout') == {'keep':'yes'}
            print('Pinned, animated, centered fuzzy search and targeted resets: OK')
        finally:
            if scroll is not None:
                scroll.close()
            settings.PATH = previous_path
            i18n.set_lang(previous_language)
            theme.set_mode('glass')


if __name__ == '__main__':
    check()
