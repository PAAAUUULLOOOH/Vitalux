#!/usr/bin/env python3
"""Record a complete, seamless branding cycle from the actual native widgets."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def capture(output, theme_name):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QImage, QPainter, QPalette
    from PySide6.QtWidgets import QApplication
    from vitalux import settings, theme
    from vitalux.brand import PulseCore, Wordmark, _MOTION
    settings.set_many({'theme': theme_name, 'motion': 'smooth', 'ui_sounds': False})
    theme.set_mode(theme_name)
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(theme.stylesheet())
    logo, mark = PulseCore(720), Wordmark()
    mark.setFixedSize(680, 168)
    for widget in (logo, mark):
        palette = widget.palette()
        palette.setColor(QPalette.Window, QColor('#101114'))
        widget.setPalette(palette)
        widget.setAutoFillBackground(True)
        widget.show()
    app.processEvents()
    logo.sync_theme()
    mark.sync_theme()
    logo._timer.stop()
    mark._timer.stop()
    duration, fps = float(_MOTION['complete_cycle']), 25

    def frame(seconds):
        seconds = round(seconds % duration, 8)
        logo._phase = seconds*360/_MOTION['outer_rotation']
        logo._heartbeat_phase = (seconds/_MOTION['heartbeat']) % 1
        mark._phase = (seconds/_MOTION['wordmark_glint']) % 1
        image = QImage(800, 960, QImage.Format_RGBA8888)
        image.fill(QColor('#101114'))
        p = QPainter(image)
        p.drawPixmap(40, 20, logo.grab())
        p.drawPixmap(60, 770, mark.grab())
        p.end()
        return image

    try:
        assert frame(0) == frame(duration)
        assert frame(.04) == frame(duration+.04)
        assert frame(-.04) == frame(duration-.04)
        assert frame(.8).save(str(output/'branding.png'))
        command = ['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-y',
                   '-f', 'rawvideo', '-pix_fmt', 'rgba', '-video_size', '800x960',
                   '-framerate', str(fps), '-i', 'pipe:0', '-an', '-c:v', 'libx264',
                   '-preset', 'fast', '-crf', '18', '-threads', '2', '-pix_fmt', 'yuv420p',
                   '-movflags', '+faststart', str(output/'branding.mp4'),
                   '-an', '-vf', 'scale=400:480:flags=lanczos',
                   '-c:v', 'libwebp_anim', '-lossless', '1', '-compression_level', '6',
                   '-loop', '0', str(output/'branding.webp')]
        started = time.monotonic()
        with (output/'encode.log').open('wb') as log:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log, stderr=log)
            try:
                for i in range(round(fps*duration)):
                    image = frame(i/fps)
                    process.stdin.write(image.constBits())
                    if i % (fps*12) == 0:
                        print(f'Captured {i//fps}/{duration:g} seconds from native branding widgets', flush=True)
                process.stdin.close()
                assert process.wait(timeout=60) == 0
            except BaseException:
                process.kill()
                process.wait()
                raise
        (output/'results.json').write_text(json.dumps(dict(
            native_widgets=True, theme=theme_name, frames=round(fps*duration), fps=fps,
            duration_seconds=duration, full_cycle=True, identical_cycle_states=True,
            render_seconds=round(time.monotonic()-started, 2),
        ), indent=2)+'\n')
    finally:
        logo.close()
        mark.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--theme', default='obsidian_gold')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    with tempfile.TemporaryDirectory(prefix='vitalux-brand-capture-') as folder:
        for key, name in (('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache'),
                          ('XDG_STATE_HOME', 'state'), ('XDG_DATA_HOME', 'data'),
                          ('XDG_RUNTIME_DIR', 'runtime')):
            path = Path(folder)/name
            path.mkdir(mode=0o700)
            os.environ[key] = str(path)
        capture(output, args.theme)


if __name__ == '__main__':
    main()
