#!/usr/bin/env python3
"""Read actual KWin placement for repeated startup dialogs in an isolated session."""
import argparse,json,os,re,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--kwin-log',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
def dbus(path,method,*values):
 result=subprocess.run(['dbus-send','--session','--print-reply','--dest=org.kde.KWin',path,method,*values],capture_output=True,text=True,timeout=8)
 assert result.returncode==0,(result.stdout,result.stderr)
 return result.stdout
script=args.output.resolve()/'placement.js'
script.write_text('''function watch(w) {
    print("VITALUX_CLIENT " + w.caption);
    if (w.caption !== "Vitalux") return;
    function report() {
        var r = w.frameGeometry;
        print("VITALUX_POSITION " + JSON.stringify({x:r.x,y:r.y,width:r.width,height:r.height,dialog:w.dialog,modal:w.modal}));
    }
    w.frameGeometryChanged.connect(report);
    report();
}
if (workspace.windowAdded) workspace.windowAdded.connect(watch);
else workspace.clientAdded.connect(watch);
var windows = workspace.windowList ? workspace.windowList() : workspace.clientList();
for (var i=0;i<windows.length;++i) watch(windows[i]);
''')
reply=dbus('/Scripting','org.kde.kwin.Scripting.loadScript','string:'+str(script))
match=re.search(r'int32\s+(\d+)',reply);assert match,reply
identifier=match[1];dbus('/Scripting/Script'+identifier,'org.kde.kwin.Script.run')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from vitalux.startup import StartupWindow
from vitalux import theme,settings
app=QApplication([]);app.setQuitOnLastWindowClosed(False);settings.set_many(dict(motion='off',component_images=False));theme.set_mode('obsidian_gold');app.setStyleSheet(theme.stylesheet())
def wait(ms):
 deadline=time.monotonic()+ms/1000
 while time.monotonic()<deadline:app.processEvents();time.sleep(.01)
def records():
 result=[]
 for line in args.kwin_log.read_text(errors='replace').splitlines():
  if 'VITALUX_POSITION ' not in line:continue
  try:result.append(json.JSONDecoder().raw_decode(line.split('VITALUX_POSITION ',1)[1])[0])
  except ValueError:pass
 return result
other=subprocess.Popen([sys.executable,'-c','from PySide6.QtWidgets import QApplication,QWidget;app=QApplication([]);w=QWidget();w.setWindowTitle("Placement occupier");w.resize(700,500);w.show();app.exec()'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
results=[]
try:
 deadline=time.monotonic()+5
 while 'VITALUX_CLIENT Placement occupier' not in args.kwin_log.read_text(errors='replace') and time.monotonic()<deadline:wait(30)
 assert other.poll() is None and 'VITALUX_CLIENT Placement occupier' in args.kwin_log.read_text(errors='replace')
 for case in range(3):
  before=len(records());window=StartupWindow();window.show();wait(1400)
  events=records()[before:];assert events,'KWin supplied no placement observation: '+args.kwin_log.read_text(errors='replace')[-6000:]
  observed=events[-1];screen=window.screen().availableGeometry()
  assert abs(observed['x']+observed['width']/2-screen.center().x())<=3,observed
  assert abs(observed['y']+observed['height']/2-screen.center().y())<=3,observed
  assert window.windowModality()==Qt.ApplicationModal
  assert window.isMaximized()
  card=window.card.geometry()
  assert abs(observed['x']+card.center().x()-screen.center().x())<=3,(observed,card)
  assert abs(observed['y']+card.center().y()-screen.center().y())<=3,(observed,card)
  observed['visible_card']=[card.x(),card.y(),card.width(),card.height()]
  window.grab().save(str(args.output/('initialization-'+str(case)+'.png')))
  results.append(observed);window.ready=True;window.close();window.deleteLater();wait(100)
finally:
 other.terminate();other.wait(timeout=5)
(args.output/'placement.json').write_text(json.dumps(results,indent=2)+'\n')
print('Three actual KWin startup placements centered after occupied-session launches:',json.dumps(results),flush=True)
