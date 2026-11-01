#!/usr/bin/env python3
"""Build compatible runtime updates together with locks, sources and notices.

Run from an authorized release build, then validate the resulting complete
package. This script never changes a user's system or publishes a release.
"""
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,tarfile
from pathlib import Path
import urllib.request
from zipfile import ZipFile
from dependency_audit import ROOT,fetch,pins,version
from ubuntu_dependencies import UbuntuArchive,verified_download
from refresh_desktop_dependencies import refresh as refresh_desktop
_notice_spec=importlib.util.spec_from_file_location('license_collector',ROOT/'scripts/collect-license-notices.py')
_notice_module=importlib.util.module_from_spec(_notice_spec);_notice_spec.loader.exec_module(_notice_module)
collect_notices=_notice_module.collect


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def source_update(entry,latest,cache):
    updated=dict(entry);old=entry['version']
    for key in ('url','filename'):updated[key]=updated[key].replace(old,latest)
    updated['version']=latest
    target=cache/updated['filename'];target.parent.mkdir(parents=True,exist_ok=True)
    # A newly selected source version is obtained from its official URL;
    # never create a new lock merely by trusting an old local cache file.
    temporary=target.with_suffix('.part')
    request=urllib.request.Request(updated['url'],headers={'User-Agent':'Vitalux-dependency-maintenance'})
    with urllib.request.urlopen(request,timeout=90) as stream,temporary.open('wb') as output:shutil.copyfileobj(stream,output)
    temporary.replace(target)
    updated['sha256']=digest(target)
    return updated


def docker(command,work,capture=False):
    env=os.environ.copy()
    for key in ('DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH'):env.pop(key,None)
    env.setdefault('BUILDX_CONFIG',str(work/'buildx'))
    result=subprocess.run(['docker','--host=unix:///var/run/docker.sock',*command],env=env,
                          text=True,stdout=subprocess.PIPE if capture else None,check=True)
    return result.stdout.strip() if capture else None


def python_payload(entry,work):
    context=work/'python-build';context.mkdir(parents=True,exist_ok=True)
    source=work/'sources'/entry['filename']
    if digest(source)!=entry['sha256']:raise ValueError('CPython source lock mismatch')
    shutil.copyfile(source,context/'cpython-source.zip')
    shutil.copyfile(ROOT/'packaging/collect-python-libraries.py',context/'collect-python-libraries.py')
    image='vitalux-cpython:'+entry['version']
    docker(['build','--secret','id=proxy_ca,src='+os.environ.get('CODEX_PROXY_CERT','/etc/ssl/certs/ca-certificates.crt'),
            '--build-arg','PYTHON_VERSION='+entry['version'],'--build-arg','SOURCE_SHA256='+entry['sha256'],
            '-f',str(ROOT/'packaging/Dockerfile.cpython'),'-t',image,str(context)],work)
    container=docker(['create',image,'/runtime/bin/python3.12','--version'],work,True)
    destination=work/'python-payload';destination.mkdir(parents=True,exist_ok=True)
    try:
        for name in ('runtime','CPython-LICENSE.txt','python-libraries.json'):
            target=destination/name
            if target.is_dir():shutil.rmtree(target)
            docker(['cp',container+':/'+name,str(target)],work)
    finally:docker(['rm',container],work)
    return destination


def select_wheel(data,python=(3,12)):
    candidates=[]
    for entry in data['urls']:
        name=entry['filename']
        if entry.get('yanked') or entry.get('packagetype')!='bdist_wheel' or 'x86_64' not in name:continue
        match=re.search(r'-(cp\d+)-(abi3|cp\d+)-',name)
        if not match:continue
        digits=match.group(1)[2:];minimum=(int(digits[0]),int(digits[1:]))
        if minimum!=python and not (match.group(2)=='abi3' and minimum<=python):continue
        platforms=[(int(a),int(b)) for a,b in re.findall(r'manylinux_(\d+)_(\d+)_x86_64',name)]
        platforms += [(2,17)] if 'manylinux2014_x86_64' in name else []
        platforms += [(2,12)] if 'manylinux2010_x86_64' in name else []
        if not platforms or min(platforms)>(2,38):continue
        candidates.append((min(platforms),name,entry))
    if not candidates:raise ValueError('No compatible Linux x86-64 wheel: '+data['info']['name'])
    return max(candidates,key=lambda item:item[:2])[2]


def install_wheel(package,latest,site,cache):
    data=fetch('https://pypi.org/pypi/'+package+'/'+latest+'/json');wheel=select_wheel(data)
    path=verified_download(wheel['url'],cache/wheel['filename'],wheel['digests']['sha256'])
    prefix={'PySide6-Essentials':'PySide6','shiboken6':'shiboken6','psutil':'psutil'}[package]
    for existing in list(site.glob(prefix+'*')):
        if existing.is_dir():shutil.rmtree(existing)
        else:existing.unlink()
    with ZipFile(path) as archive:
        for entry in archive.infolist():
            target=(site/entry.filename).resolve()
            if not target.is_relative_to(site.resolve()):raise ValueError('Unsafe wheel path')
        archive.extractall(site)


def pack_runtime(payload):
    destination=ROOT/'portable-runtime/vitalux-linux-x86_64.tar.xz'
    temporary=destination.with_suffix('.part')
    with tarfile.open(temporary,'w:xz',preset=6) as archive:
        for path in sorted(payload.rglob('*')):
            if '__pycache__' in path.parts or path.suffix in ('.pyc','.pyo'):continue
            info=archive.gettarinfo(str(path),arcname=str(path.relative_to(payload)))
            info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
            info.mode=0o755 if info.isdir() or info.issym() or path.stat().st_mode&0o100 else 0o644
            if info.isfile():
                with path.open('rb') as stream:archive.addfile(info,stream)
            else:archive.addfile(info)
    temporary.replace(destination)
    (ROOT/'portable-runtime/SHA256SUMS').write_text(digest(destination)+'  '+destination.name+'\n')


def apply(report,work,keyring):
    for entry in report['updates']:
        if entry['kind']=='cpython' and version(entry['latest'])[:2]!=(3,12):
            raise ValueError('Python minor changes require a compatibility review')
        if entry['kind']=='pypi':
            count=2 if entry['name']=='PySide6-Essentials' else 1
            if version(entry['latest'])[:count]!=version(entry['current'])[:count]:
                raise ValueError('Dependency ABI family changes require review')
    work=Path(work).resolve();work.mkdir(parents=True,exist_ok=True)
    updates={entry['name']:entry for entry in report['updates']}
    if not updates:return False
    locks_path=ROOT/'third_party/sources.lock.json';records=json.loads(locks_path.read_text())
    before={entry['name']:entry['version'] for entry in records}
    requirements=pins();desired={name:updates[name]['latest'] if name in updates else value for name,value in requirements.items()}
    changed_sources=set()
    for entry in list(records):
        latest=None
        if entry['name']=='cpython' and 'cpython' in updates:latest=updates['cpython']['latest']
        if entry['name']=='psutil' and 'psutil' in updates:latest=desired['psutil']
        if entry['name'] in ('pyside-setup','qtbase','qtdeclarative','qtsvg','qtwayland','qtimageformats') and 'PySide6-Essentials' in updates:latest=desired['PySide6-Essentials']
        if latest:
            replacement=source_update(entry,latest,work/'sources')
            records[records.index(entry)]=replacement;changed_sources.add(entry['name'])
    core=None
    runtime_updates=any(name in updates for name in ('cpython','PySide6-Essentials','psutil'))
    if runtime_updates:
        payload=work/'runtime-payload'
        if payload.exists():shutil.rmtree(payload)
        payload.mkdir()
        archive=ROOT/'portable-runtime/vitalux-linux-x86_64.tar.xz'
        expected=(ROOT/'portable-runtime/SHA256SUMS').read_text().split()[0]
        if digest(archive)!=expected:raise ValueError('Old runtime archive checksum mismatch')
        with tarfile.open(archive) as original:original.extractall(payload,filter='data')
        if 'cpython' in updates:
            entry=next(entry for entry in records if entry['name']=='cpython')
            built=python_payload(entry,work);core=built/'python-libraries.json'
            # Keep the exact selected third-party bindings while replacing the
            # complete Python core; no old standard-library modules remain.
            site=payload/'runtime/lib/python3.12/site-packages'
            saved=work/'saved-site-packages'
            if saved.exists():shutil.rmtree(saved)
            shutil.move(str(site),saved);shutil.rmtree(payload/'runtime')
            shutil.copytree(built/'runtime',payload/'runtime',symlinks=True)
            site=payload/'runtime/lib/python3.12/site-packages';site.parent.mkdir(parents=True,exist_ok=True)
            if site.exists():shutil.rmtree(site)
            shutil.move(saved,site)
            old_license='Python-'+before['cpython']+'.txt';new_license='Python-'+entry['version']+'.txt'
            (ROOT/'licenses/runtime'/old_license).unlink(missing_ok=True)
            shutil.copyfile(built/'CPython-LICENSE.txt',ROOT/'licenses/runtime'/new_license)
            (payload/'licenses/runtime'/old_license).unlink(missing_ok=True)
            shutil.copyfile(built/'CPython-LICENSE.txt',payload/'licenses/runtime'/new_license)
        site=payload/'runtime/lib/python3.12/site-packages'
        if 'PySide6-Essentials' in updates:
            install_wheel('PySide6-Essentials',desired['PySide6-Essentials'],site,work/'wheels')
            install_wheel('shiboken6',desired['PySide6-Essentials'],site,work/'wheels')
        if 'psutil' in updates:
            install_wheel('psutil',desired['psutil'],site,work/'wheels')
            source=work/'sources'/next(e['filename'] for e in records if e['name']=='psutil')
            with ZipFile(source) as zipped:
                license_file=next(name for name in zipped.namelist() if name.endswith('/LICENSE'))
                content=zipped.read(license_file)
            for directory in (ROOT/'licenses/runtime',payload/'licenses/runtime'):
                (directory/('psutil-'+before['psutil']+'.txt')).unlink(missing_ok=True)
                (directory/('psutil-'+desired['psutil']+'.txt')).write_bytes(content)
        spec=importlib.util.spec_from_file_location('runtime_cleaner',ROOT/'scripts/clean-portable-runtime.py')
        cleaner=importlib.util.module_from_spec(spec);spec.loader.exec_module(cleaner);cleaner.clean(payload)
        for name in changed_sources:
            destination=ROOT/'licenses/upstream'/name
            if destination.exists():shutil.rmtree(destination)
        collect_notices([entry for entry in records if entry['name'] in changed_sources],work/'sources',ROOT/'licenses/upstream')
        if 'cpython' in changed_sources:
            destination=payload/'licenses/upstream/cpython'
            if destination.exists():shutil.rmtree(destination)
            shutil.copytree(ROOT/'licenses/upstream/cpython',destination)
        pack_runtime(payload)
    locks_path.write_text(json.dumps(records,indent=2)+'\n')
    requirements_path=ROOT/'requirements-dev.txt';text=requirements_path.read_text()
    for name,old in requirements.items():text=text.replace(name+'=='+old,name+'=='+desired[name])
    requirements_path.write_text(text)
    # Legal notices are generated from the matching source archives above.
    for name in ('THIRD-PARTY.md','licenses/README.md','portable-runtime/README.md'):
        path=ROOT/name;text=path.read_text()
        for entry in records:
            old=before.get(entry['name'])
            if old and old!=entry['version'] and entry['name'] in changed_sources:text=text.replace(old,entry['version'])
        path.write_text(text)
    if core or any(entry['kind']=='ubuntu' for entry in updates.values()):
        ubuntu=UbuntuArchive(work/'apt',keyring);ubuntu.refresh();refresh_desktop(ubuntu,work/'desktop',core)
    print('Compatible dependency updates prepared; complete package validation is required before publication')
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--work',type=Path,default=ROOT/'build/dependencies/update')
    parser.add_argument('--keyring',type=Path,default=Path('/usr/share/keyrings/ubuntu-archive-keyring.gpg'))
    args=parser.parse_args();apply(json.loads(args.report.read_text()),args.work,args.keyring)
