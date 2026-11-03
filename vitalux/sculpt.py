"""A machined ceramic/titanium interface and optional authored 3D studio."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget, QSizePolicy

KEY='sculpt'
PALETTE=dict(title='Sculpt',subtitle='CERAMIC / TITANIUM',bg='#e6e1d7',sidebar='#24282b',
    card='#f5f2eb',border='#beb7a9',track='#d3ccc0',grid='#d8d1c6',text='#24292c',muted='#626963',
    accent='#a94426',secondary='#316b78',light='#efded1',bloom='#c3bbb0',shadow='#c8c0b2',
    series=('#a94426','#316b78','#666f40','#7b5274'))


def shape(rect,compact=False):
    x,y,r,b=rect.left(),rect.top(),rect.right(),rect.bottom()
    radius=8 if compact else 18;cut=min(18 if compact else 32,rect.width()/5,rect.height()/4)
    p=QPainterPath(QPointF(x+radius,y));p.lineTo(r-cut,y)
    p.quadTo(r-cut+3,y,r-cut+5,y+3);p.lineTo(r-3,y+cut-5)
    p.quadTo(r,y+cut-3,r,y+cut);p.lineTo(r,b-radius)
    p.quadTo(r,b,r-radius,b);p.lineTo(x+radius,b)
    p.quadTo(x,b,x,b-radius);p.lineTo(x,y+radius);p.quadTo(x,y,x+radius,y)
    p.closeSubpath();return p


def paint_panel(p,widget,rect,*,strong=False,compact=False,active=False):
    from . import theme
    path=shape(rect,compact)
    sidebar=widget.objectName()=='sidebar'
    base='#252a2c' if sidebar else theme.CARD
    p.fillPath(shape(rect.translated(0,2),compact),QColor('#ada697'))
    fill=QLinearGradient(rect.topLeft(),rect.bottomRight())
    fill.setColorAt(0,QColor('#303638' if sidebar else '#fffdf7'))
    fill.setColorAt(1,QColor(base));p.fillPath(path,fill)
    p.setPen(QPen(QColor('#454b4a' if sidebar else '#b9b2a5'),1));p.setBrush(Qt.NoBrush);p.drawPath(path)
    inner=shape(rect.adjusted(2,2,-2,-2),compact)
    p.setPen(QPen(QColor('#363c3e' if sidebar else '#ffffff'),1));p.drawPath(inner)
    # Recessed seam follows the authored cut, rather than a glass rim.
    p.setPen(QPen(QColor('#6f7774' if sidebar else '#d2cabc'),1.4))
    p.drawLine(QPointF(rect.right()-30,rect.top()+8),QPointF(rect.right()-8,rect.top()+30))
    if active:
        p.setPen(QPen(QColor(theme.accent()),2));p.drawPath(path)


def scene_pixmap(size,phase=0.):
    image=QPixmap(size);image.fill(QColor(PALETTE['bg']))
    p=QPainter(image)
    gradient=QLinearGradient(0,0,size.width(),size.height())
    for t,c in ((0,'#f4f0e8'),(.45,'#e8e2d7'),(1,'#c7c0b4')):gradient.setColorAt(t,QColor(c))
    p.fillRect(image.rect(),gradient)
    p.setPen(QPen(QColor('#d4cec2'),1))
    for i in range(9):
        x=size.width()*.3+i*70
        p.drawLine(QPointF(x,0),QPointF(x-size.height()*.22,size.height()))
    p.end();return image


def stylesheet():
    from . import theme
    accent=theme.accent()
    border='#80321e' if accent==PALETTE['accent'] else QColor(accent).darker(130).name()
    return '''
    QLabel#heroTitle {font-size:22px;font-weight:650;}
    QLabel#cardTitle {font-size:10px;font-weight:750;letter-spacing:1.5px;}
    QLabel#chipTitle {font-size:9px;letter-spacing:1px;}
    QLabel#chipValue {font-size:12px;font-weight:650;}
    QLineEdit,QComboBox,QSpinBox,QTextEdit,QListWidget,QTableWidget {
        background:#f9f6ef;color:#24292c;border:1px solid #bcb4a6;border-radius:6px;}
    QHeaderView::section {background:#e6e0d5;color:#333a3b;border:none;padding:8px;}
    QPushButton#ghostBtn,QPushButton#langBtn,QToolButton#layoutAction {
        background:#ece7dd;color:#24292c;border:1px solid #aaa294;border-radius:6px;}
    QPushButton#primaryBtn,QPushButton#langBtn:checked {
        background:#a94426;color:#fff9f0;border:1px solid #80321e;border-radius:6px;}
    QPushButton#ghostBtn:hover {background:#fffdf8;border-color:#a94426;}
    QScrollBar::handle:vertical {background:#8d8c80;border-radius:3px;}
    QProgressBar {background:#d7cfc1;border:1px solid #aaa394;border-radius:5px;}
    QProgressBar::chunk {background:#a94426;border-radius:4px;}
    '''.replace('#a94426',accent).replace('#80321e',border)


def paint_navigation(button):
    from . import theme
    from .nav_icons import paint_icon
    from .i18n import tr
    p=QPainter(button);p.setRenderHint(QPainter.Antialiasing)
    rect=QRectF(button.rect()).adjusted(2,3,-2,-3)
    selected=button.isChecked()
    if selected:
        g=QLinearGradient(rect.topLeft(),rect.bottomRight())
        g.setColorAt(0,QColor('#fffdf5'));g.setColorAt(1,QColor('#cfc8bb'))
        p.fillPath(shape(rect,True),g)
        p.setPen(QPen(QColor('#aaa291'),1));p.setBrush(Qt.NoBrush);p.drawPath(shape(rect,True))
    elif button._hover_amount>.01 or button.hasFocus():p.fillPath(shape(rect,True),QColor('#3d4445'))
    button.paint_update_background(p,rect,shape(rect,True))
    ink=QColor('#222a2c' if selected else '#ede8dd')
    paint_icon(p,button.icon_key,QRectF(11,rect.center().y()-9,18,18),ink)
    font=QFont(button.font());font.setPixelSize(11);font.setWeight(QFont.DemiBold if selected else QFont.Normal)
    p.setFont(font);p.setPen(ink)
    caption=tr(getattr(button,'_full_text',button.text()).split('    ',1)[-1])
    p.drawText(rect.adjusted(35,0,-8,0),Qt.AlignLeft|Qt.AlignVCenter,
               p.fontMetrics().elidedText(caption,Qt.ElideRight,max(1,round(rect.width()-43))))
    button.paint_notice_and_focus(p,rect,shape(rect.adjusted(1,1,-1,-1),True))
    p.end()


def paint_metric(widget,p):
    from . import theme
    r=QRectF(widget.rect()).adjusted(14,12,-14,-8)
    value=widget._display_value
    shown='–' if value is None else f'{value:.0f}'+('' if widget.kind=='health' else '%')
    font=QFont(widget.font());font.setPixelSize(45);font.setWeight(QFont.Light)
    p.setFont(font);p.setPen(QColor(theme.TEXT))
    p.drawText(r.adjusted(0,0,0,-55),Qt.AlignCenter,shown)
    track=QRectF(r.left(),r.bottom()-38,r.width(),16)
    p.fillPath(shape(track,True),QColor('#d0c8b9'))
    p.setPen(QPen(QColor('#b4ab9c'),1));p.setBrush(Qt.NoBrush);p.drawPath(shape(track,True))
    if value is not None:
        fill=QRectF(track);fill.setWidth(max(0.,track.width()*min(100,max(0,value))/100))
        gradient=QLinearGradient(track.topLeft(),track.bottomLeft())
        gradient.setColorAt(0,QColor('#e98c63'));gradient.setColorAt(1,QColor(theme.accent()))
        if fill.width()>1:p.fillPath(shape(fill,True),gradient)
    p.setPen(QPen(QColor('#b2a99a'),1))
    for i in range(11):
        x=track.left()+track.width()*i/10
        p.drawLine(QPointF(x,track.bottom()+5),QPointF(x,track.bottom()+10))


class Mark(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.setFixedSize(132,94)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        for points,color in (((QPointF(42,12),QPointF(57,12),QPointF(69,47),QPointF(58,56)),'#e6ddd0'),
                             ((QPointF(58,56),QPointF(69,47),QPointF(86,12),QPointF(72,12)),'#a94426')):
            path=QPainterPath(points[0])
            for point in points[1:]:path.lineTo(point)
            path.closeSubpath();p.fillPath(path,QColor(color))
        font=QFont(self.font());font.setPixelSize(14);font.setLetterSpacing(QFont.AbsoluteSpacing,2)
        p.setFont(font);p.setPen(QColor('#eee7db'));p.drawText(QRectF(0,64,132,25),Qt.AlignCenter,'VITALUX')
        p.end()


def configure_shell(window,shell):
    from . import theme
    enabled=theme.mode()==KEY
    if not enabled:
        if hasattr(shell,'sculpt_mark'):shell.sculpt_mark.hide()
        window.sidebar_brand.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
        return
    if not hasattr(shell,'sculpt_mark'):
        shell.sculpt_mark=Mark(window.sidebar_brand)
        window.sidebar_brand.layout().insertWidget(0,shell.sculpt_mark,0,Qt.AlignHCenter)
    shell.sculpt_mark.setVisible(enabled)
    window.sidebar.show();window.sidebar.setFixedWidth(158)
    window.sidebar_layout.setContentsMargins(9,21,9,14)
    window.sidebar_brand.show();window.pulse_core.hide();window.brand_mark.hide()
    window.sidebar_brand.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Fixed)
    window._brand_gap.setFixedHeight(7);window._brand_gap.show()
    window.sidebar_version.show();window.lang_host.show()
    window.collapse_button.hide();shell.header.hide();shell.footer.hide();shell.dock_row.hide()
    for index,button in enumerate(window.nav_buttons):
        window.nav_host.layout().insertWidget(index,button)
        button.setMinimumHeight(39)
