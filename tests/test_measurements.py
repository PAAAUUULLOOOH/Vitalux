"""Component units, zeroes, device identity, power selection and real time gaps."""
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux.measurements import MeasurementHistory,describe
from vitalux.power_display import component_power,disk_power,gpu_power,power_limit
from vitalux.hardware_sensors import block_devices


def source(key,component,value,**extra):
    return dict(id=key,component=component,kind='powers',name='Device '+key,
                value=value,limits=[],source='/sys/'+key,**extra)


package=source('package','cpu',85,primary=True,domain='package-0',scope='CPU-Package · package-0')
package['limits']=[('PL1',125),('PL2',181)]
partial=source('cores','cpu',55,domain='core',scope='core')
assert component_power([package,partial],'cpu')['value']==85
assert component_power([partial],'cpu') is None
ram1=source('dram-msr','ram',10,domain='dram',scope='package-0 · dram')
ram2=source('dram-mmio','ram',11,domain='dram',scope='package-0 · dram')
assert component_power([ram1,ram2],'ram')['value']==10,'Overlapping DRAM sources are not summed'
gpu1=source('ppt','gpu:A',150);gpu1['limits']=[('Leistungsgrenze',330)]
gpu2=source('socket','gpu:A',140)
g=dict(id='A',name='GPU A',power=150,power_source_id='ppt',hardware=[gpu1,gpu2],
       usage=42,temp=60,voltage=950,fan_rpm=0,clock=2200,clock_mem=1200,
       vram_used=4*2**30,vram_total=16*2**30)
assert gpu_power(g)['value']==150 and power_limit(gpu_power(g))==330
assert gpu_power(dict(g,hardware=[dict(gpu1,value=0),gpu2]))['value']==0
sample=dict(cpu=dict(usage=15,temp=50,freq=2000,per_core=[15,20],load=[.2,.1,.1]),
            ram=dict(percent=30,total=16*2**30,used=5*2**30),gpus=[g],
            hardware=[package,partial,ram1,ram2,gpu1,gpu2],io=dict(read=0,write=1000),
            net=dict(down=100,up=0),disks=[dict(mount='/',percent=40)])
description=describe(sample)
assert description['gpu:A']['voltage']['value']==.95 and description['gpu:A']['voltage']['unit']=='V'
assert description['gpu:A']['fan_rpm']['value']==0
assert description['cpu']['power']['value']==85
assert description['ram']['power']['value']==10
assert description['disks']['read']['value']==0

history=MeasurementHistory(maxlen=6)
history.update(sample,1000)
other=dict(g,id='B',name='GPU B',usage=5,hardware=[])
history.update(dict(sample,gpus=[other,dict(g,usage=70,power=None,hardware=[])]),1001)
assert list(history.groups['gpu:A']['usage']['values'])==[42,70]
assert list(history.groups['gpu:B']['usage']['values'])==[None,5]
assert history.groups['gpu:A']['power']['values'][-1] is None
history.update(dict(sample,_gap_before=True,gpus=[dict(g,usage=None,fan_rpm=0)]),1010,interval=2)
assert list(history.times)==[1000,1001,1003,1010]
assert list(history.groups['gpu:A']['usage']['values'])==[42,70,None,None]
assert 'usage' not in history.current['gpu:A']
assert history.current['gpu:A']['fan_rpm']['value']==0
assert history.groups['gpu:B']['usage']['value'] is None
for stamp in range(1011,1020):history.update(sample,stamp)
assert len(history.times)==6 and all(len(m['values'])==6 for group in history.groups.values() for m in group.values())

with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    controller=root/'devices/nvme/nvme0';partition=controller/'nvme0n1/nvme0n1p3'
    partition.mkdir(parents=True)
    block=root/'class/block';block.mkdir(parents=True)
    (block/'nvme0n1p3').symlink_to(partition,target_is_directory=True)
    device=root/'dev/nvme0n1p3';device.parent.mkdir();device.touch()
    paths=block_devices(str(device),root)
    assert paths==[str(partition)]
    drive=source('nvme-power','disks',3.5,device=str(controller))
    assert disk_power([drive],dict(physical_paths=paths))['value']==3.5
    assert disk_power([drive],dict(physical_paths=[])) is None
    assert disk_power([drive],dict(physical_paths=[str(partition),str(root/'other/sda')])) is None
    assert disk_power([drive,source('rail2','disks',2,device=str(controller))],dict(physical_paths=paths)) is None
    dm=root/'devices/virtual/block/dm-0';(dm/'slaves').mkdir(parents=True)
    (dm/'slaves/nvme0n1p3').symlink_to(partition,target_is_directory=True)
    (block/'dm-0').symlink_to(dm,target_is_directory=True)
    mapped=root/'dev/dm-0';mapped.touch()
    assert block_devices(str(mapped),root)==paths
print('Physical units, selected GPU watts/limit, independent histories, gaps, zero values and safe system-drive association PASS')
