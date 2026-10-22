"""Real bounded logs, concurrent records, shell rotation and native crash handles."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vitalux import logfiles

with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);path=root/'errors.log'
    with path.open('ab') as native:
        inode=path.stat().st_ino
        logfiles.append(path,'old record\n',limit=20)
        logfiles.append(path,'new complete record\n',limit=20)
        assert Path(str(path)+'.1').read_text()=='old record\n'
        assert path.stat().st_ino==inode
        native.write(b'native trace\n');native.flush()
        assert 'native trace' in path.read_text()
    logfiles.append(path,'final record\n',limit=20)
    assert path.read_text()=='final record\n'
    assert 'new complete record\nnative trace' in Path(str(path)+'.1').read_text()
    parallel=root/'parallel.log'
    with ThreadPoolExecutor(max_workers=4) as workers:
        list(workers.map(lambda i:logfiles.append(parallel,f'{i:04d} '+('x'*100)+'\n',limit=1000),range(100)))
    for p in (parallel,Path(str(parallel)+'.1')):
        assert p.stat().st_size<=1000
        assert all(len(line)==105 and line[5:]=='x'*100 for line in p.read_text().splitlines())
    shell=root/'launcher.log';shell.write_bytes(b'x'*logfiles.MAX_BYTES)
    subprocess.run(['bash','-c','source "$1"; vitalux_log_line "$2" test "new launch"',
                    'bash',str(ROOT/'packaging/logging.sh'),str(shell)],check=True)
    assert Path(str(shell)+'.1').stat().st_size==logfiles.MAX_BYTES
    assert 'new launch' in shell.read_text() and shell.stat().st_size<200
    # A real native crash must still write through the old open descriptor.
    env={**os.environ,'XDG_STATE_HOME':str(root/'state'),'PYTHONPATH':str(ROOT)}
    code='''import os,resource
from vitalux import diagnostics,logfiles
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
diagnostics.enable_native_crash_trace()
inode=diagnostics.LOG_PATH.stat().st_ino
logfiles.append(diagnostics.LOG_PATH,'after rotation\\n',limit=1)
assert diagnostics.LOG_PATH.stat().st_ino==inode
os.abort()
'''
    crash=subprocess.run([sys.executable,'-c',code],env=env,capture_output=True,timeout=15)
    assert crash.returncode==-6,crash.stderr
    files=list((root/'state').rglob('errors.log'))
    assert len(files)==1 and 'Fatal Python error: Aborted' in files[0].read_text()
    assert Path(str(files[0])+'.1').exists()
print('5 MB shell rotation, single backup, concurrent complete records and real post-rotation SIGABRT trace PASS')
