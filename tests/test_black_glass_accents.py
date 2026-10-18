"""Black Glass keeps preset accents while disabling custom accent edits."""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())

from PySide6.QtWidgets import QApplication, QWidget
from vitalux import settings, theme
from vitalux.control import PreferencesPage


class Host(QWidget):
    _tray = True
    render_backend_active = "software"
    def apply_appearance(self):
        theme.set_mode(settings.get("theme", "glass"))
        theme.set_accent(settings.get("accent", "#4f8cff"))
    def set_interval(self, value):
        pass


def run():
    app = QApplication.instance() or QApplication([])
    old = settings.PATH
    with tempfile.TemporaryDirectory(prefix="vitalux-black-accent-") as temp:
        settings.PATH = str(Path(temp) / "settings.json")
        try:
            settings.set_many({
                "theme": "glass",
                "accent": "#4f8cff",
                "custom_accents": [{"name": "Mein Petrol", "color": "#123456"}],
            })
            theme.set_mode("glass")
            host = Host()
            page = PreferencesPage(host)
            page.show()
            app.processEvents()
            custom = page.accent_combo.findData("#123456")
            preset = page.accent_combo.findData("#4f8cff")
            assert custom >= 0 and preset >= 0
            assert page.custom_accent_button.isEnabled()
            assert page.accent_combo.model().item(custom).isEnabled()

            page.mode.setCurrentIndex(page.mode.findData("black_glass"))
            app.processEvents()
            assert page.accent_combo.isEnabled(), "Built-in colors must remain available"
            assert page.accent_combo.model().item(preset).isEnabled()
            assert not page.accent_combo.model().item(custom).isEnabled()
            assert not page.custom_accent_button.isEnabled()
            page.change_accent("#123456")
            assert settings.get("accent") == "#4f8cff"
            page.remove_custom_accent()
            page.edit_custom_accent()
            page.custom_accent(page.accent_combo)
            assert settings.get("custom_accents") == [
                {"name": "Mein Petrol", "color": "#123456"}]

            page.mode.setCurrentIndex(page.mode.findData("glass"))
            app.processEvents()
            assert page.custom_accent_button.isEnabled()
            assert page.accent_combo.model().item(custom).isEnabled()
            page.close()
            host.close()
        finally:
            settings.PATH = old
            theme.set_mode("glass")
    print("Black Glass custom accent lock and non-destructive restore: OK")


if __name__ == "__main__":
    run()
