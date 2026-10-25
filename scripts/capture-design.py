#!/usr/bin/env python3
"""Capture a real, live Vitalux window using one local glass collection."""
import argparse
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('design', choices=('obsidian_gold', 'nebula_prism', 'quantum_core', 'crystal_atrium','crystal_glass'))
    parser.add_argument('output', type=Path)
    parser.add_argument('--settings', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='vitalux-design-capture-') as directory:
        for var, name in (('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                          ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')):
            os.environ[var] = str(Path(directory)/name)
        os.environ['VITALUX_LOCAL_PREVIEW'] = '1'
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
        from vitalux import distro, i18n, sensors, settings, theme
        from vitalux.logo import load_logo
        from vitalux.update_manager import UpdateManager
        from vitalux.window import MainWindow
        settings.set_many({'theme': args.design, 'motion': 'smooth', 'lang': 'de',
                           'background_style': 'theme_default', 'close_to_tray': False})
        theme.set_mode(args.design)
        i18n.set_lang('de')
        app = QApplication([])
        app.setStyleSheet(theme.stylesheet())
        app.setQuitOnLastWindowClosed(False)
        info = distro.info()
        sensors.prime()
        manager = UpdateManager()
        window = MainWindow(info, load_logo(info, 96), manager)
        window.resize(1560, 1040)
        window.show()
        if args.settings:
            window.stack.setCurrentIndex(9)
            window.nav_buttons[9].setChecked(True)
        outcome = [1]

        def capture():
            try:
                app.processEvents()
                args.output.parent.mkdir(parents=True, exist_ok=True)
                image = window.grab()
                assert not image.isNull() and image.save(str(args.output), 'PNG')
                assert window.last_sample is not None, 'Live sensor sample missing'
                print(f'{args.design}: real Qt window captured ({image.width()}x{image.height()})', flush=True)
                outcome[0] = 0
            finally:
                window.quit_from_tray()

        QTimer.singleShot(3500, capture)
        app.exec()
        return outcome[0]


if __name__ == '__main__':
    raise SystemExit(main())
