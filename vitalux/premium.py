"""Three locally rendered glass collections, shared by all native backends.

The atmosphere is cached by the scene. Cards sample that same atmosphere;
only the small logo animates continuously, rather than repainting the window.
"""
import math

from PySide6.QtCore import QPointF, QRectF, Qt, QVariantAnimation, QEasingCurve
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QFont,
                           QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QRadialGradient)
from PySide6.QtWidgets import QAbstractButton, QSizePolicy

COLLECTIONS = {
    'obsidian_gold': {
        'title': 'Obsidian Gold', 'subtitle': 'SMOKED GLASS / BRUSHED GOLD',
        'bg': '#08090c', 'sidebar': '#0d0e12', 'card': '#16171c',
        'border': '#706044', 'track': '#35312a', 'grid': '#302e2d',
        'text': '#faf4e8', 'muted': '#b9afa0', 'accent': '#e5c17b',
        'secondary': '#fff0c8', 'light': '#c69b55', 'bloom': '#725435',
        'shadow': '#111726', 'series': ('#e5c17b', '#f7eed8', '#b18c56', '#9aa8b8'),
    },
    'champagne_glass': {
        'title': 'Champagne Glass', 'subtitle': 'CRYSTAL / CHAMPAGNE METAL',
        'bg': '#171719', 'sidebar': '#202023', 'card': '#302e30',
        'border': '#95877a', 'track': '#4e4640', 'grid': '#454047',
        'text': '#fff8ef', 'muted': '#cbc0b7', 'accent': '#f0d5ad',
        'secondary': '#fff6df', 'light': '#dfc7ac', 'bloom': '#a48e89',
        'shadow': '#393343', 'series': ('#f0d5ad', '#e4deef', '#c5a37f', '#a9c4ca'),
    },
    'aurora_gold': {
        'title': 'Aurora Gold', 'subtitle': 'IRIDESCENT GLASS / LIQUID GOLD',
        'bg': '#070d16', 'sidebar': '#0c1421', 'card': '#122132',
        'border': '#697079', 'track': '#26384a', 'grid': '#29394d',
        'text': '#f8f4ef', 'muted': '#adbdce', 'accent': '#ecc784',
        'secondary': '#a4e4e1', 'light': '#447f96', 'bloom': '#715486',
        'shadow': '#153e4b', 'series': ('#ecc784', '#9cddd8', '#bba5e5', '#f5e9cf'),
    },
}
from . import signature_designs
COLLECTIONS.update(signature_designs.COLLECTIONS)
KEYS = tuple(COLLECTIONS)


def palette(mode=None):
    if mode is None:
        from . import theme
        mode = theme.mode()
    return COLLECTIONS[mode]


def color(value, alpha=255):
    result = QColor(value)
    result.setAlpha(alpha)
    return result


def rounded(rect, radius):
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path


def scene_pixmap(size, mode):
    """Fixed geometry and soft light; independent of frame rate or sensors."""
    if mode in signature_designs.KEYS:
        return signature_designs.scene_pixmap(size,mode)
    pal = palette(mode)
    w, h = max(1, size.width()), max(1, size.height())
    pixmap = QPixmap(w, h)
    pixmap.fill(QColor(pal['bg']))
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(0, 0, w, h)
    base = QLinearGradient(0, 0, w, h)
    base.setColorAt(0, QColor(pal['shadow']))
    base.setColorAt(.48, QColor(pal['bg']))
    base.setColorAt(1, color(pal['sidebar']))
    p.fillRect(r, QBrush(base))
    for x, y, radius, tone, opacity in (
            (.12, -.08, .70, pal['light'], 100),
            (.96, .32, .63, pal['bloom'], 113),
            (.57, 1.08, .66, pal['shadow'], 200)):
        glow = QRadialGradient(QPointF(w*x, h*y), w*radius)
        glow.setColorAt(0, color(tone, opacity))
        glow.setColorAt(.48, color(tone, int(opacity*.40)))
        glow.setColorAt(1, color(tone, 0))
        p.fillRect(r, QBrush(glow))

    # Sculpted ribbons: several soft strokes under one polished light edge.
    for index in range(3):
        path = QPainterPath(QPointF(-w*.12, h*(.38+index*.29)))
        path.cubicTo(w*.16, -h*(.25-index*.11),
                     w*.62, h*(.98-index*.27), w*1.15, h*(.08+index*.28))
        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0, color(pal['accent'], 0))
        gradient.setColorAt(.22, color(pal['light'], 115 if index == 0 else 45))
        gradient.setColorAt(.56, color(pal['secondary'], 155 if index == 0 else 60))
        gradient.setColorAt(.85, color(pal['bloom'], 75))
        gradient.setColorAt(1, color(pal['accent'], 0))
        for width, opacity in ((46, .045), (22, .09), (8, .17), (1.1, .7)):
            p.setOpacity(opacity)
            p.setPen(QPen(QBrush(gradient), width, Qt.SolidLine, Qt.RoundCap))
            p.drawPath(path)
        p.setOpacity(1)

    # A satin, rather than noisy, finish. It is drawn once into the scene cache.
    p.setPen(QPen(color(pal['text'], 4), .6))
    for y in range(0, h, 5):
        p.drawLine(0, y, w, y)
    vignette = QRadialGradient(QPointF(w*.52, h*.34), max(w, h)*.85)
    vignette.setColorAt(0, QColor(0, 0, 0, 0))
    vignette.setColorAt(.65, QColor(0, 0, 0, 12))
    vignette.setColorAt(1, QColor(0, 0, 0, 135))
    p.fillRect(r, QBrush(vignette))
    p.end()
    return pixmap


def paint_panel(p, widget, rect, *, strong=False, compact=False, active=False):
    """Position-correct frost, smoked depth, inner bevel and metallic edge."""
    from . import theme
    if theme.mode() in signature_designs.KEYS:
        return signature_designs.paint_panel(p,widget,rect,strong=strong,compact=compact,active=active)
    from .glass import draw_frosted_backdrop
    pal = palette()
    radius = 12 if compact else 25 if strong else 21
    body = rounded(rect, radius)
    p.save()
    p.setClipPath(body)
    # Establish a readable fallback for detached dialogs and design thumbnails.
    p.fillPath(body, QBrush(color(pal['card'])))
    draw_frosted_backdrop(p, widget, rect)
    material = QLinearGradient(rect.topLeft(), rect.bottomRight())
    material.setColorAt(0, color(pal['card'], 185 if strong else 167))
    material.setColorAt(.45, color(pal['bg'], 215 if strong else 202))
    material.setColorAt(1, color(pal['card'], 210))
    p.fillPath(body, QBrush(material))
    # Broad reflected light is clipped to the material, not laid over text.
    refraction = QRadialGradient(rect.topLeft(), max(30, rect.width()*.90))
    refraction.setColorAt(0, color(pal['secondary'], 23 if strong else 14))
    refraction.setColorAt(.45, color(pal['light'], 7))
    refraction.setColorAt(1, color(pal['accent'], 0))
    p.fillPath(body, QBrush(refraction))
    sheen = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    sheen.setColorAt(0, QColor(255, 255, 255, 21))
    sheen.setColorAt(.13, QColor(255, 255, 255, 3))
    sheen.setColorAt(.6, QColor(255, 255, 255, 0))
    sheen.setColorAt(1, QColor(0, 0, 0, 23))
    p.fillPath(body, QBrush(sheen))
    if strong and not compact:
        reflection = QPainterPath()
        reflection.moveTo(rect.right()-rect.width()*.42, rect.top())
        reflection.lineTo(rect.right(), rect.top())
        reflection.lineTo(rect.right(), rect.bottom())
        reflection.lineTo(rect.right()-rect.width()*.17, rect.bottom())
        reflection.closeSubpath()
        p.fillPath(reflection, QBrush(color(pal['secondary'], 5)))
    p.restore()
    paint_edge(p, rect, radius, active=active, compact=compact)


def paint_edge(p, rect, radius, *, active=False, compact=False):
    pal = palette()
    path = rounded(rect, radius)
    edge = QLinearGradient(rect.topLeft(), rect.bottomRight())
    for position, tone, alpha in (
            (0, pal['secondary'], 125), (.18, pal['accent'], 90),
            (.40, pal['border'], 49), (.62, pal['accent'], 62),
            (.83, pal['border'], 38), (1, pal['secondary'], 82)):
        edge.setColorAt(position, color(tone, min(255, alpha+75) if active else alpha))
    p.setBrush(Qt.NoBrush)
    if active:
        p.setPen(QPen(color(pal['accent'], 21), 5))
        p.drawPath(path)
    p.setPen(QPen(QBrush(edge), 1.15 if active else .8))
    p.drawPath(path)
    inset = rect.adjusted(2, 2, -2, -2)
    p.setPen(QPen(QColor(255, 255, 255, 20), .7))
    p.drawPath(rounded(inset, max(2, radius-2)))
    gleam = QLinearGradient(rect.left(), 0, rect.right(), 0)
    gleam.setColorAt(0, color(pal['secondary'], 0))
    gleam.setColorAt(.17, color(pal['secondary'], 190 if active else 122))
    gleam.setColorAt(.46, color(pal['accent'], 50))
    gleam.setColorAt(1, color(pal['secondary'], 0))
    p.setPen(QPen(QBrush(gleam), 1, Qt.SolidLine, Qt.RoundCap))
    pad = min(radius, rect.width()*.2)
    p.drawLine(QPointF(rect.left()+pad, rect.top()+1),
               QPointF(rect.right()-pad, rect.top()+1))


def paint_sidebar(p, widget, rect):
    from . import theme
    if theme.mode() in signature_designs.KEYS:
        return signature_designs.paint_panel(p,widget,rect.adjusted(1,1,-1,-1),strong=True)
    from .glass import draw_frosted_backdrop
    pal = palette()
    p.fillRect(rect, color(pal['sidebar']))
    draw_frosted_backdrop(p, widget, rect)
    shade = QLinearGradient(rect.topLeft(), rect.bottomRight())
    shade.setColorAt(0, color(pal['sidebar'], 208))
    shade.setColorAt(.45, color(pal['bg'], 232))
    shade.setColorAt(1, color(pal['sidebar'], 224))
    p.fillRect(rect, QBrush(shade))
    seam = QLinearGradient(0, 0, 0, rect.height())
    seam.setColorAt(0, color(pal['secondary'], 10))
    seam.setColorAt(.20, color(pal['accent'], 160))
    seam.setColorAt(.60, color(pal['accent'], 35))
    seam.setColorAt(1, color(pal['secondary'], 0))
    p.setPen(QPen(QBrush(seam), 1))
    p.drawLine(QPointF(rect.right()-1, 0), QPointF(rect.right()-1, rect.bottom()))


def paint_nav(p, widget, rect, selected, hover):
    if selected:
        paint_panel(p, widget, rect, compact=True, active=True)
    elif hover > .01:
        pal = palette()
        p.setPen(QPen(color(pal['accent'], round(35*hover)), .8))
        p.setBrush(color(pal['accent'], round(12*hover)))
        p.drawRoundedRect(rect, 12, 12)


def paint_gauge(p, widget, value, text, ring_color):
    pal = palette()
    side = min(widget.width(), widget.height())
    center = QPointF(widget.width()/2, widget.height()/2)
    diameter = side*.78
    rect = QRectF(center.x()-diameter/2, center.y()-diameter/2, diameter, diameter)
    lens = QRadialGradient(center-QPointF(side*.12, side*.16), side*.51)
    lens.setColorAt(0, color(pal['secondary'], 9))
    lens.setColorAt(.58, color(pal['card'], 90))
    lens.setColorAt(1, color(pal['bg'], 170))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(lens))
    p.drawEllipse(rect.adjusted(5, 5, -5, -5))
    for tick in range(61):
        angle = math.radians(225-tick*4.5)
        major = tick % 5 == 0
        outer = side*.48
        inner = outer-(7 if major else 3)
        p.setPen(QPen(color(pal['accent'], 140 if major else 45), 1))
        p.drawLine(center+QPointF(math.cos(angle)*inner, -math.sin(angle)*inner),
                   center+QPointF(math.cos(angle)*outer, -math.sin(angle)*outer))
    width = max(4, side*.027)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color(pal['track']), width, Qt.SolidLine, Qt.RoundCap))
    p.drawArc(rect, 225*16, -270*16)
    inset = rect.adjusted(7, 7, -7, -7)
    p.setPen(QPen(color(pal['accent'], 28), .7))
    p.drawArc(inset, 225*16, -270*16)
    if value is not None:
        value = min(100, max(0, value))
        span = round(-270*16*value/100)
        p.setPen(QPen(color(ring_color, 24), width*3.4, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 225*16, span)
        gold = QConicalGradient(center, 90)
        gold.setColorAt(0, QColor(ring_color))
        gold.setColorAt(.3, color(pal['secondary']))
        gold.setColorAt(.6, QColor(ring_color))
        gold.setColorAt(1, color(pal['accent']))
        p.setPen(QPen(QBrush(gold), width, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 225*16, span)
        angle = math.radians(225-270*value/100)
        dot = center+QPointF(math.cos(angle)*diameter/2, -math.sin(angle)*diameter/2)
        p.setPen(Qt.NoPen)
        p.setBrush(color(pal['secondary']))
        p.drawEllipse(dot, width*.62, width*.62)
    font = QFont(widget.font())
    font.setFamilies(['DejaVu Sans Mono', 'Noto Sans Mono', 'monospace'])
    font.setPixelSize(round(side*.23))
    font.setWeight(QFont.DemiBold)
    p.setFont(font)
    p.setPen(color(pal['text']))
    shown = text if text is not None else ('–' if widget.value is None else f'{widget.value:.0f}%')
    p.drawText(rect, Qt.AlignCenter, shown)


def stylesheet(mode):
    if mode in signature_designs.KEYS:
        return signature_designs.stylesheet(mode)
    pal = palette(mode)
    return f'''
    #pageTitle {{ font-size: 30px; font-weight: 500; }}
    #heroTitle {{ font-size: 23px; font-weight: 500; color: {pal['text']}; }}
    #cardTitle {{ color: {pal['accent']}; font-size: 10px; font-weight: 600; letter-spacing: 1.8px; }}
    #chipTitle {{ color: {pal['muted']}; font-size: 10px; }}
    #chipValue {{ color: {pal['text']}; font-size: 13px; font-weight: 600; }}
    #telemetryValue {{ color: {pal['text']}; font-weight: 400; }}
    #sidebarDistro {{ color: {pal['muted']}; font-size: 10px; letter-spacing: 1px; }}
    QToolTip {{ background: {pal['sidebar']}; color: {pal['text']}; border: 1px solid {pal['border']}; padding: 8px; }}
    QLineEdit, QComboBox, QSpinBox, QTextEdit, QListWidget {{
        background: {pal['sidebar']}; border: 1px solid {pal['border']}; border-radius: 10px; }}
    QComboBox QAbstractItemView {{ background: {pal['card']}; }}
    QComboBox:disabled, QPushButton:disabled {{ color: {pal['muted']}; border-color: {pal['grid']}; }}
    #primaryBtn {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {pal['secondary']},stop:0.5 {pal['accent']},stop:1 {pal['border']});
        border: 1px solid {pal['accent']}; color: #17130d; border-radius: 12px; }}
    #ghostBtn, #langBtn {{ background: {pal['sidebar']}; border-color: {pal['border']}; border-radius: 10px; }}
    QScrollBar:vertical {{ width: 7px; }}
    QScrollBar::handle:vertical {{ background: {pal['border']}; border-radius: 3px; }}
    '''


class DesignTile(QAbstractButton):
    """Native keyboard-accessible selectors with locally painted miniatures."""
    def __init__(self, key, parent=None):
        super().__init__(parent)
        self.key = key
        self._keyboard_focus=False
        self.setProperty('vitaluxCapabilityHints',True)
        from . import theme
        self.retranslate()
        self.setAccessibleName(self.text())
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(125)
        self.setFixedHeight(112)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._background_key = None
        self._background = QPixmap()
        self._hover = 0.0
        self._hover_animation = QVariantAnimation(self)
        self._hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._hover_animation.valueChanged.connect(self._hover_frame)

    def _hover_frame(self, value):
        self._hover = float(value)
        self.update()

    def _hover_to(self, value):
        from . import motion
        self._hover_animation.stop()
        duration = motion.duration(220)
        if not duration:
            self._hover_frame(value)
            return
        self._hover_animation.setDuration(duration)
        self._hover_animation.setStartValue(self._hover)
        self._hover_animation.setEndValue(float(value))
        self._hover_animation.start()

    def enterEvent(self, event):
        self._hover_to(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_to(1.0 if self._keyboard_focus else 0.0)
        super().leaveEvent(event)

    def focusInEvent(self,event):
        self._keyboard_focus=event.reason() in (Qt.TabFocusReason,Qt.BacktabFocusReason,Qt.ShortcutFocusReason)
        if self._keyboard_focus:self._hover_to(1.)
        super().focusInEvent(event)

    def focusOutEvent(self,event):
        self._keyboard_focus=False
        if not self.underMouse():self._hover_to(0.)
        super().focusOutEvent(event)

    def mousePressEvent(self,event):
        self._hover_to(1.)
        super().mousePressEvent(event)

    def retranslate(self):
        from . import theme
        from .i18n import tr
        self.setText(tr(dict(theme.CHOICES)[self.key]))
        self.setAccessibleName(self.text())
        from .design_capabilities import description
        self.setToolTip(description(self.key))
        self.setAccessibleDescription(description(self.key))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        # Paint the zoom inside a stable hit box; neighbouring tiles never move.
        scale = .975+.025*self._hover
        p.translate(self.width()/2, self.height()/2)
        p.scale(scale, scale)
        p.translate(-self.width()/2, -self.height()/2)
        from . import theme, backdrops
        pal = (palette(self.key) if self.key in KEYS else
               dict(theme._THEMES[self.key], accent='#f3cd79' if self.key == 'black_glass_gold'
                    else '#52d3ff' if self.key == 'holographic' else '#4f8cff'))
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        path = rounded(rect, 12)
        p.setClipPath(path)
        background_key = (self.size(), pal['accent'])
        if self._background_key != background_key:
            if self.key in KEYS:
                self._background = scene_pixmap(self.size(), self.key)
            elif self.key == 'holographic':
                from .holographic import scene_pixmap as hologram
                self._background = hologram(self.size(), pal['accent'])
            elif self.key in ('glass', 'black_glass', 'black_glass_gold'):
                from pathlib import Path
                filename = 'glass-atmosphere.jpg' if self.key == 'glass' else 'black-glass-atmosphere.jpg'
                source = QPixmap(str(Path(__file__).resolve().parents[1]/'assets'/filename))
                self._background = source.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            else:
                self._background = backdrops.render(self.size(),
                    'black_glass' if self.key == 'black_glass_gold' else self.key,
                    pal['accent'], self.key == 'light')[0]
            self._background_key = background_key
        p.drawPixmap(0, 0, self._background)
        if self.key in signature_designs.KEYS:
            signature_designs.paint_preview(p,self,pal)
            from .design_capabilities import paint
            paint(p,self,pal,self._hover)
            p.end()
            return
        if self._hover > .01:
            p.fillPath(path, QBrush(color(pal['accent'], round(13*self._hover))))
        p.fillRect(QRectF(0, 0, 24, 75), color(pal['bg'], 220))
        for y in (15, 26, 37, 48):
            p.setPen(QPen(color(pal['accent'], 130), 2))
            p.drawLine(9, y, 15, y)
        p.setPen(QPen(color(pal['accent'], 100), .7))
        p.setBrush(color(pal['card'], 190))
        p.drawRoundedRect(QRectF(33, 10, max(5, self.width()-44), 19), 4, 4)
        width = max(12, (self.width()-54)/3)
        for i in range(3):
            box = QRectF(33+i*(width+5), 35, width, 30)
            p.setBrush(color(pal['card'], 190))
            p.drawRoundedRect(box, 5, 5)
            p.setPen(QPen(color(pal['accent'], 215), 1.5))
            diameter = min(box.width()-8, box.height()-8)
            dial = QRectF(box.center().x()-diameter/2, box.center().y()-diameter/2,
                          diameter, diameter)
            p.drawArc(dial, 225*16, -220*16)
            p.setPen(QPen(color(pal['accent'], 100), .7))
        p.fillRect(QRectF(0, 75, self.width(), 40), color(pal['bg'], 225))
        font = QFont(self.font())
        font.setPixelSize(11)
        font.setWeight(QFont.DemiBold)
        p.setFont(font)
        p.setPen(color(pal['text']))
        p.drawText(QRectF(10, 78, self.width()-20, 27), Qt.AlignCenter, self.text())
        p.setClipping(False)
        from .design_capabilities import paint
        paint(p,self,pal,self._hover)
        p.setBrush(Qt.NoBrush)
        if self.isChecked():
            p.setPen(Qt.NoPen)
            p.setBrush(color(pal['accent']))
            p.drawEllipse(QPointF(self.width()-15, 14), 7, 7)
            p.setPen(QPen(color(pal['bg']), 1.5, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(self.width()-18, 14), QPointF(self.width()-16, 16))
            p.drawLine(QPointF(self.width()-16, 16), QPointF(self.width()-12, 12))
        selected = self.isChecked() or self.hasFocus()
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(color(pal['accent'], 240 if selected else round(75+100*self._hover)), 2 if selected else 1))
        p.drawPath(path)
        p.end()
