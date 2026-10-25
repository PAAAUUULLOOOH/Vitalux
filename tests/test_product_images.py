"""Real-image validation, manufacturer search, durable offline cache and fallbacks."""
import os
import sys
import tempfile
import json
from html import escape
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QImage,QPainter,QColor
from vitalux import product_images as images, profiles

buffer = QBuffer()
buffer.open(QIODevice.WriteOnly)
image = QImage(120, 60, QImage.Format_ARGB32)
image.fill(0)
painter=QPainter(image);painter.fillRect(12,8,image.width()-24,image.height()-16,QColor('#eeeeee'));painter.end()
assert image.save(buffer, 'PNG')
png = bytes(buffer.data())
assert images.valid_image(png)
assert not images.valid_image(b'<html>not an image</html>')
gpu = dict(kind='gpu', vendor='SAPPHIRE', model='SAPPHIRE PURE Radeon RX 9070 XT', revision='', exact=True)
board = dict(kind='mainboard', vendor='ASUS', model='ROG STRIX B650-A GAMING WIFI', revision='1.0', exact=True)
assert images.product_key(gpu) != images.product_key(board)
assert images.product_key(gpu) == images.product_key(dict(gpu, vendor='sapphire'))
assert not images.product_key(dict(gpu, exact=False))
assert images.matches_product(gpu, 'SAPPHIRE PURE AMD Radeon RX 9070 XT OC GPU')
assert not images.matches_product(gpu, 'SAPPHIRE PURE AMD Radeon RX 9070 OC GPU')
assert not images.matches_product(dict(gpu, model='SAPPHIRE PURE Radeon RX 9070'), gpu['model'])
assert images.matches_product(board, 'ROG STRIX B650-A GAMING WIFI | Motherboards | ASUS')
assert not images.allowed_url('https://asus.com.evil.invalid/photo.png', ('asus.com',))
assert not images.allowed_url('http://www.asus.com/photo.png', ('asus.com',))
assert not images.allowed_url('https://user@www.asus.com/photo.png', ('asus.com',))
assert images.allowed_url('https://dlcdnwebimgs.asus.com/product.png', ('asus.com',))
with tempfile.TemporaryDirectory() as directory:
    cache = images.ProductCache(directory)
    calls = []
    def online(url, limit, hosts):
        calls.append(url)
        assert url == images.SAPPHIRE_PURE_IMAGE and limit == images.MAX_IMAGE
        return png
    result = images.resolve(gpu, cache, online)
    assert result and len(calls) == 1 and not result['cached']
    assert Path(result['path']).read_bytes() == png
    def offline(*args):
        raise AssertionError('A valid cached image must never require a network request')
    restarted = images.resolve(gpu, images.ProductCache(directory), offline)
    assert restarted['cached'] and restarted['sha256'] == result['sha256']
    assert images.ProductCache(directory).load(dict(gpu, model='SAPPHIRE PULSE Radeon RX 9070 XT')) is None
    Path(result['path']).write_bytes(b'corrupt')
    assert images.ProductCache(directory).load(gpu) is None
    result = images.resolve(gpu, images.ProductCache(directory), online)
    assert result and len(calls) == 2
    (Path(directory)/(images.product_key(gpu)+'.json')).write_text('[]')
    assert images.ProductCache(directory).load(gpu) is None
    cache = images.ProductCache(Path(directory)/'board')
    calls.clear()
    page = 'https://www.asus.com/motherboards/rog-strix-b650-a-gaming-wifi/'
    photo = 'https://dlcdnwebimgs.asus.com/product.png'
    def search(url, limit, hosts):
        calls.append(url)
        if url.startswith('https://www.bing.com/'):
            return ('<rss><channel><item><title>ROG STRIX B650-A GAMING WIFI</title>'
                    '<link>'+page+'</link></item><item><title>ROG STRIX B650-A GAMING WIFI</title>'
                    '<link>https://untrusted.invalid/product</link></item></channel></rss>').encode()
        if url == page:
            return ('<html><title>ROG STRIX B650-A GAMING WIFI | ASUS</title>'
                    '<meta property="og:image" content="'+photo+'">'
                    '<img src="https://dlcdnwebimgs.asus.com/product-unrelated.png"></html>').encode()
        assert url == photo
        return png
    result = images.resolve(board, cache, search)
    assert result and result['source'] == page and len(calls) == 3
    assert images.resolve(board, images.ProductCache(cache.root), offline)['cached']
    assert cache.load(dict(board, revision='2.0')) is None
    # A blocked/unavailable product-page search can use image-search metadata,
    # while foreign sources and the wrong GPU/mainboard model remain rejected.
    entries = [dict(purl='https://untrusted.invalid/product', murl=photo, t=board['model']),
               dict(purl='https://www.asus.com/prime-z890-p', murl=photo, t='PRIME Z890-P'),
               dict(purl=page, murl=photo, t=board['model'])]
    markup = ''.join('<a class="iusc" m="'+escape(json.dumps(row), quote=True)+'"></a>' for row in entries)
    fallback_calls = []
    def image_search(url, limit, hosts):
        fallback_calls.append(url)
        if url.startswith('https://www.bing.com/search?'):
            raise OSError('RSS unavailable')
        if url.startswith('https://www.bing.com/images/search?'):
            return markup.encode()
        if url.startswith('https://html.duckduckgo.com/'):raise OSError('Search unavailable')
        assert url == photo
        return png
    fallback = images.resolve(board, images.ProductCache(Path(directory)/'image-search'), image_search)
    assert fallback and fallback['source'] == page and len(fallback_calls) == 4
    def network_down(*args): raise OSError('Offline')
    assert images.resolve(dict(board, model='PRIME Z890-P'), cache, network_down) is None
    assert images.resolve(dict(board, exact=False), cache, offline) is None
    with patch.object(profiles, 'directory', side_effect=lambda kind: Path(directory)/profiles.installed()):
        with patch.object(profiles, 'installed', return_value='unstable'):
            unstable = images.ProductCache().root
        with patch.object(profiles, 'installed', return_value='stable'):
            stable = images.ProductCache().root
        assert unstable != stable
print('Manufacturer pages/image search, exact model filtering, validated images, persistent cache and restart without network PASS')
