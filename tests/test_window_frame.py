"""Round native clients, operable controls, resize minima and late startup placement."""
import os,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ['VITALUX_SPEC_OFFLINE']='1';os.environ['VITALUX_LOCAL_PREVIEW']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt,QPoint,QPointF,QEvent,QRectF
from PySide6.QtGui import QMouseEvent,QImage,QPainter,QPen,QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from vitalux import settings,theme,distro,i18n
from vitalux.logo import load_logo
from vitalux.window import MainWindow,Sampler
from vitalux.update_manager import UpdateManager
from vitalux.startup import StartupWindow
app=QApplication([]);app.setQuitOnLastWindowClosed(False)
def wait(ms):
 deadline=time.monotonic()+ms/1000
 while time.monotonic()<deadline:app.processEvents();time.sleep(.005)
def corners(window):
 image=window.grab().toImage();w,h=image.width(),image.height()
 return [image.pixelColor(x,y).alpha() for x,y in ((0,0),(w-1,0),(0,h-1),(w-1,h-1))]
with tempfile.TemporaryDirectory() as directory,patch.object(settings,'PATH',str(Path(directory)/'settings.json')),patch.object(Sampler,'start',lambda self:None),patch.object(MainWindow,'_start_background_smart',lambda self:None):
 settings.set_many(dict(motion='off',component_images=False,close_to_tray=False))
 theme.set_mode('obsidian_gold');app.setStyleSheet(theme.stylesheet());info=distro.info()
 window=MainWindow(info,load_logo(info,96),UpdateManager());window.resize(1100,780);window.show();wait(80)
 try:
  assert window.windowFlags() & Qt.FramelessWindowHint
  frame=window.window_frame
  for design in [key for key,_ in theme.CHOICES]+['eclipse_crystal','minimal']:
   settings.set_many(dict(theme='obsidian_gold' if design=='minimal' else design,ultra_eco=design=='minimal'))
   window.apply_appearance();wait(60)
   assert corners(window)==[0]*4,(design,corners(window))
   image=window.grab().toImage();assert image.pixelColor(image.width()//2,image.height()//2).alpha()==255
   from vitalux.window_frame import outline
   mask=QImage(image.size(),QImage.Format_ARGB32_Premultiplied);mask.fill(0)
   painter=QPainter(mask);painter.setRenderHint(QPainter.Antialiasing)
   painter.fillPath(outline(window.rect()),QColor('white'));painter.setPen(QPen(QColor('white'),1))
   painter.drawPath(outline(QRectF(window.rect()).adjusted(-.5,-.5,.5,.5)));painter.end()
   for x in range(27):
    for y in range(27):
     for px,py in ((x,y),(image.width()-1-x,y),(x,image.height()-1-y),(image.width()-1-x,image.height()-1-y)):
      assert image.pixelColor(px,py).alpha()==mask.pixelColor(px,py).alpha(),(design,px,py,image.pixelColor(px,py).alpha(),mask.pixelColor(px,py).alpha())
   assert len([h for h in frame.handles if not h.isHidden()])==8
   for button in frame.buttons.values():
    rect=button.rect().translated(button.mapTo(window,QPoint()))
    assert window.rect().contains(rect)
    assert not any(rect.intersects(handle.geometry()) for handle in frame.handles),(design,rect)
   window.statusBar().showMessage('Fixture status');wait(10)
   assert window.statusBar().currentMessage()=='Fixture status' and not window.statusBar().isHidden()
   assert corners(window)==[0]*4
   window.statusBar().clearMessage();wait(10)
   assert window.statusBar().isHidden()
  settings.set_many(dict(theme='obsidian_gold',ultra_eco=False));window.apply_appearance();wait(20)
  initial=window.size()
  frame.buttons['maximize'].click();wait(40)
  assert window.isMaximized() and corners(window)==[255]*4
  assert all(handle.isHidden() for handle in frame.handles)
  frame.buttons['maximize'].click();wait(40)
  assert not window.isMaximized() and window.size()==initial and corners(window)==[0]*4
  QTest.mouseDClick(frame.titlebar,Qt.LeftButton,pos=QPoint(100,18));wait(30);assert window.isMaximized()
  QTest.mouseDClick(frame.titlebar,Qt.LeftButton,pos=QPoint(100,18));wait(30);assert not window.isMaximized()
  frame.buttons['minimize'].click();wait(20);assert window.isMinimized()
  window.showNormal();wait(20)
  # Offscreen's native operation is unavailable; verify its geometric fallback.
  handle=frame.handles[-1];old=window.geometry();point=handle.mapToGlobal(QPoint(3,3))
  QTest.mousePress(handle,Qt.LeftButton,pos=QPoint(3,3))
  event=QMouseEvent(QEvent.MouseMove,QPointF(43,28),QPointF(point+QPoint(40,25)),Qt.NoButton,Qt.LeftButton,Qt.NoModifier)
  QApplication.sendEvent(handle,event);QTest.mouseRelease(handle,Qt.LeftButton,pos=QPoint(3,3));wait(10)
  assert window.width()==old.width()+40 and window.height()==old.height()+25
  window.set_language('en');assert frame.buttons['close'].accessibleName()=='Close window'
  window.set_language('de');assert frame.buttons['close'].accessibleName()=='Fenster schließen'
  frame.buttons['close'].click();wait(20);assert window.isHidden()
  splash=StartupWindow();splash.show();wait(20)
  assert splash.windowType()==Qt.Dialog
  splash.move(10,10);wait(220)
  assert (splash.frameGeometry().center()-splash.screen().availableGeometry().center()).manhattanLength()<=2
  assert corners(splash)==[0]*4
  splash.ready=True;splash.close();wait(20)
  assert not splash._placement_timer.isActive()
 finally:
  window.close();wait(50)
print('Eight rounded designs, controls/resize/restore, status placement, DE/EN and post-map startup recentering PASS')
