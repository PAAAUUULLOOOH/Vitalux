#!/usr/bin/env python3
"""Verify real Steam capsules and reuse them without any subsequent network IO."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PySide6.QtCore import QCoreApplication
from vitalux.game_artwork import resolve,dimensions
app=QCoreApplication([])
output=ROOT/'build/game-artwork-network';output.mkdir(parents=True,exist_ok=True)
results=[]
for appid,name in (('1091500','Cyberpunk 2077'),('12210','Grand Theft Auto IV')):
 game=dict(id='steam:'+appid,appid=appid,store='steam',name=name)
 path=resolve(game,cache=output/'cache')
 assert path,(appid,'No usable wide Steam capsule')
 size=dimensions(path);assert size is not None
 def forbidden(*args,**kwargs):raise AssertionError('A cached capsule was fetched again')
 assert resolve(game,cache=output/'cache',fetch=forbidden)==path
 results.append(dict(appid=appid,width=size.width(),height=size.height(),offline_reused=True))
(output/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results),flush=True)
