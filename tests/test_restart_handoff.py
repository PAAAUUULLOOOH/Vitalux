"""The real ZIP launcher honors only its own completed restart, even after SIGSEGV."""
import os,resource,shlex,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vitalux import restart_protocol
with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'request';path.touch(mode=0o600)
    token=restart_protocol.initialize(path,ROOT,123,'test')
    assert not restart_protocol.requested(path,ROOT,123,'test',token)
    try:restart_protocol.requested(path,ROOT,124,'test',token)
    except RuntimeError:pass
    else:raise AssertionError('Accepted another launcher’s restart')
for intentional in (False,True):
    with tempfile.TemporaryDirectory(prefix='vitalux-restart-handoff-') as folder:
        root=Path(folder);(root/'runtime/bin').mkdir(parents=True)
        shutil.copy2(ROOT/'run.sh',root/'run.sh')
        for name in ('vitalux','packaging'):(root/name).symlink_to(ROOT/name,target_is_directory=True)
        driver=root/'driver.py'
        driver.write_text('''import os,resource,signal,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from vitalux.restart_protocol import ready
path=Path('phase');phase=int(path.read_text())+1 if path.exists() else 1;path.write_text(str(phase))
if phase==1:
 if os.environ['TEST_INTENTIONAL']=='1':assert ready()
 resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.kill(os.getpid(),signal.SIGSEGV)
''')
        executable=root/'runtime/bin/python3.12'
        executable.write_text('#!/bin/sh\nif [ "$1" = -c ]; then exit 0; fi\nif [ "$1" = -m ]; then exec '+shlex.quote(sys.executable)+' '+shlex.quote(str(driver))+'; fi\nexec '+shlex.quote(sys.executable)+' "$@"\n');executable.chmod(0o755)
        env=dict(os.environ,TEST_INTENTIONAL=str(int(intentional)),VITALUX_GUARDED='1',VITALUX_GPU_RECOVERY='1')
        for kind in ('CONFIG','STATE','CACHE','DATA'):env['XDG_'+kind+'_HOME']=str(root/kind.lower())
        result=subprocess.run(['bash',str(root/'run.sh')],cwd=root,env=env,capture_output=True,text=True,timeout=12)
        assert result.returncode==(0 if intentional else 139),(result.returncode,result.stdout,result.stderr)
        if intentional:assert not result.stderr,'Prepared restart leaked an unstamped native-crash diagnostic'
        assert (root/'phase').read_text()==('2' if intentional else '1')
        assert not list((root/'state').rglob('.restart-request.*'))
        logs='\n'.join(path.read_text() for path in (root/'state').rglob('errors.log'))
        assert '139' in logs,'Lost the native shutdown failure record'
print('Nonce/launch-bound handoff, actual SIGSEGV after committed restart, rejected startup crash and cleanup PASS')
