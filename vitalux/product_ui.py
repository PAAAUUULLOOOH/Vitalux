"""Theme-aware hardware headers with background image loading and offline reuse."""
from threading import Event
import time

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Qt, QRectF, QSize, QTimer
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QBoxLayout, QSizePolicy, QVBoxLayout, QGridLayout, QWidget

from .product_images import lookup_key, resolve
from . import settings
from .ui_locale import QLabel


class _Signals(QObject):
    done = Signal(str, object)
    preview = Signal(str, object)


class _ImageTask(QRunnable):
    def __init__(self, key, product, signals, cancelled):
        super().__init__()
        self.key, self.product, self.signals = key, dict(product), signals
        self.cancelled = cancelled

    def run(self):
        preview=[None]
        def show_preview(result):
            preview[0]=result
            if not self.cancelled.is_set():self.signals.preview.emit(self.key,result)
        try:
            result = resolve(self.product, cancelled=self.cancelled,
                             on_preview=show_preview)
        except Exception:
            # Image lookup is optional and must never disrupt monitoring.
            result = preview[0]
        if not self.cancelled.is_set():
            self.signals.done.emit(self.key, result)


class ImageLoader(QObject):
    loaded = Signal(str, object)

    def __init__(self, parent):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(2)
        self.signals = _Signals(self)
        self.signals.done.connect(self._ready)
        self.signals.preview.connect(self._preview)
        self.results = {}
        self.pending = set()
        self.failed_at = {}
        self.cancelled = Event()
        parent.aboutToQuit.connect(self.shutdown)

    def shutdown(self):
        self.cancelled.set()
        self.pool.clear()

    def request(self, product):
        if settings.get('component_images',True) is False:return
        key = lookup_key(product)
        if not key:
            return
        if key in self.failed_at and time.monotonic() - self.failed_at[key] >= 60:
            self.results.pop(key, None)
            self.failed_at.pop(key, None)
        if key in self.results:
            self.loaded.emit(key, self.results[key])
        elif key not in self.pending:
            self.pending.add(key)
            self.pool.start(_ImageTask(key, product, self.signals, self.cancelled))

    def _ready(self, key, result):
        self.pending.discard(key)
        self.results[key] = result
        if result is None:
            self.failed_at[key] = time.monotonic()
        else:self.failed_at.pop(key,None)
        self.loaded.emit(key, result)

    def _preview(self, key, result):
        self.results[key] = result
        self.failed_at.pop(key,None)
        self.loaded.emit(key, result)


def loader():
    app = QApplication.instance()
    if not hasattr(app, '_product_image_loader'):
        app._product_image_loader = ImageLoader(app)
    return app._product_image_loader


class ProductPicture(QWidget):
    def __init__(self):
        super().__init__()
        self.pixmap=QPixmap()
        self.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
        self.setMaximumHeight(190)

    def sizeHint(self):return QSize(250,170)

    def paintEvent(self,event):
        if self.pixmap.isNull():return
        painter=QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        area=self.rect().adjusted(2,2,-2,-2)
        size=self.pixmap.size().scaled(area.size(),Qt.KeepAspectRatio)
        target=QRectF(area.center().x()-size.width()/2,area.center().y()-size.height()/2,size.width(),size.height())
        painter.drawPixmap(target,self.pixmap,QRectF(self.pixmap.rect()))


class ProductHeader(QWidget):
    """A product photo at left, concise specs at right; no image means no gap."""
    def __init__(self,name,meta,kind):
        super().__init__()
        self.name,self.meta=name,meta
        self.product={};self.key='';self._requested=False;self._result=None
        self.retry=QTimer(self);self.retry.setSingleShot(True);self.retry.setInterval(65000)
        self.retry.timeout.connect(self._retry)
        self.picture=ProductPicture();self.picture.hide()
        self.details=QWidget()
        details=QVBoxLayout(self.details);details.setContentsMargins(0,0,0,0);details.setSpacing(5)
        details.addWidget(name);details.addWidget(meta)
        self.spec_host=QWidget();self.spec_grid=QGridLayout(self.spec_host)
        self.spec_grid.setContentsMargins(0,3,0,0);self.spec_grid.setHorizontalSpacing(16);self.spec_grid.setVerticalSpacing(3)
        self.spec_grid.setColumnStretch(1,1)
        details.addWidget(self.spec_host)
        self.spec_rows=[];self._spec_values=None
        self.row=QBoxLayout(QBoxLayout.LeftToRight,self);self.row.setContentsMargins(0,0,0,0)
        self.row.setSpacing(20);self.row.addWidget(self.picture,0,Qt.AlignVCenter)
        self.row.addWidget(self.details,1)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
        self._layout_image(False)
        loader().loaded.connect(self._ready)
        self.set_specs([])

    def set_specs(self,rows):
        self.meta.setVisible(bool(self.meta.text().strip()))
        rows=tuple((str(key),str(value)) for key,value in rows if value not in (None,'','–'))[:4]
        if rows==self._spec_values:return
        self._spec_values=rows
        while len(self.spec_rows)<len(rows):
            key,value=QLabel(),QLabel();key.setObjectName('muted');value.setObjectName('strong')
            value.setWordWrap(True)
            index=len(self.spec_rows);self.spec_grid.addWidget(key,index,0);self.spec_grid.addWidget(value,index,1)
            self.spec_rows.append((key,value))
        for index,(key,value) in enumerate(self.spec_rows):
            visible=index<len(rows);key.setVisible(visible);value.setVisible(visible)
            if visible:key.setText(rows[index][0]);value.setText(rows[index][1])
        self.spec_host.setVisible(bool(rows));self.updateGeometry()

    def set_product(self,product):
        product=dict(product or {});key=lookup_key(product)
        if key==self.key and self.product:return
        self.product,self.key,self._requested,self._result=product,key,False,None
        self.retry.stop()
        self.picture.pixmap=QPixmap();self.picture.hide();self.setMinimumHeight(0)
        self._layout_image(False)
        self.updateGeometry()
        if self.isVisible():self._request()

    def _request(self):
        if settings.get('component_images',True) is not False and self.key and not self._requested:
            self._requested=True;loader().request(self.product)

    def _retry(self):
        if self.isVisible():
            self._requested=False
            self._request()

    def showEvent(self,event):
        super().showEvent(event)
        if self.picture.pixmap.isNull():self._requested=False
        self._request()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if not self.picture.pixmap.isNull():
            self.picture.setFixedWidth(min(260,max(110,round(self.width()*.32))))

    def _ready(self,key,result):
        if key!=self.key:return
        self.picture.pixmap=QPixmap(result['path']) if result else QPixmap()
        self._result=result
        available=not self.picture.pixmap.isNull()
        self._layout_image(available)
        if available or settings.get('component_images',True) is False:self.retry.stop()
        elif self.key:self.retry.start()
        self.picture.update();self.updateGeometry()

    def _layout_image(self, available):
        available=available and settings.get('component_images',True) is not False
        self.picture.setVisible(available)
        self.row.setDirection(QBoxLayout.LeftToRight if available else QBoxLayout.TopToBottom)
        self.row.setSpacing(20 if available else 0)
        self.row.setAlignment(self.details, Qt.AlignVCenter if available else Qt.AlignTop)
        self.setMinimumHeight(170 if available else 0)
        self.picture.setFixedWidth(min(260,max(110,round(self.width()*.32))) if available else 0)
        self.details.setMinimumWidth(0)
        self.details.updateGeometry()
        self.updateGeometry()

    def sync_preference(self):
        enabled=settings.get('component_images',True) is not False
        if not enabled:self.retry.stop()
        self._layout_image(enabled and not self.picture.pixmap.isNull())
        if enabled and self.isVisible():
            self._requested=False
            self._request()

    def retranslate(self):
        for row in self.spec_rows:
            for label in row:label.retranslate()
        self.picture.update()
