"""Quantum Core: reactor instruments over a cached, static circuitry image.

The native image is rendered at the actual pixel size without moving layers.
Logo animation and live instruments are independent of the background.
"""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QFont,
                           QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QRadialGradient)

KEY = 'quantum_core'
PALETTE = dict(
    title='Quantum Core', subtitle='LIVING HUD / REACTOR INTERFACE',
    bg='#020306', sidebar='#05070d', card='#070b16', border='#2fe6ff',
    track='#101729', grid='#1b2438', text='#eef6ff', muted='#8ea3c9',
    accent='#2fe6ff', secondary='#ff2bd6', light='#7afcff', bloom='#ff2bd6',
    shadow='#000103',
    series=('#2fe6ff', '#ff2bd6', '#ffb22f', '#7affa0', '#9b7bff'))
SPECTRUM = ('#2fe6ff', '#7a8bff', '#ff2bd6', '#ffb22f')
_BASE_CACHE = {}


def color(value, alpha=255):
    c = QColor(value)
    c.setAlpha(max(0, min(255, round(alpha))))
    return c



def shape(rect, compact=False):
    """A chamfered (cut-corner) HUD plate instead of a rounded rectangle."""
    path = QPainterPath()
    w, h = rect.width(), rect.height()
    cut = max(3.0, min(9 if compact else 15, w / 3, h / 3))
    x0, y0, x1, y1 = rect.left(), rect.top(), rect.right(), rect.bottom()
    path.moveTo(x0 + cut, y0)
    path.lineTo(x1 - cut, y0)
    path.lineTo(x1, y0 + cut)
    path.lineTo(x1, y1 - cut)
    path.lineTo(x1 - cut, y1)
    path.lineTo(x0 + cut, y1)
    path.lineTo(x0, y1 - cut)
    path.lineTo(x0, y0 + cut)
    path.closeSubpath()
    return path



# ---------------------------------------------------------------- atmosphere
def _base_layer(w, h):
    """The expensive, static circuitry/nebula base. Cached per size."""
    cached = _BASE_CACHE.get((w, h))
    if cached is not None:
        return cached
    pixmap = QPixmap(w, h)
    pixmap.fill(color(PALETTE['bg']))
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    rect = QRectF(0, 0, w, h)
    base = QLinearGradient(0, 0, 0, h)
    base.setColorAt(0, color(PALETTE['shadow']))
    base.setColorAt(.6, color(PALETTE['bg']))
    base.setColorAt(1, color('#04060f'))
    p.fillRect(rect, base)
    for x, y, radius, tone, alpha in ((.08, .88, .62, '#0a2a6e', 150),
                                      (.92, .08, .56, '#5e0a63', 120),
                                      (.5, .46, .80, '#031022', 72),
                                      (.2, .15, .40, '#073a52', 70)):
        glow = QRadialGradient(QPointF(w * x, h * y), max(w, h) * radius)
        glow.setColorAt(0, color(tone, alpha))
        glow.setColorAt(1, color(tone, 0))
        p.fillRect(rect, glow)
    # Circuit lattice: sparse grid plus deterministic diagonal traces.
    p.setPen(QPen(color(PALETTE['accent'], 14), 1))
    step = 48
    for gx in range(0, w, step):
        p.drawLine(gx, 0, gx, h)
    for gy in range(0, h, step):
        p.drawLine(0, gy, w, gy)
    seed = 90125
    p.setPen(QPen(color(PALETTE['accent'], 24), 1))
    for i in range(30):
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        x1_ = (seed % 10000) / 10000 * w
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        y1_ = (seed % 10000) / 10000 * h
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        length = 30 + seed % 90
        tone = SPECTRUM[i % 4]
        p.setPen(QPen(color(tone, 20), 1))
        p.drawLine(QPointF(x1_, y1_), QPointF(x1_ + length, y1_ - length * .35))
        if i % 6 == 0:
            p.setPen(Qt.NoPen)
            p.setBrush(color(tone, 90))
            p.drawEllipse(QPointF(x1_, y1_), 1.4, 1.4)
    seed = 5151
    for i in range(150):
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        x = (seed % 10000) / 10000 * w
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        y = (seed % 10000) / 10000 * h
        tone = SPECTRUM[i % 4] if i % 8 == 0 else PALETTE['text']
        p.setPen(Qt.NoPen)
        p.setBrush(color(tone, 40 + (i * 53) % 130))
        s = .5 + (i % 4) * .25
        p.drawEllipse(QPointF(x, y), s, s)
    vignette = QRadialGradient(QPointF(w * .5, h * .4), max(w, h) * .9)
    vignette.setColorAt(0, QColor(0, 0, 0, 0))
    vignette.setColorAt(.6, QColor(0, 0, 4, 28))
    vignette.setColorAt(1, QColor(0, 0, 4, 195))
    p.fillRect(rect, vignette)
    p.end()
    if len(_BASE_CACHE) > 4:
        _BASE_CACHE.clear()
    _BASE_CACHE[(w, h)] = pixmap
    return pixmap


def scene_pixmap(size):
    """Return the same sharp background image until the pixel size changes."""
    w, h = max(1, size.width()), max(1, size.height())
    return _base_layer(w, h)


# -------------------------------------------------------------------- panels
def paint_panel(p, widget, rect, *, strong=False, compact=False, active=False):
    from .glass import draw_frosted_backdrop
    pal = palette()
    path = shape(rect, compact)
    p.save()
    p.setClipPath(path)
    p.fillPath(path, color(pal['card']))
    draw_frosted_backdrop(p, widget, rect, .58)
    wash = QLinearGradient(rect.topLeft(), rect.bottomRight())
    wash.setColorAt(0, color(pal['card'], 182))
    wash.setColorAt(.5, color(pal['bg'], 212))
    wash.setColorAt(1, color(pal['card'], 228))
    p.fillPath(path, wash)
    glow1 = QRadialGradient(rect.topRight(), max(40, rect.width() * .72))
    glow1.setColorAt(0, color(pal['accent'], 42 if strong else 24))
    glow1.setColorAt(1, color(pal['accent'], 0))
    p.fillPath(path, glow1)
    glow2 = QRadialGradient(rect.bottomLeft(), max(40, rect.width() * .6))
    glow2.setColorAt(0, color(pal['secondary'], 32 if strong else 17))
    glow2.setColorAt(1, color(pal['secondary'], 0))
    p.fillPath(path, glow2)
    if not compact and rect.height() > 70:
        p.setPen(QPen(color(pal['text'], 6), 1))
        y = rect.top() + 9
        bottom = rect.bottom() - 6
        while y < bottom:
            p.drawLine(QPointF(rect.left() + 10, y), QPointF(rect.right() - 10, y))
            y += 5
    p.restore()
    edge = QLinearGradient(rect.topLeft(), rect.bottomRight())
    edge.setColorAt(0, color(palette()['series'][0], 225 if active else 150))
    edge.setColorAt(.5, color(palette()['series'][2], 185 if active else 108))
    edge.setColorAt(1, color(palette()['series'][3], 205 if active else 128))
    if active:
        p.setOpacity(.32)
        p.setPen(QPen(QBrush(edge), 5))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        p.setOpacity(1)
    p.setPen(QPen(QBrush(edge), 1.5 if active else .9))
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    if rect.width() > 42 and rect.height() > 30:
        bl = min(13, rect.width() * .16, rect.height() * .3)
        p.setPen(QPen(color(pal['accent'], 195 if active else 140), 1.4))
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            cx = rect.left() if dx > 0 else rect.right()
            cy = rect.top() if dy > 0 else rect.bottom()
            p.drawLine(QPointF(cx, cy), QPointF(cx + bl * dx, cy))
            p.drawLine(QPointF(cx, cy), QPointF(cx, cy + bl * dy))



# --------------------------------------------------------------- stylesheets
def stylesheet():
    pal = palette()
    return f'''
    #heroTitle {{font-size:20px;font-weight:650;color:{pal['text']};}}
    #pageTitle {{font-size:30px;font-weight:750;}}
    #cardTitle {{font-size:10px;font-weight:700;letter-spacing:1.8px;color:{pal['accent']};}}
    #chipValue {{font-size:11px;font-weight:650;color:{pal['text']};}}
    #chipTitle {{font-size:9px;color:{pal['muted']};}}
    QLineEdit,QComboBox,QSpinBox,QTextEdit,QListWidget,QTableWidget {{
        background:{pal['sidebar']};color:{pal['text']};border:1px solid {pal['border']};border-radius:6px;}}
    QHeaderView::section {{background:{pal['sidebar']};color:{pal['muted']};border:none;padding:8px;}}
    QTableWidget::item {{padding:6px;border-bottom:1px solid {pal['grid']};}}
    QTableWidget::item:selected {{background:{pal['track']};color:{pal['text']};}}
    QComboBox::drop-down {{border-radius:6px;background:{pal['card']};}}
    QPushButton#ghostBtn,QPushButton#langBtn,QToolButton#layoutAction {{
        border:1px solid {pal['border']};border-radius:6px;background:{pal['sidebar']};color:{pal['text']};}}
    QPushButton#ghostBtn:hover,QPushButton#langBtn:hover,QToolButton#layoutAction:hover {{
        border-color:{pal['accent']};background:{pal['track']};}}
    QPushButton#primaryBtn,QPushButton#langBtn:checked {{
        background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {palette()['series'][0]},stop:.6 {palette()['series'][2]},stop:1 {palette()['series'][3]});
        border-radius:6px;border:1px solid {pal['accent']};color:#02040a;}}
    QProgressBar,QProgressBar::chunk {{border-radius:6px;}}
    QScrollBar::handle:vertical {{background:{pal['border']};border-radius:3px;}}
    '''



# --------------------------------------------------------------- instruments
def _smooth(points):
    path = QPainterPath(points[0])
    if len(points) == 1:
        return path
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i else points[i]
        p1, p2 = points[i], points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        c1 = QPointF(p1.x() + (p2.x() - p0.x()) / 6, p1.y() + (p2.y() - p0.y()) / 6)
        c2 = QPointF(p2.x() - (p3.x() - p1.x()) / 6, p2.y() - (p3.y() - p1.y()) / 6)
        path.cubicTo(c1, c2, p2)
    return path



def _ring(p, box, value, *, level_tone=None):
    pal = palette()
    cx, cy = box.center().x(), box.center().y()
    outer = box.width() / 2
    thick = max(5.0, outer * .17)
    arc = box.adjusted(thick + 6, thick + 6, -thick - 6, -thick - 6)
    fraction = 0 if value is None else max(0, min(100, value)) / 100
    for i in range(41):
        a = math.radians(225 - 270 * i / 40)
        long_ = i % 5 == 0
        r1, r2 = outer - (4 if long_ else 2.2), outer
        lit = value is not None and i / 40 <= fraction + .0001
        p.setPen(QPen(color(palette()['series'][min(3, int(3 * i / 40))] if lit else pal['grid'],
                            205 if lit else 150), 1.2 if long_ else .8))
        p.drawLine(QPointF(cx + math.cos(a) * r1, cy - math.sin(a) * r1),
                   QPointF(cx + math.cos(a) * r2, cy - math.sin(a) * r2))
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color(pal['track'], 235), thick, Qt.SolidLine, Qt.RoundCap))
    p.drawArc(arc, 225 * 16, -270 * 16)
    if value is None:
        return
    gradient = QConicalGradient(arc.center(), 225)
    gradient.setColorAt(1, color(level_tone or palette()['series'][0]))
    gradient.setColorAt(.8, color(level_tone or palette()['series'][1]))
    gradient.setColorAt(.5, color(level_tone or palette()['series'][2]))
    gradient.setColorAt(.25, color(level_tone or palette()['series'][3]))
    gradient.setColorAt(0, color(level_tone or palette()['series'][0]))
    span = round(-270 * 16 * fraction)
    for width, alpha in ((thick * 2.1, 36), (thick * 1.45, 64)):
        glow = QConicalGradient(arc.center(), 225)
        for stop, tone in ((1, palette()['series'][0]), (.8, palette()['series'][1]), (.5, palette()['series'][2]), (.25, palette()['series'][3]), (0, palette()['series'][0])):
            glow.setColorAt(stop, color(level_tone or tone, alpha))
        p.setPen(QPen(QBrush(glow), width, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(arc, 225 * 16, span)
    p.setPen(QPen(QBrush(gradient), thick, Qt.SolidLine, Qt.RoundCap))
    p.drawArc(arc, 225 * 16, span)
    if fraction > .01:
        a = math.radians(225 - 270 * fraction)
        r = arc.width() / 2
        tip = QPointF(arc.center().x() + math.cos(a) * r, arc.center().y() - math.sin(a) * r)
        halo = QRadialGradient(tip, thick * 1.15)
        halo.setColorAt(0, color('#ffffff', 230))
        halo.setColorAt(.35, color(level_tone or palette()['series'][3], 120))
        halo.setColorAt(1, color(level_tone or palette()['series'][3], 0))
        p.setPen(Qt.NoPen)
        p.setBrush(halo)
        p.drawEllipse(tip, thick * 1.15, thick * 1.15)
        p.setBrush(color('#ffffff'))
        p.drawEllipse(tip, thick * .26, thick * .26)



def _area_graph(p, rect, history):
    pal = palette()
    if rect.width() < 12 or rect.height() < 12:
        return
    p.setBrush(Qt.NoBrush)
    for i in range(3):
        y = rect.top() + rect.height() * i / 2
        p.setPen(QPen(color(pal['grid'], 150), .6, Qt.DotLine))
        p.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
    n = len(history)
    runs, run = [], []
    for i, value in enumerate(history):
        if value is None or not math.isfinite(float(value)):
            if run:
                runs.append(run)
            run = []
            continue
        run.append(QPointF(rect.right() - (n - 1 - i) * rect.width() / max(59, n - 1),
                           rect.bottom() - max(0, min(100, value)) * rect.height() / 100))
    if run:
        runs.append(run)
    line = QLinearGradient(rect.left(), 0, rect.right(), 0)
    line.setColorAt(0, color(palette()['series'][2]))
    line.setColorAt(.6, color(palette()['series'][0]))
    line.setColorAt(1, color('#eafcff'))
    for points in runs:
        if len(points) == 1:
            p.setPen(Qt.NoPen)
            p.setBrush(color(pal['accent']))
            p.drawEllipse(points[0], 2.2, 2.2)
            continue
        curve = _smooth(points)
        area = QPainterPath(curve)
        area.lineTo(points[-1].x(), rect.bottom())
        area.lineTo(points[0].x(), rect.bottom())
        area.closeSubpath()
        fill = QLinearGradient(0, rect.top(), 0, rect.bottom())
        fill.setColorAt(0, color(pal['accent'], 96))
        fill.setColorAt(.6, color(palette()['series'][2], 28))
        fill.setColorAt(1, color(palette()['series'][2], 0))
        p.fillPath(area, fill)
        # Chromatic-aberration ghost strokes either side of the true line.
        for dx, tone, a in ((-.7, palette()['series'][0], 70), (.7, palette()['series'][2], 70)):
            ghost = curve.translated(dx, 0)
            p.setPen(QPen(color(tone, a), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(ghost)
        p.setPen(QPen(color(pal['accent'], 40), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(curve)
        p.setPen(QPen(QBrush(line), 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(curve)
        tip = points[-1]
        for i, (dx, dy, a) in enumerate(((-7, 2, 90), (-13, 5, 55), (-19, 7, 28))):
            p.setPen(Qt.NoPen)
            p.setBrush(color(pal['accent'], a))
            p.drawEllipse(QPointF(tip.x() + dx, tip.y() + dy), 2.0 - i * .4, 2.0 - i * .4)
        halo = QRadialGradient(tip, 9)
        halo.setColorAt(0, color('#ffffff', 215))
        halo.setColorAt(.3, color(pal['accent'], 115))
        halo.setColorAt(1, color(pal['accent'], 0))
        p.setPen(Qt.NoPen)
        p.setBrush(halo)
        p.drawEllipse(tip, 9, 9)



def paint_metric(metric, p):
    from .i18n import tr
    pal = palette()
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    rect = QRectF(metric.drawing_rect()).adjusted(5, 3, -5, -3)
    width = rect.width()
    font = QFont(metric.font())

    def text(area, value, size=12, tone=None, weight=QFont.Normal,
             align=Qt.AlignLeft | Qt.AlignVCenter, spacing=0, aberration=False):
        font.setPixelSize(size)
        font.setWeight(weight)
        font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
        p.setFont(font)
        shown = p.fontMetrics().elidedText(str(value), Qt.ElideRight, max(1, round(area.width())))
        if aberration:
            p.setPen(color(palette()['series'][0], 150))
            p.drawText(area.translated(-1, 0), align, shown)
            p.setPen(color(palette()['series'][2], 150))
            p.drawText(area.translated(1, 0), align, shown)
        p.setPen(color(tone or pal['text']))
        p.drawText(area, align, shown)

    text(QRectF(rect.left(), rect.top(), width, 22), tr(metric.title).upper(), 11,
         pal['accent'], QFont.Bold, spacing=1.8)
    value = metric._display_value
    kind = metric.kind
    shown = '–' if value is None else f'{value:.0f}'
    unit = '' if kind == 'health' or value is None else '%'
    level = None
    if value is not None and kind != 'health' and value >= 90:
        level = '#ff6a7d'
    elif value is not None and kind != 'health' and value >= 75:
        level = '#ffc46b'
    elif kind == 'health' and value is not None and value < 50:
        level = '#ff6a7d'
    top = rect.top() + (46 if kind == 'cpu' else 26)
    if kind == 'cpu':
        text(QRectF(rect.left(), rect.top() + 22, width, 20), metric.extra, 11, pal['muted'])
    bottom = rect.bottom() - 26
    available = max(40.0, bottom - top)
    wide = width > 330 and kind in ('cpu', 'gpu')
    diameter = min(available, 190.0, width * (.36 if wide else .92 if kind in ('cpu', 'gpu') else .80))
    diameter = max(64.0, diameter)
    side_by_side = wide or (kind in ('ram', 'disk', 'health') and width > 300)
    if side_by_side:
        ring_box = QRectF(rect.left() + 4, top + (available - diameter) / 2, diameter, diameter)
    else:
        ring_box = QRectF(rect.left() + (width - diameter) / 2, top + (available - diameter) / 2,
                          diameter, diameter)
    _ring(p, ring_box, value, level_tone=level)
    size = round(max(16, min(42, diameter * .24)))
    inner = QRectF(ring_box.left(), ring_box.top() + diameter * .27, diameter, diameter * .34)
    font.setPixelSize(size)
    font.setWeight(QFont.DemiBold)
    font.setLetterSpacing(QFont.AbsoluteSpacing, 0)
    p.setFont(font)
    number_w = p.fontMetrics().horizontalAdvance(shown)
    unit_size = max(10, round(size * .5))
    font.setPixelSize(unit_size)
    p.setFont(font)
    unit_w = p.fontMetrics().horizontalAdvance(unit) + 2 if unit else 0
    start = inner.center().x() - (number_w + unit_w) / 2
    text(QRectF(start, inner.top(), number_w + 4, inner.height()), shown, size,
         weight=QFont.DemiBold, aberration=True)
    if unit:
        text(QRectF(start + number_w + 2, inner.top() + size * .12, unit_w + 6, inner.height()), unit,
             unit_size, pal['muted'], QFont.DemiBold)
    if kind == 'health' and diameter > 80:
        text(QRectF(ring_box.left(), ring_box.top() + diameter * .58, diameter, 18), '/ 100', 11,
             pal['muted'], align=Qt.AlignCenter)
    if side_by_side:
        left = ring_box.right() + 18
        if kind in ('cpu', 'gpu'):
            _area_graph(p, QRectF(left, top + 6, rect.right() - left, max(30, available - 12)), metric.history)
        else:
            text(QRectF(left, top, rect.right() - left, available), tr(metric.detail), 15,
                 pal['text'], QFont.Medium, Qt.AlignLeft | Qt.AlignVCenter)
    text(QRectF(rect.left(), rect.bottom() - 24, width, 24), tr(metric.detail), 11, pal['muted'])



def palette():
    from . import theme
    return theme.palette_for(KEY)
