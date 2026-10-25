"""Hover capability hints, keyboard discovery and native switch interaction."""
import os,sys,tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt,QPoint
from PySide6.QtGui import QFocusEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QWidget,QGridLayout
from vitalux import settings,theme,i18n
from vitalux.premium import DesignTile
from vitalux.design_capabilities import capabilities
from vitalux.design_settings import Gallery
from vitalux.ui_locale import QCheckBox


def run():
    app=QApplication([]);previous=settings.PATH
    with tempfile.TemporaryDirectory() as folder:
        settings.PATH=str(Path(folder)/'settings.json');settings.set_many(dict(motion='off',theme='glass'))
        content=QWidget();grid=QGridLayout(content);tiles=[]
        for index,(key,_) in enumerate(theme.CHOICES):
            tile=DesignTile(key);tiles.append(tile);grid.addWidget(tile,index//3,index%3)
        gallery=Gallery(content,tiles);gallery.resize(650,gallery.height());gallery.show();app.processEvents()
        for design in ('glass','aether_glass','eclipse_crystal'):
            theme.set_mode(design);app.setStyleSheet(theme.stylesheet());gallery.sync();app.processEvents()
            assert gallery.horizontalScrollBarPolicy()==Qt.ScrollBarAlwaysOff
            assert all(grid.getItemPosition(grid.indexOf(tile))[:2]==(index//3,index%3) for index,tile in enumerate(tiles))
        tile=tiles[2];tile._hover_animation.stop();tile._hover=0;before=tile.grab().toImage()
        tile.focusInEvent(QFocusEvent(QFocusEvent.FocusIn,Qt.TabFocusReason));app.processEvents()
        assert tile._hover==1 and tile.grab().toImage()!=before
        for language in ('de','en'):
            i18n.set_lang(language);tile.retranslate()
            assert ('anpassbar' if language=='de' else 'adjustable') in tile.toolTip()
        assert capabilities('obsidian_gold')['accent'] and capabilities('quantum_core')['background']
        assert capabilities('glass')['accent'] and capabilities('glass')['custom_accent']
        for design in (key for key,_ in theme.CHOICES):
            theme.set_mode(design);box=QCheckBox('Toggle');box.resize(box.sizeHint());box.show();app.processEvents()
            QTest.mouseClick(box,Qt.LeftButton,pos=QPoint(36,box.height()//2))
            assert box.isChecked() and box._toggle_progress==1,design
            box.setFocus();QTest.keyClick(box,Qt.Key_Space);assert not box.isChecked()
            box.close()
        gallery.close();settings.PATH=previous
    print('All-theme gallery grid, capability hints, keyboard hover and switch hit targets PASS')


if __name__=='__main__':run()
