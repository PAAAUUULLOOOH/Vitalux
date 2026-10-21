"""Nocturne chrome: sculpted mercury, smoked sapphire and native instruments.

The large liquid-metal sculpture is cached with the background. Live readings
and short hover reflections repaint locally, without a fullscreen frame loop.
"""
import math
from functools import lru_cache
from pathlib import Path
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QLinearGradient,
                          QPainter, QPainterPath, QPen, QPixmap, QRadialGradient)

KEY = 'liquid_chrome'
PALETTE = dict(title='Liquid Chrome', subtitle='NOCTURNE / SCULPTED CHROME',
    bg='#090c10', sidebar='#11161c', card='#181f27', border='#7f8f9c',
    track='#283745', grid='#293744', text='#dce5ed', muted='#a7b6c5',
    accent='#c4d0da', secondary='#82b7cf', light='#5f7b94', bloom='#344f64',
    shadow='#05080c', series=('#c0d2df', '#81b6ce', '#8da8a6', '#9b9dbd'))


@lru_cache(maxsize=1)
def sculpture():
    return QPixmap(str(Path(__file__).resolve().parents[1]/'assets/artwork/liquid-chrome.png'))


def color(value, alpha=255):
    result = QColor(value)
    result.setAlpha(max(0, min(255, round(alpha))))
    return result


def metal(start, end, alpha=255):
    """Narrow polished reflections separated by broad graphite valleys."""
    gradient = QLinearGradient(start, end)
    for stop, tone in ((0,'#303c47'),(.16,'#9ba7b1'),(.23,'#d5dfe7'),
                       (.28,'#5b6e7e'),(.39,'#171f27'),(.63,'#8fa1af'),
                       (.67,'#dce6ee'),(.72,'#536879'),(.9,'#202d38'),(1,'#9aabb8')):
        gradient.setColorAt(stop, color(tone, alpha))
    return gradient


def shape(rect, compact=False):
    # An asymmetric cut-glass silhouette, softer on its lower trailing edge.
    x,y,w,h=rect.x(),rect.y(),rect.width(),rect.height()
    a=min(13 if compact else 26,w/6,h/4)
    b=min(7 if compact else 11,w/8,h/5)
    path=QPainterPath(QPointF(x+a,y))
    path.lineTo(x+w-b,y);path.quadTo(x+w,y,x+w,y+b)
    path.lineTo(x+w,y+h-a);path.quadTo(x+w,y+h,x+w-a,y+h)
    path.lineTo(x+b,y+h);path.quadTo(x,y+h,x,y+h-b)
    path.lineTo(x,y+a);path.quadTo(x,y,x+a,y)
    path.closeSubpath()
    return path


def scene_pixmap(size):
    w,h=max(1,size.width()),max(1,size.height())
    image=QPixmap(w,h);image.fill(color(PALETTE['bg']))
    p=QPainter(image);p.setRenderHint(QPainter.Antialiasing)
    rect=QRectF(0,0,w,h)
    original=sculpture()
    if not original.isNull():
        scaled=original.scaled(w,h,Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation)
        p.drawPixmap(round((w-scaled.width())/2),round((h-scaled.height())/2),scaled)
        p.end()
        return image
    light=QRadialGradient(QPointF(w*.76,h*.19),w*.88)
    for stop,tone in ((0,'#343e48'),(.36,'#1b252e'),(.72,'#0c1118'),(1,'#05080d')):
        light.setColorAt(stop,color(tone))
    p.fillRect(rect,light)
    # Two sculpted, tapered mercury ribbons. Highlights are reflective metal,
    # never broad white UI surfaces. All curves share native pixel resolution.
    for offset,opacity in ((0,1),(.13,.42)):
        ribbon=QPainterPath(QPointF(w*(.38+offset),-h*.2))
        ribbon.cubicTo(w*1.13,h*.06,w*.92,h*.40,w*(.72+offset),h*.50)
        ribbon.cubicTo(w*.23,h*.75,w*.79,h*.98,w*1.14,h*.96)
        ribbon.lineTo(w*1.16,h*1.08)
        ribbon.cubicTo(w*.55,h*1.05,w*.04,h*.75,w*(.61+offset),h*.43)
        ribbon.cubicTo(w*.88,h*.28,w*.96,h*.08,w*(.27+offset),-h*.16)
        ribbon.closeSubpath()
        p.setOpacity(opacity)
        p.fillPath(ribbon,metal(QPointF(w*.25,0),QPointF(w*1.03,h*.5),190))
        p.setPen(QPen(metal(QPointF(0,0),QPointF(w,h)),1.1))
        p.drawPath(ribbon)
    p.setOpacity(1)
    vignette=QRadialGradient(QPointF(w*.55,h*.48),w*.75)
    vignette.setColorAt(0,color('#05080d',35));vignette.setColorAt(.55,color('#05080d',55))
    vignette.setColorAt(1,color('#03060a',220));p.fillRect(rect,vignette)
    p.end();return image


def paint_panel(p, widget, rect, *, strong=False, compact=False, active=False):
    from .glass import draw_frosted_backdrop
    hover=getattr(widget,'_silver_hover',0.)
    body=shape(rect.translated(0,-hover),compact)
    p.save()
    p.setBrush(Qt.NoBrush)
    for width,alpha in ((7,23),(3,45)):
        p.setPen(QPen(color('#020407',alpha),width));p.drawPath(shape(rect.translated(0,3),compact))
    p.setClipPath(body)
    p.fillPath(body,color('#101923'))
    draw_frosted_backdrop(p,widget,rect,.42 if strong else .26)
    smoked=QLinearGradient(rect.topLeft(),rect.bottomRight())
    for stop,tone,a in ((0,'#323d47',190),(.18,'#212c36',220),(.50,'#121a22',225),(1,'#1c2732',215)):
        smoked.setColorAt(stop,color(tone,a))
    p.fillPath(body,smoked)
    # Polished upper lip and directional reflections across the smoked lens.
    reflection=QLinearGradient(rect.topLeft(),rect.topRight())
    for stop,tone,a in ((0,'#c5d7e7',2),(.18,'#d7e4ec',35),(.32,'#596f82',6),(.82,'#9eb4c6',2),(1,'#b8d0e4',18)):
        reflection.setColorAt(stop,color(tone,a+14*hover))
    p.fillPath(body,reflection)
    if strong and not compact:
        rim=QPainterPath(QPointF(rect.right()-rect.width()*.3,rect.top()-12))
        rim.cubicTo(rect.right()-rect.width()*.05,rect.top()+45,rect.right()-90,rect.bottom()-30,rect.right()+20,rect.bottom()+12)
        p.setPen(QPen(metal(rect.topLeft(),rect.bottomRight(),80),2.6));p.drawPath(rim)
    p.restore()
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(metal(rect.topLeft(),rect.bottomRight(),235 if active else 155),1.2 if active else .85));p.drawPath(body)
    inner=rect.adjusted(2,2,-2,-2)
    p.setPen(QPen(color('#a5bed2',28),.7));p.drawPath(shape(inner,compact))
    if not compact:
        p.setPen(QPen(color('#c2d4e2',95),1.1,Qt.SolidLine,Qt.RoundCap))
        p.drawLine(QPointF(rect.left()+26,rect.top()+2),QPointF(rect.left()+min(98,rect.width()*.3),rect.top()+2))


def paint_sidebar(p,widget,rect):
    dock=rect.adjusted(7,10,-5,-10)
    paint_panel(p,widget,dock,strong=True)
    p.save();p.setClipPath(shape(dock))
    seam=metal(QPointF(0,0),QPointF(0,rect.height()),125)
    p.setPen(QPen(seam,1));p.drawLine(QPointF(dock.right()-3,42),QPointF(dock.right()-3,dock.bottom()-35))
    p.restore()


def paint_nav(p,widget,rect,selected,hover):
    if selected:
        paint_panel(p,widget,rect,compact=True,active=True)
        p.setPen(QPen(color('#d9e7ef',75),.8))
        p.drawLine(QPointF(rect.left()+38,rect.bottom()-2),QPointF(rect.right()-12,rect.bottom()-2))
    elif hover>.001:
        p.setPen(QPen(color('#9ab4c9',100*hover),.7));p.setBrush(color('#8fadc5',12*hover))
        p.drawPath(shape(rect,True))


def orbit(p,center,diameter,value):
    r=QRectF(center.x()-diameter/2,center.y()-diameter/2,diameter,diameter)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(metal(r.topLeft(),r.bottomRight()),3.8));p.drawEllipse(r)
    p.setPen(QPen(color('#03070d'),1.4));p.drawEllipse(r.adjusted(3,3,-3,-3))
    face=QRadialGradient(center-QPointF(diameter*.2,diameter*.2),diameter*.7)
    face.setColorAt(0,color('#293b49',210));face.setColorAt(.6,color('#101a24',245));face.setColorAt(1,color('#050a10'))
    p.setBrush(face);p.setPen(QPen(color('#6a8399',90),.7));p.drawEllipse(r.adjusted(7,7,-7,-7))
    for tick in range(51):
        angle=math.radians(220-tick*5.2);outer=diameter*.43;inner=outer-(7 if tick%5==0 else 2.8)
        p.setPen(QPen(color('#bdcddb',180 if tick%5==0 else 65),1 if tick%5==0 else .65))
        p.drawLine(center+QPointF(math.cos(angle)*inner,-math.sin(angle)*inner),center+QPointF(math.cos(angle)*outer,-math.sin(angle)*outer))
    track=r.adjusted(diameter*.14,diameter*.14,-diameter*.14,-diameter*.14)
    p.setPen(QPen(color('#293e50'),3));p.drawArc(track,220*16,-260*16)
    if value is not None:
        fraction=max(0,min(100,value))/100
        p.setPen(QPen(metal(track.topLeft(),track.bottomRight()),3.2,Qt.SolidLine,Qt.RoundCap))
        p.drawArc(track,220*16,round(-260*16*fraction))
        angle=math.radians(220-260*fraction)
        tip=center+QPointF(math.cos(angle)*diameter*.35,-math.sin(angle)*diameter*.35)
        p.setPen(QPen(color('#b6d9ec'),1.7,Qt.SolidLine,Qt.RoundCap));p.drawLine(center,tip)
        p.setBrush(color('#cfdae2'));p.setPen(QPen(color('#07101b'),1));p.drawEllipse(center,3,3)


def paint_metric(p,widget):
    from .i18n import tr
    rect=QRectF(widget.rect()).adjusted(1,0,-1,0);wide=rect.width()>330
    font=QFont(widget.font())
    def text(area,value,size=12,tone=None,weight=QFont.Normal,align=Qt.AlignLeft|Qt.AlignVCenter):
        font.setPixelSize(size);font.setWeight(weight);p.setFont(font);p.setPen(color(tone or PALETTE['text']))
        p.drawText(area,align,p.fontMetrics().elidedText(str(value),Qt.ElideRight,max(1,round(area.width()))))
    text(QRectF(0,0,rect.width(),25),tr(widget.title).upper(),10,PALETTE['accent'],QFont.DemiBold)
    value=widget._display_value
    shown='–' if value is None else f'{value:.0f}'
    diameter=min(190,rect.height()-74,rect.width()*.5 if wide else rect.width()*.85)
    center=QPointF(rect.width()-diameter/2-2 if wide else rect.center().x(),rect.height()*.46)
    orbit(p,center,diameter,value)
    if wide:
        text(QRectF(0,42,rect.width()-diameter-10,76),shown,64,weight=QFont.Light)
        if value is not None:text(QRectF(5,112,100,20),'%' if widget.kind!='health' else '/ 100',12,PALETTE['muted'])
        text(QRectF(0,rect.height()-66,rect.width()-diameter-10,25),widget.extra,11,PALETTE['muted'])
    else:
        text(QRectF(0,center.y()-8,rect.width(),64),shown+(' %' if value is not None and widget.kind!='health' else ''),34,weight=QFont.Light,align=Qt.AlignCenter)
    text(QRectF(0,rect.height()-29,rect.width(),24),widget.detail,11,PALETTE['muted'])
    # A small sparkline uses actual history only; it never invents activity.
    if wide and len(widget.history)>1:
        area=QRectF(0,rect.height()-48,max(20,rect.width()-diameter-20),12)
        path=QPainterPath()
        connected=False
        for i,v in enumerate(widget.history):
            if not isinstance(v,(int,float)) or not math.isfinite(v):
                connected=False
                continue
            point=QPointF(area.left()+area.width()*i/(len(widget.history)-1),area.bottom()-area.height()*max(0,min(100,v))/100)
            if connected:path.lineTo(point)
            else:path.moveTo(point)
            connected=True
        p.setPen(QPen(color('#96b9d0'),1.2));p.drawPath(path)


def paint_gauge(p,widget,value,text,ring_color):
    side=min(widget.width(),widget.height())
    center=QPointF(widget.width()/2,widget.height()/2)
    orbit(p,center,side*.80,value)
    font=QFont(widget.font());font.setPixelSize(round(side*.19));font.setWeight(QFont.Light)
    p.setFont(font);p.setPen(color(PALETTE['text']))
    shown=text if text is not None else ('–' if widget.value is None else f'{widget.value:.0f}%')
    p.drawText(QRectF(0,center.y(),widget.width(),side*.30),Qt.AlignCenter,shown)


def paint_preview(p,tile,pal):
    w=tile.width()
    p.setPen(Qt.NoPen);p.setBrush(color('#101a25',235));p.drawRoundedRect(QRectF(7,7,18,62),6,6)
    p.setPen(QPen(color('#b9cddd'),1.2))
    for y in (17,28,39,50):p.drawLine(12,y,19,y)
    for r in (QRectF(34,8,w-47,17),QRectF(34,32,(w-51)*.56,36),QRectF(38+(w-51)*.56,32,(w-51)*.44-4,36)):
        p.setBrush(color('#122130',245));p.setPen(QPen(metal(r.topLeft(),r.bottomRight()),.8));p.drawPath(shape(r,True))
    p.setPen(QPen(color('#bed0df'),1.2));p.drawEllipse(QPointF(w*.44,49),11,11)
    p.setPen(QPen(color('#7aacc6'),1));p.drawArc(QRectF(w*.70,39,20,20),220*16,-260*16)
    p.fillRect(QRectF(0,75,w,40),color(pal['bg'],240))
    font=QFont(tile.font());font.setPixelSize(11);font.setWeight(QFont.DemiBold)
    p.setFont(font);p.setPen(color(pal['text']));p.drawText(QRectF(7,78,w-14,27),Qt.AlignCenter,tile.text())
    p.setClipping(False);p.setBrush(Qt.NoBrush)
    selected=tile.isChecked() or tile.hasFocus()
    p.setPen(QPen(color(pal['accent'],245 if selected else 85+100*tile._hover),2 if selected else 1))
    p.drawPath(shape(QRectF(tile.rect()).adjusted(2,2,-2,-2),True))
    if tile.isChecked():
        p.setPen(Qt.NoPen);p.setBrush(color(pal['accent']));p.drawEllipse(QPointF(w-15,14),7,7)
        p.setPen(QPen(color(pal['bg']),1.3));p.drawLine(QPointF(w-18,14),QPointF(w-16,16));p.drawLine(QPointF(w-16,16),QPointF(w-12,12))


def stylesheet():
    return '''
    #pageTitle {font-size:29px;font-weight:500;letter-spacing:-.6px;}
    #heroTitle {font-size:22px;font-weight:500;color:#d6e2ec;}
    #cardTitle {font-size:10px;font-weight:600;letter-spacing:1.7px;color:#acbfce;}
    #chipTitle {color:#91a8bb;letter-spacing:.6px;}
    #chipValue {color:#d0dde6;font-size:12px;font-weight:500;}
    QLineEdit,QComboBox,QSpinBox,QTextEdit,QListWidget,QTableWidget {
        color:#d3e0e9;background:#0d1722;border:1px solid #445b70;border-radius:9px;}
    QComboBox::drop-down {background:#1c2c3a;border-left:1px solid #455d72;}
    QComboBox QAbstractItemView {color:#d3e0e9;background:#101d29;selection-background-color:#2d465a;selection-color:#e2ebf0;}
    QPushButton#ghostBtn,QPushButton#langBtn,QToolButton#layoutAction {
        color:#c4d6e3;border:1px solid #5f798f;border-radius:9px;
        background:qlineargradient(x1:0,y1:0,x2:.3,y2:1,stop:0 #3b4c5a,stop:.12 #243746,stop:.5 #12202d,stop:1 #1e3040);}
    QPushButton#ghostBtn:hover,QPushButton#langBtn:hover,QToolButton#layoutAction:hover {border-color:#a4bdcf;color:#dceaf4;}
    QPushButton#primaryBtn,QPushButton#langBtn:checked {
        color:#101b26;border:1px solid #d0dfe9;border-radius:9px;
        background:qlineargradient(x1:0,y1:0,x2:.15,y2:1,stop:0 #c1d2df,stop:.22 #91aabd,stop:.5 #b2c6d5,stop:1 #6e8ca3);}
    QHeaderView::section {color:#acbfce;background:#152331;border:none;padding:8px;}
    QTableWidget::item:selected {color:#d9e6ef;background:#29445a;}
    QScrollBar:vertical {width:6px;background:transparent;}
    QScrollBar::handle:vertical {background:#617e95;border-radius:3px;}
    '''
