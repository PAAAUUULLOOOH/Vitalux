"""Kernel-ABI fixtures: identity, units, zeroes, RAPL gaps/reset/wrap and sessions."""
import math
from pathlib import Path
import struct
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitalux.hardware_sensors import (RaplReader, HardwareMonitor, PowerSessions,
    hwmon_readings, amd_metrics, nvidia_details, primary_power, number)


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(value))


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    zone = root/'class/powercap/intel-rapl:0'
    put(zone/'name', 'package-0');put(zone/'max_energy_range_uj', 10**12)
    put(zone/'energy_uj', 400000000000)
    put(zone/'constraint_0_name','short_term');put(zone/'constraint_0_power_limit_uw',181000000)
    put(zone/'constraint_1_name','long_term');put(zone/'constraint_1_power_limit_uw',125000000)
    dram=zone/'intel-rapl:0:0';put(dram/'name','dram')
    put(dram/'energy_uj',50000000);put(dram/'max_energy_range_uj',10**10)
    (zone.parent/'alias').symlink_to(zone, target_is_directory=True)
    reader=RaplReader(root)
    first=reader.sample(100)
    assert len(first)==2 and all(r['value'] is None for r in first)
    package=next(r for r in first if r.get('primary'))
    assert dict(package['limits'])=={'PL2':181,'PL1':125},'Never infer PL1 from constraint index'
    put(zone/'energy_uj',400100000000);put(dram/'energy_uj',60000000)
    second=reader.sample(101)
    assert primary_power(second,'cpu')==100 and primary_power(second,'ram')==10
    put(zone/'energy_uj',1000000)  # reset away from a rollover boundary
    assert primary_power(reader.sample(102),'cpu') is None
    put(zone/'energy_uj',11000000)
    assert primary_power(reader.sample(103),'cpu')==10
    put(zone/'energy_uj',10**12-2000000);reader.sample(104)
    put(zone/'energy_uj',3000000)
    assert primary_power(reader.sample(105),'cpu')==5
    assert primary_power(reader.sample(105),'cpu') is None,'Zero interval must not produce watts'
    assert primary_power(reader.sample(160),'cpu') is None,'Do not bridge suspend/gaps'
    original_read=__import__('vitalux.hardware_sensors',fromlist=['read']).read
    with patch('vitalux.hardware_sensors.read',side_effect=lambda p: '' if Path(p)==zone/'energy_uj' else original_read(p)):
        denied=reader.sample(161)
        assert primary_power(denied,'cpu') is None
        assert dict(next(r for r in denied if r.get('primary'))['limits'])=={'PL2':181,'PL1':125},'Readable limits survive restricted energy counters'
    put(zone/'energy_uj',5000000)
    assert primary_power(reader.sample(162),'cpu') is None,'Permission recovery needs a fresh baseline'
    put(zone/'energy_uj',7000000)
    assert primary_power(reader.sample(164),'cpu')==1
    mmio=zone.parent/'intel-rapl-mmio:0'
    put(mmio/'name','package-0');put(mmio/'energy_uj',1000000);put(mmio/'max_energy_range_uj',10**9)
    reader.sample(165);put(mmio/'energy_uj',4000000)
    with patch('vitalux.hardware_sensors.read',side_effect=lambda p: '' if Path(p)==zone/'energy_uj' else original_read(p)):
        alternate=reader.sample(166)
        assert primary_power(alternate,'cpu')==3
        assert len([r for r in alternate if r.get('primary')])==1,'Do not add overlapping MSR/MMIO counters'

    hw=root/'class/hwmon/hwmon0'
    put(hw/'name','board');put(hw/'power1_input',0);put(hw/'power1_average',50000000)
    put(hw/'power1_cap',100000000);put(hw/'fan1_input',0);put(hw/'in0_input',1250)
    put(hw/'temp1_input',-5000);put(hw/'temp2_input','nan');put(hw/'fan2_input',700)
    put(hw/'fan2_fault',1);put(hw/'power2_cap',25000000)
    readings=hwmon_readings(root)
    powers=[r for r in readings if r['kind']=='powers']
    assert len(powers)==2
    rail=next(r for r in powers if r['channel']=='power1')
    assert rail['value']==0 and rail['limits']==[('Leistungsgrenze',100)]
    assert next(r for r in powers if r['channel']=='power2')['value'] is None
    assert [r['value'] for r in readings if r['kind']=='fans']==[0]
    assert [r['value'] for r in readings if r['kind']=='temps']==[-5]
    assert [r['value'] for r in readings if r['kind']=='voltages']==[1.25]

    device=root/'devices/pci0000/0000:03:00.0';device.mkdir(parents=True)
    (hw/'device').symlink_to(device,target_is_directory=True)
    put(hw/'name','amdgpu');put(hw/'temp3_input',80000);put(hw/'temp3_label','mem')
    gpu=dict(id='gpu0',name='Test GPU',device_path=str(device),power=None,temp=None)
    other=dict(id='gpu1',name='Second GPU',device_path=str(root/'different'),power=None)
    data=HardwareMonitor(root).sample([gpu,other],now=100,wall=1000)
    assert gpu['power']==0 and gpu['vram_temp']==80
    assert other['power'] is None and not other['hardware']
    assert all(r['component']=='gpu:gpu0' for r in data if r.get('channel'))
    (hw/'power1_input').unlink();(hw/'power1_average').unlink()
    data=HardwareMonitor(root).sample([dict(gpu,power=None)],now=101,wall=1001)
    assert next(r for r in data if r.get('channel')=='power1')['value'] is None
    fallback=dict(gpu,power=42,power_limit=100)
    HardwareMonitor(root).sample([fallback],now=102,wall=1002)
    assert fallback['power']==42,'A readable limit alone must not hide genuine driver power'
    put(root/'class/thermal/thermal_zone0/temp',40000)
    put(root/'class/thermal/thermal_zone0/type','cpu_thermal')
    for file in hw.glob('temp*_input'):file.unlink()
    assert any(r['value']==40 and r['kind']=='temps' for r in hwmon_readings(root))


def power(value, interval=None):
    return dict(id='one',kind='powers',value=value,interval=interval)
tracker=PowerSessions();a=power(10);tracker.update([a],0,1000)
assert a['average'] is None and a['maximum']==10
b=power(30);tracker.update([b],2,1002)
assert b['average']==20 and b['maximum']==30
tracker.update([],3,1003)
c=power(100);tracker.update([c],7,1007)
assert c['average']==20,'No integration over unavailable observations'
d=power(0);tracker.update([d],8,1008)
assert d['average']==30 and d['maximum']==100 and d['history'][-1][1]==0
e=power(20,4);tracker.update([e],12,1012)
assert math.isclose(e['average'],170/7),'RAPL power is the average of its actual interval'
assert number(float('nan')) is None and number(True) is None
monitor=HardwareMonitor('/not-a-sysroot')
monitor.power=tracker
monitor.reset_baselines()
assert tracker.sessions['one']['previous'] is None and tracker.sessions['one']['history'][-1][1] is None
after=power(100);tracker.update([after],14,1014)
assert math.isclose(after['average'],170/7),'A sampling-gap reset must retain stats without extrapolation'

v13=bytearray(b'\xff'*120);struct.pack_into('<HBB',v13,0,120,1,3)
for offset,value in ((4,50),(6,70),(8,82),(16,40),(18,23),(20,17),(22,100),(72,0),(106,950)):
    struct.pack_into('<H',v13,offset,value)
struct.pack_into('<Q',v13,112,0)
fields=amd_metrics(v13)
assert fields['vram_temp']==82 and fields['memory_busy']==23 and fields['fan_rpm']==0
assert fields['clock'] is None and fields['throttle_flags']=='0x0'
v14=bytearray(64);struct.pack_into('<HBB',v14,0,64,1,4)
for offset,value in ((4,75),(6,85),(10,120),(12,45),(14,33),(16,18),(18,65535),(20,65535),(22,65535)):
    struct.pack_into('<H',v14,offset,value)
fields=amd_metrics(v14)
assert fields['memory_busy']==33 and fields['socket_power']==120 and fields['video_busy_0']==18
assert 'encoder_busy' not in fields and 'decoder_busy' not in fields
assert amd_metrics(v14[:20])=={}
v14[3]=99;assert amd_metrics(v14)=={}
v14[2]=2;v14[3]=1;assert amd_metrics(v14)=={},'APU revisions have a different ABI'

xml='<nvidia_smi_log><gpu><uuid>GPU-test</uuid><temperature><memory_temp>82 C</memory_temp></temperature><utilization><memory_util>14 %</memory_util><encoder_util>0 %</encoder_util><decoder_util>N/A</decoder_util></utilization><power_readings><enforced_power_limit>250 W</enforced_power_limit></power_readings><clocks_event_reasons><clocks_event_reason_sw_power_cap>Active</clocks_event_reason_sw_power_cap></clocks_event_reasons></gpu></nvidia_smi_log>'
fields=nvidia_details(xml)['GPU-test']
assert fields['encoder_busy']==0 and fields['decoder_busy'] is None and fields['power_limit']==250
assert fields['throttle_reasons']=='sw power cap'
assert nvidia_details('not xml')=={}
print('Real-source sensor units, zeroes, limits, identities, RAPL reset/wrap/gaps, weighted sessions and versioned GPU formats PASS')
