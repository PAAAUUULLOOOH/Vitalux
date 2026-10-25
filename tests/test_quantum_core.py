"""Quantum's static background, independent logo motion and retired profiles."""
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
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication
from vitalux import (appearance, brand, design_capabilities, distro, profiles, quantum_core, settings, theme)
from vitalux.logo import load_logo
from vitalux.signature_designs import Metric
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow

ROOT = Path(__file__).resolve().parents[1]
app = QApplication.instance() or QApplication([])
app.setQuitOnLastWindowClosed(False)


def wait(milliseconds):
    end = time.monotonic() + milliseconds / 1000
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(.01)


manifest = json.loads((ROOT / 'assets/brand/manifest.json').read_text())
artwork = [item for item in manifest if 'quantum-core' in item['file']]
assert len(artwork) == 4
assert not any('aurora-gold' in item['file'] for item in manifest)
assert not list((ROOT / 'assets/brand').rglob('*aurora-gold.svg'))
for item in artwork:
    data = (ROOT / item['file']).read_bytes()
    assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']

with tempfile.TemporaryDirectory(prefix='vitalux-quantum-') as folder, patch.object(settings, 'PATH', str(Path(folder) / 'settings.json')):
    settings.set_many(dict(theme='obsidian_gold', accent='#f472b6', background_style='custom_image',
                           custom_background_selected='personal.png', close_to_tray=False,
                           motion='smooth', guide_intro_choice='completed'))
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
        scene = window.centralWidget()
        assert len(preferences.design_tiles) == len(theme.CHOICES) == 15
        assert 'aurora_gold' not in dict(theme.CHOICES)
        for mode in ('quantum_core', 'nebula_prism', 'quantum_core', 'liquid_silver', 'quantum_core'):
            preferences.select_design(mode)
            wait(120)
            assert window.sampler is sampler and sampler.isRunning()
            assert settings.get('accent') == '#f472b6'
            assert settings.get('background_style') == 'custom_image'
            assert settings.get('custom_background_selected') == 'personal.png'
            if mode != 'quantum_core':
                assert not scene._wallpaper_timer.isActive()
                continue
            assert theme.accent() == quantum_core.PALETTE['accent'] == '#2fe6ff'
            assert not any(design_capabilities.capabilities(mode).values())
            assert preferences.accent_combo.isLocked() and preferences.background_combo.isLocked()
            assert not preferences.custom_accent_button.isEnabled()
            assert not scene._wallpaper_timer.isActive()
            assert window.pulse_core._timer.isActive() and window.brand_mark._timer.isActive()
            assert window.sidebar.isVisible() and window.design_shell.dock_row.isHidden()
            assert len(window.pages) == 12
            assert all(button.isVisible() for button in window.nav_buttons)
            assert all(host.currentIndex() == 1 for host in window.pages[0][1].design_metric_hosts.values())
            assert brand._brand_asset(False) == 'brand/vitalux-wordmark-quantum-core.svg'
            assert brand._brand_asset(True) == 'brand/vitalux-pulse-quantum-core.svg'

        first = scene.sharp_backdrop().toImage()
        phase = scene._phase
        wait(560)
        assert phase == scene._phase and first == scene.sharp_backdrop().toImage()
        base = quantum_core._base_layer(scene.width(), scene.height())
        assert base is quantum_core._base_layer(scene.width(), scene.height())
        assert quantum_core.scene_pixmap(QSize(400, 240)) is quantum_core.scene_pixmap(QSize(400, 240))

        settings.set('motion', 'off')
        window.apply_appearance()
        wait(100)
        assert not scene._wallpaper_timer.isActive()
        assert not window.pulse_core._timer.isActive() and not window.brand_mark._timer.isActive()
        first = scene.sharp_backdrop().toImage()
        wait(300)
        assert scene._phase == 0 and first == scene.sharp_backdrop().toImage()
        for language in ('de', 'en'):
            window.set_language(language)
            note = preferences.theme_note.text()
            assert note.startswith('Quantum Core')
            assert ('statischem' if language == 'de' else 'static') in note
            assert window.sampler is sampler and sampler.isRunning()

        metric = Metric('Prozessor', 'cpu')
        metric.resize(440, 240)
        metric.show()
        for value in (None, 0, 58, 96):
            metric.set(value, 'Detail', extra='Frequency', history=(None, 12, None, 35, value))
            wait(20)
            assert metric.value == value and not metric.grab().isNull()
        metric.close()

        settings.set('motion', 'smooth')
        settings.set('ultra_eco', True)
        window.apply_appearance()
        wait(100)
        assert theme.mode() == 'minimal' and not scene._wallpaper_timer.isActive()
        assert settings.get('theme') == 'quantum_core'
        settings.set('ultra_eco', False)
        window.apply_appearance()
        wait(120)
        assert theme.mode() == 'quantum_core' and not scene._wallpaper_timer.isActive()
        assert window.pulse_core._timer.isActive() and window.brand_mark._timer.isActive()
        window.hide()
        phase = scene._phase
        scene._advance_backdrop()
        assert scene._phase == phase
        window.show()
        wait(100)
        window.resize(800, 560)
        wait(250)
        assert window.size() == QSize(800, 560) and not window.grab().isNull()
        preferences.select_design('glass')
        wait(100)
        assert not scene._wallpaper_timer.isActive()
        assert preferences.accent_combo.isEnabled() and preferences.background_combo.isEnabled()
        assert window.sampler is sampler and sampler.isRunning()
    finally:
        window.quit_from_tray()
        wait(400)
        assert window.isHidden()

personal = dict(accent='#f472b6', background_style='custom_image',
                custom_background_selected='personal.png', dashboard_hidden=['gpu'], lang='de')
for revision in (None, 1, 2):
    before = dict(personal, theme='aurora_gold')
    if revision is not None:
        before['_appearance_revision'] = revision
    if revision == 1:
        before['accent_before_design_migration'] = personal['accent']
        before['background_before_design_migration'] = personal['background_style']
    after = appearance.migrate(before)
    assert after['theme'] == 'obsidian_gold'
    assert all(after[key] == value for key, value in personal.items())
    assert appearance.migrate(after) == after
    assert before['theme'] == 'aurora_gold'
theme.set_mode('aurora_gold')
assert theme.mode() == 'obsidian_gold'

with tempfile.TemporaryDirectory(prefix='vitalux-aurora-retirement-') as folder, patch.dict(os.environ, {
    f'XDG_{kind.upper()}_HOME': str(Path(folder) / kind) for kind in profiles.KINDS
}):
    stable = profiles.directory('config', 'stable') / 'settings.json'
    profiles.atomic_json(stable, dict(theme='aurora_gold', lang='en'))
    stable_before = stable.read_bytes()
    target = profiles.directory('config', 'unstable') / 'settings.json'
    before = dict(personal, theme='aurora_gold', _appearance_revision=2)
    profiles.atomic_json(target, before)
    profiles.initialize()
    assert profiles.read(target)['theme'] == 'obsidian_gold'
    assert all(profiles.read(target)[key] == value for key, value in personal.items())
    assert stable.read_bytes() == stable_before
    backups = (profiles.root('config') / 'profile-backups/unstable').glob('*/settings.json')
    assert any(profiles.read(path) == before for path in backups)

print('Quantum static/cached backdrop, independent logo motion, fixed options, live sampling, DE/EN and isolated Aurora migration PASS')
