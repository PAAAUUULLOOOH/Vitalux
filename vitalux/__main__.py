from . import DEFAULT_THEME
import os
import sys

from . import profiles
profiles.initialize()

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import APP_NAME, distro, i18n, sensors, settings, theme, diagnostics, hover_hints
from .logo import load_logo
from .brand import app_icon
from .wallpaper_accents import resolve_accent
from . import renderer, eco
from .update_manager import UpdateManager


def main():
    sys.excepthook = diagnostics.exception_hook
    diagnostics.enable_native_crash_trace()
    from .window import MainWindow
    # Select the scene-graph backend before the first Quick window exists.
    renderer.prepare_start()
    app = QApplication(sys.argv)
    # Disable transient hover help across the entire application, not just navigation.
    app._vitalux_hover_guard = hover_hints.install(app)
    from .ui_sound import install as install_ui_sound
    install_ui_sound(app)
    # Hiding the final window must not kill the tray icon and sampler.
    # MainWindow.closeEvent explicitly quits on a genuine Exit command.
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(APP_NAME+'-Unstable' if profiles.installed()=='unstable' else APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    # Desktop-portal app IDs require an installed .desktop entry; avoid asking
    # the portal to register an unknown ID when using Vitalux portably.
    xdg_data = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    if os.path.isfile(os.path.join(xdg_data, "applications", "vitalux.desktop")):
        app.setDesktopFileName("vitalux")
    lang = settings.get("lang") or ("de" if os.environ.get("LANG", "").lower().startswith("de") else "en")
    i18n.set_lang(lang)
    info = distro.info()
    requested_theme = settings.get('theme', DEFAULT_THEME)
    theme.set_mode('minimal' if eco.enabled() else requested_theme)
    if not eco.enabled() and requested_theme != theme.mode():
        settings.set('theme', theme.mode())  # Migrate removed/unknown themes to Obsidian Gold.
    user_accent = settings.get('accent', '#4f8cff')
    from . import wallpaper_accents
    effective_accent = wallpaper_accents.effective_selection(user_accent)
    if effective_accent != user_accent:
        settings.set('accent', effective_accent)
    theme.set_accent('#4f8cff' if eco.enabled() else resolve_accent(effective_accent, info['color']))
    app.setStyleSheet(theme.stylesheet())
    logo = load_logo(info, 96)
    app.setWindowIcon(app_icon())
    from .brand import sync_installed_icon
    sync_installed_icon()
    sensors.prime()
    manager = UpdateManager()
    win = MainWindow(info, logo, manager)
    if os.environ.get('VITALUX_LOCAL_PREVIEW') == '1':
        win.setWindowTitle('Vitalux · Design Preview · ' + theme.mode().replace('_', ' ').title())
    print(f"Vitalux: Fensterplattform={app.platformName()}, "
          f"Grafik-Backend={win.render_backend_active}, "
          f"Fenstergröße={win.width()}x{win.height()} logisch", flush=True)
    # Resolve the final widget/layout size before the first native map on X11.
    win.ensurePolished()
    win.centralWidget().ensurePolished()
    win.layout().activate()
    win.show()
    # A native driver crash while initializing any GPU backend leaves a marker;
    # next launch automatically selects the known-working CPU renderer.
    QTimer.singleShot(4500, renderer.successful_start)
    if renderer.warning():
        QTimer.singleShot(0, lambda: win.statusBar().showMessage(renderer.warning(), 16000))
    QTimer.singleShot(0, manager.check)
    # The guide is mandatory on first launch; afterwards it stays available under Info.
    from .guide import offer_first_start_guide
    QTimer.singleShot(1800, lambda: offer_first_start_guide(win))
    result = app.exec()
    if result == 0 and win.restart_requested:
        renderer.successful_start()
        sys.exit(42)  # The portable launcher restarts with the new renderer.
    sys.exit(result)


if __name__ == "__main__":
    main()
