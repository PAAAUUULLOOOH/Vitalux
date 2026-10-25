"""CPU identity and real SMBIOS layouts, mixed DIMMs, inaccessible firmware."""
import struct,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux import hardware_inventory as inventory

def dimm(vendor,part,size=16384,kind=0x22,speed=6000,slot='DIMM_A1'):
    raw=bytearray(0x28);raw[0]=17;raw[1]=len(raw)
    struct.pack_into('<H',raw,0x0c,size)
    raw[0x10]=1;raw[0x12]=kind;raw[0x17]=2;raw[0x1a]=3
    struct.pack_into('<H',raw,0x15,speed);struct.pack_into('<H',raw,0x20,speed)
    if size==0x7fff:struct.pack_into('<I',raw,0x1c,65536)
    return bytes(raw)+('\0'.join((slot,vendor,part))+'\0\0').encode()

modules=inventory.parse_smbios(dimm('Kingston','KF560C30-16')+dimm('Corsair','CMK32GX5',slot='DIMM_B1')+dimm('Unknown','',size=0))
assert len(modules)==2 and modules[0]['capacity']==16*1024**3
assert modules[0]['memory_type']=='DDR5' and modules[0]['speed']==6000
assert modules[0]['product']['exact'] and modules[1]['vendor']=='Corsair'
assert inventory.parse_smbios(dimm('Samsung','M393',size=0x7fff))[0]['capacity']==64*1024**3
unknown=inventory.parse_smbios(dimm('Unknown','Unknown'))[0]
assert not unknown['product']['exact']
for raw in (b'',b'\x11\x00\x00\x00',dimm('Kingston','KF')[:-1],b'\x11\xff\x00\x00'):
    assert inventory.parse_smbios(raw)==[]
text='''Handle 0x1, DMI type 17, 40 bytes
Memory Device
 Size: 32 GB
 Type: DDR4
 Manufacturer: SK Hynix
 Part Number: HMAA4GR7
 Locator: DIMM_A1
 Speed: 3200 MT/s
 Configured Memory Speed: 2933 MT/s

Memory Device
 Size: No Module Installed
 Manufacturer: Unknown
'''
decoded=inventory.parse_dmidecode(text)
assert len(decoded)==1 and decoded[0]['capacity']==32*1024**3
assert decoded[0]['speed']==2933 and decoded[0]['vendor']=='SK hynix'
inventory.memory_modules.cache_clear()
with patch('builtins.open',side_effect=PermissionError),patch.object(inventory.shutil,'which',return_value=None),patch.object(inventory.subprocess,'run') as run:
    assert inventory.memory_modules()==[]
    run.assert_not_called()
inventory.memory_modules.cache_clear()
inventory.cpu_product.cache_clear()
with patch.object(Path,'read_text',return_value='vendor_id : AuthenticAMD\nmodel name : AMD Ryzen 9 9950X3D\n'):
    cpu=inventory.cpu_product();assert cpu['vendor']=='AMD' and cpu['exact']
inventory.cpu_product.cache_clear()
with patch.object(Path,'read_text',return_value='vendor_id : GenuineIntel\nmodel name : QEMU Virtual CPU\n'):
    assert not inventory.cpu_product()['exact']
inventory.cpu_product.cache_clear()
print('SMBIOS DDR4/DDR5 identities, mixed modules, exact part numbers, permission fallback and CPU vendors PASS')
