"""Original vector shine, palette-aware identity and intentional click feedback."""
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())
from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication, QWidget
from vitalux import settings, theme
from vitalux.brand import Wordmark, _pixmap, themed_icon_pixmap, wordmark_pixmap


def run():
    app = QApplication.instance() or QApplication([])
    previous = settings.PATH
    with tempfile.TemporaryDirectory() as folder:
        settings.PATH = str(Path(folder)/'settings.json')
        settings.set_many({'theme': 'obsidian_gold', 'motion': 'smooth'})
        theme.set_mode('obsidian_gold')
        theme.set_accent('#4f8cff')
        mark = Wordmark()
        mark.show()
        app.processEvents()
        assert mark._timer.isActive()
        fixed_words = set()
        for key in theme.FIXED_MODES:
            theme.set_mode(key)
            mark.sync_theme()
            suffix = '-light' if theme.is_light() else ''
            assert wordmark_pixmap(200, 42).toImage() == _pixmap(
                f"brand/vitalux-wordmark-{key.replace('_', '-')}{suffix}.svg", 200, 42, 2).toImage()
            fixed_words.add(bytes(wordmark_pixmap(200, 42).toImage().constBits()))
        assert len(fixed_words) == len(theme.FIXED_MODES), 'Gold themes share a wordmark palette'
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

    settings.PATH = previous
    print('Original wordmark, clipped shine, custom palettes and no audio dependencies PASS')


if __name__ == '__main__':
    run()
