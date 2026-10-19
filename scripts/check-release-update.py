#!/usr/bin/env python3
"""Exercise the predecessor's real checksum, ZIP install and rollback code.

Only the network transport is replaced with the locally built official asset.
The old updater performs the actual integrity check, backup and installation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile


def child(root, archive, version):
    sys.path.insert(0, str(root))
    from vitalux import __version__, settings, updater
    previous = __version__
    assert previous != version
    settings.set_many({'lang': 'en', 'accent': '#14b8a6', 'close_to_tray': False})
    saved = Path(settings.PATH).read_bytes()
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    name = archive.name
    url = f'https://github.com/{updater.DEFAULT_REPO}/releases/download/v{version}/{name}'
    updater._get_release = lambda: {
        'tag_name': 'v'+version, 'body': '## Deutsch\nTest\n## English\nTest',
        'assets': [{'name': name, 'browser_download_url': url, 'digest': 'sha256:'+digest}]}
    result = updater.check()
    assert result['ok'] and result['newer'] and result['sha256'] == digest, result

    class Asset:
        def __enter__(self):
            self.stream = archive.open('rb')
            return self
        def __exit__(self, *args):
            self.stream.close()
        def geturl(self):
            return url
        headers = {'Content-Length': str(archive.stat().st_size)}
        def read(self, size=-1):
            return self.stream.read(size)

    updater._github_request = lambda *args, **kwargs: Asset()
    original = (root/'vitalux/__init__.py').read_bytes()
    try:
        updater.install(url, root=str(root), sha256='0'*64)
    except RuntimeError:
        pass
    else:
        raise AssertionError('Corrupt update was accepted')
    assert (root/'vitalux/__init__.py').read_bytes() == original
    assert not (root/'.backup').exists()
    progress = []
    updater.install(url, root=str(root), sha256=digest, progress=progress.append)
    assert f'"{version}"' in (root/'vitalux/__init__.py').read_text()
    assert Path(settings.PATH).read_bytes() == saved
    metadata = json.loads((root/'.backup/metadata.json').read_text())
    assert metadata['version'] == previous and metadata['settings_saved']
    assert progress[-1] == 100 and updater.backup_available(str(root))
    # Older updaters did not preserve modes; run.sh repairs its interpreter.
    subprocess.run(['bash', '-n', str(root/'run.sh')], check=True)
    updater.restore_previous(str(root), restore_settings=True)
    assert (root/'vitalux/__init__.py').read_bytes() == original
    assert Path(settings.PATH).read_bytes() == saved
    assert os.access(root/'runtime/bin/python3.12', os.X_OK)
    print(f'Actual {previous} → {version} updater: checksum rejection, install, settings, backup and rollback PASS', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--child', action='store_true')
    args = parser.parse_args()
    archive = args.archive.resolve()
    with ZipFile(archive) as zipped:
        roots = {name.split('/')[0] for name in zipped.namelist()}
    assert len(roots) == 1
    version = roots.pop().removeprefix('Vitalux-v')
    if args.child:
        child(args.baseline.resolve(), archive, version)
        return
    with tempfile.TemporaryDirectory(prefix='vitalux-release-update-') as folder:
        folder = Path(folder)
        target = folder/'Vitalux previous'
        shutil.copytree(args.baseline.resolve(), target,
                        ignore=shutil.ignore_patterns('__pycache__'))
        env = os.environ.copy()
        env.pop('APPIMAGE', None)
        for key, suffix in (('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                            ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')):
            env[key] = str(folder/suffix)
        subprocess.run([sys.executable, str(Path(__file__).resolve()), str(target),
                        str(archive), '--child'], cwd=folder, env=env, check=True, timeout=180)


if __name__ == '__main__':
    main()
