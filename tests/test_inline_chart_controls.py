"""CPU/GPU use actual overview checks, wrapping and live design palettes."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt,QCoreApplication,QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QScrollArea
from vitalux import i18n,settings,theme
from vitalux.measurements import MeasurementHistory
from vitalux.pages import CpuPage,GpuCard
from vitalux.widgets import ChartSeriesCheckBox

app=QApplication.instance() or QApplication([])
cpu=dict(model='CPU',usage=25,temp=52,freq=2300,freq_max=4200,cores=8,threads=16,
         per_core=[25]*16,load=[.2,.3,.4])
power=dict(id='cpu',component='cpu',kind='powers',unit='W',name='CPU package',value=85,
           primary=True,domain='package-0',limits=[('PL1',125),('PL2',181)])
gpu_power=dict(power,id='gpu',component='gpu:A',value=150,limits=[('Leistungsgrenze',330)])
extra=dict(id='temperature',component='gpu:A',kind='temps',unit='°C',value=65,
           name='Additional device memory junction temperature sensor with a long descriptive name')
gpu=dict(id='A',name='GPU',usage=40,temp=60,power=150,power_limit=330,
         power_source_id='gpu',clock=2200,clock_mem=1200,fan_rpm=0,voltage=950,
         vram_used=2**30,vram_total=8*2**30,hardware=[gpu_power,extra])
sample=dict(cpu=cpu,gpus=[gpu],hardware=[power,gpu_power,extra])

with tempfile.TemporaryDirectory() as directory,patch.object(settings,'PATH',str(Path(directory)/'settings.json')):
    for language in ('de','en'):
        i18n.set_lang(language)
        for mode,_ in theme.CHOICES:
            theme.set_mode(mode);app.setStyleSheet(theme.stylesheet())
            for cls,scope in ((CpuPage,'cpu'),(GpuCard,'gpu:A')):
                area=QScrollArea();area.setWidgetResizable(True)
                area.measurement_history=MeasurementHistory()
                area.measurement_history.update(sample,1000)
                page=cls();area.setWidget(page)
                if cls is CpuPage:page.refresh(sample,{'cpu':[25]})
                else:page.refresh(gpu)
                chart=page.graph
                area.resize(950,1050);area.show();app.processEvents()
                assert chart.inline_selection and chart.selector.isHidden() and chart.legend.isHidden()
                assert set(chart.checks)==set(chart.available)
                assert all(isinstance(c,ChartSeriesCheckBox) and c.property('selectionControl') for c in chart.toggles)
                assert all(c.series_color==chart.color(key) for key,c in chart.checks.items())
                assert chart.selection_flow.itemAt(0).widget() is chart.time_range
                check=chart.checks['power']
                QTest.mouseClick(check,Qt.LeftButton);assert not chart.selected['power']
                check.setFocus();QTest.keyClick(check,Qt.Key_Space);assert chart.selected['power']
                QTest.keyClick(check,Qt.Key_Space);assert not chart.selected['power']
                original=check
                if cls is GpuCard:
                    missing=dict(sample,gpus=[dict(gpu,power=None,power_limit=None,hardware=[])],hardware=[])
                    area.measurement_history.update(missing,1001)
                    chart.sync(missing,scope)
                    assert check.isHidden() and not chart.selected['power']
                    area.measurement_history.update(sample,1002);chart.sync(sample,scope)
                    assert chart.checks['power'] is original and not check.isChecked()
                chart.select_all(True)
                assert {'%','°C','W','MHz'}<=set(chart.graph.units)
                for width in (550,950):
                    area.resize(width,1050);app.processEvents()
                    panel=chart.selection_controls
                    visible=[chart.selection_flow.itemAt(i).widget() for i in range(chart.selection_flow.count())
                             if not chart.selection_flow.itemAt(i).isEmpty()]
                    for item in visible:
                        rect=item.geometry()
                        assert rect.left()>=0 and rect.right()<panel.width(),(mode,cls.__name__,width,item,rect,panel.size())
                        assert rect.bottom()<panel.height(),(mode,cls.__name__,width,rect,panel.size())
                    assert not any(a.geometry().intersects(b.geometry()) for i,a in enumerate(visible) for b in visible[i+1:])
                    assert not chart.grab().isNull()
                chart.select_all(False);assert chart.graph.isHidden() and not check.isHidden()
                chart.select_all(True);assert not chart.graph.isHidden()
                area.close();area.deleteLater()
                QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
print('Overview-style CPU/GPU checkboxes, keyboard/mouse selection, all design palettes, DE/EN, wrapping and sensor recovery PASS')
