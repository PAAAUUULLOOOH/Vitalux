"""Hardware-sensor page, appearance settings and customizable dashboard controls."""
from . import DEFAULT_THEME
import json
from functools import lru_cache
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QColor, QIntValidator
from PySide6.QtWidgets import (QColorDialog, QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QSizePolicy, QSlider, QVBoxLayout, QWidget)
from .ui_locale import QCheckBox, QComboBox, QDialog, QFileDialog, QListWidgetItem, QMessageBox, QPushButton

from . import __version__, settings, theme, motion, backdrops, user_background, wallpaper_accents, renderer, eco, i18n, premium
from .pages import Page
from .sensors import fmt_bytes, fmt_rate, system_static
from .widgets import Card, KeyValue, Meter, label
from .i18n import tr
from .mini_hud import DEFAULT_KEYS
from .settings_search import FloatingSettingsSearch, _SearchIcon
from .choice_combo import ChoiceComboBox
from .expandable import ExpandableCard
from .settings_navigation import SettingsNavigator, ExpansionFollower
from .soft_controls import AccentSwatch, ResponsiveActions, SoftReveal


class SensorsPage(Page):
    def __init__(self):
        super().__init__('Sensoren', 'Temperaturen, Lüfter und Spannungen · direkt aus Linux hwmon')
        self.cards = {}
        self.rows = {}
        for ident, title in [('temps', 'Temperaturen'), ('fans', 'Lüfter'), ('frequencies', 'Frequenzen'), ('powers', 'Leistungsaufnahme'), ('voltages', 'Spannungen')]:
            card = Card(title)
            self.cards[ident] = card
            self.rows[ident] = {}
            self.content.addWidget(card)
        self.message = label('', 'muted', wrap=True)
        self.content.addWidget(self.message)

    def refresh(self, d, h):
        sensors = d.get('sensors', {})
        count = 0
        for ident in ('temps', 'fans', 'voltages', 'powers', 'frequencies'):
            seen = set()
            entries = sensors.get(ident, [])
            for sensor in entries[:80]:
                key = sensor['name']
                seen.add(key)
                row = self.rows[ident].get(key)
                if row is None:
                    row = self.rows[ident][key] = KeyValue(key)
                    self.cards[ident].body.addWidget(row)
                val = sensor['value']
                unit = {'temps': '°C', 'fans': tr('U/min'), 'voltages': 'V', 'powers': 'W', 'frequencies': 'MHz'}[ident]
                if val is None:
                    row.set('–')
                else:
                    row.set(f'{val:.1f} {unit}' if ident != 'fans' else f'{val:.0f} {unit}')
                count += 1
            for key, widget in self.rows[ident].items():
                widget.setVisible(key in seen)
            self.cards[ident].setVisible(bool(entries))
        self.message.setText(tr('Keine zusätzlichen Sensoren verfügbar.') if not count else
            tr('Nicht jeder Sensor ist von jedem Mainboard/Grafiktreiber verfügbar; fehlende Werte werden nicht erfunden.'))



class _ThresholdNumberEdit(QLineEdit):
    """A normal Qt text editor, without QSpinBox's clipped internal layout."""

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            self.parentWidget().stepBy(1 if event.key() == Qt.Key_Up else -1)
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        steps = int(event.angleDelta().y() / 120)
        if steps and self.hasFocus():
            self.parentWidget().stepBy(steps)
            event.accept()
        else:
            event.ignore()

    def focusOutEvent(self, event):
        self.parentWidget().commit()
        super().focusOutEvent(event)


class AlertThresholdField(QFrame):
    """Warning threshold: readable value and unit in a compact themed control.

    In Qt/KDE stylesheet combinations the embedded QSpinBox line editor can
    end up nearly zero pixels wide when spin buttons are hidden. Keep the
    numeric QLineEdit and its unit independently laid out instead.
    """
    valueChanged = Signal(int)

    def __init__(self, minimum, maximum, unit, value, parent=None):
        super().__init__(parent)
        self._minimum, self._maximum = int(minimum), int(maximum)
        self._value = min(self._maximum, max(self._minimum, int(value)))
        self.setObjectName("alertThresholdField")
        self.setFixedSize(84, 34)

        self.number = _ThresholdNumberEdit(str(self._value), self)
        self.number.setObjectName("alertThresholdNumber")
        self.number.setValidator(QIntValidator(self._minimum, self._maximum, self.number))
        self.number.setMaxLength(3)
        self.number.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.number.setMinimumWidth(26)
        self.number.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.unit_label = QLabel(unit, self)
        self.unit_label.setObjectName("alertThresholdUnit")
        self.unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.unit_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        row = QHBoxLayout(self)
        row.setContentsMargins(7, 2, 7, 2)
        row.setSpacing(3)
        row.addWidget(self.number, 1)
        row.addWidget(self.unit_label, 0)
        self.number.textChanged.connect(self._on_text_changed)
        self.number.editingFinished.connect(self.commit)

    def _on_text_changed(self, text):
        if text.isdecimal() and self._minimum <= int(text) <= self._maximum:
            self.setValue(int(text), update_editor=False)

    def setValue(self, value, update_editor=True):
        bounded = min(self._maximum, max(self._minimum, int(value)))
        changed = bounded != self._value
        self._value = bounded
        if update_editor and self.number.text() != str(bounded):
            was_blocked = self.number.blockSignals(True)
            self.number.setText(str(bounded))
            self.number.blockSignals(was_blocked)
        if changed:
            self.valueChanged.emit(bounded)

    def value(self):
        return self._value

    def stepBy(self, steps):
        self.setValue(self._value + int(steps))

    def commit(self):
        text = self.number.text().strip()
        if text.isdecimal() and self._minimum <= int(text) <= self._maximum:
            self.setValue(int(text))
        else:
            self.setValue(self._value)


class PreferencesPage(Page):
    # Built-in colors are never editable or removable, even when older saved
    # settings incorrectly contain an entry with the same hex color.
    PRESET_ACCENTS = (
        ('Distribution', 'auto'),
        ('Vitalux Blau', '#4f8cff'),
        ('Cyan', '#52d3ff'),
        ('Violett', '#a78bfa'),
        ('Grün', '#73ba25'),
        ('Orange', '#f59e0b'),
        ('Gelb', '#facc15'),
        ('Rot', '#ef4444'),
        ('Rosa', '#f472b6'),
    )
    PRESET_COLORS = frozenset(value for _, value in PRESET_ACCENTS)

    DEFAULTS = {
        'theme': DEFAULT_THEME, 'accent': '#4f8cff', 'ui_sounds': True, 'ui_sound_volume': 70, 'motion': 'smooth',
        'background_style': 'theme_default', 'custom_background_fit': 'cover',
        'render_backend': renderer.SOFTWARE, 'ultra_eco': False,
        'interval': 1, 'close_to_tray': True, 'alerts_enabled': False,
        'cpu_temp': 90, 'gpu_temp': 90, 'ram_usage': 90, 'disk_usage': 95,
        'mini_hud_enabled': False, 'mini_hud_layout': 'compact',
        'mini_hud_opacity': 90,
        'mini_hud_metrics': list(DEFAULT_KEYS),
    }
    SECTION_DEFAULTS = {
        'appearance': ('theme', 'accent', 'ui_sounds', 'ui_sound_volume', 'motion', 'background_style', 'custom_background_fit'),
        'hud': ('mini_hud_enabled', 'mini_hud_layout', 'mini_hud_opacity',
                'mini_hud_metrics'),
        'alerts': ('alerts_enabled', 'cpu_temp', 'gpu_temp', 'ram_usage', 'disk_usage'),
    }

    def __init__(self, window):
        super().__init__('Einstellungen', 'Design, Messintervall, Dashboard und Datenexport')
        self.window = window
        # One continuous settings page; no extra section navigation.
        self._settings_cards = {key: [] for key in ('appearance', 'general', 'hud', 'monitoring', 'energy', 'render')}
        self._reset_buttons = {}
        self._reset_reveals = {}
        self.search = QLineEdit()
        self.search.setObjectName('settingsSearch')
        self.search.setPlaceholderText(tr('Einstellungen durchsuchen …'))
        self.search.textChanged.connect(self.search_settings)
        self.search_results = QListWidget()
        self.search_results.setObjectName('settingsSearchResults')
        self.search_results.setMaximumHeight(156)
        self.search_results.setVisible(False)
        self.search_results.itemActivated.connect(self.choose_search_result)
        self.search_results.itemClicked.connect(self.choose_search_result)
        # The overlay is parented to the scroll viewport when the page is embedded.
        # A reserved top margin ensures the pinned control never covers a settings card.
        self.search_overlay = FloatingSettingsSearch(self.search, self.search_results, self)
        self.search_navigation = SettingsNavigator(self)
        self._search_words = None
        # Resting magnifier is a normal page element. Only the opened search
        # floats above the viewport; after closing, scroll can carry it away.
        self.search_home = _SearchIcon(self)
        self.search_home.clicked.connect(self.search_overlay.open_search)
        self.search_overlay.home_icon = self.search_home
        # Keep 32px of vertical space even while the anchored icon is hidden.
        # Expanding search must not jump the underlying settings layout.
        search_home_host = QWidget(self)
        search_home_host.setFixedHeight(32)
        search_home_row = QHBoxLayout(search_home_host)
        search_home_row.setContentsMargins(0, 0, 0, 0)
        search_home_row.addStretch(1)
        search_home_row.addWidget(self.search_home)
        search_home_row.addStretch(1)
        self.content.addWidget(search_home_host)

        self._search_targets = []
        look = Card('Erscheinungsbild')
        look.body.addWidget(label('Farbschema', 'strong'))
        self.design_gallery = QWidget()
        self.design_gallery.setObjectName('designGallery')
        gallery = QGridLayout(self.design_gallery)
        gallery.setContentsMargins(0, 0, 0, 0)
        gallery.setSpacing(10)
        self.design_tiles = []
        for index, (key, title) in enumerate(theme.CHOICES):
            tile = premium.DesignTile(key)
            tile.setChecked(settings.get('theme', DEFAULT_THEME) == key)
            tile.clicked.connect(lambda _checked=False, key=key: self.select_design(key))
            self.design_tiles.append(tile)
            gallery.addWidget(tile, index // 3, index % 3)
        look.body.addWidget(self.design_gallery)
        self.theme_note = label('', 'muted', wrap=True)
        self.theme_note.setObjectName('themeDescription')
        look.body.addWidget(self.theme_note)
        self.mode_notes = {
            'dark': 'Dark · Kontrastreiche, ruhige Flächen ohne Glasunschärfe.',
            'light': 'Light · Helle, gut lesbare Karten ohne Glaseffekt.',
            'glass': 'Glass · Halbtransparente Panels mit Lichtreflexen und weichgezeichnetem Hintergrund.',
            'black_glass': 'Black Glass · Tiefschwarze Glasflächen mit dezenten Reflexionen und silbernen Kanten. Eigene Akzentfarben sind hier gesperrt.',
            'black_glass_gold': 'Black Glass Gold · Tiefschwarze Glasflächen, helles Gold für Logo, Diagramme, Anzeigen, Icons und Rahmen. Akzentfarbe und Hintergrund sind fest aufeinander abgestimmt.',
            'holographic': 'Holographic · Eigenständige, undurchsichtige Sci-Fi-HUD-Oberfläche mit leuchtenden Konturen, technischen Kacheln und Diagrammen – ohne Glas.',
            'minimal': 'Minimalistisch · Einfache Flächen ohne Glas, Schatten und dekorative Animationen. Spart Zeichenaufwand.',
            'obsidian_gold': 'Obsidian Gold · Rauchglas, gebürstetes Gold und präzise Instrumentringe. Die äußeren Logo-Streifen drehen sich langsam.',
            'champagne_glass': 'Champagne Glass · Kristallglas, warme Champagnertöne und seidenweiche Reflexionen mit goldenen Instrumenten.',
            'aurora_gold': 'Aurora Gold · Irisierendes Glas mit Petrol- und Violettlicht, flüssigen Goldkanten und leuchtenden Instrumenten.',
        }
        self.theme_note.setText(tr(self.mode_notes.get(theme.mode(), self.mode_notes['dark'])))
        accent_row = QVBoxLayout()
        accent_selector = QHBoxLayout()
        accent_selector.addWidget(label('Akzentfarbe', 'strong'))
        accent = ChoiceComboBox()
        self.accent_combo = accent
        for title, value in self.PRESET_ACCENTS:
            accent.addItem(title, value)
        self.custom_accents = self._read_custom_accents()
        stored = settings.get('accent', '#4f8cff')
        if wallpaper_accents.is_legacy_accent(stored):
            stored = wallpaper_accents.AUTO
        stored = wallpaper_accents.effective_selection(stored)
        if stored != settings.get('accent', '#4f8cff'):
            settings.set('accent', stored)
        if accent.findData(stored) < 0 and QColor(str(stored)).isValid():
            # Migrate the unnamed color from earlier Vitalux installations.
            if not any(item['color'] == QColor(stored).name() for item in self.custom_accents):
                self.custom_accents.append({'name': 'Eigene Farbe', 'color': QColor(stored).name()})
                settings.set('custom_accents', self.custom_accents)
        accent.addItem('Hintergrundfarbe automatisch', wallpaper_accents.AUTO)
        for item in self.custom_accents:
            if accent.findData(item['color']) < 0:
                accent.addItem(item['name'], item['color'])
        accent.setCurrentIndex(max(0, accent.findData(stored)))
        accent.currentIndexChanged.connect(lambda _: self.change_accent(accent.currentData()))
        # Keep custom names compact; their complete text remains in the tooltip.
        accent.setFixedWidth(210)
        accent.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        accent_selector.addWidget(accent)
        self.accent_preview = AccentSwatch(self)
        accent_selector.addWidget(self.accent_preview)
        accent_selector.addStretch(1)
        accent_row.addLayout(accent_selector)
        accent_actions = QHBoxLayout()
        # Both actions appear only when a saved custom accent is selected.
        self.edit_custom_accent_button = QPushButton('Bearbeiten')
        self.edit_custom_accent_button.setObjectName('ghostBtn')
        self.edit_custom_accent_button.setCursor(Qt.PointingHandCursor)
        self.edit_custom_accent_button.setToolTip(tr('Ausgewählte eigene Farbe bearbeiten'))
        self.edit_custom_accent_button.clicked.connect(self.edit_custom_accent)
        accent_actions.addWidget(self.edit_custom_accent_button)
        self.remove_custom_accent_button = QPushButton('Löschen')
        self.remove_custom_accent_button.setObjectName('ghostBtn')
        self.remove_custom_accent_button.setCursor(Qt.PointingHandCursor)
        self.remove_custom_accent_button.setToolTip(tr('Ausgewählte eigene Farbe löschen'))
        self.remove_custom_accent_button.clicked.connect(self.remove_custom_accent)
        accent_actions.addWidget(self.remove_custom_accent_button)
        custom = QPushButton('Eigene Farbe …')
        self.custom_accent_button = custom
        custom.setObjectName('ghostBtn')
        custom.clicked.connect(lambda: self.custom_accent(accent))
        accent_actions.addWidget(custom)
        accent_actions.addStretch(1)
        accent_row.addLayout(accent_actions)
        look.body.addLayout(accent_row)
        self._sync_custom_accent_actions()
        look.body.addWidget(label('Akzentfarben gelten für Reiter, Kartenkanten, Kurven und Bedienelemente.', 'muted', wrap=True))
        # Native gradients are independent of the selected visual theme.
        bg_row = QHBoxLayout()
        bg_row.addWidget(label('Hintergrund', 'strong'))
        self.background_combo = ChoiceComboBox()
        for key, title in backdrops.PRESETS:
            self.background_combo.addItem(title, key)
        self.background_combo.addItem('Eigenes Bild', 'custom_image')
        saved_bg = settings.get('background_style', 'theme_default')
        if saved_bg == 'legacy':
            saved_bg = 'theme_default'
        self.background_combo.setCurrentIndex(max(0, self.background_combo.findData(saved_bg)))
        self.background_combo.currentIndexChanged.connect(self.change_background)
        bg_row.addWidget(self.background_combo)
        bg_row.addStretch(1)
        look.body.addLayout(bg_row)
        custom_area = QWidget()
        self.custom_background_area = custom_area
        picture_layout = QVBoxLayout(custom_area)
        picture_layout.setContentsMargins(0, 0, 0, 0)
        pictures = QHBoxLayout()
        pictures.addWidget(label('Hintergrundbild', 'strong'))
        self.background_image_combo = QComboBox()
        self.background_image_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.background_image_combo.currentIndexChanged.connect(self.select_background_image)
        pictures.addWidget(self.background_image_combo, 1)
        add_picture = QPushButton('Bild hinzufügen …')
        add_picture.setObjectName('ghostBtn')
        add_picture.clicked.connect(self.add_background_image)
        image_actions = QHBoxLayout()
        image_actions.addWidget(add_picture)
        remove_picture = QPushButton('Löschen')
        remove_picture.setObjectName('ghostBtn')
        remove_picture.clicked.connect(self.remove_background_image)
        self.remove_background_button = remove_picture
        image_actions.addWidget(remove_picture)
        image_actions.addStretch(1)
        picture_layout.addLayout(pictures)
        picture_layout.addLayout(image_actions)
        fit_row = QHBoxLayout()
        fit_row.addWidget(label('Bildausrichtung', 'strong'))
        self.background_fit_combo = QComboBox()
        for caption, fit in user_background.FITS:
            self.background_fit_combo.addItem(caption, fit)
        self.background_fit_combo.setCurrentIndex(max(0, self.background_fit_combo.findData(settings.get('custom_background_fit', 'cover'))))
        self.background_fit_combo.currentIndexChanged.connect(self.change_background_fit)
        fit_row.addWidget(self.background_fit_combo)
        fit_row.addStretch(1)
        picture_layout.addLayout(fit_row)
        self.background_preview = QLabel()
        self.background_preview.setMinimumSize(0, 0)
        self.background_preview.setMaximumSize(320, 120)
        self.background_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.background_preview.setFixedHeight(120)
        picture_layout.addWidget(self.background_preview)
        self.background_performance_note = label(
            'Leistungshinweis: Eigene Hintergrundbilder können besonders bei hoher Auflösung '
            'und aktivierten Glaseffekten zusätzliche Systemressourcen beanspruchen. '
            'Dadurch sind Ruckler oder eine verzögerte Darstellung möglich. '
            'Für eine optimale Leistung empfehlen wir die integrierten Vitalux-Hintergründe.',
            'muted', wrap=True)
        self.background_performance_note.setObjectName('backgroundPerformanceNote')
        picture_layout.addWidget(self.background_performance_note)
        look.body.addWidget(custom_area)
        self.refresh_background_images()
        look.body.addWidget(label(
            'Nur Funkeln ist animiert. Die anderen Hintergründe sind statisch; '
            'Adaptiv folgt der ausgewählten Akzentfarbe.',
            'muted', wrap=True))
        # A presentation preference, not a global reduction of monitoring speed.
        # Runtime widgets read the profile on their next interaction.
        r_motion = QHBoxLayout()
        r_motion.addWidget(label('Animationen', 'strong'))
        self.motion_combo = QComboBox()
        for name, value in [('Flüssig', 'smooth'), ('Reduziert', 'reduced'), ('Aus', 'off')]:
            self.motion_combo.addItem(name, value)
        self.motion_combo.setCurrentIndex(max(0, self.motion_combo.findData(settings.get('motion', 'smooth'))))
        self.motion_combo.currentIndexChanged.connect(self.change_motion)
        r_motion.addWidget(self.motion_combo)
        r_motion.addStretch(1)
        look.body.addLayout(r_motion)
        look.body.addWidget(label('Übergänge anpassen: weich, verkürzt oder ohne Animation.', 'muted', wrap=True))
        self.sound_toggle = QCheckBox('Glas-Klang bei Klicks')
        self.sound_toggle.setChecked(settings.get('ui_sounds', True))
        self.sound_toggle.toggled.connect(lambda enabled: self._set_preference('ui_sounds', enabled))
        look.body.addWidget(self.sound_toggle)
        volume_row = QHBoxLayout()
        volume_row.addWidget(label('Lautstärke', 'strong'))
        self.sound_volume = QSlider(Qt.Horizontal)
        self.sound_volume.setRange(0, 100)
        self.sound_volume.setValue(settings.get('ui_sound_volume', 70))
        self.sound_volume.setMaximumWidth(210)
        self.sound_volume.setAccessibleName(tr('Klanglautstärke'))
        self.sound_volume_value = label(str(self.sound_volume.value())+' %', 'muted')
        self._volume_save = QTimer(self)
        self._volume_save.setSingleShot(True)
        self._volume_save.setInterval(160)
        self._volume_save.timeout.connect(lambda: self._set_preference('ui_sound_volume', self.sound_volume.value()))
        self.sound_volume.valueChanged.connect(lambda value: self.sound_volume_value.setText(str(value)+' %'))
        self.sound_volume.valueChanged.connect(lambda _value: self._volume_save.start())
        volume_row.addWidget(self.sound_volume)
        volume_row.addWidget(self.sound_volume_value)
        volume_row.addStretch(1)
        look.body.addLayout(volume_row)
        self._add_section_reset(look.body, 'appearance', 'Darstellung zurücksetzen')
        self._settings_cards['appearance'].append(look)

        # A genuine toggle, not another GPU backend or a destructive theme switch.
        # Original theme, wallpaper, accent, motion and render choice remain saved.
        eco_card = Card('Leistung & Energie')
        self.eco_toggle = QCheckBox('Ultra Eco – maximale Ressourcenschonung')
        self.eco_toggle.setChecked(eco.enabled())
        self.eco_toggle.toggled.connect(self.toggle_ultra_eco)
        eco_card.body.addWidget(self.eco_toggle)
        eco_card.body.addWidget(label(
            'Sehr einfache, flache Oberfläche ohne Glas, Schatten, Hintergrundbilder, '
            'Funkeln oder Übergangsanimationen. CPU-Rendering und 10 Sekunden '
            'Messintervall sparen Zeichen- und Abfragearbeit. Ausschalten stellt '
            'deine bisherigen Einstellungen wieder her.', 'muted', wrap=True))
        self.eco_status = label('', 'muted', wrap=True)
        eco_card.body.addWidget(self.eco_status)
        self.eco_restart_button = QPushButton('Jetzt neu starten')
        self.eco_restart_button.setObjectName('primaryBtn')
        self.eco_restart_button.clicked.connect(self.restart_for_eco)
        eco_card.body.addWidget(self.eco_restart_button, 0, Qt.AlignLeft)
        self._settings_cards['energy'].append(eco_card)

        render_card = Card('Grafik-Rendering')
        render_row = QHBoxLayout()
        render_row.addWidget(label('Render-Methode', 'strong'))
        self.render_combo = QComboBox()
        self.render_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.render_combo.setMinimumContentsLength(14)
        self.render_combo.setMaximumWidth(280)
        for backend in renderer.CHOICES:
            self.render_combo.addItem(tr(renderer.DESCRIPTIONS[backend]), backend)
        selected_renderer = settings.get('render_backend', renderer.SOFTWARE)
        if selected_renderer not in renderer.CHOICES:
            selected_renderer = renderer.SOFTWARE
        self.render_combo.setCurrentIndex(max(0, self.render_combo.findData(selected_renderer)))
        self.render_combo.currentIndexChanged.connect(self.change_renderer)
        render_row.addWidget(self.render_combo)
        render_row.addStretch(1)
        render_card.body.addLayout(render_row)
        render_card.body.addWidget(label(
            'Wayland und X11 bleiben experimentelle GPU-Modi; Diagramme und Qt-Widgets nutzen weiterhin die CPU.',
            'muted', wrap=True))
        render_card.body.addWidget(label(
            'Für den Wechsel Jetzt neu starten klicken. Wayland setzt eine Wayland-Sitzung, '
            'X11 einen X-Server voraus. Ein fehlgeschlagener GPU-Start wird auf CPU zurückgesetzt.',
            'muted', wrap=True))
        self.render_status = label('', 'muted', wrap=True)
        render_card.body.addWidget(self.render_status)
        self.render_restart_button = QPushButton('Jetzt neu starten')
        self.render_restart_button.setObjectName('primaryBtn')
        self.render_restart_button.clicked.connect(self.restart_for_renderer)
        render_card.body.addWidget(self.render_restart_button, 0, Qt.AlignLeft)
        self._refresh_renderer_status()
        self._settings_cards['render'].append(render_card)
        # These are explicitly different: clearing harmless in-memory previews
        # does not delete user preferences, wallpapers or the OS page cache.
        maintenance = Card('Wartung')
        maintenance.body.addWidget(label(
            'Nur Vitalux-eigene Daten verwalten. Kein Eingriff in Linux-Systemcaches.',
            'muted', wrap=True))
        self.clear_cache_btn = QPushButton('Vitalux-Cache leeren')
        self.clear_cache_btn.setObjectName('ghostBtn')
        self.clear_cache_btn.clicked.connect(self.clear_app_cache)
        self.clear_preferences_btn = QPushButton('Persönliche Einstellungen löschen …')
        self.clear_preferences_btn.setObjectName('ghostBtn')
        self.clear_preferences_btn.clicked.connect(self.delete_personal_preferences)
        maintenance.body.addWidget(ResponsiveActions([self.clear_cache_btn, self.clear_preferences_btn]))
        self._maintenance_card = maintenance

        monitor = Card('Live-Monitoring')
        row = QHBoxLayout()
        row.addWidget(label('Aktualisierungsintervall', 'strong'))
        self.interval = QComboBox()
        for val in (1, 2, 5):
            self.interval.addItem(f'{val} Sekunde' if val == 1 else f'{val} Sekunden', val)
        self.interval.setCurrentIndex(max(0, self.interval.findData(settings.get('interval', 1))))
        self.interval.currentIndexChanged.connect(self.change_interval)
        row.addWidget(self.interval)
        row.addStretch()
        monitor.body.addLayout(row)
        monitor.body.addWidget(label('Die Diagramme bieten 60 Sekunden, 5 Minuten und 15 Minuten Verlauf sowie einzeln schaltbare Datenreihen.', 'muted', wrap=True))
        self._settings_cards['monitoring'].append(monitor)
        tray = Card('Systemleiste')
        self.close_to_tray = QCheckBox('Fenster schließen → in Systemleiste weiterlaufen')
        self.close_to_tray.setChecked(bool(settings.get('close_to_tray', True)))
        self.close_to_tray.setEnabled(self.window._tray is not None)
        self.close_to_tray.toggled.connect(lambda enabled: self._set_preference('close_to_tray', enabled))
        tray.body.addWidget(self.close_to_tray)
        tray.body.addWidget(label('Tray-Hover zeigt CPU-, GPU- und RAM-Auslastung sowie Temperaturen. Das Kontextmenü bietet Fenster-, MiniHUD- und Beenden-Aktionen.', 'muted', wrap=True))
        self._settings_cards['hud'].append(tray)

        hud = Card('MiniHUD · kompakte Live-Anzeige')
        hud.body.addWidget(label('Separates Desktop-Fenster mit den vorhandenen Vitalux-Messwerten. '                                 'Auch bei verborgenem Hauptfenster nutzbar; keine zusätzliche Sensorabfrage.', 'muted', wrap=True))
        self.hud_on = QCheckBox('MiniHUD anzeigen')
        self.hud_on.setChecked(bool(settings.get('mini_hud_enabled', False)))
        self.hud_on.toggled.connect(self.set_hud_enabled)
        hud.body.addWidget(self.hud_on)
        size_row = QHBoxLayout()
        size_row.addWidget(label('Größe', 'strong'))
        self.hud_size = QComboBox()
        for title, value in (('Minimal', 'minimal'), ('Kompakt', 'compact'), ('Erweitert mit Balken', 'extended')):
            self.hud_size.addItem(title, value)
        self.hud_size.setCurrentIndex(max(0, self.hud_size.findData(settings.get('mini_hud_layout', 'compact'))))
        self.hud_size.currentIndexChanged.connect(self.change_hud_size)
        size_row.addWidget(self.hud_size)
        size_row.addStretch()
        hud.body.addLayout(size_row)
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(label('Deckkraft', 'strong'))
        self.hud_opacity = QComboBox()
        for level in (50, 60, 70, 80, 90, 100):
            self.hud_opacity.addItem(f'{level} %', level)
        self.hud_opacity.setCurrentIndex(max(0, self.hud_opacity.findData(settings.get('mini_hud_opacity', 90))))
        self.hud_opacity.currentIndexChanged.connect(lambda *_: self.change_hud_option('mini_hud_opacity', self.hud_opacity.currentData()))
        opacity_row.addWidget(self.hud_opacity)
        opacity_row.addStretch()
        hud.body.addLayout(opacity_row)
        hud.body.addWidget(label('Messwerte im MiniHUD', 'strong'))
        self.hud_metrics = {}
        metric_grid = QGridLayout()
        from .mini_hud import METRIC_OPTIONS, DEFAULT_KEYS
        selections = settings.get('mini_hud_metrics', DEFAULT_KEYS)
        for idx, (key, title, _unit) in enumerate(METRIC_OPTIONS):
            box = QCheckBox(title)
            box.setChecked(key in selections)
            box.toggled.connect(self.change_hud_metrics)
            metric_grid.addWidget(box, idx // 2, idx % 2)
            self.hud_metrics[key] = box
        hud.body.addLayout(metric_grid)
        hud.body.addWidget(label('Das MiniHUD ist ein eigenständiges Desktop-Fenster. KDE/Wayland legt die Fensterreihenfolge fest; über Vollbildspielen ist keine Einblendung garantiert. Ultra Eco reduziert auch die HUD-Darstellung.',
                                 'muted', wrap=True))
        self._add_section_reset(hud.body, 'hud', 'MiniHUD zurücksetzen')
        self._settings_cards['hud'].append(hud)

        notifications = Card('Hardware-Warnungen')
        self.alert_toggle = QCheckBox('Grenzwert-Warnungen aktivieren')
        self.alert_toggle.setChecked(bool(settings.get('alerts_enabled', False)))
        self.alert_toggle.toggled.connect(lambda checked: self._set_preference('alerts_enabled', checked))
        notifications.body.addWidget(self.alert_toggle)
        notifications.body.addWidget(label('Warnungen erscheinen beim Überschreiten eines Grenzwerts. Erst nach Abkühlung oder sinkender Auslastung kann eine erneute Warnung erfolgen.', 'muted', wrap=True))
        # Shared label column: every value begins at precisely the same x position.
        # A trailing expanding column keeps both columns by the labels, not at the card edge.
        threshold_grid = QGridLayout()
        threshold_grid.setContentsMargins(0, 0, 0, 0)
        threshold_grid.setHorizontalSpacing(10)
        threshold_grid.setVerticalSpacing(9)
        threshold_grid.setColumnStretch(2, 1)
        self.alert_boxes = {}
        self.alert_labels = {}
        for row_index, (key, title, default, lo, hi, unit) in enumerate((
            ('cpu_temp', 'CPU-Temperatur', 90, 40, 110, '°C'),
            ('gpu_temp', 'GPU-Temperatur', 90, 40, 115, '°C'),
            ('ram_usage', 'RAM-Auslastung', 90, 50, 100, '%'),
            ('disk_usage', 'Systemlaufwerk', 95, 50, 100, '%'),
        )):
            value = AlertThresholdField(lo, hi, unit, settings.get(key, default))
            value.valueChanged.connect(lambda v, k=key: self._set_preference(k, v))
            text = label(title, 'strong')
            threshold_grid.addWidget(text, row_index, 0, Qt.AlignLeft | Qt.AlignVCenter)
            threshold_grid.addWidget(value, row_index, 1, Qt.AlignLeft | Qt.AlignVCenter)
            self.alert_boxes[key] = value
            self.alert_labels[key] = text
        notifications.body.addLayout(threshold_grid)
        self._add_section_reset(notifications.body, 'alerts', 'Warnwerte zurücksetzen')
        self._settings_cards['monitoring'].append(notifications)

        # Only visible when the *preferences* deviate from the original values.
        # Dashboard tile positions, update source and language are intentionally
        # not touched by this button.
        restore_row = QHBoxLayout()
        restore_row.addStretch(1)
        # Its visibility is synchronized before the final layout is attached.
        # A parentless button maps as a tiny standalone window on X11/Wayland.
        self.restore_button = QPushButton('Standardwerte wiederherstellen', self)
        self.restore_button.setObjectName('ghostBtn')
        self.restore_button.clicked.connect(self.restore_defaults)
        self.restore_reveal = SoftReveal(self.restore_button, self)
        restore_row.addWidget(self.restore_reveal)
        self._restore_row = restore_row
        self._refresh_restore_button()
        self._search_targets = [
            ('appearance', 'Glas Klang Ton Sound Klicks', self.sound_toggle),
            ('appearance', 'Farbschema Dark Light Glass Black Glass Gold Holographic Minimalistisch Obsidian Champagne Aurora', self.design_tiles[0]),
            ('appearance', 'Akzentfarbe Eigene Farben Bearbeiten Löschen', self.accent_combo),
            ('appearance', 'Hintergrund Bild Hintergrundfarbe automatisch', self.background_combo),
            ('appearance', 'Animationen Bewegung Übergang', self.motion_combo),
            ('hud', 'MiniHUD Anzeigen Einblenden', self.hud_on),
            ('hud', 'MiniHUD Größe Layout', self.hud_size),
            ('hud', 'MiniHUD Deckkraft Transparenz', self.hud_opacity),
            ('hud', 'Systemleiste Tray Schließen', self.close_to_tray),
            ('monitoring', 'Aktualisierungsintervall Live Monitoring', self.interval),
            ('monitoring', 'Warnungen Grenzwerte CPU GPU Temperatur RAM Laufwerk', self.alert_toggle),
            ('energy', 'Ultra Eco Ressourcenschonung Neustarten', self.eco_toggle),
            ('general', 'Standardwerte wiederherstellen Zurücksetzen', self.restore_button),
            ('render', 'Grafik Rendering Backend CPU OpenGL Wayland Vulkan X11', self.render_combo),
            ('maintenance', 'Wartung Maintenance Cache leeren Clear', self.clear_cache_btn),
            ('maintenance', 'Persönliche Einstellungen löschen Delete Preferences Settings', self.clear_preferences_btn),
        ]
        self.advanced = ExpandableCard(self)
        for card in self._settings_cards['render']:
            self.advanced.addWidget(card)
        self.advanced.addWidget(self._maintenance_card)
        self._search_targets.append(('advanced', 'Erweiterte Einstellungen Advanced Settings', self.advanced.header))
        for category in ('appearance', 'general', 'hud', 'monitoring', 'energy'):
            cards = (list(reversed(self._settings_cards[category])) if category == 'hud'
                     else self._settings_cards[category])
            for card in cards:
                self.content.addWidget(card)
        self.content.addWidget(self.advanced)
        self.content.addLayout(self._restore_row)
        self.expansion_follower = ExpansionFollower(self)
        self.refresh_appearance()

    SEARCH_CATEGORIES = {
        'appearance': 'Darstellung', 'general': 'Allgemein',
        'hud': 'MiniHUD & Fenster', 'monitoring': 'Monitoring & Warnungen',
        'energy': 'Leistung & Energie', 'render': 'Grafik-Rendering',
        'maintenance': 'Wartung', 'advanced': 'Erweiterte Einstellungen',
    }

    def install_search_overlay(self, scroll):
        self.search_overlay.install_on(scroll)
        self.search_navigation.install_on(scroll)
        self.expansion_follower.install_on(scroll)

    @staticmethod
    @lru_cache(maxsize=256)
    def _search_normalize(text):
        import unicodedata
        normalized = unicodedata.normalize('NFKD', str(text).casefold())
        return ''.join(c for c in normalized if not unicodedata.combining(c)).replace('ß', 'ss')

    def search_settings(self, query):
        """Predict full or partial settings names; never search outside Settings."""
        from difflib import SequenceMatcher
        self.search_results.clear()
        tokens = self._search_normalize(query).split()
        if not tokens:
            self.search_results.hide()
            self.search_overlay.suggestions_changed()
            self.search_navigation.cancel()
            return

        ranked = []
        if self._search_words is None:
            aliases = {self.sound_toggle: 'Glass Sound Click Tone Volume',
                self.design_tiles[0]: 'Theme Color Scheme Preview', self.accent_combo: 'Accent Color Colour Custom',
                self.background_combo: 'Background Image Wallpaper', self.motion_combo: 'Animation Motion Transition',
                self.hud_on: 'MiniHUD Show Enable', self.hud_size: 'MiniHUD Size Layout',
                self.hud_opacity: 'MiniHUD Opacity Transparency', self.close_to_tray: 'Tray Close Window',
                self.interval: 'Refresh Interval Live Monitoring', self.alert_toggle: 'Alerts Threshold Temperature',
                self.eco_toggle: 'Ultra Eco Energy Power Saving Restart', self.restore_button: 'Reset Restore Defaults',
                self.render_combo: 'Graphics Renderer Rendering Backend', self.clear_cache_btn: 'Maintenance Clear Cache',
                self.clear_preferences_btn: 'Delete Personal Preferences', self.advanced.header: 'Advanced Settings'}
            self._search_words = [self._search_normalize(terms+' '+self.SEARCH_CATEGORIES[key]+' '+
                tr(terms.split(' ')[0])+' '+aliases.get(target, '')).split()
                for key, terms, target in self._search_targets]
        for index, (key, terms, _target) in enumerate(self._search_targets):
            parts = self._search_words[index]
            matches = []
            for token in tokens:
                options = [
                    4 if word == token else 3 if word.startswith(token) else
                    2 if token in word else
                    1 if len(token) >= 3 and SequenceMatcher(None, token, word).ratio() >= .72
                    else 0
                    for word in parts
                ]
                if not options or max(options) == 0:
                    break
                matches.append(max(options))
            if len(matches) == len(tokens):
                primary = self._search_normalize(terms.split(' ')[0]+' '+tr(terms.split(' ')[0]))
                bonus = 2 if any(primary.startswith(token) for token in tokens if len(token) >= 3) else 0
                ranked.append((sum(matches)+bonus, index, key, terms))
        ranked.sort(key=lambda entry: (-entry[0], entry[1]))
        for _score, index, key, terms in ranked[:7]:
            item = QListWidgetItem(tr(terms.split(' ')[0]) + '  ·  ' +
                                   tr(self.SEARCH_CATEGORIES[key]))
            item.setData(Qt.UserRole, index)
            self.search_results.addItem(item)
        self.search_results.setFixedHeight(min(156, 31 * self.search_results.count() + 7))
        self.search_results.setVisible(bool(self.search_results.count()) and
                                       self.search_overlay.expanded)
        self.search_overlay.suggestions_changed()
        # Navigate only when the leading match is distinct; keep typing in the
        # search field and wait briefly so successive prefixes do not jerk it.
        distinct = ranked and (len(ranked) == 1 or ranked[0][0] > ranked[1][0])
        candidate = (self._search_targets[ranked[0][1]][2]
                     if distinct and max(map(len, tokens)) >= 3 else None)
        self.search_navigation.predict(candidate)

    def choose_search_result(self, item):
        index = item.data(Qt.UserRole)
        if not isinstance(index, int) or not (0 <= index < len(self._search_targets)):
            return
        target = self._search_targets[index][2]
        self.search_overlay.result_chosen()
        self.search_navigation.choose(target)

    def _add_section_reset(self, body, section, title):
        row = QHBoxLayout()
        row.addStretch(1)
        button = QPushButton(title)
        button.setObjectName('ghostBtn')
        button.clicked.connect(lambda _=False, key=section: self.reset_category(key))
        reveal = SoftReveal(button, self)
        row.addWidget(reveal)
        body.addLayout(row)
        self._reset_buttons[section] = button
        self._reset_reveals[section] = reveal

    @staticmethod
    def _select_without_signal(widget, data):
        widget.blockSignals(True)
        index = widget.findData(data)
        if index >= 0:
            widget.setCurrentIndex(index)
        widget.blockSignals(False)

    @staticmethod
    def _check_without_signal(widget, checked):
        widget.blockSignals(True)
        widget.setChecked(bool(checked))
        widget.blockSignals(False)

    def reset_category(self, section):
        """Restore only the selected group, preserving user assets and layouts."""
        keys = self.SECTION_DEFAULTS.get(section)
        if keys is None:
            return
        changes = {key: self.DEFAULTS[key] for key in keys}
        if not settings.set_many(changes):
            return
        if section == 'appearance':
            self._select_without_signal(self.accent_combo, self.DEFAULTS['accent'])
            self._select_without_signal(self.motion_combo, self.DEFAULTS['motion'])
            self._select_without_signal(self.background_combo, self.DEFAULTS['background_style'])
            self._select_without_signal(self.background_fit_combo, self.DEFAULTS['custom_background_fit'])
            self.sync_background_controls()
            self.window.apply_appearance()
            self.refresh_appearance()
        elif section == 'hud':
            self._check_without_signal(self.hud_on, False)
            self._select_without_signal(self.hud_size, 'compact')
            self._select_without_signal(self.hud_opacity, 90)
            for key, box in self.hud_metrics.items():
                self._check_without_signal(box, key in DEFAULT_KEYS)
            toggle = getattr(self.window, 'set_mini_hud_enabled', None)
            if callable(toggle):
                toggle(False)
            refresh = getattr(self.window, 'refresh_mini_hud', None)
            if callable(refresh):
                refresh()
        else:
            self._check_without_signal(self.alert_toggle, False)
            for key, box in self.alert_boxes.items():
                box.blockSignals(True)
                box.setValue(self.DEFAULTS[key])
                box.blockSignals(False)
        self._refresh_restore_button()

    def retranslate(self):
        self._search_words = None
        self.search.setPlaceholderText(tr('Einstellungen durchsuchen …'))
        self.search_overlay.refresh_theme()

    def set_hud_enabled(self, enabled):
        callback = getattr(self.window, 'set_mini_hud_enabled', None)
        if callable(callback):
            callback(enabled)
        else:
            # Standalone settings pages may not have a MiniHUD window.
            settings.set('mini_hud_enabled', bool(enabled))
        self._refresh_restore_button()

    def sync_hud_controls(self):
        if not hasattr(self, 'hud_on'):
            return
        self.hud_on.blockSignals(True)
        self.hud_on.setChecked(bool(settings.get('mini_hud_enabled', False)))
        self.hud_on.blockSignals(False)
        self._refresh_restore_button()

    def change_hud_size(self, *_):
        self.change_hud_option('mini_hud_layout', self.hud_size.currentData())

    def change_hud_option(self, key, value):
        settings.set(key, value)
        refresh = getattr(self.window, 'refresh_mini_hud', None)
        if callable(refresh):
            refresh()
        self._refresh_restore_button()

    def change_hud_metrics(self, *_):
        choices = [key for key, box in self.hud_metrics.items() if box.isChecked()]
        if not choices:
            return
        settings.set('mini_hud_metrics', choices)
        refresh = getattr(self.window, 'refresh_mini_hud', None)
        if callable(refresh):
            refresh()
        self._refresh_restore_button()

    def _refresh_renderer_status(self):
        active = getattr(self.window, 'render_backend_active', renderer.SOFTWARE)
        pending = renderer.desired() != active
        if eco.enabled():
            self.render_status.setText(tr(
                'Ultra Eco wartet auf Neustart für CPU-Rendering.'
                if pending else 'Ultra Eco: CPU-Rendering aktiv.'))
            self.render_restart_button.setVisible(False)
            self.eco_restart_button.setVisible(pending)
            return
        self.eco_restart_button.setVisible(False)
        selected = self.render_combo.currentData()
        if selected != active:
            status = tr('Rendering-Wechsel vorgemerkt – bitte Vitalux neu starten.')
        elif active == renderer.OPENGL:
            status = tr('Aktiv: OpenGL-GPU-Rendering (experimentell)')
        elif active in renderer.QUICK_MODES:
            status = tr('Aktiv: ') + tr(renderer.DESCRIPTIONS[active])
        else:
            status = tr('Aktiv: CPU-Rendering (Standard)')
        self.render_status.setText(status)
        self.render_restart_button.setVisible(selected != active)

    def clear_app_cache(self):
        """Drop only transient Vitalux-render caches, never user/system data."""
        from . import user_background, wallpaper_accents
        user_background._scaled_image.cache_clear()
        wallpaper_accents._sample.cache_clear()
        self._background_preview_key = None
        self.sync_background_controls()
        QMessageBox.information(
            self, 'Vitalux', tr('Temporärer Vitalux-Bild- und Farb-Cache geleert. '
                              'Einstellungen und importierte Bilder bleiben erhalten.'))

    def delete_personal_preferences(self):
        """Explicitly confirmed deletion of only the personal settings file."""
        from pathlib import Path
        answer = QMessageBox.question(
            self, 'Vitalux',
            tr('Wirklich alle gespeicherten Vitalux-Einstellungen löschen? '
               'Farbauswahl, Layouts, Warnwerte und Programmeinstellungen gehen verloren. '
               'Importierte Bilddateien bleiben auf dem Datenträger. '
               'Vitalux wird anschließend neu gestartet.'),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        def commit():
            try:
                Path(settings.PATH).unlink(missing_ok=True)
                return True
            except OSError as exc:
                QMessageBox.warning(self, 'Vitalux', str(exc))
                return False
        self._restart_after_reset(commit)

    def _restart_after_reset(self, commit):
        if self.window.restart_for_renderer(commit=commit):
            self.restore_reveal.setRevealed(False)
        else:
            QMessageBox.warning(self, 'Vitalux', tr('Ein Vorgang läuft noch. Bitte danach erneut zurücksetzen.'))

    def change_renderer(self, *_):
        if eco.enabled():
            return
        selected = self.render_combo.currentData()
        if selected not in renderer.CHOICES:
            return
        settings.set('render_backend', selected)
        # The QWidget/OpenGL/QtQuick scene graphics APIs cannot be hot-swapped
        # safely while the app and background threads are active.
        self._refresh_renderer_status()
        self._refresh_restore_button()

    def restart_for_renderer(self):
        """Ask MainWindow for a graceful full-process restart via run.sh."""
        if self.render_combo.currentData() == getattr(self.window, 'render_backend_active', renderer.SOFTWARE):
            return
        if not self.window.restart_for_renderer():
            QMessageBox.warning(self, 'Vitalux',
                tr('Vitalux kann wegen eines laufenden Vorgangs gerade nicht neu starten.'))

    def restart_for_eco(self):
        """Apply CPU or previously saved GPU graphics with a safe full restart."""
        if not self.window.restart_for_renderer():
            QMessageBox.warning(self, 'Vitalux',
                tr('Vitalux kann wegen eines laufenden Vorgangs gerade nicht neu starten.'))

    def toggle_ultra_eco(self, enabled):
        """Apply appearance live, but wait for user-initiated graphics restart."""
        enabled = bool(enabled)
        old = eco.enabled()
        if enabled == old:
            return
        if not settings.set(eco.KEY, enabled):
            self.eco_toggle.blockSignals(True)
            self.eco_toggle.setChecked(old)
            self.eco_toggle.blockSignals(False)
            return
        # No automatic application close: the user clicks the adjacent
        # restart button when an incompatible GPU/CPU host must be swapped.
        self.window.apply_appearance()
        self.window.set_interval(eco.interval())
        self.refresh_appearance()
        self._refresh_restore_button()

    def _set_preference(self, key, value):
        settings.set(key, value)
        self._refresh_restore_button()

    def _refresh_restore_button(self):
        values = settings.get_many(self.DEFAULTS)
        for section, keys in self.SECTION_DEFAULTS.items():
            button = self._reset_buttons.get(section)
            if button is not None:
                self._reset_reveals[section].setRevealed(any(values[key] != self.DEFAULTS[key] for key in keys))
        self.restore_reveal.setRevealed(
            any(values[key] != default for key, default in self.DEFAULTS.items()))

    def restore_defaults(self):
        answer = QMessageBox.question(
            self, 'Vitalux',
            tr('Alle Darstellungs-, MiniHUD-, Überwachungs- und Warnungseinstellungen zurücksetzen? Dashboard-Anordnung, importierte Bilder und Sprache bleiben erhalten. Vitalux wird anschließend neu gestartet.'),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        self._restart_after_reset(lambda: settings.set_many(self.DEFAULTS))

    def refresh_appearance(self):
        ultra = eco.enabled()
        self._check_without_signal(self.sound_toggle, settings.get('ui_sounds', True))
        self.sound_volume.blockSignals(True)
        self.sound_volume.setValue(settings.get('ui_sound_volume', 70))
        self.sound_volume.blockSignals(False)
        self.sound_volume_value.setText(str(self.sound_volume.value())+' %')
        self.eco_toggle.blockSignals(True)
        self.eco_toggle.setChecked(ultra)
        self.eco_toggle.blockSignals(False)
        active_backend = getattr(self.window, 'render_backend_active', renderer.SOFTWARE)
        pending_switch = renderer.desired() != active_backend
        if ultra:
            status = ('Ultra Eco vorgemerkt – bitte Jetzt neu starten klicken.'
                      if pending_switch else
                      'Ultra Eco aktiv: alle Effekte aus, einfache Darstellung und 10 Sekunden Messintervall.')
        else:
            status = ('Ultra Eco deaktiviert – bitte Jetzt neu starten klicken.'
                      if pending_switch else '')
        self.eco_status.setText(tr(status))
        self.background_combo.setEnabled(not ultra)
        self.custom_background_area.setEnabled(not ultra)
        self.motion_combo.setEnabled(not ultra)
        for tile in self.design_tiles:
            tile.setEnabled(not ultra)
            tile.setChecked(theme.mode() == tile.key)
            tile.update()
        self.interval.setEnabled(not ultra)
        self.render_combo.setEnabled(not ultra)
        # Show the remembered renderer after leaving Ultra Eco.
        saved = settings.get('render_backend', renderer.SOFTWARE)
        if saved in renderer.CHOICES and self.render_combo.currentData() != saved:
            self.render_combo.blockSignals(True)
            self.render_combo.setCurrentIndex(self.render_combo.findData(saved))
            self.render_combo.blockSignals(False)
        self.eco_toggle.setEnabled(True)
        for i in range(self.render_combo.count()):
            backend = self.render_combo.itemData(i)
            self.render_combo.setItemText(i, tr(renderer.DESCRIPTIONS[backend]))
        self._sync_custom_accent_actions()
        self.theme_note.setText(
            tr('Ultra Eco verwendet vorübergehend einen einfachen, flachen Skin.')
            if ultra else tr(self.mode_notes.get(theme.mode(), self.mode_notes['dark'])))
        self.accent_preview.setColor(theme.accent())
        self.sync_background_controls()
        self._refresh_renderer_status()
        self.search_overlay.refresh_theme()
        self._refresh_restore_button()

    def select_design(self, key):
        if eco.enabled() or key not in dict(theme.CHOICES):
            return
        if not settings.set('theme', key):
            return
        self.window.apply_appearance()
        self.refresh_appearance()

    def change_accent(self, val):
        if eco.enabled() or theme.mode() == 'black_glass_gold' or theme.mode() in premium.KEYS or not self.accent_combo.isEnabled():
            return
        if theme.mode() == 'black_glass' and any(
                item['color'] == val for item in self.custom_accents):
            return
        if not val or (wallpaper_accents.is_wallpaper_accent(val)
                       and not wallpaper_accents.available()):
            return
        if val == wallpaper_accents.AUTO:
            current = settings.get('accent', '#4f8cff')
            if not wallpaper_accents.is_wallpaper_accent(current):
                settings.set_many({'accent_before_wallpaper_auto': current,
                                   'accent': val})
            else:
                settings.set('accent', val)
        else:
            settings.set('accent', val)
        index = self.accent_combo.findData(val)
        if index >= 0 and self.accent_combo.currentIndex() != index:
            self.accent_combo.blockSignals(True)
            self.accent_combo.setCurrentIndex(index)
            self.accent_combo.blockSignals(False)
        self._sync_custom_accent_actions()
        self.window.apply_appearance()
        self._refresh_restore_button()

    @staticmethod
    def _read_custom_accents():
        saved = settings.get('custom_accents', [])
        if not isinstance(saved, list):
            return []
        result, seen = [], set()
        for entry in saved[:60]:
            if not isinstance(entry, dict):
                continue
            color = QColor(str(entry.get('color', '')))
            name = str(entry.get('name', '')).strip()[:32]
            if (color.isValid() and name and color.name() not in seen
                    and color.name() not in PreferencesPage.PRESET_COLORS):
                result.append({'name': name, 'color': color.name()})
                seen.add(color.name())
        # Repair settings written by older releases, so the protected default
        # palette survives subsequent upgrades and application restarts.
        if saved != result:
            settings.set('custom_accents', result)
        return result

    def _sync_custom_accent_actions(self):
        gold = theme.mode() in theme.FIXED_MODES or eco.enabled()
        custom_locked = theme.mode() in ('black_glass', *theme.FIXED_MODES) or eco.enabled()
        self.accent_combo.setLocked(
            ('Ultra Eco verwendet eine feste, einfache Farbpalette.' if eco.enabled() else
             'Dieses Farbschema verwendet eine feste Farbpalette. Eigene Akzentfarben sind hier nicht verfügbar.') if gold else '',
            'Feste Designpalette')
        self.custom_accent_button.setEnabled(not custom_locked)
        self.edit_custom_accent_button.setEnabled(not custom_locked)
        self.remove_custom_accent_button.setEnabled(not custom_locked)
        # In Black Glass individual accent entries are grayed out like
        # the unavailable automatic wallpaper accent; presets still work.
        model = self.accent_combo.model()
        for i in range(self.accent_combo.count()):
            if any(item['color'] == self.accent_combo.itemData(i)
                   for item in self.custom_accents):
                entry = model.item(i)
                if entry is not None:
                    entry.setEnabled(not custom_locked)
        # A shortened combo must not hide the selected custom color's name.
        self.accent_combo.setToolTip(self.accent_combo.currentText())
        selected = self.accent_combo.currentData()
        own_color_selected = (
            selected not in self.PRESET_COLORS
            and any(item['color'] == selected for item in self.custom_accents)
        )
        self.edit_custom_accent_button.setVisible(own_color_selected)
        self.remove_custom_accent_button.setVisible(own_color_selected)

    @staticmethod
    def _unique_custom_accent_name(combo, requested, exclude_index=None):
        name = requested.strip()[:32] or tr('Eigene Farbe')
        taken = {combo.itemText(i).casefold() for i in range(combo.count())
                 if i != exclude_index}
        original, number = name, 2
        while name.casefold() in taken:
            name = f'{original[:25]} ({number})'
            number += 1
        return name

    def edit_custom_accent(self):
        """Edit name and/or color of the selected saved accent, keeping its slot."""
        if theme.mode() in ('black_glass', *theme.FIXED_MODES) or eco.enabled():
            return
        combo = self.accent_combo
        index = combo.currentIndex()
        original_color = combo.currentData()
        entry = next((item for item in self.custom_accents
                      if item['color'] == original_color), None)
        if entry is None or index < 0 or original_color in self.PRESET_COLORS:
            return
        updated = QColorDialog.getColor(
            QColor(original_color), self, tr('Eigene Farbe bearbeiten'))
        if not updated.isValid():
            return
        new_color = updated.name()
        # The color palette is a unique-keyed collection: don't steal another
        # preset's value or leave two identically keyed custom entries.
        if new_color != original_color and any(
                combo.itemData(i) == new_color for i in range(combo.count()) if i != index):
            QMessageBox.information(self, 'Vitalux', tr('Diese Akzentfarbe ist bereits vorhanden.'))
            return
        new_name, accepted = QInputDialog.getText(
            self, tr('Eigene Farbe bearbeiten'),
            tr('Wie soll diese Akzentfarbe heißen?'), text=entry['name'])
        if not accepted:
            return
        new_name = self._unique_custom_accent_name(combo, new_name, index)
        if new_color == original_color and new_name == entry['name']:
            return
        # Apply the edit as a single operation; do not accidentally add an
        # extra entry or switch to the distribution color along the way.
        combo.blockSignals(True)
        try:
            combo.setItemText(index, new_name)
            combo.setItemData(index, new_color)
        finally:
            combo.blockSignals(False)
        entry['color'], entry['name'] = new_color, new_name
        settings.set('custom_accents', self.custom_accents)
        self.change_accent(new_color)

    def remove_custom_accent(self):
        if theme.mode() in ('black_glass', *theme.FIXED_MODES) or eco.enabled():
            return
        value = self.accent_combo.currentData()
        if (value in self.PRESET_COLORS
                or not any(item['color'] == value for item in self.custom_accents)):
            return
        self.custom_accents = [item for item in self.custom_accents if item['color'] != value]
        settings.set('custom_accents', self.custom_accents)
        idx = self.accent_combo.findData(value)
        if idx >= 0:
            self.accent_combo.removeItem(idx)
        self.accent_combo.setCurrentIndex(0)  # Distribution is a safe fallback.
        self.change_accent('auto')
        self._sync_custom_accent_actions()

    def custom_accent(self, combo):
        if theme.mode() in ('black_glass', *theme.FIXED_MODES) or eco.enabled():
            return
        color = QColorDialog.getColor(QColor(theme.accent()), self, tr('Akzentfarbe wählen'))
        if not color.isValid():
            return
        value = color.name()
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)
            return
        name, accepted = QInputDialog.getText(
            self, tr('Eigene Farbe benennen'),
            tr('Wie soll diese Akzentfarbe heißen?'), text=tr('Eigene Farbe'))
        if not accepted:
            return
        name = self._unique_custom_accent_name(combo, name)
        self.custom_accents.append({'name': name, 'color': value})
        settings.set('custom_accents', self.custom_accents)
        combo.addItem(name, value)
        combo.setCurrentIndex(combo.count()-1)
        self._sync_custom_accent_actions()

    def refresh_background_images(self):
        selected = settings.get('custom_background_selected', '')
        self.background_image_combo.blockSignals(True)
        self.background_image_combo.clear()
        for item in user_background.images():
            self.background_image_combo.addItem(item['name'], item['file'])
        index = self.background_image_combo.findData(selected)
        self.background_image_combo.setCurrentIndex(index if index >= 0 else (0 if self.background_image_combo.count() else -1))
        self.background_image_combo.blockSignals(False)
        self.sync_background_controls()

    def _sync_wallpaper_accent_option(self):
        """Disable only wallpaper-auto when no valid personal image is selected."""
        index = self.accent_combo.findData(wallpaper_accents.AUTO)
        if index < 0:
            return
        enabled = wallpaper_accents.available()
        item = self.accent_combo.model().item(index)
        if item is not None:
            item.setEnabled(enabled)
        self.accent_combo.setItemData(index, tr('Nur mit eigenem Hintergrundbild verfügbar')
                                      if not enabled else
                                      tr('Akzentfarbe aus dem eigenen Hintergrundbild'),
                                      Qt.ToolTipRole)
        chosen = settings.get('accent', '#4f8cff')
        if wallpaper_accents.is_wallpaper_accent(chosen) and not enabled:
            fallback = wallpaper_accents.manual_fallback()
            settings.set('accent', fallback)
            self.accent_combo.blockSignals(True)
            self.accent_combo.setCurrentIndex(max(0, self.accent_combo.findData(fallback)))
            self.accent_combo.blockSignals(False)

    def sync_background_controls(self):
        locked = theme.background_locked()
        self.background_combo.setLocked(
            ('Ultra Eco verwendet einen festen, einfachen Hintergrund.' if eco.enabled() else
             'Dieses Farbschema hat einen festen Hintergrund. Wähle ein anderes Farbschema, um eigene Bilder oder Hintergründe zu verwenden.') if locked else '',
            'Fester Hintergrund')
        self.custom_background_area.setEnabled(not locked)
        custom = not locked and self.background_combo.currentData() == 'custom_image'
        self._sync_wallpaper_accent_option()
        self.custom_background_area.setVisible(custom)
        count = self.background_image_combo.count()
        self.remove_background_button.setEnabled(count > 0)
        self.background_fit_combo.setEnabled(count > 0)
        self.background_preview.setVisible(custom and count > 0)
        self.background_performance_note.setVisible(custom)
        if custom and count:
            picture = (self.background_image_combo.currentData(),
                       self.background_fit_combo.currentData() or 'cover')
            if picture != getattr(self, '_background_preview_key', None):
                self.background_preview.setPixmap(user_background.draw(QSize(320, 120), *picture))
                self._background_preview_key = picture
        else:
            self._background_preview_key = None

    def add_background_image(self):
        names, _ = QFileDialog.getOpenFileNames(self, tr('Bilder auswählen'), '', 'Bilder (*.png *.jpg *.jpeg *.webp *.bmp)')
        if not names:
            return
        entries = user_background.images()
        failures = []
        new = None
        for name in names:
            try:
                new = user_background.import_image(name)
                entries.append(new)
            except (ValueError, OSError) as exc:
                failures.append(f'{name}: {exc}')
        if new:
            settings.set('custom_backgrounds', entries)
            settings.set('custom_background_selected', new['file'])
            settings.set('background_style', 'custom_image')
            self.background_combo.blockSignals(True)
            self.background_combo.setCurrentIndex(self.background_combo.findData('custom_image'))
            self.background_combo.blockSignals(False)
            self.refresh_background_images()
            self.window.apply_appearance()
            self._refresh_restore_button()
        if failures:
            QMessageBox.warning(self, 'Vitalux', '\n'.join(failures[:4]))

    def select_background_image(self, *_):
        filename = self.background_image_combo.currentData()
        if filename:
            settings.set('custom_background_selected', filename)
            self.sync_background_controls()
            if self.background_combo.currentData() == 'custom_image':
                self.window.apply_appearance()

    def remove_background_image(self):
        filename = self.background_image_combo.currentData()
        if not filename:
            return
        if QMessageBox.question(self, 'Vitalux', tr('Importiertes Bild entfernen? Das Original bleibt erhalten.'),
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        remaining = [item for item in user_background.images() if item['file'] != filename]
        path = user_background.image_path(filename)
        try:
            if path is not None:
                path.unlink()
        except OSError as exc:
            QMessageBox.warning(self, 'Vitalux', str(exc))
            return
        settings.set('custom_backgrounds', remaining)
        settings.set('custom_background_selected', remaining[0]['file'] if remaining else '')
        if not remaining:
            settings.set('background_style', 'theme_default')
            self.background_combo.blockSignals(True)
            self.background_combo.setCurrentIndex(self.background_combo.findData('theme_default'))
            self.background_combo.blockSignals(False)
        self.refresh_background_images()
        self.window.apply_appearance()
        self._refresh_restore_button()

    def change_background_fit(self, *_):
        fit = self.background_fit_combo.currentData()
        if fit is None:
            return
        settings.set('custom_background_fit', fit)
        self.sync_background_controls()
        if self.background_combo.currentData() == 'custom_image':
            self.window.apply_appearance()
        self._refresh_restore_button()

    def change_background(self, *_):
        if theme.background_locked():
            self._select_without_signal(self.background_combo, settings.get('background_style', 'theme_default'))
            self.sync_background_controls()
            return
        style = self.background_combo.currentData()
        if style == 'custom_image' and not self.background_image_combo.count():
            self.add_background_image()
            if not self.background_image_combo.count():
                self.background_combo.blockSignals(True)
                self.background_combo.setCurrentIndex(max(0, self.background_combo.findData(settings.get('background_style', 'theme_default'))))
                self.background_combo.blockSignals(False)
                self.sync_background_controls()
                return
        settings.set('background_style', style)
        self.sync_background_controls()
        self.window.apply_appearance()
        self._refresh_restore_button()

    def change_motion(self, *_):
        if eco.enabled():
            return
        profile = self.motion_combo.currentData()
        if profile in motion.MODES:
            self._set_preference('motion', profile)
            self.window.apply_appearance()

    def change_interval(self, *_):
        if eco.enabled():
            return
        val = self.interval.currentData()
        if val:
            self._set_preference('interval', int(val))
            self.window.set_interval(int(val))

    def export_diagnostics(self):
        from .diagnostics import export_report
        filename, _ = QFileDialog.getSaveFileName(self, 'Fehlerbericht speichern',
             f'Vitalux-Diagnose-{datetime.now():%Y%m%d-%H%M%S}.json', 'JSON (*.json)')
        if not filename:
            return
        try:
            export_report(filename, include_errors=True, sample=self.window.last_sample)
        except OSError as exc:
            QMessageBox.warning(self, 'Vitalux', f'Export fehlgeschlagen: {exc}')
        else:
            QMessageBox.information(self, 'Vitalux', 'Fehlerbericht gespeichert.')

    def export(self):
        """Export an explicit local system snapshot; never upload diagnostics."""
        from .monitor_insights import report_data, write_report
        if not self.window.last_sample:
            QMessageBox.information(self, "Vitalux", tr("Warte auf die erste Messung."))
            return
        suggested = f"Vitalux-Bericht-{datetime.now():%Y%m%d-%H%M%S}.txt"
        filename, selected = QFileDialog.getSaveFileName(
            self, tr("Systembericht speichern"), suggested,
            "Text (*.txt);;JSON (*.json)")
        if not filename:
            return
        if not filename.lower().endswith((".json", ".txt")):
            filename += ".json" if "JSON" in selected else ".txt"
        sample = self.window.last_sample
        report = report_data(sample, system_static(), __version__,
                             sample.get("session_extrema"))
        try:
            write_report(filename, report)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Vitalux", tr("Export fehlgeschlagen: {}").format(exc))
        else:
            QMessageBox.information(self, "Vitalux", tr("Systembericht gespeichert."))
