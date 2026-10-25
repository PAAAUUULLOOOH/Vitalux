"""Crystal Atrium: original liquid-glass dashboard over a static colourful stage.

The shared dashboard editor arranges custom-painted glass tiles: three
spheres filled with live liquid (CPU / GPU / RAM), glowing ribbon charts,
a network panel and glass drive tubes. Every tile samples the same static
window backdrop; there is no second stage behind the overview.

Why the glass reads as glass here (and not as a grey translucent box):

* There is something *to refract*. Glass over a flat dark background shows
  nothing; the stage is made of large, saturated, softly lit orbs.
* The backdrop inside every pane is magnified towards the middle and
  magnified harder in a thin band along the edge (the way a thick pane or a
  lens bends what is behind it), then lightened towards the rim (Fresnel).
* Rims are lit from two sides with a conic gradient and a tiny chromatic
  fringe, with a specular streak along the top edge and an inner shadow on
  the shaded side.
* Spheres invert the scene behind them, carry a refracting liquid with a
  meniscus and bubbles, and get a crescent of caustic light opposite the
  main highlight.

Every static pane is cached until its data, position or backdrop changes.
Only the three visible liquid instruments use a 15 fps animation timer.
"""
import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QFont,
                           QFontMetrics, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap, QRadialGradient)
from PySide6.QtWidgets import QSizePolicy, QWidget

KEY = 'crystal_atrium'
PALETTE = dict(
    title='Crystal Atrium', subtitle='LIQUID GLASS / STATIC LIGHT',
    bg='#050818', sidebar='#0a1030', card='#0e1536', border='#a9bcff',
    track='#16204a', grid='#26336a', text='#f5f8ff', muted='#a9b6dc',
    accent='#7fd6ff', secondary='#ff7ad9', light='#ffffff', bloom='#ffc46b',
    shadow='#02030a',
    series=('#7fd6ff', '#ff7ad9', '#ffc46b', '#6bffd0', '#b79bff'))

# x, y (fractions), radius (fraction of the longer side), core, edge,
# drift x/y, speed, phase
ORBS = (
    (.16, .30, .17, '#66b2ff', '#1b3fd6', .030, .040, .9, 0.0),
    (.58, .16, .15, '#ff7ccd', '#b0148f', .040, .030, .7, 1.7),
    (.88, .58, .21, '#35ead0', '#0a7f9a', .030, .050, .6, 3.1),
    (.38, .84, .19, '#ffb858', '#e0481f', .050, .030, .8, 4.4),
    (.06, .86, .12, '#a77bff', '#4a1fb8', .030, .030, 1.0, 5.2),
    (.76, .94, .10, '#7be0ff', '#2563eb', .040, .020, .5, 2.4),
)
TILE_KEYS = ('hero', 'cpu', 'gpu', 'ram', 'graph_load', 'network', 'drives')
_BASE_CACHE = {}


def color(value, alpha=255):
    c = QColor(value)
    c.setAlpha(max(0, min(255, round(alpha))))
    return c



def _mix(c1, c2, t):
    a, b = QColor(c1), QColor(c2)
    return QColor(round(a.red() + (b.red() - a.red()) * t),
                  round(a.green() + (b.green() - a.green()) * t),
                  round(a.blue() + (b.blue() - a.blue()) * t))



def _rr(rect, radius):
    path = QPainterPath()
    radius = max(0.0, min(radius, rect.width() / 2, rect.height() / 2))
    path.addRoundedRect(rect, radius, radius)
    return path



def shape(rect, compact=False):
    radius = min(rect.width(), rect.height()) * .32 if compact else 26.0
    return _rr(rect, radius)



# ---------------------------------------------------------------------- stage
def _base_layer(w, h):
    cached = _BASE_CACHE.get((w, h))
    if cached is not None:
        return cached
    pixmap = QPixmap(w, h)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    rect = QRectF(0, 0, w, h)
    base = QLinearGradient(0, 0, w, h)
    base.setColorAt(0, color('#070c26'))
    base.setColorAt(.5, color('#0b1442'))
    base.setColorAt(1, color('#140a3a'))
    p.fillRect(rect, base)
    seed = 1618
    p.setPen(Qt.NoPen)
    for i in range(170):
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        x = (seed % 10000) / 10000 * w
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        y = (seed % 10000) / 10000 * h
        p.setBrush(color('#ffffff', 14 + (i * 31) % 70))
        s = .5 + (i % 4) * .22
        p.drawEllipse(QPointF(x, y), s, s)
    p.end()
    if len(_BASE_CACHE) > 4:
        _BASE_CACHE.clear()
    _BASE_CACHE[(w, h)] = pixmap
    return pixmap


def draw_orbs(p, w, h, t, strength=1.0):
    scale = max(w, h)
    for ox, oy, r, core, edge, ax, ay, speed, ph in ORBS:
        cx = w * (ox + ax * math.sin(t * speed * .6 + ph))
        cy = h * (oy + ay * math.cos(t * speed * .5 + ph * 1.3))
        radius = scale * r
        halo = QRadialGradient(QPointF(cx, cy), radius * 2.1)
        halo.setColorAt(0, color(core, 95 * strength))
        halo.setColorAt(.55, color(edge, 34 * strength))
        halo.setColorAt(1, color(edge, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(halo)
        p.drawEllipse(QPointF(cx, cy), radius * 2.1, radius * 2.1)
        body = QRadialGradient(QPointF(cx - radius * .32, cy - radius * .38), radius * 1.18)
        body.setColorAt(0, color('#ffffff', 235 * strength))
        body.setColorAt(.22, color(core, 255 * strength))
        body.setColorAt(.75, color(edge, 255 * strength))
        body.setColorAt(1, color(edge, 220 * strength))
        p.setBrush(body)
        p.drawEllipse(QPointF(cx, cy), radius, radius)


def stage_pixmap(w, h, t=0.0, strength=1.0):
    # Keep the original orb composition frozen, including refracted backdrops.
    t = 0.0
    pixmap = _base_layer(w, h).copy()
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    draw_orbs(p, w, h, t, strength)
    rect = QRectF(0, 0, w, h)
    p.setCompositionMode(QPainter.CompositionMode_Plus)
    for x0, x1, alpha in ((.1, .75, 10), (.55, 1.1, 7)):
        beam = QLinearGradient(QPointF(w * x0, 0), QPointF(w * x1, h))
        beam.setColorAt(0, color('#ffffff', 0))
        beam.setColorAt(.5, color('#cfe4ff', alpha))
        beam.setColorAt(1, color('#ffffff', 0))
        p.fillRect(rect, beam)
    p.setCompositionMode(QPainter.CompositionMode_SourceOver)
    vignette = QRadialGradient(QPointF(w * .5, h * .45), max(w, h) * .85)
    vignette.setColorAt(0, QColor(0, 0, 0, 0))
    vignette.setColorAt(.65, QColor(2, 3, 14, 30))
    vignette.setColorAt(1, QColor(2, 3, 14, 170))
    p.fillRect(rect, vignette)
    p.end()
    return pixmap


def scene_pixmap(size, phase=0.0):
    return stage_pixmap(max(1, size.width()), max(1, size.height()), phase * .5, .72)


# ---------------------------------------------------------------------- glass
def _soft_shadow(p, rect, radius, strength=1.0):
    for i in range(8):
        t = (i + 1) / 8
        grow = t * 18
        dy = t * 11
        alpha = ((1 - t) ** 1.8) * 62 * strength
        if alpha >= 1:
            p.fillPath(_rr(rect.adjusted(-grow, -grow + dy, grow, grow + dy), radius + grow * .6),
                       color('#02030c', alpha))



def glass(p, rect, radius, draw_backdrop, *, strength=1.0, tint=None,
          active=False, lens=True, shadow=True):
    """One pane of physically-motivated glass."""
    path = _rr(rect, radius)
    if shadow:
        _soft_shadow(p, rect, radius, strength)
    p.save()
    p.setClipPath(path)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    draw_backdrop(p, rect, .94 if lens else 1.0)
    if lens:
        inner = _rr(rect.adjusted(11, 11, -11, -11), max(2.0, radius - 11))
        band = path.subtracted(inner)
        p.save()
        p.setClipPath(band, Qt.IntersectClip)
        draw_backdrop(p, rect, .72)
        p.fillPath(band, color('#ffffff', 12))
        p.restore()
    # Glass is lighter towards its rim (Fresnel) and a touch darker inside.
    cx, cy = rect.center().x(), rect.center().y()
    fresnel = QRadialGradient(QPointF(cx, cy), max(rect.width(), rect.height()) * .72)
    fresnel.setColorAt(0, color('#040a22', 150 * strength))
    fresnel.setColorAt(.62, color('#0a1640', 96 * strength))
    fresnel.setColorAt(1, color('#bcd0ff', 46 * strength))
    p.fillPath(path, fresnel)
    if tint:
        p.fillPath(path, color(tint, 30))
    shade = QLinearGradient(rect.bottomRight(),
                            QPointF(rect.right() - rect.width() * .30, rect.bottom() - rect.height() * .30))
    shade.setColorAt(0, color('#01020a', 92))
    shade.setColorAt(1, color('#01020a', 0))
    p.fillPath(path, shade)
    lit = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + rect.height() * .26))
    lit.setColorAt(0, color('#ffffff', 58))
    lit.setColorAt(1, color('#ffffff', 0))
    p.fillPath(path, lit)
    glare = QLinearGradient(rect.topLeft(), QPointF(rect.left() + rect.width() * .55, rect.top() + rect.height() * .95))
    glare.setColorAt(0, color('#ffffff', 40))
    glare.setColorAt(.2, color('#ffffff', 12))
    glare.setColorAt(.38, color('#ffffff', 0))
    p.fillPath(path, glare)
    p.restore()
    rim = QConicalGradient(rect.center(), 135)
    for t, a in ((0, 235), (.12, 125), (.25, 46), (.38, 112), (.5, 205),
                 (.62, 112), (.75, 46), (.88, 125), (1, 235)):
        rim.setColorAt(t, color('#ffffff', min(255, a + (30 if active else 0))))
    p.setBrush(Qt.NoBrush)
    if active:
        p.setOpacity(.5)
        p.setPen(QPen(color(palette()['accent'], 190), 4.5))
        p.drawPath(path)
        p.setOpacity(1)
    # A hint of chromatic dispersion: red/blue ghosts either side of the rim.
    p.setPen(QPen(color('#7fd0ff', 54), 1.0))
    p.drawPath(path.translated(.8, .3))
    p.setPen(QPen(color('#ff8fb0', 44), 1.0))
    p.drawPath(path.translated(-.8, -.3))
    p.setPen(QPen(QBrush(rim), 1.5))
    p.drawPath(path)
    p.setPen(QPen(color('#ffffff', 24), .8))
    p.drawPath(_rr(rect.adjusted(2.2, 2.2, -2.2, -2.2), max(2.0, radius - 2.2)))
    if rect.width() > 80 and rect.height() > 40:
        edge = min(radius, rect.width() / 2) * .9
        streak = QLinearGradient(rect.left() + edge, 0, rect.right() - edge, 0)
        streak.setColorAt(0, color('#ffffff', 0))
        streak.setColorAt(.35, color('#ffffff', 170 if active else 130))
        streak.setColorAt(.65, color('#ffffff', 60))
        streak.setColorAt(1, color('#ffffff', 0))
        p.setPen(QPen(QBrush(streak), 1.8))
        p.drawLine(QPointF(rect.left() + edge, rect.top() + 1.7),
                   QPointF(rect.right() - edge, rect.top() + 1.7))



def paint_panel(p, widget, rect, *, strong=False, compact=False, active=False):
    from .glass import draw_frosted_backdrop
    if compact:
        glass(p, rect, min(rect.width(), rect.height()) * .32,
              lambda painter, r, zoom: draw_frosted_backdrop(painter, widget, r, 1.0),
              strength=1.0, active=active, lens=False, shadow=False)
        return
    inner = rect.adjusted(5, 4, -5, -10)
    glass(p, inner, 26.0,
          lambda painter, r, zoom: draw_frosted_backdrop(painter, widget, r, 1.0),
          strength=1.15 if strong else 1.0, active=active, lens=False)



def stylesheet():
    pal = palette()
    return f'''
    #heroTitle {{font-size:22px;font-weight:620;color:{pal['text']};}}
    #pageTitle {{font-size:32px;font-weight:660;}}
    #cardTitle {{font-size:10px;font-weight:650;letter-spacing:1.9px;color:{pal['accent']};}}
    #chipValue {{font-size:11px;font-weight:620;color:{pal['text']};}}
    #chipTitle {{font-size:9px;color:{pal['muted']};}}
    QLineEdit,QComboBox,QSpinBox,QTextEdit,QListWidget,QTableWidget {{
        background:rgba(14,21,54,170);color:{pal['text']};border:1px solid rgba(169,188,255,110);border-radius:13px;}}
    QHeaderView::section {{background:rgba(10,16,48,190);color:{pal['muted']};border:none;padding:8px;}}
    QTableWidget::item {{padding:6px;border-bottom:1px solid {pal['grid']};}}
    QTableWidget::item:selected {{background:{pal['track']};color:{pal['text']};}}
    QComboBox::drop-down {{border-radius:13px;background:rgba(14,21,54,200);}}
    QPushButton#ghostBtn,QPushButton#langBtn,QToolButton#layoutAction {{
        border:1px solid rgba(169,188,255,120);border-radius:13px;background:rgba(14,21,54,170);color:{pal['text']};}}
    QPushButton#ghostBtn:hover,QPushButton#langBtn:hover,QToolButton#layoutAction:hover {{
        border-color:{pal['accent']};background:rgba(38,51,106,200);}}
    QPushButton#primaryBtn,QPushButton#langBtn:checked {{
        background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:.4 {pal['accent']},stop:1 {pal['secondary']});
        border-radius:13px;border:1px solid #ffffff;color:#06102e;}}
    QProgressBar,QProgressBar::chunk,QGroupBox#insightGroup {{border-radius:13px;}}
    QScrollBar::handle:vertical {{background:rgba(169,188,255,120);border-radius:3px;}}
    '''



def paint_metric(metric, p):
    """Fallback for an instrument before its Atrium tile is selected."""
    p.setPen(color(palette()['text']))
    p.drawText(metric.rect(), Qt.AlignCenter, str(metric.detail or '–'))



# -------------------------------------------------------------------- sphere
def draw_sphere(p, centre, radius, fraction, col_a, col_b, t, seed, blur, scale):
    """A glass sphere with liquid: refraction, meniscus, bubbles, caustic."""
    cx, cy, R = centre.x(), centre.y(), radius
    p.save()
    p.translate(cx, cy + R * 1.1)
    p.scale(1.0, .15)
    shadow = QRadialGradient(QPointF(0, 0), R * 1.15)
    shadow.setColorAt(0, color('#000010', 150))
    shadow.setColorAt(1, color('#000010', 0))
    p.setPen(Qt.NoPen)
    p.setBrush(shadow)
    p.drawEllipse(QPointF(0, 0), R * 1.15, R * 1.15)
    p.restore()
    circle = QPainterPath()
    circle.addEllipse(centre, R, R)
    p.save()
    p.setClipPath(circle)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    if blur is not None and not blur.isNull():
        # A real sphere inverts what is behind it: draw the backdrop flipped
        # about the centre, magnified, behind the liquid.
        sx, sy = scale
        half_w, half_h = R * 1.1 * sx, R * 1.1 * sy
        src = QRectF(cx * sx - half_w, cy * sy - half_h, half_w * 2, half_h * 2)
        p.save()
        p.translate(cx, cy)
        p.scale(-1, -1)
        p.setOpacity(.62)
        p.drawPixmap(QRectF(-R * 1.1, -R * 1.1, R * 2.2, R * 2.2), blur, src)
        p.restore()
    body = QRadialGradient(centre, R)
    body.setColorAt(0, color('#0a1640', 70))
    body.setColorAt(.72, color('#9fb8ff', 10))
    body.setColorAt(.93, color('#dfe9ff', 34))
    body.setColorAt(1, color('#ffffff', 80))
    p.setBrush(body)
    p.setPen(Qt.NoPen)
    p.drawEllipse(centre, R, R)
    if fraction is not None:
        frac = max(.045, min(.955, fraction))
        level = cy + R - 2 * R * frac
        amp = R * .032
        k = math.pi * 2.0 / (R * 1.5)
        wave = QPainterPath(QPointF(cx - R - 2, level))
        steps = 36
        for i in range(steps + 1):
            x = cx - R - 2 + (2 * R + 4) * i / steps
            y = (level + amp * math.sin(k * x + t * 2.1 + seed)
                 + amp * .45 * math.sin(k * 2.3 * x - t * 1.5 + seed * 2))
            wave.lineTo(x, y)
        surface = QPainterPath(wave)
        wave.lineTo(cx + R + 2, cy + R + 2)
        wave.lineTo(cx - R - 2, cy + R + 2)
        wave.closeSubpath()
        liquid = QLinearGradient(0, level, 0, cy + R)
        liquid.setColorAt(0, color(_mix(col_a, '#ffffff', .18), 214))
        liquid.setColorAt(.5, color(col_a, 226))
        liquid.setColorAt(1, color(_mix(col_b, '#000020', .18), 248))
        p.fillPath(wave, liquid)
        glow = QRadialGradient(QPointF(cx, cy + R * .62), R * .9)
        glow.setColorAt(0, color(_mix(col_a, '#ffffff', .3), 62))
        glow.setColorAt(1, color(col_a, 0))
        p.save()
        p.setClipPath(wave, Qt.IntersectClip)
        p.fillRect(QRectF(cx - R, level, 2 * R, cy + R - level), glow)
        side = QLinearGradient(cx - R, 0, cx + R, 0)
        side.setColorAt(0, color('#ffffff', 46))
        side.setColorAt(.28, color('#ffffff', 0))
        side.setColorAt(.8, color('#000010', 0))
        side.setColorAt(1, color('#000010', 96))
        p.fillRect(QRectF(cx - R, level, 2 * R, cy + R - level), side)
        # Bubbles rising through the liquid.
        depth = max(1.0, cy + R - level)
        p.setBrush(Qt.NoBrush)
        for i in range(8):
            bx = cx + R * ((((i * 53 + int(seed * 10)) % 100) / 100) * 1.3 - .65)
            speed = .035 + (i % 3) * .022
            by = cy + R - ((t * speed * R * 2 + i * R * .41) % depth)
            br = R * (.018 + (i % 3) * .009)
            p.setPen(QPen(color('#ffffff', 150), .9))
            p.setBrush(color('#ffffff', 38))
            p.drawEllipse(QPointF(bx, by), br, br)
        p.restore()
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(color(_mix(col_a, '#ffffff', .55), 90), 4.2))
        p.drawPath(surface.translated(0, 1.6))
        p.setPen(QPen(color('#ffffff', 190), 1.5))
        p.drawPath(surface)
    p.restore()
    p.setBrush(Qt.NoBrush)
    fres = QRadialGradient(centre, R)
    fres.setColorAt(.0, color('#ffffff', 0))
    fres.setColorAt(.82, color('#ffffff', 0))
    fres.setColorAt(.96, color('#bcd2ff', 52))
    fres.setColorAt(1, color('#ffffff', 96))
    p.setPen(Qt.NoPen)
    p.setBrush(fres)
    p.drawEllipse(centre, R, R)



def draw_sphere_glints(p, centre, radius, col_a):
    """Specular highlights and the opposite-side caustic, drawn *over* the
    value text so the glass is clearly in front of everything inside it."""
    cx, cy, R = centre.x(), centre.y(), radius
    p.save()
    p.translate(cx - R * .34, cy - R * .5)
    p.rotate(-34)
    soft = QRadialGradient(QPointF(0, 0), R * .5)
    soft.setColorAt(0, color('#ffffff', 210))
    soft.setColorAt(.5, color('#ffffff', 70))
    soft.setColorAt(1, color('#ffffff', 0))
    p.setPen(Qt.NoPen)
    p.setBrush(soft)
    p.scale(1.0, .5)
    p.drawEllipse(QPointF(0, 0), R * .5, R * .5)
    p.restore()
    outer = QPainterPath()
    outer.addEllipse(centre, R * .95, R * .95)
    inner = QPainterPath()
    inner.addEllipse(QPointF(cx + R * .075, cy + R * .1), R * .95, R * .95)
    crescent = outer.subtracted(inner)
    grad = QLinearGradient(QPointF(cx - R, cy - R), QPointF(cx + R * .2, cy + R * .2))
    grad.setColorAt(0, color('#ffffff', 245))
    grad.setColorAt(.55, color('#ffffff', 40))
    grad.setColorAt(1, color('#ffffff', 0))
    p.fillPath(crescent, grad)
    inner2 = QPainterPath()
    inner2.addEllipse(QPointF(cx - R * .07, cy - R * .09), R * .95, R * .95)
    caustic = outer.subtracted(inner2)
    grad2 = QLinearGradient(QPointF(cx + R, cy + R), QPointF(cx - R * .2, cy - R * .2))
    grad2.setColorAt(0, color(_mix(col_a, '#ffffff', .35), 170))
    grad2.setColorAt(.6, color(col_a, 30))
    grad2.setColorAt(1, color(col_a, 0))
    p.fillPath(caustic, grad2)
    rim = QConicalGradient(centre, 135)
    for t, a in ((0, 220), (.25, 50), (.5, 150), (.75, 50), (1, 220)):
        rim.setColorAt(t, color('#ffffff', a))
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QBrush(rim), 1.5))
    p.drawEllipse(centre, R, R)



def draw_tube(p, rect, fraction, col_a, col_b, t, seed):
    """A horizontal glass capsule filled with liquid (drive usage)."""
    radius = rect.height() / 2
    path = _rr(rect, radius)
    p.save()
    p.setClipPath(path)
    p.fillPath(path, color('#06102e', 120))
    if fraction is not None:
        fill_w = max(rect.height(), rect.width() * max(0.0, min(1.0, fraction)))
        liquid = QLinearGradient(0, rect.top(), 0, rect.bottom())
        liquid.setColorAt(0, color(_mix(col_a, '#ffffff', .28), 235))
        liquid.setColorAt(.55, color(col_a, 235))
        liquid.setColorAt(1, color(col_b, 245))
        edge = rect.left() + fill_w
        wave = QPainterPath(QPointF(rect.left(), rect.top()))
        amp = rect.height() * .09
        steps = 14
        wave.lineTo(edge - amp, rect.top())
        for i in range(steps + 1):
            y = rect.top() + rect.height() * i / steps
            wave.lineTo(edge + amp * math.sin(y * .5 + t * 2.4 + seed), y)
        wave.lineTo(rect.left(), rect.bottom())
        wave.closeSubpath()
        p.fillPath(wave, liquid)
    p.restore()
    top = QLinearGradient(0, rect.top(), 0, rect.bottom())
    top.setColorAt(0, color('#ffffff', 120))
    top.setColorAt(.4, color('#ffffff', 16))
    top.setColorAt(1, color('#ffffff', 0))
    p.save()
    p.setClipPath(path)
    p.fillRect(rect, top)
    p.restore()
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color('#ffffff', 120), 1.1))
    p.drawPath(path)



# ------------------------------------------------------------------- canvas
def _fmt_pct(value):
    return '–' if value is None else f'{value:.0f}'



class AtriumTile(QWidget):
    """One editable glass tile, aligned to the shared window background."""

    SPHERES = (
        ('cpu', 'Prozessor', '#7fd6ff', '#2b6bff'),
        ('gpu', 'Grafik', '#ff8bdc', '#a42cff'),
        ('ram', 'Arbeitsspeicher', '#ffcb72', '#ff6a3c'),
    )

    def __init__(self, key, distro_name, logo, parent=None):
        super().__init__(parent)
        self.key = key
        self.distro_name = distro_name
        self.logo = logo
        self.logo_visible = True
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._backdrop_key = None
        self._data = None
        self._hint_regions=[]
        self._static = QPixmap()
        self._blur = QPixmap()
        self._dirty = True
        self._t0 = time.monotonic()
        self._shown = {'cpu': 0.0, 'gpu': 0.0, 'ram': 0.0}
        self._sphere_geo = {}
        self._sphere_meta = {}
        self._scale = (1, 1)
        self._timer = QTimer(self)
        self._timer.setInterval(66)
        self._timer.timeout.connect(self._tick)
        from .overview_text import OverviewInfo
        self.captions={name:OverviewInfo(self) for name,*_ in self.SPHERES if name == key}
        for caption in self.captions.values():caption.setAttribute(Qt.WA_TranslucentBackground,True)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(340, 370)

    # -- data / lifecycle ------------------------------------------------
    def set_data(self, data):
        self._data = data
        self._dirty = True
        self.sync_timer()
        self.update()

    def _animate(self):
        from . import motion
        return self.key in self.captions and self.isVisible() and motion.enabled()

    def showEvent(self, event):
        super().showEvent(event)
        self._dirty = True
        self.sync_timer()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()

    def sync_timer(self):
        if self._animate():
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._dirty = True

    def _tick(self):
        if not self._animate():
            self._timer.stop()
            return
        data = self._data or {}
        for key in self._shown:
            target = (data.get(key) or {}).get('value')
            target = 0.0 if target is None else target / 100
            self._shown[key] += (target - self._shown[key]) * .14
        region = None
        for geo in self._sphere_geo.values():
            r = geo.toAlignedRect()
            region = r if region is None else region.united(r)
        if region is not None:
            self.update(region)
        else:
            self.update()

    # -- painting --------------------------------------------------------
    def _background(self):
        from .glass import scene_for
        from PySide6.QtCore import QPoint
        scene = scene_for(self)
        if scene is None:
            return None, QPoint(), (self.size(), self.devicePixelRatioF())
        image = scene.soft_backdrop()
        pos = self.mapTo(scene, QPoint())
        return image, pos, (self.size(), self.devicePixelRatioF(), pos, image.cacheKey())

    def _backdrop(self):
        blur = self._blur
        sx = blur.width() / max(1, self.width())
        sy = blur.height() / max(1, self.height())

        def draw(p, rect, zoom):
            cx, cy = rect.center().x(), rect.center().y()
            sw, sh = rect.width() * zoom, rect.height() * zoom
            src = QRectF((cx - sw / 2) * sx, (cy - sh / 2) * sy, sw * sx, sh * sy)
            p.drawPixmap(rect, blur, src)
        return draw

    def _font(self, size, weight=QFont.Normal, spacing=0.0):
        font = QFont(self.font())
        font.setPixelSize(int(size))
        font.setWeight(weight)
        font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
        return font

    def _text(self, p, rect, value, size, tone, weight=QFont.Normal,
              align=Qt.AlignCenter, spacing=0.0):
        p.setFont(self._font(size, weight, spacing))
        shown = QFontMetrics(p.font()).elidedText(str(value), Qt.ElideRight, max(1, int(rect.width())))
        if shown!=str(value):
            self._hint_regions.append((QRectF(rect),str(value)))
            self.setProperty('vitaluxFullNameHint',True)
        p.setPen(color('#02061a', 150))
        p.drawText(rect.translated(0, 1.2), align, shown)
        p.setPen(color(tone))
        p.drawText(rect, align, shown)

    def _wrapped_text(self, p, rect, value, size, tone):
        p.setFont(self._font(size))
        p.setPen(color(tone))
        p.drawText(rect, Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, str(value))

    def _rebuild(self):
        self._hint_regions=[];self.setProperty('vitaluxFullNameHint',False)
        w, h = max(1, self.width()), max(1, self.height())
        dpr = self.devicePixelRatioF()
        image, pos, self._backdrop_key = self._background()
        self._blur = QPixmap(max(1, round(w*dpr)), max(1, round(h*dpr)))
        self._blur.setDevicePixelRatio(dpr)
        self._blur.fill(Qt.transparent)
        if image is not None and not image.isNull():
            ratio=image.devicePixelRatioF()
            painter=QPainter(self._blur)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(QRectF(0,0,w,h),image,
                               QRectF(pos.x()*ratio,pos.y()*ratio,w*ratio,h*ratio))
            painter.end()
        pm = QPixmap(max(1, round(w * dpr)), max(1, round(h * dpr)))
        pm.setDevicePixelRatio(dpr)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        from . import settings
        data = self._data
        area = QRectF(5, 5, max(1,w-10), max(1,h-10))
        backdrop = self._backdrop()
        self._sphere_geo = {}
        self._sphere_meta = {}
        self._scale = (self._blur.width()/w, self._blur.height()/h)
        if self.key == 'hero':
            glass(p, area, 28, backdrop)
            self._paint_hero(p, area, data)
        for i, (key, title, col_a, col_b) in enumerate(self.SPHERES):
            if key != self.key:
                continue
            if settings.get('accent','design_default')!='design_default':
                colors=palette()['series'];col_a=colors[i%len(colors)];col_b=palette()['secondary']
            glass(p, area, 30, backdrop, tint=col_a)
            info = (data or {}).get(key) or {}
            self._text(p, QRectF(area.left() + 24, area.top() + 16, area.width() - 48, 20),
                       self._tr(title).upper(), 11, _mix(col_a, '#ffffff', .5).name(), QFont.DemiBold, align=Qt.AlignCenter, spacing=2.0)
            radius = max(48.0, min(area.width() * .30, (area.height() - 185) / 2))
            centre = QPointF(area.center().x(), area.top() + 36 + radius + 14)
            self._sphere_geo[key] = QRectF(centre.x() - radius - 8, centre.y() - radius - 8,
                                           radius * 2 + 16, radius * 2.45)
            caption=self.captions[key]
            caption.set(info.get('name',''),info.get('detail',''),info.get('power',''))
            top=round(centre.y()+radius+16)
            caption.setGeometry(round(area.left()+20),top,round(area.width()-40),max(1,round(area.bottom()-top-16)))
            self._sphere_meta[key] = (centre, radius, col_a, col_b, i)
        for key, paint in (('graph_load',self._paint_graph),
                           ('network',self._paint_network),('drives',self._paint_drives)):
            if self.key == key:
                glass(p, area, 28, backdrop)
                paint(p, area, data)
        p.end()
        self._static = pm
        self._dirty = False

    def _tr(self, value):
        from .i18n import tr
        return tr(value)

    def _paint_hero(self, p, rect, data):
        data = data or {}
        if self.logo_visible and self.logo is not None and not self.logo.isNull():
            ratio=max(1.,self.logo.devicePixelRatioF())
            pix=self.logo.scaled(round(76*ratio),round(76*ratio),Qt.KeepAspectRatio,Qt.SmoothTransformation)
            p.drawPixmap(QPointF(rect.left()+24,rect.top()+16),pix)
        self._text(p,QRectF(rect.left()+112,rect.top()+24,rect.width()-224,44),self.distro_name,23,'#ffffff',QFont.DemiBold)
        chips=data.get('chips') or []
        gap=10;width=(rect.width()-48-gap*max(0,len(chips)-1))/max(1,len(chips))
        for index,(title,value) in enumerate(chips):
            chip=QRectF(rect.left()+24+index*(width+gap),rect.bottom()-82,width,64)
            glass(p,chip,22,self._backdrop(),strength=.9,lens=False,shadow=False)
            self._text(p,chip.adjusted(10,8,-10,-36),self._tr(title),9,'#c9d6ff')
            self._text(p,chip.adjusted(10,28,-10,-10),value,13,'#ffffff',QFont.DemiBold)

    def _ribbon(self, p, rect, history, tone, fill_alpha=80):
        points = []
        n = len(history)
        if n < 2:
            return
        for i, v in enumerate(history):
            if v is None or not math.isfinite(float(v)):
                points.append(None)
                continue
            points.append(QPointF(rect.right() - (n - 1 - i) * rect.width() / max(59, n - 1),
                                  rect.bottom() - max(0.0, min(100.0, float(v))) * rect.height() / 100))
        runs, run = [], []
        for pt in points:
            if pt is None:
                if run:
                    runs.append(run)
                run = []
            else:
                run.append(pt)
        if run:
            runs.append(run)
        for pts in runs:
            if len(pts) < 2:
                continue
            path = QPainterPath(pts[0])
            for i in range(len(pts) - 1):
                p0 = pts[i - 1] if i else pts[i]
                p1, p2 = pts[i], pts[i + 1]
                p3 = pts[i + 2] if i + 2 < len(pts) else p2
                c1 = QPointF(p1.x() + (p2.x() - p0.x()) / 6, p1.y() + (p2.y() - p0.y()) / 6)
                c2 = QPointF(p2.x() - (p3.x() - p1.x()) / 6, p2.y() - (p3.y() - p1.y()) / 6)
                path.cubicTo(c1, c2, p2)
            area = QPainterPath(path)
            area.lineTo(pts[-1].x(), rect.bottom())
            area.lineTo(pts[0].x(), rect.bottom())
            area.closeSubpath()
            fill = QLinearGradient(0, rect.top(), 0, rect.bottom())
            fill.setColorAt(0, color(tone, fill_alpha))
            fill.setColorAt(1, color(tone, 0))
            p.fillPath(area, fill)
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(color(tone, 46), 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(path)
            p.setPen(QPen(color(_mix(tone, '#ffffff', .35)), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(path)
            tip = pts[-1]
            halo = QRadialGradient(tip, 10)
            halo.setColorAt(0, color('#ffffff', 230))
            halo.setColorAt(.35, color(tone, 130))
            halo.setColorAt(1, color(tone, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(halo)
            p.drawEllipse(tip, 10, 10)

    def _paint_graph(self, p, rect, data):
        data = data or {}
        hist = data.get('history') or {}
        self._text(p, QRectF(rect.left() + 24, rect.top() + 16, 200, 20), self._tr('Auslastung').upper(), 11,
                   palette()['accent'], QFont.DemiBold, spacing=2.0)
        compact = rect.width() < 420
        legend_y = rect.top() + (36 if compact else 16)
        lx = rect.right() - 24
        for label, tone in reversed((('CPU', '#7fd6ff'), ('GPU', '#ff8bdc'), ('RAM', '#ffcb72'))):
            wlab = QFontMetrics(self._font(11, QFont.DemiBold)).horizontalAdvance(label)
            lx -= wlab
            self._text(p, QRectF(lx, legend_y, wlab + 2, 20), label, 11, tone, QFont.DemiBold)
            p.setPen(Qt.NoPen)
            p.setBrush(color(tone))
            p.drawEllipse(QPointF(lx - 9, legend_y + 10), 3.5, 3.5)
            lx -= 26
        area = QRectF(rect.left() + 26, rect.top() + (72 if compact else 52), rect.width() - 80, rect.height() - (102 if compact else 82))
        for i in range(5):
            y = area.top() + area.height() * i / 4
            p.setPen(QPen(color('#ffffff', 26), .7, Qt.DotLine))
            p.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
            self._text(p, QRectF(area.right() + 8, y - 8, 40, 16), f'{100 - 25 * i}%', 9, palette()['muted'])
        for key, tone in (('ram', '#ffcb72'), ('gpu', '#ff8bdc'), ('cpu', '#7fd6ff')):
            self._ribbon(p, area, hist.get(key) or [], tone, 70 if key == 'cpu' else 38)
        self._text(p, QRectF(area.left(), area.bottom() + 6, 60, 16), '−1m', 9, palette()['muted'])
        self._text(p, QRectF(area.right() - 60, area.bottom() + 6, 60, 16), self._tr('Jetzt'), 9,
                   palette()['muted'], QFont.Normal, Qt.AlignRight | Qt.AlignVCenter)

    def _paint_network(self, p, rect, data):
        net = (data or {}).get('net') or {}
        hist = (data or {}).get('history') or {}
        self._text(p, QRectF(rect.left() + 24, rect.top() + 16, rect.width() - 48, 20),
                   self._tr('Netzwerk').upper(), 11, palette()['accent'], QFont.DemiBold, spacing=2.0)
        self._text(p, QRectF(rect.left() + 24, rect.top() + 36, rect.width() - 48, 18), net.get('name', '–'), 10,
                   palette()['muted'])
        compact = rect.width() < 240
        half = (rect.width() - 48) / (1 if compact else 2)
        for i, (label, key, tone) in enumerate((('Download', 'down', '#7fd6ff'), ('Upload', 'up', '#ff8bdc'))):
            x = rect.left() + 24 + (0 if compact else i * half)
            y = rect.top() + 62 + (i * 60 if compact else 0)
            self._text(p, QRectF(x, y, half, 16), self._tr(label), 10, tone, QFont.DemiBold)
            self._text(p, QRectF(x, y + 18, half, 30), net.get(key, '–'), 18 if compact else 20, '#ffffff', QFont.DemiBold)
        start = 194 if compact else 122
        spark = QRectF(rect.left() + 24, rect.top() + start, rect.width() - 48, max(0,rect.height() - start - 54))
        for series, tone in ((hist.get('net_down') or [], '#7fd6ff'), (hist.get('net_up') or [], '#ff8bdc')):
            values = [v for v in series if v is not None]
            peak = max(values) if values else 0
            scaled = [None if v is None else (v / peak * 100 if peak > 0 else 0) for v in series]
            self._ribbon(p, spark, scaled, tone, 56)
        self._text(p, QRectF(rect.left() + 24, rect.bottom() - 40, rect.width() - 48, 18), net.get('total', ''), 10,
                   palette()['muted'])

    def _paint_drives(self, p, rect, data):
        data = data or {}
        self._text(p, QRectF(rect.left() + 24, rect.top() + 16, rect.width() - 48, 20),
                   self._tr('Systemzustand').upper(), 11, palette()['accent'], QFont.DemiBold, spacing=2.0)
        health = data.get('health') or {}
        score = health.get('score')
        ring = QRectF(rect.center().x()-31, rect.top() + 42, 62, 62)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(color('#ffffff', 30), 6, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(ring.adjusted(5, 5, -5, -5), 225 * 16, -270 * 16)
        if score is not None:
            tone = '#6bffd0' if score >= 70 else '#ffcb72' if score >= 45 else '#ff7a8a'
            arc = QConicalGradient(ring.center(), 225)
            arc.setColorAt(1, color('#ffffff'))
            arc.setColorAt(.5, color(tone))
            arc.setColorAt(0, color(tone))
            p.setPen(QPen(color(tone, 60), 11, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(ring.adjusted(5, 5, -5, -5), 225 * 16, round(-270 * 16 * max(0, min(100, score)) / 100))
            p.setPen(QPen(QBrush(arc), 5.5, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(ring.adjusted(5, 5, -5, -5), 225 * 16, round(-270 * 16 * max(0, min(100, score)) / 100))
        self._text(p, ring, _fmt_pct(score), 19, '#ffffff', QFont.DemiBold, Qt.AlignCenter)
        self._text(p, QRectF(rect.left()+24,ring.bottom()+6,rect.width()-48,20),
                   health.get('state', ''), 13, '#ffffff', QFont.DemiBold)
        self._text(p, QRectF(rect.left()+24,ring.bottom()+29,rect.width()-48,18),
                   health.get('detail', ''), 10, palette()['muted'])
        y = ring.bottom() + 58
        tones = (('#7fd6ff', '#2b6bff'), ('#ffcb72', '#ff6a3c'), ('#ff8bdc', '#a42cff'))
        for i, disk in enumerate((data.get('disks') or [])[:3]):
            if y + 40 > rect.bottom() - 14:
                break
            col_a, col_b = tones[i % 3]
            self._text(p,QRectF(rect.left()+24,y,rect.width()-48,16),f"{disk['mount']} · {disk['percent']:.0f}%",11,col_a,QFont.DemiBold)
            draw_tube(p, QRectF(rect.left() + 24, y + 19, rect.width() - 48, 15), disk['percent'] / 100,
                      col_a, col_b, 0.0, i)
            self._text(p, QRectF(rect.left() + 24, y + 35, rect.width() - 48, 14), disk['detail'], 9,
                       palette()['muted'])
            y += 56

    def event(self,event):
        from PySide6.QtCore import QEvent
        if event.type()==QEvent.ToolTip:
            from PySide6.QtWidgets import QToolTip
            text=next((text for rect,text in getattr(self,'_hint_regions',()) if rect.contains(event.pos())),None)
            if text:QToolTip.showText(event.globalPos(),text,self)
            else:QToolTip.hideText()
            event.accept();return True
        return super().event(event)

    def paintEvent(self, event):
        if self._dirty or self._static.isNull() or self._background()[2] != self._backdrop_key:
            self._rebuild()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawPixmap(0, 0, self._static)
        t = time.monotonic() - self._t0
        data = self._data or {}
        meta = self._sphere_meta
        for key, (centre, radius, col_a, col_b, index) in meta.items():
            info = data.get(key) or {}
            value = info.get('value')
            fraction = None if value is None else self._shown.get(key, value / 100)
            if value is not None and not self._animate():
                fraction = value / 100
            draw_sphere(p, centre, radius, fraction, col_a, col_b, t, index * 1.7,
                        self._blur, self._scale)
            size = max(18, int(radius * .46))
            shown = _fmt_pct(value)
            p.setFont(self._font(size, QFont.DemiBold))
            fm = QFontMetrics(p.font())
            text_rect = QRectF(centre.x() - radius, centre.y() - size * .75, radius * 2, size * 1.5)
            unit = '' if value is None else '%'
            number_w = fm.horizontalAdvance(shown)
            p.setFont(self._font(size * .5, QFont.DemiBold))
            unit_w = QFontMetrics(p.font()).horizontalAdvance(unit) + 3 if unit else 0
            start = centre.x() - (number_w + unit_w) / 2
            for dx, dy, tone in ((0, 2.2, QColor(0, 6, 30, 150)), (0, 0, QColor('#ffffff'))):
                p.setFont(self._font(size, QFont.DemiBold))
                p.setPen(tone)
                p.drawText(QRectF(start + dx, text_rect.top() + dy, number_w + 6, text_rect.height()),
                           Qt.AlignLeft | Qt.AlignVCenter, shown)
                if unit:
                    p.setFont(self._font(size * .5, QFont.DemiBold))
                    p.drawText(QRectF(start + number_w + 2 + dx, text_rect.top() + dy - size * .1,
                                      unit_w + 6, text_rect.height()), Qt.AlignLeft | Qt.AlignVCenter, unit)
            draw_sphere_glints(p, centre, radius, col_a)
        p.end()



def palette():
    from . import theme
    return theme.palette_for(KEY)
