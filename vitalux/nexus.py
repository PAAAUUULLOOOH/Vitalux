"""Dark technical materials around a depth-layered Vitalux emblem."""
from math import cos,sin,pi
from PySide6.QtCore import QPointF,QRectF,Qt
from PySide6.QtGui import QColor,QFont,QLinearGradient,QPainter,QPainterPath,QPen,QPixmap,QRadialGradient
from PySide6.QtWidgets import QWidget,QSizePolicy

KEY='nexus'
PALETTE=dict(title='Nexus',subtitle='TACTICAL / DEPTH',bg='#060e0a',sidebar='#08140e',
    card='#0d1c14',border='#38522d',track='#283b27',grid='#213022',text='#eef6e6',muted='#a9baa0',
    accent='#c1e75b',secondary='#6fd7ac',light='#779b30',bloom='#254c33',shadow='#030906',
    series=('#c1e75b','#6fd7ac','#e8cf7a','#a4b6dd'))


def shape(rect,compact=False):
    cut=min(6 if compact else 14,rect.width()/5,rect.height()/4)
    path=QPainterPath(rect.topLeft()+QPointF(cut,0))
    for point in (rect.topRight(),rect.bottomRight()-QPointF(0,cut),
                  rect.bottomRight()-QPointF(cut,0),rect.bottomLeft(),rect.topLeft()+QPointF(0,cut)):
        path.lineTo(point)
    path.closeSubpath();return path


def paint_panel(p,widget,rect,*,strong=False,compact=False,active=False):
    from . import theme
    from .glass import draw_frosted_backdrop
    path=shape(rect,compact);p.save();p.setClipPath(path)
    p.fillPath(path,QColor(PALETTE['bg']))
    draw_frosted_backdrop(p,widget,rect,.70)
    wash=QLinearGradient(rect.topLeft(),rect.bottomLeft())
    wash.setColorAt(0,QColor(10,25,16,196 if strong else 177))
    wash.setColorAt(1,QColor(4,14,10,221 if strong else 207));p.fillPath(path,wash)
    p.restore();p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(theme.accent() if active else PALETTE['border']),1.1 if active else .8));p.drawPath(path)
    edge=QColor(theme.accent());edge.setAlpha(135)
    p.setPen(QPen(edge,1.5));p.drawLine(rect.topLeft()+QPointF(18,1),rect.topLeft()+QPointF(min(82,rect.width()*.35),1))
    if not compact:
        p.setPen(QPen(QColor('#6c8846'),1));p.drawLine(rect.bottomRight()-QPointF(24,3),rect.bottomRight()-QPointF(14,3))


def scene_pixmap(size,phase=0.):
    image=QPixmap(size);image.fill(QColor(PALETTE['bg']))
    p=QPainter(image);p.setRenderHint(QPainter.Antialiasing)
    center=QPointF(size.width()*.63,size.height()*.43);radius=min(size.width()*.31,size.height()*.34)
    glow=QRadialGradient(center,radius*2.)
    glow.setColorAt(0,QColor('#18341c'));glow.setColorAt(1,QColor(PALETTE['bg']));p.fillRect(image.rect(),glow)
    p.setPen(QPen(QColor(105,147,65,18),.7))
    for row in range(-1,size.height()//33+2):
        for column in range(-1,size.width()//38+2):
            x=column*38+(19 if row%2 else 0);y=row*33
            path=QPainterPath(QPointF(x+19,y))
            for n in range(1,7):path.lineTo(QPointF(x+19*cos(n*pi/3),y+19*sin(n*pi/3)))
            p.drawPath(path)
    p.setBrush(Qt.NoBrush)
    circle=QRectF(center.x()-radius,center.y()-radius,radius*2,radius*2)
    for offset,tone,width in ((QPointF(4,8),'#020704',10),(QPointF(0,0),'#455a37',9),(QPointF(-1,-1),'#9bad72',1.5)):
        p.setPen(QPen(QColor(tone),width,Qt.SolidLine,Qt.RoundCap))
        for start,span in ((8,141),(158,145),(313,37)):p.drawArc(circle.translated(offset),start*16,span*16)
    from .nexus_geometry import PULSE
    path=QPainterPath()
    for n,(x,y) in enumerate(PULSE):
        point=center+QPointF((x-628)/500*radius,(y-628)/500*radius)
        path.moveTo(point) if n==0 else path.lineTo(point)
    p.setPen(QPen(QColor('#020704'),radius*.067,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));p.drawPath(path.translated(3,5))
    p.setPen(QPen(QColor('#87a643'),radius*.055,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));p.drawPath(path)
    p.setPen(QPen(QColor('#c7e78c'),radius*.012,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));p.drawPath(path.translated(-1,-1))
    p.end();return image


def stylesheet():
    from . import theme
    accent=theme.accent()
    return '''
    QLabel#cardTitle {font-size:11px;font-weight:650;letter-spacing:1.5px;color:#c1e75b;}
    QLineEdit,QComboBox,QSpinBox,QTextEdit,QListWidget,QTableWidget {
        background:rgba(5,17,10,225);color:#eef6e6;border:1px solid #405a31;border-radius:4px;}
    QHeaderView::section {background:#122315;color:#c1e75b;border:none;padding:8px;}
    QPushButton#ghostBtn,QPushButton#langBtn,QToolButton#layoutAction {
        background:rgba(12,28,15,220);color:#e5efd9;border:1px solid #496338;border-radius:4px;}
    QPushButton#primaryBtn,QPushButton#langBtn:checked {
        background:#b4d953;color:#10200b;border:1px solid #dcf7a5;border-radius:4px;}
    QPushButton#ghostBtn:hover {background:#233922;border-color:#c1e75b;}
    QScrollBar::handle:vertical {background:#6e8d42;border-radius:3px;}
    QProgressBar {background:#142513;border:1px solid #3c5530;border-radius:3px;}
    QProgressBar::chunk {background:#b4d953;border-radius:2px;}
    '''.replace('#c1e75b',accent).replace('#b4d953',accent).replace('#dcf7a5',QColor(accent).lighter(130).name())


def paint_navigation(button):
    from . import theme
    from .nav_icons import paint_icon
    from .i18n import tr
    p=QPainter(button);p.setRenderHint(QPainter.Antialiasing)
    rect=QRectF(button.rect()).adjusted(2,3,-2,-3);path=shape(rect,True)
    if button.isChecked():
        p.fillPath(path,QColor(109,151,45,53));p.setPen(QPen(QColor(theme.accent()),.8));p.setBrush(Qt.NoBrush);p.drawPath(path)
        p.fillRect(QRectF(rect.left()+1,rect.top()+7,2,rect.height()-14),QColor(theme.accent()))
    elif button._hover_amount>.01:p.fillPath(path,QColor(105,145,62,24))
    button.paint_update_background(p,rect,path)
    ink=QColor(theme.accent() if button.isChecked() else PALETTE['text'])
    paint_icon(p,button.icon_key,QRectF(13,rect.center().y()-9,18,18),ink)
    font=QFont(button.font());font.setPixelSize(12);font.setWeight(QFont.DemiBold if button.isChecked() else QFont.Normal)
    p.setFont(font);p.setPen(ink)
    caption=tr(getattr(button,'_full_text',button.text()).split('    ',1)[-1])
    p.drawText(rect.adjusted(41,0,-8,0),Qt.AlignLeft|Qt.AlignVCenter,
               p.fontMetrics().elidedText(caption,Qt.ElideRight,max(1,round(rect.width()-49))))
    button.paint_notice_and_focus(p,rect,path);p.end()


def paint_metric(widget,p):
    from . import theme
    center=QPointF(widget.width()/2,widget.height()/2-5);radius=min(widget.width(),widget.height())*.39
    path=QPainterPath(center+QPointF(0,-radius))
    for n in range(1,7):path.lineTo(center+QPointF(radius*sin(n*pi/3),-radius*cos(n*pi/3)))
    p.setBrush(Qt.NoBrush);p.setPen(QPen(QColor('#30462a'),4));p.drawPath(path)
    value=widget._display_value
    if value is not None:
        active=QPainterPath();active.moveTo(path.pointAtPercent(0))
        for n in range(1,max(2,round(min(100,max(0,value))*2))+1):
            active.lineTo(path.pointAtPercent(min(1.,n/200)))
        p.setPen(QPen(QColor(theme.accent()),3,Qt.SolidLine,Qt.RoundCap));p.drawPath(active)
    font=QFont(widget.font());font.setPixelSize(38);font.setWeight(QFont.Light)
    p.setFont(font);p.setPen(QColor(theme.TEXT))
    shown='–' if value is None else f'{value:.0f}'+('' if widget.kind=='health' else '%')
    p.drawText(QRectF(center.x()-radius,center.y()-30,radius*2,60),Qt.AlignCenter,shown)


class Mark(QWidget):
    def __init__(self,parent=None):super().__init__(parent);self.setFixedSize(180,65)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        font=QFont(self.font());font.setPixelSize(23);font.setWeight(QFont.Light);font.setLetterSpacing(QFont.AbsoluteSpacing,3)
        p.setFont(font);p.setPen(QColor(PALETTE['text']));p.drawText(QRectF(0,7,180,36),Qt.AlignCenter,'VITALUX')
        p.setPen(QPen(QColor(PALETTE['accent']),1.2));p.drawLine(QPointF(19,52),QPointF(161,52));p.end()


def configure_shell(window,shell):
    from . import theme
    if theme.mode()!=KEY:
        if hasattr(shell,'nexus_mark'):shell.nexus_mark.hide()
        return
    if not hasattr(shell,'nexus_mark'):
        shell.nexus_mark=Mark(window.sidebar_brand)
        window.sidebar_brand.layout().insertWidget(0,shell.nexus_mark,0,Qt.AlignHCenter)
    shell.nexus_mark.show();window.sidebar_brand.show()
    window.sidebar_brand.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Fixed)
    window.pulse_core.hide();window.brand_mark.hide();window._brand_gap.setFixedHeight(12);window._brand_gap.show()
    window.sidebar.show();window.sidebar.setFixedWidth(224);window.sidebar_layout.setContentsMargins(12,15,12,14)
    window.sidebar_version.show();window.lang_host.show();window.collapse_button.hide()
    shell.header.hide();shell.footer.hide();shell.dock_row.hide()
    for index,button in enumerate(window.nav_buttons):
        window.nav_host.layout().insertWidget(index,button);button.setMinimumHeight(40)


def activate(page):
    from . import design_catalog,eco,motion
    if eco.enabled():return
    before=page.window.grab() if motion.enabled() and page.window.isVisible() else None
    if design_catalog.switch(KEY):
        page.window.apply_appearance(before=before);page.refresh_appearance()
