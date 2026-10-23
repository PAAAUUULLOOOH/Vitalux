"""Lumen Drift: warm, calm luxury glass with a floating pill nav and a
gently *breathing* backdrop.

Where Nebula Prism is cool prismatic glass and Quantum Core is an energetic
neon HUD, Lumen Drift is the quiet, premium register: soft pastel light,
generous rounding, a single slow ambient pulse instead of particles or
sweeps. The expensive backdrop (orbs, grain, vignette) is cached per pixel
size in ``_BASE_CACHE``; each animation tick only re-blends two of those
glows at a different opacity, which costs a fraction of a millisecond.
"""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap, QRadialGradient)

KEY = 'lumen_drift'
PALETTE = dict(
    title='Lumen Drift', subtitle='LIQUID LIGHT / QUIET LUXURY',
    bg='#0c0a10', sidebar='#120f17', card='#17131c', border='#5a4f6b',
    track='#241f2c', grid='#2c2634', text='#f7f1ea', muted='#b4a9bf',
    accent='#f3c98b', secondary='#c9a6ff', light='#ffe7cf', bloom='#eab0c9',
    shadow='#050409',
    series=('#f3c98b', '#c9a6ff', '#eab0c9', '#9fd8c9', '#ffd9a0'))
# Soft pastel quad: champagne gold -> rose -> lavender -> sage mint.
SPECTRUM = ('#f3c98b', '#eab0c9', '#c9a6ff', '#9fd8c9')
_BASE_CACHE = {}


def color(value, alpha=255):
    c = QColor(value)
    c.setAlpha(max(0, min(255, round(alpha))))
    return c


def shape(rect, compact=False):
    """A true pill for compact chrome (nav capsule, chips); a generous,
    softly rounded plate for everything else."""
    path = QPainterPath()
    if compact:
        r = rect.height() / 2
    else:
        r = min(30.0, rect.width() / 2, rect.height() / 2)
    path.addRoundedRect(rect, r, r)
    return path


# ---------------------------------------------------------------- atmosphere
def _base_layer(w, h):
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
    base.setColorAt(.55, color(PALETTE['bg']))
    base.setColorAt(1, color('#0f0c14'))
    p.fillRect(rect, base)
    # Large, very soft static pastel fields (the calm base layer).
    for x, y, radius, tone, alpha in ((.14, .12, .55, '#6b4f8f', 78),
                                      (.86, .20, .50, '#8f5f52', 66),
                                      (.78, .92, .58, '#4f6b64', 58),
                                      (.10, .90, .42, '#8f6f45', 50)):
        glow = QRadialGradient(QPointF(w * x, h * y), max(w, h) * radius)
        glow.setColorAt(0, color(tone, alpha))
        glow.setColorAt(1, color(tone, 0))
        p.fillRect(rect, glow)
    # Fine matte grain for a premium, non-flat surface (deterministic).
    seed = 61803
    p.setPen(Qt.NoPen)
    for i in range(260):
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        x = (seed % 10000) / 10000 * w
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        y = (seed % 10000) / 10000 * h
        tone = SPECTRUM[i % 4] if i % 11 == 0 else PALETTE['text']
        p.setBrush(color(tone, 8 + (i * 17) % 20))
        p.drawEllipse(QPointF(x, y), .5, .5)
    vignette = QRadialGradient(QPointF(w * .5, h * .42), max(w, h) * .92)
    vignette.setColorAt(0, QColor(0, 0, 0, 0))
    vignette.setColorAt(.65, QColor(4, 2, 8, 20))
    vignette.setColorAt(1, QColor(4, 2, 8, 150))
    p.fillRect(rect, vignette)
    p.end()
    if len(_BASE_CACHE) > 4:
        _BASE_CACHE.clear()
    _BASE_CACHE[(w, h)] = pixmap
    return pixmap


def scene_pixmap(size, phase=0.0):
    """Cached calm base, plus two glows that slowly breathe in and out."""
    w, h = max(1, size.width()), max(1, size.height())
    pixmap = _base_layer(w, h).copy()
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    rect = QRectF(0, 0, w, h)
    # A slow, gentle pulse (one full cycle roughly every 20 seconds).
    pulse = .5 + .5 * math.sin(phase * .35)
    for x, y, radius, tone, base_alpha in ((.30, .34, .40, SPECTRUM[0], 30),
                                           (.70, .62, .36, SPECTRUM[2], 26)):
        glow = QRadialGradient(QPointF(w * x, h * y), max(w, h) * radius)
        a = base_alpha * (.4 + .6 * pulse)
        glow.setColorAt(0, color(tone, a))
        glow.setColorAt(1, color(tone, 0))
        p.fillRect(rect, glow)
    # A single slow-drifting mote of light, barely perceptible.
    mx = w * (.5 + .22 * math.sin(phase * .22))
    my = h * (.5 + .16 * math.cos(phase * .18))
    drift = QRadialGradient(QPointF(mx, my), max(w, h) * .14)
    drift.setColorAt(0, color(PALETTE['light'], 20))
    drift.setColorAt(1, color(PALETTE['light'], 0))
    p.fillRect(rect, drift)
    p.end()
    return pixmap


# -------------------------------------------------------------------- panels
def paint_panel(p, widget, rect, *, strong=False, compact=False, active=False):
    from .glass import draw_frosted_backdrop
    pal = PALETTE
    path = shape(rect, compact)
    if not compact and rect.width() > 36 and rect.height() > 24:
        # A faked soft elevation shadow: three widening, fading passes.
        for grow, dy, alpha in ((3, 2, 34), (7, 5, 22), (13, 9, 12)):
            halo = shape(rect.adjusted(-grow, -grow + dy, grow, grow + dy), False)
            p.fillPath(halo, color('#000000', alpha))
    p.save()
    p.setClipPath(path)
    p.fillPath(path, color(pal['card']))
    draw_frosted_backdrop(p, widget, rect, .52)
    wash = QLinearGradient(rect.topLeft(), rect.bottomRight())
    wash.setColorAt(0, color(pal['card'], 150))
    wash.setColorAt(.6, color(pal['bg'], 190))
    wash.setColorAt(1, color(pal['card'], 205))
    p.fillPath(path, wash)
    glow1 = QRadialGradient(rect.bottomRight(), max(40, rect.width() * .85))
    glow1.setColorAt(0, color(pal['accent'], 30 if strong else 16))
    glow1.setColorAt(1, color(pal['accent'], 0))
    p.fillPath(path, glow1)
    glow2 = QRadialGradient(rect.topLeft(), max(40, rect.width() * .62))
    glow2.setColorAt(0, color(pal['secondary'], 24 if strong else 12))
    glow2.setColorAt(1, color(pal['secondary'], 0))
    p.fillPath(path, glow2)
    sheen = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + rect.height() * .45))
    sheen.setColorAt(0, color(pal['text'], 24))
    sheen.setColorAt(1, color(pal['text'], 0))
    p.fillPath(path, sheen)
    p.restore()
    p.setBrush(Qt.NoBrush)
    if active:
        p.setOpacity(.45)
        p.setPen(QPen(color(pal['accent'], 160), 3.4))
        p.drawPath(path)
        p.setOpacity(1)
    p.setPen(QPen(color(pal['border'], 150 if active else 80), 1.1 if active else .8))
    p.drawPath(path)
    if not compact:
        p.setPen(QPen(color(pal['text'], 16), .8))
        p.drawPath(shape(rect.adjusted(1.4, 1.4, -1.4, -1.4), False))


# --------------------------------------------------------------- stylesheets
def stylesheet():
    pal = PALETTE
    return f'''
    #heroTitle {{font-size:21px;font-weight:600;color:{pal['text']};}}
    #pageTitle {{font-size:30px;font-weight:650;}}
    #cardTitle {{font-size:10px;font-weight:650;letter-spacing:1.4px;color:{pal['accent']};}}
    #chipValue {{font-size:11px;font-weight:600;color:{pal['text']};}}
    #chipTitle {{font-size:9px;color:{pal['muted']};}}
    QLineEdit,QComboBox,QSpinBox,QTextEdit,QListWidget,QTableWidget {{
        background:{pal['sidebar']};color:{pal['text']};border:1px solid {pal['border']};border-radius:14px;}}
    QHeaderView::section {{background:{pal['sidebar']};color:{pal['muted']};border:none;padding:8px;}}
    QTableWidget::item {{padding:6px;border-bottom:1px solid {pal['grid']};}}
    QTableWidget::item:selected {{background:{pal['track']};color:{pal['text']};}}
    QComboBox::drop-down {{border-radius:14px;background:{pal['card']};}}
    QPushButton#ghostBtn,QPushButton#langBtn,QToolButton#layoutAction {{
        border:1px solid {pal['border']};border-radius:14px;background:{pal['sidebar']};color:{pal['text']};}}
    QPushButton#ghostBtn:hover,QPushButton#langBtn:hover,QToolButton#layoutAction:hover {{
        border-color:{pal['accent']};background:{pal['track']};}}
    QPushButton#primaryBtn,QPushButton#langBtn:checked {{
        background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {SPECTRUM[0]},stop:.6 {SPECTRUM[1]},stop:1 {SPECTRUM[2]});
        border-radius:14px;border:1px solid {pal['accent']};color:#1c1320;}}
    QProgressBar,QProgressBar::chunk,QGroupBox#insightGroup {{border-radius:14px;}}
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
    """A calm, minimal 270-degree ring: no ticks, one soft gradient arc."""
    pal = PALETTE
    outer = box.width() / 2
    thick = max(5.0, outer * .155)
    arc = box.adjusted(thick / 2 + 3, thick / 2 + 3, -thick / 2 - 3, -thick / 2 - 3)
    fraction = 0 if value is None else max(0, min(100, value)) / 100
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color(pal['track'], 220), thick, Qt.SolidLine, Qt.RoundCap))
    p.drawArc(arc, 225 * 16, -270 * 16)
    if value is None:
        return
    from PySide6.QtGui import QConicalGradient
    gradient = QConicalGradient(arc.center(), 225)
    gradient.setColorAt(1, color(level_tone or SPECTRUM[0]))
    gradient.setColorAt(.66, color(level_tone or SPECTRUM[1]))
    gradient.setColorAt(.33, color(level_tone or SPECTRUM[2]))
    gradient.setColorAt(0, color(level_tone or SPECTRUM[3]))
    span = round(-270 * 16 * fraction)
    glow = QConicalGradient(arc.center(), 225)
    for stop, tone in ((1, SPECTRUM[0]), (.66, SPECTRUM[1]), (.33, SPECTRUM[2]), (0, SPECTRUM[3])):
        glow.setColorAt(stop, color(level_tone or tone, 28))
    p.setPen(QPen(QBrush(glow), thick * 1.8, Qt.SolidLine, Qt.RoundCap))
    p.drawArc(arc, 225 * 16, span)
    p.setPen(QPen(QBrush(gradient), thick, Qt.SolidLine, Qt.RoundCap))
    p.drawArc(arc, 225 * 16, span)
    if fraction > .01:
        a = math.radians(225 - 270 * fraction)
        r = arc.width() / 2
        tip = QPointF(arc.center().x() + math.cos(a) * r, arc.center().y() - math.sin(a) * r)
        halo = QRadialGradient(tip, thick * 1.1)
        halo.setColorAt(0, color('#ffffff', 210))
        halo.setColorAt(.45, color(level_tone or SPECTRUM[0], 90))
        halo.setColorAt(1, color(level_tone or SPECTRUM[0], 0))
        p.setPen(Qt.NoPen)
        p.setBrush(halo)
        p.drawEllipse(tip, thick * 1.1, thick * 1.1)
        p.setBrush(color('#ffffff'))
        p.drawEllipse(tip, thick * .22, thick * .22)


def _area_graph(p, rect, history):
    pal = PALETTE
    if rect.width() < 12 or rect.height() < 12:
        return
    p.setBrush(Qt.NoBrush)
    for i in range(3):
        y = rect.top() + rect.height() * i / 2
        p.setPen(QPen(color(pal['grid'], 130), .6, Qt.DotLine))
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
    for points in runs:
        if len(points) == 1:
            p.setPen(Qt.NoPen)
            p.setBrush(color(pal['accent']))
            p.drawEllipse(points[0], 2.0, 2.0)
            continue
        curve = _smooth(points)
        area = QPainterPath(curve)
        area.lineTo(points[-1].x(), rect.bottom())
        area.lineTo(points[0].x(), rect.bottom())
        area.closeSubpath()
        fill = QLinearGradient(0, rect.top(), 0, rect.bottom())
        fill.setColorAt(0, color(pal['accent'], 78))
        fill.setColorAt(.65, color(pal['secondary'], 22))
        fill.setColorAt(1, color(pal['secondary'], 0))
        p.fillPath(area, fill)
        line = QLinearGradient(rect.left(), 0, rect.right(), 0)
        line.setColorAt(0, color(SPECTRUM[2]))
        line.setColorAt(1, color(SPECTRUM[0]))
        p.setPen(QPen(color(pal['accent'], 32), 5.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(curve)
        p.setPen(QPen(QBrush(line), 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(curve)
        tip = points[-1]
        halo = QRadialGradient(tip, 8)
        halo.setColorAt(0, color('#ffffff', 200))
        halo.setColorAt(.35, color(pal['accent'], 100))
        halo.setColorAt(1, color(pal['accent'], 0))
        p.setPen(Qt.NoPen)
        p.setBrush(halo)
        p.drawEllipse(tip, 8, 8)


def paint_metric(metric, p):
    from .i18n import tr
    pal = PALETTE
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    rect = QRectF(metric.rect()).adjusted(5, 3, -5, -3)
    width, height = rect.width(), rect.height()
    font = QFont(metric.font())

    def text(area, value, size=12, tone=None, weight=QFont.Normal,
             align=Qt.AlignLeft | Qt.AlignVCenter, spacing=0):
        font.setPixelSize(size)
        font.setWeight(weight)
        font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
        p.setFont(font)
        p.setPen(color(tone or pal['text']))
        shown = p.fontMetrics().elidedText(str(value), Qt.ElideRight, max(1, round(area.width())))
        p.drawText(area, align, shown)

    text(QRectF(rect.left(), rect.top(), width, 22), tr(metric.title).upper(), 11,
         pal['accent'], QFont.DemiBold, spacing=1.4)
    value = metric._display_value
    kind = metric.kind
    shown = '–' if value is None else f'{value:.0f}'
    unit = '' if kind == 'health' or value is None else '%'
    level = None
    if value is not None and kind != 'health' and value >= 90:
        level = '#ff8f8f'
    elif value is not None and kind != 'health' and value >= 75:
        level = '#f3c98b'
    elif kind == 'health' and value is not None and value < 50:
        level = '#ff8f8f'
    top = rect.top() + (46 if kind in ('cpu', 'gpu') else 26)
    if kind in ('cpu', 'gpu'):
        text(QRectF(rect.left(), rect.top() + 22, width, 20), metric.extra, 11, pal['muted'])
    bottom = rect.bottom() - 26
    available = max(40.0, bottom - top)
    wide = width > 330 and kind in ('cpu', 'gpu')
    diameter = min(available, 188.0, width * (.35 if wide else .90 if kind in ('cpu', 'gpu') else .78))
    diameter = max(64.0, diameter)
    side_by_side = wide or (kind in ('ram', 'disk', 'health') and width > 300)
    if side_by_side:
        ring_box = QRectF(rect.left() + 4, top + (available - diameter) / 2, diameter, diameter)
    else:
        ring_box = QRectF(rect.left() + (width - diameter) / 2, top + (available - diameter) / 2,
                          diameter, diameter)
    _ring(p, ring_box, value, level_tone=level)
    size = round(max(16, min(40, diameter * .23)))
    inner = QRectF(ring_box.left(), ring_box.top() + diameter * .28, diameter, diameter * .32)
    font.setPixelSize(size)
    font.setWeight(QFont.DemiBold)
    font.setLetterSpacing(QFont.AbsoluteSpacing, 0)
    p.setFont(font)
    number_w = p.fontMetrics().horizontalAdvance(shown)
    unit_size = max(10, round(size * .48))
    font.setPixelSize(unit_size)
    p.setFont(font)
    unit_w = p.fontMetrics().horizontalAdvance(unit) + 2 if unit else 0
    start = inner.center().x() - (number_w + unit_w) / 2
    text(QRectF(start, inner.top(), number_w + 4, inner.height()), shown, size, weight=QFont.DemiBold)
    if unit:
        text(QRectF(start + number_w + 2, inner.top() + size * .14, unit_w + 6, inner.height()), unit,
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
