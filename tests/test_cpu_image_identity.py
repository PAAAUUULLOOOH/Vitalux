"""An exact CPU page must not authorize a hero picture of another processor."""
import os,sys,tempfile,json,hashlib
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QByteArray,QBuffer,QIODevice,Qt
from PySide6.QtGui import QImage,QColor
from vitalux import product_images as images
product=dict(kind='cpu',vendor='Intel',model='Intel(R) Core(TM) i5-14600KF',exact=True,revision='')
wrong='https://cdn.shop.com/intel-core-i9-14900k.jpg'
right='https://cdn.shop.com/intel-core-i5-14600kf.png'
assert not images.cpu_image_matches(product,wrong,'Intel Core i5-14600KF')
assert not images.cpu_image_matches(product,'https://cdn.shop.com/banner.jpg')
assert images.cpu_image_matches(product,right)
assert not images.cpu_image_matches(product,'https://cdn.shop.com/i5-14600k.png')
assert images.cpu_image_matches(product,'https://cdn.shop.com/picture.png','Intel Core i5-14600KF')
image=QImage(160,160,QImage.Format_ARGB32);image.fill(Qt.transparent)
for y in range(30,130):
 for x in range(30,130):image.setPixelColor(x,y,QColor('#abcaff'))
raw=QByteArray();buffer=QBuffer(raw);buffer.open(QIODevice.WriteOnly);image.save(buffer,'PNG');raw=bytes(raw)
with tempfile.TemporaryDirectory() as directory:
 cache=images.ProductCache(directory);key=images.product_key(product)
 Path(directory,key+'.image').write_bytes(raw)
 Path(directory,key+'.json').write_text(json.dumps(dict(key=key,model=product['model'],vendor='Intel',source='https://www.intel.com/i5-14600kf',image_url=wrong,sha256=hashlib.sha256(raw).hexdigest())))
 assert cache.load(product) is None,'Legacy i9 picture reused for an i5'
 saved=cache.save(product,raw,'https://shop.com/intel-core-i5-14600kf',right)
 assert cache.load(product)['sha256']==saved['sha256']
 try:cache.save(product,raw,'https://shop.com/intel-core-i5-14600kf',wrong)
 except ValueError:pass
 else:raise AssertionError('A contradictory image was cached')
print('Exact i5-14600KF image identity, K/KF boundaries, i9 rejection and unsafe-cache recovery PASS')
