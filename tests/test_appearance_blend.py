"""A live destination must not contribute extra light to an appearance blend."""
import os, sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QWidget
from vitalux.appearance_transition import AppearanceTransition

app = QApplication([])


class Host(QWidget):
    window_frame = True
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#d086e0'))
        p.end()


def frame(tone, ratio):
    image = QPixmap(round(96*ratio), round(64*ratio))
    image.setDevicePixelRatio(ratio)
    image.fill(Qt.transparent)
    p = QPainter(image)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen);p.setBrush(QColor(tone))
    p.drawRoundedRect(QRectF(1,1,94,62), 15, 15)
    p.end()
    return image


checks = 0
for ratio in (1., 1.25, 1.5, 2.):
    for first, last in (('#131418','#2e2756'),('#e1e5f5','#27394e'),('#1d3b55','#394a59')):
        host = Host();host.setAttribute(Qt.WA_TranslucentBackground,True);host.resize(96,64)
        host.show();app.processEvents()
        before, after = frame(first,ratio), frame(last,ratio)
        overlay = AppearanceTransition(host,before,after)
        overlay.show();app.processEvents()
        for amount in (0., .1, .25, .5, .75, .9, 1.):
            overlay._frame(amount)
            image = host.grab().toImage();dpr=image.devicePixelRatio()
            actual = image.pixelColor(round(48*dpr),round(32*dpr))
            assert actual.alpha()==255,(ratio,amount,'Opaque content lost alpha',actual.alpha())
            a,b=QColor(first),QColor(last)
            for channel in ('red','green','blue'):
                expected=getattr(a,channel)()*(1-amount)+getattr(b,channel)()*amount
                assert abs(getattr(actual,channel)()-expected)<=2,(ratio,amount,channel,actual.name(),expected)
            assert image.pixelColor(0,0).alpha()==0,'Blend filled a rounded window cutout'
            checks+=1
        # Repeated paints reuse one bounded composition buffer.
        assert overlay._blend.size()==before.size()
        overlay.finish();overlay.finish()
        assert overlay._blend.isNull()
        host.close();host.deleteLater();app.processEvents()
print(f'{checks} live, rounded crossfade samples retain exact brightness at native and fractional resolutions PASS')
