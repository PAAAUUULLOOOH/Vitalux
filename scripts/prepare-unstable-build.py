#!/usr/bin/env python3
"""Advance internal test numbering while retaining authored, test-only notes."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import re,sys,subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from vitalux.versions import parse,channel
from versioning import next_version


def next_test_version(old,baseline=None):
    base,test=parse(old)
    if test is not None and baseline and base<=parse(baseline)[0]:
        return next_version(baseline)+'-unstable.1'
    return next_version(old)+'-unstable.1' if test is None else '.'.join(map(str,base))+f'-unstable.{test+1}'


def prepare(dry_run=False):
    source=ROOT/'vitalux/__init__.py';text=source.read_text()
    old=re.search(r'__version__ = "([^"]+)"',text).group(1)
    stable=subprocess.run(['git','show','origin/main:vitalux/__init__.py'],cwd=ROOT,text=True,capture_output=True)
    match=re.search(r'__version__ = "([^"]+)"',stable.stdout)
    new=next_test_version(old,match.group(1) if match else None)
    if dry_run:print(new);return
    date=datetime.now(ZoneInfo('Europe/Berlin')).date().isoformat();updates={}
    for filename in ('CHANGELOG.md','CHANGELOG.en.md'):
        path=ROOT/filename;contents=path.read_text()
        heading=re.search(r'^## \[v([^]]+)\].*$',contents,re.M)
        if not heading or channel(heading.group(1))!='unstable':
            raise ValueError(filename+': prepend the actual user-visible test changes; Stable notes cannot be copied as new test changes.')
        if parse(heading.group(1))[0]!=parse(new)[0]:
            raise ValueError(filename+': add notes for the next test cycle v'+new)
        updates[path]=contents[:heading.start()]+f'## [v{new}] - {date}'+contents[heading.end():]
    source.write_text(text.replace('"'+old+'"','"'+new+'"',1))
    for path,contents in updates.items():path.write_text(contents)
    print(new)


if __name__=='__main__':prepare('--next' in sys.argv)
