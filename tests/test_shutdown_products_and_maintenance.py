"""Default profiles hide maintenance; reset waits for optional product work."""
import os,sys,tempfile,time
from pathlib import Path
from threading import Event
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ['VITALUX_SPEC_OFFLINE']='1';os.environ['VITALUX_LOCAL_PREVIEW']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication
from vitalux import settings,theme,product_ui
from vitalux.control import PreferencesPage
from vitalux.window import MainWindow,Sampler
from vitalux.update_manager import UpdateManager
app=QApplication.instance() or QApplication([]);app.setQuitOnLastWindowClosed(False)
with tempfile.TemporaryDirectory() as directory,patch.object(settings,'PATH',str(Path(directory)/'settings.json')),patch.object(Sampler,'start',lambda self:None):
 settings.set_many(PreferencesPage.DEFAULTS)
 theme.set_mode('obsidian_gold');app.setStyleSheet(theme.stylesheet())
 original_refresh=PreferencesPage._refresh_restore_button
 def owned_refresh(page):
  assert page._maintenance_card.parentWidget() is not None,'Maintenance mapped as a standalone window during startup'
  original_refresh(page)
 with patch.object(PreferencesPage,'_refresh_restore_button',owned_refresh):
  window=MainWindow(dict(name='Test Linux',short='Test',version='1',color='#4f8cff'),QPixmap(96,96),UpdateManager())
 page=dict(window.pages)['Einstellungen'];window.show();app.processEvents()
 page._refresh_restore_button();assert page._maintenance_card.isHidden()
 page._set_preference('interval',5);app.processEvents();assert not page._maintenance_card.isHidden()
 assert page.restore_reveal.revealed
 page._set_preference('interval',1);app.processEvents();assert page._maintenance_card.isHidden()
 entered,release=Event(),Event();commits=[]
 def slow(*args,**kwargs):entered.set();release.wait(8);return None
 worker=product_ui.loader()
 with patch.object(product_ui,'resolve',slow):
  worker.request(dict(kind='cpu',vendor='Intel',model='Core i5-14600KF',exact=True))
  assert entered.wait(2)
  try:
   assert window.restart_for_renderer(commit=lambda:commits.append('reset') or True)
   assert not commits and window._close_retry.isActive(),'Reset deleted caches while image work was running'
   assert worker.cancelled.is_set()
  finally:release.set()
  deadline=time.monotonic()+5
  while not commits and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
  assert commits==['reset'] and worker.pool.activeThreadCount()==0
  assert window.isHidden() and not window._close_retry.isActive()
print('Fresh/reset maintenance visibility and nonblocking reset waiting for product-thread completion PASS')
