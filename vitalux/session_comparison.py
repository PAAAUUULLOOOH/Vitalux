"""Compare recorded facts from two sessions of the same game."""
import math
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QVBoxLayout
from .ui_locale import QDialog
from .choice_combo import ChoiceComboBox
from .widgets import label
from .i18n import tr


def metrics(report):
    def valid(value):return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    fps = report.get('average_fps')
    return (fps, report.get('low_1'), report.get('low_01'),
            1000/fps if valid(fps) and fps > 0 else None,
            report.get('long_frame_ratio'))


class SessionComparison(QDialog):
    def __init__(self, rows, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('Sitzungen vergleichen'))
        self.resize(720, 450)
        self.rows = rows
        root = QVBoxLayout(self)
        title=label(rows[0].get('game_name', ''), 'bigName', wrap=True)
        title.setTextFormat(Qt.PlainText);root.addWidget(title)
        grid = QGridLayout();root.addLayout(grid)
        self.choices = [ChoiceComboBox(), ChoiceComboBox()]
        for column, choice in enumerate(self.choices, 1):
            choice.setAccessibleName(tr('Referenzsitzung' if column == 1 else 'Vergleichssitzung'))
            for row in rows:
                try:stamp = datetime.fromtimestamp(row['started']).strftime('%d.%m.%Y %H:%M')
                except (KeyError,TypeError,ValueError,OverflowError,OSError):stamp='–'
                choice.addItem(stamp+' · '+str(row.get('target_fps', 60))+' FPS', row['id'])
            choice.setCurrentIndex(1 if column == 1 else 0)
            grid.addWidget(choice, 0, column)
        grid.addWidget(label('Änderung', 'strong'), 0, 3)
        self.cells = []
        for index, title in enumerate(('Ø FPS', '1% Low', '0,1% Low', 'Ø Frametime', 'Anteil langer Frames'), 1):
            grid.addWidget(label(title, 'strong'), index, 0)
            cells = [label('–', 'strong') for _ in range(3)]
            for column, cell in enumerate(cells, 1):grid.addWidget(cell, index, column)
            self.cells.append(cells)
        self.note = label('', 'muted', wrap=True);root.addWidget(self.note)
        root.addWidget(label('Unterschiedliche Spielszenen, FPS-Limits und Einstellungen können den Vergleich beeinflussen.', 'muted', wrap=True))
        for choice in self.choices:choice.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def refresh(self, *_):
        a, b = (self.rows[choice.currentIndex()] for choice in self.choices)
        for index, (old, new) in enumerate(zip(metrics(a), metrics(b))):
            unit = ' ms' if index == 3 else ' %' if index == 4 else ' FPS'
            factor = 100 if index == 4 else 1
            valid = lambda x:isinstance(x, (int, float)) and not isinstance(x,bool) and math.isfinite(x)
            left, right, delta = self.cells[index]
            left.setText(f'{old*factor:.2f}'+unit if valid(old) else '–')
            right.setText(f'{new*factor:.2f}'+unit if valid(new) else '–')
            delta_unit=' pp' if index==4 else unit
            delta.setText(f'{(new-old)*factor:+.2f}'+delta_unit if valid(old) and valid(new) else '–')
        notes = []
        if a.get('target_fps') != b.get('target_fps'):
            notes.append(tr('Unterschiedliche FPS-Ziele: Bewertungen sind nicht direkt vergleichbar.'))
        if not a.get('complete') or not b.get('complete'):
            notes.append(tr('Mindestens eine Sitzung ist unvollständig.'))
        if a.get('id') == b.get('id'):notes.append(tr('Dieselbe Sitzung ist zweimal ausgewählt.'))
        self.note.setText('\n'.join(notes));self.note.setVisible(bool(notes))
