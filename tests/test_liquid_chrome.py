"""Chrome is a distinct dark design; Silver and user layouts stay preserved."""
import os,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtGui import QColor,QPalette
from PySide6.QtWidgets import QApplication
from vitalux import distro,settings,theme,brand,design_capabilities,liquid_chrome
from vitalux.logo import load_logo
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow

app=QApplication.instance() or QApplication([]);app.setQuitOnLastWindowClosed(False)
def wait(ms):
    deadline=time.monotonic()+ms/1000
    while time.monotonic()<deadline:app.processEvents();time.sleep(.01)

with tempfile.TemporaryDirectory(prefix='vitalux-chrome-') as d,patch.object(settings,'PATH',str(Path(d)/'settings.json')):
    settings.set_many(dict(theme='liquid_chrome',accent='#c65b96',background_style='prism',close_to_tray=False,ui_sounds=False,motion='off'))
    theme.set_mode('liquid_chrome');app.setStyleSheet(theme.stylesheet())
    info=distro.info();manager=UpdateManager();manager._timer.stop()
    win=MainWindow(info,load_logo(info,96),manager);win.resize(1380,1000);win.show();wait(400)
    try:
        assert not theme.is_light() and QColor(theme.BG).lightness()<30
        contrast=(theme._luminance(QColor(theme.TEXT))+.05)/(theme._luminance(QColor(theme.CARD))+.05)
        assert contrast>10,contrast
        assert len(theme.CHOICES)==14 and 'liquid-silver' in brand._PALETTES['variants']
        assert 'liquid-chrome' in brand._brand_asset(True)
        overview=dict(win.pages)['Übersicht'];board=overview.board
        positions=board._render_positions()
        assert positions['cpu'][2]==6 and positions['gpu'][2]==3
        assert all(host.currentIndex()==1 for host in overview.design_metric_hosts.values())
        before=(list(board.order),set(board.hidden),settings.get('dashboard_order'))
        for metric in overview.design_metrics.values():
            metric.set(None,'Unavailable',history=[None,12,None,34]);assert not metric.grab().isNull()
            metric.set(0,'Idle',history=[0,1,0]);assert not metric.grab().isNull()
            metric.set(100,'Full',history=[0,25,100]);assert not metric.grab().isNull()
        page=dict(win.pages)['Einstellungen']
        assert not page.custom_accent_button.isEnabled()
        assert page.custom_accent_button.palette().color(QPalette.Disabled,QPalette.ButtonText).name()=='#9299a3'
        assert page.accent_combo.isLocked() and page.background_combo.isLocked()
        assert not any(design_capabilities.capabilities('liquid_chrome').values())
        win.resize(800,560);wait(150);assert not win.grab().isNull()
        win.resize(1380,1000);wait(150)
        page.select_design('liquid_silver');wait(150)
        assert theme.is_light() and QColor(theme.BG).lightness()>220
        assert all(host.currentIndex()==0 for host in overview.design_metric_hosts.values())
        assert board._render_positions()['cpu'][2]==3
        page.select_design('glass');wait(150)
        assert (list(board.order),set(board.hidden),settings.get('dashboard_order'))==before
        assert settings.get('accent')=='#c65b96' and settings.get('background_style')=='prism'
    finally:
        win.quit_from_tray();wait(400);assert win.isHidden()
print('Dark Chrome identity/contrast, actual-value instruments, asymmetric layout, fixed controls and retained Silver/preferences PASS')
