"""Gold theme regression: all dashboard legends and gauges are gold on first frame."""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())

from PySide6.QtWidgets import QApplication
from vitalux import theme
from vitalux.widgets import ChartPanel, Gauge
from vitalux.pages import MemoryPage


def gold(color):
    from PySide6.QtGui import QColor
    c = QColor(color)
    assert c.isValid(), color
    # Gold/pale gold must not have the original teal/blue or pink color cast.
    r, g, b = c.red(), c.green(), c.blue()
    assert r >= g >= b and r > b + 25, (color, r, g, b)


def run():
    app = QApplication.instance() or QApplication([])
    before = theme.mode()
    try:
        theme.set_mode('black_glass_gold')
        theme.set_accent('#f3cd79')
        chart = ChartPanel(
            ['CPU', 'GPU', 'RAM'],
            [theme.accent(), theme.secondary_accent(), theme.TEAL])
        chart.show()
        app.processEvents()
        for toggle in chart.toggles:
            gold(toggle.series_color)
        assert chart.toggles[2].series_color.lower() == '#f4cf81'
        chart.set_series([([30.0, 35.0], theme.accent()),
                          ([18.0, 22.0], theme.secondary_accent()),
                          ([60.0, 64.0], theme.TEAL)])
        assert '#f4cf81' in chart.live_labels[2].styleSheet()
        memory = MemoryPage()
        memory.show()
        app.processEvents()
        gold(memory.graph.toggles[0].series_color)
        for percent in (12, 80, 95):
            gold(theme.level_color(percent))
        gauge = Gauge()
        gauge.set_semantic('score')
        gold(gauge._ring_color(44))
        gold(gauge._ring_color(77))
        gold(gauge._ring_color(98))
        theme.set_mode('glass')
        chart.retheme()
        assert chart.toggles[2].series_color.lower() == theme.TEAL.lower(), (
            'Normal theme should retain its original series color')
        chart.close()
        memory.close()
        gauge.close()
        print('Black Glass Gold: chart legends, RAM text and gauges all themed: OK')
    finally:
        theme.set_mode(before)


if __name__ == '__main__':
    run()
