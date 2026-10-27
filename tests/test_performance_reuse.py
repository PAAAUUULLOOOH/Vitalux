"""Caches retain visuals/data freshness and temporary Qt menus are released."""
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ['VITALUX_SPEC_OFFLINE']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QSize, QTimer, Qt
from PySide6.QtGui import QColor, QFontMetrics, QImage, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMenu
from vitalux import settings, theme
from vitalux.charts import ChartPanel, HistoryGraph
from vitalux.hardware_sensors import HardwareMonitor
from vitalux.overview_text import ElidedLabel
from vitalux.pages import OverviewPage
from vitalux.product_ui import ProductHeader
from vitalux.quick_scene import WallpaperProvider
from vitalux.widgets import KeyValue

app=QApplication([])
with tempfile.TemporaryDirectory() as directory,patch.object(settings,'PATH',directory+'/settings.json'):
    settings.set_many(dict(theme='glass',motion='off',component_images=False))
    theme.set_mode('glass');app.setStyleSheet(theme.stylesheet())
    caption=ElidedLabel('A long component identity '*5);caption.resize(180,25);caption.show();app.processEvents()
    with patch('vitalux.overview_text.QFontMetrics',wraps=QFontMetrics) as metrics:
        for _ in range(100):caption.set_caption(caption.original_text)
        assert metrics.call_count==0,'Unchanged captions still recompute font metrics'
        caption.resize(250,25);app.processEvents();assert metrics.call_count>0
    assert caption.property('vitaluxFullNameHint') and caption.toolTip()==caption.original_text
    caption.close()
    fixture=Path(__file__).with_name('test_component_charts.py')
    scope={'__file__':str(fixture)};text=fixture.read_text()
    exec(compile(text[:text.index('with tempfile.TemporaryDirectory()')],str(fixture),'exec'),scope)
    logo=QPixmap(96,96);logo.fill(Qt.transparent)
    page=OverviewPage(dict(name='Linux',version='1'),logo)
    history={key:[12.,20.] for key in ('cpu','gpu','ram','net_down','net_up')}
    page.refresh(scope['sample'],history)
    with patch.object(page.design_metrics['cpu'],'set',wraps=page.design_metrics['cpu'].set) as hidden:
        page.refresh(scope['sample'],history);assert hidden.call_count==0
        theme.set_mode('quantum_core');page.refresh_design();assert hidden.call_count==1
    with patch.object(page.g_cpu,'set',wraps=page.g_cpu.set) as hidden:
        page.refresh(scope['sample'],history);assert hidden.call_count==0
        theme.set_mode('glass');page.refresh_design();assert hidden.call_count==1
        assert page.g_cpu.box.gauge._render_value==scope['sample']['cpu']['usage']
    registry=page.charts();assert registry is page.charts() and len(registry)==2
    extra=ChartPanel(['CPU'],[theme.accent()]);extra.setParent(page);page.register_charts(extra)
    assert len(page.charts())==3
    key=KeyValue('Example');header=ProductHeader(QLabel('GPU'),QLabel('Vendor'),'gpu');header.key='test'
    for owner,method in ((key,lambda:key._show_details(None)),(header,lambda:header._context_menu(QPoint())),
                         (page,page._show_hidden_tiles)):
        for _ in range(25):
            QTimer.singleShot(0,lambda:[menu.close() for menu in app.topLevelWidgets() if isinstance(menu,QMenu)])
            method();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
        assert not owner.findChildren(QMenu),'Temporary context menus survived closing'
    for widget in (key,header,page):widget.close();widget.deleteLater()
    graph=HistoryGraph(maxlen=900);graph.resize(700,260);graph.show()
    graph.set_series([([None if i%71==0 else i%100 for i in range(900)],'#4f8cff')])
    app.processEvents();graph.grab();paths=graph._curve_data
    graph._pointer=250.;graph.grab();assert graph._curve_data is paths
    graph.resize(800,260);graph.grab();assert graph._curve_data is not paths
    graph.close()
    # Cached topology must never cache values or miss new/removed channels.
    root=Path(directory)/'sys';hw=root/'class/hwmon/hwmon0';hw.mkdir(parents=True)
    (hw/'name').write_text('coretemp');(hw/'temp1_input').write_text('42000')
    monitor=HardwareMonitor(root)
    assert monitor.sample([],now=1)[0]['value']==42
    entries=monitor.topology.entries
    (hw/'temp1_input').write_text('53000')
    assert monitor.sample([],now=2)[0]['value']==53 and monitor.topology.entries is entries
    (hw/'temp2_input').write_text('61000')
    assert sorted(row['value'] for row in monitor.sample([],now=3))==[53,61]
    (hw/'temp1_input').unlink()
    assert [row['value'] for row in monitor.sample([],now=4)]==[61]
    # Both producer and consumer may mutate their own QImage value copies.
    provider=WallpaperProvider();image=QImage(20,15,QImage.Format_ARGB32);image.fill(QColor('red'))
    provider.replace(image);image.fill(QColor('blue'))
    size=QSize();first=provider.requestImage('',size,QSize())
    assert size==QSize(20,15) and first.pixelColor(0,0)==QColor('red')
    first.fill(QColor('green'))
    assert provider.requestImage('',QSize(),QSize()).pixelColor(0,0)==QColor('red')
print('Freed menus, active overview, caption/vector caches, dynamic chart registry, hotplug/live sensors and image value ownership PASS')
