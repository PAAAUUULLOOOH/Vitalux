#!/usr/bin/env python3
"""Merge a published Stable baseline into Unstable without overwriting work."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def git(*args,check=True):
    return subprocess.run(['git',*args],cwd=ROOT,check=check,text=True,capture_output=True)


def sync():
    # The rolling tag and development branch share a name. Always fetch heads.
    git('fetch','origin','refs/heads/main:refs/remotes/origin/main',
        'refs/heads/unstable:refs/remotes/origin/unstable')
    git('checkout','-B','unstable','origin/unstable')
    current=(ROOT/'vitalux/__init__.py').read_text()
    result=git('merge','--no-ff','--no-commit','origin/main',check=False)
    if result.returncode:
        conflicts=git('diff','--name-only','--diff-filter=U').stdout.splitlines()
        if conflicts==['vitalux/__init__.py']:
            # Test numbering is advanced by its own build; preserve ongoing test identity.
            (ROOT/'vitalux/__init__.py').write_text(current);git('add','vitalux/__init__.py')
        else:
            git('merge','--abort',check=False)
            raise RuntimeError('Unstable/main need a reviewed merge: '+', '.join(conflicts))
    if (ROOT/'.git/MERGE_HEAD').exists():git('commit','-m','Merge published Stable baseline into unstable')
    git('push','origin','HEAD:refs/heads/unstable')


if __name__=='__main__':sync()
