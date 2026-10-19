"""Erststartdialog fuer eine freiwillige AppImage-Desktopintegration."""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitalux import i18n, settings
from vitalux.i18n import tr


def create_dialog():
    from PySide6.QtWidgets import QMessageBox
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setWindowTitle('Vitalux – '+tr('Erster Start'))
    msg.setText(tr('Vitalux als Desktop-Anwendung installieren?'))
    msg.setInformativeText(tr(
        'Vitalux wird ohne Administratorrechte in deinem Benutzerordner abgelegt '
        'und ins Anwendungsmenü eingetragen. Alternativ kannst du es ohne '
        'Installation starten.'))
    install = msg.addButton(tr('Jetzt installieren'), QMessageBox.ButtonRole.AcceptRole)
    portable = msg.addButton(tr('Nur einmal starten'), QMessageBox.ButtonRole.RejectRole)
    msg.setDefaultButton(install)
    return msg, install, portable

def main():
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        i18n.set_lang(settings.get('lang') or ('de' if os.environ.get('LANG', '').lower().startswith('de') else 'en'))
        app = QApplication.instance() or QApplication([])
        if len(sys.argv) > 2 and sys.argv[1] == "--error":
            QMessageBox.critical(None, "Vitalux – Installation", sys.argv[2])
            return 0
        msg, install, portable = create_dialog()
        msg.exec()
        if msg.clickedButton() is install:
            return 0
        if msg.clickedButton() is portable:
            return 1
        return 2
    except Exception as exc:
        print(f"Vitalux: Erststartdialog fehlgeschlagen: {exc}", file=sys.stderr)
        return 80

if __name__ == "__main__":
    raise SystemExit(main())
