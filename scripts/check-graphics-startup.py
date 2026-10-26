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
                self.windows.append(dict(title=title,x=x.value,y=y.value,width=width.value,height=height.value))

    def close(self):
        self.lib.XCloseDisplay(self.display)


def child(mode, output):
    from vitalux import renderer, settings, theme, distro, profiles
    os.environ['VITALUX_SPEC_OFFLINE']='1'
    settings.set_many({'render_backend': mode, 'component_images':False, 'theme': 'obsidian_gold',
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
    _hover_guard = hover_hints.install(app)
    theme.set_mode('obsidian_gold')
    theme.set_accent(settings.get('accent', '#4f8cff'))
    app.setStyleSheet(theme.stylesheet())
    info = distro.info()
    win=None
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
            assert win.windowFlags() & __import__('PySide6.QtCore',fromlist=['Qt']).Qt.FramelessWindowHint
            if hasattr(win.centralWidget(), 'finish_background_frame'):win.centralWidget().finish_background_frame()
            image = win.grab().toImage()
            expanded = win.isMaximized() or win.isFullScreen()
            for x,y in ((0,0),(image.width()-1,0),(0,image.height()-1),(image.width()-1,image.height()-1)):
                assert image.pixelColor(x,y).alpha()==(255 if expanded else 0), (mode, 'outer corner',expanded,x,y,image.pixelColor(x,y).getRgb())
            original_size = win.size()
            if not expanded:  # Kiosk compositors force fullscreen permanently.
                win.window_frame.buttons['maximize'].click()
                settled(win.isMaximized)
                QTest.qWait(150)
                win.window_frame.buttons['maximize'].click()
                settled(lambda: not win.isMaximized() and win.size()==original_size)
            controls = [button.geometry() for button in win.window_frame.buttons.values()]
            for collapsed in (True, False):
                win.collapse_button.click()
                assert win._sidebar_motion is not None
                win._sidebar_motion.pause()
                overlay = win._sidebar_overlay
                assert overlay.parentWidget() is win.content_host
                overlay.set_progress(.5)
                moving = win.grab().toImage()
                for x,y in ((0,0),(moving.width()-1,0),(0,moving.height()-1),(moving.width()-1,moving.height()-1)):
                    assert moving.pixelColor(x,y).alpha()==(255 if expanded else 0)
                assert [button.geometry() for button in win.window_frame.buttons.values()]==controls
                win._sidebar_finish()
                assert win._sidebar_collapsed == collapsed
                QTest.qWait(30)
            overview=win.pages[0][1]
            win.window_frame.layout_button.click()
            assert overview.board.editing
            assert overview.layout_actions.parentWidget() is win.window_frame.titlebar
            win.window_frame.layout_button.click()
            assert not overview.board.editing
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
            for key in ('glass','light','crystal_atrium','nebula_prism','quantum_core'):
                preferences.select_design(key)
                assert win._appearance_overlay is not None
                overlay = win._appearance_overlay
                # The target design must already be present in the snapshot,
                # rather than jumping to its GPU texture at the end.
                assert not overlay.after.isNull()
                assert overlay.before.toImage() != overlay.after.toImage()
                if mode in renderer.QUICK_MODES:
                    assert not win.centralWidget()._upload_timer.isActive()
                QTest.qWait(100)
                if key == 'crystal_atrium':
                    settled(lambda: win._appearance_overlay is None)
                    assert win.grab().save(str(output/(mode+'-'+key+'.png')))
                if key == 'quantum_core':
                    settled(lambda: win._appearance_overlay is None)
                    scene = win.centralWidget()
                    phase = scene._phase
                    background = scene.sharp_backdrop().toImage()
                    QTest.qWait(520)
                    assert not scene._wallpaper_timer.isActive() and scene._phase == phase
                    assert background == scene.sharp_backdrop().toImage()
                    assert win.pulse_core._timer.isActive() and win.brand_mark._timer.isActive()
            settled(lambda: win._appearance_overlay is None)
            assert win._appearance_overlay is None
            assert win.sampler is sampler and sampler.isRunning()
            if mode in renderer.QUICK_MODES:
                assert not win.centralWidget().grabFramebuffer().isNull()
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
                  'startup_preloaded': win.last_sample is not None, 'theme_transitions': True, 'retained_design_transitions': True,
                  'quantum_core_static_background': True,
                  'search_interruptions': True,
                  'screen_available': [app.primaryScreen().availableGeometry().x(),app.primaryScreen().availableGeometry().y(),app.primaryScreen().availableGeometry().width(),app.primaryScreen().availableGeometry().height()],
                  'size': [win.width(), win.height()]}), flush=True)
            result[0] = 0
        finally:
            assert win.restart_for_renderer(commit=lambda: profiles.reset_preferences(settings.PATH)), 'Native reset restart was refused'

    from vitalux.startup import StartupController
    class Guard:
        def mark_restarting(self):pass
    def ready(window,manager):
        nonlocal win
        win=window
        assert win.render_backend_active==mode,renderer.warning()
        assert win.last_sample is not None,'Startup showed the main window before first data'
        assert controller.splash.grab().save(str(output/(mode+'-initialization.png')))
        QTimer.singleShot(3000,capture)
    controller=StartupController(app,info,load_logo(info,96),Guard(),ready)
    app.exec()
    from vitalux.lifecycle import dispose_gui
    dispose_gui(controller)
    assert profiles.read(settings.PATH)=={'_schema_version':profiles.SCHEMA},'Native reset did not preserve clean defaults'
    print(f'{mode}/{app.platformName()}: actual profile reset and native GUI disposal PASS',flush=True)
    return result[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child')
    parser.add_argument('--mode', help='Validate one renderer in an isolated compositor session')
    parser.add_argument('--platform',choices=('xcb','wayland'),help='Native QPA override for CPU rendering')
    parser.add_argument('--output', type=Path, default=ROOT/'build/graphics-checks')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.child:
        return child(args.child, output)
    from vitalux import renderer
    results = []
    modes = (args.mode,) if args.mode else renderer.CHOICES
    if args.platform and modes!=(renderer.SOFTWARE,):parser.error('Platform override requires --mode software')
    if any(mode not in renderer.CHOICES for mode in modes):
        parser.error('Unknown renderer')
    for mode in modes:
        with tempfile.TemporaryDirectory(prefix='graphics-profile-') as folder:
            env = os.environ.copy()
            for key, part in (('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                              ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')):
                env[key] = str(Path(folder)/part)
            env['QT_QPA_PLATFORM'] = args.platform or renderer.display_api(mode) or 'xcb'
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
                expected_maps = 0 if env['QT_QPA_PLATFORM'] == 'wayland' else 2
                assert watcher.maps == expected_maps, f'{mode}: {watcher.windows}, expected {expected_maps}'
                result = next(json.loads(line) for line in log.read_text().splitlines()
                              if line.startswith('{"mode"'))
                if expected_maps:
                    splash=watcher.windows[0];x,y,width,height=result['screen_available']
                    assert abs(splash['x']+splash['width']/2-(x+width/2))<=1,watcher.windows
                    assert abs(splash['y']+splash['height']/2-(y+height/2))<=1,watcher.windows
                result['native_x11_maps'] = watcher.maps
                results.append(result)
                print(f'{mode}: real startup screen, preloaded telemetry, framebuffer and no preflight window PASS', flush=True)
            finally:
                watcher.close()
    (output/'results.json').write_text(json.dumps(results, indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
