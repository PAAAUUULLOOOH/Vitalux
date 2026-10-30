"""Portable and AppImage files remain usable by a UID other than their builder."""
import json,os,stat,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from distribution_tools import normalize_permissions
with tempfile.TemporaryDirectory(prefix='vitalux-package-modes-') as folder:
 root=Path(folder);stage=root/'stage';stage.mkdir(mode=0o700)
 foreign=root/'personal-file';foreign.write_bytes(b'private');foreign.chmod(0o600)
 for name in ('run.sh','runtime/bin/python3.12','vitalux/__main__.py','assets/vitalux.svg','tools-lib/libaio.so.1'):
  p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture');p.chmod(0o700 if name.endswith('.so.1') else 0o600)
 (stage/'outside-link').symlink_to(foreign)
 normalize_permissions(stage)
 for path in (stage,*stage.rglob('*')):
  if path.is_symlink():continue
  mode=stat.S_IMODE(path.stat().st_mode);assert mode&0o444==0o444
  if path.is_dir() or mode&0o111:assert mode&0o111==0o111
 assert stat.S_IMODE(foreign.stat().st_mode)==0o600 and foreign.read_bytes()==b'private'
 library=stage/'tools-lib/libaio.so.1';library.chmod(0o700)
 tool=root/'inspect-tool';tool.write_text('#!'+sys.executable+'\n'+'''import json,stat,sys
from pathlib import Path
appdir=Path(sys.argv[-2]);output=Path(sys.argv[-1]);checked=0
for p in (appdir,*appdir.rglob('*')):
 if p.is_symlink():continue
 mode=stat.S_IMODE(p.stat().st_mode);assert mode&0o444==0o444,(p,mode)
 if p.is_dir() or mode&0o111:assert mode&0o111==0o111,(p,mode)
 checked+=1
output.write_bytes(b'checked AppImage fixture')
output.with_suffix('.json').write_text(json.dumps(dict(paths=checked)))
''');tool.chmod(0o755)
 output=root/'built.AppImage'
 result=subprocess.run(['bash',str(ROOT/'packaging/build-appimage.sh'),str(stage),str(output),str(tool)],capture_output=True,text=True,timeout=15)
 assert result.returncode==0,(result.stdout,result.stderr)
 assert output.stat().st_mode&0o111 and json.loads(output.with_suffix('.json').read_text())['paths']>5
 assert stat.S_IMODE(library.stat().st_mode)==0o700,'Builder modified the source installation'
 assert library.read_bytes()==b'fixture' and stat.S_IMODE(foreign.stat().st_mode)==0o600
print('Portable/AppImage public readability, executable bits, restrictive archived library, source immutability and external-symlink protection PASS')
