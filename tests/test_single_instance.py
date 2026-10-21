"""Real process contention, crash recovery and early second-start rejection."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitalux.single_instance import InstanceGuard


with tempfile.TemporaryDirectory(prefix='vitalux-instance-test-') as folder:
    directory = Path(folder)/'shared'
    holder = """
import os,sys,time
from vitalux.single_instance import InstanceGuard
guard=InstanceGuard(sys.argv[1]);assert guard.acquire()
assert not os.get_inheritable(guard._fd)
print('locked',flush=True)
time.sleep(60)
"""
    child = subprocess.Popen([sys.executable, '-c', holder, str(directory)], stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == 'locked'
        other = InstanceGuard(directory)
        # Different profile/channel directories must not bypass the shared lock.
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(Path(folder)/'other-profile')}):
            assert not other.acquire()
        from vitalux import __main__, profiles, renderer
        with patch('vitalux.single_instance.InstanceGuard', return_value=other), \
             patch('vitalux.single_instance.already_running', return_value=0) as notice, \
             patch.object(profiles, 'initialize') as initialize, \
             patch.object(renderer, 'prepare_start') as prepare:
            try:
                __main__.main()
            except SystemExit as result:
                assert result.code == 0, 'A normal second start must not trigger launcher recovery'
            else:
                raise AssertionError('Second launch was not stopped')
            notice.assert_called_once_with(restarting=False);initialize.assert_not_called();prepare.assert_not_called()
        child.send_signal(signal.SIGKILL);child.wait(timeout=10)
        assert other.acquire(), 'Crash left an unusable instance lock'
        assert not InstanceGuard(directory).acquire()
        other.close()
        # The persistent inode is intentional; a stale filename never blocks restart.
        assert (directory/'instance.lock').exists()
        restarted = InstanceGuard(directory);assert restarted.acquire();restarted.close()
    finally:
        if child.poll() is None:child.kill()
        child.wait(timeout=10)

    # Executed update/probe children must not prolong the parent's lock lifetime.
    launcher = """
import subprocess,sys
from vitalux.single_instance import InstanceGuard
guard=InstanceGuard(sys.argv[1]);assert guard.acquire()
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],close_fds=False,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(child.pid,flush=True)
"""
    worker_pid = int(subprocess.check_output([sys.executable,'-c',launcher,str(directory)],text=True,timeout=10))
    try:
        fresh=InstanceGuard(directory)
        assert fresh.acquire(),'An executed helper inherited the instance lock'
        fresh.close()
    finally:
        try:os.kill(worker_pid,signal.SIGTERM)
        except ProcessLookupError:pass

    # Check the actual modal notice and both translations without profile writes.
    notice_script = """
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication,QMessageBox
from vitalux import settings
from vitalux.single_instance import already_running
settings.get=lambda key:sys.argv[1]
app=QApplication([])
expected='Vitalux läuft bereits.' if sys.argv[1]=='de' else 'Vitalux is already running.'
def accept():
    dialog=app.activeModalWidget()
    if dialog is None:QTimer.singleShot(10,accept);return
    assert isinstance(dialog,QMessageBox) and dialog.text()==expected,dialog.text()
    dialog.accept()
QTimer.singleShot(0,accept)
assert already_running()==0
"""
    for language in ('de','en'):
        subprocess.run([sys.executable,'-c',notice_script,language],check=True,timeout=20)

    restarting_script="""
import sys,time
from vitalux.single_instance import InstanceGuard
guard=InstanceGuard(sys.argv[1]);assert guard.acquire()
guard.mark_restarting();print('restarting',flush=True);time.sleep(.4)
"""
    process=subprocess.Popen([sys.executable,'-c',restarting_script,str(directory)],stdout=subprocess.PIPE,text=True)
    try:
        assert process.stdout.readline().strip()=='restarting'
        waiting=InstanceGuard(directory)
        assert not waiting.acquire(wait=.01,restart_wait=.05) and waiting.restarting
        successor=InstanceGuard(directory)
        assert successor.acquire(wait=.01,restart_wait=2),'Restart successor was rejected during clean shutdown'
        assert process.poll() is not None and not successor.restarting
        duplicate=InstanceGuard(directory)
        assert not duplicate.acquire(wait=.01) and not duplicate.restarting
        successor.close()
    finally:
        if process.poll() is None:process.kill()
        process.wait(timeout=10)

    # Never follow a substituted lock file outside the protected directory.
    unsafe=Path(folder)/'unsafe';unsafe.mkdir(mode=0o700)
    (unsafe/'instance.lock').symlink_to(Path(folder)/'unrelated')
    try:InstanceGuard(unsafe).acquire()
    except OSError:pass
    else:raise AssertionError('Followed a substituted instance-lock symlink')

print('Single-instance contention, profile independence, early exit, crash/restart and DE/EN notices PASS')
