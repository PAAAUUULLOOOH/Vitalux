"""Compare application content and ancestry, ignoring release/build bookkeeping."""
import hashlib
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def git(*args,root=ROOT,check=True):
    return subprocess.run(['git',*args],cwd=root,check=check,capture_output=True)


def fingerprint(ref,root=ROOT):
    paths=git('ls-tree','-r','--name-only',ref,'--','vitalux','assets','run.sh','packaging/AppRun',
              'packaging/appimage-first-run.py','packaging/appimage-integration.sh',
              'packaging/appimage-rollback-watch.sh','packaging/appimage-activate.py','packaging/logging.sh',
              'packaging/restart-request.py','packaging/runtime-libraries.py',
              'packaging/game-overlay.sh','packaging/mangohud-launch.sh',
              'scripts/ensure-runtime.sh','portable-runtime/SHA256SUMS',
              'portable-runtime/desktop-libraries.SHA256SUMS','portable-runtime/mangohud.json',root=root).stdout.decode().splitlines()
    digest=hashlib.sha256()
    for path in paths:
        if path.startswith('assets/') and ('-preview.' in path or '-readme-' in path):continue
        data=git('show',ref+':'+path,root=root).stdout
        if path=='vitalux/__init__.py':data=re.sub(rb'(__version__\s*=\s*)"[^"]+"',rb'\1"BUILD"',data)
        digest.update(path.encode()+b'\0'+len(data).to_bytes(8,'big')+data)
    return digest.hexdigest()


def describe(ref='HEAD',main='origin/main',root=ROOT):
    source=git('show',main+':vitalux/__init__.py',root=root).stdout.decode()
    version=re.search(r'__version__ = "([^"]+)"',source).group(1)
    stable_commit=git('rev-parse',main,root=root).stdout.decode().strip()
    test_fingerprint=fingerprint(ref,root);stable_fingerprint=fingerprint(main,root)
    incorporates_main=git('merge-base','--is-ancestor',main,ref,root=root,check=False).returncode==0
    contained=git('merge-base','--is-ancestor',ref,main,root=root,check=False).returncode==0
    return dict(stable_contains_test=contained or test_fingerprint==stable_fingerprint,stable_version=version,stable_commit=stable_commit,
                app_fingerprint=test_fingerprint,stable_fingerprint=stable_fingerprint,
                same_as_stable=test_fingerprint==stable_fingerprint,
                has_test_changes=incorporates_main and test_fingerprint!=stable_fingerprint)


if __name__=='__main__':
    import json
    print(json.dumps(describe(),indent=2))
