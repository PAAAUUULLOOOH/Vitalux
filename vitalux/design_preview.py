"""Complete miniature layouts fitted inside the gallery's safe rounded area."""
from PySide6.QtCore import QRectF,QPointF,Qt
from PySide6.QtGui import QColor,QPen,QPainterPath,QFont

def paint(p,tile,pal):
    from .gallery_shape import finish
    from .design_capabilities import paint as capabilities
    p.save()
    # The icon column and rounded corners are deliberately outside the miniature.
    frame=QRectF(13,13,max(50,tile.width()-55),59)
    p.setPen(QPen(QColor(pal['border']),.7));p.setBrush(QColor(pal['bg']))
    p.drawRoundedRect(frame,7,7)
    bloom=tile.key=='aurora_bloom';sculpt=tile.key=='sculpt'
    if bloom:
        p.save();clip=QPainterPath();clip.addRoundedRect(frame,7,7);p.setClipPath(clip,Qt.IntersectClip)
        p.drawPixmap(frame,tile._background,QRectF(tile._background.rect()));p.restore()
    p.save();p.setClipRect(frame.adjusted(3,3,-3,-3))
    quantum=tile.key=='quantum_core';nebula=tile.key=='nebula_prism';eclipse=tile.key=='eclipse_crystal'
    def panel(rect):
        p.setPen(QPen(QColor(pal['accent']),.55));p.setBrush(QColor(pal['card']))
        if quantum:
            path=QPainterPath(rect.topLeft()+QPointF(3,0));path.lineTo(rect.topRight());path.lineTo(rect.bottomRight()-QPointF(3,0));path.lineTo(rect.bottomLeft());path.closeSubpath();p.drawPath(path)
        elif bloom:
            from .aurora_bloom import shape
            p.drawPath(shape(rect,True,scale=.3))
        elif sculpt:
            from .sculpt import shape
            p.setPen(QPen(QColor(pal['border']),.6))
            p.drawPath(shape(rect,True))
        else:p.drawRoundedRect(rect,2.5,2.5)
    left=frame.left()+5;right=frame.right()-5;top=frame.top()+5;bottom=frame.bottom()-5
    if not nebula and not eclipse:
        rail=QRectF(left,top,9,bottom-top);panel(rail)
        for index in range(5):
            p.setPen(QPen(QColor(pal['muted']),.9));p.drawLine(QPointF(left+3,top+6+index*7),QPointF(left+6,top+6+index*7))
        left+=13
    else:bottom-=8
    header=QRectF(left,top,right-left,17 if sculpt else 8);panel(header)
    if sculpt:
        # Same split hero as the actual design: chips beside its metal sculpture.
        for column in range(2):
            for row in range(2):panel(QRectF(left+3+column*(header.width()*.27),top+3+row*6,header.width()*.23,4))
        for offset,tone in ((-2,'#a94426'),(2,'#8b9698'),(0,'#eee9dd')):
            loop=QPainterPath();loop.addEllipse(QRectF(header.right()-22+offset,top+3,14,10))
            p.setPen(QPen(QColor(tone),1.5));p.setBrush(Qt.NoBrush);p.drawPath(loop)
    y=top+(21 if sculpt else 12);gap=3;count=4 if sculpt else 3;width=(right-left-(count-1)*gap)/count
    if eclipse:
        for index in range(6):panel(QRectF(left+index*(right-left)/6,top+9,(right-left)/6-2,3))
        y=top+15
    for index in range(count):
        box=QRectF(left+index*(width+gap),y,width,12 if sculpt else 16);panel(box)
        dial=QRectF(box.center().x()-4,box.center().y()-4,8,8)
        p.setPen(QPen(QColor(pal['accent'] if index!=1 else pal['secondary']),1));p.setBrush(Qt.NoBrush)
        if sculpt:p.drawLine(QPointF(box.left()+2,box.bottom()-3),QPointF(box.right()-2,box.bottom()-3))
        else:p.drawArc(dial,225*16,-220*16)
    plot_y=y+(16 if sculpt else 20)
    plot=QRectF(left,plot_y,right-left,max(8,bottom-plot_y));panel(plot)
    p.setBrush(Qt.NoBrush)
    for index,tone in enumerate((pal['accent'],pal['secondary'])):
        path=QPainterPath()
        for n,level in enumerate((.2,.5,.35,.8,.6,.9)):
            pt=QPointF(plot.left()+3+n*(plot.width()-6)/5,plot.bottom()-2-(plot.height()-4)*max(.05,level-index*.18))
            path.moveTo(pt) if n==0 else path.lineTo(pt)
        p.setPen(QPen(QColor(tone),.8));p.drawPath(path)
    if nebula:
        dock=QRectF(frame.center().x()-18,frame.bottom()-9,36,5);panel(dock)
        for index in range(6):
            p.setPen(QPen(QColor(pal['text']),1));x=dock.left()+4+index*5;p.drawPoint(QPointF(x,dock.center().y()))
    elif eclipse:
        panel(QRectF(frame.left()+5,frame.bottom()-7,frame.width()-10,3))
    p.restore()
    p.fillRect(QRectF(0,77,tile.width(),35),QColor(pal['bg']))
    font=QFont(tile.font());font.setPixelSize(11);font.setWeight(QFont.DemiBold)
    p.setFont(font);p.setPen(QColor(pal['text']));p.drawText(QRectF(12,79,tile.width()-24,25),Qt.AlignCenter,tile.text())
    p.restore()
    capabilities(p,tile,pal,tile._hover)
    finish(p,tile,pal)
