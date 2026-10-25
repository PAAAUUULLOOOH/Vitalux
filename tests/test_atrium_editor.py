"""Atrium uses one scene and the real save/undo/hide/reorder dashboard editor."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint,Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QVBoxLayout
from vitalux import settings,theme
from vitalux.glass import AmbientScene
from vitalux.pages import OverviewPage
ns={'__file__':str(Path(__file__).with_name('test_component_charts.py'))}
src=Path(ns['__file__']).read_text();exec(src[:src.index('with tempfile.TemporaryDirectory()')],ns)
app=ns['app'];sample=ns['sample'];sample['disks'][0]['fstype']='ext4'
with tempfile.TemporaryDirectory() as directory,patch.object(settings,'PATH',str(Path(directory)/'settings.json')):
 settings.set_many(dict(theme='crystal_atrium',accent='design_default',motion='off',background_style='theme_default'))
 theme.set_mode('crystal_atrium');app.setStyleSheet(theme.stylesheet())
 scene=AmbientScene();scene.resize(1180,1500);layout=QVBoxLayout(scene);layout.setContentsMargins(0,0,0,0)
 logo=QPixmap(96,96);logo.fill(Qt.transparent)
 page=OverviewPage(dict(name='Test Linux',version='1'),logo);layout.addWidget(page)
 scene.show();app.processEvents();page.refresh(sample,{k:[1,10,20] for k in ('cpu','gpu','ram','net_down','net_up')});app.processEvents()
 assert page.layout_toggle.isVisible() and page.board.isVisible()
 assert set(page.board._last_targets)==set(page.atrium_tiles)
 assert all(tile.isVisible() for tile in page.atrium_tiles.values())
 assert not scene._wallpaper_timer.isActive()
 picture=scene.grab();assert not picture.isNull()
 output=Path('build/atrium25');output.mkdir(parents=True,exist_ok=True);picture.save(str(output/'overview.png'))
 # A gap between glass tiles must show exactly the same scene pixels as the
 # outside margin, rather than a second independently scaled stage.
 cpu=page.board.tiles['cpu'].geometry();gpu=page.board.tiles['gpu'].geometry()
 point=page.board.mapTo(scene,QPoint((cpu.right()+gpu.left())//2,cpu.center().y()))
 ratio=scene.devicePixelRatioF();sharp=scene.sharp_backdrop().toImage();actual=picture.toImage()
 px,py=round(point.x()*ratio),round(point.y()*ratio)
 assert actual.pixelColor(px,py)==sharp.pixelColor(px,py)
 for key in ('cpu','gpu','ram'):
  tile=page.atrium_tiles[key]
  assert len(tile._sphere_meta)==1
  assert tile._blur.devicePixelRatioF()==ratio
  assert tile._blur.width()>=round(tile.width()*ratio)-1
 positions={key:tile.geometry() for key,tile in page.board.tiles.items() if tile.isVisible()}
 page.toggle_editor();app.processEvents()
 assert page.board.editing and page.layout_actions.isVisible()
 assert positions=={key:tile.geometry() for key,tile in page.board.tiles.items() if tile.isVisible()}
 gpu=page.board.tiles['gpu'];cpu=page.board.tiles['cpu']
 page.board.begin_drag('gpu',gpu.mapToGlobal(gpu.rect().center()))
 page.board.drag_to(cpu.mapToGlobal(QPoint(10,cpu.height()//2)))
 page.board.end_drag();app.processEvents()
 assert page.board.order.index('gpu')<page.board.order.index('cpu')
 assert len(page.board.order)==10
 page.board.undo();page.board.hide_tile('ram');page.board.hide_distro_logo();app.processEvents()
 assert page.board.tiles['ram'].isHidden() and not page.atrium_tiles['hero'].logo_visible
 assert ('ram','Arbeitsspeicher') in page.board.available_hidden()
 page.discard_edit();app.processEvents()
 assert 'ram' not in page.board.hidden and page.atrium_tiles['hero'].logo_visible
 page.toggle_editor();page.board.hide_tile('gpu');page.save_editor();app.processEvents()
 assert 'gpu' in settings.get('dashboard_hidden') and not page.board.editing
 page.toggle_editor();page.board.show_tile('gpu');page.reset_editor();app.processEvents()
 assert not settings.get('dashboard_hidden') and len(page.board._last_targets)==7
 page.toggle_editor();scene.grab().save(str(output/'editor.png'));page.save_editor()
 scene.close()
print('Atrium shared scene, full-resolution glass, retained spheres, editor reorder/hide/undo/cancel/save/reset PASS')

from vitalux.startup import StartupWindow
splash=StartupWindow();splash.show();app.processEvents()
image=splash.grab().toImage()
assert image.pixelColor(0,0).alpha()==0 and image.pixelColor(3,3).alpha()==0
assert image.pixelColor(image.width()//2,image.height()//2).alpha()>240
splash.ready=True;splash.close()
print('Startup outline has actual transparent rounded corners PASS')
