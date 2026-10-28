"""General product lookup, internal DMI codes, cutouts, JSON-LD and image CDNs."""
import json,os,sys,tempfile,hashlib
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QBuffer,QIODevice
from PySide6.QtGui import QImage,QPainter,QColor
from vitalux import hardware_identity as identity,product_images as images

provenance=json.loads(Path('assets/hardware/provenance.json').read_text())
assert hashlib.sha256(Path('assets/hardware/pci.ids').read_bytes()).hexdigest()==provenance['sha256']
assert identity.manufacturer('Dell Inc.')=='Dell'
assert identity.manufacturer('Hewlett-Packard')=='HP'
board=identity.board_identity('Micro-Star International Co., Ltd.','MAG B650 TOMAHAWK WIFI (MS-7D75)')
assert images.matches_product(board,'MSI MAG B650 TOMAHAWK WIFI | Motherboard')
assert images.search_model(board)=='MAG B650 TOMAHAWK WIFI'
assert not images.matches_product(board,'MSI MAG B650M TOMAHAWK WIFI')
gpu=dict(kind='gpu',vendor='ASUS',model='ASUS TUF Gaming Radeon RX 9060 XT',revision='',exact=True)
assert images.matches_product(gpu,'ASUS TUF GAMING Radeon RX 9060 XT OC Edition')
assert not images.matches_product(gpu,'ASUS PRIME Radeon RX 9060 XT')
assert images.product_key(dict(kind='cpu',vendor='AMD',model='Ryzen 7 9800X3D',exact=True))
assert images.product_key(dict(kind='ram',vendor='Kingston',model='KF560C30-16',exact=True))
assert images.matches_product(dict(kind='cpu',vendor='AMD',model='AMD Ryzen 7 9800X3D 8-Core Processor'), 'AMD Ryzen 7 9800X3D')
assert images.matches_product(dict(kind='cpu',vendor='Intel',model='Intel(R) Core(TM) i7-6700K CPU @ 4.00GHz'), 'Intel Core i7-6700K')
image=QImage(160,100,QImage.Format_ARGB32);image.fill(0)
p=QPainter(image);p.fillRect(15,10,130,80,QColor('white'));p.end()
buffer=QBuffer();buffer.open(QIODevice.WriteOnly);assert image.save(buffer,'PNG');png=bytes(buffer.data())
assert images.cutout_image(png),'White hardware itself must remain opaque and intact'
opaque=QImage(160,100,QImage.Format_ARGB32);opaque.fill(QColor('white'))
buf=QBuffer();buf.open(QIODevice.WriteOnly);opaque.save(buf,'PNG');opaque_png=bytes(buf.data())
assert images.valid_image(opaque_png) and not images.cutout_image(opaque_png)
empty=QImage(160,100,QImage.Format_ARGB32);empty.fill(0)
buf=QBuffer();buf.open(QIODevice.WriteOnly);empty.save(buf,'PNG');assert not images.cutout_image(bytes(buf.data()))
with tempfile.TemporaryDirectory() as directory:
    product=dict(kind='mainboard',vendor='Framework',model='Mainboard 16',revision='',exact=True)
    source='https://frame.work/products/mainboard-16';photo='https://cdn.frame.work/hashed-product.png'
    wrong='https://cdn.frame.work/wrong.png';calls=[]
    def download(url,limit,hosts):
        calls.append(url)
        if url.startswith('https://www.bing.com/search?'):
            return f'<rss><channel><item><title>Framework Mainboard 16</title><link>{source}</link></item></channel></rss>'.encode()
        if url==source:
            graph={'@graph':[{'@type':'Product','name':'Mainboard 13','image':wrong},
                             {'@type':'Product','name':'Mainboard 16','image':{'contentUrl':photo}}]}
            return ('<title>Framework Mainboard 16</title><script type="application/ld+json">'+json.dumps(graph)+'</script>').encode()
        assert url==photo,'An unrelated product or gallery image was selected'
        return png
    cache=images.ProductCache(directory)
    saved=images.resolve(product,cache,download)
    assert saved and Path(saved['path']).read_bytes()==png and calls==[calls[0],source,photo]
    def offline(*args):raise AssertionError('A cached cutout accessed the Internet')
    assert images.resolve(product,images.ProductCache(directory),offline)['cached']
    opaque=cache.save(product,opaque_png,source,photo)
    assert opaque and not opaque['cutout'] and cache.load(product)['cached']
    assert not images.allowed_url('https://127.0.0.1/private')
    assert not images.allowed_url('https://localhost/private')
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    for name,value in (('vendor','1002'),('device','7590'),('subsystem_vendor','1458'),('subsystem_device','2429')):
        (root/name).write_text('0x'+value)
    known=identity.gpu_identity(dict(device_path=str(root),name='GPU'))
    assert known['board_vendor']=='GIGABYTE' and '9060 XT' in known['board_model']
    (root/'subsystem_vendor').write_text('0x1043');(root/'subsystem_device').write_text('0x0639')
    shared=identity.gpu_identity(dict(device_path=str(root),name='AMD Radeon RX 9060 XT'))
    assert shared['board_vendor']=='ASUS' and '9060 XT' in shared['identified_name']
    assert not shared['product']['exact'],'A generic ASUS ID must not be guessed into TUF'
    explicit=identity.gpu_identity(dict(device_path=str(root),name='ASUS TUF Gaming Radeon RX 9060 XT'))
    assert explicit['product']['exact']
print('General manufacturer/model queries, RX 9060 family, cutouts, separate retail identities and JSON-LD CDN lookup PASS')
