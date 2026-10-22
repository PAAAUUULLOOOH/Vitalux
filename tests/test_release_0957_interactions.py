"""Exercise the new settings flows, actual painted controls and safe reset."""
import os
from pathlib import Path
import sys
import tempfile
from threading import Event
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())
from PySide6.QtCore import QPoint, QRectF, QThread, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from vitalux import DEFAULT_THEME, eco, i18n, settings, theme
from vitalux.control import PreferencesPage
from vitalux.diagnostic_center import DiagnosticCenter
from vitalux.sample_clock import sampling_gap
from vitalux.ui_locale import QMessageBox
from vitalux.update_manager import UpdateManager
from vitalux.widgets import ChartPanel
from vitalux.window import MainWindow, Sampler


class SlowRead(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.release = Event()

    def run(self):
        self.release.wait(10)


def run():
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    previous_path, previous_lang = settings.PATH, i18n.lang()
    window, workers = None, []
    with tempfile.TemporaryDirectory() as directory:
        settings.PATH = str(Path(directory)/'settings.json')
        try:
            i18n.set_lang('en')
            assert eco.theme_name() == DEFAULT_THEME == 'obsidian_gold'
            settings.set('theme', 'glass')
            assert eco.theme_name() == 'glass', 'An update replaced a saved theme'
            settings.set('theme', DEFAULT_THEME)
            # An old disabled preference must not undo the compact standard.
            settings.set('compact_overview', False)
            theme.set_mode(DEFAULT_THEME)
            app.setStyleSheet(theme.stylesheet())
            with patch.object(Sampler, 'start'):
                window = MainWindow({'name': 'Linux', 'short': 'Test', 'version': '1',
                                     'color': '#4f8cff'}, QPixmap(96, 96), UpdateManager())
            window.resize(1280, 800)
            window.show()
            QTest.qWait(100)
            page = dict(window.pages)['Einstellungen']
            index = next(i for i, (name, _) in enumerate(window.pages) if name == 'Einstellungen')
            window.nav_buttons[index].click()
            QTest.qWait(80)
            scroll = window.stack.currentWidget()
            assert page.accent_preview.width() == 38
            assert abs(page.accent_preview.mapTo(page, QPoint()).y()-
                       page.accent_combo.mapTo(page, QPoint()).y()) < 15

            # The full reset belongs to Maintenance inside the final disclosure.
            assert page.content.indexOf(page.advanced) == page.content.count()-1
            scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
            before = scroll.verticalScrollBar().value()
            page.advanced.header.click()
            QTest.qWait(450)
            assert page.advanced.panel.width() == page.advanced.clip.width()
            assert not page.expansion_follower.following
            assert scroll.verticalScrollBar().value() > before
            assert page.advanced.header.mapTo(scroll.viewport(), QPoint()).y() >= -2
            page.interval.setCurrentIndex(page.interval.findData(2))
            QTest.qWait(300)
            assert page.advanced.isAncestorOf(page.restore_reveal)
            assert page._maintenance_card.isAncestorOf(page.restore_reveal)

            # A changed section reverses its reveal cleanly when reset mid-fade.
            page.alert_boxes['cpu_temp'].setValue(97)
            QTest.qWait(100)
            reveal = page._reset_reveals['alerts']
            assert 0 < reveal.progress < 1
            height = reveal.height()
            page.reset_category('alerts')
            assert reveal.height() == height
            QTest.qWait(300)
            assert reveal.isHidden() and not window.restart_requested

            # Return to a category always begins at the top, even after animations.
            window.nav_buttons[1].click()
            cpu_scroll = window.stack.currentWidget()
            cpu_scroll.verticalScrollBar().setValue(cpu_scroll.verticalScrollBar().maximum())
            window.nav_buttons[index].click()
            window.nav_buttons[1].click()
            QTest.qWait(450)
            assert cpu_scroll.verticalScrollBar().value() == 0
            overview = window.pages[0][1]
            assert overview.distro_logo_host.width() == 48
            assert overview.board._render_positions()['hero'][3] == 6
            assert not hasattr(page, 'compact_overview')
            page.reset_category('appearance')
            assert overview.board._render_positions()['hero'][3] == 6

            # The heartbeat changes locally while the authored outer angle stays fixed.
            pulse = window.pulse_core
            pulse._timer.stop()
            pulse._heartbeat_phase = .2
            first = pulse.grab().toImage()
            pulse._heartbeat_phase = .55
            assert pulse.grab().toImage() != first

            # Failed persistence returns to the existing app with a usable reset action.
            before_failure = Path(settings.PATH).read_bytes()
            assert window.restart_for_renderer(commit=lambda: False)
            QTest.qWait(400)
            assert window.isVisible() and not window.restart_requested
            assert Path(settings.PATH).read_bytes() == before_failure
            assert page.restore_reveal.revealed

            # An ongoing diagnostic must block deletion of the preferences file.
            diagnostic = next(page for _, page in window.pages if isinstance(page, DiagnosticCenter))
            worker = SlowRead(diagnostic)
            workers.append(worker)
            diagnostic.worker = worker
            worker.start()
            QTest.qWait(20)
            saved = Path(settings.PATH).read_bytes()
            with patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes), \
                 patch.object(QMessageBox, 'warning') as notice:
                page.restore_defaults()
                assert notice.called
            assert Path(settings.PATH).read_bytes() == saved
            assert not window.restart_requested
            worker.release.set()
            assert worker.wait(1000)
            diagnostic.worker = None

            # Slow read-only workers keep their owner alive; the GUI keeps ticking.
            slow = SlowRead(window)
            workers.append(slow)
            slow.start()
            ticks = []
            timer = QTimer(window)
            timer.setInterval(10)
            timer.timeout.connect(lambda: ticks.append(1))
            timer.start()
            committed = []

            def commit():
                committed.append(1)
                return settings.set_many(PreferencesPage.DEFAULTS)

            assert window.restart_for_renderer(commit=commit)
            QTest.qWait(200)
            assert not committed and window.isVisible() and len(ticks) >= 2
            slow.release.set()
            assert slow.wait(1000)
            QTest.qWait(350)
            assert committed == [1] and window.isHidden() and window.restart_requested
            assert settings.get('theme') == DEFAULT_THEME

            # Real chart readout identifies a missing sensor instead of stale values.
            chart = ChartPanel(['CPU', 'GPU'], [theme.accent(), theme.secondary_accent()])
            chart.resize(500, 300)
            chart.set_timeline([1000.0, 1001.0, 1002.0])
            chart.set_series([([10, None, 20], theme.accent()), ([30, 40, None], theme.secondary_accent())])
            rect = QRectF(10, 14, 420, 240)
            chart.graph._pointer = rect.right()
            lines = chart.graph.hover_readout(rect)
            assert any('CPU' in line and '20%' in line for line in lines)
            assert any('GPU' in line and '–' in line for line in lines)
            assert 'GPU –' in chart.live_labels[1].text()
            assert not chart.grab().isNull()
            assert not sampling_gap((100, 10), (110, 20), 10)
            assert sampling_gap((100, 10), (3700, 11), 1)
            print('v0.9.5.7: disclosure following, reveals, page origin, heartbeat and transactional asynchronous reset PASS')
        finally:
            for worker in workers:
                worker.release.set()
                worker.wait()
            if window is not None and window.isVisible():
                window.quit_from_tray()
                QTest.qWait(350)
            settings.PATH = previous_path
            i18n.set_lang(previous_lang)


if __name__ == '__main__':
    run()
