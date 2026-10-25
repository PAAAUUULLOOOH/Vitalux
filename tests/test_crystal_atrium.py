"""Archived Atrium composition, static stage, renamed Glass and independent selection."""
import json,os,sys,tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication
from vitalux import brand,crystal_atrium,crystal_glass,premium,settings,theme
from vitalux.design_capabilities import capabilities
from vitalux.widgets import Card,label

app=QApplication.instance() or QApplication([])
assert len(theme.CHOICES)==15
assert dict(theme.CHOICES)['crystal_atrium']=='Crystal Atrium'
assert dict(theme.CHOICES)['crystal_glass']=='Crystal Glass'
for module in (crystal_atrium,crystal_glass):
 assert not capabilities(module.KEY)['background']
 one=(module.scene_pixmap(QSize(500,320),phase=0)).toImage()
 two=(module.scene_pixmap(QSize(500,320),phase=500)).toImage()
 assert one==two and one.pixelColor(10,10)!=one.pixelColor(450,290)
 theme.set_mode(module.KEY);app.setStyleSheet(theme.stylesheet())
 tile=premium.DesignTile(module.KEY);tile.show();app.processEvents();assert not tile.grab().isNull();tile.close()
 card=Card(module.PALETTE['title']);card.body.addWidget(label('Material'));card.resize(480,250);card.show();app.processEvents();assert not card.grab().isNull();card.close()
assert brand._brand_asset(True)=='brand/vitalux-pulse-crystal-glass.svg'
for kind in ('pulse','wordmark'):
 svg=(Path('assets/brand')/f'vitalux-{kind}-crystal-glass.svg').read_text()
 assert 'data-material="glass"' in svg
assert hasattr(crystal_atrium,'AtriumCanvas') and not hasattr(crystal_glass,'AtriumCanvas')
canvas=crystal_atrium.AtriumCanvas('Test distribution',None);canvas.resize(1000,850)
canvas.set_data(dict(cpu=dict(value=25,line1='4.2 GHz',line2='CPU'),gpu=dict(value=40,line1='ASUS TUF GAMING Radeon RX 9060 XT OC Edition with a long full model name',line2='16 GB'),ram=dict(value=35,line1='11 / 32 GB',line2='')))
theme.set_mode('crystal_atrium');app.setStyleSheet(theme.stylesheet());canvas.show();app.processEvents();assert not canvas.grab().isNull()
assert len(canvas._sphere_geo)==3
# Stage pixels are independent of sphere motion/data refresh.
first=crystal_atrium.stage_pixmap(600,400,0).toImage();second=crystal_atrium.stage_pixmap(600,400,100).toImage();assert first==second
canvas.close();assert not canvas._timer.isActive()
previous=settings.PATH
with tempfile.TemporaryDirectory() as directory:
 settings.PATH=str(Path(directory)/'settings.json');Path(settings.PATH).write_text(json.dumps(dict(theme='crystal_atrium',accent='#123456')))
 assert settings.migrate_crystal_designs() and settings.get('theme')=='crystal_glass'
 assert settings.get('accent')=='#123456'
 settings.set('theme','crystal_atrium');assert settings.migrate_crystal_designs() and settings.get('theme')=='crystal_atrium'
settings.PATH=previous
print('Original archived liquid-glass Atrium, static background, Crystal Glass preservation and selected-design migration PASS')
