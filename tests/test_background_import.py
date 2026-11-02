"""A real image copy remains cancellable and does not block the Qt event loop."""
import os,sys,tempfile,threading,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QThread,QTimer
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication,QWidget
from vitalux import settings,user_background,theme
from vitalux.control import PreferencesPage
from vitalux.ui_locale import QFileDialog
app=QApplication.instance() or QApplication([])
class Host(QWidget):
    render_backend_active='software';_tray=object()
    def apply_appearance(self,*,before=None):pass
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    original=user_background.import_image
    picture=QImage(64,64,QImage.Format_RGB32);picture.fill(0xff145678)
    path=Path(folder)/'source.png';assert picture.save(str(path))
    entered=threading.Event();release=threading.Event();ticks=[]
    def slow(name,**options):
        assert QThread.currentThread()!=app.thread()
        entered.set();release.wait(2)
        return original(name,**options)
    host=Host();page=PreferencesPage(host)
    heartbeat=QTimer();heartbeat.setInterval(15);heartbeat.timeout.connect(lambda:ticks.append(1));heartbeat.start()
    with patch.object(QFileDialog,'getOpenFileNames',return_value=([str(path)],'')),patch.object(user_background,'import_image',side_effect=slow):
        page.add_background_image()
        QTimer.singleShot(120,release.set)
        deadline=time.monotonic()+3
        while time.monotonic()<deadline and not settings.get('custom_backgrounds'):
            app.processEvents();time.sleep(.005)
    heartbeat.stop()
    assert entered.is_set() and len(ticks)>=3
    copied=user_background.images();assert len(copied)==1
    assert user_background.image_path(copied[0]['file']).read_bytes()==path.read_bytes()
    assert page.shutdown() and path.exists()
    page.close();host.close()
print('Image import off the GUI thread, responsive event loop, exact copied bytes and safe shutdown PASS')
