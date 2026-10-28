"""CPU readings share one selectable chart with truthful independent units."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QRectF
from vitalux import settings,theme,i18n
from vitalux.component_pages import CpuPage
from vitalux.charts import ChartPanel
from sensor_fixture import load_fixture
app,sample=load_fixture()
h=dict(cpu=[0,15],cpu_temp=[None,50],cpu_clock=[2000,4000],cpu_power=[0,85],
       cpu_load_1=[0,.1],cpu_load_5=[0,.2],cpu_load_15=[0,.3])
with tempfile.TemporaryDirectory() as directory,patch.object(settings,'PATH',str(Path(directory)/'settings.json')):
 settings.set_many(dict(motion='off',component_images=False))
 page=CpuPage();page.resize(780,1250);page.show();page.refresh(sample,h);app.processEvents()
 assert len(page.findChildren(ChartPanel))==1
 panel=page.graph;assert len(panel.toggles)==3
 assert not hasattr(page,'kv') and not hasattr(page,'gauge') and not hasattr(page,'hardware')
 assert set(panel.graph.unit_scales())=={'percent','temperature','frequency'}
 assert len(panel.graph.series)==3
 panel.toggles[2].setChecked(False);assert 'frequency' not in panel.graph.unit_scales()
 graph=panel.graph;rect=QRectF(0,0,200,150);graph._pointer=rect.right()
 text=' '.join(graph.hover_readout(rect))
 assert '50.0 °C' in text and 'W' not in text and 'Last' not in text and 'GHz' not in text,text
 panel.toggles[2].setChecked(True)
 assert '4.00 GHz' in ' '.join(graph.hover_readout(rect))
 for toggle in panel.toggles:toggle.setChecked(False)
 assert not panel.graph.series
 panel.toggles[0].setChecked(True)
 panel.time_range.setCurrentIndex(2);assert panel.graph.horizon_seconds==900
 for language in ('de','en'):
  i18n.set_lang(language);panel.retheme();assert not page.grab().isNull()
 page.close()
print('One CPU chart, selection, real units/hover, zero/gaps, removed power/load curves and time ranges PASS')
