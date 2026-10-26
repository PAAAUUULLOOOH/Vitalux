"""Editable warning thresholds with native validation and soft controls."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QSizePolicy


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
