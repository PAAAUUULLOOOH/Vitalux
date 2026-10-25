"""All visible previews clip artwork, inset checks and preserve distinct designs."""
import os,sys,math,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPointF,Qt
from PySide6.QtGui import QPixmap,QPainter,QRegion
from PySide6.QtWidgets import QApplication,QWidget
from vitalux import theme,settings,design_catalog
from vitalux.premium import DesignTile
from vitalux.gallery_shape import outline,selection_center
app=QApplication.instance() or QApplication([])
images=[];out=Path('build/gallery23');out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
 settings.set_many(dict(accent='design_default',motion='off'))
 for key in design_catalog.VISIBLE:
  tile=DesignTile(key);tile.resize(220,112);tile.setChecked(True);tile._hover=1
  tile.setAttribute(Qt.WA_TranslucentBackground,True);tile.show();app.processEvents()
  path=outline(tile);c=selection_center(tile)
  for angle in range(0,360,15):assert path.contains(c+QPointF(math.cos(math.radians(angle))*8,math.sin(math.radians(angle))*8)),key
  pm=QPixmap(tile.size());pm.fill(Qt.transparent)
  tile.render(pm,renderFlags=QWidget.DrawChildren);image=pm.toImage()
  for x,y in ((0,0),(219,0),(0,111),(219,111),(4,4),(215,4)):assert image.pixelColor(x,y).alpha()==0,(key,x,y)
  assert image.pixelColor(round(c.x()),round(c.y())).alpha()>240
  pm.save(str(out/(key+'.png')));images.append(bytes(image.constBits()));tile.close()
 assert len(set(images))==6
print('Six distinct design previews: matching rounded clipping and check circles fully inset PASS')
