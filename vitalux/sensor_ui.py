"""Optional sensor rows and measured power histories without empty placeholders."""
from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget
from . import theme
from .hardware_sensors import number
from .i18n import tr
from .widgets import Card, HistoryGraph, KeyValue, label


def reflow(grid, widgets, columns=2):
    while grid.count():
        grid.takeAt(0)
    visible = [w for w in widgets if not w.isHidden()]
    parent=grid.parentWidget()
    if parent is not None and parent.width()<640:
        columns=1
    for i, widget in enumerate(visible):
        grid.addWidget(widget, i//columns, i % columns)


def sensor_row(title, parent):
    row=KeyValue(title)
    row.setParent(parent)
    row.layout().itemAt(0).widget().setWordWrap(True)
    return row


def optional(row, value, unit='', places=1):
    valid = number(value) is not None
    row.setVisible(valid)
    if valid:
        row.set(f'{value:.{places}f} {tr(unit)}'.strip())
    else:
        row.set('')  # Do not leave the previous reading available as current text.


def power_text(records, component):
    powers = [r for r in records if r['component'] == component and r['kind'] == 'powers'
              and number(r.get('value')) is not None]
    packages = [r for r in powers if r.get('primary')]
    if packages:
        powers = packages
    return ' · '.join(f"{tr(r.get('scope') or r['name'])}: {r['value']:.1f} W" for r in powers)


class PowerDetails(QWidget):
    def __init__(self):
        super().__init__()
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(0, 6, 0, 12)
        self.title = label('', 'strong', wrap=True)
        self.body.addWidget(self.title)
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(24)
        self.rows = {}
        self.body.addLayout(self.grid)
        self.graph = HistoryGraph(mode='power')
        self.graph.setMinimumHeight(130)
        self.body.addWidget(self.graph)

    def sync(self, record):
        self.title.setText(record['name'])
        self.title.setToolTip(record.get('source', ''))
        entries = [('Aktuell', record.get('value')),
                   ('Durchschnitt seit App-Start', record.get('average')),
                   ('Maximum seit App-Start', record.get('maximum'))]
        entries += list(record.get('limits') or ())
        active = set()
        for title, value in entries:
            active.add(title)
            row = self.rows.get(title)
            if row is None:
                row = self.rows[title] = sensor_row(title,self)
            optional(row, value, 'W')
        for title, row in self.rows.items():
            if title not in active:
                optional(row, None)
        reflow(self.grid, list(self.rows.values()))
        history = record.get('history') or []
        self.graph.sample_times = [p[0] for p in history]
        self.graph.series_names = [tr('Leistungsaufnahme')]
        self.graph.set_series([([p[1] for p in history], theme.accent())])
        self.graph.setVisible(number(record.get('value')) is not None and bool(history))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        reflow(self.grid,list(self.rows.values()))


class SensorPanel(Card):
    def __init__(self):
        super().__init__('Sensoren & Leistungsaufnahme')
        self.powers, self.rows = {}, {}
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(24)
        self.body.addLayout(self.grid)
        self.hide()

    def sync(self, records):
        present, power_ids = set(), set()
        for record in records:
            key = record['id']
            if record['kind'] == 'powers':
                if number(record.get('value')) is None and not record.get('limits'):
                    continue
                power_ids.add(key)
                widget = self.powers.get(key)
                if widget is None:
                    widget = self.powers[key] = PowerDetails()
                    self.body.addWidget(widget)
                widget.sync(record)
                widget.show()
            elif number(record.get('value')) is not None:
                present.add(key)
                row = self.rows.get(key)
                if row is None:
                    row = self.rows[key] = sensor_row(record['name'],self)
                optional(row, record['value'], record['unit'], 0 if record['kind'] == 'fans' else 2 if record['kind'] == 'voltages' else 1)
                row.setToolTip(record.get('source', ''))
        for key, row in self.rows.items():
            if key not in present:
                optional(row, None)
        for key, widget in self.powers.items():
            widget.setVisible(key in power_ids)
        reflow(self.grid, list(self.rows.values()))
        self.setVisible(bool(present or power_ids))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        reflow(self.grid,list(self.rows.values()))
