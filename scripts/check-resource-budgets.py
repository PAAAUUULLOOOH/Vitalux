#!/usr/bin/env python3
"""Exercise actual caches and hidden traffic ingestion under explicit resource budgets."""
import json,os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication
from vitalux import backdrops,design_catalog,settings
from vitalux.network_ui import NetworkWatch
from unittest.mock import patch
app=QApplication([])
with tempfile.TemporaryDirectory(prefix='vitalux-budgets-') as directory:
    settings.PATH=str(Path(directory)/'settings.json')
    for key in design_catalog.PRESETS:
        sharp,soft=backdrops.render(QSize(1380,1000),key)
        assert not sharp.isNull() and not soft.isNull()
        assert backdrops._IMAGE_CACHE.bytes<=24*1024*1024
    watch=NetworkWatch();rendered=[];alerts=[]
    original=watch._render
    def render():rendered.append(1);return original()
    watch._render=render;watch.alert.connect(lambda *value:alerts.append(value))
    key='/fixture/application';watch._limits={key:1000}
    def sample(stamp,value):
        return dict(monotonic=stamp,backend='tcp',connections=[dict(cookie=1,key=key,name='fixture',exe=key,pid=123,start=1,rx=value,tx=value,protocol='TCP',local='127.0.0.1',local_port=1,remote='127.0.0.1',remote_port=2,state='ESTABLISHED')])
    for i in range(30):watch._ingest(sample(i+1,i*100))
    assert not rendered,'Hidden tab rebuilt UI'
    assert watch.ledger.apps[key]['total_down']==2900 and len(alerts)==1
    with patch.object(watch,'_start_sampler',lambda:None):
        watch.show();app.processEvents()
        assert watch.table.rowCount()==1
        cell=watch.table.item(0,0)
        watch._ingest(sample(32,3100));assert watch.table.item(0,0) is cell
        watch.hide();rendered.clear()
        watch._ingest(sample(33,3200));assert not rendered
    watch.shutdown()
    print(json.dumps(dict(background_cache_bytes=backdrops._IMAGE_CACHE.bytes,budget_bytes=24*1024*1024,hidden_table_rebuilds=0,hidden_traffic_bytes=watch.ledger.apps[key]['total_down'],warnings=len(alerts),table_cells_reused=True)))
