"""Small native Qt overlay for settings-only search, pinned above scrolling content."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QHBoxLayout, QToolButton, QVBoxLayout, QWidget
from . import theme
from .i18n import tr


class _SearchIcon(QToolButton):
    """Antialiased accent-color icon, matching the current Vitalux theme."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tr('Einstellungen durchsuchen'))
        self.setObjectName('settingsFloatingMagnifier')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        c = QColor(theme.accent())
        p = QPen(c, 2.4)
        p.setCapStyle(Qt.RoundCap)
        painter.setPen(p)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(10, 9, 14, 14))
        painter.drawLine(QPointF(22, 22), QPointF(30, 30))
        painter.end()


class FloatingSettingsSearch(QWidget):
    """Theme-aware centered search. It never participates in page scrolling."""

    COLLAPSED = 0
    DEFAULT_WIDTH = 212
    MAX_WIDTH = 500

    def __init__(self, field, suggestions, parent=None):
        super().__init__(parent)
        self._host = parent
        self._expanded = False
        self._closing = False
        self._width = 0
        self.setObjectName('settingsFloatingSearch')
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.icon = _SearchIcon(self)
        self.field = field
        self.suggestions = suggestions
        self.field.setMinimumWidth(0)
        self.field.setMaximumWidth(0)
        self.field.hide()
        self.suggestions.hide()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(5)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(5)
        row.addWidget(self.icon, 0, Qt.AlignVCenter)
        row.addWidget(self.field, 0, Qt.AlignVCenter)
        root.addLayout(row)
        root.addWidget(self.suggestions)
        self.setFixedSize(40, 40)

        self.animation = QVariantAnimation(self)
        self.animation.setDuration(280)
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
        if self._host is not viewport:
            if self._host is not None:
                self._host.removeEventFilter(self)
            self.setParent(viewport)
            self._host = viewport
            viewport.installEventFilter(self)
            app = QApplication.instance()
            if app is not None:
                app.installEventFilter(self)
        self._position()
        self.show()
        self.raise_()

    def refresh_theme(self):
        card = QColor(theme.CARD)
        line = QColor(theme.BORDER)
        text = QColor(theme.TEXT)
        accent = QColor(theme.accent())
        alpha = 187 if theme.mode() in ('glass', 'black_glass', 'black_glass_gold', 'holographic') else 242
        bg = f'rgba({card.red()}, {card.green()}, {card.blue()}, {alpha})'
        outline = f'rgba({line.red()}, {line.green()}, {line.blue()}, 190)'
        foreground = text.name()
        selection = accent.name()
        self.field.setStyleSheet(
            'QLineEdit#settingsSearch {'
            f'background: {bg}; color: {foreground}; border: 1px solid {outline};'
            f'border-radius: 18px; padding: 6px 14px; selection-background-color: {selection};'
            '}'
        )
        self.field.setFixedHeight(38)
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
        if obj is self._host and kind == QEvent.Resize:
            self._position()
        elif self._expanded and kind == QEvent.MouseButtonPress and isinstance(obj, QWidget):
            if obj is not self and not self.isAncestorOf(obj):
                self.close_search()
        elif self._expanded and kind == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self.close_search()
            return True
        return super().eventFilter(obj, event)

    def _position(self):
        if self._host is not None:
            self.move(max(0, (self._host.width() - self.width()) // 2), 12)
            self.raise_()

    def _sync_geometry(self):
        result_height = (self.suggestions.height() + 5
                         if self._expanded and not self.suggestions.isHidden() else 0)
        self.setFixedSize(40 + (5 + self._width if self._width > 0 else 0),
                          40 + result_height)
        self._position()

    def _on_frame(self, value):
        self._width = max(0, int(value))
        self.field.setFixedWidth(self._width)
        self._sync_geometry()

    def _animate(self, end):
        self.animation.stop()
        self.animation.setStartValue(self._width)
        self.animation.setEndValue(int(end))
        if int(end) == self._width:
            self._finished()
        else:
            self.animation.start()

    def _finished(self):
        if self._closing and self._width == 0:
            self.field.clear()
            self.field.hide()
            self.suggestions.hide()
            self._closing = False
            self._sync_geometry()

    def _wanted_width(self):
        advance = self.field.fontMetrics().horizontalAdvance(self.field.text())
        return max(self.DEFAULT_WIDTH, min(self.MAX_WIDTH, advance + 96))

    def _typed(self, _):
        self.idle_timer.start()
        self._animate(self._wanted_width())

    def _text_changed(self, _):
        if self._expanded:
            self._sync_geometry()

    def suggestions_changed(self):
        """Call after the result list changes; keep the overlay centered."""
        if self._expanded:
            self._sync_geometry()

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
        self.suggestions.hide()
        self.field.clearFocus()
        self._animate(0)

    @property
    def expanded(self):
        return self._expanded
