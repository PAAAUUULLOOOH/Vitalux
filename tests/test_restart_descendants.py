"""A surviving external program must not keep the GUI restart owner waiting."""
import os,shlex,shutil,signal,subprocess,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
for appimage in (False,True):
 with tempfile.TemporaryDirectory(prefix='vitalux-descendant-restart-') as folder:
  root=Path(folder);(root/'runtime/bin').mkdir(parents=True)
  shutil.copy2(ROOT/'run.sh',root/'run.sh')
  for name in ('vitalux','packaging'):(root/name).symlink_to(ROOT/name,target_is_directory=True)
  driver=root/'driver.py'
  driver.write_text('''import json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from vitalux.single_instance import InstanceGuard
from vitalux.restart_protocol import ready
guard=InstanceGuard(Path.cwd()/'instance');assert guard.acquire(),'Previous GUI instance still owns its lock'
phase=Path('phase');number=int(phase.read_text())+1 if phase.exists() else 1;phase.write_text(str(number))
if number==1:
 # Deliberately model a legacy child retaining stdout/stderr, independently
 # of the fixed launcher. It must survive the GUI restart without a signal.
 child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
 Path('child').write_text(str(child.pid))
 if os.environ['TEST_APPIMAGE']=='1':
  from vitalux.updater import queue_appimage_restart
  assert queue_appimage_restart()
 assert ready()
 print('Last GUI diagnostic before restarting',flush=True)
 raise SystemExit(42)
''')
  binary=root/'runtime/bin/python3.12'
  binary.write_text('#!/bin/sh\nif [ "$1" = -c ]; then exit 0; fi\nif [ "$1" = -m ]; then exec '+shlex.quote(sys.executable)+' '+shlex.quote(str(driver))+'; fi\nexec '+shlex.quote(sys.executable)+' "$@"\n');binary.chmod(0o755)
  env=dict(os.environ,TEST_APPIMAGE=str(int(appimage)),VITALUX_SPEC_OFFLINE='1')
  for kind in ('CONFIG','STATE','DATA','CACHE'):env['XDG_'+kind+'_HOME']=str(root/kind.lower())
  command=['bash',str(root/'run.sh')]
  if appimage:
   target=root/'Vitalux.AppImage'
   target.write_text('#!/bin/sh\nprintf successor > '+shlex.quote(str(root/'successor'))+'\n');target.chmod(0o755)
   env.update(APPDIR=str(root),APPIMAGE=str(target))
   command=['bash',str(ROOT/'packaging/appimage-rollback-watch.sh'),str(root),str(target)]
  process=subprocess.Popen(command,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  try:
   stdout,stderr=process.communicate(timeout=8)
   assert process.returncode==0,(stdout,stderr)
   assert (root/'phase').read_text()==('1' if appimage else '2')
   if appimage:assert (root/'successor').read_text()=='successor'
   os.kill(int((root/'child').read_text()),0)
   logs='\n'.join(p.read_text() for p in (root/'state').rglob('vitalux.log'))
   assert 'Last GUI diagnostic before restarting' in logs
  finally:
   if (root/'child').exists():
    try:os.kill(int((root/'child').read_text()),signal.SIGTERM)
    except ProcessLookupError:pass
   if process.poll() is None:os.killpg(process.pid,signal.SIGKILL)
   process.communicate(timeout=3)
print('ZIP/AppImage restart after GUI exit, surviving external child, released instance lock and final diagnostics PASS')
