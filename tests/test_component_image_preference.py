"""Global image preference: no new lookups, no stale column, cached reenable."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QBoxLayout
from PySide6.QtGui import QPixmap,QColor
from vitalux import settings,product_ui
from vitalux.widgets import label
app=QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
 path=Path(folder)/'image.png';image=QPixmap(250,150);image.fill(QColor('cyan'));image.save(str(path))
 result=dict(path=str(path));headers=[]
 with patch.object(product_ui.loader(),'request') as request:
  settings.set('component_images',False)
  for kind in ('cpu','gpu','mainboard'):
   header=product_ui.ProductHeader(label('Detected model'),label('Manufacturer'),kind)
   header.set_product(dict(kind=kind,model='Exact model',vendor='Vendor',exact=True))
   header.resize(700,210);header.show();headers.append(header)
   app.processEvents();header._ready(header.key,result);app.processEvents()
   assert header.picture.isHidden() and header.row.spacing()==0
   assert header.row.direction()==QBoxLayout.TopToBottom and header.minimumHeight()<170
  assert not request.called
  settings.set('component_images',True)
  for header in headers:
   header.sync_preference();app.processEvents()
   assert not header.picture.isHidden() and header.row.direction()==QBoxLayout.TopToBottom
  assert request.call_count==3 and path.exists()
  ram=product_ui.ProductHeader(label('Detected RAM part'),label('RAM manufacturer'),'ram')
  ram.set_product(dict(kind='ram',model='Exact RAM part',vendor='Vendor',exact=True))
  ram.show();app.processEvents();ram._ready(ram.key,result);ram.sync_preference()
  assert ram.picture.isHidden() and not ram.retry.isActive() and request.call_count==3
  ram.close()
  settings.set('component_images',False)
  for header in headers:
   header.sync_preference();header._ready(header.key,result)
   assert header.picture.isHidden() and not header.retry.isActive()
   header.close()
  assert path.exists(),'Disabling images must preserve cache files'
print('CPU/GPU/mainboard pictures, RAM exclusion, late result, layout collapse and retained cache PASS')
