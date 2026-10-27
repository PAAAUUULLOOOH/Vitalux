"""A chart series must not fill the area above another series' curved line."""
import os,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from vitalux import theme
from vitalux.charts import HistoryGraph

app=QApplication([])
theme.set_mode('glass')
app.setStyleSheet(theme.stylesheet())
graph=HistoryGraph(maxlen=3)
graph.resize(500,280)
graph.show()
graph.set_series([([80,20,80],'#52d3ff')])
app.processEvents()
single=graph.grab().toImage()
graph.set_series([([0,0,0],'#ffc34d'),([80,20,80],'#52d3ff')])
app.processEvents()
combined=graph.grab().toImage()
# The gold line lies along the bottom. It cannot color the space above the V.
for x,y in ((200,100),(220,100),(240,110)):
    assert single.pixelColor(x,y)==combined.pixelColor(x,y),(x,y)
assert single!=combined,'Second series did not render'
graph.close()
print('Independent chart lines, translucent fills and multi-series material PASS')
