#!/usr/bin/env python3
"""Advance test numbering without consuming another Stable release number."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import re,sys,subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from vitalux.versions import parse
from versioning import next_version


def prepare():
    source=ROOT/'vitalux/__init__.py';text=source.read_text()
    old=re.search(r'__version__ = "([^"]+)"',text).group(1)
    base,test=parse(old)
    stable=subprocess.run(['git','show','origin/main:vitalux/__init__.py'],cwd=ROOT,text=True,capture_output=True)
    match=re.search(r'__version__ = "([^"]+)"',stable.stdout)
    baseline=match.group(1) if match else None
    if test is not None and baseline and base<=parse(baseline)[0]:
        new=next_version(baseline)+'-unstable.1'
    else:new=(next_version(old)+'-unstable.1') if test is None else '.'.join(map(str,base))+f'-unstable.{test+1}'
    source.write_text(text.replace('"'+old+'"','"'+new+'"',1))
    date=datetime.now(ZoneInfo('Europe/Berlin')).date().isoformat()
    for filename in ('CHANGELOG.md','CHANGELOG.en.md'):
        path=ROOT/filename;contents=path.read_text()
        heading=re.search(r'^## \[v[^]]+\].*$',contents,re.M)
        next_heading=re.search(r'^## \[v',contents[heading.end():],re.M)
        end=heading.end()+next_heading.start() if next_heading else len(contents)
        body=contents[heading.end():end].strip()
        new_heading=f'## [v{new}] - {date}\n'
        if test is not None:contents=contents[:heading.start()]+new_heading+contents[heading.end():]
        else:contents=contents[:heading.start()]+new_heading+body+'\n\n'+contents[heading.start():]
        path.write_text(contents)
    print(new)


if __name__=='__main__':prepare()
