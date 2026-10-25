"""Authored Aether Glass and Eclipse Crystal materials and live instruments.

All geometry is native, resolution independent and shared by every renderer.
Atmospheres are cached; the live instruments only repaint on a sensor sample.
"""
import math
from PySide6.QtCore import QPointF, QRectF, Qt, QVariantAnimation, QEasingCurve
from PySide6.QtGui import (QColor, QFont, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap, QRadialGradient)
from PySide6.QtWidgets import QWidget, QLabel
from . import nebula_prism, quantum_core, crystal_atrium

COLLECTIONS = {
    'aether_glass': dict(title='Aether Glass', subtitle='OPTICAL GLASS / PLATINUM',
        bg='#080b19', sidebar='#11172c', card='#161b35', border='#777fae',
        track='#282d4b', grid='#2b3150', text='#f2f0ff', muted='#bbc0db',
        accent='#b7a6ff', secondary='#6cddf7', light='#5251a9', bloom='#316aa4',
        shadow='#10132d', series=('#b7a6ff', '#6cddf7', '#ece8ff', '#a6b9ce')),
    'eclipse_crystal': dict(title='Eclipse Crystal', subtitle='BLACK CRYSTAL / CHAMPAGNE',
        bg='#08090b', sidebar='#101113', card='#151617', border='#89785e',
        track='#302d27', grid='#35312c', text='#fff3df', muted='#c3b8a7',
        accent='#efc68d', secondary='#f4a86e', light='#9e7548', bloom='#4d3728',
        shadow='#101012', series=('#efc68d', '#f4a86e', '#e1d9cb', '#a8a6a2')),
}
COLLECTIONS['nebula_prism'] = nebula_prism.PALETTE
COLLECTIONS['quantum_core'] = quantum_core.PALETTE
COLLECTIONS['crystal_atrium'] = crystal_atrium.PALETTE
KEYS = tuple(COLLECTIONS)


def active():
    from . import theme
    return theme.mode() in KEYS


def color(value, alpha=255):
    c = QColor(value)
    c.setAlpha(max(0, min(255, round(alpha))))
    return c


def shape(rect, mode, compact=False):
    if mode == crystal_atrium.KEY:return crystal_atrium.shape(rect,compact)
    if mode == 'nebula_prism':
        return nebula_prism.shape(rect, compact)
    if mode == 'quantum_core':
        return quantum_core.shape(rect, compact)
    path = QPainterPath()
    if mode != 'eclipse_crystal':
        radius = 11 if compact else 22
        path.addRoundedRect(rect, radius, radius)
        return path
    cut = min(15 if not compact else 7, rect.width()/6, rect.height()/4)
    x, y, r, b = rect.left(), rect.top(), rect.right(), rect.bottom()
    path.moveTo(x+cut, y)
    for px, py in ((r-cut,y),(r,y+cut),(r,b-cut),(r-cut,b),(x+cut,b),(x,b-cut),(x,y+cut)):
        path.lineTo(px, py)
    path.closeSubpath()
    return path


def scene_pixmap(size, mode, phase=0.0):
    if mode == crystal_atrium.KEY:return crystal_atrium.scene_pixmap(size,phase)
    if mode == 'nebula_prism':
        return nebula_prism.scene_pixmap(size)
    if mode == 'quantum_core':
        return quantum_core.scene_pixmap(size)
    pal = COLLECTIONS[mode]
    w, h = max(1, size.width()), max(1, size.height())
    pixmap = QPixmap(w, h)
    pixmap.fill(color(pal['bg']))
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    rect = QRectF(0, 0, w, h)
    base = QLinearGradient(0, 0, w, h)
    for t, c in ((0,pal['shadow']),(.45,pal['bg']),(1,pal['sidebar'])):
        base.setColorAt(t, color(c))
    p.fillRect(rect, base)
    if mode == 'aether_glass':
        for offset in (0,.09):
            ribbon=QPainterPath(QPointF(w*(.76+offset),-h*.1))
            ribbon.cubicTo(w*.64,h*.30,w*.08,h*.28,w*.17,h*.68)
            ribbon.cubicTo(w*.27,h*.95,w*.87,h*.76,w*1.1,h*.95)
            ribbon.lineTo(w*1.1,h)
            ribbon.cubicTo(w*.86,h*.84,w*.24,h*1.04,w*.11,h*.72)
            ribbon.cubicTo(w*.03,h*.28,w*.57,h*.30,w*(.70+offset),-h*.1)
            ribbon.closeSubpath()
            glass=QLinearGradient(0,0,w,h)
            for t,tone,a in ((0,pal['accent'],5),(.22,pal['secondary'],50),(.42,pal['accent'],12),
                             (.61,pal['accent'],80),(.84,pal['secondary'],25),(1,pal['accent'],7)):
                glass.setColorAt(t,color(tone,a))
            p.fillPath(ribbon,glass)
        for i in range(4):
            ribbon = QPainterPath(QPointF(w*(.72+i*.08), -h*.15))
            ribbon.cubicTo(w*.63,h*.40,w*.10,h*.18,w*.17,h*.70)
            ribbon.cubicTo(w*.19,h*.93,w*.81,h*.75,w*1.1,h*(.85+i*.08))
            gleam = QLinearGradient(0, 0, w, h)
            for t, tone, a in ((0,pal['accent'],10),(.25,pal['secondary'],140),
                               (.5,pal['light'],25),(.75,pal['accent'],160),(1,pal['secondary'],0)):
                gleam.setColorAt(t, color(tone,a))
            for width, opacity in ((100,.08),(38,.16),(12,.22),(2.2,.8)):
                p.setOpacity(opacity)
                p.setPen(QPen(gleam,width,Qt.SolidLine,Qt.RoundCap))
                p.drawPath(ribbon)
        p.setOpacity(1)
    else:
        center = QPointF(w*.60, h*.13)
        radius = w*.33
        glow = QRadialGradient(center, radius*1.12)
        for t, tone, a in ((0,pal['light'],0),(.86,pal['light'],0),(.91,pal['accent'],48),
                           (.94,pal['secondary'],110),(.97,pal['light'],25),(1,pal['light'],0)):
            glow.setColorAt(t, color(tone,a))
        p.fillRect(rect, glow)
        lens = QRadialGradient(center-QPointF(radius*.5,radius*.5), radius*1.7)
        lens.setColorAt(0,color('#28231d'))
        lens.setColorAt(.5,color('#111113'))
        lens.setColorAt(1,color('#070809'))
        p.setBrush(lens)
        p.setPen(QPen(color(pal['accent'],100),.9))
        p.drawEllipse(center,radius*.91,radius*.91)
        # Authored facets are stable, without random noise or an animation loop.
        for i in range(14):
            x = w*((i*37 % 101)/100)
            y = h*((i*29 % 89)/100)
            facet = QPainterPath(QPointF(x,y))
            facet.lineTo(x+w*.18,y+h*.13)
            facet.lineTo(x+w*.05,y+h*.24)
            facet.closeSubpath()
            g = QLinearGradient(x,y,x+w*.17,y+h*.2)
            g.setColorAt(0,color(pal['accent'],12 if i%3 == 0 else 4))
            g.setColorAt(1,color(pal['accent'],0))
            p.fillPath(facet,g)
            p.setPen(QPen(color(pal['accent'],8),.5))
            p.drawPath(facet)
    shade = QLinearGradient(0,0,0,h)
    shade.setColorAt(0,QColor(0,0,0,0))
    shade.setColorAt(1,QColor(0,0,0,90))
    p.fillRect(rect,shade)
    p.end()
    return pixmap


def paint_panel(p, widget, rect, *, strong=False, compact=False, active=False):
    from . import theme
    if theme.mode() == crystal_atrium.KEY:return crystal_atrium.paint_panel(p,widget,rect,strong=strong,compact=compact,active=active)
    from . import theme
    from .glass import draw_frosted_backdrop
    mode = theme.mode()
    if mode == 'nebula_prism':
        return nebula_prism.paint_panel(p,widget,rect,strong=strong,compact=compact,active=active)
    if mode == 'quantum_core':
        return quantum_core.paint_panel(p,widget,rect,strong=strong,compact=compact,active=active)
    pal = COLLECTIONS[mode]
    path = shape(rect,mode,compact)
    p.save()
    p.setClipPath(path)
    p.fillPath(path,color(pal['card']))
    draw_frosted_backdrop(p,widget,rect,.62)
    wash = QLinearGradient(rect.topLeft(),rect.bottomRight())
    wash.setColorAt(0,color(pal['card'],182 if mode=='aether_glass' else 217))
    wash.setColorAt(.4,color(pal['bg'],208))
    wash.setColorAt(1,color(pal['card'],225))
    p.fillPath(path,wash)
    light = QLinearGradient(rect.topLeft(),rect.bottomLeft())
    light.setColorAt(0,color(pal['text'],24 if mode=='aether_glass' else 12))
    light.setColorAt(.13,color(pal['text'],3))
    light.setColorAt(1,color(pal['text'],0))
    p.fillPath(path,light)
    if not compact and rect.height()>110:
        if mode=='eclipse_crystal':
            # Light catches separate planes at the edges, never over data.
            for side in (0,1):
                x = rect.left() if not side else rect.right()-15
                facet = QPainterPath(QPointF(x,rect.top()+14))
                facet.lineTo(x+15,rect.top()+2)
                facet.lineTo(x+10,rect.top()+rect.height()*.35)
                facet.lineTo(x+15,rect.bottom()-13)
                facet.lineTo(x,rect.bottom()-5)
                facet.closeSubpath()
                reflection=QLinearGradient(x,rect.top(),x+15,rect.bottom())
                for t,a in ((0,115),(.25,12),(.42,77),(.60,4),(.86,60),(1,120)):
                    reflection.setColorAt(t,color(pal['accent'],a))
                p.fillPath(facet,reflection)
                for i in range(5):
                    top=rect.top()+14+i*(rect.height()-28)/5
                    height=(rect.height()-28)/5
                    triangle=QPainterPath(QPointF(x,top))
                    triangle.lineTo(x+15,top+height*.30)
                    triangle.lineTo(x+(3 if i%2 else 11),top+height)
                    triangle.closeSubpath()
                    g=QLinearGradient(x,top,x+15,top+height)
                    g.setColorAt(0,color(pal['text'],140 if i in (0,4) else 54))
                    g.setColorAt(.35,color(pal['accent'],15))
                    g.setColorAt(.68,color(pal['text'],75))
                    g.setColorAt(1,color(pal['bg'],0))
                    p.fillPath(triangle,g)
                    p.setPen(QPen(color(pal['text'],45),.6))
                    p.drawPath(triangle)
        else:
            curve=QPainterPath(QPointF(rect.left()+rect.width()*.20,rect.top()-8))
            curve.cubicTo(rect.left()-25,rect.top()+20,rect.left()-30,rect.bottom()-30,rect.left()+30,rect.bottom()+20)
            g=QLinearGradient(rect.topLeft(),rect.bottomLeft())
            g.setColorAt(0,color(pal['secondary'],135 if strong else 60))
            g.setColorAt(.40,color(pal['accent'],20))
            g.setColorAt(1,color(pal['accent'],90 if strong else 28))
            p.setPen(QPen(g,1.2))
            p.drawPath(curve)
    p.restore()
    edge=QLinearGradient(rect.topLeft(),rect.bottomRight())
    for t,tone,a in ((0,pal['text'],180),(.17,pal['accent'],160),(.4,pal['border'],60),
                      (.67,pal['border'],100),(.84,pal['secondary'],120),(1,pal['text'],180)):
        edge.setColorAt(t,color(tone,min(255,a+45) if active else a))
    p.setBrush(Qt.NoBrush)
    if active:
        p.setPen(QPen(color(pal['accent'],24),5))
        p.drawPath(path)
    p.setPen(QPen(edge,1.1 if active else .85))
    p.drawPath(path)
    p.setPen(QPen(color(pal['text'],16),.7))
    p.drawPath(shape(rect.adjusted(2,2,-2,-2),mode,compact))


def stylesheet(mode):
    if mode == crystal_atrium.KEY:return crystal_atrium.stylesheet()
    if mode=='nebula_prism':
        return nebula_prism.stylesheet()
    if mode=='quantum_core':
        return quantum_core.stylesheet()
    pal=COLLECTIONS[mode]
    radius=9 if mode=='aether_glass' else 3
    return f'''
    #heroTitle {{font-size:20px;font-weight:650;color:{pal['text']};}}
    #pageTitle {{font-size:30px;font-weight:750;}}
    #cardTitle {{font-size:10px;font-weight:700;letter-spacing:1.3px;color:{pal['text']};}}
    #chipValue {{font-size:11px;font-weight:650;color:{pal['text']};}}
    #chipTitle {{font-size:9px;color:{pal['muted']};}}
    QLineEdit,QComboBox,QSpinBox,QTextEdit,QListWidget,QTableWidget {{
        background:{pal['sidebar']};color:{pal['text']};border:1px solid {pal['border']};border-radius:{radius}px;}}
    QHeaderView::section {{background:{pal['sidebar']};color:{pal['muted']};border:none;padding:8px;}}
    QTableWidget::item {{padding:6px;border-bottom:1px solid {pal['grid']};}}
    QTableWidget::item:selected {{background:{pal['track']};color:{pal['text']};}}
    QComboBox::drop-down {{border-radius:{radius}px;background:{pal['card']};}}
    QPushButton#ghostBtn,QPushButton#langBtn,QToolButton#layoutAction {{
        border:1px solid {pal['border']};border-radius:{radius}px;background:{pal['sidebar']};color:{pal['text']};}}
    QPushButton#ghostBtn:hover,QPushButton#langBtn:hover,QToolButton#layoutAction:hover {{
        border-color:{pal['accent']};background:{pal['track']};}}
    QPushButton#primaryBtn,QPushButton#langBtn:checked {{
        background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {pal['text']},stop:.45 {pal['accent']},stop:1 {pal['border']});
        border-radius:{radius}px;border:1px solid {pal['accent']};color:{pal['bg']};}}
    QProgressBar,QProgressBar::chunk {{border-radius:{radius}px;}}
    QScrollBar::handle:vertical {{background:{pal['border']};border-radius:3px;}}
    '''


def paint_navigation(button):
    from . import theme
    from .nav_icons import paint_icon
    if theme.mode()=='nebula_prism':
        return nebula_prism.paint_navigation(button)
    p=QPainter(button)
    p.setRenderHint(QPainter.Antialiasing)
    rect=QRectF(button.rect()).adjusted(3,3,-3,-3)
    selected=button.isChecked()
    pal=COLLECTIONS[theme.mode()]
    if selected:
        paint_panel(p,button,rect,compact=True,active=True)
        if theme.mode()=='eclipse_crystal':
            face=QLinearGradient(rect.topLeft(),rect.bottomRight())
            face.setColorAt(0,color(pal['text']))
            face.setColorAt(.5,color(pal['accent']))
            face.setColorAt(1,color(pal['border']))
            p.fillPath(shape(rect,theme.mode(),True),face)
    elif button._hover_amount>.01 or button.hasFocus():
        p.fillPath(shape(rect,theme.mode(),True),color(pal['accent'],20))
    ink=color(pal['bg'] if selected and theme.mode()=='eclipse_crystal' else pal['text'])
    compact=button._compact
    x=rect.center().x()-10 if compact else rect.left()+12
    paint_icon(p,button.icon_key,QRectF(x,rect.center().y()-10,20,20),ink)
    if not compact:
        font=QFont(button.font())
        font.setPixelSize(12)
        font.setWeight(QFont.DemiBold if selected else QFont.Normal)
        p.setFont(font)
        p.setPen(ink)
        caption=button.text().split('    ',1)[-1]
        if button.glow and button._update_version:
            caption+=' '+button._update_version
        p.drawText(QRectF(rect.left()+40,rect.top(),rect.width()-47,rect.height()),
                   Qt.AlignLeft|Qt.AlignVCenter,
                   p.fontMetrics().elidedText(caption,Qt.ElideRight,max(1,round(rect.width()-47))))
    if button.hasFocus():
        p.setPen(QPen(color(pal['accent']),1,Qt.DotLine))
        p.setBrush(Qt.NoBrush)
        p.drawPath(shape(rect.adjusted(2,2,-2,-2),theme.mode(),True))
    p.end()


def paint_toggle(p,rect,checked,progress):
    from . import theme
    pal=COLLECTIONS[theme.mode()]
    p.setPen(QPen(color(pal['accent'] if checked else pal['border']),.8))
    p.setBrush(color(pal['track']))
    p.drawPath(shape(rect,theme.mode(),True))
    thumb=QRectF(rect.left()+3+progress*(rect.width()-rect.height()),rect.top()+3,rect.height()-6,rect.height()-6)
    fill=QLinearGradient(thumb.topLeft(),thumb.bottomRight())
    fill.setColorAt(0,color(pal['text'] if checked else pal['muted']))
    fill.setColorAt(1,color(pal['accent'] if checked else pal['border']))
    p.setBrush(fill)
    p.drawPath(shape(thumb,theme.mode(),True))


class Surface(QWidget):
    def paintEvent(self,event):
        if not active():
            return
        p=QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        paint_panel(p,self,QRectF(self.rect()).adjusted(1,1,-1,-1),compact=True)
        p.end()


def _atrium_preview(p,pal,box,width):
    """Three liquid-glass spheres over a glass strip and a floating dock."""
    from PySide6.QtGui import QRadialGradient,QLinearGradient
    box(QRectF(5,5,width-10,9))
    cell=(width-14)/3
    for i,(a,b) in enumerate((('#7fd6ff','#2b6bff'),('#ff8bdc','#a42cff'),('#ffcb72','#ff6a3c'))):
        x=5+i*(cell+2)
        box(QRectF(x,17,cell,32))
        cx,cy,r=x+cell/2,33,11.5
        p.setPen(Qt.NoPen)
        liquid=QLinearGradient(0,cy-r*.1,0,cy+r)
        liquid.setColorAt(0,color(a,235));liquid.setColorAt(1,color(b,245))
        clip=QPainterPath();clip.addEllipse(QPointF(cx,cy),r,r)
        p.save();p.setClipPath(clip);p.fillRect(QRectF(cx-r,cy-r*.1,2*r,r*1.1),liquid);p.restore()
        p.setBrush(Qt.NoBrush);p.setPen(QPen(color('#ffffff',150),.8));p.drawEllipse(QPointF(cx,cy),r,r)
        glint=QRadialGradient(QPointF(cx-r*.35,cy-r*.45),r*.5)
        glint.setColorAt(0,color('#ffffff',200));glint.setColorAt(1,color('#ffffff',0))
        p.setPen(Qt.NoPen);p.setBrush(glint);p.drawEllipse(QPointF(cx-r*.35,cy-r*.45),r*.45,r*.3)
    box(QRectF(5,52,(width-14)*.6,10))
    box(QRectF(5+(width-14)*.62,52,(width-14)*.38,10))
    dock_w=min(width-30,78)
    box(QRectF((width-dock_w)/2,65,dock_w,8),235)


def paint_preview(p,tile,pal):
    """Represent the actual horizontal/floating navigation in design previews."""
    mode=tile.key
    width=tile.width()
    def box(rect,alpha=200):
        p.setPen(QPen(color(pal['accent'],105),.6))
        p.setBrush(color(pal['card'],alpha))
        p.drawPath(shape(rect,mode,True))
    if mode=='crystal_atrium':
        _atrium_preview(p,pal,box,width)
        return _preview_tail(p,tile,pal,mode,width)
    if mode=='nebula_prism':
        nebula_prism.preview_contents(p,tile,pal,box,width)
        return _preview_tail(p,tile,pal,mode,width)
    box(QRectF(5,5,width-10,9))
    p.setPen(QPen(color(pal['text'],190),1))
    p.drawLine(11,9,31,9)
    offset=5
    if mode in ('aether_glass','quantum_core'):
        box(QRectF(5,18,18,52))
        for y in (24,33,42,51,60):
            p.setPen(QPen(color(pal['accent'],160),1.2))
            p.drawLine(10,y,17,y)
        offset=28
        y=18
    else:
        box(QRectF(5,17,width-10,8))
        for i in range(7):
            p.setPen(QPen(color(pal['accent'],180),1))
            x=12+i*(width-24)/7
            p.drawLine(QPointF(x,20),QPointF(x+5,20))
        y=30
    usable=width-offset-6
    for x,w in ((offset,usable*.48),(offset+usable*.51,usable*.22),(offset+usable*.76,usable*.24)):
        rect=QRectF(x,y,w,23)
        box(rect)
        path=QPainterPath(QPointF(x+4,y+18))
        for j,f in enumerate((.2,.5,.25,.65,.35,.45)):
            path.lineTo(x+4+(w-8)*j/5,y+20-f*15)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(color(pal['accent'],220),.8))
        p.drawPath(path)
    box(QRectF(offset,y+28,usable*.60,17))
    box(QRectF(offset+usable*.64,y+28,usable*.36,17))
    _preview_tail(p,tile,pal,mode,width)


def _preview_tail(p,tile,pal,mode,width):
    p.fillRect(QRectF(0,75,width,40),color(pal['bg'],235))
    font=QFont(tile.font());font.setPixelSize(11);font.setWeight(QFont.DemiBold)
    p.setFont(font);p.setPen(color(pal['text']))
    p.drawText(QRectF(7,78,width-14,27),Qt.AlignCenter,tile.text())
    p.setClipping(False)
    p.setBrush(Qt.NoBrush)
    selected=tile.isChecked() or tile.hasFocus()
    p.setPen(QPen(color(pal['accent'],245 if selected else round(75+100*tile._hover)),2 if selected else 1))
    outline=QRectF(tile.rect()).adjusted(2,2,-2,-2)
    p.drawPath(shape(outline,mode,True))
    if tile.isChecked():
        p.setPen(Qt.NoPen);p.setBrush(color(pal['accent']))
        p.drawEllipse(QPointF(width-15,14),7,7)
        p.setPen(QPen(color(pal['bg']),1.3))
        p.drawLine(QPointF(width-18,14),QPointF(width-16,16))
        p.drawLine(QPointF(width-16,16),QPointF(width-12,12))



class Metric(QWidget):
    """New instruments use real values and preserve unavailable data explicitly."""
    def __init__(self,title,kind,parent=None):
        super().__init__(parent)
        self.title,self.kind=title,kind
        self.value=None
        self.detail=''
        self.extra=''
        self.model_caption=QLabel(self)
        self.model_caption.setObjectName('muted')
        font=self.font();font.setPixelSize(11);self.model_caption.setFont(font)
        self.model_caption.setWordWrap(True)
        self.model_caption.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.model_caption.hide()
        self.history=[]
        self._display_value=None
        self._value_animation=QVariantAnimation(self)
        self._value_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._value_animation.valueChanged.connect(self._value_frame)
        self.setMinimumSize(110,100)

    def _value_frame(self,value):
        self._display_value=float(value)
        self.update()

    def hideEvent(self,event):
        self._value_animation.stop()
        self._display_value=self.value
        super().hideEvent(event)

    def set(self,value,detail='',*,extra='',history=()):
        from . import motion
        old=self._display_value
        self.value=value
        self._value_animation.stop()
        if value is not None and old is not None and self.isVisible() and motion.duration(210) and abs(value-old)>.05:
            self._value_animation.setDuration(motion.duration(210))
            self._value_animation.setStartValue(old)
            self._value_animation.setEndValue(float(value))
            self._value_animation.start()
        else:self._display_value=value
        self.detail=detail
        self.extra=extra
        self.model_caption.setText(extra if self.kind == "gpu" else "")
        self._place_caption()
        self.history=list(history)[-120:]
        self.setAccessibleName(self.title)
        self.setAccessibleDescription(f'{value if value is not None else "–"} · {detail} · {extra}')
        self.setToolTip(f'{extra}\n{detail}'.strip())
        self.update()

    def _place_caption(self):
        visible=self.kind=='gpu' and bool(self.extra)
        self.model_caption.setVisible(visible)
        height=max(18,self.model_caption.heightForWidth(max(20,self.width()-10))) if visible else 0
        self.model_caption.setGeometry(5,self.height()-height,self.width()-10,height)
        self.caption_height=height

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self._place_caption()

    def drawing_rect(self):
        from PySide6.QtCore import QRect
        # The model gets its own wrapped footer, outside the unchanged meter.
        height=max(1,self.height()-(getattr(self,'caption_height',0)+4 if self.kind=='gpu' else 0))
        return QRect(0,0,self.width(),height)

    def paintEvent(self,event):
        from . import theme
        from .i18n import tr
        p=QPainter(self)
        if theme.mode() == crystal_atrium.KEY:
            crystal_atrium.paint_metric(self,p);p.end();return
        if theme.mode()=='nebula_prism':
            nebula_prism.paint_metric(self,p)
            p.end()
            return
        if theme.mode()=='quantum_core':
            quantum_core.paint_metric(self,p)
            p.end()
            return
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        pal=COLLECTIONS[theme.mode()]
        rect=QRectF(self.drawing_rect()).adjusted(5,3,-5,-3)
        width=rect.width()
        font=QFont(self.font())
        def text(area,value,size=12,tone=None,weight=QFont.Normal,align=Qt.AlignLeft|Qt.AlignVCenter):
            font.setPixelSize(size)
            font.setWeight(weight)
            p.setFont(font)
            p.setPen(color(tone or pal['text']))
            value=p.fontMetrics().elidedText(str(value),Qt.ElideRight,max(1,round(area.width())))
            p.drawText(area,align,value)
        title_h=24
        text(QRectF(rect.left(),rect.top(),width,title_h),tr(self.title).upper(),11,weight=QFont.DemiBold)
        if self.kind == 'cpu':
            text(QRectF(rect.left(),rect.top()+27,width,22),self.extra,11,pal['muted'])
        shown='–' if self._display_value is None else f'{self._display_value:.0f} %'
        if self.kind=='health':
            shown='–' if self._display_value is None else f'{self._display_value:.0f}'
        large=round(min(65,max(28,width*.16)))
        y=rect.top()+54 if self.kind == 'cpu' else rect.top()+30
        if theme.mode()=='eclipse_crystal' and self.kind=='cpu' and width>380:
            gauge=QRectF(rect.left()+8,y,118,118)
            p.setPen(QPen(color(pal['track']),3))
            p.drawArc(gauge,225*16,-270*16)
            if self._display_value is not None:
                p.setPen(QPen(color(pal['accent']),3.5,Qt.SolidLine,Qt.RoundCap))
                p.drawArc(gauge,225*16,round(-270*16*max(0,min(100,self._display_value))/100))
            text(gauge,shown,35,weight=QFont.DemiBold,align=Qt.AlignCenter)
            graph=QRectF(rect.left()+149,y+13,width-157,max(35,rect.height()-y-56))
        else:
            text(QRectF(rect.left(),y,width,large+12),shown,large,weight=QFont.DemiBold)
            graph=QRectF(rect.left(),y+large+28,width,max(30,rect.bottom()-y-large-76))
        if self.kind in ('cpu','gpu'):
            self._graph(p,graph,pal)
        elif self.kind in ('ram','disk'):
            track=QRectF(rect.left(),y+large+27,width,28 if self.kind=='ram' else 9)
            segments=16 if self.kind=='ram' else 30
            for i in range(segments):
                box=QRectF(track.left()+i*track.width()/segments,track.top(),track.width()/segments-3,track.height())
                fraction=0 if self._display_value is None else max(0,min(1,self._display_value*segments/100-i))
                lit=fraction>0
                fill=QLinearGradient(box.topLeft(),box.bottomRight())
                fill.setColorAt(0,color(pal['text'] if lit else pal['track'],235 if lit else 110))
                fill.setColorAt(1,color(pal['accent'] if lit else pal['bg']))
                p.setBrush(fill)
                p.setPen(QPen(color(pal['accent'] if lit else pal['border'],140 if lit else 60),.7))
                if lit and fraction<1:
                    p.save()
                    p.setClipRect(QRectF(box.left(),box.top(),box.width()*fraction,box.height()))
                    p.drawPath(shape(box,theme.mode(),True))
                    p.restore()
                    p.setBrush(Qt.NoBrush)
                    p.setPen(QPen(color(pal['border'],60),.7))
                p.drawPath(shape(box,theme.mode(),True))
        text(QRectF(rect.left(),rect.bottom()-30,width,30),tr(self.detail),11,pal['muted'])
        p.end()

    def _graph(self,p,rect,pal):
        if rect.width()<5 or rect.height()<5:
            return
        for i in range(3):
            y=rect.top()+rect.height()*i/2
            p.setPen(QPen(color(pal['grid'],130),.6,Qt.DotLine))
            p.drawLine(QPointF(rect.left(),y),QPointF(rect.right(),y))
        runs=[]
        run=[]
        n=len(self.history)
        for i,value in enumerate(self.history):
            if value is None or not math.isfinite(float(value)):
                if run:runs.append(run)
                run=[]
                continue
            run.append(QPointF(rect.right()-(n-1-i)*rect.width()/max(59,n-1),
                              rect.bottom()-max(0,min(100,value))*rect.height()/100))
        if run:runs.append(run)
        for points in runs:
            path=QPainterPath(points[0])
            for point in points[1:]:path.lineTo(point)
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(color(pal['accent'],35),4.5,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
            p.drawPath(path)
            p.setPen(QPen(color(pal['accent']),1.5,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
            p.drawPath(path)
            if len(points)==1:
                p.setBrush(color(pal['accent']))
                p.drawEllipse(points[0],2,2)
