"""Original component charts and overview-style selection, with live GPU watts."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication
from vitalux import i18n,settings,theme
from vitalux.pages import OverviewPage,GpuCard,CpuPage,MemoryPage,DiskPage,NetworkPage,SystemPage
from vitalux.control import SensorsPage
from vitalux.widgets import ChartPanel,HistoryGraph

app=QApplication.instance() or QApplication([])
power=dict(id='ppt',component='gpu:A',kind='powers',name='amdgpu · PCI · PPT',
           value=150,limits=[('Leistungsgrenze',330)],unit='W',source='/sys/private/source')
gpu=dict(id='A',name='GPU',vendor='AMD',usage=42,temp=60,power=150,power_source_id='ppt',
         hardware=[power,dict(power,id='socket',value=145,limits=[])],
         fan_rpm=0,voltage=950,pcie_current='16.0 GT/s · x16',pcie_max='32.0 GT/s · x16',sensor_source='Linux DRM',clock=2200,clock_mem=1200,vram_used=2**30,vram_total=8*2**30)
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
    h=dict(cpu=[15],gpu=[42],vram=[12.5],ram=[30],cpu_temp=[50],gpu_temp=[60],gpu_clock=[2200],
           io_read=[0],io_write=[1000],net_down=[100],net_up=[0])
    sample['disks'][0]['fstype']='ext4'
    for language,word in [('de','Leistung'),('en','Power')]:
        i18n.set_lang(language)
        overview=OverviewPage(dict(name='Linux',short='Test',version='1',color='#4f8cff'),QPixmap(96,96))
        app.processEvents();overview.refresh(sample,h)
        assert 'gpu' not in overview.power_labels
        for key,value in [('cpu',85),('ram',10),('disk',3)]:
            assert all(w.text()==f'{word}: {value} W' for w in overview.power_labels[key])
        missing=dict(sample,hardware=[],gpus=[dict(gpu,power=None,hardware=[])])
        overview.refresh(missing,h)
        assert all(w.isHidden() and w.text()=='' for widgets in overview.power_labels.values() for w in widgets)
        overview.close();app.processEvents()
        card=GpuCard();card.refresh(gpu,h,mesa='Mesa test driver')
        assert len(card.findChildren(ChartPanel))==3
        assert card.graph.series_names==['Auslastung','VRAM'] and len(card.graph.toggles)==2
        assert card.temperature_graph.graph.mode=='temperature' and card.clock_graph.graph.mode=='clock'
        assert card.kv['Leistung'].v.text()=='150 W' and card.kv['Leistungsgrenze'].v.text()=='330 W'
        assert not card.hardware.powers
        assert card.details.isHidden() and not hasattr(card,'tuning')
        card.more_btn.click();assert not card.details.isHidden()
        assert card.kv['GPU-Takt'].v.text()=='2200 MHz' and card.kv['Spannung'].v.text()=='950 mV'
        assert card.kv['PCIe aktuell'].v.text().endswith('x16') and '32.0 GT/s' in card.kv['PCIe maximal'].v.text()
        assert card.kv['Mesa'].v.text()=='Mesa test driver'
        card.graph.toggles[1].setChecked(False);assert len(card.graph.graph.series)==1
        card.graph.toggles[1].setChecked(True);assert len(card.graph.graph.series)==2
        card.close()
        cpu_page=CpuPage();cpu_page.refresh(sample,h)
        assert len(cpu_page.findChildren(ChartPanel))==2
        assert cpu_page.graph.graph.mode=='percent' and cpu_page.cpu_temp_graph.graph.mode=='temperature'
        assert cpu_page.graph._source[0][0] is h['cpu']
        cpu_page.refresh(dict(sample,cpu=dict(cpu,temp=None)),h)
        assert cpu_page.cpu_temp_card.isHidden()
        cpu_page.close()
        memory=MemoryPage();memory.refresh(sample,h)
        assert len(memory.findChildren(ChartPanel))==1 and memory.graph.graph.mode=='percent'
        assert memory.graph._source[0][0] is h['ram'];memory.close()
        disk=DiskPage();disk.refresh(sample,h)
        assert len(disk.findChildren(ChartPanel))==1 and disk.io_graph.graph.mode=='rate'
        assert [values for values,_ in disk.io_graph._source]==[h['io_read'],h['io_write']];disk.close()
        network=NetworkPage();network.refresh(sample,h)
        assert len(network.findChildren(ChartPanel))==1 and network.graph.graph.mode=='rate'
        assert [values for values,_ in network.graph._source]==[h['net_down'],h['net_up']]
        network.shutdown();network.close()
        system=SystemPage(dict(name='Linux',short='Test',version='1',color='#4f8cff'))
        system.refresh(sample,h)
        assert not system.findChildren(ChartPanel) and hasattr(system,'board_header')
        assert system.status_rows['GPU'].v.text();system.close()
        sensors=SensorsPage();sensors.refresh(sample,h)
        assert not sensors.findChildren(ChartPanel);sensors.close()
    app.processEvents()
print('Original CPU/GPU/RAM/I-O/network charts, restored checks and current GPU watts/limit PASS')
