"""Offline supplementary libraries also repair an already-expanded runtime."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from desktop_runtime import check,manifest

meta=manifest(ROOT)
assert {'libgthread-2.0.so.0','libglib-2.0.so.0','libxkbcommon.so.0'}<={entry['name'] for entry in meta['libraries']}
archive=ROOT/'portable-runtime'/meta['archive']
with archive.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==meta['sha256']
with tempfile.TemporaryDirectory(prefix='vitalux-offline-desktop-') as folder:
 root=Path(folder)
 for name in ('scripts','portable-runtime','runtime/bin'):root.joinpath(name).mkdir(parents=True)
 shutil.copyfile(ROOT/'scripts/ensure-runtime.sh',root/'scripts/ensure-runtime.sh')
 shutil.copyfile(archive,root/'portable-runtime'/archive.name)
 checksum=root/'portable-runtime/desktop-libraries.SHA256SUMS'
 shutil.copyfile(ROOT/'portable-runtime/desktop-libraries.SHA256SUMS',checksum)
 (root/'runtime/bin/python3.12').write_text('# Existing Python must not skip desktop-library repair\n')
 result=subprocess.run(['bash',str(root/'scripts/ensure-runtime.sh')],capture_output=True,text=True)
 assert result.returncode==0,result.stderr
 check(root,ROOT)
 dll=root/'lib/libgthread-2.0.so.0';before=dll.stat().st_mtime_ns
 subprocess.run(['bash',str(root/'scripts/ensure-runtime.sh')],check=True,capture_output=True)
 assert dll.stat().st_mtime_ns==before,'Re-extracted unchanged libraries'
 checksum.write_text('0'*64+'  '+archive.name+'\n')
 result=subprocess.run(['bash',str(root/'scripts/ensure-runtime.sh')],capture_output=True,text=True)
 assert result.returncode!=0 and 'beschädigt' in result.stderr
 assert dll.stat().st_mtime_ns==before,'Damaged archive altered the installed runtime'
print('Portable GLib/thread libraries, existing-runtime repair, repeat launch and bad-checksum rejection PASS')
