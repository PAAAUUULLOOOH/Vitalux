"""Downloads and installation failures must retain the runnable old version."""
import hashlib
from io import BytesIO
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitalux import settings, updater
from PySide6.QtCore import QCoreApplication
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow


class Response(BytesIO):
    headers = {'Content-Length': '100'}
    def geturl(self):
        return 'https://example.invalid/update.zip'


def run():
    app = QCoreApplication.instance() or QCoreApplication([])
    previous = settings.PATH
    with tempfile.TemporaryDirectory() as folder:
        base = Path(folder)
        settings.PATH = str(base/'settings.json')
        settings.set('theme', 'glass')
        root, source = base/'installed', base/'incoming'
        for parent, value in ((root, 'old'), (source, 'new')):
            (parent/'vitalux').mkdir(parents=True)
            (parent/'vitalux/__main__.py').write_text(value)
            (parent/'run.sh').write_text(value)
        before = Path(settings.PATH).read_bytes()
        with patch.object(updater.shutil, 'disk_usage', return_value=SimpleNamespace(free=0)):
            try:
                updater._install_from_directory(str(source), str(root), lambda _: None)
                raise AssertionError('Low-space installation was accepted')
            except RuntimeError:
                pass
        with patch.object(updater.tempfile, 'mkdtemp', side_effect=PermissionError('Read-only installation')):
            try:
                updater._install_from_directory(str(source), str(root), lambda _: None)
                raise AssertionError('Read-only installation was accepted')
            except PermissionError:
                pass
        with patch.object(updater, '_github_request', return_value=Response(b'short')):
            try:
                updater._download_verified('https://example.invalid/update.zip', str(base/'download.zip'),
                                           hashlib.sha256(b'short').hexdigest(), lambda _: None, 1000)
                raise AssertionError('A truncated transfer was accepted')
            except RuntimeError:
                pass
        original_copy = updater.shutil.copy2
        def failing_copy(src, dst, *args, **kwargs):
            if Path(src) == source/'run.sh':
                raise OSError('Simulated interrupted installation')
            return original_copy(src, dst, *args, **kwargs)
        with patch.object(updater.shutil, 'copy2', side_effect=failing_copy):
            try:
                updater._install_from_directory(str(source), str(root), lambda _: None)
                raise AssertionError('Interrupted installation was reported successful')
            except OSError:
                pass
        assert (root/'vitalux/__main__.py').read_text() == 'old'
        assert (root/'run.sh').read_text() == 'old'
        assert Path(settings.PATH).read_bytes() == before
        settings.PATH = previous
    events = []
    manager = UpdateManager()
    manager.status = 'installed'
    host = SimpleNamespace(manager=manager, restart_requested=False,
                           _force_quit=False, close=lambda: events.append('close'))
    manager.restart.connect(lambda: MainWindow._restart_after_update(host))
    with patch('subprocess.Popen') as spawn:
        manager._restart()
        assert host.restart_requested and events == ['close']
        assert not spawn.called, 'ZIP update started another process before clean shutdown'
    events.clear()
    manager.pending_path = '/tmp/staged-appimage'
    with patch.object(updater, 'activate_appimage_update', side_effect=lambda _: events.append('activate')):
        manager._restart()
    assert events == ['activate', 'close'] and not host.restart_requested
    manager.shutdown()
    print('Update failures: no space, read-only folder, truncated transfer and interrupted install retain old app PASS')


if __name__ == '__main__':
    run()
