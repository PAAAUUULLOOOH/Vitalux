"""Accurate adapter accounting, indexed sessions, real frame evidence and caches."""
import os,sys,tempfile,json,hashlib,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from vitalux import sensors,settings,game_files,i18n
from vitalux.game_sessions import GameSessions,has_frame_data
from vitalux.image_cache import ImageCache,memory_usage,TOTAL_BYTES
from vitalux.session_comparison import SessionComparison,metrics
app=QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    ctr=lambda rx,tx:SimpleNamespace(bytes_recv=rx,bytes_sent=tx)
    stats={name:SimpleNamespace(isup=True,speed=1000,mtu=1500) for name in ('eth0','tun0')}
    counters={'eth0':ctr(1000,500),'tun0':ctr(900,400)}
    route=dict(route_interface='eth0',gateway='1.2.3.4',dns=[])
    clock=[10.]
    with patch.object(sensors.psutil,'net_if_stats',return_value=stats),patch.object(sensors.psutil,'net_if_addrs',return_value={}),\
         patch.object(sensors.psutil,'net_io_counters',side_effect=lambda **kw:counters if kw.get('pernic') else ctr(1900,900)),\
         patch.object(sensors.extended,'net_static_details',return_value=route),patch.object(sensors.time,'monotonic',side_effect=lambda:clock[0]):
        sensors._last.clear();first=sensors.network_info()
        assert first['source']=='eth0' and first['total_down']==1000
        clock[0]=11.;counters['eth0']=ctr(1120,550);counters['tun0']=ctr(1010,450)
        second=sensors.network_info();assert second['down']==120 and second['up']==50
        settings.set('network_interface','tun0')
        clock[0]=12.;counters['tun0']=ctr(1100,470)
        chosen=sensors.network_info();assert chosen['source']=='tun0' and chosen['down']==90
        del counters['tun0'];del stats['tun0']
        missing=sensors.network_info();assert missing['down'] is None and missing['primary'] is None
        settings.set('network_interface','all');assert sensors.network_info()['source']=='all'
    assert sensors.fmt_bytes(2**30)=='1.0 GiB' and sensors.fmt_bytes(10**9,1000)=='1.0 GB'
    game=dict(id='steam:42',name='Example',store='steam',installed=True)
    store=GameSessions(Path(folder)/'games');bridge=Path(folder)/'bridge'
    store.update_inventory([game]);store.register(game,bridge)
    sessions=bridge/'sessions';sessions.mkdir(parents=True)
    for index in range(80):
        done=sessions/f'session.{index:04}';done.mkdir();(done/'processed').write_text('x')
    active=sessions/'session.Z';active.mkdir();game_files.write_json(active/'game.json',dict(game=game,profile={}))
    assert len(store.pending())==1
    with patch.object(Path,'glob',side_effect=AssertionError('Rescanned unchanged session roots')):
        assert store.pending()[0][0]==active
    csv=active/'game.csv';csv.write_text('fps,frametime\nnot-a-frame,broken\n')
    assert not has_frame_data(csv)
    csv.write_text('fps,frametime\n60,16.67\n');assert has_frame_data(csv)
    csv.write_text('fps,frametime\nnan,16.67\n');assert not has_frame_data(csv)
    old=time.time()-32*86400
    cleanup={}
    for name in ('obsolete','retained','recent','unknown'):
        directory=sessions/('session.'+name);directory.mkdir()
        report_id=hashlib.sha256(str(directory.resolve()).encode()).hexdigest()[:32]
        marker=directory/'processed';marker.write_text(report_id+'\n')
        os.utime(marker,(old,old))
        if name=='unknown':(directory/'keep.txt').write_text('unrecognised user data')
        if name=='recent':marker.touch()
        os.utime(directory,(old,old));cleanup[name]=(directory,report_id)
    store.summaries=[dict(id=cleanup['retained'][1])]
    store.prune_raw()
    assert not cleanup['obsolete'][0].exists()
    assert all(cleanup[name][0].exists() for name in ('retained','recent','unknown'))
    a=dict(id='a'*32,game_id=game['id'],game_name='Example',started=1,target_fps=60,average_fps=60,low_1=50,low_01=40,long_frame_ratio=.01,complete=True)
    b=dict(a,id='b'*32,started=2,target_fps=120,average_fps=80)
    comparison=SessionComparison([b,a]);comparison.refresh()
    assert comparison.cells[0][2].text()=='+20.00 FPS'
    assert abs(metrics(a)[3]-1000/60)<.001
    assert comparison.note.isVisible() is False  # parent is not shown yet
    assert 'FPS' in comparison.note.text()
    i18n.set_lang('en');comparison.refresh();assert 'Different FPS targets' in comparison.note.text()
    i18n.set_lang('de');comparison.close()
    one,two=ImageCache(32*1024*1024,32),ImageCache(32*1024*1024,32)
    image=QImage(1024,1024,QImage.Format_RGB32);image.fill(0xff123456)
    for index in range(8):one[index]=QImage(image)
    for index in range(8):two[index]=QImage(image)
    assert memory_usage()<=TOTAL_BYTES
    assert two.get(7).pixel(512,512)==image.pixel(512,512)
    assert len(one)<8 and two.get(7).size()==image.size()
print('Adapter traffic/source disappearance, indexed sessions, actual CSV evidence, comparison and shared full-resolution cache budget PASS')
