"""Appearance settings and live changes, shared with the settings page."""
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QInputDialog
from .ui_locale import QFileDialog, QMessageBox

from . import settings, theme, motion, user_background, wallpaper_accents, renderer, eco, design_capabilities, design_catalog
from .i18n import tr


class AppearancePreferences:
    def refresh_appearance(self):
        ultra = eco.enabled()
        for widget,key,default in ((self.accent_combo,'accent','design_default'),
                                   (self.background_combo,'background_style','theme_default'),
                                   (self.background_fit_combo,'custom_background_fit','cover')):
            self._select_without_signal(widget,settings.get(key,default))
        selected_image=settings.get('custom_background_selected','')
        self._select_without_signal(self.background_image_combo,selected_image)
        self.design_gallery_scroll.sync()
        self.settings_deck.sync()

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
        if not design_catalog.switch(key):
            return
        self.window.apply_appearance()
        self.refresh_appearance()

    def change_component_images(self,checked):
        settings.set('component_images',bool(checked))
        from .product_ui import ProductHeader
        for header in self.window.findChildren(ProductHeader):header.sync_preference()
        self._refresh_restore_button()

    def change_accent(self, val):
        if eco.enabled() or not self.accent_combo.isEnabled():
            return
        if not val or (wallpaper_accents.is_wallpaper_accent(val)
                       and not wallpaper_accents.available()):
            return
        if val == wallpaper_accents.AUTO:
            current = settings.get('accent', 'design_default')
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

    @classmethod
    def _read_custom_accents(cls):
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
                    and color.name() not in cls.PRESET_COLORS):
                result.append({'name': name, 'color': color.name()})
                seen.add(color.name())
        # Repair settings written by older releases, so the protected default
        # palette survives subsequent upgrades and application restarts.
        if saved != result:
            settings.set('custom_accents', result)
        return result

    def _sync_custom_accent_actions(self):
        from .design_capabilities import capabilities
        cap=capabilities(theme.mode())
        gold = not cap['accent'] or eco.enabled()
        custom_locked = not cap['custom_accent'] or eco.enabled()
        self.accent_combo.setLocked(
            ('Ultra Eco verwendet eine feste, einfache Farbpalette.' if eco.enabled() else
             'Dieses Design verwendet eine feste Farbpalette. Eigene Akzentfarben sind hier nicht verfügbar.') if gold else '',
            'Feste Designpalette')
        self.custom_accent_button.setEnabled(not custom_locked)
        self.edit_custom_accent_button.setEnabled(not custom_locked)
        self.remove_custom_accent_button.setEnabled(not custom_locked)
        for button in (self.custom_accent_button,self.edit_custom_accent_button,self.remove_custom_accent_button):
            button.setCursor(Qt.ArrowCursor if custom_locked else Qt.PointingHandCursor)
        # Stored custom colors follow the same capability as creating them.
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
        if not design_capabilities.capabilities(theme.mode())['custom_accent'] or eco.enabled():
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
        if not design_capabilities.capabilities(theme.mode())['custom_accent'] or eco.enabled():
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
        if not design_capabilities.capabilities(theme.mode())['custom_accent'] or eco.enabled():
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
        chosen = settings.get('accent', 'design_default')
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
             'Dieses Design hat einen festen Hintergrund. Wähle ein anderes Design, um eigene Bilder oder Hintergründe zu verwenden.') if locked else '',
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
        if style=='custom_image' and self.background_image_combo.currentData():
            settings.set('custom_background_selected',self.background_image_combo.currentData())
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
