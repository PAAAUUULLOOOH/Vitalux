"""Outer artwork rotates while the authored pulse remains stationary."""
import os
from pathlib import Path
import sys
import tempfile
import time

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication
from vitalux import settings, theme
from vitalux.brand import PulseCore, _brand_asset, _logo_layers


def render(core, outer, angle):
    pixmap = QPixmap(256, 256)
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)
    core.render(p, QRectF(0, 0, 256, 256))
    p.translate(128, 128)
    p.rotate(angle)
    outer.render(p, QRectF(-128, -128, 256, 256))
    p.end()
    return pixmap.toImage()


def run():
    app = QApplication.instance() or QApplication([])
    previous = settings.PATH
    with tempfile.TemporaryDirectory() as directory:
        settings.PATH = str(Path(directory)/'settings.json')
        try:
            settings.set_many({'theme': 'obsidian_gold', 'motion': 'smooth'})
            theme.set_mode('obsidian_gold')
            core, outer = _logo_layers(_brand_asset(True))
            first, turned = render(core, outer, 0), render(core, outer, 95)
            assert first != turned, 'The outer SVG bands did not turn'
            for y in range(50, 207):
                for x in range(50, 207):
                    if (x-128)**2 + (y-128)**2 < 78**2:
                        assert first.pixel(x, y) == turned.pixel(x, y), 'The center moved with the bands'
            pulse = PulseCore(152)
            pulse.show()
            app.processEvents()
            assert pulse._timer.isActive()
            phase = pulse._phase
            pulse._last_tick = time.monotonic()-.12
            pulse._advance()
            assert .8 < pulse._phase-phase < 1.3, 'Rotation must follow elapsed time, not CPU load'
            pulse.hide()
            assert not pulse._timer.isActive()
            pulse.show()
            settings.set('motion', 'off')
            pulse.sync_theme()
            assert not pulse._timer.isActive()
            settings.set('motion', 'reduced')
            pulse.sync_theme()
            assert pulse._timer.isActive() and pulse._timer.interval() == 80
            settings.set('ultra_eco', True)
            pulse.sync_theme()
            assert not pulse._timer.isActive()
            pulse.close()
        finally:
            settings.PATH = previous
    print('Logo: stationary center, moving SVG bands, timed speed, hide/motion/Eco controls PASS')


if __name__ == '__main__':
    run()
