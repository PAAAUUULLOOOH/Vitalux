"""CPU remains drawable and retired renderer settings migrate safely."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from vitalux import renderer,settings
from vitalux.glass import AmbientScene,create_ambient_scene
app=QApplication([])
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    for old in ('opengl','wayland_opengl','wayland_vulkan','qtquick','qt_raster'):
        settings.set_many(dict(render_backend=old,gpu_boot_pending=True,theme='glass'))
        with patch.dict(os.environ,{'VITALUX_RENDERER':''}):assert renderer.prepare_start()==renderer.SOFTWARE
        assert settings.get('render_backend')=='software' and settings.get('theme')=='glass'
        assert not settings.get('gpu_boot_pending')
    scene=create_ambient_scene();scene.resize(320,220);scene.show();app.processEvents()
    assert isinstance(scene,AmbientScene) and not scene.grab().isNull()
    scene.close()
print('CPU framebuffer and safe migration of retired renderer settings PASS')
