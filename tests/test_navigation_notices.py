"""Every navigation renderer shows real update motion and a static fallback."""
import os, sys, tempfile, math
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from vitalux import settings, theme
from vitalux.widgets import NavButton

app=QApplication([])
app.setQuitOnLastWindowClosed(False)
checks=0
with tempfile.TemporaryDirectory() as directory, patch.object(settings,'PATH',directory+'/settings.json'):
    for mode in [key for key,_ in theme.CHOICES]+['eclipse_crystal','minimal']:
        settings.set_many(dict(theme=mode,motion='smooth',ultra_eco=mode=='minimal',accent='design_default'))
        theme.set_mode(mode);app.setStyleSheet(theme.stylesheet())
        for compact in (False,True):
            for selected in (False,True):
                button=NavButton('↻    Updates');button.setCheckable(True);button.setChecked(selected)
                button.set_compact(compact);button.set_update_version('v0.9.6.4-unstable.9')
                button.resize(54 if compact else 235,48);button.show();app.processEvents();button.clearFocus()
                button.set_glow(True);button._timer.stop()
                button._phase=-math.pi/2;dim=button.grab().toImage()
                button._phase=math.pi/2;bright=button.grab().toImage()
                if mode!='minimal':
                    changed=sum(abs(a-b)>12 for a,b in zip(dim.constBits(),bright.constBits()))
                    assert changed>60,(mode,compact,selected,'Update pulse was barely visible',changed)
                for motion in ('reduced','off'):
                    settings.set('motion',motion);button.set_glow(True)
                    assert not button._timer.isActive(),(mode,motion,'Static preference retained a timer')
                    button._phase=-math.pi/2;first=button.grab().toImage()
                    button._phase=math.pi/2;assert first==button.grab().toImage()
                    button.set_glow(False)
                    persistent=button.grab().toImage()
                    button.set_update_version('');empty=button.grab().toImage()
                    assert persistent!=empty,(mode,compact,'Update marker disappeared with animations off')
                    button.set_update_version('v0.9.6.4-unstable.9')
                settings.set('motion','smooth');button.set_glow(True)
                button.hide();assert not button._timer.isActive()
                button.show();assert button._timer.isActive()==(mode!='minimal')
                assert '0.9.6.4-unstable.9' in button.accessibleDescription()
                button.close();button.deleteLater();app.processEvents();checks+=1
print(f'{checks} all-design, selected and compact update indicators: visible pulse, persistent static marker and hidden timer stop PASS')
