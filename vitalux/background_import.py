"""Cancellable background copies; only the GUI commits imported preferences."""
from PySide6.QtCore import QThread, Signal
from . import user_background


class BackgroundImport(QThread):
    completed = Signal(object, object)

    def __init__(self, names, parent):
        super().__init__(parent)
        self.names = names
        self.destination = user_background.folder()

    def run(self):
        imported, failures = [], []
        for name in self.names:
            if self.isInterruptionRequested():break
            try:
                imported.append(user_background.import_image(
                    name, destination=self.destination, cancelled=self.isInterruptionRequested))
            except InterruptedError:break
            except (OSError, ValueError) as exc:failures.append(f'{name}: {exc}')
        if self.isInterruptionRequested():
            for row in imported:(self.destination/row['file']).unlink(missing_ok=True)
        else:self.completed.emit(imported, failures)
