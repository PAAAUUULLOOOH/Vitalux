"""Verified pending updates resume and retry preparation without another click."""
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from vitalux import __version__,profiles,updater,versions
from vitalux.update_manager import UpdateManager
from vitalux.pages_extra import UpdatePage

app=QApplication.instance() or QApplication([])
base, build = versions.parse(__version__)
target_version = '.'.join(map(str, base))+f'-unstable.{(build or 0)+1}'
def wait_for(condition):
    end=time.monotonic()+7
    while not condition() and time.monotonic()<end:app.processEvents();time.sleep(.01)
    assert condition(),'Automatic restart retries did not settle'

for failures in (1,3):
    with tempfile.TemporaryDirectory(prefix='vitalux-restart-recovery-') as folder:
        base=Path(folder);image=base/'Vitalux.AppImage';image.write_bytes(b'old')
        prepared=base/'prepared.AppImage';prepared.write_bytes(b'verified candidate')
        env={f'XDG_{kind.upper()}_HOME':str(base/kind) for kind in profiles.KINDS}
        env['APPIMAGE']=str(image)
        with patch.dict(os.environ,env):
            initial=UpdateManager();initial.shutdown();pending=initial._pending_file
            state=dict(source_version=__version__,version=target_version,channel='unstable',
                       path=str(prepared),kind='appimage',
                       sha256=hashlib.sha256(prepared.read_bytes()).hexdigest(),
                       activation_error='Previously interrupted preparation')
            profiles.atomic_json(pending,state)
            manager=UpdateManager();page=UpdatePage(manager);page.show()
            assert manager.pending_restart and manager.restart_retrying
            assert page.retry_button.isHidden()
            attempts=[]
            def activate(path,relaunch=True,sha256=None):
                assert path==str(prepared) and relaunch
                assert sha256==state['sha256']
                attempts.append(path)
                if len(attempts)<=failures:raise OSError('Transient helper setup failure')
            def finish():
                manager.shutdown()
                if not manager.prepare_exit():manager.resume_after_shutdown()
            manager.restart.connect(finish)
            with patch.object(updater,'activate_appimage_update',side_effect=activate):
                if failures==1:
                    wait_for(lambda:manager._activation_started)
                    assert len(attempts)==2 and page.retry_button.isHidden()
                else:
                    wait_for(lambda:len(attempts)==3 and not manager.restart_retrying)
                    assert manager.error and not manager._activation_started
                    assert not page.retry_button.isHidden()
                    assert not manager._restart_timer.isActive()
                    manager.set_channel('stable')
                    assert manager.pending['channel']=='unstable' and not manager.available
                    page.retry_button.click()
                    assert manager._activation_started and len(attempts)==4
                manager.finalize_exit()
                assert len(attempts)==failures+1
            assert 'activation_error' not in profiles.read(pending)
            records=[json.loads(line) for line in pending.with_name('restart-events.jsonl').read_text().splitlines()]
            assert sum(row['event']=='activation_preparation_failed' for row in records)==failures
            assert sum(row['event']=='activation_prepared' for row in records)==1
            assert records[-1]['target']==state['version']
            manager.shutdown();page.close()
print('Persisted verified target, automatic bounded retries, terminal-error recovery and single activation PASS')

# A package altered after download must fail before shutdown, retaining both
# the running image and its previous version instead of starting corrupt data.
with tempfile.TemporaryDirectory(prefix='vitalux-changed-stage-') as folder:
    base=Path(folder);image=base/'Vitalux.AppImage';image.write_bytes(b'running image')
    previous=base/'Vitalux.AppImage.previous';previous.write_bytes(b'previous image')
    staged=base/'candidate.AppImage';staged.write_bytes(b'verified download')
    digest=hashlib.sha256(staged.read_bytes()).hexdigest()
    staged.write_bytes(b'changed after download')
    env={f'XDG_{kind.upper()}_HOME':str(base/kind) for kind in profiles.KINDS}
    env['APPIMAGE']=str(image)
    with patch.dict(os.environ,env):
        try:updater.activate_appimage_update(str(staged),sha256=digest)
        except RuntimeError as error:assert 'SHA-256' in str(error)
        else:raise AssertionError('Changed prepared image accepted for activation')
    assert image.read_bytes()==b'running image' and previous.read_bytes()==b'previous image'
print('Changed prepared AppImage rejected before shutdown; running and previous images preserved PASS')
