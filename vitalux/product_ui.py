"""Theme-aware hardware headers with background image loading and offline reuse."""
from html import escape
from threading import Event
import time

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Qt, QRectF, QEvent
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from . import theme
from .i18n import tr
from .nav_icons import paint_icon
from .product_images import product_key, resolve
from .ui_locale import QLabel


class _Signals(QObject):
    done = Signal(str, object)


class _ImageTask(QRunnable):
    def __init__(self, key, product, signals, cancelled):
        super().__init__()
        self.key, self.product, self.signals = key, dict(product), signals
        self.cancelled = cancelled

    def run(self):
        try:
            result = resolve(self.product, cancelled=self.cancelled)
        except Exception:
            # Image lookup is optional and must never disrupt monitoring.
            result = None
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
        self.results = {}
        self.pending = set()
        self.failed_at = {}
        self.cancelled = Event()
        parent.aboutToQuit.connect(self.shutdown)

    def shutdown(self):
        self.cancelled.set()
        self.pool.clear()

    def request(self, product):
        key = product_key(product)
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
        self.loaded.emit(key, result)


def loader():
    app = QApplication.instance()
    if not hasattr(app, '_product_image_loader'):
        app._product_image_loader = ImageLoader(app)
    return app._product_image_loader


class ProductPicture(QWidget):
    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self.pixmap = QPixmap()
        self.setMinimumSize(190, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        area = self.rect().adjusted(10, 10, -10, -10)
        if not self.pixmap.isNull():
            size = self.pixmap.size().scaled(area.size(), Qt.KeepAspectRatio)
            target = QRectF(area.center().x() - size.width()/2,
                            area.center().y() - size.height()/2, size.width(), size.height())
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(target, self.pixmap, QRectF(self.pixmap.rect()))
        else:
            icon = QRectF(area.center().x()-36, area.center().y()-36, 72, 72)
            paint_icon(painter, 'gpu' if self.kind == 'gpu' else 'system', icon, QColor(theme.MUTED))


class ProductHeader(QWidget):
    """Names stay useful even when the exact retail identity or image is absent."""
    def __init__(self, name, meta, kind):
        super().__init__()
        self.product = {}
        self.key = ''
        self._requested = False
        self._result = None
        self.picture = ProductPicture(kind)
        self.caption = QLabel('Produktbild nicht verfügbar')
        self.caption.setObjectName('muted')
        self.caption.setAlignment(Qt.AlignCenter)
        self.caption.setWordWrap(True)
        self.caption.setOpenExternalLinks(True)
        image = QWidget()
        image.setMaximumWidth(420)
        image_layout = QVBoxLayout(image)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.addWidget(self.picture, 1)
        image_layout.addWidget(self.caption)
        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.addStretch()
        details_layout.addWidget(name)
        details_layout.addWidget(meta)
        details_layout.addStretch()
        self.row = QBoxLayout(QBoxLayout.LeftToRight, self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(22)
        self.row.addWidget(image, 1)
        self.row.addWidget(details, 1)
        self.setMinimumHeight(210)
        loader().loaded.connect(self._ready)

    def set_product(self, product):
        product = dict(product or {})
        key = product_key(product)
        if key == self.key and self.product:
            return
        self.product, self.key, self._requested, self._result = product, key, False, None
        self.picture.pixmap = QPixmap()
        self.caption.setText(tr('Produktbild wird gesucht …') if key else tr('Produktbild nicht verfügbar'))
        self.picture.update()
        if self.isVisible():
            self._request()

    def _request(self):
        if self.key and not self._requested:
            self._requested = True
            loader().request(self.product)

    def showEvent(self, event):
        super().showEvent(event)
        if self.picture.pixmap.isNull():
            self._requested = False
        self._request()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.row.setDirection(QBoxLayout.TopToBottom if self.width() < 620 else QBoxLayout.LeftToRight)

    def _ready(self, key, result):
        if key != self.key:
            return
        self.picture.pixmap = QPixmap(result['path']) if result else QPixmap()
        self._result = result
        self.retranslate()
        self.picture.update()

    def retranslate(self):
        result = self._result
        if result and not self.picture.pixmap.isNull():
            vendor, source = escape(result['vendor']), escape(result['source'], quote=True)
            self.caption.setText(f'<a href="{source}" style="color:{theme.MUTED}">{vendor}</a>'
                                 f' · {tr("Offline verfügbar")}')
        else:
            pending = self.key and self.key in loader().pending
            self.caption.setText('Produktbild wird gesucht …' if pending else 'Produktbild nicht verfügbar')

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.StyleChange and hasattr(self, '_result') and hasattr(self, 'caption'):
            self.retranslate()
            self.picture.update()
