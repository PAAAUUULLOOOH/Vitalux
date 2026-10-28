"""Real isolated Steam IPC fixtures flush settings before automatic reconnect."""
import json,os,subprocess,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import psutil
from PySide6.QtCore import QCoreApplication
from vitalux import game_profiles,game_steam,profiles,settings
from vitalux.game_service import GameService

app=QCoreApplication([])
def wait(predicate,seconds=15):
 end=time.monotonic()+seconds
 while not predicate() and time.monotonic()<end:app.processEvents();time.sleep(.01)
 assert predicate(),'Isolated Steam fixture timed out'

with tempfile.TemporaryDirectory(prefix='vitalux-steam-restart-') as folder:
 root=Path(folder);binary=root/'bin';binary.mkdir();driver=binary/'steam'
 driver.write_text('#!'+sys.executable+'\n'+r'''
import ctypes,json,os,subprocess,sys,time
from pathlib import Path
root=Path(os.environ['TEST_STEAM_ROOT']);args=sys.argv[1:]
if args and args[0]=='run':
 os.environ['FLATPAK_ID']=args[1];args=args[2:]
if args==['daemon']:
 ctypes.CDLL(None).prctl(15,b'steam',0,0,0)
 snapshot=(root/'config.vdf').read_text();(root/'client.pid').write_text(str(os.getpid()))
 while not (root/'shutdown').exists():time.sleep(.01)
 time.sleep(.15)
 (root/'config.vdf').write_text(snapshot);(root/'flushed').write_text('yes')
 sys.exit(0)
with (root/'calls').open('a') as log:log.write(json.dumps(args)+chr(10))
if args==['-shutdown']:(root/'shutdown').write_text('yes');sys.exit(0)
pid=root/'client.pid'
if pid.exists():
 try:
  os.kill(int(pid.read_text()),0)
  # A dead unreaped daemon is not a live Steam instance.
  import psutil
  if psutil.Process(int(pid.read_text())).status()!=psutil.STATUS_ZOMBIE:sys.exit(0)
 except (ProcessLookupError,psutil.Error):pass
(root/'shutdown').unlink(missing_ok=True)
subprocess.Popen([sys.executable,__file__,'daemon'],env=os.environ.copy(),start_new_session=True,
 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
''')
 driver.chmod(0o755);(binary/'flatpak').symlink_to(driver)
 tracked=set();real_iter=psutil.process_iter
 def own_processes(attrs):
  for p in real_iter(attrs):
   if p.pid in tracked:yield p
 for flatpak in (False,True):
  case=root/('flatpak' if flatpak else 'native');case.mkdir()
  config=case/'config.vdf';original='"UserLocalConfigStore" { "Software" { "Valve" { "Steam" { "apps" { "42" { "LaunchOptions" "-novid" } } } } } }\n'
  steam=case/'Steam';path=steam/'userdata/123/config/localconfig.vdf'
  path.parent.mkdir(parents=True);path.write_text(original);config.symlink_to(path)
  game=dict(id='steam:42',store='steam',appid='42',name='Fixture',installed=True,flatpak=flatpak,
            launcher_root=str(steam),launcher_uri='steam://rungameid/42')
  def pid():return int((case/'client.pid').read_text()) if (case/'client.pid').exists() else None
  env=dict(PATH=str(binary)+os.pathsep+os.defpath,TEST_STEAM_ROOT=str(case))
  with patch.dict(os.environ,env),patch.object(settings,'PATH',str(case/'settings.json')),\
       patch.object(profiles,'directory',lambda kind:case/kind),\
       patch.object(game_profiles,'bridge_root',lambda game,base=None:case/'bridge'),\
       patch.object(psutil,'process_iter',own_processes):
   service=GameService(root=case/'state',initial_games=[game]);errors=[];saved=[];launches=[]
   service.failed.connect(errors.append);service.profile_saved.connect(saved.append);service.launch_ready.connect(launches.append)
   service.start()
   try:
    command=[str(binary/'flatpak'),'run','com.valvesoftware.Steam','steam://open/main'] if flatpak else [str(driver),'steam://open/main']
    subprocess.run(command,check=True);wait(lambda:pid() is not None);first=pid();tracked.add(first)
    wait(lambda:game_steam.running(game))
    assert not game_steam.running(dict(game,flatpak=not flatpak)),'Matched the other installation type'
    service.submit('profile',game);wait(lambda:bool(saved) or bool(errors));assert not errors,errors
    wait(lambda:pid()!=first);tracked.add(pid())
    assert (case/'flushed').exists() and 'launch.sh' in config.read_text(),'Steam overwrote the new connection'
    calls=[json.loads(line) for line in (case/'calls').read_text().splitlines()]
    assert calls.count(['-shutdown'])==1
    # A valid connection starts immediately, without restarting Steam again.
    service.submit('launch',game);wait(lambda:bool(launches) or bool(errors));assert not errors and not launches[-1]['restart_steam']
    assert (case/'calls').read_text().count('-shutdown')==1
    # A real own-user game process prevents any shutdown request.
    player=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],
                            env=dict(os.environ,SteamAppId='42',**({'FLATPAK_ID':'com.valvesoftware.Steam'} if flatpak else {})))
    tracked.add(player.pid)
    try:
     assert game_steam.playing(game)
     from threading import Event
     before=(case/'calls').read_bytes()
     try:game_steam.stop_for_setup(game,Event(),lambda message:None)
     except ValueError as error:assert 'Spiele' in str(error)
     else:raise AssertionError('Restarted Steam while a game was running')
     assert player.poll() is None and (case/'calls').read_bytes()==before
    finally:player.terminate();player.wait(timeout=3);tracked.discard(player.pid)
    # A missing connection is repaired before Play; only that Play request
    # reopens Steam with the game, rather than racing a second client command.
    config.write_text(original);launches.clear();(case/'flushed').unlink(missing_ok=True)
    service.submit('launch',game);wait(lambda:bool(launches) or bool(errors));assert not errors,errors
    assert launches[-1]['restart_steam'] and 'launch.sh' in config.read_text()
    assert (case/'calls').read_text().count('-shutdown')==2
   finally:
    service.shutdown();assert service.wait(5000)
    for process_id in list(tracked):
     try:
      process=psutil.Process(process_id)
      if str(driver) in process.cmdline():process.terminate()
     except psutil.Error:pass
    # Detached launcher IPC can finish after the worker signal. Reap only
    # processes from this unique fixture, including a late-starting client.
    for _ in range(5):
     for process in real_iter(['cmdline']):
      try:
       if str(driver) in (process.info['cmdline'] or []):process.terminate()
      except psutil.Error:pass
     time.sleep(.03)
    tracked.clear()
print('Native/Flatpak orderly restart, final Steam flush, reconnect, no duplicate restart and live-game protection PASS')
