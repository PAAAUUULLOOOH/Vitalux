"""Native datasheet dialog: full scrollable content, source link and centered headers."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ['VITALUX_SPEC_OFFLINE']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt,QObject,QEvent
from PySide6.QtWidgets import QApplication,QLabel
from vitalux import settings,theme,i18n
from vitalux.product_ui import ProductHeader
from vitalux.widgets import label
from vitalux.spec_ui import SpecificationDialog
app=QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
 settings.set_many(dict(component_images=False,motion='off'))
 class VisibilityGuard(QObject):
  def __init__(self):super().__init__();self.windows=[]
  def eventFilter(self,obj,event):
   if event.type()==QEvent.Show and isinstance(obj,__import__('PySide6.QtWidgets',fromlist=['QWidget']).QWidget) and obj.isWindow():self.windows.append(obj)
   return False
 guard=VisibilityGuard();app.installEventFilter(guard)
 for kind in ('cpu','gpu','mainboard','ram'):
  hidden=ProductHeader(label('Model'),label('Vendor'),kind);app.processEvents();hidden.close()
 app.removeEventFilter(guard)
 assert not guard.windows,'Header construction mapped a separate button window'

 for language in ('de','en'):
  i18n.set_lang(language)
  header=ProductHeader(label('Exact model'),label('Manufacturer'),'gpu');header.key='fixture'
  header.set_specs([('GPU','Detected chip'),('Videospeicher','16 GB')]);header.resize(700,220);header.show()
  record=dict(source='https://www.asus.com/model/techspec/',checked_at=1700000000,sections=[dict(title='Technische Spezifikationen',rows=[['Feature '+str(i),'Full manufacturer value '+str(i)] for i in range(100)])])
  header._manufacturer_specs=record;dialog=SpecificationDialog(header);dialog.resize(600,450);dialog.show();app.processEvents()
  assert dialog.source_button.isVisible() and dialog.scroll.verticalScrollBar().maximum()>0
  texts=[x.text() for x in dialog.scroll.findChildren(QLabel)]
  assert 'Full manufacturer value 99' in texts and '16 GB' in texts
  with patch('vitalux.spec_ui.QDesktopServices.openUrl') as open_url:
   dialog.source_button.click();assert open_url.call_args.args[0].toString()==record['source']
  header._local_specs=[('GPU','Changed device')];dialog.populate(record)
  assert 'Changed device' not in [x.text() for x in dialog.scroll.findChildren(QLabel)]
  assert header.name.alignment()==Qt.AlignCenter
  dialog.close();header.close();app.processEvents()
print('Full datasheet scroll, original-source action, model snapshot, centered identity and DE/EN dialog PASS')
