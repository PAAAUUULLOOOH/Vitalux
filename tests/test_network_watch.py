"""Traffic attribution, missing data, warning boundaries and real worker lifetime."""
import os,sys,tempfile,time,struct
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer,QCoreApplication,QEvent
from PySide6.QtWidgets import QApplication
from vitalux import settings,i18n
from vitalux.network_kernel import application,parse_diag,packet_program,socket_program
from vitalux.network_monitor import TrafficLedger
from vitalux.network_ui import NetworkWatch


def row(cookie,rx,tx,key='/usr/bin/example',protocol='TCP'):
    return dict(cookie=cookie,rx=rx,tx=tx,key=key,name='example',exe=key,pid=123,
                start=12,protocol=protocol,local='127.0.0.1',local_port=100,
                remote='127.0.0.1',remote_port=200,state='ESTABLISHED')


def check_ledger():
    ledger=TrafficLedger()
    a=row(11,5000,2000)
    ledger.ingest(dict(monotonic=10,connections=[a],backend='tcp'))
    assert ledger.apps[a['key']]['total_down']==0,'Counted pre-monitor historical usage'
    a=row(11,6024,4048)
    warnings=ledger.ingest(dict(monotonic=12,connections=[a],backend='tcp'),{a['key']:3000})
    app=ledger.apps[a['key']]
    assert app['down']==512 and app['up']==1024
    assert app['total_down']==1024 and app['total_up']==2048
    assert len(warnings)==1
    assert not ledger.ingest(dict(monotonic=13,connections=[a],backend='tcp'),{a['key']:3000})
    b=row(12,None,None,protocol='UDP')
    ledger.ingest(dict(monotonic=14,connections=[a,b],backend='tcp'))
    assert ledger.apps[a['key']]['partial']
    assert ledger.apps[a['key']]['connections']==2
    unknown=row(13,None,None,key='/usr/bin/udp-only',protocol='UDP')
    ledger.ingest(dict(monotonic=15,connections=[unknown],backend='tcp'))
    assert ledger.apps[unknown['key']]['down'] is None
    assert ledger.apps[unknown['key']]['up'] is None
    # Changing transport measurement types must not mix their baselines.
    ledger.ingest(dict(monotonic=16,connections=[a],counters=[row(99,10000,20000)],backend='bpf'))
    assert ledger.apps[a['key']]['total_down']==0
    ledger.ingest(dict(monotonic=17,connections=[],counters=[row(99,11000,22000)],backend='bpf'))
    assert ledger.apps[a['key']]['total_down']==1000
    assert ledger.apps[a['key']]['total_up']==2000
    # Validate the Linux TCP_INFO offsets, including older acknowledged-byte fallback.
    payload=bytearray(72)
    payload[0]=2;payload[1]=1
    struct.pack_into('=Q',payload,44,1234)
    info=bytearray(208)
    struct.pack_into('=Q',info,128,87654)
    struct.pack_into('=Q',info,200,123456)
    payload+=struct.pack('=HH',212,2)+info
    parsed=parse_diag(payload,'TCP')
    assert parsed['rx']==87654 and parsed['tx']==123456
    assert parse_diag(payload,'UDP')['rx'] is None
    assert application(os.getpid(),os.getuid())['pid']==os.getpid()
    assert application(os.getpid(),os.getuid()+1000000) is None
    for code in (packet_program(1000,4,5,6,'rx'),packet_program(1000,4,5,6,'tx'),socket_program(1000,4,5)):
        assert len(code)%8==0 and code[-8]==0x95


def check_ui():
    app=QApplication.instance() or QApplication([])
    previous=settings.PATH
    with tempfile.TemporaryDirectory() as folder:
        settings.PATH=str(Path(folder)/'settings.json')
        watch=NetworkWatch()
        watch.resize(1000,900)
        watch.show()
        errors=[]
        def finish():
            try:
                assert watch.ledger.stamp is not None,'Live sampler never reached UI'
                assert watch.worker.isRunning()
                for language in ('de','en'):
                    i18n.set_lang(language);watch.retranslate()
                    assert watch.table.horizontalHeaderItem(0).text()==('Programm' if language=='de' else 'Application')
                watch.ledger.rules={'/usr/bin/example'}
                watch._reset()
                assert '/usr/bin/example' in watch.ledger.rules
                watch.shutdown();assert watch.worker.wait(4000)
                watch.resume_after_shutdown()
                assert watch.worker.isRunning(),'Failed restart did not resume app monitoring'
                # Exercise Qt's actual asynchronous PTR API and cancel on close.
                watch.ledger.connections=[row(91,None,None)]
                watch._key='/usr/bin/example'
                watch._resolve()
                assert '127.0.0.1' in watch._lookups or '127.0.0.1' in watch._names
            except BaseException as exc:errors.append(exc)
            finally:
                watch.shutdown()
                assert not watch._lookups,'PTR queries survived shutdown'
                assert watch.worker.wait(4000)
                watch.hide()
                app.quit()
        QTimer.singleShot(1600,finish)
        app.exec()
        watch.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
        app.processEvents()
        settings.PATH=previous
        if errors:raise errors[0]

if __name__=='__main__':
    check_ledger();check_ui()
    print('Per-app traffic, baselines, budgets, unknown UDP, UID ownership and worker shutdown PASS')
