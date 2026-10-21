"""Distinct light material, contrast, branding, navigation and motion controls."""
import os,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor,QPalette
from PySide6.QtWidgets import QApplication
from vitalux import distro,settings,theme,brand,design_capabilities
from vitalux.logo import load_logo
from vitalux.window import MainWindow
from vitalux.update_manager import UpdateManager

app=QApplication.instance() or QApplication([])
def wait(milliseconds):
    deadline=time.monotonic()+milliseconds/1000
    while time.monotonic()<deadline:app.processEvents();time.sleep(.01)

with tempfile.TemporaryDirectory(prefix='vitalux-silver-') as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    settings.set_many(dict(theme='liquid_silver',accent='#f472b6',background_style='prism',close_to_tray=False,ui_sounds=False,motion='smooth'))
    theme.set_mode('liquid_silver');app.setStyleSheet(theme.stylesheet())
    info=distro.info();m=UpdateManager();m._timer.stop();win=MainWindow(info,load_logo(info,96),m)
    win.resize(1380,1000);win.show();wait(350)
    try:
        assert theme.is_light() and QColor(theme.BG).lightness()>220
        contrast=(theme._luminance(QColor(theme.CARD))+.05)/(theme._luminance(QColor(theme.TEXT))+.05)
        assert contrast>=7,contrast
        assert not design_capabilities.capabilities('liquid_silver')['custom_accent']
        assert 'liquid-silver-light' in brand._brand_asset(False)
        assert b'#4b6378' in brand._themed_svg(True),'Light lens lost its contrasting heartbeat'
        assert win.sidebar.width()==218 and win.pulse_core.width()==108
        page=dict(win.pages)['Einstellungen'];button=page.custom_accent_button
        assert not button.isEnabled()
        assert button.palette().color(QPalette.Disabled,QPalette.ButtonText).name()=='#717983'
        assert page.background_combo.isLocked() and page.accent_combo.isLocked()
        win.nav_buttons[1].click();assert win._page_overlay is not None
        deadline=time.monotonic()+2
        while win._page_overlay is not None and time.monotonic()<deadline:wait(20)
        assert win._page_overlay is None
        settings.set('motion','off');win.nav_buttons[2].click();assert win._page_overlay is None
        assert not win.grab().isNull()
        settings.set('theme','glass');win.apply_appearance();wait(350)
        assert win.sidebar.width()==250 and settings.get('accent')=='#f472b6'
        assert settings.get('background_style')=='prism'
    finally:
        win.quit_from_tray();wait(300);assert win.isHidden()
print('Liquid Silver contrast, authored identity, fixed capabilities, floating rail, transitions and preserved preferences PASS')
