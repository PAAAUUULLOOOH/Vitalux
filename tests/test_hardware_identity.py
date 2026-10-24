"""Board partner versus GPU designer, exact models and missing DMI identities."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitalux import hardware_identity as identity, sensors
from vitalux.hardware_sensors import nvidia_details

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder)
    def device(vendor='1002', chip='7550', partner='1da2', model='3490'):
        for name, value in zip(('vendor', 'device', 'subsystem_vendor', 'subsystem_device'),
                               (vendor, chip, partner, model)):
            (path/name).write_text('0x' + value)
        return {'device_path': str(path), 'vendor': 'AMD', 'name': 'AMD Radeon RX 9070 / RX 9070 XT'}
    gpu = device()
    result = identity.gpu_identity(gpu)
    assert result['board_vendor'] == 'SAPPHIRE'
    assert result['board_model'] == 'SAPPHIRE PURE Radeon RX 9070 XT'
    assert result['product']['exact'] and result['pci_ids'] == '1002:7550:1da2:3490'
    with patch.object(sensors, '_nvidia_gpus', return_value=[]), patch.object(sensors, '_drm_gpus', return_value=[gpu]):
        reading = sensors.gpu_info()[0]
        assert reading['name'] == result['board_model']
        assert reading['chip_name'] == 'AMD Radeon RX 9070 / RX 9070 XT'
    assert identity.gpu_identity(device(model='4499'))['board_model'].endswith('RX 9070')
    assert identity.gpu_identity(device(model='e490'))['board_model'].startswith('SAPPHIRE PULSE')
    with patch.object(identity, '_pci_names', return_value=('', '')):
        shared = identity.gpu_identity(device(partner='148c', model='2435'))
        assert shared['board_vendor'] == 'PowerColor' and not shared['product']['exact']
        unknown = identity.gpu_identity(device(chip='0000'))
        assert not unknown['board_model'] and not unknown['product']['exact']
    with patch.object(identity, '_pci_names', return_value=('ASUS', 'TUF / PRIME RTX 5080')):
        assert not identity.gpu_identity(device(vendor='10de', chip='2c02', partner='1043'))['product']['exact']
    with patch.object(identity, '_pci_names', return_value=('ASUS', 'GeForce RTX 5080')):
        assert not identity.gpu_identity(device(vendor='10de', chip='2c02', partner='1043'))['product']['exact']
    missing = identity.gpu_identity({'name': 'GPU', 'vendor': 'AMD'})
    assert not missing['board_vendor'] and not missing['product']['exact']

assert identity.pci_slot('00000000:09:00.0') == '0000:09:00.0'
assert identity.pci_slot('0001:23:04.1') == '0001:23:04.1'
assert identity.pci_slot('../../bad') == ''
xml = '<nvidia_smi_log><gpu id="00000000:09:00.0"><uuid>GPU-A</uuid></gpu><gpu><uuid>GPU-B</uuid><pci><pci_bus_id>00000000:0a:00.0</pci_bus_id></pci></gpu></nvidia_smi_log>'
nv = nvidia_details(xml)
assert nv['GPU-A']['pci_slot'].endswith('09:00.0') and nv['GPU-B']['pci_slot'].endswith('0a:00.0')
board = identity.board_identity('ASUSTeK COMPUTER INC.', 'ROG STRIX B650-A GAMING WIFI', 'Rev 1.xx')
assert board['vendor'] == 'ASUS' and board['exact'] and board['revision'] == 'Rev 1.xx'
assert identity.board_identity('Micro-Star International Co., Ltd.', 'MAG X870 TOMAHAWK WIFI')['vendor'] == 'MSI'
for value in ('Default string', 'To Be Filled By O.E.M.', 'Not Specified', 'System Product Name', '–'):
    assert not identity.board_identity('ASUS', value)['exact']
print('Exact Sapphire PURE identity, shared-ID fallbacks, per-GPU PCI association and DMI products PASS')
