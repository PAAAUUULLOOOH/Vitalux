"""Renderer selection and confirmed resets wait for busy work then restart once."""
import os,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QWidget
from vitalux import renderer,settings,theme
from vitalux.control import PreferencesPage
app=QApplication([])
class Host(QWidget):
    _tray=True;render_backend_active=renderer.SOFTWARE
    def __init__(self):super().__init__();self.busy=True;self.accepted=0;self._shutdown_pending=False
    def restart_for_renderer(self,commit=None):
        if self.busy:return False
        if commit is not None:assert commit()
        self.accepted+=1;return True
    def apply_appearance(self,**kwargs):pass
    def set_interval(self,value):pass
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    host=Host();page=PreferencesPage(host)
    page.render_combo.setCurrentIndex(page.render_combo.findData(renderer.X11_OPENGL));app.processEvents()
    assert host.accepted==0 and page._renderer_restart_timer.isActive()
    host.busy=False
    end=time.monotonic()+2
    while host.accepted<1 and time.monotonic()<end:app.processEvents();time.sleep(.01)
    assert host.accepted==1 and not page._renderer_restart_timer.isActive()
    commits=[];host.busy=True
    page._restart_after_reset(lambda:commits.append('reset') or True)
    app.processEvents();assert not commits and page._renderer_restart_timer.isActive()
    host.busy=False
    end=time.monotonic()+2
    while not commits and time.monotonic()<end:app.processEvents();time.sleep(.01)
    assert commits==['reset'] and host.accepted==2
    host.busy=True;page._restart_after_reset(lambda:commits.append('unexpected') or True)
    host._shutdown_pending=True;page._try_auto_restart()
    assert commits==['reset'] and not page._renderer_restart_timer.isActive()
    page.close();host.close()
print('Automatic renderer/reset restart, busy-operation retry, one commit and intentional-exit cancellation PASS')
