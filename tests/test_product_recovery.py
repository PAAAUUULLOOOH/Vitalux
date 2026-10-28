"""Supported component lookup paths, CPU suffixes, cutouts and opaque recovery."""
import json,os,sys,tempfile
from html import escape
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QBuffer,QIODevice
from PySide6.QtGui import QImage,QPainter,QColor
from vitalux import product_images as images

def picture(transparent):
 image=QImage(200,120,QImage.Format_ARGB32);image.fill(0 if transparent else QColor('white'))
 p=QPainter(image);p.fillRect(20,15,160,90,QColor('#cccccc'));p.end()
 buf=QBuffer();buf.open(QIODevice.WriteOnly);image.save(buf,'PNG');return bytes(buf.data())
cutout,background=picture(True),picture(False)
cases=[
 ('cpu','Intel','13th Gen Intel(R) Core(TM) i7-13700K @ 3.40GHz','Intel Core i7 13700K Desktop Processor'),
 ('cpu','AMD','AMD Ryzen 7 9800X3D 8-Core Processor','AMD Ryzen 7 9800X3D'),
 ('mainboard','Micro-Star International','MAG B650 TOMAHAWK WIFI (MS-7D75)','MSI MAG B650 TOMAHAWK WIFI'),
 ('mainboard','ASUSTeK COMPUTER INC.','ROG STRIX B650-A GAMING WIFI','ASUS ROG STRIX B650 A GAMING Wi-Fi'),
 ('gpu','ASUS','ASUS TUF Gaming Radeon RX 9060 XT','ASUS TUF Gaming Radeon RX 9060 XT 16GB')]
for kind,vendor,model,title in cases:
 product=dict(kind=kind,vendor=vendor,model=model,exact=True,revision='')
 assert images.matches_product(product,title),(model,title)
 assert not images.matches_product(product,'Intel Core i5-12400F / ASUS PRIME B650M / unrelated'),model
 with tempfile.TemporaryDirectory() as directory:
  page='https://retailer.com/product';photo='https://cdn.retailer.com/'+title.replace(' ','-').lower()+'.png';events=[]
  def download(url,limit,hosts):
   if url.startswith('https://www.bing.com/search?'):
    return ('<rss><channel><item><title>'+title+'</title><link>'+page+'</link></item></channel></rss>').encode()
   if url==page:return ('<title>'+title+'</title><meta property="og:image" content="'+photo+'">').encode()
   if url==photo:return background
   raise OSError('Unavailable')
  result=images.resolve(product,images.ProductCache(directory),download,on_preview=events.append)
  assert result and result['cutout'] is False and events and events[0]['path']==result['path']
  assert json.loads((Path(directory)/(images.product_key(product)+'.lookup.json')).read_text())['result']=='background'
  def offline(*args):raise AssertionError('Existing product picture attempted network access')
  restored=images.resolve(product,images.ProductCache(directory),offline)
  assert restored['cached'] and restored['sha256']==result['sha256']
  # Old .20 metadata did not contain a transparency flag. Keep its valid image.
  meta=Path(directory)/(images.product_key(product)+'.json');data=json.loads(meta.read_text());data.pop('cutout');meta.write_text(json.dumps(data))
  assert images.resolve(product,images.ProductCache(directory),offline)['cached']

product=dict(kind='cpu',vendor='AMD',model='Ryzen 7 9800X3D',exact=True,revision='')
with tempfile.TemporaryDirectory() as directory:
 page='https://retailer.com/ryzen';opaque='https://cdn.retailer.com/ryzen-7-9800x3d-photo.png';alpha='https://cdn.retailer.com/transparent.png';events=[]
 def download(url,limit,hosts):
  if 'bing.com/search?' in url:return ('<rss><channel><item><title>AMD Ryzen 7 9800X3D</title><link>'+page+'</link></item></channel></rss>').encode()
  if url==page:return ('<title>AMD Ryzen 7 9800X3D</title><meta property="og:image" content="'+opaque+'"><img src="placeholder.gif" data-src="'+alpha+'" alt="AMD Ryzen 7 9800X3D">').encode()
  if url==opaque:return background
  if url==alpha:return cutout
  raise OSError('Unavailable')
 result=images.resolve(product,images.ProductCache(directory),download,on_preview=events.append)
 assert result['cutout'] and events and not events[0]['cutout']
 assert Path(result['path']).read_bytes()==cutout
# A transparent-only image-search filter must not suppress background alternatives.
with tempfile.TemporaryDirectory() as directory:
 def download(url,limit,hosts):
  if 'bing.com/images/search?' in url:
   if 'qft=' in url:return b''
   row=dict(t='AMD Ryzen 7 9800X3D',purl='https://retailer.com/ryzen',murl='https://cdn.retailer.com/ryzen-7-9800x3d-photo.png')
   return ('<a m="'+escape(json.dumps(row),quote=True)+'"></a>').encode()
  if url=='https://cdn.retailer.com/ryzen-7-9800x3d-photo.png':return background
  raise OSError('Unavailable')
 assert images.resolve(product,images.ProductCache(directory),download)['cutout'] is False
print('CPU/GPU/mainboard real model spellings, opaque cache recovery, early preview, preferred cutout and unfiltered image fallback PASS')
