"""Reproduce the COSMIC LIBSYSTEMD_254 collision with an actual versioned ELF."""
import ctypes,ctypes.util,json,os,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from desktop_runtime import materialize

with tempfile.TemporaryDirectory(prefix='vitalux-systemd-') as folder:
    target=Path(folder)/'app'
    if (ROOT/'portable-runtime/desktop-libraries-linux-x86_64.tar.xz').exists():
        materialize(target,ROOT)
    else:target=ROOT
    legacy=target/'fallback-libraries/libsystemd.so.0/libsystemd.so.0'
    assert legacy.is_file() and not (target/'lib/libsystemd.so.0').exists()
    env=dict(os.environ,LD_LIBRARY_PATH=str(target/'lib'))
    selected=subprocess.check_output([sys.executable,str(ROOT/'packaging/runtime-libraries.py'),str(target)],env=env,text=True).strip()
    host=ctypes.util.find_library('systemd')
    modern=False
    if host:
        try:modern=bool(getattr(ctypes.CDLL(host),'sd_event_trim_memory',None))
        except OSError:pass
    if modern and shutil.which('cc'):
        assert str(legacy.parent) not in selected,'Old private systemd shadows the desktop'
        source=Path(folder)/'consumer.c';consumer=Path(folder)/'cosmic-consumer.so'
        source.write_text('extern int sd_event_trim_memory(void);\nint require_systemd_254(void) { return sd_event_trim_memory(); }\n')
        subprocess.run(['cc','-shared','-fPIC',str(source),'-Wl,-l:libsystemd.so.0','-o',str(consumer)],check=True,timeout=30)
        probe='import ctypes,sys;ctypes.CDLL(sys.argv[1])'
        broken=subprocess.run([sys.executable,'-c',probe,str(consumer)],env=dict(env,LD_LIBRARY_PATH=str(legacy.parent)+os.pathsep+str(target/'lib')),capture_output=True,text=True,timeout=15)
        assert broken.returncode and 'LIBSYSTEMD_254' in broken.stderr,broken.stderr
        fixed=subprocess.run([sys.executable,'-c',probe,str(consumer)],env=dict(env,LD_LIBRARY_PATH=selected),capture_output=True,text=True,timeout=15)
        assert fixed.returncode==0,fixed.stderr
        print('Exact LIBSYSTEMD_254 failure reproduced; host preference loads the same ELF successfully')
    else:
        print('Host lacks the 254 interface/compiler; baseline library placement and offline fallback checked')
    # Exercise the missing-host path without hiding unrelated desktop libraries.
    spec=__import__('importlib.util',fromlist=['spec_from_file_location'])
    module=spec.module_from_spec(spec.spec_from_file_location('runtime_libraries',ROOT/'packaging/runtime-libraries.py'))
    module.__spec__.loader.exec_module(module)
    original=module.ctypes.CDLL;calls=[]
    def absent(name,*args,**kwargs):
        calls.append(str(name))
        if name=='libsystemd.so.0':raise OSError('absent on minimal desktop')
        return original(name,*args,**kwargs)
    from unittest.mock import patch
    with patch.object(module.ctypes,'CDLL',absent),patch.dict(os.environ,{'LD_LIBRARY_PATH':str(target/'lib')}):
        fallback=module.library_path(target)
    assert str(legacy.parent) in fallback and str(legacy) in calls
    subprocess.run([sys.executable,'-c','import ctypes;ctypes.CDLL("libsystemd.so.0")'],env=dict(env,LD_LIBRARY_PATH=fallback),check=True,timeout=15)
print('Host systemd ABI and usable offline fallback PASS')
