#!/usr/bin/env python3
"""Record actual MangoHud/OpenGL frames and import the finished game session."""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux import game_files, game_profiles, game_reports
from vitalux.game_sessions import GameSessions


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    for name in ('mangohud','glxgears','xdotool'):
        if not shutil.which(name):raise SystemExit('Required native test tool missing: '+name)
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    game=dict(id='steam:999999999',appid='999999999',store='steam',name='Native graphics verification',installed=True)
    bridge=game_profiles.prepare(game,dict(target_fps=60,warmup=1),base=output/'bridge')
    sessions=GameSessions(output/'state');sessions.register(game,bridge)
    env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1',vblank_mode='0')
    with (output/'graphics.log').open('w') as log:
        process=subprocess.Popen([str(bridge/'launch.sh'),'glxgears','-geometry','640x480'],env=env,
                                 stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            deadline=time.monotonic()+38
            while time.monotonic()<deadline:
                if process.poll() is not None:raise RuntimeError('Graphics program ended before capture')
                time.sleep(.2)
            windows=subprocess.check_output(['xdotool','search','--onlyvisible','--name','glxgears'],text=True).split()
            assert windows,'No actual graphics window'
            # glxgears destroys its X window on KeyPress. Sending a subsequent
            # KeyRelease to that dead window incorrectly reports BadWindow.
            subprocess.run(['xdotool','keydown','--window',windows[-1],'Escape'],check=True,timeout=5)
            assert process.wait(timeout=15)==0,'Game wrapper did not preserve the successful exit status'
        finally:
            if process.poll() is None:
                import signal
                os.killpg(process.pid,signal.SIGTERM)
                process.wait(timeout=10)
    pending=sessions.pending();assert len(pending)==1,pending
    assert sessions.ready(pending,now=10,active=set())[0]==[]
    ready,running=sessions.ready(pending,now=14,active=set())
    assert len(ready)==1 and not running
    report=sessions.finish(*ready[0])
    assert report['complete'] and report['per_frame'] and report['duration']>=30,report
    assert report['frames']>=100 and report['average_fps']>0 and report['low_1']>0,report
    # Independent CSV reference: verify the calculation with the actual frame log.
    milliseconds=[]
    for source in ready[0][2]:
        header=None
        with source.open() as stream:
            for row in csv.reader(stream):
                if 'frametime' in row and 'fps' in row:header=row;continue
                if header is None or len(row)!=len(header):continue
                value=game_reports.number(row[header.index('frametime')])
                if value is not None and 0<value<=60000:milliseconds.append(value)
    assert len(milliseconds)==report['frames']
    assert math.isclose(report['average_fps'],1000*len(milliseconds)/math.fsum(milliseconds),rel_tol=1e-5)
    worst=sorted(milliseconds,reverse=True)[:math.ceil(len(milliseconds)*.01)]
    assert math.isclose(report['low_1'],1000/(math.fsum(worst)/len(worst)),rel_tol=1e-5)
    assert GameSessions(output/'state').report(report['id'])==report
    result={key:report[key] for key in ('frames','duration','average_fps','low_1','low_01','grade','complete')}
    game_files.write_json(output/'verification.json',dict(native_mangohud=True,renderer='Mesa software OpenGL',**result))
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
