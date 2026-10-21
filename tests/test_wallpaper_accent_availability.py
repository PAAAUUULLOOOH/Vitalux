"""Accent availability regression for custom images and theme switching."""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication, QWidget
from vitalux import settings, theme, wallpaper_accents
from vitalux.control import PreferencesPage

class Host(QWidget):
    _tray = True
    render_backend_active = 'software'
    def apply_appearance(self):
        theme.set_mode(settings.get('theme', 'glass'))
        theme.set_accent(wallpaper_accents.resolve_accent(settings.get('accent', '#4f8cff')))
    def set_interval(self, interval): pass

def run():
    app = QApplication.instance() or QApplication([])
    previous = settings.PATH
    with tempfile.TemporaryDirectory(prefix='vitalux-wallpaper-accent-') as tmp:
        settings.PATH = str(Path(tmp) / 'settings.json')
        try:
            settings.set_many({'theme': 'glass', 'accent': '#f472b6',
                               'background_style': 'theme_default'})
            theme.set_mode('glass')
            host = Host()
            page = PreferencesPage(host)
            page.show()
            app.processEvents()
            index = page.accent_combo.findData(wallpaper_accents.AUTO)
            item = page.accent_combo.model().item(index)
            assert index >= 0 and not item.isEnabled()
            assert page.accent_combo.isEnabled()
            page.change_accent(wallpaper_accents.AUTO)
            assert settings.get('accent') == '#f472b6'
            folder = Path(tmp) / 'backgrounds'
            folder.mkdir()
            image = QImage(24, 24, QImage.Format_RGB32)
            image.fill(QColor('#318da3'))
            assert image.save(str(folder / 'bg.png'))
            settings.set_many({'custom_background_selected': 'bg.png',
                'custom_backgrounds': [{'file': 'bg.png', 'name': 'Background'}]})
            page.refresh_background_images()
            page.background_combo.setCurrentIndex(page.background_combo.findData('custom_image'))
            app.processEvents()
            assert wallpaper_accents.available() and item.isEnabled()
            page.accent_combo.setCurrentIndex(index)
            app.processEvents()
            assert settings.get('accent') == wallpaper_accents.AUTO
            assert settings.get('accent_before_wallpaper_auto') == '#f472b6'
            page.background_combo.setCurrentIndex(page.background_combo.findData('glass'))
            app.processEvents()
            assert not item.isEnabled() and settings.get('accent') == '#f472b6'
            page.background_combo.setCurrentIndex(page.background_combo.findData('custom_image'))
            page.accent_combo.setCurrentIndex(index)
            app.processEvents()
            (folder / 'bg.png').unlink()
            page.refresh_background_images()
            assert not item.isEnabled() and settings.get('accent') == '#f472b6'
            page.select_design('black_glass_gold')
            app.processEvents()
            assert not page.accent_combo.isLocked()
            page.select_design('glass')
            app.processEvents()
            assert page.accent_combo.isEnabled()
            page.close()
            host.close()
        finally:
            settings.PATH = previous
    print('Wallpaper accent gating and manual fallback: OK')

if __name__ == '__main__': run()
