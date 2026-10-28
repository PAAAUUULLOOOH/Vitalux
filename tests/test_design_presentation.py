"""Shared content gutters, quiet passive cards and themed readable dialogs."""
import os, sys, tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication,QVBoxLayout
from vitalux import settings,theme
from vitalux.widgets import Card,label
from vitalux.ui_locale import QDialog,QPushButton,QComboBox

app=QApplication([]);app.setQuitOnLastWindowClosed(False)
with tempfile.TemporaryDirectory() as directory,patch.object(settings,'PATH',directory+'/settings.json'):
    for design in [key for key,_ in theme.CHOICES]+['eclipse_crystal','minimal']:
        settings.set_many(dict(theme=design,accent='design_default',motion='off',ultra_eco=design=='minimal'))
        theme.set_mode(design);app.setStyleSheet(theme.stylesheet())
        card=Card('Aktuelle Werte');value=label('42 °C','chipValue');card.body.addWidget(value)
        for width in (300,700):
            card.resize(width,160);card.show();app.processEvents()
            margins=card.layout().contentsMargins()
            assert margins.left()==margins.right()
            assert margins.left()==(16 if width<520 else 20)
            assert card.rect().contains(value.geometry())
            card._hover=False;before=card.grab().toImage();card._hover=True
            assert card.grab().toImage()==before,'Passive card flashed on hover'
        dialog=QDialog();dialog.resize(500,320);layout=QVBoxLayout(dialog)
        layout.addWidget(label('Technische Spezifikationen','bigName'))
        button=QPushButton('Schließen');layout.addWidget(button)
        dialog.show();app.processEvents()
        assert dialog.layout().contentsMargins().left()==24
        assert dialog.layout().spacing()==14
        assert not dialog.grab().isNull()
        assert dialog.rect().contains(button.geometry())
        dialog.close();card.close();dialog.deleteLater();card.deleteLater();app.processEvents()
    # The native popup must have the same silhouette as its painted border,
    # including when an existing selector survives a design change.
    combo=QComboBox();combo.addItems(['One','Two','Three']);combo.show()
    theme.set_mode('aurora_bloom');app.setStyleSheet(theme.stylesheet())
    combo.showPopup();app.processEvents();popup=combo.view().window()
    assert not popup.mask().isEmpty()
    assert not popup.mask().contains(QPoint(0,0))
    assert popup.mask().contains(popup.rect().center())
    combo.hidePopup();theme.set_mode('obsidian_gold');app.setStyleSheet(theme.stylesheet())
    combo.showPopup();app.processEvents();assert popup.mask().isEmpty()
    combo.hidePopup();combo.close()
print('All-design readable dialogs, matching control gutters, adaptive card spacing and quiet passive surfaces PASS')
