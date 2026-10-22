"""Missing readings show confirmed causes, stay unknown otherwise and recover."""
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from vitalux import sensors,i18n
from vitalux.pages import CpuPage,GpuCard
from vitalux.measurement_status import unavailable
app=QApplication.instance() or QApplication([])

for result,reason in (({},'no_sensor'),(PermissionError('denied'),'permission'),
                       (NotImplementedError(),'unsupported'),(RuntimeError(),'unknown')):
    changes={'side_effect':result} if isinstance(result,Exception) else {'return_value':result}
    with patch.object(sensors.psutil,'sensors_temperatures',**changes):
        reasons={};assert sensors._cpu_temp(reasons) is None
        assert reasons['temp']==reason
reasons={}
with patch('builtins.open',side_effect=PermissionError()):assert sensors._read('/test',reasons,'usage') is None
assert reasons['usage']=='permission'
with patch('builtins.open',side_effect=FileNotFoundError()):sensors._read('/test',reasons,'usage')
assert reasons['usage']=='permission','Missing fallback hid an actual permission error'
cpu=dict(model='Test',cores=4,threads=8,freq=None,freq_max=None,temp=None,power=None,
         load=[0,0,0],per_core=[0]*8,usage=0,unavailable=dict(temp='no_sensor',freq='permission'))
gpu=dict(name='Test GPU',usage=None,temp=None,power=None,vram_used=None,vram_total=None,
         unavailable=dict(temp='permission',usage='driver_no_data'))
for language,no_sensor,permission in (('de','Kein Sensor erkannt','Berechtigung fehlt'),
                                      ('en','No sensor detected','Permission required')):
    i18n.set_lang(language)
    page=CpuPage();page.refresh(dict(cpu=cpu),dict(cpu=[0]))
    assert page.kv['Temperatur'].v.text()==no_sensor
    assert page.kv['Takt'].v.text()==permission
    card=GpuCard();card.refresh(gpu)
    assert card.kv['Temperatur'].v.text()==permission
    assert 'driver' in unavailable('driver_no_data').lower() if language=='en' else 'Treiber' in unavailable('driver_no_data')
    assert unavailable('invented reason')==unavailable()
    cpu['temp']=54;page.refresh(dict(cpu=cpu),dict(cpu=[0]))
    assert page.kv['Temperatur'].v.text()=='54 °C'
    cpu['temp']=None
    gpu['temp']=60;card.refresh(gpu);assert card.kv['Temperatur'].v.text()=='60 °C'
    gpu['temp']=None;page.close();card.close()
print('Confirmed sensor/permission/unsupported causes, conservative unknowns, DE/EN and recovered readings PASS')
