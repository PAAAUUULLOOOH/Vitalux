"""Native move/resize operations and a rounded, design-aware client window frame."""
from PySide6.QtCore import QObject, QEvent, QPoint, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen, QRegion
from PySide6.QtWidgets import (QAbstractButton, QApplication, QHBoxLayout, QLabel,
                              QMenu, QStatusBar, QWidget)
from . import APP_NAME, theme
from .i18n import tr

CORNER_RADIUS = 24


def outline(rect, radius=CORNER_RADIUS):
    path = QPainterPath()
    if radius:
        path.addRoundedRect(QRectF(rect).adjusted(1, 1, -1, -1), radius, radius)
    else:
        path.addRect(QRectF(rect))
    return path


class WindowButton(QAbstractButton):
    def __init__(self, action, frame):
        super().__init__(frame.titlebar)
        self.action, self.frame = action, frame
        self.setFixedSize(34, 28)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty('vitaluxCapabilityHints', True)
        self.clicked.connect({'minimize': frame.window.showMinimized,
                              'maximize': frame.toggle_maximized,
                              'close': frame.window.close}[action])
        self.retranslate()

    def retranslate(self):
        text = {'minimize': 'Fenster minimieren', 'close': 'Fenster schließen',
                'maximize': 'Fenster wiederherstellen' if self.frame.expanded else 'Fenster maximieren'}[self.action]
        self.setAccessibleName(tr(text))
        self.setToolTip(tr(text))
        self.update()

    def enterEvent(self, event):
        super().enterEvent(event); self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event); self.update()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.click(); event.accept()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.underMouse() or self.isDown() or self.hasFocus():
            color = QColor(theme.CRIT if self.action == 'close' else theme.accent())
            color.setAlpha(95 if self.isDown() else 44)
            painter.setPen(Qt.NoPen); painter.setBrush(color)
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 6, 6)
        painter.setPen(QPen(QColor(theme.TEXT), 1.35, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        x, y = self.width()/2, self.height()/2
        if self.action == 'minimize':
            painter.drawLine(QPoint(round(x-5), round(y+2)), QPoint(round(x+5), round(y+2)))
        elif self.action == 'close':
            painter.drawLine(QPoint(round(x-4), round(y-4)), QPoint(round(x+4), round(y+4)))
            painter.drawLine(QPoint(round(x+4), round(y-4)), QPoint(round(x-4), round(y+4)))
        elif self.frame.expanded:
            painter.drawRect(QRectF(x-2, y-5, 7, 7))
            painter.fillRect(QRectF(x-5, y-2, 7, 7), QColor(theme.BG))
            painter.drawRect(QRectF(x-5, y-2, 7, 7))
        else:
            painter.drawRect(QRectF(x-4, y-4, 8, 8))
        painter.end()


class TitleBar(QWidget):
    def __init__(self, frame):
        super().__init__(frame.window)
        self.frame = frame
        self._drag = None
        self.setObjectName('windowTitleBar')
        self.setFixedHeight(36)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda _: frame.show_menu(QCursor.pos()))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            handle = self.frame.window.windowHandle()
            moved = bool(handle and handle.startSystemMove())
            if not moved and not QApplication.platformName().startswith('wayland'):
                window = self.frame.window
                if self.frame.expanded:
                    self.frame.toggle_maximized()
                self._drag = event.globalPosition().toPoint() - window.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag is not None and event.buttons() & Qt.LeftButton:
            self.frame.window.move(event.globalPosition().toPoint() - self._drag)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag = None
            self.frame.toggle_maximized(); event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class ResizeHandle(QWidget):
    def __init__(self, frame, edges):
        super().__init__(frame.window)
        self.frame, self.edges = frame, edges
        self._drag = None
        horizontal = bool(edges & (Qt.LeftEdge | Qt.RightEdge))
        vertical = bool(edges & (Qt.TopEdge | Qt.BottomEdge))
        diagonal = (edges == (Qt.TopEdge | Qt.LeftEdge) or edges == (Qt.BottomEdge | Qt.RightEdge))
        self.setCursor(Qt.SizeFDiagCursor if horizontal and vertical and diagonal else
                       Qt.SizeBDiagCursor if horizontal and vertical else
                       Qt.SizeHorCursor if horizontal else Qt.SizeVerCursor)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:return super().mousePressEvent(event)
        window = self.frame.window
        handle = window.windowHandle()
        resized = bool(handle and handle.startSystemResize(self.edges))
        if not resized and not QApplication.platformName().startswith('wayland'):
            self._drag = (event.globalPosition().toPoint(), QRect(window.geometry()))
        event.accept()

    def mouseMoveEvent(self, event):
        if self._drag is None or not event.buttons() & Qt.LeftButton:return
        origin, original = self._drag
        delta = event.globalPosition().toPoint() - origin
        rect = QRect(original); window = self.frame.window
        if self.edges & Qt.LeftEdge:rect.setLeft(min(original.right()-window.minimumWidth()+1, original.left()+delta.x()))
        if self.edges & Qt.RightEdge:rect.setRight(max(original.left()+window.minimumWidth()-1, original.right()+delta.x()))
        if self.edges & Qt.TopEdge:rect.setTop(min(original.bottom()-window.minimumHeight()+1, original.top()+delta.y()))
        if self.edges & Qt.BottomEdge:rect.setBottom(max(original.top()+window.minimumHeight()-1, original.bottom()+delta.y()))
        window.setGeometry(rect)

    def mouseReleaseEvent(self, event):
        self._drag = None
        super().mouseReleaseEvent(event)


class ClientStatusBar(QStatusBar):
    """Keep status messages within the rounded client, including permanent notices."""
    def __init__(self, parent):
        self._notices = []
        self._queued = False
        super().__init__(parent)
        self.setSizeGripEnabled(False)
        self.messageChanged.connect(self._sync_visibility)
        self.hide()

    def _sync_visibility(self, *_):
        self._queued = False
        self.setVisible(bool(self.currentMessage()) or any(not item.isHidden() for item in self._notices))

    def addPermanentWidget(self, widget, stretch=0):
        self._notices.append(widget)
        widget.installEventFilter(self)
        super().addPermanentWidget(widget, stretch)
        self._sync_visibility()

    def eventFilter(self, obj, event):
        if obj in self._notices and event.type() in (QEvent.ShowToParent, QEvent.HideToParent) and not self._queued:
            self._queued = True
            QTimer.singleShot(0, self._sync_visibility)
        return super().eventFilter(obj, event)


class WindowFrame(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.scene = self.canvas = self.status = None
        self.titlebar = TitleBar(self)
        layout = QHBoxLayout(self.titlebar)
        layout.setContentsMargins(10, 6, 4, 2); layout.setSpacing(2)
        caption = QLabel(APP_NAME)
        caption.setAttribute(Qt.WA_TransparentForMouseEvents)
        caption.setObjectName('muted')
        layout.addWidget(caption); layout.addStretch()
        self.buttons = {action: WindowButton(action, self) for action in ('minimize', 'maximize', 'close')}
        for button in self.buttons.values():layout.addWidget(button)
        edges = (Qt.TopEdge, Qt.BottomEdge, Qt.LeftEdge, Qt.RightEdge,
                 Qt.TopEdge | Qt.LeftEdge, Qt.TopEdge | Qt.RightEdge,
                 Qt.BottomEdge | Qt.LeftEdge, Qt.BottomEdge | Qt.RightEdge)
        self.handles = [ResizeHandle(self, edge) for edge in edges]
        window.installEventFilter(self)

    @property
    def expanded(self):return self.window.isMaximized() or self.window.isFullScreen()

    def attach(self, scene, canvas):
        self.scene, self.canvas = scene, canvas
        scene.setProperty('vitaluxRoundedWindow', True)
        scene.setAttribute(Qt.WA_OpaquePaintEvent, False)
        canvas.insertWidget(0, self.titlebar)
        self.status = ClientStatusBar(scene); canvas.addWidget(self.status)
        self.refresh()

    def toggle_maximized(self):
        self.window.showNormal() if self.expanded else self.window.showMaximized()

    def show_menu(self, position):
        menu = QMenu(self.window)
        if self.expanded:menu.addAction(tr('Fenster wiederherstellen'), self.window.showNormal)
        menu.addAction(tr('Fenster minimieren'), self.window.showMinimized)
        if not self.expanded:menu.addAction(tr('Fenster maximieren'), self.window.showMaximized)
        menu.addSeparator(); menu.addAction(tr('Fenster schließen'), self.window.close)
        try:menu.exec(position)
        finally:menu.deleteLater()

    def eventFilter(self, obj, event):
        if obj is self.window and event.type() in (QEvent.Resize, QEvent.WindowStateChange, QEvent.Show, QEvent.DevicePixelRatioChange):
            self.refresh()
        return False

    def refresh(self):
        if self.scene is None:return
        radius = 0 if self.expanded else CORNER_RADIUS
        self.scene.setProperty('vitaluxWindowRadius', radius)
        margin = 0 if self.expanded else 10
        self.canvas.setContentsMargins(margin, 0, margin, margin)
        width, height = self.window.width(), self.window.height()
        t, c = 5, 12
        rectangles = (QRect(c, 0, width-2*c, t), QRect(c, height-t, width-2*c, t),
                      QRect(0, c, t, height-2*c), QRect(width-t, c, t, height-2*c),
                      QRect(0, 0, c, c), QRect(width-c, 0, c, c),
                      QRect(0, height-c, c, c), QRect(width-c, height-c, c, c))
        for handle, rect in zip(self.handles, rectangles):
            handle.setGeometry(rect); handle.setVisible(not self.expanded); handle.raise_()
        native = self.window.windowHandle()
        if native and QApplication.platformName() != 'offscreen':
            # Outset input shape preserves the antialiased painted boundary.
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.window.rect()).adjusted(-2,-2,2,2), radius, radius)
            native.setMask(QRegion(path.toFillPolygon().toPolygon()) if radius else QRegion())
        if hasattr(self.scene, '_schedule_upload'):self.scene._schedule_upload()
        self.scene.update()
        self.retranslate()

    def retranslate(self):
        for button in self.buttons.values():button.retranslate()
