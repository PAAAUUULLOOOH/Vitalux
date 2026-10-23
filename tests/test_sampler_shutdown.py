"""Idle wake-up and safe window lifetime during slow sensor shutdown."""
import os
from pathlib import Path
import sys
import tempfile
from threading import Event
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())
from PySide6.QtGui import QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from vitalux import settings
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow, Sampler


def run():
    _app = QApplication.instance() or QApplication([])
    sampled = Event()
    with patch('vitalux.window.sensors.collect', side_effect=lambda: sampled.set() or {}):
        worker = Sampler()
        worker.interval = 10
        worker.start()
        try:
            assert sampled.wait(2)
            worker.stop()
            assert worker.wait(300), 'Eco sleep did not wake for shutdown'
        finally:
            worker.stop()
            worker.wait()

    previous = settings.PATH
    entered, release = Event(), Event()
    window = None
    with tempfile.TemporaryDirectory() as folder:
        settings.PATH = str(Path(folder)/'settings.json')
        settings.set_many({'close_to_tray': False, 'render_backend': 'software'})
        try:
            with patch.object(Sampler, 'start'):
                window = MainWindow({'name': 'Linux', 'short': 'Test', 'version': '1',
                                     'color': '#4f8cff'}, QPixmap(96, 96), UpdateManager())
            window.show()

            def slow_read():
                entered.set()
                release.wait(5)
                return {}

            with patch('vitalux.window.sensors.collect', side_effect=slow_read):
                window.sampler.start()
                assert entered.wait(2)
                # The GUI must never wait on the slow worker.
                with patch.object(window.sampler, 'wait', side_effect=AssertionError('GUI blocked on worker')):
                    window.quit_from_tray()
                    assert window._force_quit, 'Pending exit lost its explicit quit intent'
                    assert window.restart_for_renderer()
                    assert window.restart_requested, 'Pending close lost the renderer restart'
                assert window.isVisible(), 'Window closed over a running sensor thread'
                assert window.sampler.isRunning() and window._close_retry.isActive()
                release.set()
                assert window.sampler.wait(1000)
                QTest.qWait(200)
                assert window.isHidden() and not window._close_retry.isActive()
        finally:
            release.set()
            if window is not None:
                window.sampler.stop()
                window.sampler.wait()
                window.quit_from_tray()
            settings.PATH = previous
    print('Sampler shutdown: immediate Eco wake and retained owner for slow reads PASS')


if __name__ == '__main__':
    run()
