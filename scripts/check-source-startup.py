#!/usr/bin/env python3
"""Exercise GitHub's source-ZIP layout without a venv or installed Python/Qt."""
import os
from pathlib import Path
from distribution_tools import check_launchers
import subprocess
import tempfile
from zipfile import ZipFile


def main():
    source = Path(__file__).resolve().parents[1]
    (source/'build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='source ZIP test ', dir=source/'build') as folder:
        folder = Path(folder)
        archive = folder/'source.zip'
        subprocess.run(['git', 'archive', '--format=zip', '--prefix=Vitalux source/',
                        '-o', str(archive), 'HEAD'], cwd=source, check=True)
        with ZipFile(archive) as zipped:
            zipped.extractall(folder)
        stage = folder/'Vitalux source'
        assert not (stage/'.venv').exists() and not (stage/'runtime').exists()
        assert (stage/'portable-runtime/vitalux-linux-x86_64.tar.xz').stat().st_size > 1_000_000
        # Any attempt to use system Python or pip must fail. Only the bundled
        # interpreter may be used by the actual user-facing launchers.
        blockers = folder/'no system Python'
        blockers.mkdir()
        marker = blockers/'unexpected-python-call'
        for name in ('python', 'python3', 'python3.12', 'pip', 'pip3'):
            path = blockers/name
            path.write_text('#!/bin/sh\ntouch "'+str(marker)+'"\nexit 99\n')
            path.chmod(0o755)
        env = os.environ.copy()
        env['PATH'] = str(blockers)+os.pathsep+env['PATH']
        env['QT_QPA_PLATFORM'] = 'offscreen'
        for key, part in (('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                          ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')):
            env[key] = str(folder/part)
        # Reject a bad checksum before installing anything.
        manifest = stage/'portable-runtime/SHA256SUMS'
        correct = manifest.read_text()
        manifest.write_text('0'*64+'  vitalux-linux-x86_64.tar.xz\n')
        failed = subprocess.run(['bash', 'run.sh'], cwd=stage, env=env,
                                text=True, capture_output=True, timeout=30)
        assert failed.returncode != 0 and 'beschädigt' in failed.stderr, failed
        assert not (stage/'runtime').exists()
        manifest.write_text(correct)

        logs = source/'build/source-startup-checks'
        logs.mkdir(exist_ok=True)
        check_launchers(stage, env, logs)
        assert 'einmalig entpackt' in (logs/'run.sh.log').read_text()
        assert 'einmalig entpackt' not in (logs/'Obsidian-Gold.sh.log').read_text()
        assert not marker.exists(), 'Launcher used system Python/pip'
        assert (stage/'runtime/bin/python3.12').is_file()
        env['LD_LIBRARY_PATH'] = str(stage/'lib')
        subprocess.run([str(stage/'runtime/bin/python3.12'), '-c',
                        'from PySide6.QtCore import QCoreApplication; '
                        'from vitalux.update_manager import UpdateManager; '
                        'app=QCoreApplication([]); m=UpdateManager(); '
                        'assert m.status=="idle" and m._timer.isActive()'],
                       cwd=stage, env=env, check=True, timeout=20)
        subprocess.run([str(stage/'runtime/bin/python3.12'),
                        'scripts/capture-design.py', 'obsidian_gold',
                        str(logs/'Source-ZIP.png')], cwd=stage, env=env, check=True, timeout=45)
        print('Source ZIP: verified offline runtime extraction, all three launchers, '
              'repeat launch, real window and live sensor data PASS', flush=True)


if __name__ == '__main__':
    main()
