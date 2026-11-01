"""Rounded application dialogs with accessible close, move and resize controls."""
from PySide6.QtCore import QObject,QEvent,QRectF,Qt
from PySide6.QtGui import QPainterPath,QRegion
from PySide6.QtWidgets import QWidget,QHBoxLayout,QLabel,QSizePolicy,QMessageBox,QApplication
from .window_frame import WindowButton,ResizeHandle


class DialogTitleBar(QWidget):
    def __init__(self,frame):
        super().__init__(frame.window)
        frame.titlebar=self
        self.frame=frame;self._drag=None
        self.setObjectName('dialogTitleBar')
        self.setFixedHeight(36)
        row=QHBoxLayout(self);row.setContentsMargins(12,4,6,4);row.setSpacing(8)
        self.caption=QLabel();self.caption.setObjectName('strong')
        self.caption.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred)
        self.caption.setAttribute(Qt.WA_TransparentForMouseEvents,True)
        row.addWidget(self.caption,1)
        self.close_button=WindowButton('close',frame);row.addWidget(self.close_button)

    def mousePressEvent(self,event):
        if event.button()!=Qt.LeftButton:return super().mousePressEvent(event)
        handle=self.frame.window.windowHandle()
        if not (handle and handle.startSystemMove()) and not QApplication.platformName().startswith('wayland'):
            self._drag=event.globalPosition().toPoint()-self.frame.window.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self,event):
        if self._drag is not None and event.buttons()&Qt.LeftButton:
            self.frame.window.move(event.globalPosition().toPoint()-self._drag);event.accept()
        else:super().mouseMoveEvent(event)

    def mouseReleaseEvent(self,event):
        self._drag=None;super().mouseReleaseEvent(event)


class DialogFrame(QObject):
    def __init__(self,window):
        super().__init__(window)
        self.window=window
        self.titlebar=DialogTitleBar(self)
        self.handles=[]
        if not isinstance(window,QMessageBox):
            edges=(Qt.TopEdge,Qt.BottomEdge,Qt.LeftEdge,Qt.RightEdge,
                   Qt.TopEdge|Qt.LeftEdge,Qt.TopEdge|Qt.RightEdge,
                   Qt.BottomEdge|Qt.LeftEdge,Qt.BottomEdge|Qt.RightEdge)
            self.handles=[ResizeHandle(self,edge) for edge in edges]
        window.installEventFilter(self)

    @property
    def expanded(self):return self.window.isMaximized() or self.window.isFullScreen()

    def toggle_maximized(self):
        self.window.showNormal() if self.expanded else self.window.showMaximized()

    def eventFilter(self,watched,event):
        if event.type() in (QEvent.Resize,QEvent.Show,QEvent.WindowTitleChange,QEvent.LayoutRequest):self.sync()
        return False

    def sync(self):
        w=self.window
        self.titlebar.setGeometry(12,6,max(0,w.width()-24),36)
        self.titlebar.caption.setText(w.windowTitle());self.titlebar.caption.setToolTip(w.windowTitle())
        self.titlebar.close_button.retranslate();self.titlebar.raise_()
        width,height=w.width(),w.height();t,c=4,10
        from PySide6.QtCore import QRect
        rects=(QRect(c,0,width-2*c,t),QRect(c,height-t,width-2*c,t),
               QRect(0,c,t,height-2*c),QRect(width-t,c,t,height-2*c),
               QRect(0,0,c,c),QRect(width-c,0,c,c),
               QRect(0,height-c,c,c),QRect(width-c,height-c,c,c))
        for handle,rect in zip(self.handles,rects):
            handle.setGeometry(rect);handle.setVisible(not self.expanded);handle.raise_()
        native=w.windowHandle()
        key=(width,height,self.expanded)
        if native and QApplication.platformName()!='offscreen' and key!=getattr(self,'_mask_key',None):
            path=QPainterPath();path.addRoundedRect(QRectF(w.rect()).adjusted(-1,-1,1,1),0 if self.expanded else 24,0 if self.expanded else 24)
            native.setMask(QRegion(path.toFillPolygon().toPolygon()));self._mask_key=key


def attach_dialog(window):
    app=QApplication.instance()
    if app is not None and not app.styleSheet():
        from . import theme,settings,distro,wallpaper_accents
        theme.set_mode('minimal' if settings.get('ultra_eco',False) else settings.get('theme','obsidian_gold'))
        theme.set_accent(wallpaper_accents.resolve_accent(settings.get('accent','design_default'),distro.info()['color']))
        app.setStyleSheet(theme.stylesheet())
    window.setWindowFlag(Qt.FramelessWindowHint,True)
    window.setAttribute(Qt.WA_TranslucentBackground,True)
    window.setAutoFillBackground(False)
    window._vitalux_dialog_frame=DialogFrame(window)
