"""One selectable chart per component, with separate physical-unit scales."""
import html
import math
import time
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGridLayout, QMenu, QSizePolicy, QToolButton, QToolTip, QWidget
from . import premium, theme
from .hardware_sensors import number
from .i18n import lang, tr
from .measurements import MeasurementHistory
from .ui_locale import QComboBox
from .widgets import ChartPanel, HistoryGraph, label


def format_value(value,unit):
    if number(value) is None:
        return ''
    if unit=='B/s':
        from .sensors import fmt_rate
        return fmt_rate(value)
    places=0 if unit in ('%','MHz','U/min') else 2 if unit in ('V','Last') else 1
    text=f'{value:.{places}f}'
    if places:
        text=text.rstrip('0').rstrip('.')
    return text+' '+tr(unit)


def metric_name(name):
    return ' · '.join(tr(part) for part in name.split(' · '))


class MeasurementGraph(HistoryGraph):
    def __init__(self):
        super().__init__(mode='mixed')
        self.units=[];self.scales={};self.axis_unit=''
        self._painting=False

    def axis_scale(self,upper):
        return self.scales.get(self.axis_unit,(0.,1.))

    def series_scale(self,index,upper):
        return self.scales.get(self.units[index],(0.,1.))

    def _format(self,value):
        return format_value(value,self.axis_unit)

    def format_series(self,index,value):
        return format_value(value,self.units[index])

    def hover_readout(self,rect):
        return [] if self._painting else super().hover_readout(rect)

    def mouseMoveEvent(self,event):
        super().mouseMoveEvent(event)
        rect=QRectF(self.rect()).adjusted(12,16,-67,-32)
        lines=self.hover_readout(rect)
        if lines:
            QToolTip.showText(event.globalPosition().toPoint(),'<br>'.join(html.escape(line) for line in lines),self)
        else:
            QToolTip.hideText()

    def leaveEvent(self,event):
        QToolTip.hideText()
        super().leaveEvent(event)

    def paintEvent(self,event):
        self._painting=True
        try:
            super().paintEvent(event)
        finally:
            self._painting=False
        rect=QRectF(self.rect()).adjusted(12,16,-67,-32)
        if self._pointer is not None and rect.left()<=self._pointer<=rect.right():
            p=QPainter(self)
            p.setPen(QPen(QColor(theme.MUTED),.8,Qt.DashLine))
            p.drawLine(QPointF(self._pointer,rect.top()),QPointF(self._pointer,rect.bottom()))
            p.end()


class SelectionMenu(QMenu):
    def mouseReleaseEvent(self,event):
        action=self.activeAction()
        if action is not None and action.isCheckable() and event.button()==Qt.LeftButton:
            action.trigger()
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class MeasurementChart(ChartPanel):
    def __init__(self):
        super().__init__([],[],mode='mixed')
        self.available={};self.histories={};self.selected={};self.order={}
        self.history=MeasurementHistory()
        self._menu_identity=None
        self._submenus=[]
        old=self.graph
        self.graph=MeasurementGraph()
        self.layout().replaceWidget(old,self.graph)
        old.hide();old.setParent(None);old.deleteLater()
        self.layout().takeAt(2)  # Empty readout row from the shared chart shell.
        self.scale_hint=label('', 'muted',wrap=True)
        self.layout().insertWidget(1,self.scale_hint)
        controls=self.layout().itemAt(0).layout()
        self.selector=QToolButton(self)
        self.selector.setObjectName('layoutAction')
        self.selector.setPopupMode(QToolButton.InstantPopup)
        self.menu=SelectionMenu(self.selector)
        self.selector.setMenu(self.menu)
        controls.insertWidget(1,self.selector)
        self.axis_label=label('Skala','muted')
        self.axis_combo=QComboBox()
        self.axis_combo.currentIndexChanged.connect(self._update)
        controls.insertWidget(2,self.axis_label)
        controls.insertWidget(3,self.axis_combo)
        self.legend=QWidget(self)
        self.legend_grid=QGridLayout(self.legend)
        self.legend_grid.setContentsMargins(0,0,0,0)
        self.legend_labels={}
        self.layout().addWidget(self.legend)
        self.hide()

    def color(self,key):
        index=self.order[key]
        if theme.mode() in premium.KEYS:
            palette=premium.palette()['series']
        elif theme.mode()=='black_glass_gold':
            palette=('#ffe5a0','#e0b55d','#f4cf81','#ba8739')
        else:
            palette=(theme.accent(),theme.secondary_accent(),theme.TEAL,theme.VIOLET,theme.WARN)
        color=QColor(palette[index%len(palette)])
        if index>=len(palette):
            color=color.darker(112) if theme.is_light() else color.lighter(112)
        return color.name()

    def sync(self,sample,scope,legacy=None):
        tracker=getattr(self.window(),'measurement_history',None)
        tracked=tracker is not None
        if tracker is None:
            self.history.update(sample,sample.get('timestamp',time.time()),self.sample_interval)
            tracker=self.history
        self.available=tracker.current.get(scope,{})
        self.histories=tracker.groups.get(scope,{})
        self._timestamps=list(tracker.times)
        mapping=({'usage':'gpu','vram_pct':'vram','temp':'gpu_temp','clock':'gpu_clock','power':'gpu_power'} if scope.startswith('gpu:') else
                 {'usage':'cpu','temp':'cpu_temp'} if scope=='cpu' else
                 {'percent':'ram'} if scope=='ram' else
                 {'read':'io_read','write':'io_write'} if scope=='disks' else
                 {'down':'net_down','up':'net_up'} if scope=='network' else {})
        self._legacy={} if tracked else {key:legacy[name] for key,name in mapping.items() if legacy is not None and name in legacy}
        priority={'usage':0,'vram_pct':1,'power':2,'temp':3}
        self.keys=sorted(self.available,key=lambda key:(priority.get(key,10),list(self.available).index(key)))
        for key in self.keys:
            self.order.setdefault(key,len(self.order))
            self.selected.setdefault(key,self.available[key]['default'])
        self.setVisible(bool(self.keys))
        self._make_menu()
        self._update()

    def _make_menu(self):
        identity=(tuple((key,self.available[key]['name'],self.available[key]['unit']) for key in self.keys),lang(),theme.mode(),theme.accent())
        if identity==self._menu_identity:
            return
        self._menu_identity=identity
        self.menu.close()
        self.menu.clear()
        for submenu in self._submenus:
            submenu.deleteLater()
        self._submenus=[]
        self.menu.addAction(tr('Alle auswählen'),lambda:self.select_all(True))
        self.menu.addAction(tr('Alle abwählen'),lambda:self.select_all(False))
        self.menu.addSeparator()
        self.actions={};units={}
        for key in self.keys:
            metric=self.available[key]
            unit=metric['unit']
            submenu=units.get(unit)
            if submenu is None:
                submenu=SelectionMenu(tr(unit),self.menu)
                self.menu.addMenu(submenu);units[unit]=submenu
                self._submenus.append(submenu)
            action=submenu.addAction(metric_name(metric['name']))
            action.setCheckable(True);action.setChecked(self.selected[key])
            pix=QPixmap(12,12);pix.fill(QColor(self.color(key)))
            action.setIcon(QIcon(pix))
            action.setToolTip(metric.get('source',''))
            action.toggled.connect(lambda checked,key=key:self.set_selected(key,checked))
            self.actions[key]=action

    def set_selected(self,key,checked):
        self.selected[key]=bool(checked)
        self._update()

    def select_all(self,checked):
        for key in self.keys:
            self.selected[key]=bool(checked)
            action=self.actions[key];action.blockSignals(True);action.setChecked(checked);action.blockSignals(False)
        self._update()

    def retheme(self):
        self._menu_identity=None
        if hasattr(self,'keys'):
            self._make_menu();self._update()

    def _update(self,*_):
        if not hasattr(self,'available'):
            return
        horizon=self.time_range.currentData() or 60
        count=max(2,round(horizon/self.sample_interval))
        if self._timestamps:
            count=max(2,sum(stamp>=self._timestamps[-1]-horizon for stamp in self._timestamps))
        self.graph.sample_times=self._timestamps[-count:]
        self.graph.maxlen=count;self.graph.horizon_seconds=horizon
        self._source=[];active=[];units=[];names=[];styles=[];unit_values={}
        keys=getattr(self,'keys',[])
        active_keys=[]
        for key in keys:
            metric=self.available[key]
            values=self._legacy.get(key,self.histories[key]['values'])
            color=self.color(key)
            self._source.append((values,color))
            if not self.selected[key]:
                continue
            active_keys.append(key)
            recent=list(values)[-count:]
            active.append((recent,color));units.append(metric['unit']);names.append(metric_name(metric['name']))
            styles.append((Qt.SolidLine,Qt.DashLine,Qt.DotLine,Qt.DashDotLine)[self.order[key]%4])
            unit_values.setdefault(metric['unit'],[]).extend(v for v in recent if number(v) is not None)
        scales={}
        for unit,values in unit_values.items():
            if unit=='%':
                scales[unit]=(0.,max(100.,math.ceil(max(values,default=0.)/25)*25))
            else:
                low=min(0.,min(values,default=0.))
                upper=max(1.,max(values,default=0.)*1.12)
                step=10**math.floor(math.log10(upper))
                scales[unit]=(low,math.ceil(upper/step*2)/2*step)
        selected_axis=self.axis_combo.currentData()
        self.axis_combo.blockSignals(True)
        if list(scales)!=[self.axis_combo.itemData(i) for i in range(self.axis_combo.count())]:
            self.axis_combo.clear()
            for unit in scales:self.axis_combo.addItem(tr(unit),unit)
            index=self.axis_combo.findData(selected_axis)
            self.axis_combo.setCurrentIndex(index if index>=0 else 0)
        for index,unit in enumerate(scales):self.axis_combo.setItemText(index,tr(unit))
        self.axis_combo.blockSignals(False)
        self.axis_combo.setVisible(len(scales)>1);self.axis_label.setVisible(len(scales)>1)
        self.graph.axis_unit=self.axis_combo.currentData() or ''
        self.graph.scales=scales;self.graph.units=units
        self.graph.series_names=names;self.graph.series_styles=styles
        self.graph.set_series(active);self.graph.setVisible(bool(active))
        self.scale_hint.setText(tr('Eigene Skala je Einheit')+' · '+' · '.join(
            tr(unit)+': '+format_value(low,unit)+'–'+format_value(high,unit) for unit,(low,high) in scales.items()))
        self.scale_hint.setVisible(len(scales)>1)
        self.selector.setText(tr('Messwerte')+f' ({len(active_keys)}/{len(keys)})')
        self.axis_label.setText(tr('Skala'))
        while self.legend_grid.count():self.legend_grid.takeAt(0)
        for key,item in self.legend_labels.items():item.setVisible(key in active_keys)
        columns=3 if self.width()>=800 else 2 if self.width()>=440 else 1
        for index,key in enumerate(active_keys):
            item=self.legend_labels.get(key)
            if item is None:
                item=self.legend_labels[key]=label('', 'muted',wrap=True)
                item.setParent(self.legend);item.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred)
            metric=self.available[key]
            item.setText('● '+metric_name(metric['name'])+' ('+tr(metric['unit'])+')')
            item.setStyleSheet('color:'+self.color(key)+';')
            item.setToolTip(metric.get('source',''));item.show()
            self.legend_grid.addWidget(item,index//columns,index%columns)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self._update()
