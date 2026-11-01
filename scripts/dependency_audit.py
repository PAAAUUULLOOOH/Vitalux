#!/usr/bin/env python3
"""Audit pinned runtime dependencies before a release; never mutate an install."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from ubuntu_dependencies import UbuntuArchive

ROOT=Path(__file__).resolve().parents[1]


def version(value):
    if not re.fullmatch(r'\d+(?:\.\d+)+',value):raise ValueError('Not a stable dependency version: '+value)
    return tuple(map(int,value.split('.')))


def python_compatible(requirement,python=(3,12,0)):
    for part in (requirement or '').split(','):
        if not part.strip():continue
        match=re.fullmatch(r'\s*(>=|<=|!=|==|>|<|~=)\s*(\d+(?:\.\d+)*(?:\.\*)?)\s*',part)
        if not match:raise ValueError('Review unsupported Python constraint: '+part)
        operator,text=match.groups();wildcard=text.endswith('.*')
        numbers=tuple(map(int,text.removesuffix('.*').split('.')))
        if wildcard:
            equal=python[:len(numbers)]==numbers
            if operator not in ('==','!='):raise ValueError('Invalid wildcard constraint')
            if equal!=(operator=='=='):return False
            continue
        target=(*numbers,*(0 for _ in range(max(0,3-len(numbers)))))
        checks={'>=':python>=target,'>':python>target,'<=':python<=target,'<':python<target,'==':python==target,'!=':python!=target}
        if operator=='~=':
            prefix=numbers[:-1]
            if python<target or python[:len(prefix)]!=prefix:return False
        elif not checks[operator]:return False
    return True


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,message,headers,newurl):
        redirected=super().redirect_request(request,fp,code,message,headers,newurl)
        if redirected is not None and (urlsplit(newurl).scheme,urlsplit(newurl).hostname)!=('https','api.github.com'):redirected.remove_header('Authorization')
        return redirected


def fetch(url):
    headers={'User-Agent':'Vitalux-dependency-audit','Accept':'application/json'}
    token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token and (urlsplit(url).scheme,urlsplit(url).hostname)==('https','api.github.com'):headers['Authorization']='Bearer '+token
    request=urllib.request.Request(url,headers=headers)
    with urllib.request.build_opener(SafeRedirect()).open(request,timeout=45) as stream:return json.load(stream)


def pins(root=ROOT):
    return dict(re.findall(r'^([A-Za-z0-9_-]+)==([^\s#]+)$',(root/'requirements-dev.txt').read_text(),re.M))


def pypi_component(item,read=fetch,python=(3,12,0)):
    name,current=item;data=read('https://pypi.org/pypi/'+name+'/json')
    branch=version(current)[:2 if name=='PySide6-Essentials' else 1]
    candidates=[]
    for candidate,files in data['releases'].items():
        try:parts=version(candidate)
        except ValueError:continue
        if parts[:len(branch)]!=branch or not files:continue
        if any(not file.get('yanked') and python_compatible(file.get('requires_python'),python) for file in files):candidates.append(candidate)
    if not candidates:raise ValueError('No compatible stable package: '+name)
    latest=max(candidates,key=version)
    installed=read('https://pypi.org/pypi/'+name+'/'+current+'/json')
    vulnerabilities=[entry for entry in installed.get('vulnerabilities',[]) if not entry.get('withdrawn')]
    return dict(name=name,current=current,latest=latest,upstream_latest=data['info']['version'],
                update=version(latest)>version(current),automatic=True,kind='pypi',vulnerabilities=vulnerabilities)


def python_component(current,read=fetch):
    branch='.'.join(current.split('.')[:2])
    refs=read('https://api.github.com/repos/python/cpython/git/matching-refs/tags/v'+branch+'.')
    candidates=[]
    for ref in refs:
        candidate=ref['ref'].removeprefix('refs/tags/v')
        try:version(candidate)
        except ValueError:continue
        if candidate.startswith(branch+'.'):candidates.append(candidate)
    if not candidates:raise ValueError('No stable CPython patch release found')
    latest=max(candidates,key=version)
    return dict(name='cpython',current=current,latest=latest,update=version(latest)>version(current),automatic=True,kind='cpython')


def source_watch(entry,read=fetch):
    """Track compiled upstream components; an ABI change requires review/rebuild."""
    match=re.match(r'https://github.com/([^/]+/[^/]+)',entry.get('url',''))
    if not match:return dict(name=entry['name'],current=entry['version'],kind='source',automatic=False,note='Tracked by locked source and baseline security packages')
    repository=match.group(1)
    try:data=read('https://api.github.com/repos/'+repository+'/releases/latest')
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
        tags=read('https://api.github.com/repos/'+repository+'/tags?per_page=100')
        data=dict(tag_name=tags[0]['name'] if tags else '')
    tag=data.get('tag_name','');numeric=re.search(r'(\d+(?:[.-]\d+)+)$',tag)
    text=numeric.group(1).replace('-','.') if numeric else ''
    latest=None
    try:version(text);latest=text
    except ValueError:pass
    update=False
    try:update=latest is not None and version(latest)>version(entry['version'])
    except ValueError:pass
    return dict(name=entry['name'],current=entry['version'],latest=latest,upstream_tag=tag,
                update=update,automatic=False,kind='source',note='New compiled upstream versions require an ABI-aware rebuild and validation')


def audit(root=ROOT,ubuntu=None,read=fetch):
    records=json.loads((root/'third_party/sources.lock.json').read_text())
    direct=[entry for entry in records if 'archive.ubuntu.com/ubuntu/pool/' not in entry.get('url','') and 'security.ubuntu.com/ubuntu/pool/' not in entry.get('url','')]
    python=next(entry['version'] for entry in records if entry['name']=='cpython')
    requirements=pins(root)
    for name in ('PySide6-Essentials','psutil'):
        if name not in requirements:raise ValueError('Required Python dependency is not pinned: '+name)
    python_release=python_component(python,read)
    work=[lambda:python_release]
    work += [lambda item=item:pypi_component(item,read,version(python_release['latest'])) for item in requirements.items()]
    work += [lambda entry=entry:source_watch(entry,read) for entry in direct if entry['name'] not in ('cpython','pyside-setup','psutil','qtbase','qtdeclarative','qtsvg','qtwayland','qtimageformats')]
    with ThreadPoolExecutor(max_workers=4) as pool:components=list(pool.map(lambda call:call(),work))
    metadata=json.loads((root/'licenses/system-libraries/desktop-libraries.json').read_text())
    packages={entry['package']:entry['version'] for entry in metadata['libraries']}
    if ubuntu:
        ubuntu.refresh();ubuntu.cache_packages(packages)
        for package,current in sorted(packages.items()):
            candidate=ubuntu.package(package)
            compared=__import__('subprocess').run(['dpkg','--compare-versions',candidate['Version'],'gt',current]).returncode==0
            components.append(dict(name=package,current=current,latest=candidate['Version'],kind='ubuntu',automatic=True,update=compared,package=candidate['Package'],signed_metadata=True))
    else:
        components += [dict(name=name,current=current,kind='ubuntu',automatic=True,checked=False) for name,current in sorted(packages.items())]
    return dict(schema=1,checked_at=datetime.now(timezone.utc).isoformat(),python_branch='3.12',
        baseline=metadata['build_base'],ubuntu_checked=ubuntu is not None,components=components,
        updates=[component for component in components if component.get('update') and component['automatic']],
        review=[component for component in components if component.get('update') and not component['automatic']],
        vulnerabilities=[dict(package=component['name'],advisory=advisory) for component in components for advisory in component.get('vulnerabilities',[])])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/dependencies/audit.json')
    parser.add_argument('--ubuntu',action='store_true')
    parser.add_argument('--apt-work',type=Path,default=ROOT/'build/dependencies/apt')
    parser.add_argument('--keyring',type=Path,default=Path('/usr/share/keyrings/ubuntu-archive-keyring.gpg'))
    parser.add_argument('--enforce',action='store_true')
    args=parser.parse_args()
    report=audit(ubuntu=UbuntuArchive(args.apt_work,args.keyring) if args.ubuntu else None)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(checked=len(report['components']),updates=[(r['name'],r['latest']) for r in report['updates']],review=[(r['name'],r.get('latest')) for r in report['review']],vulnerabilities=len(report['vulnerabilities']))))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as summary:
            summary.write('### Runtime dependency audit\n\n| Component | Pinned | Candidate | Status |\n| --- | --- | --- | --- |\n')
            for entry in report['components']:
                state='Update' if entry.get('update') and entry['automatic'] else 'ABI review' if entry.get('update') else 'Checked' if entry.get('checked',True) else 'Not checked'
                summary.write('| '+entry['name']+' | '+entry['current']+' | '+str(entry.get('latest') or entry.get('upstream_tag') or 'Locked ABI')+' | '+state+' |\n')
            summary.write('\nActive PyPI advisories: '+str(len(report['vulnerabilities']))+'. Corresponding sources and binary versions must match before publication.\n')
    if args.enforce and (report['updates'] or report['vulnerabilities']):raise SystemExit('Dependency maintenance is required before publication; see '+str(args.output))


if __name__=='__main__':main()
