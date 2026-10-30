"""Real type-2 runtimes: launcher identity and restart/update with live children."""
import hashlib,json,os,shlex,shutil,signal,subprocess,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vitalux import __version__,game_launch

tool=shutil.which('mksquashfs')
if not tool:raise RuntimeError('AppImage process verification requires the existing packaging tool mksquashfs')

def image(directory,target):
 filesystem=target.with_suffix('.squashfs')
 subprocess.run([tool,str(directory),str(filesystem),'-noappend','-all-root','-no-xattrs','-processors','1'],
                check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=25)
 with target.open('wb') as output:
  output.write((ROOT/'packaging/runtime/runtime-x86_64').read_bytes())
  with filesystem.open('rb') as source:shutil.copyfileobj(source,output)
 target.chmod(0o755);filesystem.unlink()

with tempfile.TemporaryDirectory(prefix='vitalux-real-appimage-') as folder:
 root=Path(folder);extract=root/'extract';extract.mkdir()
 env=dict(os.environ,APPIMAGE_EXTRACT_AND_RUN='1',NO_CLEANUP='1',TMPDIR=str(extract))
 # Keep only this fixture's extraction directories until its assertions finish;
 # the outer TemporaryDirectory removes them even after failed execs.
 for key in ('APPDIR','APPIMAGE','TARGET_APPIMAGE','ARGV0','OWD'):env.pop(key,None)
 for key in ('DISPLAY','WAYLAND_DISPLAY'):env.pop(key,None)
 for kind in ('CONFIG','CACHE','STATE','DATA'):env['XDG_'+kind+'_HOME']=str(root/kind.lower())
 for name in ('Vitalux','Steam'):
  appdir=root/name;appdir.mkdir()
  script=appdir/'AppRun';script.write_text('#!/bin/sh\nprintf '+name+' > '+shlex.quote(str(root/'opened'))+'\n');script.chmod(0o755)
  image(appdir,root/(name+'.AppImage'))
 # Prove that the runtime itself follows an inherited target, regardless of
 # the executable requested. This models a spurious second Vitalux launch.
 origin=dict(env,TARGET_APPIMAGE=str(root/'Vitalux.AppImage'),APPIMAGE=str(root/'Vitalux.AppImage'),
             APPDIR=str(ROOT),ARGV0=str(root/'Vitalux.AppImage'),GIO_LAUNCHED_DESKTOP_FILE='/applications/vitalux.desktop')
 subprocess.run([str(root/'Steam.AppImage')],env=origin,check=True,capture_output=True,timeout=15)
 assert (root/'opened').read_text()=='Vitalux','Runtime no longer reproduces the inherited AppImage identity'
 binary=root/'bin';binary.mkdir();(binary/'steam').symlink_to(root/'Steam.AppImage')
 (root/'opened').unlink()
 with patch.dict(os.environ,dict(origin,PATH=str(binary)+os.pathsep+os.defpath),clear=True):
  assert game_launch.start(dict(store='steam',launcher_uri='steam://open/main'))
 deadline=time.monotonic()+10
 while not (root/'opened').exists() and time.monotonic()<deadline:time.sleep(.01)
 assert (root/'opened').read_text()=='Steam','Steam opening reactivated Vitalux'

 driver=root/'driver.py';driver.write_text('''import json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from vitalux import __version__,updater
from vitalux.single_instance import InstanceGuard
from vitalux.restart_protocol import ready
state=Path(os.environ['TEST_CASE']);guard=InstanceGuard(state/'instance');assert guard.acquire()
phase=state/'phase';number=int(phase.read_text())+1 if phase.exists() else 1;phase.write_text(str(number))
with (state/'entries').open('a') as stream:stream.write(json.dumps(dict(phase=number,version=__version__,pid=os.getpid()))+'\\n')
if number==1:
 child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
 (state/'child').write_text(str(child.pid))
 if os.environ['TEST_ACTION']=='restart':assert updater.queue_appimage_restart();assert ready()
 else:updater.activate_appimage_update(str(state/'candidate.AppImage'))
 raise SystemExit(42 if os.environ['TEST_ACTION']=='restart' else 0)
''')
 for action in ('restart','update'):
  case=root/action;case.mkdir();appdir=case/'AppDir';appdir.mkdir()
  shutil.copytree(ROOT/'vitalux',appdir/'vitalux',ignore=shutil.ignore_patterns('__pycache__'))
  (appdir/'packaging').mkdir();(appdir/'runtime/bin').mkdir(parents=True)
  for name in ('AppRun','appimage-activate.py','appimage-rollback-watch.sh','restart-request.py','logging.sh'):
   shutil.copy2(ROOT/'packaging'/name,appdir/('AppRun' if name=='AppRun' else 'packaging/'+name))
  shutil.copy2(ROOT/'run.sh',appdir/'run.sh')
  (appdir/'AppRun').chmod(0o755);(appdir/'run.sh').chmod(0o755)
  python=appdir/'runtime/bin/python3.12';python.write_text('#!/bin/sh\nif [ "$1" = -c ]; then exit 0; fi\nif [ "$1" = -m ]; then exec '+shlex.quote(sys.executable)+' '+shlex.quote(str(driver))+'; fi\nexec '+shlex.quote(sys.executable)+' "$@"\n');python.chmod(0o755)
  target=case/'Vitalux.AppImage';image(appdir,target);previous_hash=hashlib.sha256(target.read_bytes()).hexdigest()
  future='9.9.9.9-unstable.1'
  if action=='update':
   init=appdir/'vitalux/__init__.py';init.write_text(init.read_text().replace(__version__,future))
   image(appdir,case/'candidate.AppImage')
  process=subprocess.Popen([str(target),'--launch'],env=dict(env,TEST_ACTION=action,TEST_CASE=str(case)),
                           stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  try:
   out,err=process.communicate(timeout=20)
   assert process.returncode==0,(out,err)
   entries=[json.loads(line) for line in (case/'entries').read_text().splitlines()]
   assert [row['phase'] for row in entries]==[1,2],entries
   assert [row['version'] for row in entries]==[__version__,future if action=='update' else __version__],entries
   assert entries[0]['pid']!=entries[1]['pid']
   os.kill(int((case/'child').read_text()),0)
   if action=='update':assert hashlib.sha256(target.with_name('Vitalux.AppImage.previous').read_bytes()).hexdigest()==previous_hash
  finally:
   if (case/'child').exists():
    try:os.kill(int((case/'child').read_text()),signal.SIGTERM)
    except ProcessLookupError:pass
   if process.poll() is None:os.killpg(process.pid,signal.SIGKILL)
   process.communicate(timeout=3)
print('Real AppImage runtime: inherited-target regression, correct Steam start, restart/update successor, instance handoff and live-child survival PASS')
