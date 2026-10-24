"""Real component watts, non-overlapping sources and physical drive association."""
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
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
print('Selected component watts, power limits, genuine zeroes and unambiguous system-drive mapping PASS')
