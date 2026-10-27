"""Four component headers: concise specs, no placeholders, mixed DIMMs, no PL1/2."""
import os,sys,tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage,QPainter,QColor
from PySide6.QtWidgets import QApplication,QScrollArea
from vitalux import theme
from vitalux.component_pages import CpuPage, MemoryPage
from vitalux.product_ui import ProductHeader,loader
from vitalux.product_images import lookup_key
from vitalux.widgets import label

app=QApplication.instance() or QApplication([])
cpu=dict(model='AMD Ryzen 7 9800X3D',manufacturer='AMD',usage=20,cores=8,threads=16,
         per_core=[20]*16,load=[.1,.2,.3],freq=4200,freq_max=5200,temp=50,
         product=dict(kind='cpu',vendor='AMD',model='Ryzen 7 9800X3D',revision='',exact=True))
ram=dict(percent=30,total=32*1024**3,used=10*1024**3,available=22*1024**3,
         cached=0,buffers=0,swap_used=0,swap_total=0,swap_percent=0,modules=[])
for vendor,part in (('Kingston','KF560C30-16'),('Corsair','CMK16GX5')):
    ram['modules'].append(dict(vendor=vendor,model=part,capacity=16*1024**3,memory_type='DDR5',speed=6000,slot='DIMM_A1',
        product=dict(kind='ram',vendor=vendor,model=part,revision='',exact=True)))
power=dict(id='cpu-pkg',component='cpu',kind='powers',unit='W',name='Package',value=88,
           limits=[('PL1',125),('PL2',181)],primary=True,domain='package-0')
sample=dict(cpu=cpu,ram=ram,hardware=[power])
history=dict(cpu=[20],ram=[30],cpu_temp=[50],cpu_clock=[4200],cpu_power=[88])
for product in [cpu['product']]+[m['product'] for m in ram['modules']]:loader().results[lookup_key(product)]=None
page=CpuPage();page.refresh(sample,history)
assert not hasattr(page,'kv')
assert len(page.graph.live_labels)==3 and all(' W' not in item.text() for item in page.graph.live_labels)
assert '4.20 GHz' in page.graph.live_labels[2].text()
assert ('Maximaler Takt','5.20 GHz') in page.product_header._spec_values
assert ('Kerne / Threads','8 / 16') in page.product_header._spec_values
assert page.product_header.picture.isHidden()
memory=MemoryPage();memory.refresh(sample,history)
assert len(memory.module_cards)==2
assert [item[2].text() for item in memory.module_cards]==['KF560C30-16','CMK16GX5']
assert all(item[1].picture.isHidden() for item in memory.module_cards)
ram['modules']=[];memory.refresh(sample,history)
assert all(item[0].isHidden() for item in memory.module_cards)
with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/'cutout.png'
    image=QImage(240,160,QImage.Format_ARGB32);image.fill(0)
    painter=QPainter(image);painter.fillRect(20,10,200,140,QColor('white'));painter.end();image.save(str(path))
    for kind in ('gpu','mainboard','cpu','ram'):
        widget=ProductHeader(label('Product model','bigName'),label('Manufacturer','muted'),kind)
        widget.set_specs([('Kapazität','16 GB'),('Speichertyp','DDR5-6000'),('Steckplatz','DIMM_A1')])
        widget.key='fixture';widget._ready('fixture',dict(path=str(path)))
        area=QScrollArea();area.setWidgetResizable(True);area.setWidget(widget)
        for design, _ in theme.CHOICES:
            theme.set_mode(design);app.setStyleSheet(theme.stylesheet())
            for width in (500,1000):
                area.resize(width,280);area.show();app.processEvents()
                assert widget.picture.isVisible()
                assert widget.picture.geometry().bottom()<widget.details.geometry().top()
                assert abs(widget.details.geometry().center().x()-widget.rect().center().x())<=2
                assert widget.name.alignment() & Qt.AlignHCenter
                assert len(widget._spec_values)==3
                assert area.horizontalScrollBar().maximum()==0
        widget._ready('fixture',None);app.processEvents()
        assert widget.picture.isHidden() and not hasattr(widget,'caption')
        assert widget.row.spacing()==0 and widget.minimumHeight()==0
        assert abs(widget.details.geometry().center().x()-widget.rect().center().x())<=2
        area.close()
page.close();memory.close()
print('Current CPU watts without PL1/PL2, separate RAM products, permanently centered identity/specs and image-above geometry and no blank placeholders PASS')
