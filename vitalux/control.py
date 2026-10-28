"""Hardware-sensor page, appearance settings and customizable dashboard controls."""
from .appearance_preferences import AppearancePreferences
from . import DEFAULT_THEME
from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QSizePolicy, QVBoxLayout, QWidget
from .ui_locale import QCheckBox, QComboBox, QListWidgetItem, QMessageBox, QPushButton

from . import settings, theme, backdrops, user_background, wallpaper_accents, renderer, eco, premium, design_catalog
from .page_base import Page
from .widgets import Card, label
from .i18n import tr
from .desktop_overlay import DEFAULT_KEYS
from .settings_search import FloatingSettingsSearch, _SearchIcon
from .choice_combo import ChoiceComboBox
from .settings_navigation import SettingsNavigator
from .soft_controls import AccentSwatch, ResponsiveActions, SoftReveal


from .threshold_field import AlertThresholdField


class PreferencesPage(AppearancePreferences, Page):
    # Built-in colors are never editable or removable, even when older saved
    # settings incorrectly contain an entry with the same hex color.
    PRESET_ACCENTS = (('Originalfarben', 'design_default'),) + tuple(
        (item['title'],'palette:'+key) for key,item in design_catalog.PRESETS.items()) + (
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
        'theme': DEFAULT_THEME, 'accent': 'design_default', 'motion': 'smooth', 'component_images':True,
        'background_style': 'theme_default', 'custom_background_fit': 'cover',
        'render_backend': renderer.SOFTWARE, 'ultra_eco': False,
        'interval': 1, 'close_to_tray': True, 'alerts_enabled': False,
        'cpu_temp': 90, 'gpu_temp': 90, 'ram_usage': 90, 'disk_usage': 95,
        'mini_hud_enabled': False, 'mini_hud_layout': 'compact',
        'mini_hud_opacity': 90,
        'mini_hud_metrics': list(DEFAULT_KEYS),
        'network_app_limits': {},
        'primary_gpu': '', 'chart_preferences': {}, 'component_picture_customized': False,
    }
    SECTION_DEFAULTS = {
        'appearance': design_catalog.FIELDS,
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
        look.body.addWidget(label('Design', 'strong'))
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
        from .design_settings import Gallery
        self.design_gallery_scroll=Gallery(self.design_gallery,self.design_tiles)
        look.body.addWidget(self.design_gallery_scroll)
        self.theme_note = label('', 'muted', wrap=True)
        self.theme_note.setObjectName('themeDescription')
        look.body.addWidget(self.theme_note)
        self.mode_notes = {key: title+' · Akzentfarben und Hintergrund sind anpassbar.'
                           for key,title in design_catalog.CHOICES}
        self.mode_notes['eclipse_crystal']='Eclipse Crystal'
        self.mode_notes['dark']=''
        self.theme_note.setText(tr(self.mode_notes.get(theme.mode(),'')))
        accent_row = QVBoxLayout()
        accent_selector = QHBoxLayout()
        accent_selector.addWidget(label('Akzentfarbe', 'strong'))
        accent = ChoiceComboBox()
        self.accent_combo = accent
        for title, value in self.PRESET_ACCENTS:
            accent.addItem(title, value)
        self.custom_accents = self._read_custom_accents()
        stored = settings.get('accent', 'design_default')
        if wallpaper_accents.is_legacy_accent(stored):
            stored = wallpaper_accents.AUTO
        stored = wallpaper_accents.effective_selection(stored)
        if stored != settings.get('accent', 'design_default'):
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
            'Funkeln hat einen animierten Hintergrund. '
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
        self.component_images = QCheckBox('Komponentenbilder anzeigen')
        self.component_images.setChecked(settings.get('component_images',True) is not False)
        self.component_images.toggled.connect(self.change_component_images)
        look.body.addWidget(self.component_images)
        self.component_images_description=label('Zeigt verfügbare Produktbilder von Prozessor, Grafikkarte, Arbeitsspeicher und Mainboard. Die Komponenteninformationen werden immer mittig dargestellt. Bereits geladene Bilder bleiben gespeichert.','muted',wrap=True)
        look.body.addWidget(self.component_images_description)
        self._add_section_reset(look.body, 'appearance', 'Design zurücksetzen')
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
        render_caption = label('Render-Methode', 'strong')
        self.render_combo = QComboBox()
        self.render_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.render_combo.setMaximumWidth(380)
        for backend in renderer.CHOICES:
            self.render_combo.addItem(tr(renderer.DESCRIPTIONS[backend]), backend)
        selected_renderer = settings.get('render_backend', renderer.SOFTWARE)
        if selected_renderer not in renderer.CHOICES:
            selected_renderer = renderer.SOFTWARE
        self.render_combo.setCurrentIndex(max(0, self.render_combo.findData(selected_renderer)))
        self.render_combo.currentIndexChanged.connect(self.change_renderer)
        render_card.body.addWidget(ResponsiveActions([render_caption, self.render_combo]))
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
        maintenance = Card('Wartung')
        maintenance.setParent(self)  # Visibility changes must never map an orphan window.
        self.reset_description = label(
            'Setzt alle Einstellungen dieses Profils zurück: Design, Farben, Layouts, Sprache, '
            'Warnwerte und Grafik-Renderer. Gespeicherte eigene Farben, importierte Bildkopien '
            'und der Vitalux-Cache werden gelöscht. Originalbilder und das andere Updateprofil '
            'bleiben erhalten. '
            'Spielberichte und Launcher-Verbindungen bleiben erhalten; Overlay-Profile werden zurückgesetzt. Danach startet Vitalux neu und zeigt die Anleitung.',
            'muted', wrap=True)
        maintenance.body.addWidget(self.reset_description)
        self.restore_button = QPushButton('Standardwerte wiederherstellen', self)
        self.restore_button.setObjectName('ghostBtn')
        self.restore_button.clicked.connect(self.restore_defaults)
        self.restore_reveal = SoftReveal(self.restore_button, self)
        maintenance.body.addWidget(self.restore_reveal, 0, Qt.AlignLeft)
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
        tray.body.addWidget(label('Tray-Hover zeigt CPU-, GPU- und RAM-Auslastung sowie Temperaturen. Das Kontextmenü bietet Fenster-, Overlay- und Beenden-Aktionen.', 'muted', wrap=True))
        self._settings_cards['hud'].append(tray)

        hud = Card('Vitalux Overlay · Desktop')
        hud.body.addWidget(label('Separates Desktop-Fenster mit den vorhandenen Vitalux-Messwerten. '                                 'Auch bei verborgenem Hauptfenster nutzbar; keine zusätzliche Sensorabfrage.', 'muted', wrap=True))
        self.hud_on = QCheckBox('Desktop-Overlay anzeigen')
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
        hud.body.addWidget(label('Messwerte im Desktop-Overlay', 'strong'))
        self.hud_metrics = {}
        metric_grid = QGridLayout()
        from .desktop_overlay import METRIC_OPTIONS, DEFAULT_KEYS
        selections = settings.get('mini_hud_metrics', DEFAULT_KEYS)
        for idx, (key, title, _unit) in enumerate(METRIC_OPTIONS):
            box = QCheckBox(title)
            box.setProperty('selectionControl',True)
            box.setChecked(key in selections)
            box.toggled.connect(self.change_hud_metrics)
            metric_grid.addWidget(box, idx // 2, idx % 2)
            self.hud_metrics[key] = box
        hud.body.addLayout(metric_grid)
        hud.body.addWidget(label('Das Desktop-Overlay ist ein eigenständiges Desktop-Fenster. KDE/Wayland legt die Fensterreihenfolge fest; über Vollbildspielen ist keine Einblendung garantiert. Ultra Eco reduziert auch die HUD-Darstellung.',
                                 'muted', wrap=True))
        hud.body.addWidget(label('Für Spiele mit FPS und automatischer Auswertung: Öffne den Reiter Spiele und richte dort MangoHud ein.', 'muted', wrap=True))
        self._add_section_reset(hud.body, 'hud', 'Desktop-Overlay zurücksetzen')
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

        self._refresh_restore_button()
        self._search_targets = [
            ('appearance','Komponentenbilder anzeigen CPU RAM Grafik Mainboard',self.component_images),
            ('appearance', 'Design Light Glass Obsidian Crystal Atrium Nebula Prism Quantum Core', self.design_tiles[0]),
            ('appearance', 'Akzentfarbe Eigene Farben Bearbeiten Löschen', self.accent_combo),
            ('appearance', 'Hintergrund Bild Hintergrundfarbe automatisch', self.background_combo),
            ('appearance', 'Animationen Bewegung Übergang', self.motion_combo),
            ('hud', 'MiniHUD Overlay Anzeigen Einblenden', self.hud_on),
            ('hud', 'MiniHUD Overlay Größe Layout', self.hud_size),
            ('hud', 'MiniHUD Overlay Deckkraft Transparenz', self.hud_opacity),
            ('hud', 'Systemleiste Tray Schließen', self.close_to_tray),
            ('monitoring', 'Aktualisierungsintervall Live Monitoring', self.interval),
            ('monitoring', 'Warnungen Grenzwerte CPU GPU Temperatur RAM Laufwerk', self.alert_toggle),
            ('energy', 'Ultra Eco Ressourcenschonung Neustarten', self.eco_toggle),
            ('render', 'Grafik Rendering Backend CPU OpenGL Wayland Vulkan X11', self.render_combo),
            ('maintenance', 'Wartung Maintenance', self._maintenance_card),
            ('maintenance', 'Standardwerte wiederherstellen Zurücksetzen Werkseinstellungen Cache Reset Restore Defaults Delete Personal Preferences', self.restore_button),
        ]
        self.advanced = Card()
        self.advanced.header=label('Erweiterte Einstellungen','strong')
        self.advanced.body.addWidget(self.advanced.header)
        self.advanced.panel=QWidget(self.advanced)
        advanced_layout=QVBoxLayout(self.advanced.panel)
        advanced_layout.setContentsMargins(0,0,0,0)
        self.advanced.body.addWidget(self.advanced.panel)
        for card in self._settings_cards['render']:
            advanced_layout.addWidget(card)
        advanced_layout.addWidget(self._maintenance_card)
        self._search_targets.append(('advanced', 'Erweiterte Einstellungen Advanced Settings', self.advanced.header))
        from .design_settings import CardDeck
        for card in self._settings_cards['appearance']:self.content.addWidget(card)
        deck=[]
        for category in ('general', 'hud', 'monitoring', 'energy'):
            cards = (list(reversed(self._settings_cards[category])) if category == 'hud'
                     else self._settings_cards[category])
            for card in cards:
                deck.append(card)
        self.settings_deck=CardDeck(deck)
        self.content.addWidget(self.settings_deck)
        self.content.addWidget(self.advanced)
        self.refresh_appearance()

    SEARCH_CATEGORIES = {
        'appearance': 'Darstellung', 'general': 'Allgemein',
        'hud': 'Overlay & Fenster', 'monitoring': 'Monitoring & Warnungen',
        'energy': 'Leistung & Energie', 'render': 'Grafik-Rendering',
        'maintenance': 'Wartung', 'advanced': 'Erweiterte Einstellungen',
    }

    def install_search_overlay(self, scroll):
        self.search_overlay.install_on(scroll)
        self.search_navigation.install_on(scroll)

    @staticmethod
    @lru_cache(maxsize=256)
    def _search_normalize(text):
        import unicodedata
        normalized = unicodedata.normalize('NFKD', str(text).casefold())
        return ''.join(c for c in normalized if not unicodedata.combining(c)).replace('ß', 'ss')

    def search_settings(self, query):
        """Predict full or partial settings names; never search outside Settings."""
        hidden_design={'timbooh':'eclipse_crystal'}.get(query.strip().casefold())
        if hidden_design:
            if eco.enabled():settings.set('ultra_eco',False)
            if design_catalog.switch(hidden_design):
                self.window.apply_appearance()
                self.refresh_appearance()
            self.search.clear()
            return
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
            aliases = {self.component_images:'Component Pictures Images Photos Hardware Show', self.design_tiles[0]: 'Theme Design Preview', self.accent_combo: 'Accent Color Colour Custom',
                self.background_combo: 'Background Image Wallpaper', self.motion_combo: 'Animation Motion Transition',
                self.hud_on: 'MiniHUD Show Enable', self.hud_size: 'MiniHUD Size Layout',
                self.hud_opacity: 'MiniHUD Opacity Transparency', self.close_to_tray: 'Tray Close Window',
                self.interval: 'Refresh Interval Live Monitoring', self.alert_toggle: 'Alerts Threshold Temperature',
                self.eco_toggle: 'Ultra Eco Energy Power Saving Restart', self.restore_button: 'Reset Restore Defaults',
                self.render_combo: 'Graphics Renderer Rendering Backend', self._maintenance_card: 'Maintenance', self.advanced.header: 'Advanced Settings'}
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
                if not bonus and any(SequenceMatcher(None,token,word).ratio()>=.72
                        for token in tokens if len(token)>=3 for word in primary.split()):
                    bonus=1
                ranked.append((sum(matches)+bonus, index, key, terms))
        ranked.sort(key=lambda entry: (-entry[0], entry[1]))
        titles = {self.hud_on: 'Desktop-Overlay anzeigen', self.hud_size: 'Desktop-Overlay-Größe',
                  self.hud_opacity: 'Desktop-Overlay-Deckkraft',
                  self.restore_button: 'Standardwerte wiederherstellen',
                  self.accent_combo: 'Akzentfarbe', self.background_combo: 'Hintergrund',
                  self.motion_combo: 'Animationen', self.design_tiles[0]: 'Design',
                  self.close_to_tray: 'Beim Schließen minimieren', self.interval: 'Aktualisierungsintervall',
                  self.alert_toggle: 'Warnungen', self.eco_toggle: 'Ultra Eco',
                  self.render_combo: 'Grafik-Renderer', self._maintenance_card: 'Wartung',
                  self.advanced.header: 'Erweiterte Einstellungen'}
        for _score, index, key, terms in ranked[:7]:
            target = self._search_targets[index][2]
            item = QListWidgetItem(tr(titles.get(target, terms.split(' ')[0])) + '  ·  ' +
                                   tr(self.SEARCH_CATEGORIES[key]))
            item.setData(Qt.UserRole, index)
            self.search_results.addItem(item)
        self.search_results.setFixedHeight(min(156, 31 * self.search_results.count() + 7))
        self.search_results.setVisible(bool(self.search_results.count()) and
                                       self.search_overlay.expanded)
        self.search_overlay.suggestions_changed()
        # Navigate only when the leading match is distinct; keep typing in the
        # search field and wait briefly so successive prefixes do not jerk it.
        # Prefixes such as MiniH/MiniHU tie across show/layout/opacity. These
        # are one subject, so predict its first control instead of suppressing
        # navigation. Keep genuinely different subjects ambiguous.
        leading = [entry for entry in ranked if entry[0] == ranked[0][0]] if ranked else []
        subjects = {(entry[2], self._search_normalize(entry[3].split(' ')[0]))
                    for entry in leading}
        distinct = bool(leading) and len(subjects) == 1
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
        changes = design_catalog.defaults() if section=='appearance' else {key: self.DEFAULTS[key] for key in keys}
        if not settings.set_many(changes):
            return
        if section == 'appearance':
            self._select_without_signal(self.accent_combo, self.DEFAULTS['accent'])
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

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_restore_button()

    def _refresh_restore_button(self):
        values = settings.get_many(self.DEFAULTS)
        for section, keys in self.SECTION_DEFAULTS.items():
            button = self._reset_buttons.get(section)
            if button is not None:
                defaults=design_catalog.defaults() if section=='appearance' else self.DEFAULTS
                self._reset_reveals[section].setRevealed(any(settings.get(key,defaults[key]) != defaults[key] for key in keys))
        changed=(any(values[key] != default for key, default in self.DEFAULTS.items()) or
                 any(settings.get(key) for key in ('custom_accents','custom_backgrounds','dashboard_order',
                     'dashboard_hidden','dashboard_layout','lang')))
        self._maintenance_card.setVisible(True)
        self.restore_reveal.setRevealed(True)
        self.restore_button.setEnabled(bool(changed))

    def restore_defaults(self):
        answer = QMessageBox.question(
            self, 'Vitalux',
            tr('Alle Einstellungen dieses Profils zurücksetzen und eigene Farben, Layouts, '
               'importierte Hintergrundbildkopien und den Vitalux-Cache löschen? '
               'Design, Sprache, Warnwerte und Grafik-Renderer werden auf Standard gesetzt. '
               'Originalbilder und das andere Updateprofil bleiben erhalten. '
               'Spielberichte und Launcher-Verbindungen bleiben erhalten; Overlay-Profile werden zurückgesetzt. Vitalux startet anschließend neu und zeigt die Anleitung.'),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        from . import profiles
        def commit():
            try:
                return profiles.reset_preferences(settings.PATH)
            except OSError as exc:
                QMessageBox.warning(self, 'Vitalux',
                    tr('Zurücksetzen konnte nicht vollständig abgeschlossen werden:')+' '+str(exc))
                return False
        self._restart_after_reset(commit)

    def change_interval(self, *_):
        if eco.enabled():
            return
        val = self.interval.currentData()
        if val:
            self._set_preference('interval', int(val))
            self.window.set_interval(int(val))
