"""Real window switching: palettes, gallery, live workers and restored settings."""
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from vitalux import distro, i18n, premium, settings, theme
from vitalux.logo import load_logo
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow


def run():
    app = QApplication.instance() or QApplication([])
    previous = settings.PATH
    with tempfile.TemporaryDirectory() as directory:
        settings.PATH = str(Path(directory)/'settings.json')
        window = None
        try:
            settings.set_many({'theme': 'glass', 'accent': '#f472b6',
                               'close_to_tray': False, 'background_style': 'theme_default'})
            theme.set_mode('glass')
            info = distro.info()
            manager = UpdateManager()
            window = MainWindow(info, load_logo(info, 96), manager)
            window.resize(1380, 900)
            window.show()
            QTest.qWait(1200)
            assert window.last_sample is not None
            sampler = window.sampler
            preferences = dict(window.pages)['Einstellungen']
            settings_index = next(i for i, (name, _) in enumerate(window.pages) if name == 'Einstellungen')
            window.stack.setCurrentIndex(settings_index)
            app.processEvents()
            scroll = window.stack.currentWidget()
            scroll.verticalScrollBar().setValue(180)
            scroll_position = scroll.verticalScrollBar().value()
            preferences.select_design('dark')
            first = window._appearance_overlay
            assert first is not None and first.isVisible()
            first.animation.setCurrentTime(130)
            preferences.select_design('light')
            second = window._appearance_overlay
            assert second is not None and second is not first
            assert first.isHidden() and first.before is None
            assert window.stack.currentIndex() == settings_index
            assert scroll.verticalScrollBar().value() == scroll_position
            assert window.sampler is sampler and sampler.isRunning()
            window.resize(window.width()-10, window.height())
            app.processEvents()
            assert window._appearance_overlay is None, 'Resize retained stale snapshots'
            assert not hasattr(preferences, 'mode')
            assert len(preferences.design_tiles) == len(theme.CHOICES) == 13
            assert {tile.key for tile in preferences.design_tiles} == set(theme._THEMES)
            for tile in preferences.design_tiles:
                tile.click()
                app.processEvents()
                assert settings.get('theme') == tile.key
                assert sum(t.isChecked() for t in preferences.design_tiles) == 1
                assert not tile.grab().isNull()
            images = []
            for key in premium.KEYS:
                preferences.select_design(key)
                app.processEvents()
                assert theme.mode() == key
                assert theme.accent() == premium.COLLECTIONS[key]['accent']
                assert preferences.accent_combo.isLocked()
                assert preferences.background_combo.isLocked()
                for language in ('de', 'en'):
                    i18n.set_lang(language)
                    preferences.refresh_appearance()
                    for combo in (preferences.accent_combo, preferences.background_combo):
                        assert not combo.isEnabled()
                        combo.showPopup()
                        assert not combo.view().isVisible()
                        assert not hasattr(combo, '_locked_menu')
                assert not hasattr(preferences, 'background_lock_note')
                assert not hasattr(preferences, 'accent_lock_note')
                original_bg = settings.get('background_style')
                preferences.background_combo.setCurrentIndex(preferences.background_combo.findData('prism'))
                assert settings.get('background_style') == original_bg
                assert settings.get('accent') == '#f472b6'
                assert window.sampler is sampler and sampler.isRunning()
                assert sum(t.isChecked() for t in preferences.design_tiles) == 1
                tile = next(t for t in preferences.design_tiles if t.key == key)
                tile.click()  # Clicking the current design must keep it selected.
                assert tile.isChecked()
                images.append(window.centralWidget().sharp_backdrop().toImage())
            assert images[0] != images[1] and images[1] != images[2]
            preferences.select_design('glass')
            app.processEvents()
            assert preferences.accent_combo.isEnabled()
            assert settings.get('accent') == '#f472b6'
            assert window.sampler is sampler
            assert sum(t.isChecked() for t in preferences.design_tiles) == 1
            assert next(t for t in preferences.design_tiles if t.isChecked()).key == 'glass'
        finally:
            if window is not None:
                window.quit_from_tray()
                for _ in range(400):
                    if window.isHidden(): break
                    QTest.qWait(25)
                assert window.isHidden()
            settings.PATH = previous
    print('Three collections: live switching, distinct backdrops, gallery and preserved preferences PASS')


if __name__ == '__main__':
    run()
