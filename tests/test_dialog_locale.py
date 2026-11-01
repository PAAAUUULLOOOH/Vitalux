"""Dialogs follow Vitalux's selected language, not Qt's host locale."""
import os
import sys
import runpy
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.getcwd())

from PySide6.QtCore import QTimer,Qt,QPoint
from PySide6.QtWidgets import QApplication,QVBoxLayout,QLabel
from PySide6.QtGui import QColor
from vitalux.i18n import set_lang
from vitalux.ui_locale import QMessageBox,QDialog,QInputDialog,QColorDialog,QFileDialog
from vitalux import theme

app = QApplication.instance() or QApplication([])
prompt = ('Alle Einstellungen dieses Profils zurücksetzen und eigene Farben, Layouts, '
          'importierte Hintergrundbildkopien und den Vitalux-Cache löschen? '
          'Design, Sprache, Warnwerte und Grafik-Renderer werden auf Standard gesetzt. '
          'Originalbilder und das andere Updateprofil bleiben erhalten. '
          'Vitalux startet anschließend neu und zeigt die Anleitung.')

for code, positive, negative in (('de', 'Ja', 'Nein'),
                                  ('en', 'Yes', 'No')):
    set_lang(code)
    seen = {}
    def inspect_and_cancel():
        dialog = app.activeModalWidget()
        assert dialog is not None, 'The confirmation popup is not modal'
        yes = dialog.button(QMessageBox.Yes)
        no = dialog.button(QMessageBox.No)
        seen['buttons'] = (yes.text(), no.text())
        seen['message'] = dialog.text()
        no.click()

    QTimer.singleShot(0, inspect_and_cancel)
    # Fail closed rather than block a release indefinitely on a headless Qt
    # platform if native modal focus/translation behavior changes.
    def watchdog():
        dialog = app.activeModalWidget()
        if dialog is not None:
            dialog.reject()
    QTimer.singleShot(2000, watchdog)
    result = QMessageBox.question(None, 'Vitalux', prompt,
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    assert result == QMessageBox.No, (code, result)
    assert seen['buttons'] == (positive, negative), (code, seen)
    assert seen['message'].startswith('Reset all preferences' if code == 'en'
                                       else 'Alle Einstellungen'), (code, seen)
    first_run = runpy.run_path('packaging/appimage-first-run.py')
    dialog, install, portable = first_run['create_dialog']()
    assert install.text() == ('Install now' if code == 'en' else 'Jetzt installieren')
    assert portable.text() == ('Run once' if code == 'en' else 'Nur einmal starten')
    assert dialog.informativeText().startswith('Vitalux will' if code == 'en' else 'Vitalux wird')
    dialog.close()

for design,_ in theme.CHOICES:
    theme.set_mode(design);app.setStyleSheet(theme.stylesheet())
    dialog=QDialog();dialog.setWindowTitle('Vitalux');layout=QVBoxLayout(dialog)
    layout.addWidget(QLabel('Content'));dialog.resize(480,240);dialog.show();app.processEvents()
    assert dialog.windowFlags()&Qt.FramelessWindowHint,design
    assert dialog.testAttribute(Qt.WA_TranslucentBackground),design
    chrome=dialog._vitalux_dialog_frame
    assert layout.geometry().top()+layout.contentsMargins().top()>chrome.titlebar.geometry().bottom(),design
    assert dialog.grab().toImage().pixelColor(0,0).alpha()==0,design
    chrome.titlebar.close_button.click();assert not dialog.isVisible()
    dialog.deleteLater()

errors=[]
def interact(action):
    def ready():
        dialog=app.activeModalWidget()
        try:
            assert dialog is not None
            assert dialog.windowFlags()&Qt.FramelessWindowHint
            assert dialog._vitalux_dialog_frame.titlebar.isVisible()
            action(dialog)
        except BaseException as exc:
            errors.append(exc)
            if dialog is not None:dialog.reject()
    QTimer.singleShot(0,ready)

interact(lambda d:(d.setTextValue('custom'),d.accept()))
assert QInputDialog.getText(None,'Name','Name:',text='old')==('custom',True)
interact(lambda d:(d.setIntValue(8),d.accept()))
assert QInputDialog.getInt(None,'Value','Value:',3,1,10,1)==(8,True)
interact(lambda d:(d.setCurrentColor(QColor('#123456')),d.accept()))
assert QColorDialog.getColor().name()=='#123456'
interact(lambda d:d.reject())
assert not QColorDialog.getColor().isValid()
import tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as folder:
    target=Path(folder)/'image.png';target.write_bytes(b'file selection only')
    interact(lambda d:(d.selectFile(str(target)),d.accept()))
    assert QFileDialog.getOpenFileName(None,'Open',folder,'Images (*.png)')[0]==str(target)
    interact(lambda d:d.reject())
    assert QFileDialog.getSaveFileName(None,'Save',folder)==('','')
assert not errors,errors
set_lang('de')
print('DE/EN confirmations, rounded frameless dialogs across designs and modal file/color/input actions PASS')
