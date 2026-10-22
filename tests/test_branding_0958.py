"""Approved identity: authored colors, stable core, seamless motion and caches."""
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from vitalux import i18n, settings, theme
from vitalux.brand import (PulseCore, Wordmark, _brand_asset, _themed_svg,
                           _tinted_svg, _asset_bytes)

ASSETS = Path(__file__).resolve().parents[1]/'assets'


def difference(a, b):
    first, second = bytes(a.constBits()), bytes(b.constBits())
    return sum(abs(x-y) for x, y in zip(first, second))/len(first)


def run():
    app = QApplication.instance() or QApplication([])
    previous = settings.PATH
    with tempfile.TemporaryDirectory() as folder:
        settings.PATH = str(Path(folder)/'settings.json')
        pulse = mark = None
        try:
            settings.set_many({'theme': 'obsidian_gold', 'motion': 'smooth'})
            theme.set_mode('obsidian_gold')
            config = json.loads((ASSETS/'brand/palettes.json').read_text())
            # Every authored color keeps the exact approved outlines and has
            # working native filenames; no external font/image is required.
            outlines = set()
            for name in config['variants']:
                for kind in ('pulse', 'wordmark'):
                    path = ASSETS/f'brand/vitalux-{kind}-{name}.svg'
                    root = ET.parse(path).getroot()
                    assert not any(node.tag.rsplit('}', 1)[-1] in ('image', 'text')
                                   for node in root.iter()), path
                    if kind == 'wordmark':
                        outlines.add(next(n.get('d') for n in root.iter()
                                          if n.get('id') == 'wordmark-outline'))
            assert len(outlines) == 1
            for mode, variant in config['theme_assets'].items():
                theme.set_mode(mode)
                assert _brand_asset(True) == f'brand/vitalux-pulse-{variant}.svg'
                suffix = '-light' if config['variants'][variant].get('light_lens') else ''
                assert _brand_asset(False) == f'brand/vitalux-wordmark-{variant}{suffix}.svg'
            theme.set_mode('light')
            for key in ('blue', 'cyan', 'violet', 'green', 'orange', 'yellow', 'red', 'pink'):
                theme.set_accent(config['variants'][key]['accent'])
                assert _brand_asset(False) == f'brand/vitalux-wordmark-{key}-light.svg'

            # Custom circle tint is modestly richer. The wordmark preserves
            # the prior tint contract, including luminance and neutral edges.
            target = QColor('#d13d8f')
            hue, saturation, _, _ = target.getHsv()
            for filename in ('vitalux-pulse.svg', 'vitalux-wordmark.svg'):
                source = re.findall(r'#[0-9a-fA-F]{6}', _asset_bytes(filename).decode())
                result = re.findall(r'#[0-9a-fA-F]{6}', _tinted_svg(filename, target.name()).decode())
                enriched = False
                for before, after in zip(source, result):
                    old, new = QColor(before), QColor(after)
                    _, s, v, _ = old.getHsv()
                    if s < 22:
                        assert new == old
                        continue
                    legacy = QColor.fromHsv(hue, round(s*.65+saturation*.35), v)
                    if filename == 'vitalux-wordmark.svg':
                        assert new.name() == legacy.name(), 'Extra saturation escaped the circle logo'
                    else:
                        enriched |= new.hsvSaturation() > legacy.hsvSaturation()
                        assert abs(new.value()-v) <= 1
                        assert new.hsvSaturation() <= legacy.hsvSaturation()*1.081+2
                if filename == 'vitalux-pulse.svg':
                    assert enriched

            theme.set_mode('obsidian_gold')
            pulse, mark = PulseCore(256), Wordmark()
            pulse.show()
            mark.show()
            app.processEvents()
            pulse._timer.stop()
            mark._timer.stop()
            pulse._heartbeat_phase = .9
            pulse._phase = 0
            first = pulse.grab().toImage()
            cache = pulse._core_pixmap.cacheKey()
            pulse._phase = 95
            turned = pulse.grab().toImage()
            assert first != turned
            assert pulse._core_pixmap.cacheKey() == cache
            assert pulse._core_pixmap.devicePixelRatioF() >= 2
            # The glass and complete pulse remain stationary inside the bands.
            for y in range(48, 201):
                for x in range(53, 206):
                    if (x-129)**2+(y-124)**2 < 73**2:
                        assert first.pixel(x, y) == turned.pixel(x, y)
            pulse._heartbeat_phase = .15
            beat = pulse.grab().toImage()
            pulse._heartbeat_phase = .55
            assert pulse.grab().toImage() != beat

            # Just before/after the cycle boundary, only subpixel rotation
            # differs; heartbeat and letter reflection are already faded out.
            pulse._heartbeat_phase = .999999
            pulse._phase = 359.999
            end = pulse.grab().toImage()
            pulse._heartbeat_phase = .000001
            pulse._phase = .001
            assert difference(end, pulse.grab().toImage()) < .08
            mark._phase = .999999
            end = mark.grab().toImage()
            mark._phase = .000001
            assert end == mark.grab().toImage()
            mark._phase = .22
            assert mark.grab().toImage() != end

            # Changing colors and hiding/showing must not reset the clocks.
            pulse._phase, pulse._heartbeat_phase, mark._phase = 123, .34, .27
            theme.set_mode('aurora_gold')
            pulse.sync_theme()
            mark.sync_theme()
            assert (pulse._phase, pulse._heartbeat_phase, mark._phase) == (123, .34, .27)
            pulse.hide()
            mark.hide()
            assert not pulse._timer.isActive() and not mark._timer.isActive()
            pulse.show()
            mark.show()
            assert pulse._timer.isActive() and mark._timer.isActive()
            for motion in ('off', 'reduced', 'smooth'):
                settings.set('motion', motion)
                pulse.sync_theme()
                mark.sync_theme()
                assert pulse._timer.isActive() == (motion != 'off')
                assert mark._timer.isActive() == (motion != 'off')
            for language in ('de', 'en'):
                i18n.set_lang(language)
                pulse.sync_theme()
                assert ('Live-Telemetrie' if language == 'de' else 'Live telemetry') in pulse.toolTip()
        finally:
            if pulse is not None:
                pulse.close()
            if mark is not None:
                mark.close()
            settings.PATH = previous
    print('Approved vector colors, stationary core, clear pulse, seamless boundaries, DPR cache and motion controls PASS')


if __name__ == '__main__':
    run()
