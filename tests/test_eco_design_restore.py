"""Real MainWindow returns from Ultra Eco to the last design and saved choices."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ['VITALUX_LOCAL_PREVIEW']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication
from vitalux import eco,settings,theme
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow,Sampler

app=QApplication.instance() or QApplication([])
app.setQuitOnLastWindowClosed(False)

def create_window():
    theme.set_mode(eco.theme_name());app.setStyleSheet(theme.stylesheet())
    logo=QPixmap(96,96);logo.fill()
    window=MainWindow(dict(name='Test Linux',short='Test',version='1',color='#4f8cff'),logo,UpdateManager())
    window.show();app.processEvents()
    return window,dict(window.pages)['Einstellungen']

def close(window):
    window._force_quit=True;window.close();app.processEvents();window.deleteLater()
    QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()

with tempfile.TemporaryDirectory() as directory,patch.object(settings,'PATH',str(Path(directory)/'settings.json')),\
     patch.object(Sampler,'start',lambda self:None),patch.object(MainWindow,'_start_background_smart',lambda self:None):
    personal=dict(accent='#f472b6',background_style='animated_sparkle',custom_background_selected='',
                  custom_background_fit='contain',interval=2,motion='off',render_backend='software')
    settings.set_many(dict(personal,theme='obsidian_gold',ultra_eco=False,close_to_tray=False))
    window,pref=create_window()
    try:
        pages=[page for _,page in window.pages]
        for mode,_ in theme.CHOICES:
            pref.select_design(mode);app.processEvents()
            assert theme.mode()==mode
            remembered=settings.get_many(personal)
            pref.eco_toggle.click();app.processEvents()
            assert eco.enabled() and theme.mode()=='minimal' and settings.get('theme')==mode
            assert window.sampler.interval==10
            pref.eco_toggle.click();app.processEvents()
            assert not eco.enabled() and theme.mode()==mode and window.design_shell.mode==mode
            assert window.sampler.interval==2
            assert [page for _,page in window.pages]==pages,'Eco must retain the running pages'
            assert all(settings.get(key)==value for key,value in remembered.items()),mode
        pref.select_design('nebula_prism');remembered=settings.get_many(personal);pref.eco_toggle.click();app.processEvents()
        assert settings.get('theme')=='nebula_prism' and eco.enabled()
    finally:
        close(window)
    window,pref=create_window()
    try:
        assert theme.mode()=='minimal' and settings.get('theme')=='nebula_prism'
        pref.eco_toggle.click();app.processEvents()
        assert theme.mode()=='nebula_prism' and window.design_shell.mode=='nebula_prism'
        assert window.design_shell.dock_row.isVisible() and window.sidebar.isHidden()
        assert all(settings.get(key)==value for key,value in remembered.items())
    finally:
        close(window)
print('Actual Ultra Eco switches restore all 13 designs, personal settings and the saved design after window recreation PASS')
