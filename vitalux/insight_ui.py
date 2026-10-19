"""Native, theme-aware, read-only Vitalux Insights panel and focus window."""
from __future__ import annotations


from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QFont
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLineEdit, QListWidget, QListWidgetItem, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsSimpleTextItem, QFileDialog,
    QComboBox, QFrame,
)
from .ui_locale import QPushButton, QCheckBox, QMessageBox
from .widgets import Card, ChartPanel, label
from . import theme, settings, sensors
from .i18n import tr
from .insight_engine import FIELDS, telemetry, number


METRIC_TITLES = {
    "cpu_usage": ("CPU", "%"), "cpu_temp": ("CPU-Temperatur", "°C"),
    "gpu_usage": ("GPU", "%"), "gpu_temp": ("GPU-Temperatur", "°C"),
    "gpu_clock": ("GPU-Takt", "MHz"), "gpu_power": ("GPU-Leistung", "W"),
    "ram_usage": ("RAM", "%"), "vram_usage": ("VRAM", "%"),
}


def fmt(value, unit, digits=1):
    return f"{value:.{digits}f} {unit}" if number(value) else tr("nicht verfügbar")


class FocusWindow(QWidget):
    """Independent movable Qt window for a second monitor; no sampling thread."""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Vitalux · Fokusmodus")
        self.setMinimumSize(430, 290)
        self.resize(660, 380)
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(label("LIVE · FOKUSMODUS", "cardTitle"), 1)
        self.ontop = QCheckBox("Immer im Vordergrund")
        self.ontop.toggled.connect(self._on_top)
        header.addWidget(self.ontop)
        layout.addLayout(header)
        grid = QGridLayout()
        grid.setSpacing(12)
        self.entries = []
        for i, key in enumerate(("gpu_usage", "gpu_temp", "cpu_usage", "vram_usage")):
            card = QGroupBox()
            card.setObjectName("insightGroup")
            col = QVBoxLayout(card)
            choose = QComboBox()
            for metric, (title, _unit) in METRIC_TITLES.items():
                choose.addItem(tr(title), metric)
            choose.setCurrentIndex(choose.findData(key))
            reading = QLabel("–")
            reading.setAlignment(Qt.AlignCenter)
            reading.setObjectName("focusReading")
            reading.setStyleSheet(f"color: {theme.accent()}; font-size: 29px; font-weight: 800;")
            col.addWidget(choose)
            col.addWidget(reading, 1)
            grid.addWidget(card, i // 2, i % 2)
            self.entries.append((choose, reading))
        layout.addLayout(grid, 1)
        layout.addWidget(label("Nur vorhandene Sensordaten – keine Übertaktung oder Hardwaresteuerung.",
                               "muted", wrap=True))

    def retranslate(self):
        self.setWindowTitle(tr("Vitalux · Fokusmodus"))
        for choose, reading in self.entries:
            for idx in range(choose.count()):
                key = choose.itemData(idx)
                choose.setItemText(idx, tr(METRIC_TITLES[key][0]))
            reading.setStyleSheet(
                f"color: {theme.accent()}; font-size: 29px; font-weight: 800;")

    def _on_top(self, enabled):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.show()

    def update_sample(self, sample):
        values = telemetry(sample)
        for choose, reading in self.entries:
            key = choose.currentData()
            reading.setText(fmt(values.get(key), METRIC_TITLES[key][1]))


class MonitoringLabPanel(QWidget):
    """Optional analytical tools beneath the existing Grafikkarte information."""
    def __init__(self, lab, open_focus):
        super().__init__()
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(10)
        self.body.addWidget(label('Performance & Insights', 'cardTitle'))
        self.lab = lab
        self._open_focus = open_focus
        self.last_sample = None
        self._last_findings = None
        self._static = sensors.system_static()

        self.intro = label(
            "Rein lesende Analyse · gemessene Fakten und mögliche Ursachen werden unterschieden.",
            "muted", wrap=True)
        self.body.addWidget(self.intro)
        self.focus = QPushButton("Fokusmodus für zweiten Monitor öffnen")
        self.focus.clicked.connect(self._open_focus)
        self.body.addWidget(self.focus)

        self.detector = QGroupBox("Performance Detective")
        dl = QVBoxLayout(self.detector)
        self.findings = QLabel(tr("Warte auf Messwerte …"))
        self.findings.setWordWrap(True)
        dl.addWidget(self.findings)
        self.body.addWidget(self.detector)

        self.trend_group = QGroupBox("Performance-Verlauf")
        trend_layout = QVBoxLayout(self.trend_group)
        self.trend_chart = ChartPanel(
            ["CPU", "GPU", "VRAM"],
            [theme.accent(), theme.secondary_accent(), theme.TEAL])
        trend_layout.addWidget(self.trend_chart)
        trend_layout.addWidget(label(
            "Gemeinsamer Verlauf der Auslastung. Zeitraum und Datenreihen frei wählbar.",
            "muted", wrap=True))
        self.body.addWidget(self.trend_group)

        self.record_group = QGroupBox("Gaming Session Analyzer")
        rg = QVBoxLayout(self.record_group)
        controls = QHBoxLayout()
        self.session_name = QLineEdit()
        self.session_name.setPlaceholderText("Sitzungsname, z. B. CS2 oder Cyberpunk")
        self.begin = QPushButton("Aufzeichnung starten")
        self.end = QPushButton("Stoppen & auswerten")
        self.begin.clicked.connect(self._begin_session)
        self.end.clicked.connect(self._stop_session)
        controls.addWidget(self.session_name, 1)
        controls.addWidget(self.begin)
        controls.addWidget(self.end)
        rg.addLayout(controls)
        buttons = QHBoxLayout()
        self.import_log = QPushButton("MangoHud-CSV importieren")
        self.import_log.clicked.connect(self._import_mangohud)
        self.save_session = QPushButton("Sitzung als JSON speichern")
        self.save_session.clicked.connect(self._save_session)
        buttons.addWidget(self.import_log)
        buttons.addWidget(self.save_session)
        rg.addLayout(buttons)
        self.session_report = QLabel(tr("Noch keine Gaming-Sitzung abgeschlossen."))
        self.session_report.setWordWrap(True)
        rg.addWidget(self.session_report)
        rg.addWidget(label("FPS und 1%-Lows nur aus importierten MangoHud-Daten; "
                           "1%-Low ist bei Stichproben ein Näherungswert.", "muted", wrap=True))
        self.body.addWidget(self.record_group)

        self.show_advanced = QPushButton("Analysewerkzeuge einklappen")
        self.show_advanced.setCheckable(True)
        self.show_advanced.setChecked(True)
        self.show_advanced.toggled.connect(self._advanced_visible)
        # Keep the primary observation on top; other tools can be collapsed.
        self.body.insertWidget(2, self.show_advanced)
        self._tools = (self.trend_group, self.record_group)
        for group in (self.detector, *self._tools):
            group.setObjectName("insightGroup")
        self._advanced_visible(False)
        self.show_advanced.setChecked(False)
        self._update_session()
        self._update_comparison()

    def retranslate(self):
        for group, title in (
            (self.detector, "Performance Detective"),
            (self.trend_group, "Performance-Verlauf"),
            (self.record_group, "Gaming Session Analyzer"),
        ):
            group.setTitle(tr(title))
        self._advanced_visible(self.show_advanced.isChecked())

    def _advanced_visible(self, shown):
        for widget in getattr(self, "_tools", ()):
            widget.setVisible(shown)
        self.show_advanced.setText(tr("Analysewerkzeuge einklappen") if shown
                                   else tr("Analysewerkzeuge anzeigen"))

    def _begin_session(self):
        try:
            self.lab.start_session(self.session_name.text())
        except ValueError as exc:
            QMessageBox.warning(self, "Vitalux", str(exc))
        self._update_session()

    def _stop_session(self):
        try:
            self.lab.stop_session()
        except ValueError as exc:
            QMessageBox.warning(self, "Vitalux", str(exc))
        self._update_session()

    def _import_mangohud(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, tr("MangoHud-Protokoll öffnen"), "", "CSV (*.csv);;Alle Dateien (*)")
        if not filename:
            return
        try:
            self.lab.import_mangohud(filename)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Vitalux", str(exc))
        self._update_session()

    def _save_session(self):
        if not self.lab.last_session:
            QMessageBox.information(self, "Vitalux", tr("Noch keine Gaming-Sitzung abgeschlossen."))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Gaming-Sitzung speichern"), "Vitalux-Gaming-Session.json", "JSON (*.json)")
        if not path:
            return
        try:
            self.lab.export_session(path if path.lower().endswith(".json") else path + ".json")
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Vitalux", str(exc))

    def _update_session(self):
        live = self.lab.started is not None
        self.begin.setEnabled(not live)
        self.end.setEnabled(live)
        self.save_session.setEnabled(self.lab.last_session is not None)
        if live:
            self.session_report.setText(
                f"Aufzeichnung läuft: {self.lab.session_name} · {self.lab.session_count} Messpunkte")
            return
        report = self.lab.last_session
        if report:
            parts = [f"{report['name']} · {report['samples']} Messpunkte"]
            for key in ("gpu_usage", "gpu_temp", "gpu_clock", "cpu_usage", "vram_usage"):
                data = report["metrics"].get(key)
                if data:
                    title, unit = METRIC_TITLES[key]
                    parts.append(f"{title}: Ø {fmt(data['avg'],unit)}, "
                                 f"Min {fmt(data['min'],unit)}, Max {fmt(data['max'],unit)}")
            if self.lab.mangohud:
                hud = self.lab.mangohud
                parts.append(f"MangoHud ({hud['source']}): "
                             f"Ø FPS {_f(hud.get('avg_fps'))}; "
                             f"1%-Low ≈ {_f(hud.get('one_percent_low_approx'))}")
            self.session_report.setText("\n".join(parts))
        elif self.lab.mangohud:
            hud = self.lab.mangohud
            self.session_report.setText(
                f"MangoHud: Ø FPS {_f(hud.get('avg_fps'))} · "
                f"1%-Low ≈ {_f(hud.get('one_percent_low_approx'))}")
        else:
            self.session_report.setText(tr("Noch keine Gaming-Sitzung abgeschlossen."))

    def refresh(self, sample):
        self.last_sample = sample
        result = self.lab.detective({
            key: settings.get(key, default)
            for key, default in (("cpu_temp", 90), ("gpu_temp", 90),
                                 ("ram_usage", 90))
        })
        signature = tuple((name, detail) for name, detail, _ in result)
        if self._last_findings != signature:
            self._last_findings = signature
            self.findings.setText("\n\n".join(f"• {name}: {detail}"
                                             for name, detail, _ in result))
        self._update_session()
        if self.show_advanced.isChecked():
            rows = list(self.lab.history)[-900:]
            self.trend_chart.set_series([
                ([row["metrics"].get(metric) for row in rows], color)
                for metric, color in (
                    ("cpu_usage", theme.accent()),
                    ("gpu_usage", theme.secondary_accent()),
                    ("vram_usage", theme.TEAL),
                )
            ])


def _f(value):

def _f(value):
    return f"{value:.1f}" if number(value) else "–"
