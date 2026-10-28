"""Native-resolution appearance blends, with no live subtree repaint per frame."""
from PySide6.QtCore import QEasingCurve, QEvent, Signal, QVariantAnimation, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QWidget
from . import motion


class AppearanceTransition(QWidget):
    finished = Signal()

    def __init__(self, parent, before, after, *, slide=0):
        super().__init__(parent)
        self.setObjectName('appearanceTransition')
        self.before, self.after = before, after
        self._blend = QPixmap()
        self._layer = QPixmap()
        self.progress = 0.0
        self.slide=slide
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._framed = hasattr(parent, 'window_frame')
        self.setAttribute(Qt.WA_OpaquePaintEvent, not self._framed)
        self.setGeometry(parent.rect())
        parent.installEventFilter(self)
        self.animation = QVariantAnimation(self)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(motion.duration(300))
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.valueChanged.connect(self._frame)
        self.animation.finished.connect(self.finish)

    def start(self):
        if self.before is None:return
        self.show()
        self.raise_()
        self.animation.start()

    def _frame(self, value):
        self.progress = float(value)
        self.update()

    def finish(self):
        if self.before is None:return
        self.animation.stop()
        self.hide()
        self.before = self.after = None
        self._blend = QPixmap()
        self._layer = QPixmap()
        self.parentWidget().removeEventFilter(self)
        self.finished.emit()
        self.deleteLater()

    def eventFilter(self, obj, event):
        if obj is self.parentWidget() and event.type() in (QEvent.Resize, QEvent.Hide):
            self.finish()
        return False

    def paintEvent(self, event):
        if self.before is None:
            return
        if self._framed:
            # QWidget painting shares the live window's backing store. Adding
            # layers there adds the destination AGAIN and creates a bright flash.
            # Blend into a cleared, reusable native-resolution buffer instead.
            if self._blend.size() != self.before.size() or self._blend.devicePixelRatio() != self.before.devicePixelRatio():
                self._blend = QPixmap(self.before.size())
                self._blend.setDevicePixelRatio(self.before.devicePixelRatio())
                self._layer = QPixmap(self.before.size())
                self._layer.setDevicePixelRatio(self.before.devicePixelRatio())
            self._blend.fill(Qt.transparent)
            self._layer.fill(Qt.transparent)
            blend = QPainter(self._blend)
            blend.setOpacity(1. - self.progress)
            blend.drawPixmap(0, 0, self.before)
            # Apply source opacity with SourceOver on an EMPTY layer. Qt's
            # constant opacity on Plus interpolates the operation's destination
            # as well, making even a cleared one-buffer blend lose alpha.
            layer = QPainter(self._layer)
            layer.setOpacity(self.progress)
            if self.slide:layer.translate(round(self.slide * (1 - self.progress)), 0)
            layer.drawPixmap(0, 0, self.after)
            layer.end()
            blend.setOpacity(1.)
            blend.setCompositionMode(QPainter.CompositionMode_Plus)
            blend.drawPixmap(0, 0, self._layer)
            blend.end()
            painter = QPainter(self)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.drawPixmap(0, 0, self._blend)
        else:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self.before)
            painter.setOpacity(self.progress)
            if self.slide:painter.translate(round(self.slide * (1 - self.progress)), 0)
            painter.drawPixmap(0, 0, self.after)
        painter.end()
