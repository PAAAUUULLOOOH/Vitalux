"""Full GPU captions, stable gauge dimensions and no overview GPU power in every design."""
import os,sys
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap
from vitalux import theme,i18n,motion
from vitalux.pages import OverviewPage
# Use the same complete monitoring fixture as the original-chart regression.
namespace={'__file__':str(Path(__file__).with_name('test_component_charts.py'))}
source=Path(namespace['__file__']).read_text();exec(source[:source.index('with tempfile.TemporaryDirectory()')],namespace)
app=namespace['app'];sample=namespace['sample']
history={key:[10,20] for key in ('cpu','gpu','ram','net_down','net_up')}
name='ASUS TUF GAMING Radeon RX 9060 XT OC Edition 16GB GDDR6 PCI Express Graphics Card'
sample['gpus'][0]['name']=name
page=OverviewPage(dict(name='Linux',version='1'),QPixmap(96,96))
with patch.object(motion,'enabled',return_value=False),patch.object(motion,'duration',return_value=0):
 for language in ('de','en'):
  i18n.set_lang(language)
  for design,_ in theme.CHOICES:
   theme.set_mode(design);app.setStyleSheet(theme.stylesheet());page.refresh_design()
   for width in (760,1180):
    page.resize(width,1800);page.show();page.refresh(sample,history);app.processEvents();page.board.refresh_geometry();app.processEvents();page.grab()
    assert 'gpu' not in page.power_labels
    sub=page.g_gpu.box.sub
    assert name in sub.text() and '\u2026' not in sub.text() and '...' not in sub.text()
    assert len({card.box.gauge.height() for card in (page.g_cpu,page.g_gpu,page.g_ram,page.g_disk)})==1
    if design not in ('aether_glass','eclipse_crystal','nebula_prism','quantum_core','crystal_atrium'):
     assert len({card.box.gauge.mapTo(card,QPoint(0,0)).y() for card in (page.g_cpu,page.g_gpu,page.g_ram,page.g_disk)})==1
     assert sub.height()>=sub.heightForWidth(sub.width()),(design,width,sub.height(),sub.heightForWidth(sub.width()))
    else:
     metric=page.design_metrics['gpu']
     assert metric.model_caption.text()==name
     assert metric.model_caption.geometry().top()>metric.drawing_rect().bottom()
page.close()
print('All 15 designs, DE/EN, full wrapped GPU name, same load-gauge geometry and no GPU overview watts PASS')
