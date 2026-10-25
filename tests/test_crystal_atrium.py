"""Static Crystal Atrium on the shared dashboard, and tidy Eclipse CPU/GPU rows."""
import os,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QSize
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication,QLabel
from vitalux import brand,crystal_atrium,premium,theme
from vitalux.design_capabilities import capabilities
from vitalux.signature_designs import Metric
from vitalux.widgets import Gauge,Card,label
from vitalux.product_ui import ProductHeader

app=QApplication.instance() or QApplication([])
assert len(theme.CHOICES)==14 and dict(theme.CHOICES)['crystal_atrium']=='Crystal Atrium'
assert not capabilities('crystal_atrium')['background']
one=crystal_atrium.scene_pixmap(QSize(500,320),phase=0).toImage()
two=crystal_atrium.scene_pixmap(QSize(500,320),phase=500).toImage()
assert one==two and one.pixelColor(10,10)!=one.pixelColor(450,290)
theme.set_mode('crystal_atrium');app.setStyleSheet(theme.stylesheet())
assert brand._brand_asset(True)=='brand/vitalux-pulse-crystal-atrium.svg'
for kind in ('pulse','wordmark'):
    svg=(Path('assets/brand')/f'vitalux-{kind}-crystal-atrium.svg').read_text()
    assert 'data-material="glass"' in svg and 'stop-opacity=' in svg
tile=premium.DesignTile('crystal_atrium');tile.show();app.processEvents();assert not tile.grab().isNull()
card=Card('Crystal Atrium');card.body.addWidget(label('Crystal Atrium'));card.resize(480,250);card.show();app.processEvents();assert not card.grab().isNull()
assert card.findChild(QLabel,'cardTitle').palette().color(QPalette.WindowText).name()==crystal_atrium.PALETTE['accent']
gauge=Gauge();gauge.set(38);gauge.show();app.processEvents();assert not gauge.grab().isNull()
assert not hasattr(crystal_atrium,'AtriumCanvas')
theme.set_mode('eclipse_crystal');app.setStyleSheet(theme.stylesheet())
for kind in ('cpu','gpu'):
    metric=Metric('Prozessor' if kind=='cpu' else 'Grafik',kind)
    metric.set(38,'52 °C',extra='Model fixture',history=[10,20,38])
    for width,height in ((200,190),(440,230),(600,300)):
        metric.resize(width,height);metric.show();app.processEvents();metric.grab()
        value,detail,graph=metric.reading_regions
        assert value.bottom()<detail.top() and detail.bottom()<graph.top()
        assert detail.bottom()<=metric.height()
    metric.close()
header=ProductHeader(label('CPU'),label(''),'cpu');header.set_specs([('Kerne / Threads','8 / 16')]);header.show();app.processEvents()
assert header.picture.isHidden() and header.minimumSizeHint().height()<170 and not hasattr(header,'caption')
header.close();tile.close();card.close();gauge.close()
print('Crystal Atrium static gradient, original dashboard material, glass branding/gallery and separated Eclipse readings PASS')
