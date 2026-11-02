"""Tray creation and action wiring; lifecycle behavior remains on the owner."""
from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QSystemTrayIcon,QMenu
from . import settings
from .i18n import tr
from .brand import app_icon,TrayPulse
from .tray_tooltip import tray_tooltip


def setup(window):
    # Create the tray icon even when Plasma's StatusNotifier host comes up
    # after Vitalux. Qt automatically registers a visible icon when a host
    # becomes available. Checking isSystemTrayAvailable() here loses that.
    window._tray = QSystemTrayIcon(app_icon(), window)
    window._tray.setToolTip(tray_tooltip(None))
    window._tray_glow = TrayPulse(window._tray, window)
    window._tray_menu = QMenu(window)
    window._tray_open_action = QAction(tr('Vitalux öffnen'), window._tray_menu)
    window._tray_quit_action = QAction(tr('Beenden'), window._tray_menu)
    window._tray_open_action.triggered.connect(window.show_from_tray)
    window._tray_quit_action.triggered.connect(window.quit_from_tray)
    window._tray_menu.addAction(window._tray_open_action)
    window._tray_hud_action = QAction(tr('Desktop-Overlay anzeigen'), window._tray_menu)
    window._tray_hud_action.setCheckable(True)
    window._tray_hud_action.setChecked(bool(settings.get('mini_hud_enabled', False)))
    window._tray_hud_action.toggled.connect(window.set_mini_hud_enabled)
    window._tray_menu.addAction(window._tray_hud_action)
    window._tray_update_action = QAction('', window._tray_menu)
    window._tray_update_action.setVisible(False)
    window._tray_update_action.triggered.connect(window._open_updates_from_tray)
    window._tray_menu.addAction(window._tray_update_action)
    window._tray_menu.addSeparator()
    window._tray_menu.addAction(window._tray_quit_action)
    window._tray.setContextMenu(window._tray_menu)
    window._tray.activated.connect(window._on_tray_activated)
    # A single click normally produces Trigger. A double click may first
    # produce Trigger, so debounce it to avoid hiding an opened window.
    window._tray_click_timer = QTimer(window)
    window._tray_click_timer.setSingleShot(True)
    window._tray_click_timer.setInterval(190)
    window._tray_click_timer.timeout.connect(window._toggle_tray_window)
    window._tray.show()
