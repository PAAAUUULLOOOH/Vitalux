"""Ultra Eco regression: temporary flat skin, no GPU, animation or lost settings."""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())

from PySide6.QtWidgets import QApplication, QWidget
from vitalux import eco, renderer, settings, theme, motion, backdrops
from vitalux.control import PreferencesPage
from vitalux.glass import AmbientScene, create_ambient_scene


class Host(QWidget):
    _tray = True
    render_backend_active = renderer.SOFTWARE

    def __init__(self):
        super().__init__()
        self.intervals = []
        self.restarts = 0

    def apply_appearance(self):
        theme.set_mode(eco.theme_name())

    def set_interval(self, val):
        self.intervals.append(val)

    def restart_for_renderer(self):
        self.restarts += 1
        return True


def run():
    app = QApplication.instance() or QApplication([])
    previous = settings.PATH
    with tempfile.TemporaryDirectory(prefix='vitalux-eco-') as folder:
        settings.PATH = str(Path(folder) / 'settings.json')
        try:
            original = {
                'theme': 'glass', 'accent': '#f472b6', 'motion': 'smooth',
                'background_style': 'animated_sparkle',
                'render_backend': renderer.WAYLAND_VULKAN, 'interval': 1,
                'ultra_eco': False,
            }
            assert settings.set_many(original)
            theme.set_mode('glass')
            assert not eco.enabled()
            assert renderer.desired() == renderer.WAYLAND_VULKAN
            host = Host()
            pref = PreferencesPage(host)
            pref.show()
            app.processEvents()
            app.processEvents()
            assert pref.eco_toggle.isEnabled()
            assert not pref.eco_toggle.isChecked()
            assert pref.render_restart_button.isVisible(), 'Saved GPU profile is awaiting renderer restart'
            assert not pref.eco_restart_button.isVisible(), 'Renderer changes must not activate Ultra Eco restart'
            pref.eco_toggle.setChecked(True)
            app.processEvents()
            assert eco.enabled()
            assert theme.mode() == 'minimal'
            assert eco.interval() == 10
            assert renderer.desired() == renderer.SOFTWARE
            # Software renderer is already active, so enabling Ultra Eco does
            # not require a restart. Only pending backend changes show buttons.
            assert not pref.eco_restart_button.isVisible()
            assert not pref.render_restart_button.isVisible()
            assert host.restarts == 0, 'Never restart automatically on toggle'
            assert renderer.prepare_start() == renderer.SOFTWARE
            assert motion.level() == 'off' and not motion.enabled()
            assert motion.duration(500) == 0
            assert backdrops.resolve('animated_sparkle', 'minimal') == 'minimal'
            assert host.intervals[-1] == 10
            assert not pref.design_tiles[0].isEnabled()
            assert pref.background_combo.isLocked()
            assert pref.accent_combo.isLocked()
            assert not pref.motion_combo.isEnabled()
            assert not pref.render_combo.isEnabled()
            assert not pref.interval.isEnabled()
            scene = create_ambient_scene()
            assert isinstance(scene, AmbientScene), 'GPU should never initialize in eco mode'
            assert scene.render_backend == renderer.SOFTWARE
            assert not scene._wallpaper_timer.isActive()
            scene.resize(320, 220)
            scene.show()
            app.processEvents()
            assert not scene.grab().isNull()
            scene.close()
            for key, expected in original.items():
                if key != 'ultra_eco':
                    assert settings.get(key) == expected, (key, settings.get(key))
            pref.eco_toggle.setChecked(False)
            app.processEvents()
            assert not eco.enabled()
            assert theme.mode() == 'glass'
            assert eco.interval() == 1
            assert motion.level() == 'smooth'
            assert renderer.desired() == renderer.WAYLAND_VULKAN
            assert host.intervals[-1] == 1
            assert host.restarts == 0, 'Toggle never restarts without user action'
            assert pref.render_restart_button.isVisible()
            assert not pref.eco_restart_button.isVisible()
            assert pref.render_combo.currentData() == renderer.WAYLAND_VULKAN
            pref.render_restart_button.click()
            assert host.restarts == 1, 'Explicit restart applies remembered GPU backend'
            assert pref.design_tiles[0].isEnabled()
            assert pref.background_combo.isEnabled()
            assert pref.accent_combo.isEnabled()
            assert pref.motion_combo.isEnabled()
            assert pref.render_combo.isEnabled()
            assert pref.interval.isEnabled()
            for key, expected in original.items():
                assert settings.get(key) == expected, (key, settings.get(key))
            pref.close()
            host.close()
            print('Ultra Eco primitive skin, CPU fallback, and complete restoration: OK')
        finally:
            settings.PATH = previous
            theme.set_mode('glass')


if __name__ == '__main__':
    run()
