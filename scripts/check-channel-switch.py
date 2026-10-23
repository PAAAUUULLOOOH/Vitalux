#!/usr/bin/env python3
"""Exercise real ZIP channel changes and profile-aware rollback in isolation.

The test package differs only in its version. Only HTTPS transport is replaced;
checksum verification, installation, profile initialization and rollback are real.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED


def child(root, archive, phase):
    sys.path.insert(0, str(root))
    from vitalux import profiles
    profiles.initialize()
    from vitalux import settings, updater
    stable = profiles.directory('config', 'stable')/'settings.json'
    test = profiles.directory('config', 'unstable')/'settings.json'
    if phase == 'enter':
        assert profiles.installed() == 'stable'
        settings.set_many({'lang': 'de', 'interval': 2})
    elif phase == 'leave':
        assert profiles.installed() == 'unstable'
        assert settings.get('lang') == 'de' and settings.get('interval') == 2
        settings.set_many({'lang': 'en', 'interval': 5})
    elif phase == 'rollback':
        assert profiles.installed() == 'stable'
        assert settings.get('lang') == 'de' and settings.get('interval') == 2
        saved = stable.read_bytes()
        updater.restore_previous(str(root))
        assert stable.read_bytes() == saved
        assert profiles.read(test)['lang'] == 'en'
        return
    elif phase == 'restored':
        assert profiles.installed() == 'unstable'
        assert settings.get('lang') == 'en' and settings.get('interval') == 5
        assert profiles.read(stable)['lang'] == 'de'
        assert profiles.read(stable)['interval'] == 2
        assert list((profiles.root('config')/'profile-backups/stable').glob('*/backup.json'))
        assert list((profiles.root('config')/'profile-backups/unstable').glob('*/backup.json'))
        return
    stable_saved, test_saved = stable.read_bytes(), test.read_bytes() if test.exists() else None
    profiles.backup('stable'); profiles.backup('unstable')
    target = 'unstable' if phase == 'enter' else 'stable'
    profiles.select(target)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    url = f'https://github.com/{updater.DEFAULT_REPO}/releases/download/test/{archive.name}'

    class Asset:
        def __enter__(self):
            self.stream = archive.open('rb'); return self
        def __exit__(self, *args): self.stream.close()
        def geturl(self): return url
        headers = {'Content-Length': str(archive.stat().st_size)}
        def read(self, size=-1): return self.stream.read(size)

    updater._github_request = lambda *args, **kwargs: Asset()
    updater.install(url, root=str(root), sha256=digest)
    assert stable.read_bytes() == stable_saved
    if test_saved is not None: assert test.read_bytes() == test_saved
    assert os.access(root/'runtime/bin/python3.12', os.X_OK)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--child', choices=('enter','leave','rollback','restored'))
    parser.add_argument('--root', type=Path)
    args = parser.parse_args()
    if args.child:
        child(args.root.resolve(), args.archive.resolve(), args.child); return
    archive = args.archive.resolve()
    with tempfile.TemporaryDirectory(prefix='vitalux-channel-switch-') as directory:
        directory = Path(directory)
        installation = directory/'application with spaces'
        with ZipFile(archive) as zipped:
            roots = {name.split('/')[0] for name in zipped.namelist()}
            assert len(roots) == 1
            prefix = roots.pop()
            zipped.extractall(directory/'extract')
        shutil.move(directory/'extract'/prefix, installation)
        for script in installation.glob('*.sh'): script.chmod(0o755)
        (installation/'runtime/bin/python3.12').chmod(0o755)
        test_archive = directory/'test-build.zip'
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from versioning import next_version
        with ZipFile(archive) as original:
            current=re.search(rb'__version__ = "([^"]+)"',original.read(prefix+'/vitalux/__init__.py')).group(1).decode()
        test_version=(next_version(current)+'-unstable.1').encode()
        with ZipFile(archive) as original, ZipFile(test_archive,'w',ZIP_DEFLATED,compresslevel=1) as test:
            for item in original.infolist():
                data = original.read(item)
                if item.filename == prefix+'/vitalux/__init__.py':
                    data = re.sub(rb'(__version__ = ")[^"]+',lambda match:match[1]+test_version,data,count=1)
                test.writestr(item,data)
        env = os.environ.copy(); env.pop('APPIMAGE',None)
        for kind in ('CONFIG','STATE','DATA','CACHE'):
            env['XDG_'+kind+'_HOME'] = str(directory/kind.lower())
        for phase, package in (('enter',test_archive),('leave',archive),('rollback',archive),('restored',archive)):
            subprocess.run([sys.executable,str(Path(__file__).resolve()),str(package),
                            '--child',phase,'--root',str(installation)],cwd=directory,
                           env=env,check=True,timeout=180)
            print('PASS channel switch: '+phase,flush=True)
    print('Stable → Unstable → Stable, both profiles, backups and cross-channel rollback PASS',flush=True)


if __name__ == '__main__': main()
