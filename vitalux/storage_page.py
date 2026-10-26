"""Storage overview, SMART loading and drive diagnostics."""
from PySide6.QtCore import QThread, Signal

from . import theme
from .benchmark_ui import BenchmarkPanel
from .sensors import drives, fmt_bytes, fmt_rate
from . import smart_monitor
from .smart_ui import SmartPane
from .widgets import Card, ChartPanel, KeyValue, Meter
from .sensor_ui import SensorPanel


from .page_base import Page, _row


class SmartWorker(QThread):
    completed = Signal(object)

    def run(self):
        try:
            self.completed.emit(smart_monitor.scan(drives()))
        except Exception as exc:
            self.completed.emit([{'name': 'SMART', 'error': str(exc)}])


class DiskPage(Page):
    def __init__(self):
        super().__init__("Laufwerke", "Datenträger, Belegung und Durchsatz")
        self.hw = Card("Physische Datenträger")
        self.hw_rows = {}
        self.parts = Card("Partitionen")
        self.part_meters = {}
        io = Card("Durchsatz")
        self.read, self.write = KeyValue("Lesen"), KeyValue("Schreiben")
        io.body.addWidget(self.read)
        io.body.addWidget(self.write)
        self.content.addLayout(_row(self.hw, self.parts))
        self.content.addWidget(io)
        io_graph = Card('Laufwerksaktivität')
        self.io_graph = ChartPanel(['Lesen','Schreiben'], [theme.accent(),theme.secondary_accent()],mode='rate')
        io_graph.body.addWidget(self.io_graph)
        self.content.addWidget(io_graph)
        self.hardware=SensorPanel()
        self.content.addWidget(self.hardware)
        self.smart_card = SmartPane()
        self.smart_button = self.smart_card.button
        self.smart_status = self.smart_card.status
        self.smart_button.clicked.connect(self.request_smart)
        self.content.addWidget(self.smart_card)
        self._smart_worker = None
        self._smart_loaded = False
        # Disk selectors are already visible while SMART runs in a worker.
        # Do not delay the user's first access to drive details.
        self.smart_card.set_devices(drives())
        # Integrierter Laufwerks-Benchmark unter den Laufwerksdaten.
        self.benchmark = BenchmarkPanel()
        self.content.addWidget(self.benchmark)
        self._tick = 0


    def request_smart(self):
        if self._smart_worker and self._smart_worker.isRunning():
            return
        self.smart_button.setEnabled(False)
        self.smart_status.setText('Lese SMART-Daten im Hintergrund …')
        self._smart_worker = SmartWorker(self)
        self._smart_worker.completed.connect(self.show_smart)
        self._smart_worker.finished.connect(lambda: self.smart_button.setEnabled(True))
        self._smart_worker.start()

    def show_smart(self, reports):
        self._smart_loaded = True
        self.smart_card.set_reports(reports, drives())

    def refresh_appearance(self):
        self.smart_card.refresh_theme()

    def retranslate(self):
        self.smart_card.retranslate()

    def refresh(self, d, h):
        self.hardware.sync([r for r in d.get('hardware',[]) if r['component']=='disks'])
        if self._tick % 30 == 0:
            for dr in drives():
                if dr["name"] not in self.hw_rows:
                    kv = KeyValue(f"{dr['name']}  ·  {dr['kind']}")
                    self.hw.body.addWidget(kv)
                    self.hw_rows[dr["name"]] = kv
                text = (dr["model"] + "  ·  " if dr["model"] else "") + fmt_bytes(dr["size"], 1000)
                self.hw_rows[dr["name"]].set(text)
        self._tick += 1
        self.benchmark.update_volumes(d["disks"])
        self.read.set(fmt_rate(d["io"]["read"]))
        self.write.set(fmt_rate(d["io"]["write"]))
        self.io_graph.set_series([(h['io_read'],theme.accent()),(h['io_write'],theme.secondary_accent())])
        current = {x["mount"] for x in d["disks"]}
        for x in d["disks"]:
            m = self.part_meters.get(x["mount"])
            if m is None:
                m = self.part_meters[x["mount"]] = Meter(f"{x['mount']}   ({x['device']}, {x['fstype']})")
                self.parts.body.addWidget(m)
            m.setVisible(True)
            m.set(x["percent"], f"{fmt_bytes(x['used'])} / {fmt_bytes(x['total'])}   ({x['percent']:.0f}%)")
        for mount, m in self.part_meters.items():
            if mount not in current:
                m.setVisible(False)
