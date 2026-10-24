"""Wrap visible chart controls without shrinking their labels or indicators."""
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtWidgets import QLayout


class FlowLayout(QLayout):
    def __init__(self, parent=None, spacing=10):
        super().__init__(parent)
        self._items=[]
        self.setContentsMargins(0,0,0,0)
        self.setSpacing(spacing)

    def addItem(self,item):
        self._items.append(item)
        self.invalidate()

    def count(self):
        return len(self._items)

    def itemAt(self,index):
        return self._items[index] if 0<=index<len(self._items) else None

    def takeAt(self,index):
        if 0<=index<len(self._items):
            item=self._items.pop(index)
            self.invalidate()
            return item
        return None

    def expandingDirections(self):
        return Qt.Orientations()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self,width):
        return self._arrange(QRect(0,0,max(1,width),0),measure=True)

    def minimumSize(self):
        size=QSize()
        for item in self._items:
            if not item.isEmpty():size=size.expandedTo(item.minimumSize())
        left,top,right,bottom=self.getContentsMargins()
        return size+QSize(left+right,top+bottom)

    def sizeHint(self):
        return self.minimumSize()

    def setGeometry(self,rect):
        super().setGeometry(rect)
        self._arrange(rect)

    def _arrange(self,rect,measure=False):
        left,top,right,bottom=self.getContentsMargins()
        area=rect.adjusted(left,top,-right,-bottom)
        x,y=area.x(),area.y()
        line_height=0
        row=[]
        def place_row():
            if not measure:
                for item,left,width,height in row:
                    item.setGeometry(QRect(left,y+(line_height-height)//2,width,height))
        for item in self._items:
            if item.isEmpty():continue
            hint=item.sizeHint()
            width=min(hint.width(),max(1,area.width()))
            height=item.heightForWidth(width) if item.hasHeightForWidth() else hint.height()
            height=max(hint.height(),height)
            if x>area.x() and x+width>area.right()+1:
                place_row();row.clear()
                x=area.x();y+=line_height+self.spacing();line_height=0
            row.append((item,x,width,height))
            x+=width+self.spacing()
            line_height=max(line_height,height)
        place_row()
        return y+line_height-rect.y()+bottom
