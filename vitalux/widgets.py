import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QBrush, QColor, QConicalGradient, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
from .ui_locale import QLabel, QPushButton, QComboBox, QCheckBox, paint_check_indicator

from . import theme, motion, premium
from .glass import GlassSurface, paint_glass_body, rgba
from .i18n import tr
from .nav_icons import GLYPHS, paint_icon


def label(text="", name=None, align=None, wrap=False):
    l = QLabel(tr(text))
    if name:
        l.setObjectName(name)
    if name in ('chipValue', 'telemetryValue'):
        font = l.font()
        font.setFamilies(['DejaVu Sans Mono', 'Noto Sans Mono', 'monospace'])
        l.setFont(font)
    if align:
        l.setAlignment(align)
    l.setWordWrap(wrap)
    return l


def _glass_shadow(widget, blur=30, y=8, alpha=44):
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(blur)
    fx.setOffset(0, y)
    c = QColor(0, 0, 0)
    c.setAlpha(alpha)
    fx.setColor(c)
    widget.setGraphicsEffect(fx)


class Card(GlassSurface):
    def __init__(self, title=None, hero=False):
        super().__init__(hero=hero)
        _glass_shadow(self, 26 if hero else 18, 6 if hero else 3, 42 if hero else 27)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 18)
        lay.setSpacing(12)
        if title:
            lay.addWidget(label(title.upper(), "cardTitle"))
        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        lay.addLayout(self.body)


class StatChip(GlassSurface):
    def __init__(self, title, value="–"):
        super().__init__(compact=True)
        _glass_shadow(self, 12, 2, 18)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)
        lay.addWidget(label(title, "chipTitle", wrap=True))
        self.value = label(value, "chipValue", wrap=True)
        lay.addWidget(self.value)

    def set(self, value):
        self.value.setText(tr(value))
        self.value.setToolTip(tr(value))


class ChipsGrid(QWidget):
    def __init__(self, titles, columns=4):
        super().__init__()
        self.columns = columns
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(10)
        self.chips = {}
        for i, t in enumerate(titles):
            chip = StatChip(t)
            self.chips[t] = chip
            self.grid.addWidget(chip, i // columns, i % columns)

    def set(self, title, value):
        if title in self.chips:
            self.chips[title].set(value)


class Bar(QWidget):
    def __init__(self):
        super().__init__()
        self.value = 0.0
        self.flat = False
        self.custom_color = None
        self.setFixedHeight(8)

    def set_value(self, v):
        self.value = 0.0 if v is None else max(0.0, min(100.0, v))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        if theme.mode() == 'minimal':
            p.fillRect(self.rect(), QColor(theme.TRACK))
            p.fillRect(0, 0, round(self.width()*self.value/100.0), self.height(),
                       QColor(self.custom_color or theme.level_color(self.value)))
            p.end()
            return
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(QPen(QColor(theme.BORDER), 1))
        base = QColor(theme.TRACK)
        if theme.mode() == "light":
            base.setAlpha(95)
        else:
            base.setAlpha(80)
        p.setBrush(base)
        p.drawRoundedRect(r, 4, 4)
        w = r.width() * self.value / 100
        if w > 0:
            p.setBrush(QColor(self.custom_color or (theme.accent() if self.flat else theme.level_color(self.value))))
            p.drawRoundedRect(QRectF(0, 0, max(w, 8), r.height()), 4, 4)


class Meter(QWidget):
    def __init__(self, text):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        row = QHBoxLayout()
        self.name = label(text, "muted")
        self.value = label("–", "strong", Qt.AlignRight)
        row.addWidget(self.name)
        row.addStretch(1)
        row.addWidget(self.value)
        lay.addLayout(row)
        self.bar = Bar()
        lay.addWidget(self.bar)

    def set(self, pct, text=None):
        self.bar.set_value(pct)
        self.value.setText(tr(text) if text is not None else ("–" if pct is None else f"{pct:.0f}%"))


class KeyValue(QWidget):
    def __init__(self, key):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)
        lay.addWidget(label(key, "muted"))
        lay.addStretch(1)
        self.v = label("–", "strong", Qt.AlignRight, wrap=True)
        self.v.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self.v, 1)

    def set(self, text):
        self.v.setText(tr(text))


class Gauge(QWidget):
    def __init__(self):
        super().__init__()
        self.value = None
        self._render_value = None
        self._target = None
        self.text = None
        self.semantic = 'load'
        font = self.font()
        font.setFamilies(['DejaVu Sans Mono', 'Noto Sans Mono', 'monospace'])
        self.setFont(font)
        self._animate = QTimer(self)
        self._animate.setInterval(25)
        self._animate.timeout.connect(self._tick)
        self.setMinimumSize(130, 130)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_semantic(self, semantic):
        self.semantic = semantic or 'load'
        self.update()

    def _ring_color(self, value):
        if self.semantic == 'score':
            if value is None or value >= 86:
                return theme.accent()
            if value >= 66:
                return theme.WARN
            return theme.CRIT
        return theme.level_color(value)

    def set(self, value, text=None):
        self.text = text
        self.value = value
        self._target = value
        if theme.mode() == "minimal" or not self.isVisible():
            self._animate.stop()
            self._render_value = value
            self.update()
            return
        if value is None:
            self._render_value = None
            self._animate.stop()
            self.update()
            return
        if self._render_value is None:
            self._render_value = 0.0
        self._animate.start()

    def _tick(self):
        if self._render_value is None or self._target is None:
            self._animate.stop()
            return
        self._render_value += (self._target - self._render_value) * 0.32
        if abs(self._render_value - self._target) < 0.15:
            self._render_value = self._target
            self._animate.stop()
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        if theme.mode() == 'minimal':
            shown = self.text if self.text is not None else (
                '–' if self.value is None else f'{self.value:.0f}%')
            font = QFont(self.font())
            font.setBold(True)
            font.setPixelSize(max(16, min(self.width(), self.height()) // 6))
            p.setFont(font)
            p.setPen(QColor(theme.TEXT))
            p.drawText(self.rect(), Qt.AlignCenter, shown)
            p.end()
            return
        p.setRenderHint(QPainter.Antialiasing)
        if theme.mode() in premium.KEYS:
            value = self._render_value
            premium.paint_gauge(p, self, value, self.text,
                                self._ring_color(value or 0))
            p.end()
            return
        side = min(self.width(), self.height())
        pen_w = max(9.0, side * 0.08)
        rect = QRectF((self.width() - side) / 2 + pen_w / 2, (self.height() - side) / 2 + pen_w / 2,
                      side - pen_w, side - pen_w)
        p.setPen(QPen(QColor(theme.TRACK), pen_w, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 225 * 16, -270 * 16)
        if self._render_value is not None:
            v = max(0.0, min(100.0, self._render_value))
            ring_color = self._ring_color(v)
            glow = QColor(ring_color)
            glow.setAlpha(35)
            p.setPen(QPen(glow, pen_w * 1.75, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, 225 * 16, int(-270 * 16 * v / 100))
            grad = QConicalGradient(rect.center(), 90)
            grad.setColorAt(0, QColor(ring_color))
            grad.setColorAt(0.7, QColor(theme.secondary_accent()))
            grad.setColorAt(1, QColor(ring_color))
            p.setPen(QPen(QBrush(grad), pen_w, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, 225 * 16, int(-270 * 16 * v / 100))
        font = QFont(self.font())
        font.setPixelSize(int(side * 0.22))
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor(theme.TEXT))
        shown = self.text if self.text is not None else ("–" if self.value is None else f"{self.value:.0f}%")
        p.drawText(rect, Qt.AlignCenter, shown)


from .overview_text import ElidedLabel

class GaugeCaption(ElidedLabel):
    """Bounded model name; the complete name remains available on hover."""
    pass


class GaugeBox(QWidget):
    def __init__(self, title=None, compact_caption=False, gauge_semantic='load'):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self.gauge = Gauge()
        self.gauge.set_semantic(gauge_semantic)
        lay.addWidget(self.gauge, 1)
        if title:
            lay.addWidget(label(title, "gaugeTitle", Qt.AlignHCenter))
        self.sub = GaugeCaption() if compact_caption else label("", "muted", Qt.AlignHCenter, wrap=True)
        lay.addWidget(self.sub)

    def set(self, value, sub="", text=None):
        self.gauge.set(value, text)
        if isinstance(self.sub, GaugeCaption):
            self.sub.set_caption(sub)
        else:
            self.sub.setText(tr(sub))


class GaugeCard(Card):
    def __init__(self, title, compact_caption=False, gauge_semantic='load'):
        super().__init__(title)
        self.box = GaugeBox(compact_caption=compact_caption, gauge_semantic=gauge_semantic)
        self.body.addWidget(self.box)

    def set(self, value, sub="", text=None):
        self.box.set(value, sub, text)


class HistoryGraph(QWidget):
    def __init__(self, maxlen=60, mode="percent"):
        super().__init__()
        self.maxlen, self.mode = maxlen, mode
        self.series, self.series_names, self.series_styles = [], [], []
        self.sample_times = []
        self.horizon_seconds = 60
        self._pointer = None
        self.setMouseTracking(True)
        self.setMinimumHeight(185)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_series(self, series):
        self.series = series
        self.update()

    def mouseMoveEvent(self, event):
        self._pointer = event.position().x()
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._pointer = None
        self.update()
        super().leaveEvent(event)

    def _format(self, value):
        if value is None or not math.isfinite(float(value)):
            return '–'
        if self.mode == 'percent': return f'{value:.0f}%'
        if self.mode == 'temperature': return f'{value:.1f} °C'
        if self.mode == 'clock': return f'{value:.0f} MHz'
        from .sensors import fmt_rate
        return fmt_rate(value)

    def _x(self, index, count, rect):
        if self.sample_times and len(self.sample_times) >= count:
            timestamp = self.sample_times[-count+index]
            fraction = 1-(self.sample_times[-1]-timestamp)/max(1, self.horizon_seconds)
        else:
            fraction = 1-(count-1-index)/max(1, self.maxlen-1)
        return rect.left()+max(0, min(1, fraction))*rect.width()

    def hover_readout(self, rect):
        if self._pointer is None or not rect.left() <= self._pointer <= rect.right():
            return []
        count = max((len(values) for values, _ in self.series), default=0)
        if not count:
            return []
        index = min(range(count), key=lambda i: abs(self._x(i, count, rect)-self._pointer))
        if len(self.sample_times) >= count:
            from datetime import datetime
            stamp = datetime.fromtimestamp(self.sample_times[-count+index]).strftime('%H:%M:%S')
        else:
            stamp = f'−{round((count-1-index)*self.horizon_seconds/max(1, self.maxlen-1))} s'
        lines = [stamp]
        for number, (values, _color) in enumerate(self.series):
            offset = index-(count-len(values))
            name = self.series_names[number] if number < len(self.series_names) else str(number+1)
            value = values[offset] if 0 <= offset < len(values) else None
            lines.append(f'{tr(name)}  {self._format(value)}')
        return lines

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        outer = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        minimal = theme.mode() == 'minimal'
        if theme.mode() in premium.KEYS:
            premium.paint_panel(p, self, outer, compact=True)
        else:
            fill = QColor(theme.CARD)
            fill.setAlpha(255 if minimal else 160)
            p.setBrush(fill)
            p.setPen(QPen(QColor(theme.BORDER), .75))
            p.drawRoundedRect(outer, 0 if minimal else 13, 0 if minimal else 13)
        rect = outer.adjusted(10, 14, -65, -30)
        if rect.width() <= 8 or rect.height() <= 8:
            p.end()
            return
        largest = max((float(value) for values, _ in self.series
                       for value in values if value is not None and math.isfinite(float(value))), default=0)
        if self.mode == 'percent':
            upper = 100.0
        elif self.mode == 'rate':
            raw = max(1024.0, largest*1.15)
            step = 10**math.floor(math.log10(raw))
            upper = max(1024.0, math.ceil(raw/step*2)/2*step)
        else:
            upper = max(10.0, largest*1.18)
        font = self.font()
        font.setPointSize(8)
        p.setFont(font)
        for fraction in (0, .25, .5, .75, 1):
            y = rect.bottom()-fraction*rect.height()
            grid = QColor(theme.GRID)
            grid.setAlpha(150)
            p.setPen(QPen(grid, .7))
            p.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            p.setPen(QColor(theme.MUTED))
            p.drawText(QRectF(rect.right()+6, y-10, 58, 20), Qt.AlignLeft | Qt.AlignVCenter,
                       self._format(upper*fraction))
        for fraction in (.25, .5, .75):
            p.setPen(QPen(QColor(theme.GRID), .6, Qt.DotLine))
            x = rect.left()+rect.width()*fraction
            p.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
        for fraction in (0, .5, 1):
            seconds = round(self.horizon_seconds*(1-fraction))
            stamp = tr('Jetzt') if not seconds else (f'−{seconds//60}m' if seconds % 60 == 0 else f'−{seconds}s')
            x = rect.left()+fraction*rect.width()
            align = Qt.AlignLeft if fraction == 0 else Qt.AlignRight if fraction == 1 else Qt.AlignHCenter
            p.setPen(QColor(theme.MUTED))
            p.drawText(QRectF(x-(0 if fraction == 0 else 29), rect.bottom()+6, 58, 20), align, stamp)
        any_data = False
        for number, (values, color) in enumerate(self.series):
            values = list(values)[-self.maxlen:]
            runs, run = [], []
            for index, value in enumerate(values):
                if value is None or not math.isfinite(float(value)):
                    if run: runs.append(run)
                    run = []
                    continue
                any_data = True
                y = rect.bottom()-min(1, max(0, float(value)/upper))*rect.height()
                run.append(QPointF(self._x(index, len(values), rect), y))
            if run: runs.append(run)
            style = self.series_styles[number] if number < len(self.series_styles) else Qt.SolidLine
            c = QColor(color)
            for points in runs:
                stride = max(1, len(points)//400)
                points = points[::stride]+([points[-1]] if (len(points)-1) % stride else [])
                path = QPainterPath(points[0])
                for previous, current in zip(points, points[1:]):
                    if minimal:
                        path.lineTo(current)
                    else:
                        dx = current.x()-previous.x()
                        path.cubicTo(previous+QPointF(dx*.36, 0), current-QPointF(dx*.36, 0), current)
                if not minimal:
                    area = QPainterPath(path)
                    area.lineTo(points[-1].x(), rect.bottom())
                    area.lineTo(points[0].x(), rect.bottom())
                    area.closeSubpath()
                    gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                    top, bottom = QColor(c), QColor(c)
                    top.setAlpha(51 if number else 68); bottom.setAlpha(0)
                    gradient.setColorAt(0, top); gradient.setColorAt(1, bottom)
                    p.fillPath(area, gradient)
                    halo = QColor(c); halo.setAlpha(39)
                    p.setBrush(Qt.NoBrush)
                    p.setPen(QPen(halo, 5, style, Qt.RoundCap, Qt.RoundJoin))
                    p.drawPath(path)
                p.setBrush(Qt.NoBrush)
                p.setPen(QPen(c, 1.8, style, Qt.RoundCap, Qt.RoundJoin))
                p.drawPath(path)
            if values and values[-1] is not None and runs:
                p.setBrush(c); p.setPen(Qt.NoPen)
                p.drawEllipse(runs[-1][-1], 2.5, 2.5)
        if not any_data:
            p.setPen(QColor(theme.MUTED))
            p.drawText(rect, Qt.AlignCenter, tr('Noch keine Messwerte verfügbar'))
        lines = self.hover_readout(rect)
        if lines:
            p.setPen(QPen(QColor(theme.MUTED), .8, Qt.DashLine))
            p.drawLine(QPointF(self._pointer, rect.top()), QPointF(self._pointer, rect.bottom()))
            width = min(rect.width()-10, max(p.fontMetrics().horizontalAdvance(line) for line in lines)+24)
            box = QRectF(min(rect.right()-width-5, max(rect.left()+5, self._pointer+10)),
                         rect.top()+5, width, 20*len(lines)+12)
            p.setBrush(QColor(theme.CARD)); p.setPen(QPen(QColor(theme.BORDER), .8))
            p.drawRoundedRect(box, 8, 8)
            for index, line in enumerate(lines):
                p.setPen(QColor(theme.MUTED if index == 0 else theme.TEXT))
                p.drawText(box.adjusted(10, 6+index*20, -8, 0), Qt.AlignLeft | Qt.AlignTop, line)
        p.end()


class ChartSeriesCheckBox(QCheckBox):
    """Outlined, theme-aware chart-series selector (no solid checked fill).

    We paint the check ourselves: Qt stylesheet backgrounds replace the native
    indicator on some Linux styles and otherwise hide the tick. This renders a
    crisp tick and an empty unchecked square in the active Vitalux design. The localized QCheckBox base keeps keyboard handling.
    """
    def __init__(self, name, color, parent=None):
        super().__init__(name, parent)
        self.setProperty('selectionControl',True)
        self.series_color = color
        self.setMinimumHeight(24)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def set_series_color(self, color):
        self.series_color = color
        self.update()

    def sizeHint(self):
        font = QFont(self.font())
        font.setBold(True)
        metrics = QFontMetrics(font)
        return QSize(metrics.horizontalAdvance(self.text()) + 32,
                     max(24, metrics.height()+6))

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        side = 15.0
        x, y = 2.0, (self.height()-side)/2
        r = QRectF(x, y, side, side)
        if not self.isEnabled():
            p.setOpacity(.45)
        paint_check_indicator(p, r, self.isChecked(), self.underMouse(), self.hasFocus())
        font = QFont(self.font())
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor(self.series_color))
        p.drawText(QRectF(x + side + 8, 0, max(0, self.width() - side - x - 10), self.height()),
                   Qt.AlignLeft | Qt.AlignVCenter, self.text())
        p.end()


class ChartPanel(QWidget):
    """History chart with 1/5/15min selection and per-series visibility toggles."""
    def __init__(self, series_names, colors, mode="percent"):
        super().__init__()
        self.series_names = list(series_names)
        self.colors = list(colors)
        self.color_roles = ["accent" if c.lower() == theme.accent().lower() else
                            "secondary" if c.lower() == theme.secondary_accent().lower() else
                            "teal" if c.lower() == theme.TEAL.lower() else "fixed"
                            for c in colors]
        self._source = []
        self.sample_interval = 1
        self._timestamps = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(10)
        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.time_range = QComboBox()
        for label_, secs in (("60 s", 60), ("5 min", 300), ("15 min", 900)):
            self.time_range.addItem(label_, secs)
        self.time_range.currentIndexChanged.connect(self._update)
        controls.addWidget(self.time_range)
        self.toggles = []
        self.live_labels = []
        for idx, name in enumerate(self.series_names):
            # Apply the current theme immediately. The old initial color
            # leaked teal into the RAM legend on Black Glass Gold until retheme().
            cb = ChartSeriesCheckBox(name, self._palette_color(idx))
            cb.setChecked(True)
            cb.toggled.connect(self._update)
            controls.addWidget(cb)
            self.toggles.append(cb)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.graph = HistoryGraph(mode=mode)
        layout.addWidget(self.graph)
        # Values are real samples, not decoration; unavailable data is shown as dashes.
        live = QHBoxLayout()
        live.setSpacing(10)
        for name in self.series_names:
            item = label(f"{name}  –", "muted")
            item.setToolTip(tr("Aktueller Wert / Minimum / Maximum im ausgewählten Zeitraum"))
            self.live_labels.append(item)
            live.addWidget(item)
        live.addStretch()
        layout.addLayout(live)

    def _palette_color(self, idx):
        if theme.mode() in premium.KEYS:
            return premium.palette()['series'][idx % 4]
        role = self.color_roles[idx]
        if role == 'accent': return theme.accent()
        if role == 'secondary': return theme.secondary_accent()
        if role == 'teal': return theme.TEAL
        return self.colors[idx]

    def retheme(self):
        for idx, cb in enumerate(self.toggles):
            cb.set_series_color(self._palette_color(idx))
        self._update()

    def set_series(self, series):
        self._source = series
        self._update()

    def set_timeline(self, timestamps):
        self._timestamps = list(timestamps)

    def set_interval(self, interval):
        new_interval = max(1, int(interval))
        if self.sample_interval == new_interval:
            return
        self.sample_interval = new_interval
        self._update()

    def _update(self, *_):
        horizon = self.time_range.currentData() or 60
        count = max(2, round(horizon/self.sample_interval))
        if self._timestamps:
            cutoff = self._timestamps[-1]-horizon
            count = max(2, sum(stamp >= cutoff for stamp in self._timestamps))
        self.graph.sample_times = self._timestamps[-count:]
        self.graph.series_names = []
        self.graph.series_styles = []
        self.graph.maxlen = count
        self.graph.horizon_seconds = horizon
        active = []
        for i, (values, _color) in enumerate(self._source):
            if i >= len(self.toggles):
                continue
            color = self._palette_color(i)
            self.live_labels[i].setStyleSheet(f'color: {color}; font-weight: 700;')
            if not self.toggles[i].isChecked():
                self.live_labels[i].setText('')
                self.live_labels[i].hide()
                continue
            vals = [float(v) for v in list(values)[-count:] if v is not None]
            if vals:
                from .sensors import fmt_rate
                if self.graph.mode == "percent":
                    fmt = lambda value: f"{value:.0f}%"
                elif self.graph.mode == "temperature":
                    fmt = lambda value: f"{value:.1f} °C"
                elif self.graph.mode == "clock":
                    fmt = lambda value: f"{value:.0f} MHz"
                else:
                    fmt = fmt_rate
                current = list(values)[-1] if values else None
                shown = fmt(current) if current is not None else '–'
                self.live_labels[i].setText(f'{tr(self.series_names[i])} {shown}  ·  {fmt(min(vals))}–{fmt(max(vals))}')
                self.live_labels[i].setToolTip(f'{tr(self.series_names[i])}: {tr("Jetzt")} {shown} | Min {fmt(min(vals))} | Max {fmt(max(vals))}')
            else:
                self.live_labels[i].setText(f'{tr(self.series_names[i])} –')
            self.live_labels[i].show()
            recent = list(values)[-count:]
            active.append((recent, color))
            self.graph.series_names.append(self.series_names[i])
            self.graph.series_styles.append((Qt.SolidLine, Qt.DashLine, Qt.DotLine)[i % 3])
        self.graph.set_series(active)


class _SoftHover:
    """A tiny scalar animation – no layouts or surfaces are repainted indirectly."""

    def _init_soft_hover(self):
        self._hover_amount = 0.0
        self._hover_motion = QVariantAnimation(self)
        self._hover_motion.setEasingCurve(QEasingCurve.InOutCubic)
        self._hover_motion.valueChanged.connect(self._hover_frame)

    def _hover_frame(self, value):
        self._hover_amount = max(0.0, min(1.0, float(value)))
        self.update()

    def _set_hover(self, value):
        self._hover_motion.stop()
        ms = motion.duration(155)
        if not ms:
            self._hover_frame(value)
            return
        self._hover_motion.setDuration(ms)
        self._hover_motion.setStartValue(self._hover_amount)
        self._hover_motion.setEndValue(float(value))
        self._hover_motion.start()

    def enterEvent(self, event):
        self._set_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._set_hover(0.0)
        super().leaveEvent(event)


class NavButton(_SoftHover, QPushButton):
    """Fully drawn frosted-glass navigation, same lighting as the content cards.

    No QPushButton/QSS background gets painted over the translucent material.
    Buttons still use the original accessible keyboard/focus/checked behavior.
    """
    def __init__(self, text):
        super().__init__(text)
        self.glow = False
        self._update_version = ''
        self.icon_key = GLYPHS.get(str(text).split('    ',1)[0].strip(), 'overview')
        self._compact = False
        self._phase = 0.0
        self._init_soft_hover()
        self.setMinimumHeight(39)
        self.setMouseTracking(True)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._timer = QTimer(self)
        self._timer.setInterval(90)
        self._timer.timeout.connect(self._tick)

    def sizeHint(self):
        if self._compact:
            return QSize(44, 39)
        return super().sizeHint()

    def minimumSizeHint(self):
        if self._compact:
            return QSize(44, 39)
        return super().minimumSizeHint()

    def set_compact(self, compact):
        self._compact = bool(compact)
        # A compact button must not reserve space for its hidden text.
        self.setMinimumWidth(0)
        if compact:
            self.setFixedWidth(44)
        else:
            self.setMaximumWidth(16777215)
        caption = self.text().split('    ', 1)[-1]
        self.setAccessibleName(caption)
        self.setToolTip('')
        self.updateGeometry()
        self.update()


    def set_update_version(self, version):
        self._update_version = str(version or '')
        # The icon-only dock paints a badge, so it does not need an extra
        # caption row like the sidebar's update button.
        from . import theme
        self.setMinimumHeight(46 if theme.mode() == 'nebula_prism' else 47 if self._update_version else 39)
        self.updateGeometry()
        self.update()

    def set_glow(self, on):
        self.glow = bool(on)
        if self.glow:
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def _tick(self):
        self._phase += .105
        self.update()

    def _paint_minimal_nav(self):
        """Plain navigation with two text draws and no effects."""
        p = QPainter(self)
        if self.isChecked():
            p.fillRect(self.rect(), QColor(theme.CARD))
        if self.glow:
            intensity = 0.5 + 0.5 * math.sin(self._phase)
            background = theme.accent_qcolor(int(8 + 23 * intensity))
            p.fillRect(self.rect().adjusted(2, 2, -2, -2), background)
            left = theme.accent_qcolor(int(95 + 135 * intensity))
            p.fillRect(QRectF(2, 5, 3, max(1, self.height()-10)), left)
        text = self.text()
        glyph, caption = text.split('    ', 1) if '    ' in text else ('◈', text)
        color = QColor(theme.accent() if self.isChecked() else theme.TEXT)
        p.setPen(color)
        font = self.font()
        font.setPixelSize(15)
        p.setFont(font)
        paint_icon(p, self.icon_key, QRectF((44-20)/2 if self._compact else 19, (self.height()-20)/2, 20, 20), color)
        if not self._compact:
            font.setPixelSize(13)
            p.setFont(font)
            ypos = 7 if self._update_version and self.glow else 0
            height = self.height()-19 if ypos else self.height()
            p.drawText(QRectF(52, ypos, max(1, self.width()-54), height), Qt.AlignVCenter | Qt.AlignLeft, caption)
            if self._update_version and self.glow:
                font.setPixelSize(10)
                font.setBold(True)
                p.setFont(font)
                p.setPen(theme.accent_qcolor())
                p.drawText(QRectF(52, self.height()-20, max(1, self.width()-54), 16),
                           Qt.AlignVCenter | Qt.AlignLeft, self._update_version)
        p.end()

    def paintEvent(self, event):
        if theme.mode() == "minimal":
            self._paint_minimal_nav()
            return
        from . import signature_designs
        if signature_designs.active():
            return signature_designs.paint_navigation(self)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self.isDown(): p.translate(0, .8)
        r = QRectF(self.rect()).adjusted(2.5, 2.5, -2.5, -2.5)
        checked = self.isChecked()
        hover_amount = 1.0 if self.hasFocus() else self._hover_amount
        hovered = hover_amount > .01
        # Keep the selected card stable; idle hover lighting fades in with a
        # low-alpha brush, rather than forcing a glass redraw every tick.
        if theme.mode() in premium.KEYS:
            premium.paint_nav(p, self, r, checked, hover_amount)
        elif checked:
            paint_glass_body(p, self, r, 11, compact=True, active=True)
        else:
            idle = QColor(218, 243, 255, 7) if theme.mode() != 'light' else QColor(40, 65, 90, 6)
            p.setBrush(idle)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(r, 11, 11)
            if hovered:
                c = theme.accent_qcolor(max(0, round((19 if theme.mode() in ('glass',) else 14) * hover_amount)))
                p.setBrush(c)
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(r, 11, 11)

        if self.glow:
            # Breathing theme-accent halo instead of a bright orange alarm.
            intensity = 0.5 + 0.5 * math.sin(self._phase)
            glow = theme.accent_qcolor(int(9 + 27 * intensity))
            p.setPen(Qt.NoPen)
            p.setBrush(glow)
            p.drawRoundedRect(r, 11, 11)
            rail_glow = theme.accent_qcolor(int(90 + 125 * intensity))
            p.setBrush(rail_glow)
            p.drawRoundedRect(QRectF(r.left()+.3, r.top()+5, 3, r.height()-10), 1.5, 1.5)

        if checked:
            # A precision-cut cyan seam indicates the current section.
            rail = QLinearGradient(0, r.top(), 0, r.bottom())
            a = theme.accent_qcolor()
            faint = QColor(a); faint.setAlpha(0)
            rail.setColorAt(0.0, faint)
            a.setAlpha(240)
            rail.setColorAt(.22, a)
            a.setAlpha(220)
            rail.setColorAt(.75, a)
            rail.setColorAt(1.0, faint)
            p.setPen(QPen(QBrush(rail), 2.3, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(r.left()+1.8, r.top()+9),
                       QPointF(r.left()+1.8, r.bottom()-9))

        text = self.text()
        if '    ' in text:
            glyph, caption = text.split('    ', 1)
            glyph = glyph.strip()
        else:
            glyph, caption = '◈', text
        # Minimal glass node, anchored in the same place on every row.
        cx, cy = (r.center().x() if self._compact else r.left() + 21), r.center().y()
        color = QColor(theme.accent() if checked else theme.blend(theme.accent(), theme.TEXT, .60+.32*hover_amount))
        aura = QColor(color); aura.setAlpha(43 if checked else 10)
        p.setPen(Qt.NoPen)
        p.setBrush(aura)
        p.drawRoundedRect(QRectF(cx-12, cy-12, 24, 24), 7, 7)
        if self.glow:
            intensity = 0.5 + 0.5 * math.sin(self._phase)
            ring = theme.accent_qcolor(int(75 + 105 * intensity))
            p.setPen(QPen(ring, 1.1 + intensity * 1.0))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(cx - 13 - intensity*2, cy - 13 - intensity*2,
                                 26 + intensity*4, 26 + intensity*4))
        # Distinct category symbols stay recognizable in both wide and compact nav.
        paint_icon(p, self.icon_key, QRectF(cx-10, cy-10, 20, 20), color)

        font = self.font()
        font.setBold(checked)
        font.setPixelSize(13)
        p.setFont(font)
        ink = QColor(color)
        p.setPen(ink)
        if not self._compact:
            if self.glow and self._update_version:
                p.drawText(QRectF(r.left()+45, r.top()+4, r.width()-54, r.height()-23),
                           Qt.AlignVCenter | Qt.AlignLeft, caption)
                p.setPen(theme.accent_qcolor())
                small = QFont(self.font())
                small.setPixelSize(10)
                small.setBold(True)
                p.setFont(small)
                p.drawText(QRectF(r.left()+45, r.bottom()-20, r.width()-54, 15),
                           Qt.AlignVCenter | Qt.AlignLeft, self._update_version)
            else:
                p.drawText(QRectF(r.left()+45, r.top(), r.width()-54, r.height()),
                           Qt.AlignVCenter | Qt.AlignLeft, caption)

        if self.glow:
            intensity = (0.5 + 0.5 * math.sin(self._phase))
            dot = QColor(theme.accent())
            dot.setAlpha(int(130 + 120 * intensity))
            p.setPen(Qt.NoPen)
            p.setBrush(dot)
            if self._compact:
                # In icon-only mode, keep the update marker away from the icon.
                p.drawEllipse(QPointF(r.right() - 7, r.top() + 7),
                              1.8 + .65 * intensity, 1.8 + .65 * intensity)
            else:
                p.drawEllipse(QPointF(r.right() - 14, r.center().y()),
                              2.8 + 1.4 * intensity, 2.8 + 1.4 * intensity)
        # No dotted keyboard/mouse focus outline. The active rail and icon
        # color already communicate selection; keep keyboard focus semantics.
        p.end()


class SidebarToggle(_SoftHover, QPushButton):
    """Small, keyboard-accessible arrow that docks to the sidebar seam."""
    def __init__(self, parent=None, orientation="horizontal"):
        super().__init__('', parent)
        self._collapsed = False
        self._orientation = orientation
        self._init_soft_hover()
        self.setObjectName('sidebarToggle')
        self.setFixedSize(26, 30)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName(tr('Seitenleiste ein-/ausklappen'))
        self.setToolTip(tr('Seitenleiste einklappen'))

    def reset_highlight(self):
        """Clear clicked/focused highlight, especially after closing edit mode."""
        self.clearFocus()
        self._hover_motion.stop()
        self._hover_frame(0.0)
        self.update()

    def set_collapsed(self, collapsed):
        self._collapsed = bool(collapsed)
        self.setToolTip(tr('Seitenleiste ausklappen') if collapsed else tr('Seitenleiste einklappen'))
        self.update()

    def paintEvent(self, event):
        """Theme-native, understated edge control (no generic opaque glass tile).

        The small arrow is kept exactly in place. Only its material, rim and ink
        change with the active theme; hover and keyboard focus remain apparent.
        """
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0)
        mode = theme.mode()
        hover_amount = self._hover_amount
        hovered = hover_amount > .01
        focused = self.hasFocus()
        if focused:
            hover_amount = 1.0

        if mode == 'glass':
            # This control belongs to the frosted sidebar, not to the active
            # navigation items. A mostly clear surface and a faint rim prevent
            # it looking like a bright, glued-on button.
            fill = QLinearGradient(rect.topLeft(), rect.bottomRight())
            fill.setColorAt(0, rgba(34, 59, 81, round(76 + 26 * hover_amount)))
            fill.setColorAt(1, rgba(14, 29, 49, round(47 + 32 * hover_amount)))
            border = rgba(179, 213, 234, round(48 + 52 * hover_amount))
            ink = QColor(theme.blend(theme.accent(), theme.MUTED, hover_amount))
            ink.setAlpha(round(186 + 36 * hover_amount))
        elif mode == 'light':
            # Light deliberately uses a solid, pale button with a visible
            # graphite chevron, rather than transparent frosted navy.
            fill = QColor(theme.blend(theme.CARD, theme.SIDEBAR, .67))
            if hovered:
                fill = QColor(theme.blend(theme.accent(), fill, .07 * hover_amount))
            border = QColor(theme.BORDER)
            border.setAlpha(238)
            ink = QColor(theme.blend(theme.accent(), theme.MUTED, hover_amount))
        else:  # Dark: matte and quiet, matching the surrounding solid rail.
            fill = QColor(theme.blend(theme.CARD, theme.SIDEBAR, .47))
            if hovered:
                fill = QColor(theme.blend(theme.accent(), fill, .09 * hover_amount))
            border = QColor(theme.BORDER)
            border.setAlpha(160)
            ink = QColor(theme.blend(theme.accent(), theme.MUTED, hover_amount))

        if hovered or focused:
            # The distribution/user accent is subtle on hover, but the focus
            # state remains clear for keyboard users in all three themes.
            border = theme.accent_qcolor(
                round((165 if focused else 105 * hover_amount) if mode in ('glass',) else
                      (225 if focused else 168 * hover_amount))
            )
            if focused:
                ink = QColor(theme.accent())
                ink.setAlpha(240)

        p.setBrush(QBrush(fill))
        p.setPen(QPen(border, 1.15 if focused else .85 if mode in ('glass',) else 1.0))
        p.drawRoundedRect(rect, 9, 9)

        if mode in ('glass',):
            # A short, low-opacity specular reflection replaces a harsh
            # bright outline; it is almost invisible until light catches it.
            sheen = rgba(233,248,255,round(35+25*hover_amount))
            p.setPen(QPen(sheen, .8, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(rect.left()+7, rect.top()+1.4),
                       QPointF(rect.right()-7, rect.top()+1.4))

        p.setPen(QPen(ink, 1.65, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        cx, cy = rect.center().x(), rect.center().y()
        if self._orientation == 'vertical':
            shift = -1 if self._collapsed else 1
            p.drawLine(QPointF(cx-4.5,cy-2*shift),QPointF(cx,cy+2.5*shift))
            p.drawLine(QPointF(cx,cy+2.5*shift),QPointF(cx+4.5,cy-2*shift))
        elif self._collapsed:
            p.drawLine(QPointF(cx-2, cy-4.5), QPointF(cx+2.5, cy))
            p.drawLine(QPointF(cx+2.5, cy), QPointF(cx-2, cy+4.5))
        else:
            p.drawLine(QPointF(cx+2, cy-4.5), QPointF(cx-2.5, cy))
            p.drawLine(QPointF(cx-2.5, cy), QPointF(cx+2, cy+4.5))
        p.end()
