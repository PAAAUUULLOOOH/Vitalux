"""Read signed Ubuntu baseline metadata without changing the build host."""
import hashlib
import os
from pathlib import Path
import subprocess
import urllib.request

BASE='https://archive.ubuntu.com/ubuntu/'


def paragraphs(text):
    for part in text.strip().split('\n\n'):
        fields={};key=None
        for line in part.splitlines():
            if line[:1].isspace() and key:fields[key]+='\n'+line.strip()
            elif ':' in line:
                key,value=line.split(':',1);fields[key]=value.strip()
        if fields:yield fields


def verified_download(url,path,sha256):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==sha256:return path
    temporary=path.with_suffix(path.suffix+'.part')
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'Vitalux-dependency-maintenance'})
        with urllib.request.urlopen(request,timeout=90) as stream,temporary.open('wb') as output:
            while data:=stream.read(1024*1024):output.write(data)
        if hashlib.sha256(temporary.read_bytes()).hexdigest()!=sha256:
            raise ValueError('Dependency checksum mismatch: '+path.name)
        temporary.replace(path)
    finally:temporary.unlink(missing_ok=True)
    return path


class UbuntuArchive:
    """APT verifies InRelease and index hashes with the Ubuntu archive keyring."""
    def __init__(self,work,keyring=Path('/usr/share/keyrings/ubuntu-archive-keyring.gpg')):
        self.work=Path(work).resolve();self.work.mkdir(parents=True,exist_ok=True)
        self.keyring=Path(keyring).resolve()
        if not self.keyring.is_file():raise RuntimeError('Ubuntu archive keyring is required for the signed dependency check')
        for folder in ('lists/partial','archives/partial','empty'):(self.work/folder).mkdir(parents=True,exist_ok=True)
        (self.work/'status').touch()
        sources=self.work/'sources.list'
        sources.write_text('\n'.join(
            f'{kind} [arch=amd64 signed-by={self.keyring}] {url} {suite} main universe'
            for kind in ('deb','deb-src')
            for url,suites in ((BASE,('jammy','jammy-updates')),('https://security.ubuntu.com/ubuntu/',('jammy-security',)))
            for suite in suites)+'\n')
        self._packages={};self._sources={}
        self.options=[]
        for key,value in {
            'Dir::Etc::sourcelist':sources,'Dir::Etc::sourceparts':self.work/'empty',
            'Dir::Etc::parts':self.work/'empty','Dir::Etc::main':self.work/'unused.conf',
            'Dir::State::lists':self.work/'lists','Dir::State::status':self.work/'status',
            'Dir::Cache::archives':self.work/'archives','Dir::Cache::pkgcache':'',
            'Dir::Cache::srcpkgcache':'','APT::Architecture':'amd64','Acquire::Languages':'none',
            'APT::Sandbox::User':__import__('pwd').getpwuid(os.getuid()).pw_name,
            'Acquire::Retries':'2','Acquire::https::Timeout':'45','Debug::NoLocking':'true',
        }.items():self.options+=['-o',str(key)+'='+str(value)]

    def run(self,program,*args):
        result=subprocess.run([program,*self.options,*args],capture_output=True,text=True,timeout=240)
        if result.returncode:raise RuntimeError(program+' failed: '+result.stderr[-3000:])
        return result.stdout

    def refresh(self):
        log=self.run('apt-get','update','--error-on=any');(self.work/'signed-update.log').write_text(log)

    def cache_packages(self,names):
        names=sorted({name.split(':')[0] for name in names})
        policy=self.run('apt-cache','policy',*names);selected={};name=None
        for line in policy.splitlines():
            if line and not line[0].isspace() and line.endswith(':'):name=line[:-1]
            elif line.strip().startswith('Candidate:') and name:selected[name]=line.split(':',1)[1].strip()
        records=list(paragraphs(self.run('apt-cache','show',*[name+'='+version for name,version in selected.items() if version!='(none)'])))
        for record in records:
            name=record.get('Package')
            if record.get('Version')==selected.get(name) and record.get('Architecture') in ('amd64','all'):self._packages[name]=record

    def cache_sources(self,names):
        for record in paragraphs(self.run('apt-cache','showsrc',*sorted(set(names)))):
            self._sources[(record.get('Package'),record.get('Version'))]=record

    def package(self,name):
        name=name.split(':')[0]
        if name in self._packages:return self._packages[name]
        policy=self.run('apt-cache','policy',name)
        version=next((line.split(':',1)[1].strip() for line in policy.splitlines() if line.strip().startswith('Candidate:')),None)
        if not version or version=='(none)':raise ValueError('No signed Ubuntu candidate for '+name)
        records=list(paragraphs(self.run('apt-cache','show',name+'='+version)))
        record=next(r for r in records if r.get('Version')==version and r.get('Architecture') in ('amd64','all'))
        if not record.get('SHA256'):raise ValueError('Missing signed package checksum: '+name)
        return record

    def source(self,name,version):
        record=self._sources.get((name,version))
        if record is None:
            records=list(paragraphs(self.run('apt-cache','showsrc',name)))
            record=next((r for r in records if r.get('Version')==version),None)
        if record is None:raise ValueError('No signed corresponding source: '+name+' '+version)
        result=[]
        for line in record['Checksums-Sha256'].splitlines():
            if not line.strip():continue
            checksum,size,filename=line.split()
            result.append(dict(name=name+'-'+filename,version=version,
                url=BASE+record['Directory'].strip('/')+'/'+filename,
                filename=filename,sha256=checksum))
        if not any(r['filename'].endswith('.dsc') for r in result):raise ValueError('Source descriptor missing: '+name)
        return result
