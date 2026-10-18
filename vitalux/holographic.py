"""Holographic HUD: independent opaque native Qt painting, no blur or glass.

Drawing is cached at the scene level. Widget surfaces only draw inexpensive
solid polygons, technical corner accents, and readable telemetry framing.
All geometry derives from actual widget bounds: no fixed image assets.
"""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap


def color(value, alpha=255):
    c = QColor(value)
    c.setAlpha(alpha)
    return c


def _cut_path(rect, amount=9):
    r = QRectF(rect)
    d = min(float(amount), r.width() / 6, r.height() / 4)
    path = QPainterPath()
    path.moveTo(r.left()+d, r.top())
    path.lineTo(r.right()-d, r.top())
    path.lineTo(r.right(), r.top()+d)
    path.lineTo(r.right(), r.bottom()-d)
    path.lineTo(r.right()-d, r.bottom())
    path.lineTo(r.left()+d, r.bottom())
    path.lineTo(r.left(), r.bottom()-d)
    path.lineTo(r.left(), r.top()+d)
    path.closeSubpath()
    return path


def scene_pixmap(size, accent):
    """Opaque, crisp background shared by software, OpenGL and Qt Quick."""
    px = QPixmap(max(1, size.width()), max(1, size.height()))
    px.fill(QColor("#030b13"))
    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing, True)
    paint_scene(painter, QRectF(px.rect()), accent)
    painter.end()
    return px


def paint_scene(p, rect, accent):
    w, h = rect.width(), rect.height()
    if w < 2 or h < 2:
        return
    background = QLinearGradient(0, 0, w, h)
    background.setColorAt(0, QColor("#030912"))
    background.setColorAt(.52, QColor("#051523"))
    background.setColorAt(1, QColor("#020811"))
    p.fillRect(rect, background)
    # Two independent dot-and-wire grids. They remain below the opaque tiles.
    p.setPen(QPen(color(accent, 20), .7))
    for x in range(0, int(w)+1, 48):
        p.drawLine(QPointF(x, 0), QPointF(x, h))
    for y in range(0, int(h)+1, 48):
        p.drawLine(QPointF(0, y), QPointF(w, y))
    p.setPen(QPen(color(accent, 33), 1))
    for x in range(0, int(w)+1, 144):
        for y in range(0, int(h)+1, 144):
            p.drawPoint(QPointF(x, y))
    # Offset circuitry: precision traces rather than a glass highlight.
    p.setPen(QPen(color(accent, 72), 1.1))
    for row in range(5):
        y = 45 + row * 102
        if y >= h-25:
            break
        start = max(260.0, w*.56 + row*14)
        p.drawLine(QPointF(start,y), QPointF(min(w-26,start+56),y))
        p.drawLine(QPointF(min(w-26,start+56),y), QPointF(min(w-12,start+76),y+15))
        p.setBrush(color(accent, 145))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(min(w-12,start+76),y+15), 1.9, 1.9)
        p.setPen(QPen(color(accent, 72), 1.1))
    # Thin segmented edges frame the window, not the entire desktop.
    p.setPen(QPen(color(accent, 115), 1))
    for x in range(12, int(w)-12, 116):
        p.drawLine(QPointF(x, 9), QPointF(min(x+43,w-12), 9))
        p.drawLine(QPointF(x, h-10), QPointF(min(x+31,w-12),h-10))
    p.setPen(QPen(color(accent, 82), 1))
    p.drawLine(QPointF(w-10, 17), QPointF(w-10, h-17))


def paint_panel(p, rect, accent, *, strong=False, compact=False, active=False):
    """Cut-corner matte chassis with layered luminous circuit borders."""
    r = QRectF(rect)
    if r.width() < 12 or r.height() < 12:
        return
    cut = 6 if compact else 12 if strong else 9
    path = _cut_path(r, cut)
    # The interior is strictly opaque, deliberately not a frosted glass effect.
    p.fillPath(path, QColor("#0a1b2b" if strong else "#081725" if compact else "#091826"))
    core = color(accent, 125 if active else 83)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color(accent, 27 if not active else 52), 4.5))
    p.drawPath(path)
    p.setPen(QPen(core, 1.1 if active else .9))
    p.drawPath(path)
    x, y, right, bottom = r.left(), r.top(), r.right(), r.bottom()
    short = min(31, max(12, r.width()*.15))
    # Bright cut corners and carefully separated perimeter segments.
    p.setPen(QPen(color(accent, 238 if active else 188), 1.6))
    p.drawLine(QPointF(x+cut, y), QPointF(x+cut+short,y))
    p.drawLine(QPointF(right-cut-short, bottom), QPointF(right-cut, bottom))
    p.drawLine(QPointF(x, bottom-cut-short*.7), QPointF(x, bottom-cut))
    p.drawLine(QPointF(right, y+cut), QPointF(right, y+cut+short*.65))
    p.setPen(QPen(color("#b6faff", 66 if strong else 39), .8))
    p.drawLine(QPointF(x+cut+6,y+6), QPointF(min(right-cut-9,x+cut+85),y+6))
    # Functional-looking mini telemetry notches, hidden on tiny cards.
    if r.width() > 130 and r.height() > 72:
        p.setPen(QPen(color(accent, 102), 1))
        for k in range(5):
            xx = right-cut-33+k*5
            p.drawLine(QPointF(xx, y+8), QPointF(xx, y+10+(k%2)*3))
        p.setPen(Qt.NoPen)
        p.setBrush(color(accent, 180 if active else 94))
        p.drawEllipse(QPointF(right-cut-8,bottom-9), 1.7, 1.7)


def paint_sidebar(p, rect, accent):
    r = QRectF(rect)
    bg = QLinearGradient(r.topLeft(), r.bottomRight())
    bg.setColorAt(0, QColor("#030c16"))
    bg.setColorAt(1, QColor("#091b29"))
    p.fillRect(r, bg)
    x = r.right()-1.5
    p.setPen(QPen(color(accent, 39), 5.0))
    p.drawLine(QPointF(x,0), QPointF(x,r.bottom()))
    p.setPen(QPen(color(accent, 181), 1.15))
    p.drawLine(QPointF(x,0), QPointF(x,r.bottom()))
    p.setPen(QPen(color(accent, 86), 1))
    for y in range(24, int(r.height())-14, 38):
        p.drawLine(QPointF(x-7,y), QPointF(x-3,y))
    p.setPen(QPen(color(accent, 84), 1))
    p.drawLine(QPointF(14,14), QPointF(57,14))
    p.drawLine(QPointF(14,14), QPointF(14,31))


def paint_nav(p, rect, accent, selected=False, hovered=False):
    r = QRectF(rect)
    if not (selected or hovered):
        return
    path = _cut_path(r, 5)
    p.fillPath(path, QColor("#103046" if selected else "#0b2537"))
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color(accent, 190 if selected else 105), 1.05))
    p.drawPath(path)
    p.setPen(QPen(color(accent, 225 if selected else 116), 2.2))
    p.drawLine(QPointF(r.left()+2,r.top()+9), QPointF(r.left()+2,r.bottom()-9))
    p.setPen(QPen(color(accent, 105), 1))
    p.drawLine(QPointF(r.right()-29, r.top()+7), QPointF(r.right()-11, r.top()+7))


def paint_chart_frame(p, rect, accent):
    r = QRectF(rect)
    p.fillPath(_cut_path(r, 7), QColor("#061725"))
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color(accent, 94), 1))
    p.drawPath(_cut_path(r, 7))
    p.setPen(QPen(color(accent, 183), 1.4))
    p.drawLine(QPointF(r.left()+7,r.top()), QPointF(min(r.right()-8,r.left()+49),r.top()))
    p.drawLine(QPointF(r.right()-32,r.bottom()), QPointF(r.right()-7,r.bottom()))


def paint_chart_grid(p, rect, accent):
    r = QRectF(rect)
    p.setPen(QPen(color(accent, 30), .75))
    for i in range(1, 13):
        x = r.left()+r.width()*i/13
        p.drawLine(QPointF(x,r.top()), QPointF(x,r.bottom()))
    p.setPen(QPen(color(accent, 65), 1))
    for x in (r.left(),r.right()):
        for y in (r.top(),r.bottom()):
            p.drawLine(QPointF(x-3,y), QPointF(x+3,y))
            p.drawLine(QPointF(x,y-3), QPointF(x,y+3))


def paint_gauge_ticks(p, rect, accent):
    """Small radial instrument markings outside the data arc."""
    r = QRectF(rect)
    center = r.center()
    radius = r.width()*.5 + 6
    p.setBrush(Qt.NoBrush)
    for index in range(17):
        angle = math.radians(-135 + index * 270/16)
        x, y = math.cos(angle), math.sin(angle)
        p.setPen(QPen(color(accent, 135 if index%4==0 else 55), 1.05))
        p.drawLine(QPointF(center.x()+x*(radius-3),center.y()+y*(radius-3)),
                   QPointF(center.x()+x*(radius+(3 if index%4==0 else 1)),
                           center.y()+y*(radius+(3 if index%4==0 else 1))))
