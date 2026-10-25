"""Actual retained overview layouts, watts on/off, ellipsis and native hover."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint,QEvent,Qt
from PySide6.QtGui import QPixmap,QHelpEvent
from PySide6.QtWidgets import QToolTip
from vitalux import theme,i18n,motion,settings,design_catalog
from vitalux.pages import OverviewPage
from vitalux.hover_hints import install
ns={'__file__':str(Path(__file__).with_name('test_component_charts.py'))}
source=Path(ns['__file__']).read_text();exec(source[:source.index('with tempfile.TemporaryDirectory()')],ns)
app=ns['app'];sample=ns['sample'];guard=install(app)
history={key:[10,20] for key in ('cpu','gpu','ram','net_down','net_up')}
name='ASUS TUF GAMING Radeon RX 9060 XT OC Edition 16GB GDDR6 PCI Express Graphics Card'
sample['gpus'][0]['name']=name
sample['cpu']['model']='AMD Ryzen 9 9950X3D 16-Core Processor with a long identification string'
output=Path('build/overview23');output.mkdir(parents=True,exist_ok=True)
page=OverviewPage(dict(name='Linux',version='1'),QPixmap(96,96))
cases=0
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')),patch.object(motion,'enabled',return_value=False),patch.object(motion,'duration',return_value=0):
 for language in ('de','en'):
  i18n.set_lang(language)
  for design in (*design_catalog.VISIBLE,'eclipse_crystal','minimal'):
   settings.set_many(dict(theme=design,accent='design_default',motion='off'))
   theme.set_mode(design);app.setStyleSheet(theme.stylesheet());page.refresh_design()
   for width in (760,1180):
    for measured in (True,False):
     data=dict(sample) if measured else dict(sample,hardware=[],gpus=[dict(sample['gpus'][0],power=None,hardware=[])])
     page.resize(width,1800);page.show();page.refresh(data,history);app.processEvents();page.board.refresh_geometry();app.processEvents()
     picture=page.grab();assert not picture.isNull()
     assert 'gpu' not in page.power_labels
     assert all(w.height()<=max(24,w.fontMetrics().height()+2) for widgets in page.power_labels.values() for w in widgets)
     assert len({card.box.gauge.height() for card in (page.g_cpu,page.g_gpu,page.g_ram,page.g_disk)})==1
     if design=='crystal_atrium':
      infos=page.atrium.captions
      assert len(page.atrium._sphere_meta)==3
      caption=infos['gpu'].name
     else:
      signature=design in ('nebula_prism','quantum_core','eclipse_crystal')
      index=1 if signature else 0
      infos={key:items[index] for key,items in page.overview_info.items()}
      caption=infos['gpu'].name
      for key,info in infos.items():
       meter=page.design_metrics[key] if signature else getattr(page,'g_'+key).box.gauge
       assert meter.height()==180,(design,key,meter.height())
       assert info.mapTo(page,QPoint(0,0)).y()>=meter.mapTo(page,QPoint(0,meter.height())).y(),(design,width,key)
       labels=[w for w in (info.name,info.detail,info.power) if not w.isHidden()]
       for first,second in zip(labels,labels[1:]):assert first.geometry().bottom()<second.geometry().top(),(design,key)
       assert info.geometry().bottom()<=info.parentWidget().height(),(design,key,info.geometry(),info.parentWidget().size())
     assert caption.original_text==name and caption.property('vitaluxFullNameHint')
     assert '\u2026' in caption.text() and caption.alignment()==Qt.AlignCenter
     event=QHelpEvent(QEvent.ToolTip,QPoint(4,4),caption.mapToGlobal(QPoint(4,4)))
     app.sendEvent(caption,event);assert QToolTip.text()==name
     QToolTip.hideText()
     if language=='de' and width==1180 and measured:picture.save(str(output/(design+'.png')))
     cases+=1
page.close();app.removeEventFilter(guard)
print(f'{cases} real overview renders: retained/internal designs, DE/EN, widths, watts present/missing, bounded captions and native hover PASS')
