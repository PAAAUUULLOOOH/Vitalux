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


def unpublished_test_version(old, baseline=None, published_assets=None):
    """Retry a failed, unpublished build without skipping its test number."""
    base,test=parse(old)
    if (published_assets is not None and test is not None
            and (not baseline or base>parse(baseline)[0])):
        prefix='Vitalux-v'+old
        if not {prefix+'-linux-x86_64.zip',prefix+'-x86_64.AppImage'}.intersection(published_assets):
            return old
    return next_test_version(old,baseline)


def prepare(dry_run=False,published_assets=None):
    source=ROOT/'vitalux/__init__.py';text=source.read_text()
    old=re.search(r'__version__ = "([^"]+)"',text).group(1)
    stable=subprocess.run(['git','show','origin/main:vitalux/__init__.py'],cwd=ROOT,text=True,capture_output=True)
    match=re.search(r'__version__ = "([^"]+)"',stable.stdout)
    new=unpublished_test_version(old,match.group(1) if match else None,published_assets)
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


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--next',action='store_true')
    parser.add_argument('--published-assets',type=Path)
    args=parser.parse_args()
    assets=set(args.published_assets.read_text().splitlines()) if args.published_assets else None
    prepare(args.next,assets)
