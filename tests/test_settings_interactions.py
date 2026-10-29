"""User interactions: predictions, disclosure, safe wheels, feedback and hover."""
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QEnterEvent, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QScrollArea, QWidget
from vitalux import settings, theme
from vitalux.control import PreferencesPage


class Host(QWidget):
    _tray = None
    render_backend_active = 'software'
    def apply_appearance(self, *, before=None):
        theme.set_mode(settings.get('theme', 'glass'))
        theme.set_accent(settings.get('accent', '#4f8cff'))
    def set_interval(self, value):
        self.interval = value


def run():
    app = QApplication.instance() or QApplication([])
    previous = settings.PATH
    with tempfile.TemporaryDirectory() as folder:
        settings.PATH = str(Path(folder)/'settings.json')
        settings.set_many({'theme': 'glass', 'motion': 'smooth'})
        theme.set_mode('glass')
        app.setStyleSheet(theme.stylesheet())
        host = Host()
        page = PreferencesPage(host)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.resize(1050, 700)
        page.install_search_overlay(scroll)
        scroll.show()
        QTest.qWait(120)
        advanced = page.advanced
        assert page.content.indexOf(advanced) == page.content.count()-1
        assert advanced.panel.isVisible()
        assert advanced.isAncestorOf(page.render_combo) and advanced.isAncestorOf(page.restore_button)
        assert not hasattr(advanced,'animation') and not hasattr(advanced.header,'click')

        # Recognition opens the advanced section and glides there while input stays.
        floating = page.search_overlay
        scroll.verticalScrollBar().setValue(0)
        floating.open_search()
        QTest.qWait(400)
        page.search.setText('x11')
        QTest.qWait(230)
        assert advanced.panel.isVisible()
        navigation = page.search_navigation
        import time
        deadline=time.monotonic()+3
        while scroll.verticalScrollBar().value()==0 and time.monotonic()<deadline:
            QTest.qWait(20)
        assert scroll.verticalScrollBar().value() > 0
        assert page.search.hasFocus() and floating.expanded
        page.choose_search_result(page.search_results.item(0))
        assert floating.expanded and floating.idle_timer.isActive()
        assert 4700 <= floating.idle_timer.remainingTime() <= 5250
        # Qt completes navigation asynchronously; wait for the focus handoff
        # instead of assuming an exact animation frame under parallel load.
        deadline = time.monotonic()+2
        while not page.render_combo.hasFocus() and time.monotonic() < deadline:
            QTest.qWait(20)
        assert page.render_combo.hasFocus()
        assert floating.field.text() == 'x11' and floating.expanded
        floating.idle_timer.timeout.emit()
        floating.animation.setCurrentTime(170)
        assert floating.isVisible() and 0 < floating._opacity.opacity() < 1
        QTest.qWait(450)
        import time
        deadline=time.monotonic()+2
        while not floating.isHidden() and time.monotonic()<deadline:QTest.qWait(20)
        assert floating.isHidden()

        # Maintenance is searchable in English too, even while the UI is German.
        page.search.setText('maintenance')
        assert page.search_results.count()
        page.search_navigation.cancel()

        # A focused but closed selector must never consume wheel-based choices.
        for combo in (page.interval, page.hud_size, page.render_combo):
            combo.setFocus()
            index = combo.currentIndex()
            point = QPointF(combo.rect().center())
            event = QWheelEvent(point, QPointF(combo.mapToGlobal(combo.rect().center())), QPoint(),
                                QPoint(0, -120), Qt.NoButton, Qt.NoModifier, Qt.ScrollUpdate, False)
            QApplication.sendEvent(combo, event)
            assert combo.currentIndex() == index
            assert not combo.view().isVisible()

        combo = page.interval
        scroll.ensureWidgetVisible(combo)
        QTest.qWait(30)
        QTest.mouseClick(combo, Qt.LeftButton)
        assert combo.view().isVisible()
        QTest.keyClick(combo.view(), Qt.Key_Down)
        QTest.keyClick(combo.view(), Qt.Key_Return)
        assert combo.currentIndex() == 1
        page.select_design('quantum_core')
        fixed = page.background_combo
        assert not fixed.isLocked() and fixed.isEnabled()
        fixed.showPopup()
        QTest.mouseClick(fixed, Qt.LeftButton)
        fixed.hidePopup()
        assert not fixed.view().isVisible()

        # Hover paints a small zoom without reflowing or rebuilding its backdrop.
        tile = page.design_tiles[0]
        geometry = tile.geometry()
        tile._hover_to(0.0)
        QTest.qWait(200)
        resting = tile.grab().toImage()
        backdrop = tile._background
        QApplication.sendEvent(tile, QEnterEvent(QPointF(10, 10), QPointF(10, 10), QPointF(10, 10)))
        tile._hover_animation.setCurrentTime(90)
        assert 0 < tile._hover < 1
        assert tile.geometry() == geometry and tile._background is backdrop
        assert tile.grab().toImage() != resting
        QApplication.sendEvent(tile, QEvent(QEvent.Leave))
        QTest.qWait(300)
        assert tile._hover == 0 and tile.geometry() == geometry
        scroll.close()
        host.close()
        settings.PATH = previous
    print('Prediction, delayed search close, advanced disclosure, wheel safety and tile zoom PASS')


if __name__ == '__main__':
    run()
