"""Deterministic CPU/GPU/RAM/storage readings shared by regressions and captures."""
from copy import deepcopy
from PySide6.QtWidgets import QApplication

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


def load_fixture():
    return QApplication.instance() or QApplication([]), deepcopy(sample)
