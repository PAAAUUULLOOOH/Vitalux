"""Fresh equivalent/contained releases return automatically; all other cases stay put."""
import os,sys,tempfile,copy,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from vitalux import profiles,update_manager,updater
app=QApplication.instance() or QApplication([])
source='0.9.6.3-unstable.24';target='0.9.6.3'
base=dict(stable=dict(ok=True,latest=target,channel='stable',eligible=True,newer=True,url='https://example.invalid/verified.zip',sha256='a'*64),
          unstable=dict(ok=True,latest=source,channel='unstable',eligible=False,has_test_changes=False,stable_version=target,stable_verified=True,manifest_verified=True,same_as_stable=True))
with tempfile.TemporaryDirectory() as folder,patch.object(update_manager,'__version__',source),patch.object(profiles,'__version__',source),patch.object(profiles,'installed',return_value='unstable'),patch.object(profiles,'directory',side_effect=lambda *_:Path(folder)),patch.object(profiles,'root',side_effect=lambda *_:Path(folder)):
 for kind in ('valid','contained','baseline','baseline_without_coverage','uncovered_future','has_changes','stale_baseline','missing_manifest','offline','missing_test','stable_too_old','old_test','new_test'):
  m=update_manager.UpdateManager();m._timer.stop();data=copy.deepcopy(base)
  if kind=='contained':data['unstable'].update(same_as_stable=False,stable_contains_test=True)
  if kind in ('baseline','baseline_without_coverage','uncovered_future'):
   data['unstable'].update(latest=target,covered_test_version=source)
   if kind=='baseline_without_coverage':data['unstable'].pop('covered_test_version')
   if kind=='uncovered_future':data['unstable']['covered_test_version']='0.9.6.3-unstable.23'
  if kind=='has_changes':data['unstable']['has_test_changes']=True
  if kind=='stale_baseline':data['unstable']['stable_version']='0.9.6.2'
  if kind=='missing_manifest':data['unstable'].pop('manifest_verified')
  if kind=='offline':data['stable']=dict(ok=False,error='offline')
  if kind=='missing_test':data['unstable']=dict(ok=True,latest='',eligible=False)
  if kind=='stable_too_old':data['stable']['latest']='0.9.6.2';data['unstable']['stable_version']='0.9.6.2'
  if kind=='old_test':data['unstable']['latest']='0.9.6.3-unstable.23'
  if kind=='new_test':data['unstable'].update(latest='0.9.6.4-unstable.1',eligible=True,has_test_changes=True)
  with patch.object(m,'install') as install:
   m._on_checked(data);app.processEvents();app.processEvents()
   assert install.call_count==int(kind in ('valid','contained','baseline')),kind
   if install.called:
    assert m.channel=='stable' and m.latest==target
    m._on_checked(data);app.processEvents();assert install.call_count==1
  m.shutdown();m.deleteLater();app.processEvents()
 # Exercise the actual asynchronous install and automatic restart path.
 m=update_manager.UpdateManager();m._timer.stop();restarts=[];m.restart.connect(lambda:restarts.append(dict(m.pending)))
 with patch.object(updater,'install',return_value=None) as install,patch.object(updater,'appimage_path',return_value=''):
  m._on_checked(copy.deepcopy(base))
  deadline=time.monotonic()+4
  while not restarts and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
  assert len(restarts)==1 and restarts[0]['version']==target and restarts[0]['channel']=='stable'
  assert install.call_count==1 and install.call_args.kwargs['defer'] is True
  m._pending_file.unlink(missing_ok=True)
  while not m.shutdown() and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
 m.deleteLater();app.processEvents()
 # Cached data and merely browsing a channel must never initiate a return.
 m=update_manager.UpdateManager();m._timer.stop();m.records=copy.deepcopy(base)
 for record in m.records.values():record['stale']=True
 with patch.object(m,'install') as install:
  m.set_channel('stable');app.processEvents();assert not install.called
 m.shutdown();m.deleteLater();app.processEvents()
with patch.object(profiles,'installed',return_value='stable'):
 m=update_manager.UpdateManager();m._timer.stop()
 with patch.object(m,'install') as install:m._on_checked(base);app.processEvents();assert not install.called
 m.shutdown()
print('Automatic Stable return: fresh parity/containment, no replay, no cache/offline/older/new-test activation, Stable stays Stable PASS')
