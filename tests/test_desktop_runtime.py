"""Offline supplementary libraries also repair an already-expanded runtime."""
import ctypes.util,hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from desktop_runtime import check,manifest

meta=manifest(ROOT)
assert {'libgthread-2.0.so.0','libglib-2.0.so.0','libxkbcommon.so.0'}<={entry['name'] for entry in meta['libraries']}
archive=ROOT/'portable-runtime'/meta['archive']
def check_preference(root):
 for entry in meta['libraries']:
  if 'path' in entry:assert not (root/'lib'/entry['name']).exists(),'Fallback shadows the graphics driver'
 if all(ctypes.util.find_library(name) for name in ('wayland-client','wayland-cursor','drm')):
  selected=subprocess.check_output([sys.executable,str(ROOT/'packaging/runtime-libraries.py'),str(root)],
      env=dict(os.environ,LD_LIBRARY_PATH=str(root/'lib')),text=True).strip()
  assert 'fallback-libraries' not in selected,selected

# The binary package contains expanded libraries, without redundant archives.
# Its regression pass verifies those actual files; source bootstrap is tested
# separately before assembly and again by the full offline source-ZIP check.
if not archive.exists():
 assert (ROOT/'runtime/bin/python3.12').is_file(),'Missing source supplement'
 check(ROOT,ROOT);check_preference(ROOT)
 print('Expanded packaged desktop libraries and native driver interface preference PASS')
 sys.exit(0)
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
 # On a desktop that provides these interfaces, prefer the actual host ABI.
 check_preference(root)
 dll=root/'lib/libgthread-2.0.so.0';before=dll.stat().st_mtime_ns
 subprocess.run(['bash',str(root/'scripts/ensure-runtime.sh')],check=True,capture_output=True)
 assert dll.stat().st_mtime_ns==before,'Re-extracted unchanged libraries'
 checksum.write_text('0'*64+'  '+archive.name+'\n')
 result=subprocess.run(['bash',str(root/'scripts/ensure-runtime.sh')],capture_output=True,text=True)
 assert result.returncode!=0 and 'beschädigt' in result.stderr
 assert dll.stat().st_mtime_ns==before,'Damaged archive altered the installed runtime'
print('Portable GLib/thread libraries, existing-runtime repair, repeat launch and bad-checksum rejection PASS')
