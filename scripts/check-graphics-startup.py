#!/usr/bin/env python3
"""Validate all five renderers in real X11 and Wayland test sessions.

Requires DISPLAY and WAYLAND_DISPLAY (e.g. Xvfb and headless Weston).
Mesa software GL/Vulkan is sufficient; this does not benchmark a physical GPU.
"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class XMaps:
    """Watch actual native map events, including the isolated GPU preflight."""
    def __init__(self):
        self.lib = ctypes.CDLL('libX11.so.6')
        self.lib.XOpenDisplay.restype = ctypes.c_void_p
        self.lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.display = self.lib.XOpenDisplay(None)
        if not self.display:
            raise RuntimeError('DISPLAY is not reachable')
        self.lib.XDefaultRootWindow.restype = ctypes.c_ulong
        self.lib.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        self.lib.XSelectInput.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_long]
        self.lib.XPending.argtypes = [ctypes.c_void_p]
        self.lib.XNextEvent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self.lib.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.lib.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.lib.XGetGeometry.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
        self.lib.XFetchName.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_void_p)]
        self.lib.XFree.argtypes = [ctypes.c_void_p]
        self._ignore_error = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(lambda *_: 0)
        self.lib.XSetErrorHandler(self._ignore_error)
        self.lib.XSelectInput(self.display, self.lib.XDefaultRootWindow(self.display), 1 << 19)
        self.lib.XSync(self.display, 0)
        self.maps = 0
        self.windows = []

    def poll(self):
        while self.lib.XPending(self.display):
            event = (ctypes.c_long*24)()
            self.lib.XNextEvent(self.display, ctypes.byref(event))
            if ctypes.cast(event, ctypes.POINTER(ctypes.c_int))[0] == 19:
                self.maps += 1  # X11 MapNotify on a root child
                window = event[5]
                root = ctypes.c_ulong()
                x, y = ctypes.c_int(), ctypes.c_int()
                width, height, border, depth = (ctypes.c_uint() for _ in range(4))
                self.lib.XGetGeometry(self.display, window, ctypes.byref(root),
                    ctypes.byref(x), ctypes.byref(y), ctypes.byref(width), ctypes.byref(height),
                    ctypes.byref(border), ctypes.byref(depth))
                name = ctypes.c_void_p()
                self.lib.XFetchName(self.display, window, ctypes.byref(name))
                title = ctypes.string_at(name).decode(errors='replace') if name else ''
                if name: self.lib.XFree(name)
                self.windows.append(dict(title=title, width=width.value, height=height.value))

    def close(self):
        self.lib.XCloseDisplay(self.display)


def child(mode, output):
    from vitalux import renderer, settings, theme, distro
    settings.set_many({'render_backend': mode, 'theme': 'obsidian_gold',
                       'first_start_guide_seen': True, 'close_to_tray': False})
    if renderer.prepare_start() != mode:
        raise RuntimeError(renderer.warning())
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from vitalux.logo import load_logo
    from vitalux.update_manager import UpdateManager
    from vitalux.window import MainWindow
    app = QApplication([])
    from vitalux import hover_hints
    guard = hover_hints.install(app)
    theme.set_mode('obsidian_gold')
    theme.set_accent(theme.default_accent())
    app.setStyleSheet(theme.stylesheet())
    info = distro.info()
    win = MainWindow(info, load_logo(info, 96), UpdateManager())
    assert win.render_backend_active == mode, renderer.warning()
    win.ensurePolished()
    win.layout().activate()
    win.show()
    result = [1]

    def capture():
        try:
            from PySide6.QtTest import QTest
            def settled(condition):
                deadline = time.monotonic()+2
                while not condition() and time.monotonic() < deadline:
                    QTest.qWait(20)
                assert condition(), 'Native animation did not settle within two seconds'
            assert win.width() >= 800 and win.height() >= 560
            assert win.last_sample is not None
            scene = win.centralWidget()
            if mode in renderer.QUICK_MODES:
                assert not scene.grabFramebuffer().isNull()
                api = scene.quickWindow().rendererInterface().graphicsApi().name
                assert ('Vulkan' if mode == renderer.WAYLAND_VULKAN else 'OpenGL') in api
            elif mode == renderer.OPENGL:
                assert scene.context().isValid()
                assert not scene.grabFramebuffer().isNull()
            assert win.grab().save(str(output/(mode+'.png')))
            preferences = dict(win.pages)['Einstellungen']
            index = next(i for i, (name, _) in enumerate(win.pages) if name == 'Einstellungen')
            win.stack.setCurrentIndex(index)
            QTest.qWait(100)
            sampler = win.sampler
            for key in ('black_glass_gold', 'dark', 'obsidian_gold', 'aether_glass'):
                preferences.select_design(key)
                preferences.select_background('liquid_silver')
                preferences.change_accent('#b9ccdc')
                assert win._appearance_overlay is not None
                overlay = win._appearance_overlay
                # A static design must already be present in the target
                # snapshot, rather than jumping to its GPU texture at the end.
                target = overlay.after.toImage()
                if mode in renderer.QUICK_MODES:
                    assert not win.centralWidget()._upload_timer.isActive()
                QTest.qWait(100)
                if key == 'obsidian_gold':
                    settled(lambda: win._appearance_overlay is None)
                    assert win.grab().save(str(output/(mode+'-'+key+'.png')))
            settled(lambda: win._appearance_overlay is None)
            assert win._appearance_overlay is None
            assert win.sampler is sampler and sampler.isRunning()
            search = preferences.search_overlay
            search.open_search()
            settled(lambda: search.expanded and search._opacity.opacity() == 1)
            search.field.setText('render')
            QTest.qWait(300)
            search.close_search()
            search.animation.setCurrentTime(search.animation.duration()//2)
            assert search.isVisible() and 0 < search._opacity.opacity() < 1
            search.open_search()
            settled(lambda: search.expanded and search._opacity.opacity() == 1)
            assert search.expanded and search._opacity.opacity() == 1
            assert win.grab().save(str(output/(mode+'-settings.png')))
            search.close_search()
            settled(search.isHidden)
            assert search.isHidden()
            renderer.successful_start()
            print(json.dumps({'mode': mode, 'active': win.render_backend_active,
                  'platform': app.platformName(), 'live_sample': True,
                  'theme_transitions': True, 'shared_background_transitions': True,
                  'search_interruptions': True,
                  'size': [win.width(), win.height()]}), flush=True)
            result[0] = 0
        finally:
            win.quit_from_tray()

    QTimer.singleShot(3000, capture)
    app.exec()
    return result[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child')
    parser.add_argument('--mode', help='Validate one renderer in an isolated compositor session')
    parser.add_argument('--output', type=Path, default=ROOT/'build/graphics-checks')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.child:
        return child(args.child, output)
    from vitalux import renderer
    results = []
    modes = (args.mode,) if args.mode else renderer.CHOICES
    if any(mode not in renderer.CHOICES for mode in modes):
        parser.error('Unknown renderer')
    for mode in modes:
        with tempfile.TemporaryDirectory(prefix='graphics-profile-') as folder:
            env = os.environ.copy()
            for key, part in (('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                              ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')):
                env[key] = str(Path(folder)/part)
            env['QT_QPA_PLATFORM'] = renderer.display_api(mode) or 'xcb'
            env['VITALUX_RENDERER'] = mode
            env['VITALUX_LOCAL_PREVIEW'] = '1'
            watcher = XMaps()
            log = output/(mode+'.log')
            try:
                with log.open('w') as stream:
                    process = subprocess.Popen([sys.executable, __file__, '--child', mode,
                        '--output', str(output)], cwd=ROOT, env=env,
                        stdout=stream, stderr=subprocess.STDOUT)
                    deadline = time.monotonic()+40
                    while process.poll() is None:
                        watcher.poll()
                        if time.monotonic() > deadline:
                            process.kill()
                            process.wait()
                            raise RuntimeError(mode+': timeout')
                        time.sleep(.005)
                watcher.poll()
                assert process.returncode == 0, log.read_text()
                expected_maps = 0 if renderer.display_api(mode) == 'wayland' else 1
                assert watcher.maps == expected_maps, f'{mode}: {watcher.windows}, expected {expected_maps}'
                result = next(json.loads(line) for line in log.read_text().splitlines()
                              if line.startswith('{"mode"'))
                result['native_x11_maps'] = watcher.maps
                results.append(result)
                print(f'{mode}: real framebuffer, live telemetry, no preflight window PASS', flush=True)
            finally:
                watcher.close()
    (output/'results.json').write_text(json.dumps(results, indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
