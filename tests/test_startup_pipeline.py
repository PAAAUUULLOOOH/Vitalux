"""Actual startup controller: GUI-thread construction, first data and static Eco mode."""
import os,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ['VITALUX_SPEC_OFFLINE']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QThread
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication
from vitalux import startup,settings,theme
from vitalux.window import Sampler,MainWindow
ns={'__file__':str(Path(__file__).with_name('test_component_charts.py'))}
source=Path(ns['__file__']).read_text();exec(source[:source.index('with tempfile.TemporaryDirectory()')],ns)
app=ns['app'];app.setQuitOnLastWindowClosed(False);sample=ns['sample'];sample['disks'][0]['fstype']='ext4'
class Guard:
 def mark_restarting(self):pass
with tempfile.TemporaryDirectory() as directory,patch.object(settings,'PATH',str(Path(directory)/'settings.json')),patch.object(Sampler,'start',lambda self:None),patch.object(MainWindow,'_start_background_smart',lambda self:None):
 for case in ('normal','failed','eco','animated'):
  settings.set_many(dict(theme='obsidian_gold',motion='smooth' if case=='animated' else 'off',ultra_eco=case=='eco',component_images=False,close_to_tray=False,guide_intro_choice='completed'))
  theme.set_mode('minimal' if case=='eco' else 'obsidian_gold');app.setStyleSheet(theme.stylesheet())
  threads=[];windows=[]
  def prepare(worker):
   threads.append(QThread.currentThread()!=app.thread())
   worker.stage.emit('Sensorwerte einlesen …')
   if case=='failed':worker.failed.emit('test failure')
   else:worker.prepared.emit(dict(sample=sample,images={},specs={}))
  def ready(window,manager):
   assert QThread.currentThread()==app.thread();windows.append(window);manager._timer.stop()
  with patch.object(startup.StartupWorker,'run',prepare):
   controller=startup.StartupController(app,dict(name='Test Linux',short='Test',version='1',color='#4f8cff'),QPixmap(96,96),Guard(),ready)
   deadline=time.monotonic()+12
   while not windows and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
   assert windows,case
   assert threads==[True] and controller.splash.ready
   assert controller.splash.testAttribute(__import__('PySide6.QtCore',fromlist=['Qt']).Qt.WA_TranslucentBackground)
   if case!='animated':assert not controller.splash.activity.timer.isActive()
   else:assert not controller.splash.logo.grab().isNull()
   win=windows[0];assert win.isVisible()
   if case!='failed':
    assert win.last_sample and dict(win.pages)['Prozessor'].name.text()=='CPU'
    assert dict(win.pages)['Grafik'].cards[0].name.text()=='GPU'
    assert win.pages[0][1].g_cpu.box.gauge.value==15
   else:assert win.statusBar().currentMessage()
   controller.worker.wait(2000);win._force_quit=True;win.close();app.processEvents()
   win.manager.shutdown();controller.splash.close()
print('Startup worker, GUI-only construction, all-page first-sample preload, failure completion and static Eco/off display PASS')
