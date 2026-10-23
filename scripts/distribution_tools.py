"""Shared safe release extraction and offline launcher validation."""
import os
from pathlib import Path
import signal
import stat
import subprocess
import time
from zipfile import ZipFile


def extract_release_zip(archive, destination):
    with ZipFile(archive) as source:
        for info in source.infolist():
            path = destination/info.filename
            if not path.resolve().is_relative_to(destination.resolve()):
                raise RuntimeError('Unsafe archive member: '+info.filename)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise RuntimeError('Unexpected symbolic link in release: '+info.filename)
            source.extract(info, destination)
            if path.is_file() and mode & 0o777:
                path.chmod(mode & 0o777)


def check_launchers(stage, env, logs):
    for launcher in ('run.sh', 'Obsidian-Gold.sh', 'Quantum-Core.sh'):
        log = logs/(launcher+'.log')
        with log.open('w') as output:
            process = subprocess.Popen(['bash', str(stage/launcher)], cwd=stage, env=env,
                                       stdout=output, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                deadline = time.monotonic()+30
                while time.monotonic() < deadline:
                    text = log.read_text()
                    if launcher == 'run.sh' and not (stage/'DESIGN-BUILD.json').exists():
                        normal_log = Path(env['XDG_STATE_HOME'])/'vitalux/vitalux.log'
                        if '-unstable.' in (stage/'vitalux/__init__.py').read_text():
                            normal_log=Path(env['XDG_STATE_HOME'])/'vitalux/profiles/unstable/vitalux.log'
                        if normal_log.exists():
                            text += normal_log.read_text()
                    if 'Vitalux: Fensterplattform=offscreen, Grafik-Backend=software' in text:
                        if process.poll() is not None or 'Traceback' in text:
                            raise RuntimeError(text)
                        break
                    if process.poll() is not None:
                        raise RuntimeError(f'{launcher} failed: {text}')
                    time.sleep(.2)
                else:
                    raise RuntimeError(f'{launcher}: startup timed out; see {log}')
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
        print(f'{launcher}: portable startup passed', flush=True)
