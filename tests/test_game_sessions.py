"""A quiet file is not game completion; reports survive restart/uninstall."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux import game_files, game_profiles
from vitalux.game_sessions import GameSessions, _pid_active

with tempfile.TemporaryDirectory() as folder:
    root=Path(folder)
    store=GameSessions(root/'state')
    game=dict(id='steam:42',appid='42',store='steam',name='Example',installed=True)
    bridge=root/'bridge';bridge.mkdir()
    game_files.write_json(bridge/'connection.json',dict(store='steam'))
    store.update_inventory([game]);store.register(game,bridge)
    session=bridge/'sessions/session.TEST';session.mkdir(parents=True)
    metadata=dict(game=game,profile=dict(target_fps=60),per_frame=True)
    game_files.write_json(session/'game.json',metadata)
    (session/'started').write_text(str(time.time()-40))
    (session/'owner.pid').write_text(str(os.getpid()))
    (session/'owner.stat').write_text(Path('/proc/self/stat').read_text())
    log=session/'example.csv'
    with log.open('w') as output:
        output.write('fps,frametime,gpu_temp,elapsed\n')
        for i in range(2400):output.write(f'60,{1000/60},72,{round((i+1)*1e9/60)}\n')
    pending=store.pending();assert len(pending)==1
    assert store.ready(pending,now=10,active=set())[0]==[], 'Finished a running game with a quiet CSV'
    # A real PID with a different start tick must not retain this session.
    stat=(session/'owner.stat').read_text()
    prefix,fields=stat.rsplit(')',1);fields=fields.split();fields[19]=str(int(fields[19])+1)
    (session/'owner.stat').write_text(prefix+') '+' '.join(fields))
    assert not _pid_active(session)
    assert store.ready(pending,now=20,active={str(session)})[0]==[], 'Forgot an orphaned game child'
    assert store.ready(pending,now=21,active=set())[0]==[]
    ready,running=store.ready(pending,now=25,active=set())
    assert len(ready)==1 and not running
    (session/'exit-code').write_text('0')
    (session/'finished').write_text(str(time.time()))
    report=store.finish(*ready[0])
    assert report['grade']=='excellent' and report['game_id']=='steam:42'
    assert report['frames']==2400 and (session/'processed').is_file()
    assert not store.pending(), 'Imported the same log twice'
    again=GameSessions(root/'state');assert again.report(report['id'])==report
    again.update_inventory([])
    assert again.catalog()[0]['installed'] is False
    assert again.history('steam:42')[0]['id']==report['id']
    before=(root/'state/catalog.json').stat().st_mtime_ns
    again.update_inventory([])
    assert (root/'state/catalog.json').stat().st_mtime_ns==before, 'Rewrote an unchanged catalog'
    # Raw cleanup cannot remove an active session or follow a symlink.
    active=bridge/'sessions/session.ACTIVE';active.mkdir()
    (active/'game.csv').write_text('keep running')
    external=root/'outside.csv';external.write_text('keep external')
    (session/'link.csv').symlink_to(external)
    with patch('vitalux.game_sessions.RAW_BUDGET',0):again.prune_raw()
    assert not log.exists() and external.read_text()=='keep external'
    assert (active/'game.csv').read_text()=='keep running'
    # Corrupt optional state is ignored rather than killing the service thread.
    game_files.write_json(root/'state/catalog.json',dict(games={'broken':None},connections={'bad':[] }))
    game_files.write_json(root/'state/sessions.json',dict(sessions=[dict(id='/'*32),dict(id='a'*32)]))
    damaged=GameSessions(root/'state');assert damaged.catalog()==[] and damaged.summaries==[]
print('Session owner/child tracking, stable finished files, restart history and bounded completed-only raw cleanup PASS')
