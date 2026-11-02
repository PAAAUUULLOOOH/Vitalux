#!/usr/bin/env python3
"""Start shipped Qt inside an untouched Ubuntu base, with networking disabled."""
import argparse,json,subprocess
from pathlib import Path

IMAGE='ubuntu:22.04@sha256:e0f80c829509ef4df9e76bd8944eb7b8ec25cbb379b112a7f9448b2c77a77c9b'

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('runtime',type=Path);parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
 subprocess.run(['docker','pull',IMAGE],check=True)
 script='''import ctypes,json
from PySide6.QtWidgets import QApplication,QLabel
from PySide6.QtNetwork import QNetworkAccessManager
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtOpenGLWidgets import QOpenGLWidget
import psutil,ssl,sqlite3
app=QApplication([]);label=QLabel('Vitalux portable startup');label.show();app.processEvents()
assert not label.grab().isNull()
assert sqlite3.connect(':memory:').execute('select 1').fetchone()==(1,)
for name in ('libsystemd.so.0','libwayland-client.so.0','libwayland-cursor.so.0','libdrm.so.2'):ctypes.CDLL(name)
mapped=[line.split()[-1] for line in open('/proc/self/maps') if '/app/lib/' in line or '/app/fallback-libraries/' in line]
assert any(path.endswith('/libgthread-2.0.so.0') for path in mapped)
assert any(path.endswith('/libglib-2.0.so.0') for path in mapped)
assert any('/app/fallback-libraries/libwayland-client.so.0/' in path for path in mapped)
label.close();app.processEvents()
print(json.dumps(dict(minimal_qt_startup=True,glib_from_package=True,no_network=True,libraries=sorted(set(mapped)))))
'''
 reports=[]
 for missing_crypto in (False,True):
  # Removing files affects only this disposable, network-isolated container.
  prefix=''
  if missing_crypto:
   prefix='for name in libcrypto.so.3 libssl.so.3 libsqlite3.so.0; do for directory in /usr/lib/x86_64-linux-gnu /lib/x86_64-linux-gnu; do if [[ -e "$directory/$name" ]]; then mv "$directory/$name" "/tmp/hidden-$name"; fi; done; done; '
  result=subprocess.run(['docker','run','--rm','--network','none','--mount',
     'type=bind,src='+str(args.runtime.resolve())+',dst=/app,readonly',
     '-e','LD_LIBRARY_PATH=/app/lib','-e','QT_QPA_PLATFORM=offscreen',IMAGE,
     '/bin/bash','-c',prefix+
     'export LD_LIBRARY_PATH="$(/app/runtime/bin/python3.12 /app/packaging/runtime-libraries.py /app)"; exec /app/runtime/bin/python3.12 -c "$1"',
     'vitalux-minimal-startup',script],capture_output=True,text=True,timeout=60)
  (args.output/('fallback-startup.log' if missing_crypto else 'startup.log')).write_text(result.stdout+result.stderr)
  result.check_returncode();report=json.loads(result.stdout.splitlines()[-1])
  if missing_crypto:
   for name in ('libcrypto.so.3','libssl.so.3','libsqlite3.so.0'):
    assert any('/app/fallback-libraries/'+name+'/' in path for path in report['libraries']),name
  reports.append(report)
 report=reports[0];report['missing_host_crypto']=reports[1]
 (args.output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report),flush=True)

if __name__=='__main__':main()
