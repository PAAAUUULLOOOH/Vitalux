"""Black Glass permits preset/custom accents and preserves them across designs."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QColor
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

            page.select_design("black_glass_gold")
            app.processEvents()
            assert page.accent_combo.isEnabled(), "Built-in colors must remain available"
            assert page.accent_combo.model().item(preset).isEnabled()
            assert page.accent_combo.model().item(custom).isEnabled()
            assert page.custom_accent_button.isEnabled()
            page.change_accent("#123456")
            assert settings.get("accent") == "#123456"
            assert settings.get("custom_accents") == [
                {"name": "Mein Petrol", "color": "#123456"}]

            with patch('vitalux.control.QColorDialog.getColor', return_value=QColor('#965173')), \
                    patch('vitalux.control.QInputDialog.getText', return_value=('Beere', True)):
                page.custom_accent_button.click()
            assert settings.get('accent') == '#965173'
            assert settings.get('custom_accents')[-1] == dict(name='Beere', color='#965173')
            with patch('vitalux.control.QColorDialog.getColor', return_value=QColor('#736495')), \
                    patch('vitalux.control.QInputDialog.getText', return_value=('Lavendel', True)):
                page.edit_custom_accent_button.click()
            assert settings.get('accent') == '#736495'
            assert settings.get('custom_accents')[-1] == dict(name='Lavendel', color='#736495')
            assert page.accent_combo.findData('#965173') == -1
            page.remove_custom_accent_button.click()
            assert settings.get('accent') == 'auto'
            assert page.accent_combo.findData('#736495') == -1
            assert settings.get('custom_accents') == [dict(name='Mein Petrol', color='#123456')]

            page.select_design('obsidian_gold')
            assert page.custom_accent_button.isEnabled()
            page.change_accent('#b9ccdc')
            assert theme.accent()=='#b9ccdc'
            assert settings.get('theme')=='obsidian_gold'

            page.select_design("glass")
            app.processEvents()
            assert page.custom_accent_button.isEnabled()
            assert page.accent_combo.model().item(custom).isEnabled()
            page.close()
            host.close()
        finally:
            settings.PATH = old
            theme.set_mode("glass")
    print("Black Glass create/apply/edit/delete, fixed-theme guards and cross-design persistence: OK")


if __name__ == "__main__":
    run()
