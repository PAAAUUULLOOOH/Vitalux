#!/usr/bin/env python3
"""Exercise Play game -> launcher preparation -> real visible MangoHud/CSV."""
import argparse,json,os,shlex,signal,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--probe',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='vitalux-launch-client-') as folder:
  for kind in ('CONFIG','CACHE','STATE','DATA'):os.environ['XDG_'+kind+'_HOME']=str(output/kind.lower())
  os.environ.update(QT_QPA_PLATFORM='xcb',LIBGL_ALWAYS_SOFTWARE='1',vblank_mode='0',VITALUX_GAME_ART_OFFLINE='1')
  os.environ.pop('VITALUX_SPEC_OFFLINE',None)
  from PySide6.QtGui import QImage
  from PySide6.QtCore import QCoreApplication,QEvent
  from PySide6.QtWidgets import QApplication
  from vitalux import game_files,game_profiles,settings,theme
  from vitalux.games_page import GamesPage
  app=QApplication([])
  app.setQuitOnLastWindowClosed(False)
  settings.set_many(dict(motion='off',component_images=False));theme.set_mode('obsidian_gold')
  config=output/'Steam test files/userdata/123/config/localconfig.vdf';config.parent.mkdir(parents=True,exist_ok=True)
  config.write_text('"UserLocalConfigStore" { "Software" { "Valve" { "Steam" { "apps" { "42" { "LaunchOptions" "" } } } } } }')
  marker=output/'launch-result.json';pidfile=output/'client.pid';driver=Path(folder)/'driver.py'
  keys=('UserLocalConfigStore','Software','Valve','Steam','apps','42','LaunchOptions')
  driver.write_text('import os,sys,json,subprocess,shlex\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom vitalux import game_files\n'
    +'Path('+repr(str(pidfile))+').write_text(str(os.getpid()))\n'
    +'value=game_files.loads(Path('+repr(str(config))+').read_text())\n'
    +'for key in '+repr(keys)+':value=game_files.get(value,key,{})\n'
    +'assert isinstance(value,str) and "launch.sh" in value\n'
    +'log=Path('+repr(str(output/'client.log'))+').open("w")\n'
    +'code=subprocess.run(["/bin/sh","-c",value.replace("%command%",shlex.join('+repr([str(args.probe.resolve()),'gl','14'])+'))],stdout=log,stderr=subprocess.STDOUT).returncode\n'
    +'Path('+repr(str(marker))+').write_text(json.dumps(dict(code=code,uri=sys.argv[1],prepared="launch.sh" in value)))\n')
  launcher=Path(folder)/'steam';launcher.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(driver))+' "$@"\n');launcher.chmod(0o755)
  os.environ['PATH']=folder+os.pathsep+os.environ.get('PATH',os.defpath)
  game=dict(id='steam:42',store='steam',appid='42',name='Play game integration',installed=True,flatpak=False,
            launcher_root=str(output/'Steam test files'),launcher_uri='steam://rungameid/42',cover='')
  game_profiles.save(game['id'],dict(enabled=True,warmup=1,metrics=['fps','frametime','frame_timing']))
  page=GamesPage(startup_games=[game]);errors=[];page.service.failed.connect(errors.append)
  def wait(predicate,seconds):
   end=time.monotonic()+seconds
   while time.monotonic()<end:
    app.processEvents()
    if predicate():return
    if errors:raise AssertionError(errors)
    time.sleep(.02)
   detail=(output/'client.log').read_text(errors='replace')[-3000:] if (output/'client.log').exists() else page.notice.text()
   raise AssertionError('Play game integration timed out: '+detail)
  try:
   wait(lambda:any(g['id']==game['id'] for g in page.games),8)
   page.select_game(game['id']);page.start_button.click()
   bright=[0]
   def overlay():
    picture=app.primaryScreen().grabWindow(0).toImage().convertToFormat(QImage.Format_RGBA8888)
    data=bytes(picture.constBits());stride=picture.bytesPerLine()
    bright[0]=sum(all(data[y*stride+x*4+c]>135 for c in range(3)) for y in range(min(240,picture.height())) for x in range(min(420,picture.width())))
    if bright[0]>40:picture.save(str(output/'play-game-overlay.png'));return True
    return False
   wait(pidfile.exists,30);wait(overlay,12);wait(marker.exists,22)
   result=json.loads(marker.read_text());assert result==dict(code=0,uri=game['launcher_uri'],prepared=True)
   bridge=game_profiles.bridge_root(game)
   csvs=list((bridge/'sessions').rglob('*.csv'));assert csvs and any(p.stat().st_size>1000 for p in csvs)
   assert game_profiles.connected(game,bridge)
   result.update(visible_overlay_pixels=bright[0],recording=True,play_button=True)
   game_files.write_json(output/'verification.json',result);print(json.dumps(result),flush=True)
  finally:
   page.shutdown();assert page.service.wait(5000);assert page.artwork.wait(5000)
   # Deliver the worker's final queued signals while the page still exists,
   # then destroy its widgets with QApplication alive. Leaving this cyclic
   # object graph to Python finalization can tear down shared Qt objects late.
   app.processEvents();page.close();page.deleteLater()
   QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
   import shiboken6
   assert not shiboken6.isValid(page),'Native game page outlived its QApplication'
   if pidfile.exists():
    try:
     import psutil
     process=psutil.Process(int(pidfile.read_text()))
     if str(driver) in process.cmdline():os.killpg(process.pid,signal.SIGTERM)
    except (ProcessLookupError,psutil.Error):pass
  app.quit()

if __name__=='__main__':main()
