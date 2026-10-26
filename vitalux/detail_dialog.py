"""Explicit, selectable details for information that must not depend on hover."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QHBoxLayout, QApplication
from PySide6.QtCore import Qt
from .ui_locale import QPushButton
from .i18n import tr


def show_details(parent, title, text):
    dialog = QDialog(parent.window())
    dialog.setAttribute(Qt.WA_DeleteOnClose)
    dialog.setWindowTitle(tr(title))
    dialog.resize(650, 380)
    layout = QVBoxLayout(dialog)
    content = QPlainTextEdit()
    content.setReadOnly(True)
    content.setPlainText(str(text))
    layout.addWidget(content)
    actions = QHBoxLayout()
    copy = QPushButton('Kopieren')
    copy.clicked.connect(lambda: QApplication.clipboard().setText(content.toPlainText()))
    actions.addWidget(copy)
    actions.addStretch()
    close = QPushButton('Schließen')
    close.clicked.connect(dialog.accept)
    actions.addWidget(close)
    layout.addLayout(actions)
    dialog.open()
    return dialog
