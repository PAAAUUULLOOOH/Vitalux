"""Native chart rendering, selection and recorded/live timelines."""
import math
from bisect import bisect_left
from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QImage, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget
from .ui_locale import QComboBox, QCheckBox, paint_check_indicator
from . import theme, premium
from .i18n import tr
from .ui_labels import label


class HistoryGraph(QWidget):
    def __init__(self, maxlen=60, mode="percent"):
        super().__init__()
        self.maxlen, self.mode = maxlen, mode
        self.series, self.series_names, self.series_styles = [], [], []
        self.series_modes = []
        self.sample_times = []
        self.horizon_seconds = 60
        self._pointer = None
        self._revision=0
        self._curve_key=None
        self._scale_key=None
        self.setMouseTracking(True)
        self.setMinimumHeight(185)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_series(self, series):
        self.series = series
        self._revision+=1
        self._curve_key=None
        self._scale_key=None
        self.update()

    def mouseMoveEvent(self, event):
        self._pointer = event.position().x()
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._pointer = None
        self.update()
        super().leaveEvent(event)

    def _format(self, value, mode=None):
        if value is None or not math.isfinite(float(value)):
            return '–'
        mode = mode or self.mode
        if mode == 'percent': return f'{value:.0f}%'
        if mode == 'temperature': return f'{value:.1f} °C'
        if mode == 'clock': return f'{value:.0f} MHz'
        if mode == 'frequency': return f'{value/1000:.2f} GHz'
        if mode == 'power': return f'{value:.1f} W'
        if mode == 'load': return f'{value:.2f}'
        if mode == 'fps': return f'{value:.0f} FPS'
        if mode == 'frametime': return f'{value:.1f} ms'
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
        if self.property('recordedSession') and len(self.sample_times) >= count:
            target=self.sample_times[-1]-(rect.right()-self._pointer)/rect.width()*self.horizon_seconds
            offset=len(self.sample_times)-count
            right=min(count-1,bisect_left(self.sample_times,target,lo=offset)-offset)
            index=min((max(0,right-1),right),key=lambda i:abs(self._x(i,count,rect)-self._pointer))
        else:index = min(range(count), key=lambda i: abs(self._x(i, count, rect)-self._pointer))
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
            mode=self.series_modes[number] if number<len(self.series_modes) else self.mode
            lines.append(f'{tr(name)}  {self._format(value,mode)}')
        return lines

    def unit_scales(self):
        """Independent axes keep GHz, degrees, watts and percentages truthful."""
        key=(self._revision,self.mode,tuple(self.series_modes))
        if key==self._scale_key:return self._scales
        scales={}
        for index,(values,tone) in enumerate(self.series):
            mode=self.series_modes[index] if index<len(self.series_modes) else self.mode
            peak=max((float(v) for v in values if v is not None and math.isfinite(float(v))),default=0.)
            if mode=='percent':upper=100.
            elif mode=='temperature':upper=max(100.,math.ceil(peak/20)*20)
            elif mode=='frequency':upper=max(1000.,math.ceil(peak*1.08/1000)*1000)
            elif mode=='power':upper=max(10.,math.ceil(peak*1.1/25)*25)
            elif mode=='fps':upper=max(30.,math.ceil(peak*1.08/30)*30)
            elif mode=='frametime':upper=max(10.,math.ceil(peak*1.08/5)*5)
            else:upper=max(1.,math.ceil(peak*1.1))
            previous=scales.get(mode,(0,tone))
            scales[mode]=(max(previous[0],upper),previous[1])
        self._scale_key,self._scales=key,scales
        return scales

    def _curves(self, rect, upper, scales, minimal):
        key=(self._revision,self.mode,upper,bool(self.property("recordedSession")),rect.x(),rect.y(),rect.width(),rect.height(),minimal,
             self.maxlen,self.horizon_seconds,tuple(self.sample_times),tuple(self.series_modes),
             tuple(self.series_styles),tuple(scales.items()))
        if key==self._curve_key:return self._curve_data
        result=[]
        for number,(values,color) in enumerate(self.series):
            limit=scales[self.series_modes[number]][0] if scales else upper
            values=list(values)[-self.maxlen:]
            runs,run=[],[]
            for index,value in enumerate(values):
                if value is None or not math.isfinite(float(value)):
                    if run:runs.append(run)
                    run=[]
                    continue
                y=rect.bottom()-min(1,max(0,float(value)/limit))*rect.height()
                run.append(QPointF(self._x(index,len(values),rect),y))
            if run:runs.append(run)
            paths=[]
            for points in runs:
                recorded=bool(self.property('recordedSession'))
                dense=recorded and len(points)>max(2,rect.width()*self.devicePixelRatioF()*2)
                if dense:
                    # Preserve the low/high in each physical pixel column.
                    # Full recorded values remain available for hover/statistics.
                    buckets={}
                    for i,point in enumerate(points):
                        bucket=int((point.x()-rect.left())*self.devicePixelRatioF())
                        low,high=buckets.get(bucket,(i,i))
                        buckets[bucket]=(i if point.y()<points[low].y() else low,
                                         i if point.y()>points[high].y() else high)
                    upper_points=[points[low] for low,high in buckets.values()]
                    lower_points=[points[high] for low,high in buckets.values()]
                    boundaries=[]
                    for edge in (upper_points,lower_points):
                        boundary=QPainterPath(edge[0])
                        for point in edge[1:]:boundary.lineTo(point)
                        boundaries.append(boundary)
                    # Draw a pixel envelope instead of thousands of overlapping
                    # stroked turns. Both extrema remain at their actual x/y.
                    band=QPainterPath(boundaries[0])
                    for point in reversed(lower_points):band.lineTo(point)
                    band.closeSubpath()
                    base=QPainterPath(boundaries[1])
                    base.lineTo(lower_points[-1].x(),rect.bottom())
                    base.lineTo(lower_points[0].x(),rect.bottom());base.closeSubpath()
                    paths.extend(((boundaries[0],band),(boundaries[1],base)))
                    continue
                else:
                    stride=1 if recorded else max(1,len(points)//400)
                    points=points[::stride]+([points[-1]] if (len(points)-1)%stride else [])
                path=QPainterPath(points[0])
                for previous,current in zip(points,points[1:]):
                    if minimal:path.lineTo(current)
                    else:
                        dx=current.x()-previous.x()
                        path.cubicTo(previous+QPointF(dx*.36,0),current-QPointF(dx*.36,0),current)
                area=QPainterPath(path)
                area.lineTo(points[-1].x(),rect.bottom())
                area.lineTo(points[0].x(),rect.bottom());area.closeSubpath()
                paths.append((path,area))
            end=runs[-1][-1] if values and values[-1] is not None and runs else None
            result.append((paths,end))
        self._curve_key,self._curve_data=key,result
        return result

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
        scales=self.unit_scales() if self.mode=='mixed' else {}
        rect = outer.adjusted(10, 20 if scales else 14, -max(65,66*len(scales)), -30)
        if rect.width() <= 8 or rect.height() <= 8:
            p.end()
            return
        if getattr(self,'_largest_revision',None)!=self._revision:
            self._largest=max((float(value) for values,_ in self.series
                               for value in values if value is not None and math.isfinite(float(value))),default=0)
            self._largest_revision=self._revision
        largest=self._largest
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
            if scales:
                for index,(mode,(limit,tone)) in enumerate(scales.items()):
                    p.setPen(QColor(tone))
                    p.drawText(QRectF(rect.right()+6+index*66,y-10,64,20),Qt.AlignLeft|Qt.AlignVCenter,
                               self._format(limit*fraction,mode))
            elif self.mode!='mixed':
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
        curves=self._curves(rect,upper,scales,minimal)
        any_data=any(paths for paths,_end in curves)
        if self.property('recordedSession'):
            key=(self._curve_key,self.devicePixelRatioF(),self.size(),theme.mode())
            if key!=getattr(self,'_recorded_layer_key',None):
                ratio=self.devicePixelRatioF()
                layer=QImage(round(self.width()*ratio),round(self.height()*ratio),QImage.Format_ARGB32_Premultiplied)
                layer.setDevicePixelRatio(ratio);layer.fill(Qt.transparent)
                painter=QPainter(layer);painter.setRenderHint(QPainter.Antialiasing)
                self._paint_curves(painter,curves,rect,minimal);painter.end()
                self._recorded_layer_key,self._recorded_layer=key,layer
            p.drawImage(QPointF(0,0),self._recorded_layer)
        else:self._paint_curves(p,curves,rect,minimal)
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


    def _paint_curves(self,p,curves,rect,minimal):
        for number,((values,color),(paths,end)) in enumerate(zip(self.series,curves)):
            style=self.series_styles[number] if number<len(self.series_styles) else Qt.SolidLine
            c=QColor(color)
            for path,area in paths:
                if not minimal:
                    gradient=QLinearGradient(rect.topLeft(),rect.bottomLeft())
                    top,bottom=QColor(c),QColor(c)
                    top.setAlpha(51 if number else 68);bottom.setAlpha(0)
                    gradient.setColorAt(0,top);gradient.setColorAt(1,bottom)
                    p.fillPath(area,gradient)
                    halo=QColor(c);halo.setAlpha(39)
                    p.setBrush(Qt.NoBrush)
                    p.setPen(QPen(halo,5,style,Qt.RoundCap,Qt.RoundJoin));p.drawPath(path)
                p.setBrush(Qt.NoBrush)
                p.setPen(QPen(c,1.8,style,Qt.RoundCap,Qt.RoundJoin));p.drawPath(path)
            if end is not None:
                p.setBrush(c);p.setPen(Qt.NoPen);p.drawEllipse(end,2.5,2.5)


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
    def __init__(self, series_names, colors, mode="percent", series_modes=None):
        super().__init__()
        self.series_names = list(series_names)
        self.colors = list(colors)
        self.series_modes=list(series_modes or [mode]*len(series_names))
        self.color_roles = ["accent" if c.lower() == theme.accent().lower() else
                            "secondary" if c.lower() == theme.secondary_accent().lower() else
                            "teal" if c.lower() == theme.TEAL.lower() else "fixed"
                            for c in colors]
        self._source = []
        self.sample_interval = 1
        self._timestamps = []
        self._loaded_key = None
        self._loading_choices = False
        self._scope = ''
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(10)
        controls = QGridLayout() if mode=='mixed' else QHBoxLayout()
        controls.setSpacing(10)
        self._mixed_controls=controls if mode=='mixed' else None
        self.time_range = QComboBox()
        for label_, secs in (("60 s", 60), ("5 min", 300), ("15 min", 900)):
            self.time_range.addItem(label_, secs)
        self.time_range.currentIndexChanged.connect(self._update)
        controls.addWidget(self.time_range,0,0) if mode=="mixed" else controls.addWidget(self.time_range)
        self.toggles = []
        self.live_labels = []
        for idx, name in enumerate(self.series_names):
            # Apply the current theme immediately. The old initial color
            # leaked teal into the RAM legend on Black Glass Gold until retheme().
            cb = ChartSeriesCheckBox(name, self._palette_color(idx))
            cb.setChecked(True)
            cb.toggled.connect(self._update)
            controls.addWidget(cb,(idx+1)//3,(idx+1)%3) if mode=="mixed" else controls.addWidget(cb)
            self.toggles.append(cb)
        if mode!='mixed':controls.addStretch(1)
        layout.addLayout(controls)
        self.graph = HistoryGraph(mode=mode)
        layout.addWidget(self.graph)
        # Values are real samples, not decoration; unavailable data is shown as dashes.
        live = QGridLayout() if mode=='mixed' else QHBoxLayout()
        live.setSpacing(10)
        for name in self.series_names:
            item = label(f"{name}  –", "muted")
            item.setToolTip(tr("Aktueller Wert / Minimum / Maximum im ausgewählten Zeitraum"))
            self.live_labels.append(item)
            if mode=='mixed':
                index=len(self.live_labels)-1
                live.addWidget(item,index//2,index%2)
                item.setWordWrap(True)
            else:live.addWidget(item)
        if mode!='mixed':live.addStretch()
        layout.addLayout(live)
        self.time_range.currentIndexChanged.connect(self._choice_changed)
        for toggle in self.toggles:
            toggle.toggled.connect(self._choice_changed)

    def _preferences_key(self):
        parent = self.parentWidget()
        while parent is not None:
            page = parent.property('page_key')
            if page:
                return '|'.join((page, self._scope, *self.series_names))
            parent = parent.parentWidget()
        return None

    def _load_choices(self):
        from .chart_preferences import load
        key = self._preferences_key()
        if not key or key == self._loaded_key:
            return
        self._loaded_key = key
        self._loading_choices = True
        try:
            saved = load(key)
            index = self.time_range.findData(saved.get('seconds', self.property('defaultHorizon') or 60))
            self.time_range.setCurrentIndex(max(0, index))
            enabled = saved.get('enabled', [])
            if not isinstance(enabled, (list, tuple)):enabled = []
            for index, toggle in enumerate(self.toggles):
                toggle.setChecked(enabled[index] if index < len(enabled) and isinstance(enabled[index], bool) else True)
        finally:
            self._loading_choices = False
        self._update()

    def set_scope(self, scope):
        self._scope = str(scope or '')
        self._load_choices()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_choices()

    def _choice_changed(self, *_):
        from .chart_preferences import save
        key = self._preferences_key()
        if key and not self._loading_choices:
            save(key, self.time_range.currentData(), [toggle.isChecked() for toggle in self.toggles])

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
        if horizon < 0:
            horizon = max(1, self._timestamps[-1]-self._timestamps[0]) if self._timestamps else 60
        count = max(2, round(horizon/self.sample_interval))
        if self._timestamps:
            cutoff = self._timestamps[-1]-horizon
            count = max(2, sum(stamp >= cutoff for stamp in self._timestamps))
        self.graph.sample_times = self._timestamps[-count:]
        self.graph.series_names = []
        self.graph.series_styles = []
        self.graph.series_modes = []
        self.graph.maxlen = count
        self.graph.horizon_seconds = horizon
        active = []
        for i, (values, _color) in enumerate(self._source):
            if i >= len(self.toggles):
                continue
            color = self._palette_color(i)
            style=f'color: {color}; font-weight: 700;'
            if self.live_labels[i].styleSheet()!=style:self.live_labels[i].setStyleSheet(style)
            if not self.toggles[i].isChecked():
                self.live_labels[i].setText('')
                self.live_labels[i].hide()
                continue
            recent=list(values)[-count:]
            vals = [float(v) for v in recent if v is not None and math.isfinite(float(v))]
            if vals:
                fmt = lambda value: self.graph._format(value,self.series_modes[i])
                smallest,largest=min(vals),max(vals)
                current = recent[-1] if recent else None
                shown = fmt(current) if current is not None else '–'
                self.live_labels[i].setText(f'{tr(self.series_names[i])} {shown}  ·  {fmt(smallest)}–{fmt(largest)}')
                self.live_labels[i].setToolTip(f'{tr(self.series_names[i])}: {tr("Jetzt")} {shown} | Min {fmt(smallest)} | Max {fmt(largest)}')
            else:
                self.live_labels[i].setText(f'{tr(self.series_names[i])} –')
            self.live_labels[i].show()
            active.append((recent, color))
            self.graph.series_names.append(self.series_names[i])
            self.graph.series_modes.append(self.series_modes[i])
            self.graph.series_styles.append((Qt.SolidLine, Qt.DashLine, Qt.DotLine)[i % 3])
        self.graph.set_series(active)
