"""Light platinum, satin metal and cut-crystal surfaces, drawn at native scale.

The atmosphere is cached. Hover reflections animate only the affected panel;
there is no full-window shader, texture download or permanent repaint loop.
"""
import math
from PySide6.QtCore import QPointF,QRectF,Qt
from PySide6.QtGui import QColor,QFont,QLinearGradient,QPainter,QPainterPath,QPen,QPixmap,QRadialGradient

KEY='liquid_silver'
PALETTE=dict(title='Liquid Silver',subtitle='SATIN PLATINUM / OPTICAL CRYSTAL',
    bg='#e6ecf2',sidebar='#f5f8fc',card='#f8fbff',border='#aab9c8',
    track='#d3dfe9',grid='#cad5df',text='#203142',muted='#586b7e',
    accent='#356e98',secondary='#688aa7',light='#d1ecf9',bloom='#bdcbdc',
    shadow='#c8d4e0',series=('#356e98','#66738f','#21877e','#8c669d'))


def color(value,alpha=255):
    c=QColor(value);c.setAlpha(round(alpha));return c


def shape(rect,radius=22):
    path=QPainterPath();path.addRoundedRect(rect,radius,radius);return path


def scene_pixmap(size):
    w,h=max(1,size.width()),max(1,size.height())
    image=QPixmap(w,h);image.fill(color(PALETTE['bg']))
    p=QPainter(image);p.setRenderHint(QPainter.Antialiasing)
    rect=QRectF(0,0,w,h)
    base=QLinearGradient(0,0,w,h)
    for stop,tone in ((0,'#fbfdff'),(.38,'#e3ebf3'),(.72,'#f5f8fc'),(1,'#d1dfeb')):base.setColorAt(stop,color(tone))
    p.fillRect(rect,base)
    for x,y,r,tone,a in ((.12,.02,.75,'#ffffff',235),(.94,.65,.65,'#91b7d4',75),(.42,1.1,.68,'#ffffff',210)):
        g=QRadialGradient(QPointF(w*x,h*y),w*r)
        g.setColorAt(0,color(tone,a));g.setColorAt(1,color(tone,0));p.fillRect(rect,g)
    # Broad, asymmetric silver ribbons have a sharp lit lip and soft underside.
    for i in range(3):
        path=QPainterPath(QPointF(w*(.40+i*.14),-h*.2))
        path.cubicTo(w*(.12+i*.08),h*.2,w*(1.15-i*.08),h*.46,w*(.42+i*.14),h*1.14)
        sheen=QLinearGradient(0,0,w,h)
        for stop,tone,a in ((0,'#ffffff',0),(.28,'#ffffff',160),(.53,'#819bb2',50),(.75,'#ffffff',190),(1,'#ffffff',0)):
            sheen.setColorAt(stop,color(tone,a))
        for width,opacity in ((95,.08),(34,.15),(9,.25),(1.1,.9)):
            p.setOpacity(opacity);p.setPen(QPen(sheen,width,Qt.SolidLine,Qt.RoundCap));p.drawPath(path)
    p.setOpacity(1)
    # Widely spaced satin reflections remain fixed in the cached atmosphere.
    p.setPen(QPen(color('#ffffff',38),.7))
    for y in range(0,h,7):p.drawLine(0,y,w,y)
    p.end();return image


def paint_panel(p,widget,rect,*,strong=False,compact=False,active=False):
    from .glass import draw_frosted_backdrop
    amount=getattr(widget,'_silver_hover',1. if active else 0.)
    radius=12 if compact else 29 if strong else 23
    body=shape(rect.adjusted(0,-amount,0,-amount),radius)
    p.save()
    # A contact shadow is geometry, rather than an offscreen widget effect.
    p.setBrush(Qt.NoBrush)
    for width,a in ((8,3),(4,7),(1,14)):
        p.setPen(QPen(color('#47627d',a),width));p.drawPath(shape(rect.translated(0,2+amount),radius))
    p.setClipPath(body)
    p.fillPath(body,color('#f5f9fd'))
    draw_frosted_backdrop(p,widget,rect,.25)
    material=QLinearGradient(rect.topLeft(),rect.bottomRight())
    for stop,tone,a in ((0,'#ffffff',245),(.40,'#f6faff',223),(.78,'#e9f0f7',232),(1,'#fdfefe',240)):
        material.setColorAt(stop,color(tone,a))
    p.fillPath(body,material)
    reflection=QLinearGradient(rect.left(),rect.top(),rect.right(),rect.top()+rect.height()*.6)
    for stop,tone,a in ((0,'#ffffff',180),(.12,'#ffffff',35),(.46,'#c0dced',8),(.86,'#ffffff',80),(1,'#ffffff',180)):
        reflection.setColorAt(stop,color(tone,a))
    p.fillPath(body,reflection)
    if amount>.001:
        sweep=QLinearGradient(rect.left()+rect.width()*(.1+.55*amount),rect.top(),rect.right(),rect.bottom())
        sweep.setColorAt(0,color('#ffffff',0));sweep.setColorAt(.5,color('#ffffff',65*amount));sweep.setColorAt(1,color('#ffffff',0))
        p.fillPath(body,sweep)
    p.restore()
    edge=QLinearGradient(rect.topLeft(),rect.bottomRight())
    for stop,tone in ((0,'#ffffff'),(.21,'#c7d8e6'),(.50,'#8fa8bd'),(.79,'#d0deea'),(1,'#ffffff')):
        edge.setColorAt(stop,color(tone))
    p.setBrush(Qt.NoBrush);p.setPen(QPen(edge,1.25 if active else .9));p.drawPath(body)
    p.setPen(QPen(color('#ffffff',230),.8));p.drawPath(shape(rect.adjusted(2,2,-2,-2),max(3,radius-2)))


def paint_sidebar(p,widget,rect):
    dock=rect.adjusted(8,12,-6,-12)
    paint_panel(p,widget,dock,strong=True)
    seam=QLinearGradient(dock.topLeft(),dock.bottomRight())
    seam.setColorAt(0,color('#ffffff'));seam.setColorAt(.5,color('#9fb6ca',120));seam.setColorAt(1,color('#ffffff'))
    p.setPen(QPen(seam,.8));p.drawPath(shape(dock.adjusted(3,3,-3,-3),26))


def paint_gauge(p,widget,value,text,ring_color):
    side=min(widget.width(),widget.height());center=QPointF(widget.width()/2,widget.height()/2)
    diameter=side*.77;r=QRectF(center.x()-diameter/2,center.y()-diameter/2,diameter,diameter)
    face=QRadialGradient(center-QPointF(side*.12,side*.16),side*.6)
    face.setColorAt(0,color('#ffffff'));face.setColorAt(.65,color('#eff5fb'));face.setColorAt(1,color('#c6d6e4'))
    p.setBrush(face);p.setPen(QPen(color('#afc3d5'),.8));p.drawEllipse(r)
    p.setBrush(Qt.NoBrush);p.setPen(QPen(color('#ffffff'),1));p.drawEllipse(r.adjusted(2,2,-2,-2))
    for tick in range(41):
        angle=math.radians(220-tick*6.5);outer=side*.46;inner=outer-(7 if tick%5==0 else 3)
        p.setPen(QPen(color('#5b7a95',170 if tick%5==0 else 65),.9))
        p.drawLine(center+QPointF(math.cos(angle)*inner,-math.sin(angle)*inner),center+QPointF(math.cos(angle)*outer,-math.sin(angle)*outer))
    track=r.adjusted(9,9,-9,-9)
    p.setPen(QPen(color('#cedbe7'),3,Qt.SolidLine,Qt.RoundCap));p.drawArc(track,220*16,-260*16)
    if value is not None:
        value=max(0,min(100,value));angle=math.radians(220-260*value/100)
        p.setPen(QPen(color(ring_color),3.2,Qt.SolidLine,Qt.RoundCap));p.drawArc(track,220*16,round(-260*16*value/100))
        tip=center+QPointF(math.cos(angle)*diameter*.38,-math.sin(angle)*diameter*.38)
        tail=center-QPointF(math.cos(angle)*diameter*.10,-math.sin(angle)*diameter*.10)
        p.setPen(QPen(color('#354d63'),1.3,Qt.SolidLine,Qt.RoundCap));p.drawLine(tail,tip)
        p.setBrush(color('#667f96'));p.setPen(QPen(color('#ffffff'),1));p.drawEllipse(center,3.2,3.2)
    font=QFont(widget.font());font.setFamilies(['DejaVu Sans Mono','monospace']);font.setPixelSize(round(side*.205));font.setWeight(QFont.Medium)
    p.setFont(font);p.setPen(color(PALETTE['text']))
    shown=text if text is not None else ('–' if widget.value is None else f'{widget.value:.0f}%')
    p.drawText(r.adjusted(0,side*.17,0,side*.17),Qt.AlignCenter,shown)


def stylesheet():
    return '''
    #pageTitle {font-size:29px;font-weight:600;letter-spacing:-.5px;}
    #heroTitle {font-size:22px;font-weight:500;color:#263c50;}
    #cardTitle {font-size:10px;font-weight:700;letter-spacing:1.6px;color:#496b87;}
    #chipTitle,#sidebarDistro,#sidebarVersion {color:#596e82;}
    #chipValue {font-size:12px;font-weight:600;color:#253c50;}
    #telemetryValue,#bigName {color:#203142;font-weight:500;}
    QToolTip {background:#f7fbff;color:#203142;border:1px solid #aabfce;padding:8px;}
    QLineEdit,QComboBox,QSpinBox,QTextEdit,QListWidget,QTableWidget {
        color:#253c50;background:#f4f8fc;border:1px solid #b4c4d2;border-radius:11px;}
    QComboBox::drop-down {background:#e7eef5;border-left:1px solid #bdcbd7;}
    QComboBox QAbstractItemView {color:#203142;background:#f5f9fd;selection-background-color:#d6e6f2;selection-color:#203142;}
    QPushButton#ghostBtn,QPushButton#langBtn,QToolButton#layoutAction {
        background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #e3ecf4);
        color:#304c63;border:1px solid #afc3d4;border-radius:11px;}
    QPushButton#ghostBtn:hover,QPushButton#langBtn:hover,QToolButton#layoutAction:hover {
        background:#edf7ff;border-color:#7299b8;}
    QPushButton#primaryBtn,QPushButton#langBtn:checked {color:#ffffff;background:#356e98;border:1px solid #356e98;border-radius:11px;}
    QHeaderView::section {color:#4f687e;background:#eaf1f7;border:none;padding:8px;}
    QTableWidget::item:selected {color:#203142;background:#dceaf5;}
    QScrollBar:vertical {width:7px;background:transparent;}
    QScrollBar::handle:vertical {background:#a7bfd1;border-radius:3px;}
    '''
