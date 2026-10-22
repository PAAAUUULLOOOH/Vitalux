"""Edit feedback stays visible; entering edit mode never moves tiles."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication,QFrame
from vitalux import settings
from vitalux.dashboard import DashboardBoard

app=QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    settings.set('motion','smooth')
    board=DashboardBoard();board.resize(1000,800)
    for key in ('hero','cpu','gpu'):board.register(key,QFrame())
    board.show();app.processEvents();board.refresh_geometry()
    origins={key:tile.pos() for key,tile in board.tiles.items()}
    board.begin_edit()
    for tile in board.tiles.values():
        QApplication.sendEvent(tile,QEvent(QEvent.Leave))
        assert tile.drag.isVisible() and tile.remove.isVisible()
    from PySide6.QtTest import QTest
    QTest.qWait(2100)
    assert all(tile.pos()==origins[key] for key,tile in board.tiles.items())
    assert not hasattr(board,'_wobble')
    board.finish_edit(save=False)
    assert all(tile.drag.isHidden() and tile.remove.isHidden() for tile in board.tiles.values())
    board.begin_edit()
    tile=board.tiles['cpu']
    board.begin_drag('cpu',tile.mapToGlobal(tile.rect().center()))
    assert board._dragging is not None
    board.end_drag();board.finish_edit(save=False)
    settings.set('motion','off');board.begin_edit()
    assert all(tile.drag.isVisible() for tile in board.tiles.values())
    board.finish_edit(save=False);board.close()
print('Stationary editing, permanent hold/X captions and drag/off-motion safety PASS')
