"""Actual window shutdown, automatic updates, worker ordering and retry recovery."""
import hashlib,os,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread
from vitalux import distro,profiles,settings,updater
from vitalux.logo import load_logo
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow

app=QApplication.instance() or QApplication([]);app.setQuitOnLastWindowClosed(False)
def wait_for(condition):
    deadline=time.monotonic()+8
    while not condition() and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
    assert condition(),'Automatic restart/shutdown did not settle'

with tempfile.TemporaryDirectory(prefix='vitalux-auto-update-') as folder,patch.dict(os.environ,{f'XDG_{kind.upper()}_HOME':str(Path(folder)/kind) for kind in profiles.KINDS}):
    with patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
        settings.set_many(dict(close_to_tray=False,motion='off'))
        info=distro.info()
        for target in ('stable','unstable'):
            m=UpdateManager();m._timer.stop();win=MainWindow(info,load_logo(info,96),m);win.show()
            image=Path(folder)/('prepared-'+target+'.AppImage');image.write_bytes(b'candidate')
            events=[];m.restart.connect(lambda:events.append('request'))
            attempts=[]
            def activate(path,relaunch=True,sha256=None):
                assert QThread.currentThread()==app.thread(),'Restart ran outside the GUI thread'
                assert sha256==worker.sha256
                assert not win.sampler.isRunning(),'Activated before live telemetry stopped'
                assert m.shutdown(),'Activated before update workers stopped'
                attempts.append((path,relaunch))
                if len(attempts)==1:raise OSError('Simulated helper launch failure')
            worker=SimpleNamespace(channel=target,version='0.9.6.2' if target=='stable' else '0.9.6.3-unstable.3',pending_path=str(image),kind='appimage',sha256=hashlib.sha256(b'candidate').hexdigest())
            m.channel=target;m.latest=worker.version;m.status='available'
            m.url='https://example.invalid/verified-test.AppImage';m.sha256=worker.sha256
            with patch.object(updater,'activate_appimage_update',side_effect=activate), \
                    patch.object(updater,'install',return_value=str(image)), \
                    patch.object(updater,'appimage_path',return_value=str(Path(folder)/'running.AppImage')):
                m.install()
                m.set_channel('unstable' if target=='stable' else 'stable')
                wait_for(lambda:bool(m.error))
                assert win.isVisible() and win.centralWidget().isEnabled()
                assert m.pending['channel']==target and not m.available and not m.can_install
                page=next(p for name,p in win.pages if name=='Updates')
                assert not hasattr(page,'restart_button') and not hasattr(page,'later_button')
                assert page.retry_button.isHidden() and m.restart_retrying
                wait_for(win.isHidden)
                assert len(attempts)==2 and attempts[-1]==(str(image),True)
                assert events==['request','request'] and m._activation_started
                assert 'activation_error' not in profiles.read(m._pending_file)
                m.finalize_exit();assert len(attempts)==2
            m._pending_file.unlink(missing_ok=True);m.shutdown()
print('Both channel destinations: automatic restart, worker completion, frozen target, failure recovery and exactly one activation PASS')
