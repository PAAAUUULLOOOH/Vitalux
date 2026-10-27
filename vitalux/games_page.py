"""Installed games, per-game MangoHud setup and automatic post-game reports."""
from datetime import datetime
from pathlib import Path
import math
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QColor, QDesktopServices, QImageReader, QPainter, QPen, QPixmap
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (QDialog, QFormLayout, QGridLayout, QLineEdit,
                              QHBoxLayout, QScrollArea, QSpinBox, QTableWidget,
                              QTableWidgetItem, QVBoxLayout, QWidget)
from . import game_profiles, theme
from .choice_combo import ChoiceComboBox
from .game_service import GameService
from .i18n import tr
from .page_base import Page
from .ui_locale import QCheckBox, QLabel, QPushButton, QMessageBox
from .widgets import Card, label
from .charts import ChartPanel

GRADES = dict(excellent='Sehr gut', good='Gut', adequate='Ausreichend',
              improve='Verbesserungsbedürftig', incomplete='Unvollständig',
              insufficient='Zu wenige Messdaten')
METRIC_NAMES = dict(fps='FPS', frametime='Frametime', frame_timing='Frametime-Diagramm',
                    cpu_stats='CPU-Auslastung', cpu_temp='CPU-Temperatur', cpu_power='CPU-Verbrauch',
                    gpu_stats='GPU-Auslastung', gpu_temp='GPU-Temperatur', gpu_power='GPU-Verbrauch',
                    ram='Arbeitsspeicher', vram='Videospeicher', io_read='Lesen', io_write='Schreiben')


def shown(value, suffix='', digits=0):
    if value is None or not isinstance(value, (float, int)) or not math.isfinite(value):
        return '–'
    return f'{value:.{digits}f}'+suffix


def duration(seconds):
    seconds = max(0, int(seconds or 0))
    return tr('{minutes} min {seconds} s').format(minutes=seconds//60, seconds=seconds % 60)


def date_text(stamp):
    from .i18n import lang
    return datetime.fromtimestamp(stamp).strftime('%d.%m.%Y · %H:%M' if lang() == 'de' else '%Y-%m-%d · %H:%M')


class GameTile(Card):
    selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.game_id = ''
        self.checked = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.layout().setContentsMargins(12, 12, 12, 12)
        row = QHBoxLayout()
        row.setSpacing(12)
        self.cover = QLabel()
        self.cover.setFixedSize(70, 82)
        self.cover.setAlignment(Qt.AlignCenter)
        row.addWidget(self.cover)
        text = QVBoxLayout()
        self.name = label('', 'strong', wrap=True)
        self.name.setTextFormat(Qt.PlainText)
        self.name.setMaximumHeight(42)
        self.source = label('', 'muted')
        self.result = label('', 'strong')
        text.addWidget(self.name)
        text.addWidget(self.source)
        text.addWidget(self.result)
        row.addLayout(text, 1)
        self.body.addLayout(row)
        self.setMinimumWidth(190)
        self.setMaximumHeight(128)
        self._cover_identity = None

    def set_game(self, game, checked):
        self.game_id, self.checked = game['id'], checked
        self.name.setText(game['name'])
        self.name.setToolTip(game['name'])
        self.setAccessibleName(game['name'])
        self.source.setText(tr('Letzte Sitzung') if game.get('latest') else
                            ('Steam' if game['store'] == 'steam' else game['store'].title()))
        self.result.setText(tr(GRADES.get((game.get('latest') or {}).get('grade'), 'Noch keine Sitzung'))
                            if game.get('installed') else tr('Nicht installiert'))
        self.setAccessibleName(game['name'])
        self.setAccessibleDescription(self.result.text())
        path = Path(game.get('cover') or '')
        identity = (str(path), path.stat().st_mtime_ns) if path.is_file() else None
        if identity != self._cover_identity or self.cover.pixmap().isNull():
            self._cover_identity = identity
            pixmap = QPixmap()
            if identity and path.stat().st_size <= 12*1024*1024:
                reader = QImageReader(str(path))
                size = reader.size()
                if size.isValid() and size.width()*size.height() <= 60_000_000:
                    reader.setScaledSize(size.scaled(140, 164, Qt.KeepAspectRatio))
                    image = reader.read()
                    if not image.isNull():
                        pixmap = QPixmap.fromImage(image)
                        pixmap.setDevicePixelRatio(2)
            self.cover.setPixmap(pixmap)
            self.cover.setText('' if not pixmap.isNull() else '◇')
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.selected.emit(self.game_id)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.selected.emit(self.game_id)
            event.accept()
            return
        super().keyPressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.selected.emit(self.game_id)
            event.accept()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.checked or self.hasFocus():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(QColor(theme.accent()), 1.5))
            painter.setBrush(Qt.NoBrush)
            from . import signature_designs
            rect = QRectF(self.rect()).adjusted(3, 3, -3, -3)
            if signature_designs.active():
                painter.drawPath(signature_designs.shape(rect, theme.mode()))
            else:
                painter.drawRoundedRect(rect, 17, 17)
            painter.end()


class OverlayProfile(QDialog):
    def __init__(self, page, game):
        super().__init__(page.window())
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.page, self.game = page, game
        self.setWindowTitle(tr('Overlay-Profil')+' · '+game['name'])
        self.resize(620, 720)
        root = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        body = QWidget()
        form = QVBoxLayout(body)
        title = label(game['name'], 'bigName', wrap=True)
        title.setTextFormat(Qt.PlainText)
        form.addWidget(title)
        self.notice = label('', 'muted', wrap=True)
        form.addWidget(self.notice)
        profile = game_profiles.load(game['id'])
        self.enabled = QCheckBox('Overlay und Aufzeichnung für dieses Spiel aktivieren')
        self.enabled.setChecked(profile['enabled'])
        form.addWidget(self.enabled)
        choices = QFormLayout()
        self.target = QSpinBox()
        self.target.setRange(20, 1000)
        self.target.setValue(profile['target_fps'])
        self.target.setSuffix(' FPS')
        choices.addRow(label('FPS-Ziel für die Bewertung', 'strong'), self.target)
        self.position = ChoiceComboBox()
        for key, title in zip(game_profiles.POSITIONS, ('Oben links', 'Oben rechts', 'Unten links',
                             'Unten rechts', 'Oben mittig', 'Unten mittig')):
            self.position.addItem(tr(title), key)
        self.position.setCurrentIndex(self.position.findData(profile['position']))
        choices.addRow(label('Position', 'strong'), self.position)
        self.size = QSpinBox();self.size.setRange(12, 40);self.size.setValue(profile['font_size'])
        choices.addRow(label('Schriftgröße', 'strong'), self.size)
        self.opacity = QSpinBox();self.opacity.setRange(0, 100);self.opacity.setSuffix(' %')
        self.opacity.setValue(round(profile['background_alpha']*100))
        choices.addRow(label('Hintergrund-Deckkraft', 'strong'), self.opacity)
        self.warmup = QSpinBox();self.warmup.setRange(1, 120);self.warmup.setSuffix(' s')
        self.warmup.setValue(profile['warmup'])
        choices.addRow(label('Aufzeichnung nach Spielstart', 'strong'), self.warmup)
        self.hud_key = QLineEdit(profile['toggle_hud'])
        self.log_key = QLineEdit(profile['toggle_logging'])
        choices.addRow(label('Overlay-Tastenkürzel', 'strong'), self.hud_key)
        choices.addRow(label('Aufzeichnungs-Tastenkürzel', 'strong'), self.log_key)
        form.addLayout(choices)
        self.horizontal = QCheckBox('Metriken als horizontale Zeile anzeigen')
        self.horizontal.setChecked(profile['horizontal'])
        form.addWidget(self.horizontal)
        form.addWidget(label('Metriken im Spiele-Overlay', 'strong'))
        grid = QGridLayout()
        self.metrics = {}
        for index, key in enumerate(game_profiles.METRICS):
            checkbox = QCheckBox(tr(METRIC_NAMES[key]))
            checkbox.setProperty('selectionControl', True)
            checkbox.setChecked(key in profile['metrics'])
            self.metrics[key] = checkbox
            grid.addWidget(checkbox, index//2, index % 2)
        form.addLayout(grid)
        form.addWidget(label('Änderungen gelten beim nächsten Spielstart. MangoHud zeichnet einzelne Framezeiten auf. '
                            'Vitalux muss für die automatische Auswertung im Hintergrund laufen.', 'muted', wrap=True))
        form.addWidget(label('Die ersten Sekunden werden nach der gewählten Wartezeit aufgezeichnet. '
                            'Menüs und Ladephasen bleiben Teil der Messung; die Aufnahme kann per Tastenkürzel unterbrochen werden.',
                            'muted', wrap=True))
        self.connection = QPushButton('Mit Launcher verbinden')
        self.connection.setObjectName('ghostBtn')
        self.connection.clicked.connect(self._connection)
        form.addWidget(self.connection)
        form.addWidget(label('Beende den Launcher zum Einrichten oder Entfernen der Verbindung. '
                            'Vorhandene Startargumente bleiben erhalten. Für Flatpak wird die passende MangoHud-Erweiterung benötigt.',
                            'muted', wrap=True))
        scroll.setWidget(body)
        root.addWidget(scroll, 1)
        actions = QHBoxLayout()
        cancel = QPushButton('Schließen');cancel.setObjectName('ghostBtn');cancel.clicked.connect(self.reject)
        save = QPushButton('Speichern');save.setObjectName('primaryBtn');save.clicked.connect(self._save_close)
        self.save_button = save
        actions.addStretch();actions.addWidget(cancel);actions.addWidget(save);root.addLayout(actions)
        self.update_game(game)

    def update_game(self, game):
        self.game = game
        connected = bool(game.get('connected'))
        self.connection.setText(tr('Verbindung entfernen' if connected else 'Mit Launcher verbinden'))
        self.notice.setText(tr('MangoHud bereit' if game.get('mangohud_available') else
                              'MangoHud fehlt. Installiere MangoHud bzw. die passende Flatpak-Erweiterung und prüfe erneut.'))
        self.connection.setEnabled(connected or bool(game.get('mangohud_available')))

    def _save(self):
        profile = dict(enabled=self.enabled.isChecked(), target_fps=self.target.value(),
                       position=self.position.currentData(), font_size=self.size.value(),
                       background_alpha=self.opacity.value()/100, warmup=self.warmup.value(),
                       toggle_hud=self.hud_key.text().strip(), toggle_logging=self.log_key.text().strip(),
                       horizontal=self.horizontal.isChecked(),
                       metrics=[key for key, checkbox in self.metrics.items() if checkbox.isChecked()])
        for key in ('toggle_hud', 'toggle_logging'):
            if game_profiles.normalize(profile)[key] != profile[key]:
                QMessageBox.warning(self, 'Vitalux', tr('Ungültiges Tastenkürzel. Beispiel: Shift_R+F12'))
                return False
        try:
            game_profiles.save(self.game['id'], profile)
        except OSError as error:
            QMessageBox.warning(self, 'Vitalux', str(error))
            return False
        self.page.service.submit('profile', self.game)
        return True

    def _save_close(self):
        if self._save():
            self.accept()

    def _connection(self):
        if self._save():
            self.page.service.submit('disconnect' if self.game.get('connected') else 'connect', self.game)


class GamesPage(Page):
    def __init__(self, startup_games=None):
        super().__init__('Spiele')
        self.setProperty('uses_session_timeline', True)
        self.games, self.summaries = [], []
        self.selected_id = ''
        self.selected_report = ''
        self.current_report = None
        self.offset = 0
        self._tile_columns = 3
        self._dialog = None
        self._closing = False
        self.service = GameService(self, initial_games=startup_games)
        self.service.catalog_ready.connect(self._catalog)
        self.service.report_ready.connect(self._report)
        self.service.session_finished.connect(self._finished)
        self.service.activity.connect(self._activity)
        self.service.failed.connect(self._error)
        self.service.busy.connect(self._busy)
        heading = Card()
        title_row = QHBoxLayout()
        texts = QVBoxLayout()
        texts.addWidget(label('Spiele', 'pageTitle'))
        texts.addWidget(label('Overlay und Spielauswertungen', 'muted'))
        title_row.addLayout(texts, 1)
        self.status = label('Spiele werden eingelesen …', 'strong')
        self.status.setWordWrap(True)
        title_row.addWidget(self.status)
        heading.body.addLayout(title_row)
        tools = QHBoxLayout()
        self.search = QLineEdit();self.search.setPlaceholderText(tr('Spiel suchen …'))
        self.search.textChanged.connect(self._filter)
        tools.addWidget(self.search, 1)
        self.rescan = QPushButton('Neu erkennen');self.rescan.setObjectName('ghostBtn')
        self.rescan.clicked.connect(self.service.scan);tools.addWidget(self.rescan)
        heading.body.addLayout(tools)
        self.tile_host = QWidget()
        self.tile_row = QHBoxLayout(self.tile_host);self.tile_row.setContentsMargins(0, 0, 0, 0)
        self.tile_row.setSpacing(12)
        self.tiles = [GameTile() for _ in range(3)]
        for tile in self.tiles:
            tile.selected.connect(self.select_game)
            self.tile_row.addWidget(tile, 1)
        heading.body.addWidget(self.tile_host)
        pager = QHBoxLayout()
        self.previous = QPushButton('‹');self.next = QPushButton('›')
        for button in (self.previous, self.next):
            button.setObjectName('ghostBtn');button.setFixedWidth(34)
        self.previous.setAccessibleName(tr('Vorherige Spiele'))
        self.next.setAccessibleName(tr('Nächste Spiele'))
        self.previous.clicked.connect(lambda:self._move(-1));self.next.clicked.connect(lambda:self._move(1))
        self.counter = label('', 'muted')
        pager.addWidget(self.counter, 1);pager.addWidget(self.previous);pager.addWidget(self.next)
        heading.body.addLayout(pager)
        self.empty = label('Keine installierten Spiele gefunden. Steam, Heroic und Lutris werden lokal geprüft. '
                           'Nach einer Installation kannst du die Erkennung erneut starten.', 'muted', wrap=True)
        heading.body.addWidget(self.empty)
        self.content.addWidget(heading)
        self.notice = label('', 'muted', wrap=True);self.notice.hide();self.content.addWidget(self.notice)
        self.details = Card()
        selected = QHBoxLayout()
        names = QVBoxLayout()
        self.game_name = label('', 'bigName', wrap=True);self.game_name.setTextFormat(Qt.PlainText)
        self.session_name = label('', 'muted', wrap=True)
        names.addWidget(self.game_name);names.addWidget(self.session_name);selected.addLayout(names, 1)
        buttons = QVBoxLayout()
        self.profile_button = QPushButton('Overlay-Profil');self.profile_button.setObjectName('ghostBtn')
        self.profile_button.clicked.connect(self.open_profile)
        self.start_button = QPushButton('Spiel starten');self.start_button.setObjectName('primaryBtn')
        self.start_button.clicked.connect(self.start_game)
        buttons.addWidget(self.profile_button);buttons.addWidget(self.start_button);selected.addLayout(buttons)
        self.details.body.addLayout(selected)
        self.metrics_host = QWidget();self.metrics_grid = QGridLayout(self.metrics_host)
        self.metrics_grid.setContentsMargins(0, 0, 0, 0);self.metrics_grid.setSpacing(12)
        self.metric_cards, self.values = [], []
        for index, name in enumerate(('Ø FPS', '1% Low', '0,1% Low', 'Bewertung')):
            card = Card()
            card.body.addWidget(label(name, 'muted', Qt.AlignCenter))
            value = label('–', 'heroTitle', Qt.AlignCenter, wrap=True)
            card.body.addWidget(value)
            self.metric_cards.append(card);self.values.append(value)
            self.metrics_grid.addWidget(card, 0, index)
        self.details.body.addWidget(self.metrics_host)
        self.reason = label('', 'strong', wrap=True);self.details.body.addWidget(self.reason)
        self.criteria = QPushButton('Bewertung erklären');self.criteria.setObjectName('ghostBtn')
        self.criteria.clicked.connect(self._explain);self.details.body.addWidget(self.criteria, 0, Qt.AlignLeft)
        plot = Card('Spielverlauf')
        self.plot_card = plot
        self.chart = ChartPanel(['FPS', 'Frametime'], [theme.accent(), theme.secondary_accent()],
                                mode='mixed', series_modes=['fps', 'frametime'])
        self.chart.set_scope('games')
        self.chart.setProperty('defaultHorizon', -1)
        self.chart.graph.setProperty('fullSessionPoints', True)
        self.chart.time_range.insertItem(0, tr('Gesamte Sitzung'), -1)
        self.chart.time_range.setCurrentIndex(0)
        plot.body.addWidget(self.chart)
        self.details.body.addWidget(plot)
        self.hardware = label('', 'muted', Qt.AlignCenter, wrap=True)
        self.details.body.addWidget(self.hardware)
        history = Card('Frühere Sitzungen')
        self.history_card = history
        self.history = QTableWidget(0, 5)
        self.history.setSelectionBehavior(QTableWidget.SelectRows)
        self.history.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history.verticalHeader().hide()
        self.history.horizontalHeader().setStretchLastSection(True)
        self.history.setMinimumHeight(110);self.history.setMaximumHeight(230)
        self.history.cellClicked.connect(self._history_selected)
        history.body.addWidget(self.history)
        self.details.body.addWidget(history)
        self.content.addWidget(self.details)
        self.details.hide()
        self._report_visible(False)
        self._arrange()
        self.service.start()

    def _catalog(self, data):
        if self._closing:return
        self.games, self.summaries = data['games'], data['sessions']
        self.status.setText(tr('MangoHud · Bereit') if any(g.get('mangohud_available') for g in self.games)
                            else tr('MangoHud · Nicht eingerichtet'))
        self.empty.setVisible(not self.games)
        if not self.selected_id or not any(g['id']==self.selected_id for g in self.games):
            self.selected_id = self.games[0]['id'] if self.games else ''
        self._tiles()
        if self.selected_id:
            self._show_game()
        if self._dialog is not None:
            import shiboken6
            if shiboken6.isValid(self._dialog):
                game = next((g for g in self.games if g['id']==self._dialog.game['id']), None)
                if game:self._dialog.update_game(game)

    def _filtered(self):
        needle = self.search.text().casefold().strip()
        return [game for game in self.games if not needle or needle in game['name'].casefold()]

    def _filter(self):
        self.offset = 0
        self._tiles()

    def _move(self, direction):
        count = len(self._filtered())
        self.offset = max(0, min(max(0, count-self._tile_columns), self.offset+direction*self._tile_columns))
        self._tiles()

    def _tiles(self):
        games = self._filtered()
        self.offset = min(self.offset, max(0, len(games)-self._tile_columns))
        for index, tile in enumerate(self.tiles):
            position = self.offset+index
            visible = index < self._tile_columns and position < len(games)
            tile.setVisible(visible)
            if visible:tile.set_game(games[position], games[position]['id']==self.selected_id)
        self.tile_host.setVisible(bool(games))
        self.previous.setEnabled(self.offset > 0)
        self.next.setEnabled(self.offset+self._tile_columns < len(games))
        self.counter.setText(tr('{start}–{end} von {count} Spielen').format(
            start=self.offset+1 if games else 0, end=min(len(games), self.offset+self._tile_columns), count=len(games)))

    def select_game(self, game_id):
        if game_id != self.selected_id:
            self.selected_id, self.selected_report, self.current_report = game_id, '', None
            self._report_visible(False)
        self._tiles()
        self._show_game()

    def _show_game(self):
        game = next((game for game in self.games if game['id']==self.selected_id), None)
        self.details.setVisible(game is not None)
        if not game:return
        self.game_name.setText(game['name'])
        self.start_button.setEnabled(bool(game.get('installed')))
        history = [row for row in self.summaries if row['game_id']==self.selected_id]
        self._history_table(history)
        if history and not self.selected_report:
            self.selected_report = history[0]['id']
            self.session_name.setText(tr('Auswertung wird geladen …'))
            self.service.submit('report', self.selected_report)
        elif not history:
            self.current_report = None
            self._report_visible(False)
            self.session_name.setText(tr('Noch keine Sitzung. MangoHud verbinden und das Spiel über seinen Launcher starten.'))

    def _report_visible(self, visible):
        for widget in (self.metrics_host, self.reason, self.criteria, self.plot_card, self.hardware):
            widget.setVisible(visible)
        self.history_card.setVisible(bool(self.history.rowCount()))

    def _report(self, report):
        if report.get('game_id') != self.selected_id or report.get('id') != self.selected_report:
            return
        self.current_report = report
        self.session_name.setText(tr('{date} · {duration} · Ziel: {target} FPS').format(
            date=date_text(report['started']), duration=duration(report['duration']), target=shown(report['target_fps'])))
        for widget, key in zip(self.values[:3], ('average_fps', 'low_1', 'low_01')):
            widget.setText(shown(report.get(key)))
        self.values[3].setText(tr(GRADES.get(report['grade'], 'Zu wenige Messdaten')))
        reasons = dict(excellent='FPS-Ziel erreicht · sehr gleichmäßige Bildausgabe',
                       good='Überwiegend gleichmäßige Bildausgabe im Verhältnis zum FPS-Ziel',
                       adequate='Spielbar, mit deutlichen Einbrüchen gegenüber dem FPS-Ziel',
                       improve='Häufige Einbrüche oder deutlich unter dem gewählten FPS-Ziel',
                       incomplete='Aufzeichnung unvollständig · keine Gesamtnote',
                       insufficient='Zu wenige Einzelbilddaten für eine verlässliche Bewertung')
        explanation=tr(reasons[report['grade']])
        if 'multiple_graphics_processes' in report.get('warnings',[]):
            explanation+='\n'+tr('Mehrere Grafikprogramme aufgezeichnet. Ausgewertet wird die längste Aufzeichnung: {process}.').format(process=report.get('source_process','–'))
        self.reason.setTextFormat(Qt.PlainText)
        self.reason.setText(explanation)
        points = report.get('plot', [])
        self.chart.set_timeline([report['started']+point[0] for point in points])
        self.chart.set_series([([point[1] for point in points], theme.accent()),
                               ([point[2] for point in points], theme.secondary_accent())])
        maxima = report.get('maxima', {})
        parts = []
        for key, name, unit, digits in (('cpu_temp','CPU max.',' °C',0), ('gpu_temp','GPU max.',' °C',0),
                                       ('gpu_vram_used','VRAM max.',' GB',1), ('gpu_power','GPU max.',' W',1)):
            if maxima.get(key, 0) > 0:
                parts.append(tr(name)+' '+shown(maxima[key], unit, digits))
        self.hardware.setText('   ·   '.join(parts))
        self._report_visible(True)
        self.hardware.setVisible(bool(parts))
        self.plot_card.setVisible(bool(points))

    def _history_table(self, rows):
        self.history.blockSignals(True)
        self.history.setHorizontalHeaderLabels([tr(text) for text in ('Sitzung','Dauer','Ø FPS','1% Low','Bewertung')])
        self.history.setRowCount(len(rows))
        for index, row in enumerate(rows):
            values = (date_text(row['started']), duration(row['duration']), shown(row.get('average_fps')),
                      shown(row.get('low_1')), tr(GRADES.get(row['grade'], 'Zu wenige Messdaten')))
            for column, text in enumerate(values):
                item = self.history.item(index, column)
                if item is None:item = QTableWidgetItem();self.history.setItem(index, column, item)
                item.setText(text)
                item.setData(Qt.UserRole, row['id'])
        self.history.resizeColumnsToContents()
        self.history.blockSignals(False)
        self.history_card.setVisible(bool(rows))

    def _history_selected(self, row, _column):
        item = self.history.item(row, 0)
        if item:
            self.selected_report = item.data(Qt.UserRole)
            self.service.submit('report', self.selected_report)

    def open_profile(self):
        game = next((g for g in self.games if g['id']==self.selected_id), None)
        if game:
            self._dialog = OverlayProfile(self, game)
            self._dialog.open()

    def start_game(self):
        game = next((g for g in self.games if g['id']==self.selected_id), None)
        if game and game.get('installed'):
            if not QDesktopServices.openUrl(QUrl(game['launcher_uri'])):
                self._error(tr('Der Spiele-Launcher konnte nicht geöffnet werden.'))

    def _explain(self):
        from .detail_dialog import show_details
        text = tr('Die Bewertung vergleicht FPS-Ziel, Durchschnitt, 1%-Low und lange Frames. '
                  'Sehr gut: mindestens 99 % des FPS-Ziels, 1%-Low mindestens 95 %, höchstens 1 % lange Frames. '
                  'Gut: 90 %, 70 %, höchstens 3 %. Ausreichend: 70 %, 45 %, höchstens 8 %. '
                  'Darunter besteht Verbesserungsbedarf. Lange Frames überschreiten sowohl 50 ms als auch das doppelte Ziel-Framebudget. '
                  'Unter 30 Sekunden oder bei unvollständigen Daten gibt es keine Gesamtnote. '
                  '1%-Lows werden aus den durchschnittlichen langsamsten 1 % der Framezeiten berechnet. '
                  '0,1%-Lows benötigen mindestens 10.000 Frames. Die Kurve wird für die Anzeige verdichtet; '
                  'die Statistik verwendet sämtliche gültigen Frames. Menüs und Ladebildschirme werden mitgemessen. '
                  'Dies bewertet die Spielsitzung, nicht die Gesundheit der Hardware.')
        self._explanation = show_details(self, 'Bewertung erklären', text)

    def _activity(self, active):
        if active:
            self.status.setText(tr('MangoHud · Spielsitzung aktiv'))
        else:
            self.status.setText(tr('MangoHud · Bereit') if any(g.get('mangohud_available') for g in self.games)
                                else tr('MangoHud · Nicht eingerichtet'))

    def _finished(self, report):
        if self._closing:return
        self.select_game(report['game_id'])
        self.selected_report = report['id']
        self._report(report)
        window = self.window()
        index = next((i for i, (_name, page) in enumerate(getattr(window, 'pages', [])) if page is self), None)
        if index is not None:
            window.nav_buttons[index].setChecked(True)
            window._switch_page(index)
            window.show_from_tray()

    def _error(self, message):
        if self._closing:return
        self.notice.setText(tr(message))
        self.notice.show()
        self.notice.setTextFormat(Qt.PlainText)

    def _busy(self, busy):
        self.profile_button.setEnabled(not busy)
        if self._dialog is not None:
            import shiboken6
            if shiboken6.isValid(self._dialog):
                self._dialog.save_button.setEnabled(not busy)
                self._dialog.connection.setEnabled(not busy and
                    (self._dialog.game.get('connected') or self._dialog.game.get('mangohud_available')))

    def _arrange(self):
        width = self.width()
        self._tile_columns = 3 if width >= 1000 else 2 if width >= 680 else 1
        for index, card in enumerate(self.metric_cards):
            columns = 4 if width >= 760 else 2
            self.metrics_grid.addWidget(card, index//columns, index % columns)
        if hasattr(self, 'search'):self._tiles()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'metric_cards'):self._arrange()

    def retranslate(self):
        self.search.setPlaceholderText(tr('Spiel suchen …'))
        self._tiles()
        if self.current_report:self._report(self.current_report)
        self._history_table([row for row in self.summaries if row['game_id']==self.selected_id])

    def shutdown(self):
        self._closing = True
        return self.service.shutdown()

    def resume_after_shutdown(self):
        if not self.service.isRunning():
            from threading import Event
            from queue import Queue
            self.service.cancelled = Event()
            self.service.commands = Queue()
            self._closing = False
            self.service.start()
