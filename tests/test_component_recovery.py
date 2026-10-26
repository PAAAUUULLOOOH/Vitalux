"""Per-component recovery preserves other caches and rejects superseded worker results."""
import os,sys,tempfile,threading,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ['VITALUX_SPEC_OFFLINE']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QBuffer,QIODevice
from PySide6.QtGui import QImage,QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from vitalux import profiles,settings,product_ui,product_images as images,product_specs
from vitalux.widgets import label
app=QApplication.instance() or QApplication([])
def picture(color):
    image=QImage(160,100,QImage.Format_ARGB32);image.fill(QColor(color))
    buffer=QBuffer();buffer.open(QIODevice.WriteOnly);assert image.save(buffer,'PNG')
    return bytes(buffer.data())
def wait_until(condition):
    deadline=time.monotonic()+4
    while not condition() and time.monotonic()<deadline:QTest.qWait(10)
    assert condition()
product=dict(kind='gpu',vendor='ASUS',model='TUF GAMING Radeon RX 9060 XT',exact=True)
other=dict(kind='mainboard',vendor='ASUS',model='ROG STRIX B650-A GAMING WIFI',exact=True)
source='https://www.asus.com/product/fixture'
old_url='https://www.asus.com/images/wrong.png'
with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{f'XDG_{kind.upper()}_HOME':str(Path(directory)/kind) for kind in profiles.KINDS}),patch.object(settings,'PATH',str(Path(directory)/'settings.json')):
    cache=images.ProductCache();old=cache.save(product,picture('red'),source,old_url)
    preserved=cache.save(other,picture('blue'),source,source+'/board.png')
    with patch.object(images,'decode_image',wraps=images.decode_image) as decode:
        assert cache.load(product)
        assert decode.call_count==1,'One cache load decoded the image repeatedly'
    started,release=threading.Event(),threading.Event()
    def delayed(*args,**kwargs):started.set();release.wait(3);return dict(old)
    header=product_ui.ProductHeader(label('GPU'),label('ASUS'),'gpu');header.set_product(product)
    local=Path(directory)/'selected.png';local.write_bytes(picture('green'))
    with patch.object(product_ui,'resolve',side_effect=delayed):
        header._request();wait_until(started.is_set)
        with patch.object(__import__('vitalux.ui_locale',fromlist=['QFileDialog']).QFileDialog,'getOpenFileName',return_value=(str(local),'')):
            header.choose_image()
        manual=header._result['sha256'];assert header._result['manual']
        release.set();wait_until(lambda:product_ui.loader().pool.activeThreadCount()==0);QTest.qWait(30)
        assert header._result['sha256']==manual and header._result['manual'],'Old worker replaced the user-selected image'
        assert cache.load(other)['sha256']==preserved['sha256']
    # Reload discards only this product's overrides and does not reset preferences.
    settings.set('accent','#123456')
    def fresh(*args,**kwargs):return cache.save(product,picture('yellow'),source,source+'/fresh.png')
    with patch.object(product_ui,'resolve',side_effect=fresh):
        header.refresh_component();wait_until(lambda:bool(header._result and not header._result.get('manual')))
    assert settings.get('accent')=='#123456' and cache.load(other)['sha256']==preserved['sha256']
    rejected=header._result['image_url'];header.discard_image()
    assert header.picture.pixmap.isNull() and rejected in cache.rejected(product)
    assert cache.load(product) is None and cache.load(other)
    requested=[]
    html=('<title>'+product['model']+'</title><img class="product" src="'+rejected+'"><img class="product" src="'+source+'/replacement.png">').encode()
    def fetch(url,*args):
        requested.append(url)
        return picture('cyan') if url.endswith('.png') else html
    with patch.object(images,'manufacturer_pages',return_value=[source]),patch.object(images,'search_pages',return_value=[]),patch.object(images,'search_images',return_value=[]):
        result=images.resolve(product,cache=cache,download=fetch)
    assert result and rejected not in requested and result['image_url']!=rejected
    header.close();product_ui.loader().shutdown();product_ui.loader().pool.waitForDone(3000)
print('One image decode, manual/offline import, stale worker rejection, targeted refresh and persistent wrong-image exclusion PASS')
