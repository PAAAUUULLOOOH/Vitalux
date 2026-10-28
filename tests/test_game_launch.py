"""Detected launcher routing, portable environment isolation and real detached startup."""
import os,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QCoreApplication
from vitalux import game_launch

app=QCoreApplication([])
with tempfile.TemporaryDirectory() as folder:
 root=Path(folder);binary=root/'bin';binary.mkdir();marker=root/'started'
 for name in ('steam','flatpak'):
  script=binary/name
  script.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > '+str(marker)+'\nprintf "LIB=%s\\n" "${LD_LIBRARY_PATH-}" >> '+str(marker)+'\n')
  script.chmod(0o755)
 game=dict(id='steam:42',store='steam',launcher_uri='steam://rungameid/42',flatpak=False)
 env=game_launch.environment(dict(PATH=str(binary),APPDIR=str(game_launch.ROOT),
       LD_LIBRARY_PATH=str(game_launch.ROOT/'lib')+':/user/library',LD_PRELOAD='/user/preload.so',
       VITALUX_RENDERER='software',XDG_CONFIG_HOME='/user/config'))
 assert env['LD_LIBRARY_PATH']=='/user/library' and env['LD_PRELOAD']=='/user/preload.so'
 assert env['XDG_CONFIG_HOME']=='/user/config' and 'APPDIR' not in env and 'VITALUX_RENDERER' not in env
 assert game_launch.command(game,env)==[str(binary/'steam'),game['launcher_uri']]
 assert game_launch.command(dict(game,flatpak=True),env)==[str(binary/'flatpak'),'run','com.valvesoftware.Steam',game['launcher_uri']]
 with patch.dict(os.environ,dict(PATH=str(binary)+os.pathsep+os.defpath,APPDIR=str(game_launch.ROOT),LD_LIBRARY_PATH=str(game_launch.ROOT/'lib'))):
  for flatpak,expected in ((False,[game['launcher_uri'],'LIB=']),(True,['run','com.valvesoftware.Steam',game['launcher_uri'],'LIB='])):
   marker.unlink(missing_ok=True)
   assert game_launch.start(dict(game,flatpak=flatpak))
   end=time.monotonic()+3
   while (not marker.exists() or 'LIB=' not in marker.read_text()) and time.monotonic()<end:
    app.processEvents();time.sleep(.005)
   assert marker.read_text().splitlines()==expected
print('Native/Flatpak launcher identity, preserved user environment and real detached start PASS')
