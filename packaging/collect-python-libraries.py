"""Describe the native CPython closure from the signed Ubuntu build image."""
import hashlib,json,re,subprocess
from pathlib import Path

runtime=Path('/out/runtime');dependencies={}
for path in [runtime/'bin/python3.12',*(runtime/'lib/python3.12/lib-dynload').glob('*.so')]:
    result=subprocess.run(['ldd',str(path)],capture_output=True,text=True,check=True)
    for name,filename in re.findall(r'^\s*(\S+)\s+=>\s+(\/\S+)',result.stdout,re.M):
        actual=Path(filename).resolve()
        if actual.is_relative_to(runtime):continue
        owner=None
        for variant in dict.fromkeys((str(actual),str(actual).removeprefix('/usr'),'/usr'+str(actual))):
            found=subprocess.run(['dpkg-query','-S',variant],capture_output=True,text=True)
            if found.returncode==0:owner=found.stdout.split(': ',1)[0];break
        if owner is None:raise RuntimeError('Untracked Python dependency: '+str(actual))
        if owner.split(':')[0]=='libc6':continue  # The supported host provides glibc.
        version,source,source_version=subprocess.check_output(['dpkg-query','-W','-f=${Version}\t${source:Package}\t${source:Version}',owner],text=True).split('\t')
        dependencies[name]=dict(name=name,package=owner,source=source,version=version,source_version=source_version,sha256=hashlib.sha256(actual.read_bytes()).hexdigest())
Path('/out/python-libraries.json').write_text(json.dumps(list(dependencies.values()),indent=2)+'\n')
