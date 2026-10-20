"""Signature designs use a horizontal gallery and responsive settings columns."""
from PySide6.QtCore import QTimer,Qt
from PySide6.QtWidgets import QScrollArea,QFrame,QGridLayout,QWidget
from . import signature_designs


class Gallery(QScrollArea):
    def __init__(self,content,tiles,parent=None):
        super().__init__(parent)
        self.tiles=tiles
        self._mode=None
        self.setObjectName('glassScroll')
        self.setFrameShape(QFrame.NoFrame)
        self.setWidget(content)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sync()

    def sync(self):
        signature=signature_designs.active()
        if signature!=self._mode:
            self._mode=signature
            grid=self.widget().layout()
            for tile in self.tiles:grid.removeWidget(tile)
            for column in range(len(self.tiles)):grid.setColumnStretch(column,0)
            for index,tile in enumerate(self.tiles):
                tile.setMinimumWidth(176 if signature else 125)
                tile.setMaximumWidth(176 if signature else 16777215)
                grid.addWidget(tile,0 if signature else index//3,index if signature else index%3)
            self.setWidgetResizable(not signature)
            width=len(self.tiles)*176+(len(self.tiles)-1)*grid.spacing()
            self.widget().setMinimumWidth(width if signature else 0)
            self.widget().setMaximumWidth(width if signature else 16777215)
            height=112 if signature else ((len(self.tiles)+2)//3)*112+((len(self.tiles)-1)//3)*grid.spacing()
            self.widget().setFixedHeight(height)
            self.setFixedHeight(height+(14 if signature else 2))
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded if signature else Qt.ScrollBarAlwaysOff)
        if signature:QTimer.singleShot(0,self._show_selected)

    def _show_selected(self):
        if self._mode:
            selected=next((tile for tile in self.tiles if tile.isChecked()),None)
            if selected is not None:self.ensureWidgetVisible(selected,12,0)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self._mode:QTimer.singleShot(0,self._show_selected)


class CardDeck(QWidget):
    def __init__(self,cards,parent=None):
        super().__init__(parent)
        self.cards=list(cards)
        self._columns=0
        self.grid=QGridLayout(self)
        self.grid.setContentsMargins(0,0,0,0)
        self.grid.setSpacing(16)
        self.sync()

    def sync(self):
        columns=2 if signature_designs.active() and self.width()>=1000 else 1
        if columns==self._columns:return
        self._columns=columns
        for card in self.cards:self.grid.removeWidget(card)
        for index,card in enumerate(self.cards):self.grid.addWidget(card,index//columns,index%columns)
        self.grid.setColumnStretch(0,1)
        self.grid.setColumnStretch(1,1 if columns==2 else 0)
        self.updateGeometry()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.sync()
