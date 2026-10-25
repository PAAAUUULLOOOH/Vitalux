"""Asynchronous datasheets and a native, scrollable manufacturer-spec dialog."""
from threading import Event
import time
from PySide6.QtCore import QObject,QRunnable,QThreadPool,Signal,Qt,QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication,QDialog,QVBoxLayout,QHBoxLayout,QScrollArea,QWidget,QSizePolicy
from .ui_locale import QLabel,QPushButton
from . import product_specs,theme
from .i18n import tr

class _Signals(QObject):done=Signal(str,object)
class _Task(QRunnable):
    def __init__(self,product,signals,cancelled):
        super().__init__();self.product=dict(product);self.signals=signals;self.cancelled=cancelled
    def run(self):
        try:result=product_specs.resolve(self.product,cancelled=self.cancelled)
        except Exception:result=None
        if not self.cancelled.is_set():self.signals.done.emit(product_specs.product_key(self.product),result)

class SpecLoader(QObject):
    loaded=Signal(str,object)
    def __init__(self,app):
        super().__init__(app);self.pool=QThreadPool(self);self.pool.setMaxThreadCount(3)
        self.signals=_Signals(self);self.signals.done.connect(self._ready)
        self.results={};self.pending=set();self.failed_at={};self.cancelled=Event();app.aboutToQuit.connect(self.shutdown)
    def request(self,product):
        key=product_specs.product_key(product)
        if not key or product.get('kind') not in ('cpu','gpu','mainboard'):return
        if key in self.failed_at and time.monotonic()-self.failed_at[key]>=60:self.results.pop(key,None);self.failed_at.pop(key,None)
        if key in self.results:self.loaded.emit(key,self.results[key]);return
        if key in self.pending:return
        cached=product_specs.SpecCache().load(product)
        if cached:self._ready(key,cached);return
        import os
        if os.environ.get('VITALUX_SPEC_OFFLINE')=='1':self._ready(key,None);return
        self.pending.add(key);self.pool.start(_Task(product,self.signals,self.cancelled))
    def _ready(self,key,result):
        self.pending.discard(key);self.results[key]=result
        if result is None:self.failed_at[key]=time.monotonic()
        else:self.failed_at.pop(key,None)
        self.loaded.emit(key,result)
    def shutdown(self):self.cancelled.set();self.pool.clear()

def loader():
    app=QApplication.instance()
    if not hasattr(app,'_spec_loader'):app._spec_loader=SpecLoader(app)
    return app._spec_loader

KEYS={'video memory':'Videospeicher','memory size/bus':'Speichergröße / Busbreite','bus standard':'Schnittstelle','graphic engine':'Grafikchip','total cores':'Kerne','total threads':'Threads','# of cpu cores':'Kerne','# of threads':'Threads','max. boost clock':'Maximaler Boost-Takt','memory support':'Speicherunterstützung','cpu':'Prozessor','socket':'Sockel','chipset':'Chipsatz','form factor':'Formfaktor','memory type':'Speichertyp',
      'memory size':'Speichergröße','engine clock':'GPU-Takt','boost clock':'Boost-Takt','outputs':'Anschlüsse',
      'dimensions':'Abmessungen','cores':'Kerne','threads':'Threads','cache':'Cache','tdp':'TDP',
      'memory':'Speicher','graphics memory':'Videospeicher','gpu':'GPU','power consumption':'Leistungsaufnahme'}
def caption(key):return tr(KEYS.get(key.strip().casefold(),key))

def brief(data,local,kind=''):
    if not data:return list(local)
    import re
    patterns={
        'gpu':(r'video.?memory|memory.?size|memory.?type|graphics.?memory',r'engine.?clock|boost|core.?clock',r'^outputs?$|^interface$|bus.standard',r'^gpu$|graphic.engine'),
        'cpu':(r'total.cores|#.of.cpu.cores|^cores$',r'total.threads|#.of.threads|^threads$',r'max.*(?:boost|turbo)|boost.clock',r'socket|package'),
        'mainboard':(r'chipset',r'^cpu$|socket',r'^memory$|memory.support',r'form.factor',r'^lan$|^storage$')
    }.get(kind,(r'socket|chipset|memory|clock|boost|core|thread|output|interface',))
    preferred=[]
    for section in data.get('sections',[]):
        for key,value in section['rows']:
            if len(value)>180:continue
            rank=next((index for index,pattern in enumerate(patterns) if re.search(pattern,key,re.I)),None)
            if rank is not None:preferred.append((rank,caption(key),value))
    preferred.sort(key=lambda row:row[0])
    seen=set();result=[]
    for key,value in [(key,value) for _,key,value in preferred]+list(local):
        if key.casefold() in seen:continue
        seen.add(key.casefold());result.append((key,value))
        if len(result)==4:break
    return result

class SpecificationDialog(QDialog):
    def __init__(self,header):
        super().__init__(header.window());self.header=header;self.key=header.key;self.local_specs=list(header._local_specs)
        self.setWindowTitle(tr('Alle Spezifikationen'));self.setObjectName('specificationDialog')
        self.setStyleSheet(f'QDialog#specificationDialog {{ background:{theme.BG}; color:{theme.TEXT}; }}')
        self.resize(760,650);self.setMinimumSize(400,320)
        layout=QVBoxLayout(self);layout.setContentsMargins(24,20,24,20);layout.setSpacing(14)
        title=QLabel(header.name.text());title.setObjectName('bigName');title.setWordWrap(True);title.setAlignment(Qt.AlignCenter);layout.addWidget(title)
        self.status=QLabel();self.status.setObjectName('muted');self.status.setWordWrap(True);self.status.setAlignment(Qt.AlignCenter);layout.addWidget(self.status)
        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);layout.addWidget(self.scroll,1)
        actions=QHBoxLayout();self.source_button=QPushButton('Herstellerseite öffnen');self.source_button.clicked.connect(self.open_source)
        actions.addWidget(self.source_button);actions.addStretch();close=QPushButton('Schließen');close.clicked.connect(self.accept);actions.addWidget(close);layout.addLayout(actions)
        loader().loaded.connect(self._ready);self.finished.connect(lambda *_:self._disconnect())
        self.populate(header._manufacturer_specs)
    def _disconnect(self):
        try:loader().loaded.disconnect(self._ready)
        except (RuntimeError,TypeError):pass
    def _ready(self,key,result):
        if key==self.key:self.populate(result)
    def open_source(self):
        if self.source:QDesktopServices.openUrl(QUrl(self.source))
    def populate(self,data):
        self.source=data.get('source','') if data else ''
        self.source_button.setVisible(bool(self.source))
        host=QWidget();body=QVBoxLayout(host);body.setContentsMargins(8,8,8,8);body.setSpacing(14)
        groups=[]
        if self.local_specs:groups.append(dict(title='Erkannte Systemdaten',rows=self.local_specs))
        if data:groups+=data['sections']
        for group in groups:
            heading=QLabel(tr(group['title']));heading.setObjectName('strong');heading.setWordWrap(True);body.addWidget(heading)
            for key,value in group['rows']:
                name=QLabel(caption(key));name.setObjectName('muted');name.setWordWrap(True);body.addWidget(name)
                text=QLabel(str(value));text.setTextFormat(Qt.PlainText);text.setWordWrap(True);text.setTextInteractionFlags(Qt.TextSelectableByMouse)
                text.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred);text.setMinimumWidth(0);body.addWidget(text)
        body.addStretch(1)
        old=self.scroll.takeWidget()
        if old:old.deleteLater()
        self.scroll.setWidget(host)
        if data:
            from datetime import datetime
            stamp=datetime.fromtimestamp(data['checked_at']).strftime('%d.%m.%Y')
            self.status.setText(tr('Herstellerangaben · Originalsprache · Stand: {date}').format(date=stamp))
        elif self.key in loader().pending:self.status.setText(tr('Herstellerspezifikationen werden geladen …'))
        else:self.status.setText(tr('Herstellerangaben derzeit nicht verfügbar. Erkannte Systemdaten werden angezeigt.'))
