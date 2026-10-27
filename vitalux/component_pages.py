"""CPU, graphics and memory pages with independent device histories."""
from collections import deque
import platform

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget, QLayout

from . import theme
from .ui_locale import QPushButton
from .i18n import tr
from .sensors import fmt_bytes, system_static
from .widgets import Card, GaugeCard, KeyValue, Meter, label
from .charts import ChartPanel
from .sensor_ui import SensorPanel, optional, reflow
from .hardware_sensors import number
from .power_display import component_power, gpu_power, power_limit, source_text
from .product_ui import ProductHeader


from .page_base import Page, _row, _vram_text


class CpuPage(Page):
    def __init__(self):
        super().__init__("Prozessor", "Auslastung, Takt und Temperatur")
        top = Card()
        self.name = label("–", "bigName", wrap=True)
        self.meta = label('', 'muted', wrap=True)
        self.product_header = ProductHeader(self.name, self.meta, 'cpu')
        top.body.addWidget(self.product_header)
        self.content.addWidget(top)
        graph=Card('CPU-Messwerte · Verlauf')
        self.graph=ChartPanel(['Auslastung','Temperatur','Takt'],
                             [theme.accent(),theme.secondary_accent(),theme.TEAL],mode='mixed',
                             series_modes=['percent','temperature','frequency'])
        graph.body.addWidget(self.graph)
        graph.body.addWidget(label('Jede Messgröße hat eine eigene farbige Skala.','muted',wrap=True))
        self.content.addWidget(graph)

        self.cores_card = Card("Kerne / Threads · Auslastung")
        self.cores_card.body.addWidget(label(
            'Alle logischen Prozessoren in CPU-Reihenfolge; abgeschaltete CPUs bleiben sichtbar.',
            'muted', wrap=True))
        self.cores_grid = QGridLayout()
        self.cores_grid.setHorizontalSpacing(24)
        self.cores_grid.setVerticalSpacing(12)
        self.cores_card.body.addLayout(self.cores_grid)
        self.content.addWidget(self.cores_card)
        self.core_meters = []
        self._core_columns = 0
        self.root.setSizeConstraint(QLayout.SetMinimumSize)
        self.cores_card.layout().setSizeConstraint(QLayout.SetMinimumSize)

    def showEvent(self,event):
        super().showEvent(event)
        if self.parentWidget() is not None:self.parentWidget().installEventFilter(self)
        self._arrange_cores()

    def eventFilter(self,watched,event):
        if watched is self.parentWidget() and event.type()==QEvent.Resize:
            self._arrange_cores()
        return super().eventFilter(watched,event)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self._arrange_cores()

    def _arrange_cores(self):
        # A large grid's minimum width can prevent the page from shrinking.
        # Follow its viewport too, so columns reflow before that constraint.
        parent=self.parentWidget()
        available=min(self.width(),parent.width()) if parent is not None else self.width()
        columns = max(1, min(4, (available - 100) // 200))
        if columns == self._core_columns:
            return
        for i, meter in enumerate(self.core_meters):
            self.cores_grid.addWidget(meter, i // columns, i % columns)
        self._core_columns = columns
        self.cores_card.updateGeometry()
        self.updateGeometry()

    def refresh(self, d, h):
        c = d["cpu"]
        self.name.setText(c["model"])
        self.meta.setText(c.get('manufacturer') or '')
        self.product_header.set_product(c.get('product'))
        self.product_header.set_specs([
            ('Kerne / Threads', f'{c["cores"]} / {c["threads"]}'),
            ('Maximaler Takt', f'{c["freq_max"]/1000:.2f} GHz' if c.get('freq_max') else ''),
            ('Architektur', platform.machine())])
        keys=('cpu','cpu_temp','cpu_clock')
        self.graph.set_series([(h.get(key,()),tone) for key,tone in zip(keys,self.graph.colors)])
        entries = c.get('logical_cpus')
        if entries is None:
            entries = [dict(id=i, usage=v, online=True) for i, v in enumerate(c['per_core'])]
        entries = sorted(entries, key=lambda row: row['id'])
        count_changed = len(self.core_meters) != len(entries)
        while len(self.core_meters) < len(entries):
            i = len(self.core_meters)
            m = Meter(f"CPU {i}")
            m.setMinimumHeight(m.minimumSizeHint().height())
            self.core_meters.append(m)
        while len(self.core_meters) > len(entries):
            meter = self.core_meters.pop()
            self.cores_grid.removeWidget(meter)
            meter.hide()
            meter.deleteLater()
        for meter, row in zip(self.core_meters, entries):
            core = row.get('core')
            text = f'CPU {row["id"]}'
            if core is not None:
                text += ' · ' + tr('Kern {id}').format(id=core)
            meter.name.setText(text)
            package = row.get('package')
            meter.setToolTip(tr('Sockel {id}').format(id=package) if package is not None else '')
            meter.set(row.get('usage'), tr('Offline') if not row.get('online', True) else None)
        if count_changed:
            self._core_columns = 0
        self._arrange_cores()


class GpuCard(Card):
    """One coherent read-only GPU card: no privileged service or tuning controls."""

    def __init__(self):
        super().__init__()
        self.name = label("–", "bigName", wrap=True)
        self.meta = label("", "muted", wrap=True)
        self.product_header = ProductHeader(self.name, self.meta, 'gpu')
        self.body.addWidget(self.product_header)


        self.body.addWidget(label("AKTUELLE GPU-WERTE", "cardTitle"))
        self.kv = {key: KeyValue(key) for key in (
            "Auslastung", "Videospeicher", "GPU-Takt", "Speicher-Takt", "Temperatur", "Hotspot",
            "Spannung", "Leistung", 'Leistungsgrenze', "Lüfterdrehzahl", "Lüfter",
            "VRAM-Temperatur", "Speichercontroller", "Video-Engine", "Encoder", "Decoder",
            "Begrenzungsgründe", "Begrenzungsflags (Treiber)",
            "PCIe aktuell", "PCIe maximal", "Datenquelle", "Mesa",
        )}
        live = QGridLayout()
        self.live_grid = live
        self.live_fields = (
            'Auslastung','Videospeicher','Leistung','Leistungsgrenze','GPU-Takt','Speicher-Takt','Temperatur','Hotspot','VRAM-Temperatur',
            'Spannung','Lüfterdrehzahl','Lüfter','Speichercontroller',
            'Video-Engine','Encoder','Decoder','Begrenzungsgründe','Begrenzungsflags (Treiber)')
        live.setHorizontalSpacing(18)
        live.setVerticalSpacing(10)
        for i, name in enumerate((
            "GPU-Takt", "Speicher-Takt", "Temperatur", "Hotspot",
            "Spannung", "Leistung", "Lüfterdrehzahl", "Lüfter",
        )):
            live.addWidget(self.kv[name], i // 2, i % 2)
        self.body.addLayout(live)
        for key in self.live_fields:
            if self.kv[key].parent() is None:
                self.kv[key].setParent(self)
                self.kv[key].hide()
        self.kv['Leistung'].hide();self.kv['Leistungsgrenze'].hide()

        self.load_title=label('AUSLASTUNG UND VIDEOSPEICHER · VERLAUF', "cardTitle")
        self.body.addWidget(self.load_title)
        self.graph = ChartPanel(["Auslastung", "VRAM"], [theme.accent(), theme.secondary_accent()])
        self.body.addWidget(self.graph)
        self.h_use=deque(maxlen=900)
        self.h_vram=deque(maxlen=900)
        self.h_temp=deque(maxlen=900)
        self.h_clock=deque(maxlen=900)

        # Genuine detail-on-demand, not a second duplicate overview.
        self.more_btn = QPushButton("Technische Details anzeigen")
        self.more_btn.setCheckable(True)
        self.more_btn.toggled.connect(self._toggle_details)
        self.body.addWidget(self.more_btn)
        self.details = QWidget()
        detail_layout = QVBoxLayout(self.details)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(12)
        technical = QGridLayout()
        self.technical_grid=technical
        technical.setHorizontalSpacing(18)
        for i, name in enumerate(("PCIe aktuell", "PCIe maximal", "Datenquelle", "Mesa")):
            technical.addWidget(self.kv[name], i // 2, i % 2)
        detail_layout.addLayout(technical)
        self.sensor_hint = label(
            "Fehlende Werte bedeuten: Der Linux-Treiber liefert dafür momentan keine Daten.",
            "muted", wrap=True)
        detail_layout.addWidget(self.sensor_hint)
        self.temperature_graph = ChartPanel(["GPU-Temperatur"], [theme.accent()], mode="temperature")
        self.clock_graph = ChartPanel(["GPU-Takt"], [theme.secondary_accent()], mode="clock")
        self.temperature_title=label("TEMPERATURVERLAUF", "cardTitle")
        self.clock_title=label("TAKTVERLAUF", "cardTitle")
        detail_layout.addWidget(self.temperature_title)
        detail_layout.addWidget(self.temperature_graph)
        detail_layout.addWidget(self.clock_title)
        detail_layout.addWidget(self.clock_graph)
        self.body.addWidget(self.details)
        self.details.hide()

        self.extrema = KeyValue("GPU-Temperatur · Min/Max seit Start")
        self.body.addWidget(self.extrema)


    def _toggle_details(self, checked):
        self.details.setVisible(checked)
        self.more_btn.setText(tr("Technische Details ausblenden") if checked
                              else tr("Technische Details anzeigen"))

    def refresh(self, g, history=None, extrema=None, mesa=None):
        from .monitoring import format_range, valid_number
        for graph in (self.graph, self.temperature_graph, self.clock_graph):
            graph.set_scope(g.get('id') or g.get('name'))

        self.name.setText(g.get("name") or tr("nicht verfügbar"))
        vendor = g.get("vendor")
        driver = g.get("driver")
        self.meta.setText(g.get('board_vendor') or '')
        self.product_header.set_product(g.get('product'))
        self.product_header.set_specs([
            ('GPU', vendor), ('Videospeicher', fmt_bytes(g.get('vram_total')) if g.get('vram_total') else ''),
            ('Treiber', driver)])
        reasons = g.get('unavailable') or {}
        optional(self.kv["Auslastung"],g.get("usage"),"%",0)
        used, total = g.get("vram_used"), g.get("vram_total")
        pct = used / total * 100 if valid_number(used) and valid_number(total) and total > 0 else None
        self.kv["Videospeicher"].set(_vram_text(g) if total else "")
        self.kv["Videospeicher"].setVisible(pct is not None)

        for field, source, unit in (
            ("GPU-Takt", "clock", "MHz"), ("Speicher-Takt", "clock_mem", "MHz"),
            ("Temperatur", "temp", "°C"), ("Hotspot", "hotspot", "°C"),
            ("Spannung", "voltage", "mV"),
            ("Lüfterdrehzahl", "fan_rpm", "U/min"), ("Lüfter", "fan", "%"),
            ('VRAM-Temperatur','vram_temp','°C'), ('Speichercontroller','memory_busy','%'),
            ('Video-Engine','video_busy','%'), ('Encoder','encoder_busy','%'), ('Decoder','decoder_busy','%'),
        ):
            optional(self.kv[field],g.get(source),unit,1 if unit=='W' else 0)
        for field,source in (('Begrenzungsgründe','throttle_reasons'),('Begrenzungsflags (Treiber)','throttle_flags')):
            text=g.get(source) or ''
            self.kv[field].set(text);self.kv[field].setVisible(bool(text))
        records=g.get('hardware') or []
        power=gpu_power(g)
        optional(self.kv['Leistung'],(power or {}).get('value'),'W')
        optional(self.kv['Leistungsgrenze'],power_limit(power),'W',0)
        self.kv['Leistung'].setToolTip(source_text(power))
        self.kv['Leistungsgrenze'].setToolTip(source_text(power))
        reflow(self.live_grid,[self.kv[key] for key in self.live_fields])
        for field, source in (("PCIe aktuell", "pcie_current"), ("PCIe maximal", "pcie_max")):
            value=g.get(source)
            visible=bool(value and value not in ('–','-'))
            self.kv[field].set(value if visible else '');self.kv[field].setVisible(visible)
        for field,value in (('Datenquelle',g.get('sensor_source')),('Mesa',mesa)):
            visible=bool(value and value not in ('–','-'))
            self.kv[field].set(value if visible else '');self.kv[field].setVisible(visible)
        reflow(self.technical_grid,[self.kv[k] for k in ('PCIe aktuell','PCIe maximal','Datenquelle','Mesa')])
        self.extrema.set(format_range(extrema or {},'gpu_temp','°C',1))
        self.extrema.setVisible(number(g.get('temp')) is not None and bool((extrema or {}).get('gpu_temp')))
        self.graph.setVisible(number(g.get('usage')) is not None or pct is not None)
        self.load_title.setVisible(not self.graph.isHidden())
        self.temperature_graph.setVisible(number(g.get('temp')) is not None)
        self.clock_graph.setVisible(number(g.get('clock')) is not None)
        self.temperature_title.setVisible(not self.temperature_graph.isHidden())
        self.clock_title.setVisible(not self.clock_graph.isHidden())
        if history is None:
            self.h_use.append(g.get("usage"))
            self.h_vram.append(pct)
            self.h_temp.append(g.get("temp"))
            self.h_clock.append(g.get("clock"))
        if history:
            self.graph.set_series([
                (history.get("gpu", self.h_use), theme.accent()),
                (history.get("vram", self.h_vram), theme.secondary_accent()),
            ])
            self.temperature_graph.set_series([
                (history.get("gpu_temp", self.h_temp), theme.accent())])
            self.clock_graph.set_series([
                (history.get("gpu_clock", self.h_clock), theme.secondary_accent())])
        else:
            self.graph.set_series([(self.h_use, theme.accent()),
                                   (self.h_vram, theme.secondary_accent())])
            self.temperature_graph.set_series([(self.h_temp, theme.accent())])
            self.clock_graph.set_series([(self.h_clock, theme.secondary_accent())])


class GpuPage(Page):
    def __init__(self):
        super().__init__("Grafik", "GPU-Auslastung, Videospeicher und Sensoren")
        self.cards = []
        from .ui_locale import QComboBox
        self.primary_card = Card('Bevorzugte Grafikkarte')
        self.primary_choice = QComboBox()
        self.primary_choice.currentIndexChanged.connect(self._select_primary)
        self.primary_card.body.addWidget(self.primary_choice)
        self.primary_card.body.addWidget(label('Für Übersicht, Desktop-Overlay und Diagnosen. Alle Grafikkarten bleiben hier sichtbar.', 'muted', wrap=True))
        self.content.addWidget(self.primary_card)
        self.primary_card.hide()
        self._mesa = system_static().get("mesa")
        self.none = Card()
        self.none.body.addWidget(label(
            "Keine GPU-Daten gefunden. Unterstützt werden NVIDIA, AMD und Intel, "
            "soweit Linux entsprechende Sensorwerte liefert.", wrap=True))
        self.content.addWidget(self.none)

    def _select_primary(self, *_):
        from . import settings
        settings.set('primary_gpu', self.primary_choice.currentData() or '')
        window = self.window()
        if hasattr(window, 'select_primary_gpu'):
            window.select_primary_gpu()

    def refresh(self, d, h):
        from . import settings
        from .monitoring import GpuHistory
        gpus = d.get("gpus") or []
        choices = [('', tr('Automatisch'))] + sorted((GpuHistory.identity(g, i), g.get('name') or GpuHistory.identity(g, i)) for i, g in enumerate(gpus))
        if choices != getattr(self, '_primary_choices', None):
            self._primary_choices = choices
            self.primary_choice.blockSignals(True)
            self.primary_choice.clear()
            for key, name in choices:
                self.primary_choice.addItem(name, key)
            self.primary_choice.setCurrentIndex(max(0, self.primary_choice.findData(settings.get('primary_gpu', ''))))
            self.primary_choice.blockSignals(False)
        self.primary_card.setVisible(len(gpus) > 1)
        self.none.setVisible(not gpus)
        while len(self.cards) < len(gpus):
            card = GpuCard()
            self.content.insertWidget(1 + len(self.cards), card)
            self.cards.append(card)
            self.register_charts(card)
            for chart in card.findChildren(ChartPanel):chart.set_timeline(h.get("time", []))
        recorder=getattr(self.window(),'gpu_history',None)
        for i, card in enumerate(self.cards):
            card.setVisible(i < len(gpus))
            if i < len(gpus):
                card.refresh(
                    gpus[i], history=recorder.get(gpus[i],i) if recorder is not None else h if i==0 else None,
                    extrema=d.get('gpu_extrema', {}).get(GpuHistory.identity(gpus[i], i), d.get("session_extrema") if i == 0 else None),
                    mesa=self._mesa)


class MemoryPage(Page):
    def __init__(self):
        super().__init__("Arbeitsspeicher", "RAM und Swap")
        self.module_cards = []
        self.g_ram, self.g_swap = GaugeCard("RAM"), GaugeCard("Swap")
        stats = Card("Details")
        self.kv = {k: KeyValue(k) for k in ('Leistung','Leistungsgrenze',"Gesamt", "In Benutzung", "Verfügbar", "Cache", "Puffer")}
        for w in self.kv.values():
            stats.body.addWidget(w)
        self.kv['Leistung'].hide();self.kv['Leistungsgrenze'].hide()
        self.content.addLayout(_row(self.g_ram, self.g_swap, stats))
        graph = Card("Verlauf")
        self.graph = ChartPanel(['RAM'], [theme.TEAL])
        graph.body.addWidget(self.graph)
        self.content.addWidget(graph)
        self.hardware=SensorPanel(include_power=False)
        self.content.addWidget(self.hardware)

    def refresh(self, d, h):
        r = d["ram"]
        grouped = {}
        for module in r.get('modules', []):
            identity = tuple(module.get(k) for k in ('vendor','model','capacity','memory_type','speed'))
            grouped.setdefault(identity, []).append(module)
        groups = list(grouped.values())
        while len(self.module_cards) < len(groups):
            card = Card()
            name, meta = label('', 'bigName', wrap=True), label('', 'muted', wrap=True)
            header = ProductHeader(name, meta, 'ram')
            card.body.addWidget(header)
            self.content.insertWidget(len(self.module_cards), card)
            self.module_cards.append((card, header, name, meta))
        for index, (card, header, name, meta) in enumerate(self.module_cards):
            card.setVisible(index < len(groups))
            if index >= len(groups):continue
            modules = groups[index];module = modules[0]
            name.setText(module.get('model') or tr('Arbeitsspeicher'))
            meta.setText(module.get('vendor') or '')
            header.set_product(module.get('product'))
            speed = module.get('speed')
            detail = ' · '.join(str(x) for x in (module.get('memory_type'),f'{speed} MT/s' if speed else '') if x)
            header.set_specs([
                ('Kapazität', f'{len(modules)} × {fmt_bytes(module.get("capacity"))}'),
                ('Speichertyp', detail),
                ('Steckplatz', ', '.join(m.get('slot','') for m in modules if m.get('slot')))])
        power=component_power(d.get('hardware',[]),'ram')
        optional(self.kv['Leistung'],(power or {}).get('value'),'W')
        optional(self.kv['Leistungsgrenze'],power_limit(power),'W')
        self.kv['Leistung'].setToolTip(source_text(power))
        self.hardware.sync([r for r in d.get('hardware',[]) if r['component']=='ram'])
        self.g_ram.set(r["percent"], f"{fmt_bytes(r['used'])} / {fmt_bytes(r['total'])}")
        if r["swap_total"]:
            self.g_swap.set(r["swap_percent"], f"{fmt_bytes(r['swap_used'])} / {fmt_bytes(r['swap_total'])}")
        else:
            self.g_swap.set(None, "nicht aktiv")
        self.kv["Gesamt"].set(fmt_bytes(r["total"]))
        self.kv["In Benutzung"].set(fmt_bytes(r["used"]))
        self.kv["Verfügbar"].set(fmt_bytes(r["available"]))
        self.kv["Cache"].set(fmt_bytes(r["cached"]))
        self.kv["Puffer"].set(fmt_bytes(r["buffers"]))
        self.graph.set_series([(h['ram'],theme.TEAL)])
