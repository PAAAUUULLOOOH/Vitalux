"""CPU rendering and the optional X11/OpenGL scene, with safe startup fallback.
"""
import os
import subprocess
import sys

from . import settings, eco

SOFTWARE = 'software'
X11_OPENGL = 'x11_opengl'
CHOICES = (SOFTWARE, X11_OPENGL)
QUICK_MODES = (X11_OPENGL,)
GPU_MODES = QUICK_MODES
DESCRIPTIONS = {
    SOFTWARE: 'CPU · Standard (stabil)',
    X11_OPENGL: 'X11 · OpenGL',
}
_failure = ''
_preflight_ok = False
_saved_environment = {}


def desired():
    if eco.enabled():return SOFTWARE
    forced=os.environ.get('VITALUX_RENDERER','').strip().lower()
    if forced:return forced if forced in CHOICES else SOFTWARE
    saved=settings.get('render_backend',SOFTWARE)
    if saved not in CHOICES:
        settings.set_many({'render_backend':SOFTWARE,'gpu_boot_pending':False})
        return SOFTWARE
    return saved


def graphics_api(mode=None):
    return 'opengl'


def display_api(mode=None):
    return 'xcb' if (mode or desired())==X11_OPENGL else None


def _set_environment(mode):
    """Apply QPA and RHI *before* QApplication; remember prior overrides."""
    global _saved_environment
    _saved_environment = {key: os.environ.get(key)
                          for key in ('QT_QPA_PLATFORM', 'QSG_RHI_BACKEND')}
    display = display_api(mode)
    if display is not None:
        os.environ['QT_QPA_PLATFORM'] = display
    if mode in QUICK_MODES:
        os.environ['QSG_RHI_BACKEND'] = graphics_api(mode)


def _restore_environment():
    global _saved_environment
    for key, previous in _saved_environment.items():
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous
    _saved_environment = {}


def _probe(mode, timeout=12):
    """The test may SIGABRT inside a Qt display/OpenGL driver: never run in UI."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'vitalux.quick_probe'],
            capture_output=True, check=False, timeout=timeout,
            env=os.environ.copy())
    except subprocess.TimeoutExpired:
        return False, 'Zeitüberschreitung beim Grafik-Starttest'
    except OSError as exc:
        return False, str(exc)
    if result.returncode == 0:
        return True, ''
    detail = (result.stderr or result.stdout).decode('utf-8', errors='replace').strip()
    return False, f'Grafik-Starttest fehlgeschlagen (Code {result.returncode}): {detail[-300:]}'


def prepare_start():
    """Validate a requested GPU mode before QApplication and recover crashes.

    A stale pending marker indicates the previous GUI was interrupted before
    initialization finished. We also verify QPA plugin and actual RHI API in
    an isolated child, so platform-plugin aborts cannot kill Vitalux.
    """
    global _failure, _preflight_ok
    _failure = ''
    _preflight_ok = False
    _restore_environment()
    selected = desired()
    if selected == SOFTWARE:
        successful_start()
        return selected
    if settings.get('gpu_boot_pending', False):
        _failure = 'Vorheriger GPU-Start abgebrochen; CPU-Rendering wieder aktiviert.'
        fallback()
        return SOFTWARE
    settings.set('gpu_boot_pending', True)
    if selected == X11_OPENGL and not os.environ.get('DISPLAY'):
        _failure = 'Kein X11-Display erreichbar; CPU-Rendering aktiviert.'
        fallback()
        return SOFTWARE
    _set_environment(selected)
    if selected in QUICK_MODES:
        if os.environ.get('QT_QPA_PLATFORM', '').lower() in ('offscreen', 'minimal'):
            _failure = 'Qt Quick benötigt eine grafische Sitzung; CPU-Rendering aktiviert.'
            fallback()
            return SOFTWARE
        ok, reason = _probe(selected)
        if not ok:
            _failure = f'{DESCRIPTIONS[selected]}: {reason}'
            fallback()
            return SOFTWARE
        _preflight_ok = True
    return selected


def successful_start():
    if settings.get('gpu_boot_pending', False):
        settings.set('gpu_boot_pending', False)


def quick_available():
    """A successful early child probe is reused instead of probing twice."""
    global _failure
    if os.environ.get('QT_QPA_PLATFORM', '').lower() in ('offscreen', 'minimal'):
        _failure = 'Qt Quick benötigt eine grafische Sitzung.'
        return False
    if _preflight_ok:
        return True
    ok, reason = _probe(desired())
    if not ok:
        _failure = reason
    return ok


def fallback():
    """Restore Qt environment and persisted safe mode, avoiding restart loops."""
    global _failure, _preflight_ok
    if not _failure:
        _failure = 'GPU-Grafikausgabe nicht verfügbar; CPU-Rendering aktiviert.'
    print('Vitalux: Grafik-Backend auf CPU zurückgesetzt:', _failure, flush=True)
    from . import events
    events.record('renderer_fallback')
    _preflight_ok = False
    _restore_environment()
    if os.environ.get('VITALUX_RENDERER', '').strip().lower() not in GPU_MODES:
        settings.set('render_backend', SOFTWARE)
    successful_start()


def warning():
    return _failure
