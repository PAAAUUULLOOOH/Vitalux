"""Read-only network and system pages."""
import platform

import PySide6
from PySide6.QtCore import qVersion
from PySide6.QtWidgets import QVBoxLayout, QWidget, QTabWidget

from . import theme
from .ui_locale import QPushButton
from .i18n import tr
from .sensors import fmt_bytes, fmt_duration, fmt_rate, system_static
from .monitor_extra import graphics_runtime, system_gpu_device
from .widgets import Card, KeyValue, label
from .charts import ChartPanel
from .sensor_ui import SensorPanel
from .product_ui import ProductHeader


from .page_base import Page, _row


class NetworkPage(Page):
    def __init__(self):
        super().__init__("Netzwerk", "Live-Datenverkehr, Schnittstellen und Verbindungsdetails")
        page_content=self.content
        self.tabs=QTabWidget()
        overview=QWidget()
        self.content=QVBoxLayout(overview)
        self.content.setContentsMargins(0,12,0,0)
        self.content.setSpacing(14)
        top = Card(hero=True)
        self.primary = KeyValue("Aktive Schnittstelle")
        self.addr = KeyValue("IPv4")
        self.total = KeyValue("Daten gesamt")
        self.speed = KeyValue("Link-Geschwindigkeit")
        self.gateway = KeyValue('Gateway')
        self.dns = KeyValue('DNS-Server')
        self.mac = KeyValue('MAC-Adresse')
        top.body.addWidget(self.primary)
        top.body.addWidget(self.addr)
        top.body.addWidget(self.total)
        top.body.addWidget(self.speed)
        top.body.addWidget(self.gateway)
        top.body.addWidget(self.dns)
        top.body.addWidget(self.mac)
        self.content.addWidget(top)

        graph = Card("Netzwerk-Verlauf")
        self.graph = ChartPanel(['Download','Upload'],[theme.accent(),theme.secondary_accent()],mode='rate')
        graph.body.addWidget(self.graph)
        rates = Card("Aktuelle Übertragungsraten")
        self.down = KeyValue("Download")
        self.up = KeyValue("Upload")
        rates.body.addWidget(self.down)
        rates.body.addWidget(self.up)

        self.ifaces_card = Card("Netzwerkschnittstellen")
        self.iface_rows = {}
        self.content.addWidget(rates)
        self.content.addWidget(graph)
        self.content.addWidget(self.ifaces_card)
        self.hardware=SensorPanel()
        self.content.addWidget(self.hardware)
        from .network_ui import NetworkWatch
        self.watcher=NetworkWatch()
        self.tabs.addTab(overview,tr('Übersicht'))
        self.tabs.addTab(self.watcher,tr('Programme & Verbindungen').replace('&','&&'))
        self.content=page_content
        self.content.addWidget(self.tabs)

    def retranslate(self):
        self.tabs.setTabText(0,tr('Übersicht'))
        self.tabs.setTabText(1,tr('Programme & Verbindungen').replace('&','&&'))
        self.watcher.retranslate()

    def shutdown(self):
        return self.watcher.shutdown()

    def refresh(self, d, h):
        net = d["net"]
        self.hardware.sync([r for r in d.get('hardware',[]) if r['component']=='network'])
        p = net.get("primary") or {}
        self.primary.set(p.get("name", "–"))
        self.addr.set(p.get("ipv4") or "–")
        self.total.set(f"↓ {fmt_bytes(net['total_down'])}   ·   ↑ {fmt_bytes(net['total_up'])}")
        self.speed.set(f"{p.get('speed', 0)} Mbit/s" if p.get("speed") else "–")
        self.gateway.set(net.get('gateway') or '–')
        self.dns.set(', '.join(net.get('dns', [])) or '–')
        self.mac.set(p.get('mac') or '–')
        self.down.set(fmt_rate(net["down"]))
        self.up.set(fmt_rate(net["up"]))
        self.graph.set_series([(h['net_down'],theme.accent()),(h['net_up'],theme.secondary_accent())])
        for iface in net.get("interfaces", []):
            row = self.iface_rows.get(iface["name"])
            if row is None:
                row = self.iface_rows[iface["name"]] = KeyValue(iface["name"])
                self.ifaces_card.body.addWidget(row)
            state = "UP" if iface["isup"] else "DOWN"
            speed = f"{iface['speed']} Mbit/s" if iface["speed"] else "–"
            ip = iface.get("ipv4") or iface.get("ipv6") or tr('keine IP')
            row.set(f"{state} · {speed} · {ip}")


class SystemPage(Page):
    def __init__(self, distro):
        super().__init__("System", "Betriebssystem, Hardware und Software")
        s = system_static()
        product = s.get('board_product') or {}
        self.board_card = Card('Mainboard')
        self.board_name = label(product.get('model') or s.get('board') or '–', 'bigName', wrap=True)
        revision = product.get('revision')
        self.board_meta = label(product.get('vendor') or '', 'muted', wrap=True)
        self.board_header = ProductHeader(self.board_name, self.board_meta, 'mainboard')
        self.board_header.set_product(product)
        self.board_header.set_specs([('Revision', revision), ('BIOS', s.get('bios'))])
        self.board_card.body.addWidget(self.board_header)
        self.content.addWidget(self.board_card)
        os_card = Card("Betriebssystem")
        self.uptime = KeyValue("Laufzeit")
        for k, v in (("Distribution", distro["name"]), ("Kernel", s["kernel"]), ("Architektur", s["arch"]),
                     ("Rechnername", s["host"]), ("Benutzer", s["user"]), ("Desktop", s["desktop"]),
                     ("Sitzung", s["session"])):
            kv = KeyValue(k)
            kv.set(v)
            os_card.body.addWidget(kv)
        os_card.body.addWidget(self.uptime)

        hw_card = Card("Hardware")
        self.cpu_kv, self.gpu_kv = KeyValue("Prozessor"), KeyValue("Grafik")
        for k, v in (("Hersteller", s["vendor"]), ("Modell", s["product"]),
                     ("BIOS", s["bios"])):
            kv = KeyValue(k)
            kv.set(v)
            hw_card.body.addWidget(kv)
        hw_card.body.addWidget(self.cpu_kv)
        hw_card.body.addWidget(self.gpu_kv)

        sw_card = Card("Software")
        for k, v in (("Python", platform.python_version()), ("Qt", qVersion()), ("PySide6", PySide6.__version__),
                     ("KDE Plasma", s["plasma"]), ("KWin", s["kwin"]), ("KDE Frameworks", s["frameworks"]),
                     ("Mesa", s["mesa"])):
            kv = KeyValue(k)
            kv.set(v)
            sw_card.body.addWidget(kv)
        self.content.addLayout(_row(os_card, hw_card))
        self.content.addWidget(sw_card)
        graphics_card = Card('Grafiksystem & Anzeigen')
        from PySide6.QtGui import QGuiApplication
        runtime = graphics_runtime(QGuiApplication.platformName(), QGuiApplication.screens())
        for title, value in (('Qt-Grafikbackend', runtime['qt_platform']),
                             ('Display-Server', runtime['runtime']),
                             ('Sitzungstyp', runtime['session'])):
            kv = KeyValue(title)
            kv.set(value)
            graphics_card.body.addWidget(kv)
        for idx, screen in enumerate(runtime['screens'], 1):
            rate = f" · {screen['hz']:g} Hz" if screen['hz'] is not None else ''
            kv = KeyValue(f'Bildschirm {idx} · {screen["name"]}')
            scale = f" · {screen['scale_percent']} % {tr('Skalierung')}" if screen.get('scale_percent', 100) != 100 else ''
            kv.set(f"{screen['width']} × {screen['height']}{rate}{scale}")
            graphics_card.body.addWidget(kv)
        self.render_gpu = KeyValue('Erkannte Grafik / mögliche Render-GPU')
        graphics_card.body.addWidget(self.render_gpu)
        self.render_driver = KeyValue('Grafiktreiber')
        graphics_card.body.addWidget(self.render_driver)
        graphics_card.body.addWidget(label('Bei mehreren GPUs lässt sich das aktive Rendergerät ohne zusätzliche Abfrage nicht immer eindeutig bestimmen.', 'muted', wrap=True))
        self.content.addWidget(graphics_card)
        perf_card = Card('Vitalux · Ressourcenverbrauch')
        self.app_cpu = KeyValue('Vitalux CPU')
        self.app_ram = KeyValue('Vitalux RAM')
        self.app_paint = KeyValue('Messwert-Aktualisierung')
        perf_card.body.addWidget(self.app_cpu)
        perf_card.body.addWidget(self.app_ram)
        perf_card.body.addWidget(self.app_paint)
        self.content.addWidget(perf_card)

        self.status_card = Card("Hardware-Status")
        self.status_rows = {title: KeyValue(title) for title in (
            "CPU", "GPU", "RAM", "Systemlaufwerk")}
        for row in self.status_rows.values():
            self.status_card.body.addWidget(row)
        self.status_card.body.addWidget(label(
            "Status nach realen Messwerten und eingestellten Warnwerten; "
            "keine Schätzung des Hardwarezustands.", "muted", wrap=True))
        self.reset_btn = QPushButton("Min-/Max-Werte zurücksetzen")
        self.reset_btn.clicked.connect(self._reset_session)
        self.status_card.body.addWidget(self.reset_btn)
        self.content.addWidget(self.status_card)
        self.hardware=SensorPanel()
        self.content.addWidget(self.hardware)

    def _reset_session(self):
        main = self.window()
        if hasattr(main, "reset_session_extrema"):
            main.reset_session_extrema()

    def refresh(self, d, h):
        from .monitoring import hardware_status
        self.hardware.sync([r for r in d.get('hardware',[]) if r['component']=='system'])
        from . import settings
        limits = {name: settings.get(name, default) for name, default in (
            ("cpu_temp", 90), ("gpu_temp", 90),
            ("ram_usage", 90), ("disk_usage", 95))}
        status = dict(hardware_status(d, limits))
        for key, row in self.status_rows.items():
            row.set(status.get(key, tr("nicht verfügbar")))
        self.render_gpu.set(system_gpu_device(d['gpus']))
        self.render_driver.set(', '.join(dict.fromkeys(str(g.get('driver')) for g in d['gpus'] if g.get('driver'))) or '–')
        app = d.get('app_resources') or {}
        self.app_cpu.set(f"{app['cpu_percent']:.1f} %" if app.get('cpu_percent') is not None else '–')
        self.app_ram.set(fmt_bytes(app.get('rss_bytes')))
        # The render duration is measured by the main window after paint data dispatch.
        from PySide6.QtWidgets import QApplication
        window = QApplication.activeWindow()
        duration = getattr(window, 'last_render_ms', None)
        self.app_paint.set(f'{duration:.1f} ms' if duration is not None else '–')
        self.uptime.set(fmt_duration(d["uptime"]))
        self.cpu_kv.set(d["cpu"]["model"])
        self.gpu_kv.set(", ".join(g["name"] for g in d["gpus"]) or "–")
