"""Real warning/update/fallback hooks feed five compact localized local events."""
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from vitalux import events,profiles,i18n,settings,renderer
from vitalux.diagnostic_center import DiagnosticCenter
from vitalux.ui_locale import QMessageBox
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow
from vitalux.alerts import AlertMonitor
app=QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);env={f'XDG_{kind.upper()}_HOME':str(root/kind) for kind in profiles.KINDS}
    with patch.dict(os.environ,env),patch.object(settings,'PATH',str(root/'settings.json')):
        settings.set('alerts_enabled',True)
        class Host:
            _alerts=AlertMonitor();_tray=None
            def statusBar(self):return self
            def showMessage(self,*args):pass
        host=Host()
        MainWindow._check_alerts(host,dict(cpu=dict(temp=96)))
        MainWindow._check_alerts(host,dict(cpu=dict(temp=96)))
        assert len(events.snapshot()[1])==1,'Sustained warning flooded history'
        manager=UpdateManager();manager._on_installed('controlled transfer error')
        manager.shutdown()
        renderer.fallback()
        events.record('renderer_fallback')
        events.flush()
        revision,rows=events.snapshot()
        assert len(rows)==3 and {r['kind'] for r in rows}==events.KINDS
        manager.cancelling=True;manager._on_installed('cancelled transfer')
        assert len(events.snapshot()[1])==3,'Cancelling a download was recorded as a failure'
        for language,expected in (('de','CPU-Rendering aktiviert'),('en','CPU rendering activated')):
            i18n.set_lang(language)
            page=DiagnosticCenter();page.refresh({},{});page.retranslate()
            assert expected in page.recent_events.text()
            assert len(page.recent_events.text().splitlines())==3
            assert 'controlled transfer error' not in page.recent_events.text()
            assert page.texts['all'].toPlainText().startswith('No check performed' if language=='en' else 'Keine Untersuchung')
            with patch.object(QMessageBox, 'information') as notice:
                page.export_report()
                assert notice.called,'An empty diagnostic report was offered for export'
            page.close()
        events.flush();path=profiles.directory('state')/'events.jsonl'
        assert len(path.read_text().splitlines())==3
        other='stable' if profiles.installed()=='unstable' else 'unstable'
        with patch.object(profiles,'__version__','0.9.6.2' if other=='stable' else '0.9.6.3-unstable.9'):
            assert not events.snapshot()[1]
            events.record('update_failed',stage='restart');events.flush()
        assert len(events.snapshot()[1])==3,'Other channel changed event history'
        for n in range(8):events.record('warning',metric='ram_usage',value=91+n,limit=90)
        assert len(events.snapshot()[1])==5
        events.flush()
print('Warning latch, actual update/fallback hooks, DE/EN five-row history, persistence and channel isolation PASS')
