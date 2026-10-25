#!/usr/bin/env python3
"""Merge a published Stable baseline into Unstable without overwriting work."""
import subprocess,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vitalux.versions import key


def git(*args,check=True):
    return subprocess.run(['git',*args],cwd=ROOT,check=check,text=True,capture_output=True)


def merge_changelog(ours,theirs):
    pattern=re.compile(r'^## \[v([^]]+)\].*$',re.M)
    entries={}
    for source in (ours,theirs):
        headings=list(pattern.finditer(source))
        for index,heading in enumerate(headings):
            end=headings[index+1].start() if index+1<len(headings) else len(source)
            block=source[heading.start():end].strip()
            version=heading.group(1)
            if version in entries and '\n'.join(entries[version].splitlines()[1:]).strip()!='\n'.join(block.splitlines()[1:]).strip():
                raise ValueError('Different changes for the same published version: '+version)
            entries[version]=block
    first=pattern.search(theirs)
    if not first:raise ValueError('Missing changelog headings')
    return theirs[:first.start()]+('\n\n'.join(entries[version] for version in sorted(entries,key=key,reverse=True)))+'\n'


def sync():
    # The rolling tag and development branch share a name. Always fetch heads.
    git('fetch','origin','refs/heads/main:refs/remotes/origin/main',
        'refs/heads/unstable:refs/remotes/origin/unstable')
    git('checkout','-B','unstable','origin/unstable')
    result=git('merge','--no-ff','--no-commit','origin/main',check=False)
    if result.returncode:
        conflicts=git('diff','--name-only','--diff-filter=U').stdout.splitlines()
        allowed={'vitalux/__init__.py','CHANGELOG.md','CHANGELOG.en.md'}
        if not conflicts or not set(conflicts)<=allowed:
            git('merge','--abort',check=False)
            raise RuntimeError('Unstable/main need a reviewed merge: '+', '.join(conflicts))
        try:
            for filename in conflicts:
                if filename=='vitalux/__init__.py':content=git('show',':3:'+filename).stdout
                else:
                    ours=git('show',':2:'+filename).stdout
                    theirs=git('show',':3:'+filename).stdout
                    content=merge_changelog(ours,theirs)
                (ROOT/filename).write_text(content);git('add',filename)
        except Exception:
            git('merge','--abort',check=False);raise
    if git('rev-parse','-q','--verify','MERGE_HEAD',check=False).returncode==0:git('commit','-m','Merge published Stable baseline into unstable')
    git('push','origin','HEAD:refs/heads/unstable')


if __name__=='__main__':sync()
