"""A prepared update and simulated abnormal old-process exit have one owner."""
import os,sys,tempfile,subprocess,shlex,itertools,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vitalux import __version__
for action,status in itertools.product(('update','restart'),(0,42,139,135,134)):
 with tempfile.TemporaryDirectory(prefix='vitalux-one-owner-') as directory:
  stage=Path(directory);mounted=stage/'mounted';(mounted/'vitalux').mkdir(parents=True)
  (mounted/'packaging').mkdir();(mounted/'runtime/bin').mkdir(parents=True)
  (mounted/'packaging/appimage-activate.py').write_bytes((ROOT/'packaging/appimage-activate.py').read_bytes())
  (mounted/'packaging/restart-request.py').write_bytes((ROOT/'packaging/restart-request.py').read_bytes())
  (mounted/'vitalux/restart_protocol.py').write_bytes((ROOT/'vitalux/restart_protocol.py').read_bytes())
  (mounted/'vitalux/__init__.py').write_text('__version__ = "'+__version__+'"\n')
  restarted=stage/'restarted'
  current=(b'current version' if action=='update' else
           ('#!/bin/sh\necho restart >> '+shlex.quote(str(restarted))+'\n').encode())
  target=stage/'Vitalux.AppImage';target.write_bytes(current);target.chmod(0o755)
  previous=stage/'Vitalux.AppImage.previous';previous.write_bytes(b'older version')
  candidate=stage/'candidate.AppImage';payload=b'\x7fELF'+b'\0'*4+b'AI\x02'+b'prepared candidate';candidate.write_bytes(payload)
  driver=stage/'driver.py';driver.write_text('''import sys,os
from unittest.mock import patch
sys.path.insert(0,'''+repr(str(ROOT))+''')
from vitalux import updater
with patch.object(updater.subprocess,'Popen',side_effect=AssertionError('A second activation owner was spawned')):
 '''+("updater.activate_appimage_update("+repr(str(candidate))+",relaunch=False)" if action=='update' else 'assert updater.queue_appimage_restart()')+'''
os._exit('''+str(status)+''')
''')
  # Exercise the real launcher too: its GPU fallback must not launch the
  # old mount again while AppRun owns a prepared update.
  invocations=stage/'app-starts';fallbacks=stage/'gpu-fallbacks'
  runtime=mounted/'runtime/bin/python3.12'
  runtime.write_text('#!/bin/bash\n'+
   'if [[ "$1" == -m ]]; then\n'+
   ' echo app >> '+shlex.quote(str(invocations))+'\n'+
   ' exec '+shlex.quote(sys.executable)+' '+shlex.quote(str(driver))+'\n'+
   'elif [[ "$1" == -c ]]; then exit 0\n'+
   'elif [[ "$1" == - ]]; then echo fallback >> '+shlex.quote(str(fallbacks))+'; exit 0\n'+
   'else exec '+shlex.quote(sys.executable)+' "$@"; fi\n')
  runtime.chmod(0o755)
  (mounted/'run.sh').write_bytes((ROOT/'run.sh').read_bytes())
  env=os.environ.copy();env.update(APPIMAGE=str(target),APPDIR=str(mounted))
  for kind in ('CONFIG','CACHE','STATE','DATA'):env['XDG_'+kind+'_HOME']=str(stage/kind.lower())
  result=subprocess.run(['bash',str(ROOT/'packaging/appimage-rollback-watch.sh'),str(mounted),str(target)],env=env,capture_output=True,text=True,timeout=15)
  assert result.returncode==0,result.stderr
  assert target.read_bytes()==(payload if action=='update' else current),'Transition changed to an unintended version'
  assert previous.read_bytes()==(current if action=='update' else b'older version'),'Wrong fallback version was retained'
  if action=='restart':
   deadline=time.monotonic()+3
   while not restarted.exists() and time.monotonic()<deadline:time.sleep(.01)
   assert restarted.read_text().splitlines()==['restart'],'Intentional reset did not restart exactly once'
  logs='\n'.join(p.read_text() for p in (stage/'state').rglob('restart.log'))
  assert logs.count('Prepared update activated' if action=='update' else 'Requested restart retained')==1 and 'Attempting rollback' not in logs,logs
  assert not list((stage/'state').rglob('.appimage-launch-*'))
  assert invocations.read_text().splitlines()==['app'],'Old mount started twice'
  assert not fallbacks.exists(),'GPU recovery competed with prepared activation'
  if status not in (0,42):
   assert any('Process crashed (exit code '+str(status) in p.read_text()
              for p in (stage/'state').rglob('errors.log')),'Native error was suppressed'
print('One AppRun owner: update/reset after normal/restart/SIGSEGV/SIGBUS/SIGABRT codes, exactly one restart, retained versions and native error logging PASS')
