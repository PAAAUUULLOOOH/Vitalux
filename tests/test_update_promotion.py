"""Normal ZIP/AppImage updates promote once, including in-flight and saved staging.

Only HTTPS responses and release catalog timing are simulated. Checksums, ZIP /
Type-2 ELF staging, activation helpers, profile choice and relaunch are real.
"""
import copy,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile
SOURCE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SOURCE))


def child(folder,kind,scenario):
    from PySide6.QtWidgets import QApplication
    from vitalux import profiles,updater,update_manager
    app=QApplication([]);app.setQuitOnLastWindowClosed(False)
    source='0.9.6.4-unstable.1';candidate='0.9.6.4-unstable.2';stable='0.9.6.4'
    root=folder/'application';assets={}
    for name,version in [('test',candidate),('stable',stable)]:
        package=folder/(name+('.zip' if kind=='zip' else '.AppImage'))
        if kind=='zip':
            with ZipFile(package,'w') as z:
                z.writestr('Vitalux/vitalux/__main__.py','pass\n')
                z.writestr('Vitalux/vitalux/__init__.py','__version__ = '+repr(version)+'\n')
                z.writestr('Vitalux/run.sh','#!/bin/sh\nprintf "'+version+'\\n" >> "$PROMOTION_MARKER"\n')
        else:
            program=folder/(name+'.c')
            program.write_text('#include <stdio.h>\n#include <stdlib.h>\nint main(){FILE*f=fopen(getenv("PROMOTION_MARKER"),"a");fprintf(f,"'+version+'\\n");fclose(f);return 0;}\n')
            subprocess.run(['gcc',str(program),'-o',str(package)],check=True,capture_output=True)
            data=bytearray(package.read_bytes());data[8:11]=b'AI\x02';package.write_bytes(data)
        assets[name]=package.read_bytes()
    def record(name,version):
        return dict(ok=True,eligible=True,newer=True,channel='unstable' if name=='test' else 'stable',latest=version,
                    url='https://github.com/PAAAUUULLOOOH/Vitalux/releases/download/test/'+name,
                    sha256=hashlib.sha256(assets[name]).hexdigest(),bytes=len(assets[name]),manifest_verified=True)
    active=dict(stable=record('stable',stable),unstable=record('test',candidate))
    active['unstable'].update(has_test_changes=True,stable_verified=True,stable_version=stable)
    parity=copy.deepcopy(active);parity['unstable'].update(eligible=False,has_test_changes=False,same_as_stable=True)
    if scenario=='uncovered':parity['unstable']['covered_test_version']=source
    calls=[];downloads=[]
    def catalog():
        calls.append(1)
        if scenario=='offline':raise OSError('offline')
        cutoff={'known':0,'before':0,'during':1,'prepared':2,'resumed':0,'retry':2,'no_parity':99,'uncovered':0}[scenario]
        return copy.deepcopy(parity if len(calls)>cutoff else active)
    class Response:
        def __init__(self,url):
            import io
            url=url if isinstance(url,str) else url.full_url
            if scenario=='retry' and url.endswith('/stable') and 'failed-stable' not in downloads:
                downloads.append('failed-stable');raise OSError('Transient Stable download failure')
            self.url=url;self.stream=io.BytesIO(assets[url.rsplit('/',1)[-1]])
            self.headers={'Content-Length':str(len(self.stream.getvalue()))};downloads.append(url.rsplit('/',1)[-1])
        def __enter__(self):return self
        def __exit__(self,*_):self.stream.close()
        def geturl(self):return self.url
        def read(self,n=-1):return self.stream.read(n)
    expected=candidate if scenario in ('no_parity','offline','uncovered') else stable
    with patch.object(update_manager,'__version__',source),patch.object(profiles,'__version__',source),patch.object(updater,'__version__',source),patch.object(updater,'app_root',return_value=str(root)),patch.object(updater,'catalog',side_effect=catalog),patch.object(updater,'_github_request',side_effect=lambda url,**_:Response(url)):
        m=update_manager.UpdateManager();m._timer.stop();m.records=copy.deepcopy(parity if scenario=='known' else active);m.set_channel('unstable')
        if scenario=='resumed':
            r=active['unstable'];path=updater.install(r['url'],sha256=r['sha256'],defer=True,expected_size=r['bytes'])
            worker=SimpleNamespace(channel='unstable',version=candidate,pending_path=path,kind=kind,sha256=r['sha256'],promotion_guard=True)
            m._on_installed('',worker);m._restart_timer.stop();m.shutdown();m.deleteLater()
            m=update_manager.UpdateManager();m._timer.stop()
        else:m.install()
        restarts=[]
        failures=[]
        def changed():
            if scenario=='retry' and m.error:
                failures.append(m.error)
                assert m.prepare_exit() and not m._activation_started,'Activated failed promotion'
        m.changed.connect(changed)
        def restart():
            restarts.append(dict(m.pending))
            assert m.pending['version']==expected,m.pending
            assert m.pending['channel']==('stable' if expected==stable else 'unstable')
            assert profiles.selected()==m.pending['channel']
            assert m.prepare_exit(),m.error
        m.restart.connect(restart)
        deadline=time.monotonic()+10
        while not restarts and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
        assert len(restarts)==1,(scenario,m.status,m.error,calls)
        if scenario=='retry':assert failures and m.pending['channel']=='stable'
        while not m.shutdown() and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
        m.finalize_exit()
        report=dict(scenario=scenario,kind=kind,downloads=downloads,checks=len(calls),target=m.pending['version'],restarts=len(restarts))
        (folder/'report.json').write_text(json.dumps(report))
        if scenario in ('before','known'):assert downloads==['stable'],downloads
        if expected==stable:
            assert not list(profiles.directory('cache').glob('prepared-zip-*/package.zip')) if kind=='appimage' else True
            assert len(list(root.glob('.vitalux-next-*')))==(1 if kind=='appimage' else 0)


if len(sys.argv)>1 and sys.argv[1]=='--child':
    child(Path(sys.argv[2]),sys.argv[3],sys.argv[4])
else:
    from vitalux import profiles
    with tempfile.TemporaryDirectory(prefix='vitalux-normal-promotion-') as temp:
        for kind in ('zip','appimage'):
            for scenario in ('known','before','during','prepared','resumed','retry','no_parity','offline','uncovered'):
                folder=Path(temp)/(kind+'-'+scenario);folder.mkdir();root=folder/'application'
                shutil.copytree(SOURCE/'vitalux',root/'vitalux',ignore=shutil.ignore_patterns('__pycache__'))
                marker=folder/'launched';env=os.environ.copy();env['PROMOTION_MARKER']=str(marker);env['QT_QPA_PLATFORM']='offscreen'
                for name in profiles.KINDS:env['XDG_'+name.upper()+'_HOME']=str(folder/name)
                for name in ('APPIMAGE','VITALUX_RESTART_MAILBOX','VITALUX_UPDATE_MAILBOX'):env.pop(name,None)
                if kind=='appimage':
                    image=root/'Vitalux.AppImage';image.write_bytes(b'old');env['APPIMAGE']=str(image)
                result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child',str(folder),kind,scenario],env=env,capture_output=True,text=True,timeout=25)
                assert result.returncode==0,(kind,scenario,result.stdout,result.stderr)
                deadline=time.monotonic()+8
                while not marker.exists() and time.monotonic()<deadline:time.sleep(.05)
                assert marker.exists(),(kind,scenario,list(folder.rglob('activation.log')))
                time.sleep(.2)
                report=json.loads((folder/'report.json').read_text())
                assert marker.read_text().splitlines()==[report['target']],(report,marker.read_text())
                if kind=='zip':assert report['target'] in (root/'vitalux/__init__.py').read_text()
                print('PASS normal update',json.dumps(report),flush=True)
    print('Normal updates: direct Stable, mid-transfer/pre-restart/resumed promotion, no downgrade/offline guessing, real staging and one relaunch PASS')
