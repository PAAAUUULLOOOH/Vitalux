"""Real scrollbar drag targets, logo hover/context restore and HUD tray lifecycle."""
import os,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ['VITALUX_SPEC_OFFLINE']='1';os.environ['VITALUX_LOCAL_PREVIEW']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint,Qt,QTimer
from PySide6.QtWidgets import QApplication,QStyle,QStyleOptionSlider,QSystemTrayIcon
from PySide6.QtTest import QTest
from vitalux import settings,theme,distro
from vitalux.logo import load_logo
from vitalux.window import MainWindow,Sampler
from vitalux.game_service import GameService
from vitalux.update_manager import UpdateManager
app=QApplication([]);app.setQuitOnLastWindowClosed(False)
def wait(ms=50):
    end=time.monotonic()+ms/1000
    while time.monotonic()<end:app.processEvents();time.sleep(.003)
def point(widget,p):return widget.mapTo(window,p)
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',folder+'/settings.json'),\
        patch.object(Sampler,'start',lambda self:None),patch.object(GameService,'start',lambda self:None),\
        patch.object(MainWindow,'_start_background_smart',lambda self:None):
    settings.set_many(dict(theme='glass',motion='off',component_images=False,close_to_tray=False))
    theme.set_mode('glass');app.setStyleSheet(theme.stylesheet())
    info=distro.info();window=MainWindow(info,load_logo(info,96),UpdateManager())
    window.resize(1200,760);window.show();wait()
    try:
        page=window.pages[0][1]
        for mode,_ in theme.CHOICES:
            print('Checking controls:',mode,flush=True)
            settings.set('theme',mode);window.apply_appearance();window._switch_page(9);wait()
            scroll=window.stack.currentWidget();bar=scroll.verticalScrollBar()
            assert bar.isVisible() and bar.maximum()>0,mode
            bar.setValue(0);wait()
            option=QStyleOptionSlider();bar.initStyleOption(option)
            thumb=bar.style().subControlRect(QStyle.CC_ScrollBar,option,QStyle.SC_ScrollBarSlider,bar)
            for x in (2,bar.width()-3):
                hit=bar.mapToGlobal(QPoint(x,thumb.center().y()))
                actual=window.childAt(window.mapFromGlobal(hit))
                assert actual is bar,(mode,'thumb intercepted',actual)
            header=window.design_shell.header
            if not header.isHidden():assert point(bar,QPoint()).y()>=point(header,QPoint(0,header.height())).y(),mode
            if mode=='eclipse_crystal':
                footer=window.design_shell.footer
                assert point(bar,QPoint(0,bar.height())).y()<=point(footer,QPoint()).y(),mode
            QTest.mousePress(bar,Qt.LeftButton,pos=thumb.center())
            QTest.mouseMove(bar,thumb.center()+QPoint(0,90),delay=5)
            QTest.mouseRelease(bar,Qt.LeftButton,pos=thumb.center()+QPoint(0,90))
            assert bar.value()>0,(mode,'drag failed')
            window._switch_page(0);wait()
            if os.environ.get('VITALUX_CONTROL_EVIDENCE'):
                folder=Path(os.environ['VITALUX_CONTROL_EVIDENCE']);folder.mkdir(parents=True,exist_ok=True)
                window.grab().save(str(folder/(mode+'.png')))
            QTest.mouseMove(page.distro_logo_host,page.distro_logo_host.rect().center());wait()
            assert page.distro_logo_remove.isVisible(),mode
            QTest.mouseClick(page.distro_logo_remove,Qt.LeftButton);wait()
            assert not page.distro_logo_host.isVisible() and not settings.get('dashboard_distro_logo_visible'),mode
            # Exercise the actual popup and its restore action.
            def choose():
                menu=app.activePopupWidget()
                if menu is not None:
                    menu.actions()[0].trigger();menu.close()
            QTimer.singleShot(0,choose)
            page._distro_logo_menu(QPoint(10,10))
            assert page.distro_logo_host.isVisible() and settings.get('dashboard_distro_logo_visible'),mode
        with patch.object(QSystemTrayIcon,'isSystemTrayAvailable',return_value=False):
            window.set_mini_hud_enabled(True)
            assert window.isVisible() and window._mini_hud.isVisible()
            assert window._hud_tray_timer.isActive()
        with patch.object(QSystemTrayIcon,'isSystemTrayAvailable',return_value=True):
            window._hide_main_for_hud();wait()
            assert not window.isVisible() and window._mini_hud.isVisible()
            window.show_from_tray();wait(60)
            assert window.isVisible() and window._mini_hud.isVisible()
            assert not window._hud_tray_timer.isActive()
            window.set_mini_hud_enabled(False)
            window.set_mini_hud_enabled(True);wait()
            assert not window.isVisible()
            window._mini_hud.hide_by_user();wait()
            assert window.isVisible() and not settings.get('mini_hud_enabled')
    finally:
        window._force_quit=True;window.close();wait(100)
    # An enabled overlay is restored at startup and the first main-window show
    # goes to tray; explicit subsequent restores remain visible.
    settings.set('mini_hud_enabled',True)
    with patch.object(QSystemTrayIcon,'isSystemTrayAvailable',return_value=True):
        restarted=MainWindow(info,load_logo(info,96),UpdateManager())
        try:
            restarted.show();wait()
            assert restarted._mini_hud.isVisible() and not restarted.isVisible()
            restarted.show_from_tray();wait()
            assert restarted.isVisible() and restarted._mini_hud.isVisible()
        finally:
            restarted._force_quit=True;restarted.close();wait(100)
print('All-design native scrollbar hit/drag, logo hover/context persistence and safe HUD tray lifecycle PASS')
