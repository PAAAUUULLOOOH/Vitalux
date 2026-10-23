"""Lumen's original artwork, crown navigation, loop continuity and live switching."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QEvent, QSize
from PySide6.QtGui import QCursor, QHelpEvent
from PySide6.QtWidgets import QApplication, QToolTip
from vitalux import brand, design_capabilities, distro, hover_hints, i18n, lumen_drift, profiles, settings, theme
from vitalux.logo import load_logo
from vitalux.signature_designs import Metric
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow

ROOT = Path(__file__).resolve().parents[1]
app = QApplication.instance() or QApplication([])
app.setQuitOnLastWindowClosed(False)
guard = hover_hints.install(app)

def wait(milliseconds):
    deadline = time.monotonic() + milliseconds / 1000
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)

manifest = json.loads((ROOT / 'assets/brand/manifest.json').read_text())
assets = [entry for entry in manifest if 'lumen-drift' in entry['file']]
assert len(assets) == 4
for entry in assets:
    data = (ROOT / entry['file']).read_bytes()
    assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256']

with tempfile.TemporaryDirectory(prefix='vitalux-lumen-') as folder, patch.object(settings, 'PATH', str(Path(folder) / 'settings.json')):
    settings.set_many(dict(theme='obsidian_gold', accent='#f472b6', background_style='prism',
                           motion='off', close_to_tray=False, guide_intro_choice='completed'))
    theme.set_mode('obsidian_gold')
    app.setStyleSheet(theme.stylesheet())
    info = distro.info()
    manager = UpdateManager()
    manager._timer.stop()
    window = MainWindow(info, load_logo(info, 96), manager)
    window.resize(1380, 1000)
    window.show()
    try:
        wait(1400)
        assert window.last_sample is not None
        sampler = window.sampler
        preferences = dict(window.pages)['Einstellungen']
        scene = window.centralWidget()
        assert len(theme.CHOICES) == len(preferences.design_tiles) == 14
        assert 'aurora_gold' not in dict(theme.CHOICES)
        window.pulse_core._phase = 137
        for mode in ('lumen_drift', 'nebula_prism', 'lumen_drift', 'eclipse_crystal',
                     'lumen_drift', 'quantum_core', 'lumen_drift', 'glass', 'lumen_drift'):
            preferences.select_design(mode)
            wait(80)
            assert window.sampler is sampler and sampler.isRunning()
            assert window.pulse_core._phase == 137
            assert settings.get('accent') == '#f472b6' and settings.get('background_style') == 'prism'
            if mode != 'lumen_drift':
                assert window.design_shell.crown_row.isHidden()
                assert not any(button.property('vitaluxCapabilityHints') for button in window.nav_buttons)
                continue
            assert theme.accent() == lumen_drift.PALETTE['accent'] == '#f3c98b'
            assert not any(design_capabilities.capabilities(mode).values())
            assert preferences.accent_combo.isLocked() and preferences.background_combo.isLocked()
            assert not preferences.custom_accent_button.isEnabled()
            assert window.sidebar.isHidden() and window.design_shell.crown_row.isVisible()
            assert window.design_shell.dock_row.isHidden()
            assert window.design_shell.crown_layout.count() == len(window.pages) == 12
            assert window.lang_host.parentWidget() is window.design_shell.bar
            assert brand._brand_asset(True) == 'brand/vitalux-pulse-lumen-drift.svg'
            assert brand._brand_asset(False) == 'brand/vitalux-wordmark-lumen-drift.svg'
            for button in window.nav_buttons:
                assert button.isVisible() and button.parentWidget() is window.design_shell.crown
                assert button.size() == QSize(50, 42)

        version = '0.9.6.3-unstable.99'
        manager.records[profiles.installed()] = dict(ok=True, newer=True, eligible=True, latest=version)
        manager.status = 'available'
        window._notified_update_version = version
        window._sync_glow()
        for language in ('de', 'en'):
            window.set_language(language)
            wait(50)
            assert ('Pastellakzenten' if language == 'de' else 'pastel accents') in preferences.theme_note.text()
            for (name, _), button in zip(window.pages, window.nav_buttons):
                assert button.accessibleName() == i18n.tr(name)
                assert button.toolTip().startswith(i18n.tr(name))
                assert button.size() == QSize(50, 42)
            assert version in window.update_btn.toolTip()
        # Keep the pointer inside the offscreen platform's 800px virtual
        # screen and test one real hover after language changes have settled.
        # Reopening identical text during Qt's delayed hide can cancel a tip.
        window.resize(800, 560)
        wait(160)
        button = window.update_btn
        point = button.rect().center()
        global_point = button.mapToGlobal(point)
        QCursor.setPos(global_point)
        wait(80)
        event = QHelpEvent(QEvent.ToolTip, point, global_point)
        assert not guard.eventFilter(button, event)
        QApplication.sendEvent(button, event)
        deadline = time.monotonic() + 1
        while not QToolTip.isVisible() and time.monotonic() < deadline:
            wait(20)
        assert QToolTip.isVisible() and version in QToolTip.text()
        QToolTip.hideText()
        QCursor.setPos(0, 0)
        wait(360)
        manager.records.clear()
        manager.status = 'idle'
        window._sync_glow()

        settings.set('motion', 'smooth')
        window.apply_appearance()
        wait(120)
        assert scene._wallpaper_timer.isActive()
        first = scene.sharp_backdrop().toImage()
        phase = scene._phase
        wait(560)
        assert scene._phase != phase and first != scene.sharp_backdrop().toImage()
        scene._wallpaper_timer.stop()
        scene._phase = 6.2
        scene._advance_backdrop()
        assert scene._phase > 6.28, 'Lumen must not cut its slower waves at one turn'
        size = QSize(400, 240)
        assert lumen_drift.scene_pixmap(size, 0).toImage() == lumen_drift.scene_pixmap(size, 100 * math.tau - 1e-7).toImage()
        assert lumen_drift._base_layer(400, 240) is lumen_drift._base_layer(400, 240)

        settings.set('motion', 'off')
        window.apply_appearance()
        assert not scene._wallpaper_timer.isActive() and scene._phase == 0
        first = scene.sharp_backdrop().toImage()
        wait(300)
        assert first == scene.sharp_backdrop().toImage()
        metric = Metric('Prozessor', 'cpu')
        metric.resize(440, 240)
        metric.show()
        for value in (None, 0, 58, 96):
            metric.set(value, 'Detail', extra='Frequency', history=(None, 12, None, 35, value))
            wait(20)
            assert metric.value == value and not metric.grab().isNull()
        metric.close()

        settings.set('ultra_eco', True)
        window.apply_appearance()
        assert theme.mode() == 'minimal' and not scene._wallpaper_timer.isActive()
        assert settings.get('theme') == 'lumen_drift'
        settings.set('ultra_eco', False)
        window.apply_appearance()
        window.resize(800, 560)
        wait(250)
        assert window.size() == QSize(800, 560)
        assert window.design_shell.crown.width() <= window.width()
        assert all(button.geometry().right() <= window.design_shell.crown.width() for button in window.nav_buttons)
        preferences.select_design('obsidian_gold')
        wait(80)
        assert window.sidebar.isVisible() and window.design_shell.crown_row.isHidden()
        assert window.pulse_core.parentWidget() is window.sidebar_brand
        assert all(button.maximumHeight() == 16777215 for button in window.nav_buttons)
        assert window.sampler is sampler and sampler.isRunning()
    finally:
        QToolTip.hideText()
        window.quit_from_tray()
        wait(400)
        assert window.isHidden()

print('Lumen artwork, 800px crown, real DE/EN hover/update hints, live sampling, fixed options and seamless motion/Eco PASS')
