"""Asynchronous product pictures, stale results, language/theme changes and board UI."""
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QThread
from PySide6.QtGui import QImage,QPainter,QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from vitalux import i18n, product_ui, theme, pages
from vitalux.product_images import product_key
from vitalux.widgets import label
from vitalux.ui_locale import retranslate_widgets

app = QApplication.instance() or QApplication([])
product = dict(kind='gpu', vendor='SAPPHIRE', model='SAPPHIRE PURE Radeon RX 9070 XT', revision='', exact=True)
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)/'fixture.png'
    image = QImage(320, 160, QImage.Format_ARGB32)
    image.fill(0)
    painter=QPainter(image);painter.fillRect(12,8,image.width()-24,image.height()-16,QColor('#eeeeee'));painter.end()
    assert image.save(str(path))
    result = dict(path=str(path), vendor='SAPPHIRE', source='https://www.sapphiretech.com/product')
    calls = []
    started, release = threading.Event(), threading.Event()
    def resolve(item, **kwargs):
        assert QThread.currentThread() != app.thread(), 'Network/cache lookup must run off the GUI thread'
        calls.append(dict(item))
        started.set()
        release.wait(2)
        return result
    with patch.object(product_ui, 'resolve', side_effect=resolve):
        one = product_ui.ProductHeader(label('PURE RX 9070 XT'), label('SAPPHIRE'), 'gpu')
        two = product_ui.ProductHeader(label('Same card'), label('SAPPHIRE'), 'gpu')
        for widget in (one, two):
            widget.set_product(product)
            widget.resize(800, 260)
            widget.show()
        QTest.qWait(50)
        assert started.is_set() and len(calls) == 1, 'Same product must not start duplicate downloads'
        assert one.picture.pixmap.isNull()
        release.set()
        deadline = time.monotonic() + 3
        while one.picture.pixmap.isNull() and time.monotonic() < deadline:
            QTest.qWait(20)
        assert not one.picture.pixmap.isNull() and not two.picture.pixmap.isNull()
        assert not hasattr(one, 'caption') and not one.picture.isHidden()
        for design, title in theme.CHOICES:
            theme.set_mode(design)
            app.setStyleSheet(theme.stylesheet())
            for language, expected in (('de', 'Offline verfügbar'), ('en', 'Available offline')):
                i18n.set_lang(language)
                retranslate_widgets(one)
                app.processEvents()
                assert not hasattr(one, 'caption')
                assert not one.picture.pixmap.isNull()
        assert len(calls) == 1, 'Restyling/retranslation must retain the cached image'
        one.set_product(dict(product, exact=False))
        one._ready(product_key(product), result)
        assert one.picture.pixmap.isNull() and one.picture.isHidden(), 'Late results must not overwrite a different product'
        for widget in (one, two): widget.close()
    static = dict(kernel='fixture', arch='x86_64', host='host', user='user', desktop='KDE',
                  session='Wayland', vendor='ASUS', product='Desktop', board='ASUS ROG STRIX B650-A GAMING WIFI',
                  bios='1', plasma='6', kwin='6', frameworks='6', mesa='25',
                  board_product=dict(kind='mainboard', vendor='ASUS', model='ROG STRIX B650-A GAMING WIFI', revision='1.0', exact=True))
    with patch.object(pages, 'system_static', return_value=static):
        board = pages.SystemPage(dict(name='Linux'))
        assert board.board_name.text() == static['board_product']['model']
        assert board.board_header.product['kind'] == 'mainboard'
        assert board.content.itemAt(0).widget() is board.board_card
        board.close()
    from vitalux.widgets import ChartPanel
    gpu = dict(id='A', name=product['model'], board_vendor='SAPPHIRE', product=product, vendor='AMD',
               driver='amdgpu', usage=0, vram_used=0, vram_total=16*2**30, power=83, temp=52,
               hardware=[dict(id='p', component='gpu:A', kind='powers', name='PPT', value=83, unit='W',
                              limits=[('Leistungsgrenze', 317)])])
    card = pages.GpuCard()
    card.refresh(gpu)
    assert card.name.text() == product['model'] and 'SAPPHIRE' in card.meta.text()
    assert card.kv['Leistung'].v.text() == '83 W' and card.kv['Leistungsgrenze'].v.text() == '317 W'
    assert len(card.findChildren(ChartPanel)) == 3 and card.details.isHidden()
    assert card.body.itemAt(0).widget() is card.product_header
    card.close()
app._product_image_loader.shutdown()
app._product_image_loader.pool.waitForDone(3000)
print('Background loading, deduplication, stale-image rejection, 14 palettes, DE/EN and clean GPU/Mainboard cards PASS')
