"""Theme regression: two glass styles, gold override, opaque Holographic."""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())
from PySide6.QtWidgets import QApplication, QWidget
from vitalux import settings, theme
from vitalux.backdrops import resolve
from vitalux.brand import _brand_asset
from vitalux.control import PreferencesPage

class Host(QWidget):
    _tray = True
    render_backend_active = "software"
    def apply_appearance(self):
        theme.set_mode(settings.get("theme","glass"))
        theme.set_accent(settings.get("accent","#4f8cff"))
    def set_interval(self, value):
        pass

def run():
    app = QApplication.instance() or QApplication([])
    assert "glass" in theme._THEMES and "black_glass" not in theme._THEMES
    assert "black_glass_gold" in theme._THEMES and "holographic" in theme._THEMES
    previous_theme = settings.get("theme","glass")
    previous_accent = settings.get("accent","#4f8cff")
    try:
        settings.set_many({"theme":"black_glass_gold","accent":"#f472b6"})
        theme.set_mode("black_glass_gold")
        theme.set_accent("#f472b6")
        assert theme.accent() == "#f472b6"
        assert theme.secondary_accent() != "#ffe4a2"
        assert resolve("theme_default","black_glass_gold") == "black_glass_gold"
        assert _brand_asset(True).endswith("pulse-pink.svg")
        assert _brand_asset(False).endswith("wordmark-pink.svg")
        host = Host()
        page = PreferencesPage(host)
        page.show()
        app.processEvents()
        assert "holographic" in {tile.key for tile in page.design_tiles}
        assert "black_glass" not in {tile.key for tile in page.design_tiles}
        assert "black_glass_gold" in {tile.key for tile in page.design_tiles}
        assert not page.accent_combo.isLocked()
        assert page.custom_accent_button.isEnabled()
        assert not page.background_combo.isLocked()
        assert not hasattr(page, 'background_lock_note')
        assert resolve('custom_image', 'black_glass_gold') == 'custom_image'
        page.change_accent("#ef4444")
        assert settings.get("accent") == "#ef4444"
        page.select_design("glass")
        app.processEvents()
        assert page.accent_combo.isEnabled()
        assert settings.get("accent") == "#ef4444"
        page.close()
        host.close()
    finally:
        settings.set_many({"theme":previous_theme,"accent":previous_accent})
        theme.set_mode(previous_theme)
        theme.set_accent(previous_accent)
    print("Gold, Glass, Black Glass and Holographic theme compatibility: OK")
if __name__ == "__main__":
    run()
