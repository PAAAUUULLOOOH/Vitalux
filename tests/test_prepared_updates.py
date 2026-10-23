"""Prepared ZIPs leave the running app untouched and activate after exit only."""
import hashlib,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux import profiles,updater
SOURCE=Path(__file__).resolve().parents[1]


def wait_for(condition):
    deadline=time.monotonic()+12
    while not condition() and time.monotonic()<deadline:time.sleep(.05)
    assert condition(),'External activation did not finish'


with tempfile.TemporaryDirectory(prefix='vitalux-prepared-') as folder:
    folder=Path(folder);env=os.environ.copy()
    for kind in profiles.KINDS:env['XDG_'+kind.upper()+'_HOME']=str(folder/kind)
    env.pop('APPIMAGE',None)
    root=folder/'application';shutil.copytree(SOURCE/'vitalux',root/'vitalux',ignore=shutil.ignore_patterns('__pycache__'))
    old=(root/'vitalux/__main__.py').read_bytes()
    archive=folder/'incoming.zip'
    marker=folder/'reopened'
    with ZipFile(archive,'w') as zipped:
        zipped.writestr('Vitalux/vitalux/__main__.py','updated=True\n')
        zipped.writestr('Vitalux/vitalux/__init__.py','__version__ = "0.9.6.2"\n')
        zipped.writestr('Vitalux/run.sh','#!/bin/sh\ntouch "'+str(marker)+'"\n')
    raw=archive.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    class Asset:
        headers={'Content-Length':str(len(raw))}
        def __enter__(self):self.stream=archive.open('rb');return self
        def __exit__(self,*args):self.stream.close()
        def geturl(self):return 'https://github.com/PAAAUUULLOOOH/Vitalux/releases/download/test/file.zip'
        def read(self,size=-1):return self.stream.read(size)
    with patch.dict(os.environ,env,clear=True),patch.object(updater,'_github_request',side_effect=lambda *a,**k:Asset()):
        prepared=Path(updater.install('https://github.com/PAAAUUULLOOOH/Vitalux/releases/download/test/file.zip',root=str(root),sha256=digest,defer=True))
    assert (root/'vitalux/__main__.py').read_bytes()==old and not (root/'.backup').exists()
    prepared.write_bytes(raw+b'damaged')
    try:updater.apply_prepared_zip(prepared,str(root),digest)
    except RuntimeError:pass
    else:raise AssertionError('Prepared ZIP checksum was not rechecked')
    assert (root/'vitalux/__main__.py').read_bytes()==old
    prepared.write_bytes(raw)
    pending=folder/'pending.json';profiles.atomic_json(pending,{'version':'0.9.6.2'})
    code='''import sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from vitalux import updater
root,archive,digest,pending=sys.argv[1:]
old=Path(root,'vitalux/__main__.py').read_bytes()
updater.activate_zip_update(archive,digest,pending,relaunch=False)
time.sleep(.25)
assert Path(root,'vitalux/__main__.py').read_bytes()==old,'Applied before source process exited'
'''
    result=subprocess.run([sys.executable,'-c',code,str(root),str(prepared),digest,str(pending)],env=env,capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stdout+result.stderr
    wait_for(lambda:(root/'vitalux/__main__.py').read_text()=='updated=True\n')
    wait_for(lambda:not pending.exists())
    assert not marker.exists(),'Later reopened the application'
    assert (root/'.backup/vitalux/__main__.py').read_bytes()==old
    # Real AppImage activation helper must honor the same Later/Exit choice.
    image=folder/'Vitalux.AppImage';candidate=folder/'candidate.AppImage'
    image.write_text('old-image\n');candidate.write_text('#!/bin/sh\ntouch "'+str(marker)+'"\n');candidate.chmod(0o755)
    env['APPIMAGE']=str(image)
    code='''import sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from vitalux import updater
updater.activate_appimage_update(sys.argv[2],relaunch=False)
time.sleep(.25)
assert Path(sys.argv[3]).read_text()=='old-image\\n'
'''
    result=subprocess.run([sys.executable,'-c',code,str(SOURCE),str(candidate),str(image)],env=env,capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stdout+result.stderr
    wait_for(lambda:image.read_text().startswith('#!/bin/sh'))
    assert image.with_name(image.name+'.previous').read_text()=='old-image\n'
    assert not marker.exists(),'Deferred AppImage unexpectedly reopened'

    # Automatic activation uses the same real helpers and reopens exactly once.
    shutil.copytree(SOURCE/'vitalux', root/'vitalux', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__'))
    with ZipFile(archive, 'w') as zipped:
        zipped.writestr('Vitalux/vitalux/__main__.py', 'automatic=True\n')
        zipped.writestr('Vitalux/vitalux/__init__.py', '__version__ = "0.9.6.2"\n')
        zipped.writestr('Vitalux/run.sh', '#!/bin/sh\nprintf x >> "'+str(marker)+'"\n')
    raw=archive.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    prepared.parent.mkdir(parents=True,exist_ok=True);prepared.write_bytes(raw)
    profiles.atomic_json(pending,{'version':'0.9.6.2'})
    env.pop('APPIMAGE',None)
    code='''import sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from vitalux import updater
root,archive,digest,pending=sys.argv[1:]
old=Path(root,'vitalux/__main__.py').read_bytes()
updater.activate_zip_update(archive,digest,pending,relaunch=True)
time.sleep(.25)
assert Path(root,'vitalux/__main__.py').read_bytes()==old
'''
    result=subprocess.run([sys.executable,'-c',code,str(root),str(prepared),digest,str(pending)],env=env,capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stdout+result.stderr
    wait_for(marker.exists);time.sleep(.3)
    assert marker.read_text()=='x' and not pending.exists()
    assert (root/'vitalux/__main__.py').read_text()=='automatic=True\n'
    marker.unlink()
    image.write_text('old-again\n')
    candidate.write_text('#!/bin/sh\nprintf x >> "'+str(marker)+'"\n');candidate.chmod(0o755)
    env['APPIMAGE']=str(image)
    code='''import sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from vitalux import updater
updater.activate_appimage_update(sys.argv[2],relaunch=True)
time.sleep(.25)
assert Path(sys.argv[3]).read_text()=='old-again\\n'
'''
    result=subprocess.run([sys.executable,'-c',code,str(SOURCE),str(candidate),str(image)],env=env,capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stdout+result.stderr
    wait_for(marker.exists);time.sleep(.3)
    assert marker.read_text()=='x'
    assert image.with_name(image.name+'.previous').read_text()=='old-again\n'
print('Actual ZIP/AppImage helpers: exit coordination, checksums, backups, manual exit and exactly one automatic relaunch PASS')
