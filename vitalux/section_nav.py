"""Shared compact vertical navigation for Settings and Diagnostics."""
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QSizePolicy
from .ui_locale import QPushButton
from .i18n import tr


class CurrentSizeStack(QStackedWidget):
    """Visible section alone determines the page size in its outer scroll area."""

    def sizeHint(self):
        page = self.currentWidget()
        return page.sizeHint() if page is not None else QSize(480, 300)

    def minimumSizeHint(self):
        return QSize(340, 160)

    def setCurrentIndex(self, index):
        super().setCurrentIndex(index)
        self.updateGeometry()
        if self.parentWidget():
            self.parentWidget().updateGeometry()


class SectionNav(QWidget):
    changed = Signal(str)

    def __init__(self, sections, parent=None):
        super().__init__(parent)
        self.keys = [key for key, _title in sections]
        self.labels = {key: title for key, title in sections}
        self.buttons = {}
        self.pages = {}
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)
        rail = QWidget(self)
        rail.setObjectName('subCategoryRail')
        rail.setFixedWidth(183)
        rail_lay = QVBoxLayout(rail)
        rail_lay.setContentsMargins(0, 4, 0, 4)
        rail_lay.setSpacing(5)
        self.stack = CurrentSizeStack(self)
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        for key, title in sections:
            btn = QPushButton(tr(title).replace('&', '&&'))
            btn.setCheckable(True)
            btn.setObjectName('subCategoryButton')
            btn.setProperty('sectionKey', key)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self.select(k))
            btn.setMinimumHeight(38)
            rail_lay.addWidget(btn)
            self.buttons[key] = btn
            page = QWidget(self.stack)
            layout = QVBoxLayout(page)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(14)
            layout.addStretch(1)  # Preserve natural card heights.
            self.pages[key] = layout
            self.stack.addWidget(page)
        rail_lay.addStretch(1)
        root.addWidget(rail, 0, Qt.AlignTop)
        root.addWidget(self.stack, 1, Qt.AlignTop)
        self.select(self.keys[0])

    def select(self, key):
        if key not in self.buttons:
            return
        for candidate, btn in self.buttons.items():
            btn.setChecked(candidate == key)
        self.stack.setCurrentIndex(self.keys.index(key))
        self.changed.emit(key)

    def current_key(self):
        return self.keys[self.stack.currentIndex()]

    def add(self, key, widget):
        self.pages[key].insertWidget(self.pages[key].count() - 1, widget, 0, Qt.AlignTop)

    def add_layout(self, key, layout):
        self.pages[key].insertLayout(self.pages[key].count() - 1, layout)

    def retranslate(self):
        for key, title in self.labels.items():
            self.buttons[key].setText(tr(title).replace('&', '&&'))
