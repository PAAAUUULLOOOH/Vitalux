"""Native, keyboard-accessible background and accent previews."""
from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QAbstractButton, QSizePolicy, QWidget, QGridLayout, QLayout
from . import backdrops, settings, theme, user_background
from .premium import DesignTile, rounded
from .i18n import tr


class PreviewGrid(QWidget):
    """Wrap previews without making the settings page wider than its viewport."""
    def __init__(self, minimum=150, maximum=4):
        super().__init__()
        self.minimum,self.maximum=minimum,maximum
        self.tiles=[];self._columns=0
        self.grid=QGridLayout(self)
        self.grid.setContentsMargins(0,0,0,0);self.grid.setSpacing(10)
        self.grid.setSizeConstraint(QLayout.SetNoConstraint)
        self.setMinimumWidth(0)
        self.setFocusPolicy(Qt.StrongFocus)

    def set_tiles(self, tiles):
        for tile in self.tiles:self.grid.removeWidget(tile)
        self.tiles=list(tiles);self._columns=0;self.reflow()
        self.setFocusProxy(self.tiles[0] if self.tiles else None)

    def reflow(self):
        columns=max(1,min(self.maximum,(self.width()+10)//(self.minimum+10)))
        if columns==self._columns:return
        self._columns=columns
        for tile in self.tiles:self.grid.removeWidget(tile)
        for column in range(self.maximum):self.grid.setColumnStretch(column,0)
        for i,tile in enumerate(self.tiles):self.grid.addWidget(tile,i//columns,i%columns)
        for column in range(columns):self.grid.setColumnStretch(column,1)
        rows=(len(self.tiles)+columns-1)//columns
        height=self.tiles[0].height() if self.tiles else 0
        self.setFixedHeight(max(0,rows*height+max(0,rows-1)*10))

    def resizeEvent(self,event):
        super().resizeEvent(event);self.reflow()


class BackgroundTile(DesignTile):
    def __init__(self, key, parent=None):
        super().__init__(key, parent)
        self.setProperty('vitaluxCapabilityHints', False)
        self.setFixedHeight(92)

    def retranslate(self):
        title = 'Eigenes Bild …' if self.key == 'custom_image' else dict(backdrops.PRESETS)[self.key]
        self.setText(tr(title))
        self.setAccessibleName(self.text())
        self.setToolTip(self.text())

    def paintEvent(self, event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        scale=.975+.025*self._hover
        p.translate(self.width()/2,self.height()/2);p.scale(scale,scale)
        p.translate(-self.width()/2,-self.height()/2)
        rect=QRectF(self.rect()).adjusted(2,2,-2,-2);path=rounded(rect,10)
        p.setClipPath(path)
        style=backdrops.resolve(self.key,theme.mode())
        selected=settings.get('custom_background_selected','')
        source=user_background.image_path(selected) if style=='custom_image' else None
        stamp=source.stat().st_mtime_ns if source else None
        key=(style,self.size(),theme.mode(),theme.accent(),selected,stamp,settings.get('custom_background_fit','cover'),settings.get('background_tint',''))
        if self._background_key!=key:
            if style=='custom_image':
                self._background=user_background.draw(self.size(),selected,settings.get('custom_background_fit','cover'))
            else:self._background=backdrops.render(self.size(),style,theme.accent(),theme.is_light())[0]
            self._background=backdrops.tint(self._background,settings.get('background_tint',''))
            self._background_key=key
        p.drawPixmap(0,0,self._background)
        if style=='custom_image' and source is None:
            p.setPen(QPen(QColor(theme.TEXT),2));cx,cy=rect.center().x(),rect.center().y()-10
            p.drawLine(QPointF(cx-8,cy),QPointF(cx+8,cy));p.drawLine(QPointF(cx,cy-8),QPointF(cx,cy+8))
        p.fillRect(QRectF(0,self.height()-29,self.width(),29),QColor(8,12,18,225))
        p.setPen(QColor('#f0f4f8'));p.drawText(QRectF(7,self.height()-27,self.width()-14,25),Qt.AlignCenter,self.text())
        p.setClipping(False);p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(theme.accent() if self.isChecked() or self.hasFocus() else theme.BORDER),2 if self.isChecked() else 1))
        p.drawPath(path)
        if self.isChecked():
            p.setBrush(QColor(theme.accent()));p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(self.width()-14,14),5,5)
        p.end()


class AccentTile(QAbstractButton):
    def __init__(self, value, title, color, parent=None):
        super().__init__(parent)
        self.value,self.color=value,color
        self.setText(title);self.setAccessibleName(title);self.setToolTip(title)
        self.setCheckable(True);self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40);self.setMinimumWidth(110)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        r=QRectF(self.rect()).adjusted(1,1,-1,-1)
        p.setBrush(QColor(theme.CARD));p.setPen(QPen(QColor(theme.accent() if self.isChecked() or self.hasFocus() else theme.BORDER),2 if self.isChecked() else 1))
        p.drawRoundedRect(r,8,8)
        c=QColor(self.color if self.isEnabled() else theme.MUTED)
        p.setPen(QPen(QColor(theme.TEXT),.6));p.setBrush(c);p.drawEllipse(QPointF(18,20),8,8)
        p.setPen(QColor(theme.TEXT if self.isEnabled() else theme.MUTED))
        text=p.fontMetrics().elidedText(self.text(),Qt.ElideRight,max(1,self.width()-41))
        p.drawText(QRectF(33,0,self.width()-40,40),Qt.AlignVCenter|Qt.AlignLeft,text);p.end()
