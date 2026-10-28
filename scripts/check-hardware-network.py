#!/usr/bin/env python3
"""Run independent manufacturer checks with isolated profiles and logs."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def run(case):
    script,args=case
    output=Path('build/hardware-network');output.mkdir(parents=True,exist_ok=True)
    print('START '+script,flush=True)
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='vitalux-hardware-check-') as folder:
        env=os.environ.copy()
        for kind in ('CONFIG','STATE','DATA','CACHE'):
            env['XDG_'+kind+'_HOME']=str(Path(folder)/kind)
        try:
            result=subprocess.run([sys.executable,'scripts/'+script,*args],env=env,
                                  capture_output=True,text=True,timeout=600)
            code,log=result.returncode,result.stdout+result.stderr
        except subprocess.TimeoutExpired as exc:
            code=124;log=(exc.stdout or b'')+(exc.stderr or b'')
            if isinstance(log,bytes):log=log.decode(errors='replace')
            log+='\nManufacturer check exceeded 600 seconds\n'
    (output/(Path(script).stem+'.log')).write_text(log)
    print(('FAIL ' if code else 'PASS ')+script,flush=True)
    print(log[-8000:] if code else log[-2000:],flush=True)
    return dict(script=script,exit_code=code,seconds=round(time.monotonic()-started,2))


if __name__=='__main__':
    cases=(('check-product-image-network.py',['--require-all-components']),
           ('check-product-spec-network.py',['--require-all-components']),
           ('check-spec-translation-network.py',[]))
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,cases))
    Path('build/hardware-network/results.json').write_text(json.dumps(results,indent=2)+'\n')
    raise SystemExit(int(any(row['exit_code'] for row in results)))
