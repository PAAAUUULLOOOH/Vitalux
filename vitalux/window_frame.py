"""Native move/resize operations and a rounded, design-aware client window frame."""
from PySide6.QtCore import QObject, QEvent, QPoint, QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen, QRegion, QWheelEvent
from PySide6.QtWidgets import (QAbstractButton, QApplication, QHBoxLayout,
                              QMenu, QStatusBar, QWidget)
from . import theme
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
        handler = {'minimize': frame.window.showMinimized,
                              'maximize': frame.toggle_maximized,
                              'close': frame.window.close}.get(action)
        if handler:self.clicked.connect(handler)
        self.retranslate()

    def retranslate(self):
        text = {'layout': 'Dashboard-Layout', 'minimize': 'Fenster minimieren', 'close': 'Fenster schließen',
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
        if self.underMouse() or self.isDown() or self.hasFocus() or self.isChecked():
            color = QColor(theme.CRIT if self.action == 'close' else theme.accent())
            color.setAlpha(95 if self.isDown() else 44)
            painter.setPen(Qt.NoPen); painter.setBrush(color)
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 6, 6)
        painter.setPen(QPen(QColor(theme.TEXT), 1.35, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        x, y = self.width()/2, self.height()/2
        if self.action == 'layout':
            for dx,dy in ((-5,-5),(1,-5),(-5,1),(1,1)):
                painter.drawRoundedRect(QRectF(x+dx,y+dy,4,4),.6,.6)
        elif self.action == 'minimize':
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


class LayoutButton(WindowButton):
    def __init__(self, frame, overview):
        super().__init__('layout', frame)
        self.setCheckable(True)
        self.clicked.connect(overview.toggle_editor)

    def set_collapsed(self, value):self.setChecked(bool(value))

    def reset_highlight(self):self.clearFocus();self.update()


class TitleBar(QWidget):
    def __init__(self, frame):
        super().__init__(frame.window)
        self.frame = frame
        self._drag = None
        self.setObjectName('windowTitleBar')
        self.setFixedHeight(32)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda _: frame.show_menu(QCursor.pos()))

    def wheelEvent(self, event):
        viewport=self.frame.window.stack.currentWidget().viewport()
        forwarded=QWheelEvent(QPointF(viewport.mapFromGlobal(event.globalPosition().toPoint())),
            event.globalPosition(),event.pixelDelta(),event.angleDelta(),event.buttons(),
            event.modifiers(),event.phase(),event.inverted(),event.source(),event.pointingDevice())
        QApplication.sendEvent(viewport,forwarded)
        event.setAccepted(forwarded.isAccepted())

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
        shown=bool(self.currentMessage()) or any(not item.isHidden() for item in self._notices)
        self.setVisible(shown)
        if self.parentWidget().objectName()=='clientStatusHost':self.parentWidget().setVisible(shown)

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
        self.title_layout = layout
        layout.setContentsMargins(0, 2, 8, 2); layout.setSpacing(2)
        layout.addStretch()
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
        scene.installEventFilter(self)
        from .edge_material import EdgeMaterials
        self.materials=EdgeMaterials(self)
        self.window.sidebar.setProperty('vitaluxEdgeJoined',True)
        self.window.design_shell.bar._window_frame=self
        self.titlebar.setParent(scene)
        self.titlebar.show()
        self.layout_button = LayoutButton(self, self.window.pages[0][1])
        self.title_layout.insertWidget(self.title_layout.indexOf(self.buttons['minimize']), self.layout_button)
        self.window.pages[0][1].set_window_layout_toggle(self.layout_button)
        self.title_layout.insertWidget(self.title_layout.indexOf(self.layout_button), self.window.pages[0][1].layout_actions)
        self.window.stack.currentChanged.connect(self._sync_page)
        self._sync_page()
        status_host=QWidget(scene);status_host.setObjectName('clientStatusHost')
        status_layout=QHBoxLayout(status_host);status_layout.setContentsMargins(24,0,24,2)
        self.status = ClientStatusBar(status_host);status_layout.addWidget(self.status)
        canvas.addWidget(status_host);status_host.hide()
        for widget in (self.window.design_shell.header,self.window.design_shell.footer,self.window.content_host):widget.installEventFilter(self)
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
        if obj in (self.window,self.scene) and event.type() in (QEvent.Resize, QEvent.WindowStateChange, QEvent.Show, QEvent.DevicePixelRatioChange):
            self.refresh()
        elif self.scene is not None and event.type() in (QEvent.Resize,QEvent.Move):
            self._clip_content()
        return False

    def refresh(self):
        if self.scene is None:return
        radius = 0 if self.expanded else CORNER_RADIUS
        self.scene.setProperty('vitaluxWindowRadius', radius)
        self.canvas.setContentsMargins(0,0,0,0)
        width, height = self.window.width(), self.window.height()
        self.sync_controls()
        self.window.design_shell.sync_window_geometry()
        t, c = 5, 12
        rectangles = (QRect(c, 0, width-2*c, 2), QRect(c, height-t, width-2*c, t),
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
            key=(width,height,radius,self.window.devicePixelRatioF())
            if key!=getattr(self,'_native_mask_key',None):
                native.setMask(QRegion(path.toFillPolygon().toPolygon()) if radius else QRegion())
                self._native_mask_key=key
        if hasattr(self.scene, '_schedule_upload'):self.scene._schedule_upload()
        self.scene.update()
        self.retranslate()

    def retranslate(self):
        for button in self.buttons.values():button.retranslate()
        if hasattr(self, 'layout_button'):self.layout_button.retranslate()

    def sync_controls(self):
        if self.scene is None or not hasattr(self,'layout_button'):return
        shell=self.window.design_shell
        joined=not shell.header.isHidden()
        self.title_layout.setContentsMargins(0,2,8 if joined or self.expanded else 18,2)
        page=self.window.pages[0][1]
        page.set_frame_editor_compact(getattr(page,'_editor_compact',False))
        wide_extra=0
        if page._editor_compact and not page.layout_actions.isHidden():
            wide_extra=sum(action.property('layoutWideWidth')-action.width()
                           for _,_,_,action in page._editor_buttons)
        if joined:
            if self.titlebar.parentWidget() is not shell.bar:
                self.titlebar.setParent(shell.bar);shell.top.addWidget(self.titlebar,0,Qt.AlignVCenter)
            shell.current_page.setVisible(self.window.width()>=980)
            self.titlebar.setFixedWidth(self.title_layout.sizeHint().width())
            page.set_frame_editor_compact(shell.top.minimumSize().width()+wide_extra>self.window.width())
            self.titlebar.setFixedWidth(self.title_layout.sizeHint().width())
        else:
            page.set_frame_editor_compact(self.title_layout.sizeHint().width()+wide_extra>self.window.width())
            shell.top.removeWidget(self.titlebar)
            if self.titlebar.parentWidget() is not self.scene:self.titlebar.setParent(self.scene)
            self.titlebar.setMinimumWidth(0);self.titlebar.setMaximumWidth(16777215)
            self.titlebar.setGeometry(0,0,self.window.width(),32)
        self.titlebar.show();self.title_layout.activate()
        if joined:shell.top.activate()
        self.materials.update()

    def _clip_content(self):
        if self.scene is None:return
        path=QPainterPath()
        path.addRoundedRect(QRectF(self.scene.rect()).adjusted(3,3,-3,-3),22,22)
        for widget in (self.window.content_host,self.window.design_shell.header,self.window.design_shell.footer):
            position=widget.mapTo(self.scene,QPoint())
            key=(self.scene.width(),self.scene.height(),position.x(),position.y(),self.expanded)
            if key!=getattr(widget,'_vitalux_clip_key',None):
                widget.setMask(QRegion() if self.expanded else QRegion(path.translated(-position.x(),-position.y()).toFillPolygon().toPolygon()))
                widget._vitalux_clip_key=key

    def _sync_page(self, *_):
        overview = self.window.pages[0][1]
        visible = self.window.stack.currentIndex() == 0
        if not visible and overview.board.editing:overview.save_editor()
        self.layout_button.setVisible(visible)
        if not visible:overview.layout_actions.hide()
        self.sync_controls()
