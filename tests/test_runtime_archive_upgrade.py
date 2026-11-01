"""Changed source-runtime locks replace old cores; corruption preserves them."""
import hashlib,io,os,shutil,subprocess,tarfile,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='vitalux-core-upgrade-') as folder:
    root=Path(folder)
    for part in ('scripts','portable-runtime','bin','runtime/bin','runtime/lib/python3.12'):(root/part).mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/'scripts/ensure-runtime.sh',root/'scripts/ensure-runtime.sh')
    (root/'runtime/bin/python3.12').write_text('legacy core')
    (root/'runtime/lib/python3.12/obsolete.py').write_text('old implementation')
    (root/'bin/fio').write_text('wrapper');(root/'user-profile.json').write_text('keep user preferences')
    def archive(value):
        path=root/'portable-runtime/vitalux-linux-x86_64.tar.xz'
        with tarfile.open(path,'w:xz') as output:
            for name,data in {'runtime/bin/python3.12':value,'runtime/lib/python3.12/current.py':'current',
                'bin/fio.real':'fio','lib/fixture.so':'library','tools-lib/tool.so':'tool','licenses/runtime/fixture.txt':'notice'}.items():
                body=data.encode();entry=tarfile.TarInfo(name);entry.size=len(body);entry.mode=0o755 if '/bin/' in name else 0o644
                output.addfile(entry,io.BytesIO(body))
        (root/'portable-runtime/SHA256SUMS').write_text(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.name+'\n')
    def run():return subprocess.run(['bash',str(root/'scripts/ensure-runtime.sh')],capture_output=True,text=True,timeout=20)
    archive('updated core');result=run();assert result.returncode==0,result.stderr
    assert (root/'runtime/bin/python3.12').read_text()=='updated core'
    assert not (root/'runtime/lib/python3.12/obsolete.py').exists()
    assert (root/'user-profile.json').read_text()=='keep user preferences'
    stamp=(root/'runtime/bin/python3.12').stat().st_mtime_ns
    result=run();assert result.returncode==0,result.stderr
    assert (root/'runtime/bin/python3.12').stat().st_mtime_ns==stamp,'Unchanged core was extracted again'
    archive('next patch');result=run();assert result.returncode==0,result.stderr
    assert (root/'runtime/bin/python3.12').read_text()=='next patch'
    archive('corrupted patch');(root/'portable-runtime/vitalux-linux-x86_64.tar.xz').write_bytes(b'broken')
    result=run();assert result.returncode and 'beschädigt' in result.stderr
    assert (root/'runtime/bin/python3.12').read_text()=='next patch','Bad archive replaced a working core'
    archive('core requiring a valid supplement')
    (root/'portable-runtime/desktop-libraries.SHA256SUMS').write_text('0'*64+'  desktop-libraries-linux-x86_64.tar.xz\n')
    (root/'portable-runtime/desktop-libraries-linux-x86_64.tar.xz').write_bytes(b'damaged supplement')
    result=run();assert result.returncode and 'beschädigt' in result.stderr
    assert (root/'runtime/bin/python3.12').read_text()=='next patch','Bad supplement replaced a working core'
print('Legacy source-core upgrade, stale-module removal, unchanged fast path and corrupt update preservation PASS')
