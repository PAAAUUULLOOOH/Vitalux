"""Small native Qt overlay for settings-only search, pinned above scrolling content."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QPointF, QRectF, Qt, QTimer, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect, QToolButton, QWidget
from . import theme, motion
from .i18n import tr


class _SearchIcon(QToolButton):
    """Antialiased accent-color icon, matching the current Vitalux theme."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tr('Einstellungen durchsuchen'))
        self.setObjectName('settingsFloatingMagnifier')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        c = QColor(theme.MUTED)
        c.setAlpha(176)
        p = QPen(c, 1.6)
        p.setCapStyle(Qt.RoundCap)
        painter.setPen(p)
        painter.setBrush(Qt.NoBrush)
        x,y=self.width()/2,self.height()/2
        painter.drawEllipse(QRectF(x-6.5,y-6.5,9,9))
        painter.drawLine(QPointF(x+1,y+1), QPointF(x+6.5,y+6.5))
        painter.end()


class FloatingSettingsSearch(QWidget):
    """Theme-aware centered search. It never participates in page scrolling."""

    DEFAULT_WIDTH = 235
    MAX_WIDTH = 500

    def __init__(self, field, suggestions, parent=None):
        super().__init__(parent)
        self._host = parent
        self._page = parent
        self._header_mode = False
        self._viewport = None
        self._expanded = False
        self._closing = False
        self._width = 0
        self._result_height = 0
        self._from = (0, 0.0, 0)
        self._to = (0, 0.0, 0)
        self.home_icon = None
        self.setObjectName('settingsFloatingSearch')
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.icon = _SearchIcon(self)
        self.field = field
        self.suggestions = suggestions
        self.field.setMinimumWidth(0)
        # A permanent maximum of zero silently defeats the absolute geometry
        # animation: QWidget clamps setGeometry() to its maximumWidth.
        self.field.setMaximumWidth(self.MAX_WIDTH)
        self.field.hide()
        self.suggestions.hide()

        # Absolute child geometry avoids repeated Qt layout invalidation on every
        # animation frame (which otherwise makes transitions visually jump).
        self.field.setParent(self)
        self.suggestions.setParent(self)
        self.icon.move(0, 0)
        self.field.move(37, 0)
        self.field.setFixedHeight(32)
        self.setFixedSize(32, 32)
        self.hide()

        self._opacity = QGraphicsOpacityEffect(self)
        self._content = QWidget(self)
        self._content.setObjectName('settingsSearchContent')
        self._content.setAttribute(Qt.WA_TranslucentBackground, True)
        self.field.setParent(self._content)
        self.suggestions.setParent(self._content)
        self._content.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0)
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(340)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.valueChanged.connect(self._on_frame)
        self.animation.finished.connect(self._finished)
        self.idle_timer = QTimer(self)
        self.idle_timer.setSingleShot(True)
        self.idle_timer.setInterval(5000)
        self.idle_timer.timeout.connect(self.close_search)
        self.icon.clicked.connect(self.toggle)
        self.field.textEdited.connect(self._typed)
        self.field.textChanged.connect(self._text_changed)
        self.refresh_theme()

    def install_on(self, scroll):
        """Put the overlay in the scroll viewport, not in the scrolling widget."""
        viewport = scroll.viewport()
        window=getattr(self._page,'window',None)
        header_mode=(hasattr(window,'window_frame') and window.window_frame.scene is not None
                     and hasattr(window,'design_shell'))
        host=window if header_mode else viewport
        parent=window.window_frame.scene if header_mode else viewport
        if self._host is not host:
            if self._host is not None:
                self._host.removeEventFilter(self)
            self.setParent(parent)
            self._host = host
            host.installEventFilter(self)
            app = QApplication.instance()
            if app is not None:
                app.installEventFilter(self)
        self._viewport=viewport
        self._header_mode=header_mode
        if header_mode:
            self.icon.setFixedSize(34,28)
            if self.home_icon is not None:
                self.home_icon.parentWidget().hide()
                self.home_icon=None
            self._page.search_home=self.icon
            self._page.installEventFilter(self)
            self.refresh_theme()
        self._position()
        if self._expanded or (header_mode and self._page.isVisible()):
            self.show()
            self.raise_()

    def refresh_theme(self):
        card = QColor(theme.CARD)
        line = QColor(theme.BORDER)
        text = QColor(theme.TEXT)
        accent = QColor(theme.accent())
        alpha = 187 if theme.mode() in ('glass',) else 242
        bg = f'rgba({card.red()}, {card.green()}, {card.blue()}, {alpha})'
        outline = f'rgba({line.red()}, {line.green()}, {line.blue()}, 190)'
        foreground = text.name()
        selection = accent.name()
        inset='padding-left: 42px;' if self._header_mode else ''
        height=self.icon.height()
        self.field.setStyleSheet(
            'QLineEdit#settingsSearch {'
            f'background: {bg}; color: {foreground}; border: 1px solid {outline};'
            f'border-radius: {height/2:g}px; padding: 3px 11px; {inset} selection-background-color: {selection};'
            '}'
        )
        self.field.setFixedHeight(height)
        self.suggestions.setStyleSheet(
            'QListWidget#settingsSearchResults {'
            f'background: {bg}; color: {foreground}; border: 1px solid {outline};'
            'border-radius: 12px; padding: 3px;'
            '}'
        )
        self.icon.setToolTip(tr('Einstellungen durchsuchen'))
        self.icon.update()

    def eventFilter(self, obj, event):
        kind = event.type()
        if self._header_mode and obj is self._page:
            if kind==QEvent.Show:
                self._sync_geometry();self.show();self.raise_()
            elif kind==QEvent.Hide:
                self.animation.stop();self._expanded=False;self._closing=True
                self._to=(0,0.0,0);self._finished();self.hide()
        if self._expanded and kind == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.close_search()
            return True
        if obj is self._host and kind == QEvent.Resize:
            if self._expanded:
                self._animate(self._wanted_width())
            else:
                self._position()
        elif self._expanded and kind in (QEvent.MouseButtonPress, QEvent.KeyPress):
            if isinstance(obj, QWidget) and (obj is self or self.isAncestorOf(obj)):
                self.idle_timer.start()
            elif kind == QEvent.MouseButtonPress:
                self.close_search()
        return super().eventFilter(obj, event)

    def _position(self):
        if self._host is not None:
            if self._header_mode:
                shell=self._host.design_shell
                anchor=shell.bar if not shell.header.isHidden() else self._host.window_frame.titlebar
                top=anchor.mapTo(self.parentWidget(),QPoint()).y()
                self.move((self._host.width()-self.width())//2,top+(anchor.height()-self.icon.height())//2)
            else:
                inset=self._host.property('vitaluxTopInset') or 0
                self.move(max(0, (self._host.width()-self.width())//2), 12+inset)
            self.raise_()

    def _sync_geometry(self):
        icon_width,height=self.icon.width(),self.icon.height()
        width = icon_width + (5+self._width if self._width > 0 else 0)
        self.setFixedSize(width, height+self._result_height)
        self.icon.move(0, 0)
        content_width=width if self._header_mode else self._width
        self._content.setGeometry(0 if self._header_mode else 37,
                                  0 if self._header_mode else round((1-self._opacity.opacity())*5),
                                  content_width, height+self._result_height)
        self.field.setGeometry(0, 0, content_width, height)
        self.suggestions.setGeometry(0, height+5, content_width, self.suggestions.height())
        self.icon.raise_()
        self._position()

    def _on_frame(self, progress):
        amount = float(progress)
        self._width = max(0, round(self._from[0]+(self._to[0]-self._from[0])*amount))
        self._opacity.setOpacity(self._from[1]+(self._to[1]-self._from[1])*amount)
        self._result_height = max(0, round(self._from[2]+(self._to[2]-self._from[2])*amount))
        self._sync_geometry()

    def _animate(self, end):
        self.animation.stop()
        self._from = (self._width, self._opacity.opacity(), self._result_height)
        result_height = self.suggestions.height()+5 if self._expanded and not self.suggestions.isHidden() else 0
        self._to = (int(end), 1.0 if self._expanded else 0.0, result_height)
        duration = motion.timing('search')
        if not duration or self._from == self._to:
            self._on_frame(1.0)
            self._finished()
            return
        self.animation.setDuration(duration)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

    def _finished(self):
        # Width, opacity and results finish together. Never hide midway through
        # a collapse or after a close was interrupted by another open action.
        self._on_frame(1.0)
        if self._closing and not self._expanded:
            self._closing = False
            self.field.clear()
            self.field.hide()
            self.suggestions.hide()
            self.setVisible(self._header_mode and self._page.isVisible())
            if self.home_icon is not None:
                self.home_icon.show()

    def _wanted_width(self):
        metrics = self.field.fontMetrics()
        if self._header_mode:
            window=self._host;shell=window.design_shell;center=window.width()/2
            left,right=24,window.width()-24
            candidates=([shell.brand,window.lang_host,window.window_frame.titlebar]
                        if not shell.header.isHidden() else [window.window_frame.buttons['minimize']])
            for widget in candidates:
                if not widget.isVisible():continue
                position=widget.mapTo(window,QPoint())
                if position.x()+widget.width()/2<center:left=max(left,position.x()+widget.width()+12)
                else:right=min(right,position.x()-12)
            available=max(self.icon.width(),round(2*min(center-left,right-center)))
            full=min(self.MAX_WIDTH,available,max(self.DEFAULT_WIDTH,
                metrics.horizontalAdvance(self.field.placeholderText())+62,
                metrics.horizontalAdvance(self.field.text())+66))
            return max(0,full-self.icon.width()-5)
        # Never truncate the complete placeholder to 'Einstellung…' on opening.
        # Reserve room for the caret, borders and the search field's padding.
        placeholder = metrics.horizontalAdvance(self.field.placeholderText()) + 36
        typed = metrics.horizontalAdvance(self.field.text()) + 56
        available = max(100, self._host.width()-61) if self._host else self.MAX_WIDTH
        return min(self.MAX_WIDTH, available, max(self.DEFAULT_WIDTH, placeholder, typed))

    def _typed(self, _):
        self.idle_timer.start()

    def _text_changed(self, _):
        if self._expanded:
            self.idle_timer.start()
            self._animate(self._wanted_width())

    def suggestions_changed(self):
        """Call after the result list changes; keep the overlay centered."""
        if self._expanded:
            self._animate(self._wanted_width())

    def result_chosen(self):
        """Keep the query visible for five seconds after navigating to a match."""
        self.suggestions.hide()
        self.idle_timer.start()
        self._animate(self._wanted_width())

    def toggle(self):
        if self._expanded:
            self.close_search()
        else:
            self.open_search()

    def open_search(self):
        if self._expanded:
            self.field.setFocus(Qt.ShortcutFocusReason)
            self.idle_timer.start()
            return
        self._expanded = True
        self._closing = False
        if self.home_icon is not None:
            self.home_icon.hide()
        self.show()
        self.field.show()
        self.field.setFocus(Qt.ShortcutFocusReason)
        self.idle_timer.start()
        self.refresh_theme()
        self._animate(self._wanted_width())
        self.raise_()

    def close_search(self):
        if not self._expanded:
            return
        self._expanded = False
        self._closing = True
        self.idle_timer.stop()
        self.field.clearFocus()
        self._animate(0)

    @property
    def expanded(self):
        return self._expanded
