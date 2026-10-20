#!/usr/bin/env python3
"""Capture the actual Vitalux UI, optionally check fractional-scale layouts."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def export_heartbeat(widget, output):
    """Store untouched native Qt frames in an animated PNG container."""
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice
    from PySide6.QtTest import QTest
    frames = []
    for _ in range(36):
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.WriteOnly)
        assert widget.grab().save(buffer, 'PNG')
        raw, chunks, offset = bytes(data), [], 8
        while offset < len(raw):
            length = struct.unpack('>I', raw[offset:offset+4])[0]
            chunks.append((raw[offset+4:offset+8], raw[offset+8:offset+8+length]))
            offset += length+12
        frames.append(chunks)
        QTest.qWait(65)
    def chunk(kind, payload):
        return struct.pack('>I', len(payload))+kind+payload+struct.pack('>I', zlib.crc32(kind+payload))
    header = next(data for kind, data in frames[0] if kind == b'IHDR')
    width, height = struct.unpack('>II', header[:8])
    result = b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', header)+chunk(b'acTL', struct.pack('>II', len(frames), 0))
    sequence = 0
    for index, frame in enumerate(frames):
        result += chunk(b'fcTL', struct.pack('>IIIIIHHBB', sequence, width, height, 0, 0, 65, 1000, 0, 0))
        sequence += 1
        for kind, data in frame:
            if kind != b'IDAT':
                continue
            if index == 0:
                result += chunk(b'IDAT', data)
            else:
                result += chunk(b'fdAT', struct.pack('>I', sequence)+data)
                sequence += 1
    output.write_bytes(result+chunk(b'IEND', b''))


def capture(output, language, checks, warmup):
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    from vitalux import distro, i18n, settings, theme
    from vitalux.logo import load_logo
    from vitalux.update_manager import UpdateManager
    from vitalux.window import MainWindow
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    i18n.set_lang(language)
    settings.set_many({'theme': 'obsidian_gold', 'close_to_tray': False,
                       'first_start_guide_seen': True, 'ui_sounds': False})
    theme.set_mode('obsidian_gold')
    app.setStyleSheet(theme.stylesheet())
    info = distro.info()
    window = MainWindow(info, load_logo(info, 96), UpdateManager())
    window.resize(1380, 1000)
    window.show()
    try:
        remaining = max(2600, round(warmup*1000))
        while remaining:
            step = min(5000, remaining)
            QTest.qWait(step)
            remaining -= step
        assert window.last_sample is not None
        assert window.grab().save(str(output/'overview.png'))
        if not checks:
            export_heartbeat(window.pulse_core, output/'logo-heartbeat.png')
        index = next(i for i, (name, _) in enumerate(window.pages) if name == 'Einstellungen')
        page = window.pages[index][1]
        window.nav_buttons[index].click()
        QTest.qWait(180)
        assert window.grab().save(str(output/'appearance.png'))
        scroll = window.stack.currentWidget()
        page.interval.setCurrentIndex(page.interval.findData(2))
        QTest.qWait(280)
        scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
        page.advanced.header.click()
        QTest.qWait(500)
        assert window.grab().save(str(output/'advanced-settings.png'))
        assert page.advanced.header.mapTo(scroll.viewport(), QPoint()).y() >= 0
        scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
        QTest.qWait(30)
        assert window.grab().save(str(output/'advanced-settings.png'))
        page.select_design('glass')
        QTest.qWait(500)
        page.accent_combo.setCurrentIndex(page.accent_combo.findData('#52d3ff'))
        QTest.qWait(500)
        destination = page.accent_combo.mapTo(page, QPoint()).y()-100
        scroll.verticalScrollBar().setValue(destination)
        assert window.grab().save(str(output/'accent-color.png'))
        results = {'scale': window.devicePixelRatioF(), 'native_capture': True, 'language': language}
        if checks:
            window.resize(800, 560)
            QTest.qWait(500)
            assert page.width() <= scroll.viewport().width()+2, (page.width(), scroll.viewport().width())
            for control in (page.accent_combo, page.accent_preview, page.render_combo,
                            page.clear_cache_btn, page.clear_preferences_btn):
                assert control.mapTo(page, QPoint(control.width(), 0)).x() <= page.width()
            from PySide6.QtWidgets import QLabel
            for item in page.advanced.panel.findChildren(QLabel):
                if item.wordWrap():
                    assert item.height() >= item.heightForWidth(item.width()), item.text()
            pixmap = window.grab()
            assert abs(pixmap.width()-window.width()*window.devicePixelRatioF()) <= 2
            assert pixmap.save(str(output/'compact-window.png'))
            results['compact_layout'] = True
        (output/'results.json').write_text(json.dumps(results, indent=2)+'\n')
        print(json.dumps(results), flush=True)
    finally:
        window.quit_from_tray()
        for _ in range(600):
            if window.isHidden():
                break
            QTest.qWait(25)
        assert window.isHidden(), 'Capture did not shut down cleanly'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--language', choices=('de', 'en'), default='en')
    parser.add_argument('--scales', help='Comma-separated Qt scale factors')
    parser.add_argument('--child', action='store_true')
    parser.add_argument('--checks', action='store_true')
    parser.add_argument('--warmup-seconds', type=float, default=2.6)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.child:
        capture(output, args.language, args.checks, args.warmup_seconds)
        return
    scales = args.scales.split(',') if args.scales else ['1']
    for scale in scales:
        destination = output/('scale-'+scale) if args.scales else output
        destination.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='vitalux-capture-') as folder:
            env = os.environ.copy()
            env['QT_QPA_PLATFORM'] = 'offscreen'
            env['QT_SCALE_FACTOR'] = scale
            env['VITALUX_LOCAL_PREVIEW'] = '1'
            for name, part in (('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                               ('XDG_CACHE_HOME', 'cache'), ('XDG_DATA_HOME', 'data'),
                               ('XDG_RUNTIME_DIR', 'runtime')):
                target = Path(folder)/part
                target.mkdir(mode=0o700)
                env[name] = str(target)
            command = [sys.executable, __file__, '--child', '--output', str(destination),
                       '--language', args.language, '--warmup-seconds', str(args.warmup_seconds)]
            if args.scales or args.checks:
                command.append('--checks')
            result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    timeout=max(90, args.warmup_seconds+60))
            (destination/'capture.log').write_text(result.stdout)
            print(result.stdout, end='', flush=True)
            if result.returncode and os.environ.get('GITHUB_ACTIONS') == 'true':
                detail = result.stdout[-10000:].replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
                print(f'::error title=UI scale {scale}::{detail}', flush=True)
            result.check_returncode()


if __name__ == '__main__':
    main()
