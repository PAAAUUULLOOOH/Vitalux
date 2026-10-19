"""User interactions: predictions, disclosure, safe wheels, feedback and hover."""
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QEnterEvent, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QScrollArea, QWidget
from vitalux import i18n, settings, theme
from vitalux.control import PreferencesPage
from vitalux.ui_sound import install


class Host(QWidget):
    _tray = None
    render_backend_active = 'software'
    def apply_appearance(self):
        theme.set_mode(settings.get('theme', 'glass'))
        theme.set_accent(settings.get('accent', '#4f8cff'))
    def set_interval(self, value):
        self.interval = value


def run():
    app = QApplication.instance() or QApplication([])
    previous = settings.PATH
    with tempfile.TemporaryDirectory() as folder:
        settings.PATH = str(Path(folder)/'settings.json')
        settings.set_many({'theme': 'glass', 'motion': 'smooth', 'ui_sounds': True})
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
        assert not advanced.expanded and advanced.clip.isHidden()
        assert advanced.isAncestorOf(page.render_combo) and advanced.isAncestorOf(page.clear_cache_btn)
        advanced.header.click()
        advanced.animation.setCurrentTime(170)
        height = advanced.clip.height()
        assert 0 < height < advanced._extent
        advanced.header.click()
        assert advanced.clip.height() == height, 'Collapse jumped to an endpoint'
        advanced.animation.setCurrentTime(170)
        assert 0 < advanced.clip.height() < height
        advanced.header.click()
        QTest.qWait(450)
        assert advanced.expanded and advanced.clip.height() == advanced._extent
        advanced.header.click()
        QTest.qWait(450)
        assert advanced.clip.isHidden() and advanced.clip.height() == 0

        # Recognition opens the advanced section and glides there while input stays.
        floating = page.search_overlay
        scroll.verticalScrollBar().setValue(0)
        floating.open_search()
        QTest.qWait(400)
        page.search.setText('vulk')
        QTest.qWait(230)
        assert advanced.expanded
        navigation = page.search_navigation
        navigation.animation.setCurrentTime(180)
        assert scroll.verticalScrollBar().value() > 0
        assert page.search.hasFocus() and floating.expanded
        page.choose_search_result(page.search_results.item(0))
        assert floating.expanded and floating.idle_timer.isActive()
        assert 4700 <= floating.idle_timer.remainingTime() <= 5250
        QTest.qWait(550)
        assert page.render_combo.hasFocus()
        assert floating.field.text() == 'vulk' and floating.expanded
        floating.idle_timer.timeout.emit()
        floating.animation.setCurrentTime(170)
        assert floating.isVisible() and 0 < floating._opacity.opacity() < 1
        QTest.qWait(450)
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

        guard = install(app)
        combo = page.interval
        scroll.ensureWidgetVisible(combo)
        QTest.qWait(30)
        with patch.object(guard, 'play') as play:
            QTest.mouseClick(combo, Qt.LeftButton)
            assert combo.view().isVisible()
            assert play.call_count == 1, play.call_count
            QTest.qWait(50)
            view = combo.view()
            QTest.keyClick(view, Qt.Key_Down)
            QTest.keyClick(view, Qt.Key_Return)
            assert combo.currentIndex() == 1
            assert play.call_count == 2, play.call_count
            page.select_design('aurora_gold')
            fixed = page.background_combo
            assert fixed.isLocked() and not fixed.isEnabled()
            fixed.showPopup()
            QTest.mouseClick(fixed, Qt.LeftButton)
            assert not fixed.view().isVisible()
            assert play.call_count == 2

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
        QTest.qWait(220)
        assert tile._hover == 0 and tile.geometry() == geometry
        scroll.close()
        host.close()
        guard.stop()
        settings.PATH = previous
    print('Prediction, delayed search close, advanced disclosure, wheel safety, combo audio and tile zoom PASS')


if __name__ == '__main__':
    run()
