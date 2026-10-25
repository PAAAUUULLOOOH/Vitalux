"""Nebula Prism: prismatic deep-space glass with a floating bottom dock.

Everything is painted natively. The atmosphere is cached by the scene, panels
sample it through the shared frosted-backdrop path, and the instruments only
repaint on a sensor sample, so the design costs no continuous animation loop.
"""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QFont,
                           QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QRadialGradient)

KEY = 'nebula_prism'
PALETTE = dict(
    title='Nebula Prism', subtitle='PRISMATIC GLASS / DEEP SPACE',
    bg='#05060f', sidebar='#0a0c1d', card='#0f1227', border='#5560a8',
    track='#1c2040', grid='#252a55', text='#f5f7ff', muted='#a8b0d8',
    accent='#5ef0ff', secondary='#ff6ad5', light='#3a2bd6', bloom='#b03cff',
    shadow='#0b0a2b',
    series=('#5ef0ff', '#ff6ad5', '#a78bfa', '#ffd36a', '#7dffb0'))
# Spectral stops used for prismatic edges, beams and gauges.
SPECTRUM = ('#5ef0ff', '#8d7bff', '#ff6ad5', '#ffb86b')


def color(value, alpha=255):
    c = QColor(value)
    c.setAlpha(max(0, min(255, round(alpha))))
    return c


def shape(rect, compact=False):
    path = QPainterPath()
    radius = min(15 if compact else 27, rect.height() / 2, rect.width() / 2)
    path.addRoundedRect(rect, radius, radius)
    return path


def _spectrum(gradient, alpha=255, reverse=False):
    stops = SPECTRUM[::-1] if reverse else SPECTRUM
    for i, tone in enumerate(stops):
        gradient.setColorAt(i / (len(stops) - 1), color(tone, alpha))
    return gradient


# ---------------------------------------------------------------- atmosphere
def scene_pixmap(size):
    pal = PALETTE
    w, h = max(1, size.width()), max(1, size.height())
    pixmap = QPixmap(w, h)
    pixmap.fill(color(pal['bg']))
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    rect = QRectF(0, 0, w, h)
    base = QLinearGradient(0, 0, w, h)
    for t, tone in ((0, pal['shadow']), (.5, pal['bg']), (1, pal['sidebar'])):
        base.setColorAt(t, color(tone))
    p.fillRect(rect, base)

    # Mesh gradient: large soft light fields in indigo, violet, cyan, magenta.
    for x, y, radius, tone, alpha in ((.06, .02, .66, '#3a2bd6', 150),
                                      (.95, .10, .58, '#b03cff', 118),
                                      (.80, .98, .70, '#0b9fd8', 92),
                                      (.04, .92, .52, '#ff3fb4', 66),
                                      (.52, .46, .46, '#1b2a96', 58)):
        glow = QRadialGradient(QPointF(w * x, h * y), max(w, h) * radius)
        glow.setColorAt(0, color(tone, alpha))
        glow.setColorAt(.5, color(tone, alpha * .30))
        glow.setColorAt(1, color(tone, 0))
        p.fillRect(rect, glow)

    # Prism beams: additive spectral bands refracting from the upper right.
    p.setCompositionMode(QPainter.CompositionMode_Plus)
    for offset, width, alpha in ((.10, .060, 30), (.30, .030, 24),
                                 (.58, .090, 18), (.82, .020, 34)):
        x0 = w * (offset + .35)
        band = QPainterPath(QPointF(x0, -h * .05))
        band.lineTo(x0 + w * width, -h * .05)
        band.lineTo(x0 + w * width - w * .85, h * 1.05)
        band.lineTo(x0 - w * .85, h * 1.05)
        band.closeSubpath()
        gradient = QLinearGradient(x0 - w * .1, 0, x0 + w * (width + .1), 0)
        gradient.setColorAt(0, color(SPECTRUM[0], 0))
        gradient.setColorAt(.25, color(SPECTRUM[0], alpha))
        gradient.setColorAt(.5, color(SPECTRUM[1], alpha))
        gradient.setColorAt(.75, color(SPECTRUM[2], alpha))
        gradient.setColorAt(1, color(SPECTRUM[3], 0))
        p.fillPath(band, gradient)
    p.setCompositionMode(QPainter.CompositionMode_SourceOver)

    # Orbit rings around a distant light source.
    centre = QPointF(w * .86, -h * .06)
    for i in range(1, 8):
        ring = QRadialGradient(centre, w * .09 * i + 1)
        ring.setColorAt(0, color(pal['accent'], 0))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(color(SPECTRUM[i % 3], max(4, 26 - i * 3)), .8))
        p.drawEllipse(centre, w * .09 * i, w * .09 * i)

    # Fine dot lattice and deterministic stars (no randomness, stable caches).
    p.setPen(Qt.NoPen)
    p.setBrush(color(pal['text'], 11))
    for gy in range(18, h, 34):
        for gx in range(18, w, 34):
            p.drawEllipse(QPointF(gx, gy), .8, .8)
    seed = 7919
    for i in range(110):
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        x = (seed % 10000) / 10000 * w
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        y = (seed % 10000) / 10000 * h
        size_ = .5 + (i % 5) * .22
        tone = SPECTRUM[i % 4] if i % 7 == 0 else pal['text']
        p.setBrush(color(tone, 50 + (i * 37) % 120))
        p.drawEllipse(QPointF(x, y), size_, size_)
        if i % 17 == 0:
            p.setPen(QPen(color(tone, 70), .6))
            p.drawLine(QPointF(x - 4, y), QPointF(x + 4, y))
            p.drawLine(QPointF(x, y - 4), QPointF(x, y + 4))
            p.setPen(Qt.NoPen)

    vignette = QRadialGradient(QPointF(w * .5, h * .38), max(w, h) * .88)
    vignette.setColorAt(0, QColor(0, 0, 0, 0))
    vignette.setColorAt(.62, QColor(0, 0, 4, 22))
    vignette.setColorAt(1, QColor(0, 0, 6, 170))
    p.fillRect(rect, vignette)
    p.end()
    return pixmap


# -------------------------------------------------------------------- panels
def paint_panel(p, widget, rect, *, strong=False, compact=False, active=False):
    from .glass import draw_frosted_backdrop
    pal = PALETTE
    path = shape(rect, compact)
    p.save()
    p.setClipPath(path)
    p.fillPath(path, color(pal['card']))
    draw_frosted_backdrop(p, widget, rect, .66)
    wash = QLinearGradient(rect.topLeft(), rect.bottomRight())
    wash.setColorAt(0, color(pal['card'], 168))
    wash.setColorAt(.45, color(pal['bg'], 205))
    wash.setColorAt(1, color(pal['card'], 215))
    p.fillPath(path, wash)
    # Coloured depth: cyan from the lower right, magenta from the upper left.
    lower = QRadialGradient(rect.bottomRight(), max(40, rect.width() * .72))
    lower.setColorAt(0, color(pal['accent'], 46 if strong else 28))
    lower.setColorAt(1, color(pal['accent'], 0))
    p.fillPath(path, lower)
    upper = QRadialGradient(rect.topLeft(), max(40, rect.width() * .55))
    upper.setColorAt(0, color(pal['secondary'], 34 if strong else 20))
    upper.setColorAt(1, color(pal['secondary'], 0))
    p.fillPath(path, upper)
    sheen = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    sheen.setColorAt(0, color(pal['text'], 30))
    sheen.setColorAt(.12, color(pal['text'], 5))
    sheen.setColorAt(1, color(pal['text'], 0))
    p.fillPath(path, sheen)
    if not compact and rect.height() > 90:
        # A specular streak on the upper edge, clear of any data.
        streak = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.top())
        streak.setColorAt(0, color(pal['text'], 0))
        streak.setColorAt(.22, color(pal['text'], 105 if strong else 70))
        streak.setColorAt(.5, color(pal['accent'], 36))
        streak.setColorAt(1, color(pal['text'], 0))
        p.setPen(QPen(streak, 1.2))
        p.drawLine(QPointF(rect.left() + 26, rect.top() + 1.4),
                   QPointF(rect.right() - 26, rect.top() + 1.4))
    p.restore()
    edge = QConicalGradient(rect.center(), 38)
    for t, tone, alpha in ((0, SPECTRUM[0], 175), (.22, SPECTRUM[1], 105),
                           (.42, pal['border'], 70), (.58, SPECTRUM[2], 135),
                           (.78, pal['border'], 60), (1, SPECTRUM[0], 175)):
        edge.setColorAt(t, color(tone, min(255, alpha + 55) if active else alpha))
    p.setBrush(Qt.NoBrush)
    if active:
        halo = QConicalGradient(rect.center(), 38)
        _spectrum(halo, 38)
        p.setPen(QPen(QBrush(halo), 6))
        p.drawPath(path)
    p.setPen(QPen(QBrush(edge), 1.6 if active else .9))
    p.drawPath(path)
    p.setPen(QPen(color(pal['text'], 14), .7))
    p.drawPath(shape(rect.adjusted(2, 2, -2, -2), compact))


# ------------------------------------------------------------------ dock nav
DOCK_BUTTON = (54, 46)


def paint_navigation(button):
    from .nav_icons import paint_icon
    pal = PALETTE
    p = QPainter(button)
    p.setRenderHint(QPainter.Antialiasing)
    rect = QRectF(button.rect()).adjusted(3, 3, -3, -3)
    selected = button.isChecked()
    path = shape(rect, True)
    if selected:
        fill = QLinearGradient(rect.topLeft(), rect.bottomRight())
        fill.setColorAt(0, color(SPECTRUM[0], 74))
        fill.setColorAt(.55, color(SPECTRUM[1], 70))
        fill.setColorAt(1, color(SPECTRUM[2], 82))
        p.fillPath(path, fill)
        glow = QRadialGradient(QPointF(rect.center().x(), rect.bottom() + 4), rect.width())
        glow.setColorAt(0, color(pal['accent'], 82))
        glow.setColorAt(1, color(pal['accent'], 0))
        p.save()
        p.setClipPath(path)
        p.fillRect(rect, glow)
        p.restore()
        edge = QLinearGradient(rect.topLeft(), rect.bottomRight())
        _spectrum(edge, 230)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QBrush(edge), 1.2))
        p.drawPath(path)
        p.setPen(Qt.NoPen)
        p.setBrush(color(pal['accent']))
        p.drawEllipse(QPointF(rect.center().x(), rect.bottom() - 4.5), 1.7, 1.7)
    elif button._hover_amount > .01 or button.hasFocus():
        p.fillPath(path, color(pal['accent'], 12 + 26 * button._hover_amount))
    ink = color(pal['text'] if selected else pal['muted'] if button._hover_amount < .3 else pal['text'])
    paint_icon(p, button.icon_key,
               QRectF(rect.center().x() - 10, rect.center().y() - 12, 22, 22), ink)
    if button.glow and button._update_version:
        p.setPen(QPen(color(pal['bg']), 1.4))
        p.setBrush(color(pal['secondary']))
        p.drawEllipse(QPointF(rect.right() - 9, rect.top() + 8), 4, 4)
    if button.hasFocus():
        p.setPen(QPen(color(pal['accent']), 1, Qt.DotLine))
        p.setBrush(Qt.NoBrush)
        p.drawPath(shape(rect.adjusted(2, 2, -2, -2), True))
    p.end()


# --------------------------------------------------------------- stylesheets
def stylesheet():
    pal = PALETTE
    return f'''
    #heroTitle {{font-size:20px;font-weight:650;color:{pal['text']};}}
    #pageTitle {{font-size:30px;font-weight:750;}}
    #cardTitle {{font-size:10px;font-weight:700;letter-spacing:1.5px;color:{pal['accent']};}}
    #chipValue {{font-size:11px;font-weight:650;color:{pal['text']};}}
    #chipTitle {{font-size:9px;color:{pal['muted']};}}
    QLineEdit,QComboBox,QSpinBox,QTextEdit,QListWidget,QTableWidget {{
        background:{pal['sidebar']};color:{pal['text']};border:1px solid {pal['border']};border-radius:12px;}}
    QHeaderView::section {{background:{pal['sidebar']};color:{pal['muted']};border:none;padding:8px;}}
    QTableWidget::item {{padding:6px;border-bottom:1px solid {pal['grid']};}}
    QTableWidget::item:selected {{background:{pal['track']};color:{pal['text']};}}
    QComboBox::drop-down {{border-radius:12px;background:{pal['card']};}}
    QPushButton#ghostBtn,QPushButton#langBtn,QToolButton#layoutAction {{
        border:1px solid {pal['border']};border-radius:12px;background:{pal['sidebar']};color:{pal['text']};}}
    QPushButton#ghostBtn:hover,QPushButton#langBtn:hover,QToolButton#layoutAction:hover {{
        border-color:{pal['accent']};background:{pal['track']};}}
    QPushButton#primaryBtn,QPushButton#langBtn:checked {{
        background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {SPECTRUM[0]},stop:.55 {SPECTRUM[1]},stop:1 {SPECTRUM[2]});
        border-radius:12px;border:1px solid {pal['accent']};color:#06071a;}}
    QProgressBar,QProgressBar::chunk {{border-radius:12px;}}
    QScrollBar::handle:vertical {{background:{pal['border']};border-radius:3px;}}
    '''


# ------------------------------------------------------------ design preview
def preview_contents(p, tile, pal, box, width):
    box(QRectF(5, 5, width - 10, 9))
    p.setPen(QPen(color(pal['text'], 190), 1))
    p.drawLine(11, 9, 31, 9)
    for x, w, h, y in ((5, (width - 14) * .46, 28, 17), (5 + (width - 14) * .49, (width - 14) * .24, 28, 17),
                       (5 + (width - 14) * .76, (width - 14) * .24, 28, 17)):
        box(QRectF(x, y, w, h))
    # Ring gauge and area chart miniatures.
    ring = QRectF(11, 22, 18, 18)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color(pal['track']), 2.2))
    p.drawArc(ring, 225 * 16, -270 * 16)
    gradient = QLinearGradient(ring.topLeft(), ring.bottomRight())
    _spectrum(gradient)
    p.setPen(QPen(QBrush(gradient), 2.2, Qt.SolidLine, Qt.RoundCap))
    p.drawArc(ring, 225 * 16, -190 * 16)
    path = QPainterPath(QPointF(36, 37))
    span = (width - 14) * .46 - 44
    for j, f in enumerate((.2, .5, .3, .7, .4, .55)):
        path.lineTo(36 + span * j / 5, 37 - f * 14)
    p.setPen(QPen(color(pal['accent'], 230), .9))
    p.drawPath(path)
    box(QRectF(5, 48, (width - 14) * .62, 12))
    box(QRectF(5 + (width - 14) * .65, 48, (width - 14) * .35, 12))
    # The floating dock, centred under the content.
    dock_w = min(width - 26, 86)
    dock = QRectF((width - dock_w) / 2, 63, dock_w, 10)
    box(dock, 235)
    for i in range(6):
        x = dock.left() + 9 + i * (dock_w - 18) / 5
        if i == 2:
            pill = QRectF(x - 5, dock.top() + 1.5, 10, 7)
            fill = QLinearGradient(pill.topLeft(), pill.bottomRight())
            _spectrum(fill, 210)
            p.setPen(Qt.NoPen)
            p.setBrush(fill)
            p.drawRoundedRect(pill, 3.5, 3.5)
        else:
            p.setPen(Qt.NoPen)
            p.setBrush(color(pal['muted'], 170))
            p.drawEllipse(QPointF(x, dock.center().y()), 1.4, 1.4)


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
    """Prismatic 270-degree gauge with graduated ticks and a luminous cap."""
    pal = PALETTE
    cx, cy = box.center().x(), box.center().y()
    outer = box.width() / 2
    thick = max(5.0, outer * .17)
    arc = box.adjusted(thick + 6, thick + 6, -thick - 6, -thick - 6)
    fraction = 0 if value is None else max(0, min(100, value)) / 100
    # Ticks sit outside the arc and light up with the reading.
    for i in range(41):
        a = math.radians(225 - 270 * i / 40)
        long_ = i % 5 == 0
        r1, r2 = outer - (4 if long_ else 2.2), outer
        lit = value is not None and i / 40 <= fraction + .0001
        p.setPen(QPen(color(SPECTRUM[min(3, int(3 * i / 40))] if lit else pal['grid'],
                            200 if lit else 150), 1.2 if long_ else .8))
        p.drawLine(QPointF(cx + math.cos(a) * r1, cy - math.sin(a) * r1),
                   QPointF(cx + math.cos(a) * r2, cy - math.sin(a) * r2))
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color(pal['track'], 235), thick, Qt.SolidLine, Qt.RoundCap))
    p.drawArc(arc, 225 * 16, -270 * 16)
    if value is None:
        return
    gradient = QConicalGradient(arc.center(), 225)
    # Conical stops run counter-clockwise; the arc runs clockwise.
    gradient.setColorAt(1, color(level_tone or SPECTRUM[0]))
    gradient.setColorAt(.8, color(level_tone or SPECTRUM[1]))
    gradient.setColorAt(.5, color(level_tone or SPECTRUM[2]))
    gradient.setColorAt(.25, color(level_tone or SPECTRUM[3]))
    gradient.setColorAt(0, color(level_tone or SPECTRUM[0]))
    span = round(-270 * 16 * fraction)
    for width, alpha in ((thick * 2.1, 34), (thick * 1.45, 62)):
        glow = QConicalGradient(arc.center(), 225)
        for stop, tone in ((1, SPECTRUM[0]), (.8, SPECTRUM[1]), (.5, SPECTRUM[2]), (.25, SPECTRUM[3]), (0, SPECTRUM[0])):
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
        halo.setColorAt(.35, color(level_tone or SPECTRUM[3], 120))
        halo.setColorAt(1, color(level_tone or SPECTRUM[3], 0))
        p.setPen(Qt.NoPen)
        p.setBrush(halo)
        p.drawEllipse(tip, thick * 1.15, thick * 1.15)
        p.setBrush(color('#ffffff'))
        p.drawEllipse(tip, thick * .26, thick * .26)


def _area_graph(p, rect, history):
    pal = PALETTE
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
    line.setColorAt(0, color(SPECTRUM[1]))
    line.setColorAt(.6, color(SPECTRUM[0]))
    line.setColorAt(1, color('#e9fdff'))
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
        fill.setColorAt(.6, color(SPECTRUM[1], 30))
        fill.setColorAt(1, color(SPECTRUM[1], 0))
        p.fillPath(area, fill)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(color(pal['accent'], 40), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(curve)
        p.setPen(QPen(QBrush(line), 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(curve)
        tip = points[-1]
        halo = QRadialGradient(tip, 9)
        halo.setColorAt(0, color('#ffffff', 210))
        halo.setColorAt(.3, color(pal['accent'], 110))
        halo.setColorAt(1, color(pal['accent'], 0))
        p.setPen(Qt.NoPen)
        p.setBrush(halo)
        p.drawEllipse(tip, 9, 9)


def paint_metric(metric, p):
    from .i18n import tr
    pal = PALETTE
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    rect = QRectF(metric.drawing_rect()).adjusted(5, 3, -5, -3)
    width = rect.width()
    font = QFont(metric.font())

    def text(area, value, size=12, tone=None, weight=QFont.Normal,
             align=Qt.AlignLeft | Qt.AlignVCenter, spacing=0):
        font.setPixelSize(size)
        font.setWeight(weight)
        font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
        p.setFont(font)
        p.setPen(color(tone or pal['text']))
        value = p.fontMetrics().elidedText(str(value), Qt.ElideRight, max(1, round(area.width())))
        p.drawText(area, align, value)

    text(QRectF(rect.left(), rect.top(), width, 22), tr(metric.title).upper(), 11,
         pal['accent'], QFont.Bold, spacing=1.6)
    value = metric._display_value
    kind = metric.kind
    shown = '–' if value is None else (f'{value:.0f}' if kind == 'health' else f'{value:.0f}')
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
    text(QRectF(start, inner.top(), number_w + 4, inner.height()), shown, size, weight=QFont.DemiBold)
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
