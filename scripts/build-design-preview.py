#!/usr/bin/env python3
"""Build and validate a complete portable ZIP for the experimental UI branch.

Only generated files under build/ and dist/ are changed. The original release
runtime is checked against its published SHA-256 manifest before extraction.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import sysconfig
import tempfile
import time
import urllib.request
from zipfile import ZipFile, ZIP_DEFLATED

BASE_VERSION = '0.9.5.4'
REPOSITORY = 'PAAAUUULLOOOH/Vitalux'
DESIGNS = (
    ('obsidian_gold', 'Obsidian-Gold'),
    ('aurora_gold', 'Aurora-Gold'),
)
EXCLUDE = {'__pycache__', '.git', '.venv', 'design-test-data', 'build', '.pytest_cache'}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fetch(url, path):
    temporary = path.with_suffix(path.suffix+'.part')
    with urllib.request.urlopen(url, timeout=90) as response, temporary.open('wb') as output:
        shutil.copyfileobj(response, output)
    temporary.replace(path)


def verified_runtime(cache):
    cache.mkdir(parents=True, exist_ok=True)
    prefix = f'https://github.com/{REPOSITORY}/releases/download/v{BASE_VERSION}/'
    manifest = cache/f'Vitalux-v{BASE_VERSION}-SHA256SUMS.txt'
    archive = cache/f'Vitalux-v{BASE_VERSION}-linux-x86_64.zip'
    fetch(prefix+manifest.name, manifest)
    expected = next(line.split()[0] for line in manifest.read_text().splitlines()
                    if line.split()[-1].lstrip('*') == archive.name)
    if not archive.exists():
        print('Downloading the official portable runtime', flush=True)
        fetch(prefix+archive.name, archive)
    if digest(archive) != expected:
        raise RuntimeError('Official runtime checksum mismatch; refusing to use it')
    print('Official runtime SHA-256 verified', flush=True)
    return archive, manifest


def extract(archive, destination):
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


def prepare(source, stage, manifest):
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo')
    for folder in ('vitalux', 'assets', 'scripts', 'tests', 'packaging'):
        target = stage/folder
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source/folder, target, ignore=ignore)
    for name in ('Designs-testen.sh', 'Obsidian-Gold.sh', 'Aurora-Gold.sh', 'run.sh', 'DESIGN-VORSCHAU.md', 'README.md',
                 'CHANGELOG.md', 'CHANGELOG.en.md'):
        shutil.copy2(source/name, stage/name)
    for name in ('run.sh', 'Designs-testen.sh', 'Obsidian-Gold.sh',
                 'Aurora-Gold.sh'):
        (stage/name).chmod(0o755)
    for name in ('Vitalux-installieren.sh', 'Vitalux-deinstallieren.sh',
                 'README-GITHUB-RELEASE.md'):
        (stage/name).unlink(missing_ok=True)
    shutil.copy2(manifest, stage/'ORIGINAL-SHA256SUMS.txt')

    # The official runtime omits development-only test modules. Add matching
    # trusted modules so the same regressions can also run in the final ZIP.
    import PySide6
    if PySide6.__version__ != '6.12.0':
        raise RuntimeError('Build with the matching PySide6==6.12.0')
    stdlib = stage/'runtime/lib/python3.12'
    shutil.copytree(Path(sysconfig.get_path('stdlib'))/'unittest',
                    stdlib/'unittest', dirs_exist_ok=True, ignore=ignore)
    qt = Path(PySide6.__file__).parent
    bundled = stdlib/'site-packages/PySide6'
    shutil.copy2(qt/'QtTest.abi3.so', bundled/'QtTest.abi3.so')
    shutil.copy2(qt/'Qt/lib/libQt6Test.so.6', bundled/'Qt/lib/libQt6Test.so.6')
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'],
                                     text=True).strip()
    build = {'base_version': BASE_VERSION, 'source_commit': commit,
             'channel': 'experimental/glass-gold-preview', 'official_release': False,
             'designs': [key for key, _ in DESIGNS], 'logo_rotation_seconds': 48}
    (stage/'DESIGN-BUILD.json').write_text(json.dumps(build, indent=2)+'\n')
    (stage/'START-HIER.txt').write_text(
        'Vitalux – experimentelle Designvorschau (Linux x86-64)\n\n'
        'Vollständig in einen eigenen Ordner entpacken.\n'
        'Dann starten: bash Designs-testen.sh\n\n'
        'Direktstarter: Obsidian-Gold.sh, Aurora-Gold.sh.\n'
        'Python und Qt sind enthalten. Getrennte Einstellungen in design-test-data/.\n'
        'Anleitung: DESIGN-VORSCHAU.md. Bildschirmaufnahmen: Vorschauen/.\n')


def check_launchers(stage, env, logs):
    for launcher in ('run.sh', 'Obsidian-Gold.sh', 'Aurora-Gold.sh'):
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


def validate(stage, logs):
    logs.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    env['LD_LIBRARY_PATH'] = str(stage/'lib')
    for key, part in (('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                      ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')):
        env[key] = str(logs/part)
    python = str(stage/'runtime/bin/python3.12')
    subprocess.run([python, 'scripts/run-regressions.py', '--output', str(logs)],
                   cwd=stage, env=env, check=True)
    shutil.copy2(logs/'results.json', stage/'TEST-RESULTS.json')
    check_launchers(stage, env, logs)
    for key, title in DESIGNS:
        subprocess.run([python, 'scripts/capture-design.py', key,
                        f'Vorschauen/{title}.png'], cwd=stage, env=env, check=True, timeout=45)
    subprocess.run([python, 'scripts/capture-design.py', 'obsidian_gold',
                    'Vorschauen/Design-Auswahl.png', '--settings'],
                   cwd=stage, env=env, check=True, timeout=45)
    summary = json.loads((logs/'results.json').read_text())
    (stage/'PRUEFBERICHT.md').write_text(
        '# Prüfung der experimentellen Designvorschau\n\n'
        f'{summary["passed"]} Testskripte bestanden; {summary["failed"]} fehlgeschlagen.\n'
        'Geprüft mit der mitgelieferten Python-/Qt-Laufzeit unter Linux x86-64,\n'
        'Qt offscreen und CPU-Rendering. Alle vier Starter wurden ausgeführt;\n'
        'alle drei Dashboards und die Designauswahl wurden als echte Qt-Fenster\n'
        'mit realen Sensordaten aufgenommen (Vorschauen/).\n\n'
        'Physische GPU-Treiber und eine echte KDE-/Wayland-Sitzung wurden nicht geprüft.\n')


def pack(stage, output):
    output.mkdir(parents=True, exist_ok=True)
    archive = output/f'{stage.name}-linux-x86_64.zip'
    if archive.exists():
        raise FileExistsError(f'Preserve the existing ZIP before rebuilding: {archive}')
    with ZipFile(archive, 'w', ZIP_DEFLATED, compresslevel=6, allowZip64=True) as target:
        for path in sorted(stage.rglob('*')):
            relative = path.relative_to(stage)
            if (path.is_file() and not any(part in EXCLUDE for part in relative.parts)
                    and path.suffix not in ('.pyc', '.pyo', '.log')):
                target.write(path, stage.name+'/'+relative.as_posix())
    with ZipFile(archive) as check:
        if check.testzip() is not None:
            raise RuntimeError('Generated ZIP failed its integrity check')
        for name in ('run.sh', 'Designs-testen.sh', 'runtime/bin/python3.12'):
            if not (check.getinfo(stage.name+'/'+name).external_attr >> 16) & 0o111:
                raise RuntimeError('Executable bit missing: '+name)
    archive.with_suffix('.zip.sha256').write_text(digest(archive)+'  '+archive.name+'\n')
    for path in (stage/'Vorschauen').glob('*.png'):
        shutil.copy2(path, output/path.name)
    for name in ('DESIGN-VORSCHAU.md', 'PRUEFBERICHT.md', 'TEST-RESULTS.json'):
        shutil.copy2(stage/name, output/name)
    print(f'Portable preview ZIP ready: {archive} ({archive.stat().st_size:,} bytes)', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path('build/design-preview/downloads'))
    parser.add_argument('--output', type=Path, default=Path('dist/design-preview'))
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise SystemExit('Use Python 3.12 with PySide6==6.12.0 and psutil==7.2.2')
    source = Path(__file__).resolve().parents[1]
    archive, manifest = verified_runtime(args.cache.resolve())
    (source/'build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='design-preview-', dir=source/'build') as folder:
        directory = Path(folder)
        extract(archive, directory)
        stage = directory/f'Vitalux-v{BASE_VERSION}-Designvorschau'
        (directory/f'Vitalux-v{BASE_VERSION}').rename(stage)
        prepare(source, stage, manifest)
        validate(stage, source/'build/design-preview-checks')
        pack(stage, args.output.resolve())


if __name__ == '__main__':
    main()
