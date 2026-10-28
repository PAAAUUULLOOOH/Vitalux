"""Bounded native-resolution navigation materials following the window contour."""
import math
from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap, QRegion
from PySide6.QtWidgets import QWidget
from . import theme, premium


class HeaderMaterial(QWidget):
    """The header's part of one navigation pane, above the scrolling page."""
    def __init__(self, materials):
        super().__init__(materials.parentWidget())
        self.materials=materials
        self.setAttribute(Qt.WA_TransparentForMouseEvents,True)
        self.hide()

    def paintEvent(self,event):
        painter=QPainter(self)
        w=self.materials.frame.window;height=w.design_shell.header.height()
        region=QRegion(QRect(0,0,w.width(),height))
        if theme.mode() in ('crystal_atrium','aurora_bloom'):
            region=region.united(QRegion(QRect(w.sidebar.width(),height,22,22)))
        painter.setClipRegion(region)
        painter.drawImage(0,0,self.materials._joined_image('header'))
        painter.end()


class EdgeMaterials(QWidget):
    """Paint the sidebar behind live widgets; retain just one cache per surface."""
    def __init__(self, frame):
        super().__init__(frame.scene)
        self.frame = frame
        self._cache = {}
        self.header_layer=HeaderMaterial(self)
        self.setProperty('vitaluxEdgeJoined',True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAutoFillBackground(False)
        self.show()
        self.lower()

    def joined(self):
        captured=getattr(self,'_capture_joined',None)
        if captured is not None:return captured
        shell=self.frame.window.design_shell
        return not shell.header.isHidden() and not self.frame.window.sidebar.isHidden()

    def navigation_path(self):
        """One silhouette: rounded outer ends and a concave inner glass corner."""
        w=self.frame.window;header=w.design_shell.header
        radius=22 if theme.mode()=='crystal_atrium' else 0
        inner_radius=22 if theme.mode() in ('crystal_atrium','aurora_bloom') else 0
        path=QPainterPath();side=QPainterPath()
        path.addRoundedRect(QRectF(3,3,w.width()-6,header.height()-3),radius,radius)
        side.addRoundedRect(QRectF(3,3,w.sidebar.width()-3,w.height()-6),radius,radius)
        path=path.united(side)
        if inner_radius:
            radius=inner_radius
            x,y=w.sidebar.width(),header.height()
            corner=QPainterPath();corner.addRect(QRectF(x,y,radius,radius))
            inside=QPainterPath();inside.addEllipse(QRectF(x,y,2*radius,2*radius))
            path=path.united(corner.subtracted(inside))
        if not self.frame.expanded:
            outer=QPainterPath()
            outer.addRoundedRect(QRectF(w.rect()).adjusted(3,3,-3,-3),22,22)
            path=path.intersected(outer)
        return path

    def _joined_image(self,name):
        scene=self.frame.scene;w=self.frame.window
        ratio=scene.devicePixelRatioF();height=w.design_shell.header.height()
        radius=22 if theme.mode() in ('crystal_atrium','aurora_bloom') else 0
        patch=(QRect(0,0,w.width(),height+radius) if name=='header' else
               QRect(0,0,w.sidebar.width(),w.height()))
        scene.sharp_backdrop()
        key=(patch.size(),w.size(),w.sidebar.width(),height,ratio,scene._composed_key,
             theme.mode(),theme.accent(),theme.secondary_accent(),self.frame.expanded)
        cached=self._cache.get('joined-'+name)
        if cached and cached[0]==key:return cached[1]
        image=QImage(max(1,math.ceil(patch.width()*ratio)),max(1,math.ceil(patch.height()*ratio)),QImage.Format_ARGB32_Premultiplied)
        image.setDevicePixelRatio(ratio);image.fill(0)
        painter=QPainter(image);painter.setRenderHint(QPainter.Antialiasing)
        # Both bounded patches use the same scene coordinates and shader.
        # No full-window material cache or independently shaded overlapping pane.
        premium.paint_sidebar(painter,self,QRectF(scene.rect()).adjusted(-32,-32,32,32))
        painter.setPen(QPen(QColor(theme.BORDER),1.2));painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.navigation_path());painter.end()
        mask=QImage(image.size(),QImage.Format_ARGB32_Premultiplied)
        mask.setDevicePixelRatio(ratio);mask.fill(0)
        painter=QPainter(mask);painter.setRenderHint(QPainter.Antialiasing)
        # Both halves retain the same translucency. The header remains above
        # live scrolling cards rather than an opaque wallpaper sample.
        painter.fillPath(self.navigation_path(),QColor(255,255,255,219));painter.end()
        painter=QPainter(image);painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.drawImage(0,0,mask);painter.end()
        self._cache['joined-'+name]=(key,image)
        return image

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
            painter.fillPath(path,QColor('white'))
            painter.end()
            painter = QPainter(image)
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
        if self.joined():
            height=self.frame.window.design_shell.header.height()
            painter.setClipRect(QRect(0,height,sidebar.width(),max(0,self.height()-height)))
            painter.drawImage(0,0,self._joined_image('sidebar'))
        else:
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.drawImage(0,0,self._image('sidebar',sidebar))
        painter.end()

    def paint_header(self, painter, widget):
        if self.joined():return
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
        joined=self.joined()
        self.header_layer.setVisible(joined)
        if joined:
            self._cache.pop('sidebar',None);self._cache.pop('header',None)
            w=self.frame.window;radius=22 if theme.mode() in ('crystal_atrium','aurora_bloom') else 0
            self.header_layer.setGeometry(0,0,w.width(),w.design_shell.header.height()+radius)
            self.header_layer.update();self.header_layer.raise_()
            w.design_shell.header.raise_();self.frame.titlebar.raise_()
        else:
            self._cache.pop('joined-header',None);self._cache.pop('joined-sidebar',None)
        if hasattr(self.frame,'border'):
            self.frame.border.setGeometry(self.frame.scene.rect())
            self.frame.border.raise_();self.frame.border.update()

