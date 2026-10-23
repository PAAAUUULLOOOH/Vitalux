"""Nebula's imported artwork, fixed controls and live dock/design transitions."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from vitalux import brand, design_capabilities, distro, i18n, nebula_prism, profiles, settings, theme
from vitalux.logo import load_logo
from vitalux.signature_designs import Metric
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow


app = QApplication.instance() or QApplication([])
app.setQuitOnLastWindowClosed(False)


def wait(milliseconds):
    end = time.monotonic() + milliseconds / 1000
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(.01)


assets = Path(__file__).resolve().parents[1] / 'assets'
manifest = json.loads((assets / 'brand/manifest.json').read_text())
imported = [item for item in manifest if 'nebula-prism' in item['file']]
assert len(imported) == 4
for item in imported:
    data = (assets.parent / item['file']).read_bytes()
    assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']

with tempfile.TemporaryDirectory(prefix='vitalux-nebula-') as temporary, patch.object(settings, 'PATH', str(Path(temporary) / 'settings.json')):
    settings.set_many(dict(theme='obsidian_gold', accent='#f472b6', background_style='prism',
                           close_to_tray=False, motion='off', guide_intro_choice='completed'))
    theme.set_mode('obsidian_gold')
    app.setStyleSheet(theme.stylesheet())
    info = distro.info()
    manager = UpdateManager()
    manager._timer.stop()
    window = MainWindow(info, load_logo(info, 96), manager)
    window.resize(1380, 1000)
    window.show()
    try:
        wait(1500)
        assert window.last_sample is not None
        sampler = window.sampler
        preferences = dict(window.pages)['Einstellungen']
        window.pulse_core._phase = 137
        for mode in ('nebula_prism', 'liquid_silver', 'nebula_prism', 'eclipse_crystal', 'nebula_prism', 'glass', 'nebula_prism'):
            preferences.select_design(mode)
            wait(100)
            assert window.sampler is sampler and sampler.isRunning()
            assert window.pulse_core._phase == 137, 'Design changes reset the existing animation phase'
            assert settings.get('accent') == '#f472b6' and settings.get('background_style') == 'prism'
            if mode != 'nebula_prism':
                assert window.design_shell.dock_row.isHidden()
                continue
            assert theme.accent() == nebula_prism.PALETTE['accent'] == '#5ef0ff'
            assert not any(design_capabilities.capabilities(mode).values())
            assert preferences.accent_combo.isLocked() and preferences.background_combo.isLocked()
            assert not preferences.custom_accent_button.isEnabled()
            assert window.sidebar.isHidden() and window.design_shell.dock_row.isVisible()
            assert window.design_shell.dock_layout.count() == len(window.pages) == 12
            assert window.lang_host.parentWidget() is window.design_shell.bar
            assert brand._brand_asset(False) == 'brand/vitalux-wordmark-nebula-prism.svg'
            assert brand._brand_asset(True) == 'brand/vitalux-pulse-nebula-prism.svg'
            assert window.pages[0][1].design_metric_hosts['cpu'].currentIndex() == 1
            for button in window.nav_buttons:
                assert button.isVisible() and button.parentWidget() is window.design_shell.dock
                assert button.width() == 54 and button.height() == 46
        version = '0.9.6.3-unstable.99'
        manager.status = 'available'
        manager.records[profiles.installed()] = dict(ok=True, newer=True, eligible=True, latest=version)
        window._notified_update_version = version
        window._sync_glow()
        for language in ('en', 'de'):
            window.set_language(language)
            wait(100)
            for (name, _), button in zip(window.pages, window.nav_buttons):
                caption = i18n.tr(name)
                assert button.accessibleName() == caption
                assert button.toolTip().startswith(caption)
                assert button.height() == 46
            assert version in window.update_btn.toolTip(), 'Language change lost the icon-only update version'
        manager.records.clear()
        manager.status = 'idle'
        window._sync_glow()
        window.resize(800, 560)
        wait(300)
        assert window.size().width() == 800 and window.size().height() == 560
        dock = window.design_shell.dock
        assert dock.width() <= window.width()
        for button in window.nav_buttons:
            assert button.geometry().right() <= dock.width()
        assert not window.grab().isNull()
        # Missing readings and gaps remain real gaps in the imported gauges.
        metric = Metric('Prozessor', 'cpu')
        metric.resize(440, 240)
        metric.show()
        for value in (None, 0, 58, 96):
            metric.set(value, 'Detail', extra='Frequency', history=(None, 12, None, 35, value))
            wait(20)
            assert metric.value == value and not metric.grab().isNull()
        metric.close()
        preferences.select_design('obsidian_gold')
        wait(100)
        assert not window.sidebar.isHidden() and window.design_shell.dock_row.isHidden()
        assert window.pulse_core.parentWidget() is window.sidebar_brand
        assert all(button.maximumHeight() == 16777215 for button in window.nav_buttons)
    finally:
        window.quit_from_tray()
        wait(350)
        assert window.isHidden()

print('Nebula artwork, fixed palette/background, 800px dock, DE/EN hints, update badge, data gaps and preserved live sampling PASS')
