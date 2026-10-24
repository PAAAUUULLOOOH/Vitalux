"""Find real manufacturer product images and keep a verified, persistent cache."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile
import time
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, HTTPSHandler
import xml.etree.ElementTree as ET

from . import profiles
from .updater import _tls_context


DOMAINS = {
    'sapphire': ('sapphiretech.com', 'sapphiretech.com.cn', 'sapphiretech.global'),
    'asus': ('asus.com',), 'msi': ('msi.com',), 'gigabyte': ('gigabyte.com',),
    'asrock': ('asrock.com',), 'powercolor': ('powercolor.com',),
    'xfx': ('xfxforce.com',), 'zotac': ('zotac.com',), 'evga': ('evga.com',),
    'pny': ('pny.com',), 'palit': ('palit.com',), 'gainward': ('gainward.com',),
    'biostar': ('biostar.com.tw',), 'intel': ('intel.com',),
    'amd': ('amd.com',), 'nvidia': ('nvidia.com',),
    'dell': ('dell.com',), 'hp': ('hp.com',), 'lenovo': ('lenovo.com',),
}
SAPPHIRE_PURE_PAGE = 'https://www.sapphiretech.com/en/consumer/pure-radeon-rx-9070-xt-16g-gddr6'
SAPPHIRE_PURE_IMAGE = ('https://media.cdn.sapphiretech.com.cn/-/media/sites/sapphire/pim/'
                       'product-images/11348_02_rx9070xt_pure_16ggddr6/'
                       'rx9070xt_pure_photo_c01_800x500.ashx?v=4f6b3314b44c4a42882a5f98b0404402')
MAX_IMAGE = 10 * 1024 * 1024
MAX_PAGE = 2 * 1024 * 1024


def product_key(product):
    if not product or not product.get('exact'):
        return ''
    fields = [str(product.get(k) or '').strip().casefold()
              for k in ('kind', 'vendor', 'model', 'revision')]
    if fields[0] not in ('gpu', 'mainboard') or not all(fields[1:3]):
        return ''
    return hashlib.sha256(json.dumps(fields, ensure_ascii=True).encode()).hexdigest()


def domains(product):
    return DOMAINS.get(str(product.get('vendor') or '').lower(), ())


def allowed_url(url, hosts):
    try:
        value = urlsplit(url)
        return (value.scheme == 'https' and value.port in (None, 443) and
                not value.username and not value.password and
                any(value.hostname == host or (value.hostname or '').endswith('.' + host)
                    for host in hosts))
    except ValueError:
        return False


def fetch(url, limit, hosts):
    if not allowed_url(url, hosts):
        raise ValueError('Unsupported product source')
    request = Request(url, headers={'User-Agent': 'Vitalux-ProductImages/1.0',
                                   'Accept': 'text/html,application/xml,image/*;q=0.9,*/*;q=0.5'})
    class ManufacturerRedirect(HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            if not allowed_url(newurl, hosts):
                raise ValueError('Unsupported product redirect')
            return super().redirect_request(request, fp, code, msg, headers, newurl)
    opener = build_opener(ManufacturerRedirect(), HTTPSHandler(context=_tls_context()))
    with opener.open(request, timeout=5) as response:
        if not allowed_url(response.url, hosts):
            raise ValueError('Unsupported product redirect')
        chunks, size, deadline = [], 0, time.monotonic() + 6
        while size <= limit:
            if time.monotonic() >= deadline:
                raise TimeoutError('Product response timed out')
            chunk = response.read1(min(65536, limit + 1 - size))
            if not chunk:
                return b''.join(chunks)
            chunks.append(chunk)
            size += len(chunk)
        raise ValueError('Product response too large')


def valid_image(raw):
    # Decode in the image worker, never on the GUI thread. Reject HTML error
    # pages and huge dimensions before asking an image plugin to allocate.
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice
    from PySide6.QtGui import QImageReader
    if not raw or len(raw) > MAX_IMAGE:
        return False
    buffer = QBuffer()
    buffer.setData(QByteArray(raw))
    buffer.open(QIODevice.ReadOnly)
    reader = QImageReader(buffer)
    size = reader.size()
    if size.width() <= 0 or size.height() <= 0 or size.width() * size.height() > 16000000:
        return False
    return not reader.read().isNull()


def _atomic_bytes(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.product-', delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(raw)
            stream.flush()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


class ProductCache:
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else profiles.directory('cache') / 'hardware-products'

    def load(self, product):
        key = product_key(product)
        if not key:
            return None
        try:
            meta = json.loads((self.root / (key + '.json')).read_text())
            path = self.root / (key + '.image')
            if (meta.get('key') != key or path.stat().st_size > MAX_IMAGE or
                    meta.get('vendor', '').casefold() != product['vendor'].casefold() or
                    meta.get('model', '').casefold() != product['model'].casefold()):
                return None
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != meta.get('sha256') or not valid_image(raw):
                return None
            if not allowed_url(meta.get('source', ''), domains(product)):
                return None
            return dict(meta, path=str(path), cached=True)
        except (OSError, ValueError, TypeError, AttributeError):
            return None

    def save(self, product, raw, source, image_url):
        key = product_key(product)
        if not key or not valid_image(raw):
            raise ValueError('Invalid product image')
        if not all(allowed_url(url, domains(product)) for url in (source, image_url)):
            raise ValueError('Unsupported manufacturer source')
        meta = {'key': key, 'source': source, 'image_url': image_url,
                'sha256': hashlib.sha256(raw).hexdigest(), 'saved': int(time.time()),
                'vendor': product['vendor'], 'model': product['model']}
        path = self.root / (key + '.image')
        _atomic_bytes(path, raw)
        _atomic_bytes(self.root / (key + '.json'), json.dumps(meta).encode())
        return dict(meta, path=str(path), cached=False)


class ProductPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.titles, self.images, self.gallery = [], [], []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self.in_title = True
        if tag == 'meta':
            field = (attrs.get('property') or attrs.get('name') or '').lower()
            value = attrs.get('content', '')
            if field in ('og:image', 'og:image:secure_url', 'twitter:image', 'twitter:image:src'):
                self.images.append(value)
            elif field in ('og:title', 'twitter:title'):
                self.titles.append(value)
        if tag == 'img':
            src = attrs.get('src') or attrs.get('data-src') or ''
            if any(word in src.lower() for word in ('product', 'photo', 'gallery')):
                self.gallery.append(src)

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.titles.append(data)


def matches_product(product, title):
    def words(value):
        return set(re.findall(r'[a-z]+|\d+', value.casefold()))
    ignored = words(product['vendor']) | {'amd', 'radeon', 'nvidia', 'geforce',
                                         'graphics', 'card', 'gpu'}
    required = words(product['model']) - ignored
    actual = words(title)
    if not required or not required <= actual:
        return False
    if product['kind'] == 'gpu':
        for variant in ('xt', 'xtx', 'super', 'ti', 'gre'):
            if (variant in required) != (variant in actual):
                return False
    return True


def search_pages(product, download=fetch):
    hosts = domains(product)
    if not hosts:
        return []
    query = f'site:{hosts[0]} {product["vendor"]} "{product["model"]}"'
    url = 'https://www.bing.com/search?' + urlencode({'format': 'rss', 'q': query})
    document = ET.fromstring(download(url, MAX_PAGE, ('bing.com',)))
    result = []
    for item in document.findall('.//item'):
        link = item.findtext('link') or ''
        title = item.findtext('title') or ''
        if allowed_url(link, hosts) and matches_product(product, title) and link not in result:
            result.append(link)
    return result[:3]


class ImageSearch(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []

    def handle_starttag(self, tag, attrs):
        value = dict(attrs).get('m')
        if value and len(value) < 20000:
            try:
                item = json.loads(value)
                if isinstance(item, dict):
                    self.results.append(item)
            except ValueError:
                pass


def search_images(product, download=fetch):
    hosts = domains(product)
    query = f'{product["vendor"]} {product["model"]} site:{hosts[0]}'
    url = 'https://www.bing.com/images/search?' + urlencode({'q': query})
    page = ImageSearch()
    page.feed(download(url, MAX_PAGE, ('bing.com',)).decode('utf-8', 'replace'))
    matches = []
    for item in page.results[:60]:
        source, image = item.get('purl', ''), item.get('murl', '')
        title = str(item.get('t', ''))
        if (allowed_url(source, hosts) and allowed_url(image, hosts) and
                (matches_product(product, title) or matches_product(product, urlsplit(source).path)) and
                not any(word in urlsplit(image).path.lower() for word in ('logo', 'icon', 'banner'))):
            matches.append((source, image))
    return matches[:4]


def resolve(product, cache=None, download=fetch, cancelled=None):
    """The cache is always checked first, including after a complete restart."""
    cache = cache or ProductCache()
    saved = cache.load(product)
    if saved:
        return saved
    if not product_key(product) or not domains(product):
        return None
    deadline = time.monotonic() + 20
    original_download = download
    def download(url, limit, hosts):
        if time.monotonic() >= deadline or (cancelled is not None and cancelled.is_set()):
            raise TimeoutError('Product lookup finished')
        return original_download(url, limit, hosts)
    # Stable manufacturer gallery URL for the explicitly identified PURE XT.
    if (product['kind'] == 'gpu' and product['vendor'].lower() == 'sapphire' and
            re.sub(r'[^a-z0-9]', '', product['model'].lower()) == 'sapphirepureradeonrx9070xt'):
        try:
            raw = download(SAPPHIRE_PURE_IMAGE, MAX_IMAGE, domains(product))
            return cache.save(product, raw, SAPPHIRE_PURE_PAGE, SAPPHIRE_PURE_IMAGE)
        except (OSError, ValueError):
            pass
    try:
        pages = search_pages(product, download)
    except (OSError, ValueError, ET.ParseError):
        pages = []
    for source in pages:
        try:
            page = ProductPage()
            page.feed(download(source, MAX_PAGE, domains(product)).decode('utf-8', 'replace'))
            if not any(matches_product(product, title) for title in page.titles):
                continue
            # Metadata may point at a brand-wide logo. Prefer actual product
            # galleries and never accept logo/icon/banner assets as the card.
            images = list(dict.fromkeys(page.images + [url for url in page.gallery
                         if matches_product(product, url)]))
            for image in images[:8]:
                image = urljoin(source, image)
                if not allowed_url(image, domains(product)) or any(
                        word in urlsplit(image).path.lower() for word in ('logo', 'icon', 'banner')):
                    continue
                try:
                    raw = download(image, MAX_IMAGE, domains(product))
                    if valid_image(raw):
                        return cache.save(product, raw, source, image)
                except (OSError, ValueError):
                    continue
        except (OSError, ValueError):
            continue
    try:
        for source, image in search_images(product, download):
            try:
                raw = download(image, MAX_IMAGE, domains(product))
                if valid_image(raw):
                    return cache.save(product, raw, source, image)
            except (OSError, ValueError):
                continue
    except (OSError, ValueError):
        pass
    return None
