"""Apply appearance changes without rebuilding live pages or sensor workers."""
from PySide6.QtCore import QEventLoop
from PySide6.QtWidgets import QApplication,QGraphicsDropShadowEffect,QScrollArea,QWidget
from . import settings,theme,eco,motion
from .brand import app_icon,sync_installed_icon
from .wallpaper_accents import resolve_accent
from .widgets import Gauge
from .charts import ChartPanel
from .glass import GlassSurface
from .games_page import GamesPage


class WindowAppearance:
    @staticmethod
    def _is_scrolling_card(widget):
        """Qt drop shadows require expensive offscreen redraws on each scroll."""
        parent = widget.parentWidget()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                return True
            parent = parent.parentWidget()
        return False


    @staticmethod
    def _appearance_signature():
        return tuple(settings.get_many(dict(theme=theme.DEFAULT_THEME, accent='#4f8cff',
            background_style='theme_default', custom_background_selected='',
            custom_background_fit='cover', ultra_eco=False)).values())


    def apply_appearance(self, *, before=None):
        """Restyle in-place; keep selected page, benchmark worker and scroll intact."""
        if self._sidebar_motion is not None:
            self._sidebar_finish()
        from . import design_catalog
        design_catalog.remember()
        next_key = self._appearance_signature()
        if (self.isVisible() and not self.isMinimized() and motion.duration(300)
                and getattr(self, '_appearance_key', next_key) != next_key):
            if before is None:before = self.grab()
        else:before=None
        overlay = getattr(self, '_appearance_overlay', None)
        transition = None
        changed = getattr(self, '_appearance_key', next_key) != next_key
        if before is not None:
            from .appearance_transition import AppearanceTransition
            # Cover the visible window BEFORE any material/layout mutation.
            # This child of MainWindow is deliberately outside the scene, so
            # the destination scene can be captured without hiding the cover.
            transition = AppearanceTransition(self, before, before)
            self._appearance_overlay = transition
            transition.show()
            transition.raise_()
            def clear_overlay():
                if self._appearance_overlay is transition:
                    self._appearance_overlay = None
            transition.finished.connect(clear_overlay)
        if overlay is not None and (changed or not motion.duration(300) or not self.isVisible()):
            overlay.finish()
            if transition is None:self._appearance_overlay = None
        theme.set_mode(eco.theme_name())
        user_accent = settings.get('accent', '#4f8cff')
        theme.set_accent('#4f8cff' if eco.enabled() else resolve_accent(user_accent, self.distro['color']))
        stylesheet = theme.stylesheet()
        if QApplication.instance().styleSheet() != stylesheet:
            QApplication.instance().setStyleSheet(stylesheet)
        self.design_shell.sync()
        self.brand_mark.sync_theme()
        self.pulse_core.sync_theme()
        current_icon = app_icon()
        QApplication.instance().setWindowIcon(current_icon)
        self.setWindowIcon(current_icon)
        if not self._tray_glow.active:
            self._tray.setIcon(current_icon)
        self._sync_glow()  # Stop/restart all logo, sidebar and tray pulses.
        self._tray_glow.refresh()
        self.refresh_mini_hud()
        sync_installed_icon()
        minimal = theme.mode() == 'minimal'
        self.centralWidget().set_low_power(minimal)
        # _build may call apply_appearance before Sampler has been created.
        if hasattr(self, 'sampler'):
            self.set_interval(eco.interval())
        # Disabling graphics effects (rather than removing them) retains the
        # original glass shadows when switching back to Glass/Dark/Light.
        for card in self.findChildren(GlassSurface):
            fx = card.graphicsEffect()
            if isinstance(fx, QGraphicsDropShadowEffect):
                fx.setEnabled(not minimal and not self._is_scrolling_card(card))
        for gauge in self.findChildren(Gauge):
            if minimal:
                gauge._animate.stop()
                gauge._render_value = gauge.value
        for nav in self.nav_buttons:
            nav._sync_notice_animation()
        for graph in self.findChildren(ChartPanel):
            graph.retheme()
        for _,page in self.pages:
            if isinstance(page,GamesPage):page.retranslate()
        disk = next((p for name, p in self.pages if name == 'Laufwerke'), None)
        if disk is not None and hasattr(disk, 'refresh_appearance'):
            disk.refresh_appearance()
        # Keep the linked credit in sync with the active theme accent.
        info_page = next((page for title, page in self.pages if title == 'Info'), None)
        if info_page is not None:
            info_page.support_credit.retranslate()
            info_page.author_credit.retranslate()
        # QPainter-based glass/rings/navigation read colors directly from theme.
        self.centralWidget().update()
        for widget in self.centralWidget().findChildren(QWidget):
            widget.update()
        pref = next((page for title, page in self.pages if title == 'Einstellungen'), None)
        if pref is not None and hasattr(pref, 'refresh_appearance'):
            pref.refresh_appearance()
        self._appearance_key = next_key
        if transition is not None:
            self.layout().activate()
            scene = self.centralWidget()
            # Deferred Qt layout changes settle under the frozen source frame.
            QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
            self.layout().activate()
            if hasattr(scene, 'finish_background_frame'):
                scene.finish_background_frame()
            if self._appearance_overlay is transition:
                transition.after = scene.grab()
                transition.start()
