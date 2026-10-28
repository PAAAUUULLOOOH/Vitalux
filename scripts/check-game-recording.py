#!/usr/bin/env python3
"""Exercise bundled OpenGL/Vulkan 32/64 overlays without a system MangoHud."""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vitalux import game_files,game_profiles,game_reports,game_runtime
from vitalux.game_sessions import GameSessions


def record(probe,api,bits,seconds,output,app,flatpak_app=None,loader32=None,steam_runtime=None):
    name=f'{api}{bits}'
    game=dict(id='steam:'+str(9999999900+(bits if api=='gl' else bits+100)),store='steam',
              appid='9999999900',name='Bundled '+name,installed=True,flatpak=bool(flatpak_app))
    if flatpak_app:
        base=Path.home()/'.var/app'/flatpak_app/'data/vitalux-overlay/verification'
    else:base=output/'bridge'
    bridge=game_profiles.prepare(game,dict(target_fps=60,warmup=1),base=base)
    sessions=GameSessions(output/(name+'-state'));sessions.register(game,bridge)
    env=dict(os.environ,LIBGL_ALWAYS_SOFTWARE='1',vblank_mode='0')
    env['PATH']=str(output/'shadow')+':'+os.defpath
    payload=([loader32] if bits==32 and loader32 else [])+[str(probe),api,str(seconds)]
    if steam_runtime:payload=[str(Path(steam_runtime)/'_v2-entry-point'),'--verb=run','--',*payload]
    command=[str(bridge/'launch.sh'),*payload]
    if flatpak_app:
        command=['flatpak','run','--env=LIBGL_ALWAYS_SOFTWARE=1','--env=vblank_mode=0',
                 '--command=/app/bin/with-compat',flatpak_app,str(bridge/'launch.sh'),*payload]
    with (output/(name+'.log')).open('w') as log:
        process=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            # Mesa/MangoHud cold startup varies on shared runners. Wait for
            # actual overlay pixels instead of taking one fixed four-second
            # screenshot before the first composited frame is ready.
            started=time.monotonic()
            deadline=started+min(12,seconds-1)
            from PySide6.QtGui import QImage
            bright=0;picture=None
            while time.monotonic()<deadline:
                if process.poll() is not None:raise RuntimeError(name+' ended before drawing')
                app.processEvents()
                picture=app.primaryScreen().grabWindow(0).toImage().convertToFormat(QImage.Format_RGBA8888)
                data=bytes(picture.constBits());stride=picture.bytesPerLine()
                bright=sum(all(data[y*stride+x*4+c]>135 for c in range(3))
                           for y in range(min(240,picture.height())) for x in range(min(420,picture.width())))
                if bright>40:break
                time.sleep(.1)
            assert picture is not None
            assert picture.save(str(output/(name+'-overlay.png')))
            assert bright>40,(name,'Overlay text did not appear',bright)
            startup_seconds=time.monotonic()-started
            alive=sessions.pending();assert len(alive)==1
            assert sessions.ready(alive,now=2)[1]==[game['id']]
            assert sessions.ready(alive,now=6)[1]==[game['id']],'A live game was mistaken for a completed session'
            # The probe only clears a dark color. Bright pixels demonstrate that
            # MangoHud actually drew its text, rather than merely writing CSV.
            assert process.wait(timeout=seconds+20)==0,(name,'Graphics probe failed')
        except BaseException:
            log.flush()
            print((output/(name+'.log')).read_text(errors='replace')[-6000:],flush=True)
            raise
        finally:
            if process.poll() is None:
                import signal
                os.killpg(process.pid,signal.SIGTERM);process.wait(timeout=10)
    pending=sessions.pending();assert len(pending)==1,pending
    assert sessions.ready(pending,now=10,active=set())[0]==[]
    ready,running=sessions.ready(pending,now=14,active=set())
    assert len(ready)==1 and not running
    report=sessions.finish(*ready[0])
    assert report['complete'] and report['per_frame'] and report['frames']>=50,report
    assert report['average_fps']>0 and report['low_1'] is not None,report
    if seconds>=35:assert report['duration']>=30 and report['grade']!='insufficient',report
    else:assert report['grade']=='insufficient',report
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
    total=math.fsum(milliseconds)
    assert math.isclose(report['average_fps'],1000*len(milliseconds)/total,rel_tol=1e-5)
    assert abs(total/1000-report['duration'])<max(.4,report['duration']*.08),'Frame time/elapsed units disagree'
    worst=sorted(milliseconds,reverse=True)[:math.ceil(len(milliseconds)*.01)]
    assert math.isclose(report['low_1'],1000/(math.fsum(worst)/len(worst)),rel_tol=1e-5)
    assert GameSessions(output/(name+'-state')).report(report['id'])==report
    result={key:report[key] for key in ('frames','duration','average_fps','low_1','low_01','grade','complete')}
    result.update(api=api,bits=bits,visible_overlay_pixels=bright,flatpak=bool(flatpak_app),steam_runtime=bool(steam_runtime))
    result['overlay_startup_seconds']=round(startup_seconds,3)
    print(json.dumps(result),flush=True)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--probe64',default=None)
    parser.add_argument('--probe32',default=None)
    parser.add_argument('--flatpak-app',default=None)
    parser.add_argument('--loader32',default=None)
    parser.add_argument('--steam-runtime',default=None)
    parser.add_argument('--short',action='store_true')
    args=parser.parse_args();output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    assert game_runtime.available(),'Portable MangoHud payload missing'
    shadow=output/'shadow';shadow.mkdir(exist_ok=True)
    bad=shadow/'mangohud';bad.write_text('#!/bin/sh\necho SYSTEM_MANGOHUD_MUST_NOT_BE_USED >&2\nexit 97\n');bad.chmod(0o755)
    probes={}
    for bits,provided in ((64,args.probe64),(32,args.probe32)):
        if provided:probes[bits]=provided;continue
        executable=output/('graphics-probe'+str(bits))
        subprocess.run(['g++','-m'+str(bits),'-std=c++17','-O2',str(ROOT/'tests/native_overlay_probe.cpp'),
                        '-o',str(executable),'-lX11','-lGL','-lvulkan','-pthread'],check=True,timeout=60)
        probes[bits]=str(executable)
    os.environ['QT_QPA_PLATFORM']='xcb'
    from PySide6.QtWidgets import QApplication
    app=QApplication([])
    results=[]
    for bits in (64,32):
        for api in ('gl','vk'):
            seconds=36 if bits==64 and api=='gl' and not args.short else 7
            results.append(record(probes[bits],api,bits,seconds,output,app,args.flatpak_app,args.loader32,args.steam_runtime))
    game_files.write_json(output/'verification.json',dict(bundled_mangohud=True,
        engine=game_runtime.descriptor()['version'],no_system_mangohud=True,cases=results))
    app.quit()


if __name__=='__main__':main()
