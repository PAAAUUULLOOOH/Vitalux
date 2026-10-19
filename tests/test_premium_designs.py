"""Real window switching: palettes, gallery, live workers and restored settings."""
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from vitalux import distro, premium, settings, theme
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
            assert not hasattr(preferences, 'mode')
            assert len(preferences.design_tiles) == len(theme.CHOICES) == 10
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
                assert not preferences.accent_combo.isEnabled()
                assert not preferences.background_combo.isEnabled()
                assert not preferences.background_lock_note.isHidden()
                assert not preferences.accent_lock_note.isHidden()
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
            settings.PATH = previous
    print('Three collections: live switching, distinct backdrops, gallery and preserved preferences PASS')


if __name__ == '__main__':
    run()
