"""Current readings reflow on loss/recovery; running versions remain independent."""
import os
from pathlib import Path
import sys
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from vitalux import appearance, i18n, theme, profiles, pages_extra
from vitalux.pages import GpuCard
from vitalux.sensor_ui import SensorPanel
from vitalux.widgets import HistoryGraph
from vitalux.update_manager import UpdateManager

app=QApplication.instance() or QApplication([])
for language in ('de','en'):
    i18n.set_lang(language)
    card=GpuCard()
    gpu=dict(name='GPU',temp=40,fan_rpm=0,power=50,usage=10,vram_used=10,vram_total=100,
             vram_temp=80,memory_busy=25,encoder_busy=0,decoder_busy=None)
    card.refresh(gpu)
    assert card.kv['Lüfterdrehzahl'].v.text() in ('0 U/min','0 RPM')
    assert not card.kv['Lüfterdrehzahl'].isHidden() and card.kv['Decoder'].isHidden()
    gpu.update(temp=None,fan_rpm=None,power=None,vram_temp=None,memory_busy=None)
    card.refresh(gpu)
    for key in ('Temperatur','Lüfterdrehzahl','Leistung','VRAM-Temperatur','Speichercontroller'):
        assert card.kv[key].isHidden() and card.kv[key].v.text()==''
    assert not card.kv['Encoder'].isHidden() and '0' in card.kv['Encoder'].v.text()
    positions=[card.live_grid.getItemPosition(i)[:2] for i in range(card.live_grid.count())]
    columns=1 if card.width()<640 else 2
    assert positions==[(i//columns,i%columns) for i in range(len(positions))],'No gaps after missing fields'
    gpu.update(fan_rpm=0);card.refresh(gpu)
    assert not card.kv['Lüfterdrehzahl'].isHidden()
    card.close()

panel=SensorPanel()
record=dict(id='cpu',name='CPU Package',kind='powers',value=0,
            limits=[('PL1',125)],source='fixture')
panel.sync([record]);block=panel.powers['cpu']
assert not panel.isHidden() and not block.rows['Leistung'].isHidden()
assert set(block.rows)=={'Leistung','PL1'}
assert block.rows['PL1'].v.text()=='125 W'
assert not panel.findChildren(HistoryGraph),'Power rows must not create separate history plots'
panel.sync([]);assert panel.isHidden() and block.isHidden()
panel.sync([dict(record,value=None)]);assert block.rows['Leistung'].isHidden()
assert not block.rows['PL1'].isHidden()
panel.close()

for running in ('0.9.6.3-unstable.14','0.9.6.3-unstable.29','0.9.6.2'):
    channel='unstable' if '-unstable.' in running else 'stable'
    with patch.object(pages_extra,'__version__',running),patch.object(profiles,'installed',return_value=channel):
        manager=UpdateManager();manager._timer.stop()
        page=pages_extra.UpdatePage(manager)
        assert page.current.v.text()==channel.title()+' · v'+running
        manager.channel='stable' if channel=='unstable' else 'unstable'
        manager.records[manager.channel]=dict(ok=True,latest='0.9.6.4-unstable.1',eligible=True)
        page.sync()
        assert page.current.v.text().endswith(running)
        manager.pending_restart=True;manager.status='installed'
        manager.pending=dict(channel='unstable',version='0.9.6.4-unstable.1')
        page.sync()
        assert page.current.v.text().endswith(running),'Prepared version is not running yet'
        manager.pending_restart=False;manager.pending={};manager.shutdown();page.close()

personal=dict(theme='lumen_drift',accent='#123456',custom_background='/original/photo.png',
              custom_colors=['#654321'],dashboard_layout={'cpu':1},_appearance_revision=2)
migrated=appearance.migrate(personal)
assert migrated['theme']=='obsidian_gold' and migrated['accent']=='design_default'
assert all(migrated[k]==v for k,v in personal.items() if k not in ('theme','accent'))
assert len(theme.CHOICES)== 6 and 'lumen_drift' not in dict(theme.CHOICES)
theme.set_mode('lumen_drift');assert theme.mode()=='obsidian_gold'
print('Sensor disappearance/recovery, zero RPM, gap-free rows, numeric limits, full running version and retired-design migration PASS')
