"""Real release-note overflow, resizing and history selection without installs."""
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from vitalux import i18n, settings, theme
from vitalux.pages_extra import UpdatePage
from vitalux.update_manager import UpdateManager


app = QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory(prefix='vitalux-changelog-view-') as folder, patch.object(
        settings, 'PATH', str(Path(folder) / 'settings.json')):
    host = QWidget()
    host.resize(800, 1000)
    layout = QVBoxLayout(host)
    manager = UpdateManager()
    manager._timer.stop()
    page = UpdatePage(manager)
    layout.addWidget(page)
    host.show()
    QTest.qWait(100)
    try:
        # Installation controls and version selection are never inside the text.
        view = page.changelog_scroll
        assert not view.isAncestorOf(page.history_combo)
        assert not view.isAncestorOf(page.install_button)
        assert not view.isAncestorOf(page.progress_bar)
        page._history = {'0.9.6.2': 'One short change.',
                         '0.9.6.1': '\n'.join(f'Change {i}: ' + 'Useful release detail. ' * 5
                                              for i in range(60))}
        page.history_combo.blockSignals(True)
        page.history_combo.clear()
        for version in page._history:
            page.history_combo.addItem(version, version)
        page.history_combo.blockSignals(False)
        page._show_history()
        QTest.qWait(80)
        assert view.verticalScrollBar().maximum() == 0
        assert not view.verticalScrollBar().isVisible()
        assert view.height() < 100

        page.history_combo.setCurrentIndex(1)
        QTest.qWait(80)
        assert view.verticalScrollBar().isVisible()
        assert view.verticalScrollBar().maximum() > 0
        assert view.height() <= 350
        bar = view.verticalScrollBar()
        bar.setValue(bar.maximum())
        assert bar.value() > 0
        assert 'Change 59:' in page.changelog_details.text()
        page._show_history()  # An unchanged status refresh must not jump to top.
        QTest.qWait(80)
        assert bar.value() > 0

        host.resize(800, 760)  # Height-only resize must update the text area too.
        QTest.qWait(80)
        assert view.height() < 350
        for language in ('en', 'de'):
            i18n.set_lang(language)
            page._show_history()
            QTest.qWait(80)
            assert bar.value() == 0
            bar.setValue(bar.maximum())
        for mode in ('glass', 'obsidian_gold', 'quantum_core'):
            theme.set_mode(mode)
            app.setStyleSheet(theme.stylesheet())
            QTest.qWait(80)
            assert view.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded
            assert view.verticalScrollBar().isVisible()
        page.history_combo.setCurrentIndex(0)
        QTest.qWait(80)
        assert bar.value() == 0 and bar.maximum() == 0
        assert not bar.isVisible()
        assert not view.grab().isNull()
    finally:
        host.close()
        manager.shutdown()

print('Bounded notes: overflow-only scrollbar, full text, resize, stable position, languages and version reset PASS')
