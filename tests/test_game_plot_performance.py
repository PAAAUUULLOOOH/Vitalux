"""Long recorded sessions preserve spikes and remain responsive on hover."""
import os,sys,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication
from vitalux.charts import HistoryGraph

app=QApplication([])
graph=HistoryGraph(maxlen=4096,mode='mixed');graph.resize(820,260)
graph.setProperty('recordedSession',True)
graph.sample_times=[i*3.5 for i in range(4096)];graph.horizon_seconds=graph.sample_times[-1]
graph.series_names=['FPS','Frametime'];graph.series_modes=['fps','frametime']
graph.series_styles=[]
values=[60+120*(i%2) for i in range(4096)]
graph.set_series([(values,'#43ce96'),([5+25*(i%2) for i in range(4096)],'#f5c15c')])
graph.show();start=time.perf_counter();app.processEvents();graph.grab()
cold=time.perf_counter()-start
assert cold<2.5,('Long session blocked the interface',cold)
layer=graph._recorded_layer
with patch.object(graph,'_paint_curves',wraps=graph._paint_curves) as draw:
 start=time.perf_counter()
 for x in range(100,600,40):graph._pointer=x;graph.grab()
 elapsed=time.perf_counter()-start
 assert draw.call_count==0,'Hover rebuilt the recorded curves'
 assert elapsed<1.5,('Session hover blocked the interface',elapsed)
assert graph.series[0][0]==values and len(graph.sample_times)==4096
rect=QRectF(12,22,650,190);scales=graph.unit_scales()
curves=graph._curves(rect,200,scales,False)
paths=curves[0][0]
assert len(paths)==2,'Dense recorded points need their min/max envelope'
upper,lower=[path for path,area in paths]
assert abs(upper.boundingRect().top()-(rect.bottom()-180/scales['fps'][0]*rect.height()))<.01
assert abs(lower.boundingRect().bottom()-(rect.bottom()-60/scales['fps'][0]*rect.height()))<.01
graph._pointer=rect.right()
assert any('180 FPS' in line for line in graph.hover_readout(rect))
with patch.object(graph,'devicePixelRatioF',return_value=2.):
 high_dpi=graph._curves(rect,200,scales,False)[0][0][0][0]
 assert high_dpi.elementCount()>upper.elementCount(),'Display scaling reused a lower-resolution envelope'
 assert abs(high_dpi.boundingRect().top()-upper.boundingRect().top())<.01
graph.resize(900,260);graph.grab();assert graph._recorded_layer is not layer
graph.close();graph.deleteLater()
print(f'4096-point extrema/exact hover, cached interaction and resize PASS; cold={cold:.3f}s hover={elapsed:.3f}s')
