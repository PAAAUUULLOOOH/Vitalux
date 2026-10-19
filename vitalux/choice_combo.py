"""Explain a fixed design inside its dropdown while keeping choices unavailable."""
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (QLabel, QMenu, QStyle, QStyleOptionComboBox,
                              QStylePainter, QWidgetAction)
from .ui_locale import QComboBox
from . import theme
from .i18n import tr


class ChoiceComboBox(QComboBox):
    def __init__(self, parent=None):
        self._lock_reason = ''
        self._lock_title = ''
        self._locked_menu = None
        super().__init__(parent)

    def isLocked(self):
        return bool(self._lock_reason)

    def setLocked(self, reason='', title=''):
        self._lock_reason, self._lock_title = reason, title
        self.setEnabled(True)  # The explanation remains accessible by keyboard.
        style = ('QComboBox { color: #8b8e95; border-color: #54565c; '
                 'background: rgba(92,96,104,35); }') if reason else ''
        if self.styleSheet() != style:
            self.setStyleSheet(style)
        self.update()

    def paintEvent(self, event):
        if not self.isLocked():
            return super().paintEvent(event)
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = tr(self._lock_title)
        painter.drawComplexControl(QStyle.CC_ComboBox, option)
        painter.drawControl(QStyle.CE_ComboBoxLabel, option)

    def showPopup(self):
        if not self.isLocked():
            return super().showPopup()
        self.hidePopup()
        # Do not inherit the combo's privately owned Fusion style. Native menus
        # can outlive that style during shutdown and dereference freed memory.
        menu = QMenu(self.window())
        menu.setObjectName('fixedDesignChoices')
        menu.setStyleSheet(f'QMenu {{ background: {theme.CARD}; color: {theme.TEXT}; '
            f'border: 1px solid {theme.BORDER}; padding: 6px; }} '
            'QMenu::item { padding: 5px 12px; } QMenu::item:disabled { color: #8b8e95; }')
        message = QLabel(tr(self._lock_reason), menu)
        message.setObjectName('choiceLockMessage')
        message.setWordWrap(True)
        message.setFixedWidth(310)
        message.setContentsMargins(12, 8, 12, 10)
        message.setStyleSheet(f'color: {theme.MUTED}; background: transparent;')
        header = QWidgetAction(menu)
        header.setDefaultWidget(message)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()
        for index in range(self.count()):
            action = menu.addAction(self.itemText(index))
            action.setEnabled(False)
        self._locked_menu = menu
        menu.popup(self.mapToGlobal(QPoint(0, self.height()+3)))

    def hidePopup(self):
        if self._locked_menu is not None:
            self._locked_menu.close()
            self._locked_menu.deleteLater()
            self._locked_menu = None
        super().hidePopup()

    def keyPressEvent(self, event):
        if self.isLocked() and event.key() not in (Qt.Key_Tab, Qt.Key_Backtab):
            if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Down):
                self.showPopup()
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        if self.isLocked():
            event.ignore()
        else:
            super().wheelEvent(event)
