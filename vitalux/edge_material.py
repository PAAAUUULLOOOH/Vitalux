"""Bounded native-resolution navigation materials following the window contour."""
import math
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap, QRegion
from PySide6.QtWidgets import QWidget
from . import theme, premium


class EdgeMaterials(QWidget):
    """Paint the sidebar behind live widgets; retain just one cache per surface."""
    def __init__(self, frame):
        super().__init__(frame.scene)
        self.frame = frame
        self._cache = {}
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAutoFillBackground(False)
        self.show()
        self.lower()

    def _image(self, name, widget):
        scene = self.frame.scene
        ratio = scene.devicePixelRatioF()
        wallpaper = scene.sharp_backdrop()
        size = scene.size() if name == 'sidebar' else widget.size()
        width = widget.width()
        height = size.height()
        palette = (theme.mode(), theme.BG, theme.CARD, theme.SIDEBAR,
                   theme.BORDER, theme.TEXT, theme.accent(), theme.secondary_accent())
        key = (width, height, scene.size(), ratio, self.frame.expanded,
               scene._composed_key, palette)
        cached = self._cache.get(name)
        if cached and cached[0] == key:
            return cached[1]
        image = QImage(max(1,math.ceil(width*ratio)),max(1,math.ceil(height*ratio)),
                       QImage.Format_ARGB32_Premultiplied)
        image.setDevicePixelRatio(ratio)
        image.fill(QColor(theme.BG))
        painter = QPainter(image)
        if not wallpaper.isNull():painter.drawPixmap(0,0,wallpaper)
        painter.setRenderHint(QPainter.Antialiasing)
        if name == 'sidebar':
            widget._paint_material(painter,QRectF(0,0,width,height))
        else:
            # Extend the authored pane past the local edges: only the shared
            # window contour and its highlight close the outer silhouette.
            premium.paint_panel(painter,widget,QRectF(widget.rect()).adjusted(-32,-32,32,32),compact=True)
            painter.setPen(QPen(QColor(theme.BORDER),1))
            start = self.frame.window.sidebar.width() if not self.frame.window.sidebar.isHidden() else 0
            painter.drawLine(start,widget.height()-1,widget.width(),widget.height()-1)
        painter.end()
        if name == 'sidebar':
            from .window_frame import outline
            mask = QImage(image.size(),QImage.Format_ARGB32_Premultiplied)
            mask.setDevicePixelRatio(ratio);mask.fill(0)
            painter = QPainter(mask);painter.setRenderHint(QPainter.Antialiasing)
            path = outline(scene.rect(),0 if self.frame.expanded else 24)
            painter.fillPath(path,QColor('white'));painter.setPen(QPen(QColor('white'),1));painter.drawPath(path)
            painter.end()
            painter = QPainter(image)
            painter.setPen(QPen(QColor(theme.BORDER),1));painter.setBrush(Qt.NoBrush)
            painter.setRenderHint(QPainter.Antialiasing);painter.drawPath(path)
            painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            painter.drawImage(0,0,mask);painter.end()
        self._cache[name] = (key,image)
        return image

    def paintEvent(self,event):
        sidebar = self.frame.window.sidebar
        if sidebar.isHidden():
            self._cache.pop('sidebar',None)
            return
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.drawImage(0,0,self._image('sidebar',sidebar));painter.end()

    def paint_header(self, painter, widget):
        # Authored glass stays translucent over live scrolling content. Keep
        # the outer antialiased highlight owned by the root window unchanged.
        painter.save()
        if not self.frame.expanded:
            key=(self.frame.scene.width(),self.frame.scene.height())
            if key!=getattr(self,'_header_clip_key',None):
                path=QPainterPath()
                path.addRoundedRect(QRectF(self.frame.scene.rect()).adjusted(3,3,-3,-3),22,22)
                self._header_clip=QRegion(path.toFillPolygon().toPolygon())
                self._header_clip_key=key
            painter.setClipRegion(self._header_clip)
        painter.setOpacity(.86)
        painter.drawImage(0,0,self._image('header',widget))
        painter.restore()

    def sidebar_background(self):
        sidebar=self.frame.window.sidebar
        return QPixmap.fromImage(self._image('sidebar',sidebar)).copy(0,0,
            round(sidebar.width()*self.devicePixelRatioF()),round(sidebar.height()*self.devicePixelRatioF()))

    def refresh(self):
        if self.frame.window.design_shell.header.isHidden():
            self._cache.pop('header',None)
        self.setGeometry(self.frame.scene.rect())
        self.lower()
        self.update()

