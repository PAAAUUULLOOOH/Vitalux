#!/usr/bin/env python3
"""Repeated real UI interactions, bounded memory growth and hidden-logo idle."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['VITALUX_LOCAL_PREVIEW'] = '1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cycles', type=int, default=180)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='vitalux-endurance-') as folder:
        for name, part in (('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                           ('XDG_CACHE_HOME', 'cache'), ('XDG_DATA_HOME', 'data')):
            os.environ[name] = str(Path(folder)/part)
        import psutil
        from PySide6.QtCore import QObject
        from PySide6.QtWidgets import QApplication
        from vitalux import distro, settings, theme
        from vitalux.logo import load_logo
        from vitalux.update_manager import UpdateManager
        from vitalux.window import MainWindow
        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
        def wait(milliseconds):
            deadline=time.monotonic()+milliseconds/1000
            while time.monotonic()<deadline:
                app.processEvents()
                time.sleep(min(.012,max(0,deadline-time.monotonic())))
        settings.set_many({'theme': 'obsidian_gold', 'close_to_tray': False})
        theme.set_mode('obsidian_gold')
        app.setStyleSheet(theme.stylesheet())
        info = distro.info()
        window = MainWindow(info, load_logo(info, 96), UpdateManager())
        window.show()
        process = psutil.Process()
        started = time.monotonic()
        page_index = next(i for i, (name, _) in enumerate(window.pages) if name == 'Einstellungen')
        page = window.pages[page_index][1]
        keys = [key for key, _ in theme.CHOICES]
        try:
            wait(2500)
            window.nav_buttons[page_index].click()
            for key in keys:
                page.select_design(key)
                wait(550)
            wait(500)
            before = process.memory_info().rss
            objects = len(window.findChildren(QObject))
            sampler = window.sampler
            for cycle in range(args.cycles):
                key = keys[cycle % len(keys)]
                page.select_design(key)
                if cycle % 9 == 0:
                    page.search_overlay.open_search()
                    page.search.setText('render')
                elif cycle % 9 == 2:
                    page.search_overlay.close_search()
                if cycle % 17 == 0:
                    window.nav_buttons[0].click()
                    wait(30)
                    window.nav_buttons[page_index].click()
                wait(70 if cycle % 11 == 0 else 550)
                if cycle % 30 == 29:
                    print(f'Completed {cycle+1} theme/search/navigation cycles', flush=True)
            page.select_design('obsidian_gold')
            wait(800)
            window.hide()
            wait(400)
            assert not window.pulse_core._timer.isActive()
            assert not window.brand_mark._timer.isActive()
            assert sampler.isRunning()
            window.show()
            window.nav_buttons[0].click()
            wait(30000)
            assert window.pulse_core._timer.isActive()
            assert window.sampler is sampler and sampler.isRunning()
            assert window.last_sample is not None and len(window.hist['cpu']) > 20
            after = process.memory_info().rss
            remaining = len(window.findChildren(QObject))
            assert after-before < 96*1024*1024, (before, after)
            assert remaining-objects < 200, (objects, remaining)
            result = {'cycles': args.cycles, 'seconds': round(time.monotonic()-started, 1),
                      'rss_before': before, 'rss_after': after,
                      'qt_objects_before': objects, 'qt_objects_after': remaining,
                      'samples': len(window.hist['cpu']), 'hidden_animations_paused': True}
            (output/'results.json').write_text(json.dumps(result, indent=2)+'\n')
            window.grab().save(str(output/'after-endurance.png'))
            print(json.dumps(result), flush=True)
        finally:
            window.quit_from_tray()
            for _ in range(600):
                if window.isHidden():
                    break
                wait(25)
            assert window.isHidden()


if __name__ == '__main__':
    main()
