"""Original vector shine, palette-aware identity and intentional click feedback."""
import os
from pathlib import Path
import struct
import sys
import tempfile
import wave
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton, QSlider, QWidget
from vitalux import settings, theme
from vitalux.brand import Wordmark, _pixmap, themed_icon_pixmap, wordmark_pixmap
from vitalux.ui_sound import SOUND, _volume_pcm, install


def run():
    app = QApplication.instance() or QApplication([])
    previous = settings.PATH
    with tempfile.TemporaryDirectory() as folder:
        settings.PATH = str(Path(folder)/'settings.json')
        settings.set_many({'theme': 'obsidian_gold', 'motion': 'smooth', 'ui_sounds': True})
        theme.set_mode('obsidian_gold')
        theme.set_accent('#4f8cff')
        mark = Wordmark()
        mark.show()
        app.processEvents()
        assert mark._timer.isActive()
        for key in theme.FIXED_MODES:
            theme.set_mode(key)
            mark.sync_theme()
            assert wordmark_pixmap(200, 42).toImage() == _pixmap(
                'brand/vitalux-wordmark-gold.svg', 200, 42, 2).toImage()
        mark._phase = .15
        reflected = mark.grab().toImage()
        mark._phase = .75
        resting = mark.grab().toImage()
        assert reflected != resting, 'No visible reflection over original letters'
        settings.set('motion', 'off')
        mark.sync_theme()
        assert not mark._timer.isActive()
        settings.set('motion', 'smooth')
        mark.sync_theme()
        mark.hide()
        assert not mark._timer.isActive()
        mark.close()

        # Changed preferences must not briefly show their reset button as an
        # independent native window before the settings layout is attached.
        from vitalux.control import PreferencesPage
        class VisibilityGuard(QObject):
            shown = []
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Show and isinstance(obj, QWidget) and obj.isWindow():
                    self.shown.append(obj.objectName())
                return False
        visibility = VisibilityGuard(app)
        app.installEventFilter(visibility)
        host = QWidget()
        host._tray = None
        page = PreferencesPage(host)
        app.processEvents()
        app.removeEventFilter(visibility)
        assert not visibility.shown, 'A preferences child was shown as a top-level window'
        assert not page.restore_button.isWindow()
        page.close()
        host.close()

        theme.set_mode('glass')
        images = []
        for color in ('#d13d8f', '#14b8a6', '#aaaaaa'):
            settings.set('accent', color)
            theme.set_accent(color)
            images.append((themed_icon_pixmap(96).toImage(), wordmark_pixmap().toImage()))
        assert images[0][0] != images[1][0] and images[0][1] != images[1][1]

        guard = install(app)
        button = QPushButton('Click')
        button.show()
        app.processEvents()
        with patch.object(guard, 'play') as play:
            QTest.mouseClick(button, Qt.LeftButton)
            assert play.call_count == 1
            QTest.keyClick(button, Qt.Key_Space)
            assert play.call_count == 2
            button.setEnabled(False)
            QTest.mouseClick(button, Qt.LeftButton)
            assert play.call_count == 2
            for other in (QWidget(), QLineEdit(), QSlider(Qt.Horizontal)):
                other.show()
                app.processEvents()
                QTest.mouseClick(other, Qt.LeftButton)
                assert play.call_count == 2, 'A non-button produced click feedback'
                other.close()
        # Turning sound off must not start an audio thread.
        settings.set('ui_sounds', False)
        guard.play()
        assert guard._worker is None
        button.close()
        with wave.open(str(SOUND)) as source:
            assert source.getnchannels() == 1 and source.getsampwidth() == 2
            assert .16 <= source.getnframes()/source.getframerate() <= .19
            pcm = source.readframes(source.getnframes())
        samples = struct.unpack('<'+'h'*(len(pcm)//2), pcm)
        assert samples[0] == samples[-1] == 0
        assert 1000 < max(abs(x) for x in samples) < 12000
        muted = struct.unpack('<'+'h'*len(samples), _volume_pcm(pcm, 0))
        half = struct.unpack('<'+'h'*len(samples), _volume_pcm(pcm, 50))
        assert not any(muted)
        assert abs(max(abs(x) for x in half)*2-max(abs(x) for x in samples)) <= 1
    settings.PATH = previous
    print('Original wordmark, clipped shine, custom palettes, click routing and glass PCM PASS')


if __name__ == '__main__':
    run()
