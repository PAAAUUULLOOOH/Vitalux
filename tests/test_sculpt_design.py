"""Private exact-key activation, eight public choices and safe no-GPU lifecycle."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QWidget
from vitalux import design_catalog,settings,theme
from vitalux.control import PreferencesPage
from vitalux.sculpt_host import SculptHost
app=QApplication.instance() or QApplication([])
class Host(QWidget):
    render_backend_active='software';_tray=object()
    def apply_appearance(self,*,before=None):
        theme.set_mode(settings.get('theme'));app.setStyleSheet(theme.stylesheet())
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    settings.set_many(dict(theme='obsidian_gold',motion='off',component_images=False))
    host=Host();page=PreferencesPage(host)
    page.search.setText('tdd');assert settings.get('theme')=='obsidian_gold'
    page.search.setText(' td ');assert settings.get('theme')=='sculpt' and theme.mode()=='sculpt'
    assert len(page.design_tiles)==8 and 'sculpt' not in dict(theme.CHOICES)
    assert page.search.text()==''
    scene=SculptHost();scene.enable(True);assert scene.view is None
    assert scene.shutdown()
    page.select_design('glass');assert settings.get('theme')=='glass'
    page.search.setText('TD');assert settings.get('theme')=='sculpt'
    assert page.shutdown();page.close();host.close();scene.close()
    for name in ('README.md','USER-GUIDE.md','CHANGELOG.md','CHANGELOG.en.md'):
        text=Path(name).read_text().casefold()
        assert 'sculpt' not in text and 'easter egg' not in text
print('Exact private activation, ordinary return, hidden gallery, persisted choice and no-GPU fallback PASS')
