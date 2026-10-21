"""The local preview keeps real preferences intact and never installs updates."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def run():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='vitalux-preview-test-') as directory:
        directory = Path(directory)
        shutil.copytree(root/'vitalux', directory/'vitalux',
                        ignore=shutil.ignore_patterns('__pycache__'))
        real_config = directory/'existing-config'
        (real_config/'vitalux').mkdir(parents=True)
        original = real_config/'vitalux/settings.json'
        original.write_text('{"theme":"light","accent":"#ef4444"}')
        env = os.environ.copy()
        env['PYTHONPATH'] = str(directory)
        env['XDG_CONFIG_HOME'] = str(real_config)
        code = '''
from pathlib import Path
from PySide6.QtWidgets import QApplication
from vitalux.preview import prepare
prepare('aurora_gold')
from vitalux import settings
from vitalux.update_manager import UpdateManager
assert Path(settings.PATH).resolve().is_relative_to(Path('design-test-data').resolve())
assert settings.get('theme') == 'obsidian_gold'
assert settings.get('background_style')=='aurora_gold'
assert settings.get('accent')=='#ecc784'
assert settings.get('render_backend') == 'software'
app = QApplication([])
manager = UpdateManager()
assert manager.status == 'preview' and not manager._timer.isActive()
manager.check()
assert manager._thread is None
manager.status = 'available'
manager.url = 'https://invalid.example/never-download.zip'
manager.install()
assert manager._thread is None
manager.shutdown()
settings.set('theme', 'eclipse_crystal')
prepare()
assert settings.get('theme') == 'eclipse_crystal'
'''
        subprocess.run([sys.executable, '-c', code], cwd=directory,
                       env=env, check=True, timeout=15)
        assert original.read_text() == '{"theme":"light","accent":"#ef4444"}'
    print('Local preview: isolated settings, retained selection, no update check/install PASS')


if __name__ == '__main__':
    run()
