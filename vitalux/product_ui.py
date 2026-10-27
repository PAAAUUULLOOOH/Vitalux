"""Theme-aware hardware headers with background image loading and offline reuse."""
from threading import Event
import time

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Qt, QRectF, QSize, QTimer
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QBoxLayout, QSizePolicy, QVBoxLayout, QGridLayout, QWidget

from .product_images import lookup_key, resolve, ProductCache
from .work_result import WorkResult
from . import settings
from .ui_locale import QLabel, QPushButton


class _Signals(QObject):
    done = Signal(str, int, object)
    preview = Signal(str, int, object)


class _ImageTask(QRunnable):
    def __init__(self, key, product, signals, cancelled, generation=0):
        super().__init__()
        self.key, self.product, self.signals = key, dict(product), signals
        self.cancelled = cancelled
        self.generation = generation

    def run(self):
        preview=[None]
        def show_preview(result):
            preview[0]=result
            if not self.cancelled.is_set():self.signals.preview.emit(self.key,self.generation,result)
        outcome = WorkResult.perform('product_image', lambda: resolve(
            self.product, cache=ProductCache(include_image=True), cancelled=self.cancelled,
            on_preview=show_preview))
        result = outcome.value or preview[0]
        if not self.cancelled.is_set():
            self.signals.done.emit(self.key, self.generation, WorkResult(result, outcome.error, outcome.stage))



class ImageLoader(QObject):
    loaded = Signal(str, object)

    def __init__(self, parent):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(2)
        self.signals = _Signals(self)
        self.signals.done.connect(lambda key, generation, result: self._ready(key, result, generation))
        self.signals.preview.connect(lambda key, generation, result: self._preview(key, result, generation))
        self.results = {}
        self.generations = {}
        self.errors = {}
        self.pending = set()
        self.failed_at = {}
        self.cancelled = Event()
        parent.aboutToQuit.connect(self.shutdown)

    def shutdown(self):
        self.cancelled.set()
        self.pool.clear()
        return self.pool.activeThreadCount()==0

    def resume(self):
        if not self.cancelled.is_set():return
        self.cancelled=Event();self.pending.clear()

    def request(self, product):
        if self.cancelled.is_set() or settings.get('component_images',True) is False:return
        key = lookup_key(product)
        if not key:
            return
        if key in self.failed_at and time.monotonic() - self.failed_at[key] >= 60:
            self.results.pop(key, None)
            self.failed_at.pop(key, None)
        if key in self.results:
            result=self.results[key]
            self.loaded.emit(key,result)
            if result:result.pop('_image',None)
        elif key not in self.pending:
            self.pending.add(key)
            self.pool.start(_ImageTask(key, product, self.signals, self.cancelled, self.generations.get(key, 0)))

    def invalidate(self, product):
        key = lookup_key(product)
        self.generations[key] = self.generations.get(key, 0) + 1
        self.pending.discard(key)
        self.results.pop(key, None)
        self.failed_at.pop(key, None)
        self.errors.pop(key, None)

    def _ready(self, key, result, generation=None):
        if generation is not None and generation != self.generations.get(key, 0):return
        if isinstance(result, WorkResult):
            if result.error:self.errors[key] = result.error
            elif result.value:self.errors.pop(key, None)
            result = result.value
        self.pending.discard(key)
        self.results[key] = result
        if result is None:
            self.failed_at[key] = time.monotonic()
        else:self.failed_at.pop(key,None)
        self.loaded.emit(key, result)
        if result:result.pop('_image',None)

    def _preview(self, key, result, generation=None):
        if generation is not None and generation != self.generations.get(key, 0):return
        self.results[key] = result
        self.failed_at.pop(key,None)
        self.loaded.emit(key, result)
        if result:result.pop('_image',None)


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
    """Centered product identity and specifications, with an optional image above."""
    def __init__(self,name,meta,kind):
        super().__init__()
        self.name,self.meta=name,meta
        self.kind=kind;self._local_specs=[];self._manufacturer_specs=None;self._spec_requested=False
        for text in (name,meta):text.setAlignment(Qt.AlignCenter);text.setTextFormat(Qt.PlainText)
        self.product={};self.key='';self._requested=False;self._result=None
        self.retry=QTimer(self);self.retry.setSingleShot(True);self.retry.setInterval(65000)
        self.retry.timeout.connect(self._retry)
        self.picture=ProductPicture();self.picture.hide()
        self.details=QWidget()
        details=QVBoxLayout(self.details);details.setContentsMargins(0,0,0,0);details.setSpacing(5)
        details.addWidget(name);details.addWidget(meta)
        self.spec_host=QWidget();self.spec_grid=QGridLayout(self.spec_host)
        self.spec_grid.setContentsMargins(0,3,0,0);self.spec_grid.setHorizontalSpacing(16);self.spec_grid.setVerticalSpacing(3)
        self.spec_grid.setColumnStretch(0,1)
        details.addWidget(self.spec_host)
        self.spec_rows=[];self._spec_values=None
        self.spec_button=QPushButton('Alle Spezifikationen',self.details)
        self.spec_button.setObjectName('ghostBtn');self.spec_button.clicked.connect(self.show_specifications)
        self.spec_button.setVisible(kind in ('cpu','gpu','mainboard'))
        details.addWidget(self.spec_button,0,Qt.AlignHCenter)
        self.row=QBoxLayout(QBoxLayout.TopToBottom,self);self.row.setContentsMargins(0,0,0,0)
        self.row.setSpacing(20);self.row.addWidget(self.picture,0,Qt.AlignHCenter)
        self.row.addWidget(self.details,1)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
        self._layout_image(False)
        loader().loaded.connect(self._ready)
        from .spec_ui import loader as spec_loader
        spec_loader().loaded.connect(self._spec_ready)
        self.set_specs([])
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

    def _context_menu(self, position):
        if not self.key:return
        from PySide6.QtWidgets import QMenu
        from .i18n import tr
        menu = QMenu(self)
        menu.addAction(tr('Komponentendaten neu laden'), self.refresh_component)
        menu.addAction(tr('Falsches Bild verwerfen'), self.discard_image)
        menu.addAction(tr('Eigenes Komponentenbild auswählen …'), self.choose_image)
        menu.addAction(tr('Details anzeigen'), self.lookup_details)
        try:menu.exec(self.mapToGlobal(position))
        finally:menu.deleteLater()

    def refresh_component(self):
        from . import product_specs
        from .spec_ui import loader as specs
        loader().invalidate(self.product)
        ProductCache().discard(self.product)
        specs().invalidate(self.product)
        product_specs.SpecCache().path(self.product).unlink(missing_ok=True)
        self._requested = self._spec_requested = False
        self._manufacturer_specs = None
        self._ready(self.key, None)
        self._request();self.request_specs()

    def discard_image(self):
        ProductCache().discard(self.product, reject=True)
        settings.set('component_picture_customized', True)
        loader().invalidate(self.product)
        loader()._ready(self.key, None)
        self.retry.stop()

    def choose_image(self):
        from pathlib import Path
        from .ui_locale import QFileDialog, QMessageBox
        from .i18n import tr
        path, _ = QFileDialog.getOpenFileName(self, tr('Komponentenbild auswählen'), '', 'Images (*.png *.jpg *.jpeg *.webp)')
        if not path:return
        try:
            from .product_images import MAX_IMAGE
            if Path(path).stat().st_size > MAX_IMAGE:raise ValueError(tr('Das Bild ist zu groß.'))
            result = ProductCache(include_image=True).save_manual(self.product, Path(path).read_bytes())
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, 'Vitalux', str(error));return
        loader().invalidate(self.product)
        loader()._ready(self.key, result)
        settings.set('component_picture_customized', True)

    def lookup_details(self):
        from pathlib import Path
        from .detail_dialog import show_details
        from .product_images import product_key
        from .spec_ui import loader as specs
        from .i18n import tr
        messages = [loader().errors.get(self.key, ''), specs().errors.get(self.key, '')]
        path = ProductCache().root / (product_key(self.product) + '.lookup.json')
        from .product_specs import SpecCache
        for report_path in (path, SpecCache().path(self.product).with_suffix('.lookup.json')):
            try:messages.append(report_path.read_text())
            except OSError:pass
        self._lookup_dialog = show_details(self, 'Komponentendaten', '\n\n'.join(filter(None, messages)) or tr('Keine weiteren Details verfügbar.'))

    def set_specs(self,rows):
        from .spec_ui import brief
        self._local_specs=[(str(key),str(value)) for key,value in rows if value not in (None,'','–')]
        self._display_specs(brief(self._manufacturer_specs,self._local_specs,self.kind))

    def _display_specs(self,rows):
        from .i18n import tr
        self.meta.setVisible(bool(self.meta.text().strip()))
        rows=tuple(rows[:4])
        if rows==self._spec_values:return
        self._spec_values=rows
        while len(self.spec_rows)<len(rows):
            text=QLabel();text.setObjectName('muted');text.setAlignment(Qt.AlignCenter);text.setWordWrap(True)
            index=len(self.spec_rows);self.spec_grid.addWidget(text,index,0)
            self.spec_rows.append(text)
        for index,text in enumerate(self.spec_rows):
            text.setVisible(index<len(rows))
            if index<len(rows):text.setText(f'{tr(rows[index][0])}: {rows[index][1]}')
        self.spec_host.setVisible(bool(rows));self.updateGeometry()

    def request_specs(self):
        if self.kind in ('cpu','gpu','mainboard') and self.key and not self._spec_requested:
            self._spec_requested=True
            from .spec_ui import loader as spec_loader
            spec_loader().request(self.product)

    def _spec_ready(self,key,result):
        if key!=self.key:return
        self._manufacturer_specs=result
        from .spec_ui import brief
        self._display_specs(brief(result,self._local_specs,self.kind))

    def show_specifications(self):
        if self._manufacturer_specs is None:self._spec_requested=False
        self.request_specs()
        from .spec_ui import SpecificationDialog
        self._spec_dialog=SpecificationDialog(self);self._spec_dialog.setAttribute(Qt.WA_DeleteOnClose,True)
        self._spec_dialog.open()

    def set_product(self,product):
        product=dict(product or {});key=lookup_key(product)
        if key==self.key and self.product:return
        self.product,self.key,self._requested,self._result=product,key,False,None
        self._manufacturer_specs=None;self._spec_requested=False
        self.retry.stop()
        self.picture.pixmap=QPixmap();self._image_identity=None;self.picture.hide();self.setMinimumHeight(0)
        self._layout_image(False)
        self.updateGeometry()
        if self.isVisible():self._request();self.request_specs()

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
        self._request();self.request_specs()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if not self.picture.pixmap.isNull():
            self.picture.setFixedWidth(min(280,max(110,round(self.width()*.42))))

    def _ready(self,key,result):
        if key!=self.key:return
        identity=(result.get('path'),result.get('sha256')) if result else None
        if identity!=getattr(self,'_image_identity',None):
            image=result.get('_image') if result else None
            self.picture.pixmap=QPixmap.fromImage(image) if image is not None else QPixmap(result['path']) if result else QPixmap()
            self._image_identity=identity
        self._result=result
        available=not self.picture.pixmap.isNull()
        self._layout_image(available)
        if available or settings.get('component_images',True) is False:self.retry.stop()
        elif self.key:self.retry.start()
        self.picture.update();self.updateGeometry()

    def _layout_image(self, available):
        available=available and settings.get('component_images',True) is not False
        self.picture.setVisible(available)
        self.row.setDirection(QBoxLayout.TopToBottom)
        self.row.setSpacing(20 if available else 0)
        self.row.setAlignment(self.details, Qt.AlignTop)
        self.setMinimumHeight(0)
        self.picture.setFixedWidth(min(280,max(110,round(self.width()*.42))) if available else 0)
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
        from .spec_ui import brief
        self._spec_requested=False;self._manufacturer_specs=None
        self._spec_values=None
        self._display_specs(brief(self._manufacturer_specs,self._local_specs,self.kind))
        self.request_specs()
        self.picture.update()
