"""Real regressions: lost sensors, false recovery, stale data, cache bounds and user choices."""
import os,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from vitalux import settings,diagnostic_engine as engine,i18n,product_images,sensors
from vitalux.sensor_page import SensorsPage
from vitalux.image_cache import ImageCache
from vitalux.sample_state import SamplingState
from vitalux.page_base import Page
from vitalux.charts import ChartPanel
from vitalux.monitoring import SessionExtrema
from vitalux.gpu_selection import ordered
app=QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as directory,patch.object(settings,'PATH',str(Path(directory)/'settings.json')):
    page=SensorsPage()
    readings=[dict(id=str(i),name='Same label',value=i,unit='°C',source='fixture') for i in range(121)]
    page.refresh(dict(sensors=dict(temps=readings)),{})
    assert len(page.rows['temps'])==121
    assert all(not row.isHidden() for row in page.rows['temps'].values())
    page.refresh(dict(sensors=dict(temps=readings[1:])),{})
    assert page.rows['temps']['0'].isHidden() and not page.rows['temps']['120'].isHidden()
    with patch.object(engine,'BLACKBOX',Path(directory)/'blackbox.jsonl'),patch.object(engine,'STATE_DIR',Path(directory)):
        settings.set('diag_blackbox_enabled',True)
        recorder=engine.BlackboxRecorder()
        for temperature in (100,None,None,40):
            recorder.ingest(dict(cpu=dict(temp=temperature),ram={},gpus=[]))
        records=[json.loads(line) for line in engine.BLACKBOX.read_text().splitlines()]
        cpu=[row for row in records if row.get('metric')=='cpu_temp']
        assert [row['event'] for row in cpu]==['Warnwert überschritten','Messwert nicht verfügbar','Entwarnung'],cpu
    state=SamplingState().success(100)
    assert not state.stale(101,1) and state.stale(106,1)
    assert state.failed('driver unavailable').stale(101,1)
    assert not state.failed('driver unavailable').success(107).stale(108,1)
    cache=ImageCache(max_bytes=1024*1024)
    for index in range(50):
        image=QImage(256,256,QImage.Format_ARGB32);image.fill(index);cache[index]=image
        assert cache.bytes<=1024*1024
    assert len(cache)==4 and cache.get(0) is None and not cache.get(49).isNull()
    cache.clear();assert cache.bytes==0
    p=Page('CPU fixture');chart=ChartPanel(['Load','Temperature'],['#aaaaaa','#bbbbbb']);p.content.addWidget(chart)
    p.show();app.processEvents();chart.time_range.setCurrentIndex(2);chart.toggles[1].setChecked(False)
    p.close();p2=Page('CPU fixture');again=ChartPanel(['Load','Temperature'],['#aaaaaa','#bbbbbb']);p2.content.addWidget(again)
    p2.show();app.processEvents()
    assert again.time_range.currentData()==900 and not again.toggles[1].isChecked()
    again.set_scope('another GPU');assert again.time_range.currentData()==60 and again.toggles[1].isChecked()
    again.set_scope('');assert again.time_range.currentData()==900 and not again.toggles[1].isChecked()
    gpus=[dict(id='A',name='GPU',temp=30,usage=10),dict(id='B',name='GPU',temp=70,usage=90)]
    extrema=SessionExtrema();extrema.update(dict(gpus=gpus));settings.set('primary_gpu','B')
    selected=ordered(gpus);assert [g['id'] for g in selected]==['B','A'] and gpus[0]['id']=='A'
    assert extrema.update(dict(gpus=selected))['gpu_temp']==[70,70]
    settings.set('primary_gpu','missing');assert ordered(gpus)[0]['id']=='A'
    i18n.set_lang('en')
    report=engine.raw_run('system',dict(cpu=dict(usage=15),ram={},gpus=[]))
    english=report.localized()
    assert 'CPU load: 15.0%' in english and 'GPU load: not available' in english,english
    assert 'CPU-Auslastung' in report.localized('de')
    i18n.set_lang('de')
    # External journal content, including German text, must stay untouched.
    raw='2026-10-26 kernel: nicht verfügbar / Testgerät'
    with patch.object(engine.shutil,'which',return_value='/bin/journalctl'),patch.object(engine.subprocess,'run',return_value=type('Output',(),dict(returncode=0,stdout=raw,stderr=''))()):
        report=engine.raw_run('crashes',{})
        assert raw in report.localized('en') and 'current boot' in report.localized('en')
    product=dict(kind='cpu',vendor='Intel',model='Core i5-14600KF',exact=True)
    cache=product_images.ProductCache(Path(directory)/'images')
    from PySide6.QtCore import QBuffer,QByteArray,QIODevice
    image=QImage(120,80,QImage.Format_ARGB32);image.fill(0xffeeeeee)
    buffer=QBuffer();buffer.open(QIODevice.WriteOnly);image.save(buffer,'PNG');data=bytes(buffer.data())
    result=cache.save_manual(product,data)
    assert result['manual'] and cache.load(product)['sha256']==result['sha256']
    cache.discard(product);assert cache.load(product) is None
    xml='''<nvidia_smi_log><driver_version>600</driver_version><gpu id="0000:01:00.0"><uuid>GPU-A</uuid><product_name>GeForce RTX fixture</product_name><utilization><gpu_util>25 %</gpu_util></utilization><fb_memory_usage><used>100 MiB</used><total>8000 MiB</total></fb_memory_usage><temperature><gpu_temp>50 C</gpu_temp></temperature><gpu_power_readings><instant_power_draw>42 W</instant_power_draw></gpu_power_readings></gpu></nvidia_smi_log>'''
    with patch.object(sensors.shutil,'which',return_value='/bin/nvidia-smi'),patch.object(sensors,'_run',return_value=xml) as query:
        records=sensors._nvidia_gpus()
    assert len(query.call_args_list)==1 and records[0]['vram_used']==100*1048576 and records[0]['power']==42
    p2.close();page.close()
print('121 duplicate-label sensors, unknown transitions, stale recovery, cache budget, chart persistence, GPU isolation, DE/EN/raw output, local images and single NVIDIA query PASS')
