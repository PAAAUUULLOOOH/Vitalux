"""One chart with selectable unit-aware histories and compact overview power."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication,QWidget
from vitalux import i18n,settings,theme
from vitalux.measurements import MeasurementHistory
from vitalux.measurement_chart import MeasurementChart
from vitalux.pages import OverviewPage,GpuCard,CpuPage,MemoryPage
from vitalux.widgets import ChartPanel,HistoryGraph

app=QApplication.instance() or QApplication([])
power=dict(id='ppt',component='gpu:A',kind='powers',name='amdgpu · PCI · PPT',
           value=150,limits=[('Leistungsgrenze',330)],unit='W',source='/sys/private/source')
gpu=dict(id='A',name='GPU',vendor='AMD',usage=42,temp=60,power=150,power_source_id='ppt',
         hardware=[power,dict(power,id='socket',value=145,limits=[])],
         fan_rpm=0,voltage=950,clock=2200,clock_mem=1200,vram_used=2**30,vram_total=8*2**30)
cpu=dict(model='CPU',usage=15,temp=50,freq=2000,freq_max=4000,cores=2,threads=4,
         per_core=[15]*4,load=[.1,.2,.3])
ram=dict(percent=30,total=8*2**30,used=2*2**30,available=6*2**30,cached=2**30,buffers=0,
         swap_used=0,swap_total=0,swap_percent=0)
cpu_power=dict(power,id='cpu',component='cpu',value=85,primary=True,domain='package-0',limits=[('PL1',125),('PL2',181)])
ram_power=dict(power,id='ram',component='ram',value=10,domain='dram',scope='package-0 · dram',limits=[])
drive_power=dict(power,id='drive',component='disks',device='/sys/devices/nvme0',value=3,limits=[])
sample=dict(cpu=cpu,ram=ram,gpus=[gpu],disks=[dict(mount='/',device='/dev/nvme0n1p1',percent=40,
    total=100*2**30,used=40*2**30,physical_paths=['/sys/devices/nvme0/nvme0n1/nvme0n1p1'])],
    hardware=[cpu_power,ram_power,drive_power,*gpu['hardware']],uptime=100,io=dict(read=0,write=1000),
    net=dict(down=100,up=0,total_down=1000,total_up=200,primary=None,interfaces=[]),app_resources={})

with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    host=QWidget();host.measurement_history=MeasurementHistory()
    host.measurement_history.update(sample,1000)
    host.measurement_history.update(dict(sample,gpus=[dict(gpu,power=160,hardware=[dict(power,value=160)])]),1001)
    chart=MeasurementChart();chart.setParent(host);chart.resize(700,350)
    chart.sync(sample,'gpu:A')
    assert chart.available['fan_rpm']['value']==0
    assert {'usage','vram_pct','temp','power','clock','clock_mem','voltage'}<=set(chart.available)
    before=list(host.measurement_history.groups['gpu:A']['power']['values'])
    chart.select_all(True)
    assert {'%','W','°C','MHz','V','U/min'}<=set(chart.graph.units)
    assert chart.graph.series_scale(chart.graph.units.index('W'),1)==chart.graph.scales['W']
    assert chart.graph.series_scale(chart.graph.units.index('°C'),1)!=chart.graph.scales['W']
    rect=QRectF(12,16,600,250);chart.graph._pointer=rect.right()
    readout='\n'.join(chart.graph.hover_readout(rect))
    assert '160 W' in readout and '60 °C' in readout and '0 U/min' in readout
    chart.actions['power'].trigger();assert not chart.selected['power']
    chart.select_all(False);assert chart.graph.isHidden()
    assert list(host.measurement_history.groups['gpu:A']['power']['values'])==before
    chart.select_all(True)
    assert not chart.graph.isHidden()
    assert not chart.grab().isNull()

    h=dict(cpu=[15],gpu=[42],ram=[30],net_down=[100],net_up=[0])
    for language,word in [('de','Leistung'),('en','Power')]:
        i18n.set_lang(language)
        overview=OverviewPage(dict(name='Linux',short='Test',version='1',color='#4f8cff'),QPixmap(96,96))
        app.processEvents()
        overview.refresh(sample,h)
        for key,value in [('cpu',85),('gpu',150),('ram',10),('disk',3)]:
            assert all(w.text()==f'{word}: {value} W' for w in overview.power_labels[key]),(key,[w.text() for w in overview.power_labels[key]])
        missing=dict(sample,hardware=[],gpus=[dict(gpu,power=None,hardware=[])])
        overview.refresh(missing,h)
        assert all(w.isHidden() and w.text()=='' for widgets in overview.power_labels.values() for w in widgets)
        overview.close()
        app.processEvents()
        card=GpuCard();card.refresh(gpu)
        assert len(card.findChildren(ChartPanel))==1
        assert card.kv['Leistung'].v.text().startswith('150') and card.kv['Leistungsgrenze'].v.text()=='330 W'
        assert not card.hardware.powers
        assert card.kv['Lüfterdrehzahl'].v.text() in ('0 RPM','0 U/min')
        card.close()
    chart.close();host.close();app.processEvents()
print('Compact overview watts, missing-field hiding, one GPU chart, physical scales and measurement selection PASS')
