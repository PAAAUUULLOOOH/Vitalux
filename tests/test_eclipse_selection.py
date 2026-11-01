"""Public Eclipse selection persists; former search activation has been removed."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from vitalux import settings,theme
from vitalux.control import PreferencesPage
app=QApplication.instance() or QApplication([])
class Host(QWidget):
    render_backend_active='software';_tray=object()
    def apply_appearance(self, *, before=None):theme.set_mode(settings.get('theme'))
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',folder+'/settings.json'):
    settings.set_many(dict(theme='glass',motion='off'))
    host=Host();page=PreferencesPage(host)
    tile=next(t for t in page.design_tiles if t.key=='eclipse_crystal')
    page.show();app.processEvents()
    QTest.mouseClick(tile,Qt.LeftButton);app.processEvents()
    assert theme.mode()==settings.get('theme')=='eclipse_crystal'
    assert tile.isChecked()
    page.select_design('glass')
    for text in ('timbooh',' TIMBOOH '):
        page.search.setText(text);app.processEvents()
        assert theme.mode()==settings.get('theme')=='glass'
        assert page.search.text()==text
    page.select_design('eclipse_crystal')
    settings._cache_identity=None;settings._cache_value=None
    assert settings.get('theme')=='eclipse_crystal'
    page.close();host.close()
print('Public Eclipse gallery selection, persistence and ordinary search PASS')
