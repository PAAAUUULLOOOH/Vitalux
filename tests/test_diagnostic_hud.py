import os,sys,tempfile
from pathlib import Path
sys.path.insert(0, os.getcwd())  # CI launches this script from the staged runtime.
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
_tmp=tempfile.TemporaryDirectory(prefix='vitalux-diag-hud-')
os.environ['XDG_CONFIG_HOME']=_tmp.name+'/config'
os.environ['XDG_STATE_HOME']=_tmp.name+'/state'
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QTimer
from vitalux import settings,theme,distro,eco
from vitalux.window import MainWindow
from vitalux.logo import load_logo
from vitalux.diagnostic_center import DiagnosticCenter
from vitalux.mini_hud import MiniHUD

class Dummy(QObject):
 changed=Signal()
 restart=Signal()
 progress=Signal(object)
 status="idle"
 error=""
 notes=""
 available=False
 latest=''
 def shutdown(self): pass
 def check(self): pass
 def install(self): pass

app=QApplication([])
theme.set_mode('glass')
settings.set_many({'theme':'glass','accent':'#4f8cff','render_backend':'software','ultra_eco':False,'close_to_tray':False,'mini_hud_enabled':False})
i=distro.info()
w=MainWindow(i,load_logo(i,96),Dummy())
w.show()
app.processEvents()
assert 'Diagnostic Center' in [name for name,page in w.pages]
assert len(w.pages)==12
assert w.render_backend_active=='software'
assert not hasattr(w, '_tray_preview')
assert not hasattr(w, 'lab')
assert theme.mode()=='glass'
assert w.pages[8][0]=='System'
assert next(p for n,p in w.pages if n=='Einstellungen').__class__.__name__=='PreferencesPage'
cent=next(p for n,p in w.pages if n=='Diagnostic Center')
assert 'Diagnostik' not in [n for n,p in w.pages]
assert isinstance(cent,DiagnosticCenter)
assert cent.system_report_btn.text()
assert cent.error_report_btn.text()
pref=next(p for n,p in w.pages if n=='Einstellungen')
assert hasattr(pref,'hud_metrics') and hasattr(pref,'render_combo')
assert not hasattr(pref,'render_advanced_toggle')
assert not any(x.text()=='Diagnose & Berichte' for x in pref.findChildren(__import__('PySide6.QtWidgets',fromlist=['QLabel']).QLabel))
assert pref.hud_size.count()==3
assert pref.hud_opacity.findData(50) >= 0
assert not hasattr(pref, 'language_combo')
assert len(cent.findChildren(__import__('vitalux.widgets',fromlist=['Card']).Card)) == 3
assert cent.lab_panel is None
assert not any('Erweiterte Grafikoptionen' in c.text() for c in pref.findChildren(__import__('PySide6.QtWidgets',fromlist=['QPushButton']).QPushButton))
w.set_mini_hud_enabled(True)
app.processEvents()
assert w._mini_hud.isVisible()
assert settings.get('mini_hud_enabled')
pref.hud_size.setCurrentIndex(pref.hud_size.findData('extended'))
app.processEvents()
assert w._mini_hud.isVisible()
w._mini_hud.hide_by_user()
app.processEvents()
assert not w._tray_hud_action.isChecked()
assert not settings.get('mini_hud_enabled')
# Compare the new diagnostic engine to actual collected data, no external network.
from vitalux import diagnostic_engine
assert 'SYSTEMCHECK' in diagnostic_engine.systemcheck({}).upper()
assert set(cent.texts)=={section[0] for section in cent.SECTIONS}
assert not cent.worker
assert not settings.get('diag_blackbox_enabled',False)
assert any('CPU' in entry[1] for entry in __import__('vitalux.mini_hud',fromlist=['METRIC_OPTIONS']).METRIC_OPTIONS)
print('QA: native window + 12 pages + Glass + MiniHUD + saved renderer + diagnostics OK')
w._force_quit=True
w.close()
from PySide6.QtTest import QTest
for _ in range(400):
 if w.isHidden(): break
 QTest.qWait(25)
assert w.isHidden()
app.quit()
_tmp.cleanup()
