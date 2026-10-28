"""Fixed header search, direct interrupted fades and a genuinely transparent dock."""
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ['VITALUX_SPEC_OFFLINE']='1';os.environ['VITALUX_LOCAL_PREVIEW']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint,QRect,QTimer
from PySide6.QtWidgets import QApplication,QWidget
from vitalux import settings,theme,distro
from vitalux.game_service import GameService
from vitalux.logo import load_logo
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow,Sampler

app=QApplication([]);app.setQuitOnLastWindowClosed(False)
def wait(ms=40):
    end=time.monotonic()+ms/1000
    while time.monotonic()<end:app.processEvents();time.sleep(.003)
def bounds(widget):return QRect(widget.mapTo(window,QPoint()),widget.size())

with tempfile.TemporaryDirectory() as temporary,patch.object(settings,'PATH',temporary+'/settings.json'),\
        patch.object(Sampler,'start',lambda self:None),patch.object(GameService,'start',lambda self:None),\
        patch.object(MainWindow,'_start_background_smart',lambda self:None):
    settings.set_many(dict(theme='obsidian_gold',motion='off',component_images=False,close_to_tray=False))
    theme.set_mode('obsidian_gold');app.setStyleSheet(theme.stylesheet())
    info=distro.info();window=MainWindow(info,load_logo(info,96),UpdateManager());window.show()
    expected=os.environ.get('VITALUX_RENDERER')
    if expected:assert window.render_backend_active==expected,(expected,window.render_backend_active)
    try:
        page=window.pages[9][1]
        for design in [key for key,_ in theme.CHOICES]+['eclipse_crystal','minimal']:
            settings.set_many(dict(theme='obsidian_gold' if design=='minimal' else design,ultra_eco=design=='minimal'))
            window.apply_appearance();window.nav_buttons[9].click();wait()
            for width in (1400,800):
                window.resize(width,700);wait()
                search=page.search_overlay;search.open_search();wait()
                anchor=window.design_shell.bar if not window.design_shell.header.isHidden() else window.window_frame.titlebar
                assert abs(bounds(search.icon).center().y()-bounds(anchor).center().y())<=1,(design,width)
                assert abs(bounds(search).center().x()-window.rect().center().x())<=1,(design,width)
                assert search.field.height()==window.window_frame.buttons['minimize'].height()
                assert bounds(search.field).contains(bounds(search.icon))
                assert not bounds(search).intersects(bounds(window.window_frame.buttons['minimize']))
                old=bounds(search)
                scroll=window.stack.currentWidget();scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum());wait()
                assert bounds(search)==old,'Header search moved with the page'
                search.close_search();wait()
                assert search.icon.isVisible() and search.field.isHidden()
                assert search.width()==search.icon.width()
            if design in ('obsidian_gold','glass'):
                settings.set('motion','smooth')
                contour=window.grab().toImage().copy(80,0,270,1)
                window.toggle_sidebar();animation=window._sidebar_motion
                assert animation is not None;animation.pause()
                for progress in (0.,.25,.5,.75,1.):
                    window._sidebar_overlay.set_progress(progress)
                    assert window.grab().toImage().copy(80,0,270,1)==contour,'Top contour changed during sidebar motion'
                window._sidebar_finish();settings.set('motion','off')
            if design=='nebula_prism':
                shell=window.design_shell
                assert bounds(window.stack.currentWidget().viewport()).bottom()>=window.height()-4
                assert 14<=window.height()-bounds(shell.dock_row).bottom()<=18
                # A real sibling card underneath must show through the dock.
                card=QWidget(window.content_host);card.setObjectName('dockUnderlayProbe')
                position=window.content_host.mapFromGlobal(shell.dock.mapToGlobal(QPoint()))
                card.setGeometry(QRect(position,shell.dock.size()));card.show();shell.dock_row.raise_()
                samples=[]
                for color in ('#d04040','#40d040'):
                    card.setStyleSheet('QWidget#dockUnderlayProbe {background:'+color+';}');wait()
                    image=window.grab().toImage();ratio=image.devicePixelRatio()
                    point=shell.dock.mapTo(window,QPoint(7,shell.dock.height()//2))
                    samples.append(image.pixelColor(round(point.x()*ratio),round(point.y()*ratio)))
                assert samples[0]!=samples[1],'Dock painted an opaque wallpaper instead of live cards'
                card.hide();card.deleteLater()

        settings.set_many(dict(ultra_eco=False,motion='smooth'));page.select_design('obsidian_gold');wait(400)
        # Distinct saved backgrounds expose the old-theme/new-wallpaper flash.
        settings.set('background_style','quantum_core');window.apply_appearance();wait(400)
        for timer in window.findChildren(QTimer):timer.stop()
        source=window.grab().toImage();page.select_design('glass')
        transition=window._appearance_overlay;assert transition is not None
        transition.animation.pause()
        assert transition.before.toImage()==source,'Source was repainted after changing wallpaper settings'
        for progress in (.25,.5,.75,1.):
            transition._frame(progress)
            composed=window.grab().toImage()
            first=transition.before.toImage();last=transition.after.toImage()
            for fx in (.1,.5,.9):
                for fy in (.2,.5,.8):
                    x=round(composed.width()*fx);y=round(composed.height()*fy)
                    a,b,c=first.pixelColor(x,y),last.pixelColor(x,y),composed.pixelColor(x,y)
                    if min(a.alpha(),b.alpha())<255:continue
                    for channel in ('red','green','blue'):
                        expected=getattr(a,channel)()*(1-progress)+getattr(b,channel)()*progress
                        assert abs(getattr(c,channel)()-expected)<=2,('Appearance brightness jumped',progress,channel)
        transition._frame(.4);wait(10)
        visible=window.grab().toImage();page.select_design('crystal_atrium')
        current=window._appearance_overlay;assert current is not transition
        current.animation.pause()
        assert current.before.toImage()==visible,'Interrupted fade jumped to an endpoint'
        current.finish();current.finish();wait()
        assert window._appearance_overlay is None
        settings.set('motion','off');page.select_design('light')
        assert window._appearance_overlay is None
    finally:
        window._force_quit=True;window.close();wait(100)
print('All-design fixed header search, live translucent dock, exact source frames and interrupted fades PASS')
