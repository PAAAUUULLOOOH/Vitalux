"""The real async install path also auto-restarts after promotion to Stable."""
import hashlib,os,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication
from vitalux import profiles,updater,versions,i18n,update_manager,pages_extra

app=QApplication.instance() or QApplication([])
def settle(condition):
    deadline=time.monotonic()+4
    while not condition() and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
    assert condition(),'Async install did not request its automatic restart'

assert not versions.has_automatic_restart('0.9.6.2')
assert not versions.has_automatic_restart('0.9.6.3-unstable.1')
assert versions.has_automatic_restart('0.9.6.3-unstable.2')
assert versions.has_automatic_restart('0.9.6.3')

with tempfile.TemporaryDirectory(prefix='vitalux-promoted-') as folder,patch.dict(os.environ,{f'XDG_{kind.upper()}_HOME':str(Path(folder)/kind) for kind in profiles.KINDS}):
    # The same code is compiled with a Stable version during promotion.
    for source in ('0.9.6.3-unstable.4','0.9.6.3'):
        for channel,target in (('stable','0.9.6.2'),('unstable','0.9.6.4-unstable.1')):
            with patch.object(update_manager,'__version__',source), \
                    patch.object(profiles,'__version__',source), \
                    patch.object(pages_extra,'__version__',source):
                manager=update_manager.UpdateManager();manager._timer.stop()
                manager._on_checked({channel:dict(ok=True,eligible=True,newer=True,
                    latest=target,channel=channel,url='https://example.invalid/test.zip',
                    sha256=hashlib.sha256(b'candidate').hexdigest(),notes='User changes')})
                manager.set_channel(channel)
                i18n.set_lang('de');page=pages_extra.UpdatePage(manager)
                if channel=='stable' and profiles.installed()=='unstable':
                    assert 'Stable v0.9.6.2' in page.channel_status.text()
                    assert 'Jetzt neu starten' in page.channel_status.text()
                    i18n.set_lang('en');page.sync()
                    assert 'Restart now' in page.channel_status.text()
                restarts=[]
                def restarted():
                    assert QThread.currentThread()==app.thread()
                    restarts.append(manager.pending.copy())
                manager.restart.connect(restarted)
                with patch.object(updater,'install',return_value=None) as install, \
                        patch.object(updater,'appimage_path',return_value=''):
                    manager.install();settle(lambda:bool(restarts))
                settle(lambda:manager.shutdown())
                assert install.call_count==1 and install.call_args.kwargs['defer'] is True
                assert restarts[0]['source_version']==source
                assert restarts[0]['version']==target and restarts[0]['channel']==channel
                assert manager.pending_restart and not manager.available and not manager.can_install
                assert not hasattr(page,'restart_button') and not hasattr(page,'later_button')
                manager._restart();assert len(restarts)==1
                manager._pending_file.unlink(missing_ok=True)
                page.close();manager.deleteLater();app.processEvents()
print('Real install QThread -> GUI timer: both targets, Unstable and promoted Stable, exactly one restart and localized legacy explanation PASS')
