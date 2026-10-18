"""Opt-in OpenGL renderer selection with startup recovery.

This is deliberately an experiment: Qt raster widgets continue to paint on
the CPU. The OpenGL background and Qt's final top-level composition use a
GL context when the platform can provide one.
"""
import os
import subprocess
import sys

from . import settings

SOFTWARE = 'software'
OPENGL = 'opengl'
QTQUICK = 'qtquick'
_failure = ''


def desired():
    forced = os.environ.get('VITALUX_RENDERER', '').strip().lower()
    if forced in (SOFTWARE, OPENGL, QTQUICK):
        return forced
    saved = settings.get('render_backend', SOFTWARE)
    return saved if saved in (SOFTWARE, OPENGL, QTQUICK) else SOFTWARE


def prepare_start():
    """Recover from a crash during a previous GPU-mode startup.

    This boot marker is cleared shortly after the GUI starts successfully.
    The environment override always permits an emergency CPU-only launch.
    """
    global _failure
    if os.environ.get('VITALUX_RENDERER', '').strip().lower() == SOFTWARE:
        return SOFTWARE
    selected = desired()
    if selected not in (OPENGL, QTQUICK):
        return SOFTWARE
    if selected == QTQUICK:
        # Initialize Qt Quick's scene graph with the GPU RHI rather than the
        # explicit software backend. Qt/driver may still use Mesa llvmpipe.
        os.environ.setdefault('QSG_RHI_BACKEND', 'opengl')
    if settings.get('gpu_boot_pending', False):
        _failure = 'Der vorherige GPU-Start wurde nicht abgeschlossen. CPU-Rendering wurde zur Sicherheit wieder aktiviert.'
        settings.set('render_backend', SOFTWARE)
        settings.set('gpu_boot_pending', False)
        return SOFTWARE
    settings.set('gpu_boot_pending', True)
    return selected


def successful_start():
    if settings.get('gpu_boot_pending', False):
        settings.set('gpu_boot_pending', False)


def gpu_available():
    """Probe an actual offscreen GL context before selecting QOpenGLWidget."""
    if os.environ.get('QT_QPA_PLATFORM', '').lower() in ('offscreen', 'minimal'):
        return False
    try:
        from PySide6.QtOpenGLWidgets import QOpenGLWidget  # noqa: F401
        from PySide6.QtGui import QOffscreenSurface, QOpenGLContext
        surface = QOffscreenSurface()
        surface.create()
        if not surface.isValid():
            return False
        context = QOpenGLContext()
        if not context.create() or not context.makeCurrent(surface):
            return False
        context.doneCurrent()
        return True
    except (ImportError, RuntimeError, OSError):
        return False


def quick_available():
    """Keep Qt Quick/GL initialization in a child process that may safely abort.

    Native SIGABRT (exit code 134) cannot be caught as a Python exception.
    """
    global _failure
    if os.environ.get('QT_QPA_PLATFORM', '').lower() in ('offscreen', 'minimal'):
        _failure = 'Qt Quick: keine grafische Sitzung verfügbar; CPU-Rendering aktiviert.'
        return False
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'vitalux.quick_probe'],
            capture_output=True, check=False, timeout=9,
            env={**os.environ, 'QSG_RHI_BACKEND': 'opengl'})
    except subprocess.TimeoutExpired:
        _failure = 'Qt Quick: Grafik-Starttest hat nicht reagiert; CPU-Rendering aktiviert.'
        return False
    except OSError:
        _failure = 'Qt Quick: Grafik-Starttest nicht verfügbar; CPU-Rendering aktiviert.'
        return False
    if result.returncode == 0:
        return True
    _failure = (f'Qt Quick: Grafik-Starttest fehlgeschlagen '
                f'(Code {result.returncode}); CPU-Rendering aktiviert.')
    return False


def fallback():
    global _failure
    if not _failure:
        _failure = 'Die gewählte GPU-Grafikausgabe ist hier nicht verfügbar. CPU-Rendering bleibt aktiv.'
    if os.environ.get('VITALUX_RENDERER', '').strip().lower() not in (OPENGL, QTQUICK):
        settings.set('render_backend', SOFTWARE)
    successful_start()


def warning():
    return _failure
