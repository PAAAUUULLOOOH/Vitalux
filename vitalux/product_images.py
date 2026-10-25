"""Find real manufacturer product images and keep a verified, persistent cache."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile
import ipaddress
from threading import Lock
import time
from urllib.parse import urlencode, urljoin, urlsplit, parse_qs, unquote
from urllib.request import Request, build_opener, HTTPRedirectHandler, HTTPSHandler
import xml.etree.ElementTree as ET

from . import profiles
from .hardware_identity import manufacturer, clean
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
    'corsair': ('corsair.com',), 'kingston': ('kingston.com',), 'crucial': ('crucial.com',),
    'g.skill': ('gskill.com',), 'samsung': ('samsung.com',), 'sk hynix': ('skhynix.com',),
    'teamgroup': ('teamgroupinc.com',), 'adata': ('adata.com',), 'patriot': ('patriotmemory.com',),
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
    if fields[0] not in ('gpu', 'mainboard', 'cpu', 'ram') or not all(fields[1:3]):
        return ''
    return hashlib.sha256(json.dumps(fields, ensure_ascii=True).encode()).hexdigest()


def domains(product):
    return DOMAINS.get(manufacturer(product.get('vendor')).lower(), ())


def allowed_url(url, hosts=()):
    try:
        value = urlsplit(url)
        host = (value.hostname or '').rstrip('.').lower()
        if (not host or '.' not in host or host.endswith(('.local','.internal','.localhost','.invalid','.test','.example')) or
                host in ('localhost','metadata.google.internal')):return False
        try:
            if not ipaddress.ip_address(host).is_global:return False
        except ValueError:pass
        return (value.scheme == 'https' and value.port in (None, 443) and
                not value.username and not value.password and
                (not hosts or any(host == item or host.endswith('.' + item) for item in hosts)))
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
            if not allowed_url(meta.get('source', '')) or not cutout_image(raw):
                return None
            return dict(meta, path=str(path), cached=True)
        except (OSError, ValueError, TypeError, AttributeError):
            return None

    def save(self, product, raw, source, image_url):
        key = product_key(product)
        if not key or not cutout_image(raw):
            raise ValueError('Invalid product image')
        if not all(allowed_url(url) for url in (source, image_url)):
            raise ValueError('Unsupported manufacturer source')
        meta = {'key': key, 'source': source, 'image_url': image_url,
                'sha256': hashlib.sha256(raw).hexdigest(), 'saved': int(time.time()),
                'vendor': product['vendor'], 'model': product['model'], 'cutout': True}
        path = self.root / (key + '.image')
        _atomic_bytes(path, raw)
        _atomic_bytes(self.root / (key + '.json'), json.dumps(meta).encode())
        return dict(meta, path=str(path), cached=False)


def cutout_image(raw):
    """Require a real transparent surround, never just a PNG filename/alpha flag."""
    from PySide6.QtGui import QImage
    from PySide6.QtCore import Qt
    if not valid_image(raw):return False
    image = QImage.fromData(raw)
    if not image.hasAlphaChannel():return False
    image = image.scaled(96,96,Qt.KeepAspectRatio,Qt.SmoothTransformation)
    width,height = image.width(),image.height()
    clear=solid=border_clear=border_count=0
    for y in range(height):
        for x in range(width):
            alpha=image.pixelColor(x,y).alpha()
            clear += alpha < 12
            solid += alpha > 220
            if x in (0,width-1) or y in (0,height-1):
                border_count+=1;border_clear+=alpha<20
    pixels=max(1,width*height)
    return clear/pixels>=.035 and solid/pixels>=.025 and border_clear/max(1,border_count)>=.60


def search_model(product):
    value=clean(product.get('model'))
    if product.get('kind')=='mainboard':
        value=re.sub(r'\s*\(MS-[A-Z0-9]+\)', '', value, flags=re.I)
        value=re.sub(r'\s+(?:rev(?:ision)?\.?\s*[:.]?\s*\d+(?:\.\d+)*)$', '', value, flags=re.I)
    if product.get('kind')=='cpu':
        value=re.sub(r'\s+@\s*\d+(?:\.\d+)?\s*[GM]Hz\b.*$', '', value, flags=re.I)
        value=re.sub(r'\b\d+[- ]Core(?:\s+Processor)?\b', '', value, flags=re.I)
    return re.sub(r'\s+', ' ', re.sub(r'\((?:R|TM)\)|[®™]', '', value, flags=re.I)).strip()


def matches_product(product, title):
    def words(value):return set(re.findall(r'[a-z]+|\d+',str(value).casefold()))
    ignored=words(manufacturer(product.get('vendor'))) | {'amd','radeon','nvidia','geforce','graphics','card','gpu','processor','cpu'}
    required=words(search_model(product))-ignored
    actual=words(title)
    if not required or not required<=actual:return False
    if re.search(r'\b(?:vs\.?|versus|comparison)\b',str(title),re.I):return False
    if product['kind'] in ('mainboard','ram','cpu'):
        def codes(value):
            return {re.sub(r'[^a-z0-9]','',word.lower()) for word in
                    re.findall(r'\b[a-z]+[a-z0-9-]*\d[a-z0-9-]*\b',str(value),re.I)}
        expected=codes(search_model(product))
        if expected and not expected<=codes(title):return False
    if product['kind']=='gpu':
        for variant in ('xt','xtx','super','ti','gre'):
            if (variant in required)!=(variant in actual):return False
    return True


class ProductPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.titles,self.images,self.gallery,self.named_images=[],[],[],[]
        self.in_title=False;self.json_script=False;self.json_data=[]

    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='title':self.in_title=True
        if tag=='script' and attrs.get('type','').lower()=='application/ld+json':
            self.json_script=True;self.json_data=[]
        if tag=='meta':
            field=(attrs.get('property') or attrs.get('name') or '').lower()
            if field in ('og:image','og:image:secure_url','twitter:image','twitter:image:src'):
                self.images.append(attrs.get('content',''))
            elif field in ('og:title','twitter:title'):self.titles.append(attrs.get('content',''))
        if tag=='img':
            src=attrs.get('src') or attrs.get('data-src') or ''
            self.gallery.append((src,attrs.get('alt','')))

    def handle_endtag(self, tag):
        if tag=='title':self.in_title=False
        if tag=='script' and self.json_script:
            self.json_script=False
            try:self._product(json.loads(''.join(self.json_data)))
            except (ValueError,RecursionError):pass

    def _product(self, data, depth=0):
        if depth>12:return
        if isinstance(data,list):
            for item in data[:100]:self._product(item,depth+1)
        elif isinstance(data,dict):
            types=data.get('@type',[])
            if isinstance(types,str):types=[types]
            if 'Product' in types:
                name=str(data.get('name',''))
                images=data.get('image',[])
                if not isinstance(images,list):images=[images]
                for image in images:
                    if isinstance(image,dict):image=image.get('contentUrl') or image.get('url') or ''
                    if isinstance(image,str):self.named_images.append((name,image))
            if '@graph' in data:self._product(data['@graph'],depth+1)

    def handle_data(self, data):
        if self.in_title:self.titles.append(data)
        if self.json_script:self.json_data.append(data)


class SearchPage(HTMLParser):
    def __init__(self):
        super().__init__();self.results=[];self.link='';self.title=[];self.in_link=False
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='a' and 'result__a' in attrs.get('class',''):
            link=attrs.get('href','')
            if 'duckduckgo.com/l/' in link:link=parse_qs(urlsplit('https:'+link if link.startswith('//') else link).query).get('uddg',[''])[0]
            self.link=link;self.title=[];self.in_link=True
    def handle_data(self, data):
        if self.in_link:self.title.append(data)
    def handle_endtag(self, tag):
        if tag=='a' and self.in_link:
            self.results.append((self.link,''.join(self.title)));self.in_link=False


def search_pages(product, download=fetch):
    query=f'{manufacturer(product["vendor"])} {search_model(product)}'
    candidates=[]
    try:
        url='https://www.bing.com/search?'+urlencode({'format':'rss','q':query})
        document=ET.fromstring(download(url,MAX_PAGE,('bing.com',)))
        candidates=[(item.findtext('link') or '',item.findtext('title') or '') for item in document.findall('.//item')]
    except (OSError,ValueError,ET.ParseError):pass
    result=[link for link,title in candidates if allowed_url(link) and matches_product(product,title)]
    if not result:
        try:
            url='https://html.duckduckgo.com/html/?'+urlencode({'q':query})
            page=SearchPage();page.feed(download(url,MAX_PAGE,('duckduckgo.com',)).decode('utf-8','replace'))
            result=[link for link,title in page.results if allowed_url(link) and matches_product(product,title)]
        except (OSError,ValueError):pass
    return sorted(dict.fromkeys(result),key=lambda url:0 if allowed_url(url,domains(product)) and domains(product) else 1)[:4]


class ImageSearch(HTMLParser):
    def __init__(self):super().__init__();self.results=[]
    def handle_starttag(self, tag, attrs):
        value=dict(attrs).get('m')
        if value and len(value)<20000:
            try:
                item=json.loads(value)
                if isinstance(item,dict):self.results.append(item)
            except ValueError:pass


def search_images(product, download=fetch):
    query=f'{manufacturer(product["vendor"])} {search_model(product)} product transparent png'
    url='https://www.bing.com/images/search?'+urlencode({'q':query,'qft':'+filterui:photo-transparent'})
    page=ImageSearch();page.feed(download(url,MAX_PAGE,('bing.com',)).decode('utf-8','replace'))
    result=[]
    for item in page.results[:60]:
        source,image=item.get('purl',''),item.get('murl','')
        if (allowed_url(source) and allowed_url(image) and
                (matches_product(product,item.get('t','')) or matches_product(product,unquote(urlsplit(source).path)))):
            result.append((source,image))
    return sorted(dict.fromkeys(result),key=lambda row:0 if domains(product) and allowed_url(row[0],domains(product)) else 1)[:6]


_refresh_lock=Lock()
_refreshed=False

def refresh_pci(cache, download):
    global _refreshed
    with _refresh_lock:
        if _refreshed:return
        _refreshed=True
        try:
            raw=download('https://raw.githubusercontent.com/pciutils/pciids/master/pci.ids',5*1024*1024,('raw.githubusercontent.com',))
            if raw.startswith(b'#') and b'List of PCI ID' in raw[:200] and b'1002 ' in raw:
                _atomic_bytes(cache.root/'pci.ids',raw)
        except (OSError,ValueError):pass


def lookup_key(product):
    key=product_key(product)
    ids=product.get('pci_ids','') if product else ''
    if key:return key
    if re.fullmatch(r'(?:[a-f0-9]{4}:){3}[a-f0-9]{4}',ids):
        return hashlib.sha256(('pci:'+ids).encode()).hexdigest()
    return ''


def resolve(product, cache=None, download=fetch, cancelled=None):
    cache=cache or ProductCache()
    saved=cache.load(product)
    if saved:return saved
    if not product:return None
    if not product_key(product):
        if lookup_key(product):refresh_pci(cache,download)
        return None
    deadline=time.monotonic()+35
    original_download=download
    def download(url,limit,hosts=()):
        if time.monotonic()>=deadline or (cancelled is not None and cancelled.is_set()):
            raise TimeoutError('Product lookup finished')
        return original_download(url,limit,hosts)
    def image_result(source,image):
        if not allowed_url(image):return None
        if re.search(r'(?:^|[/_.-])(?:logo|icon|banner|box|packaging)(?:[/_.-]|$)',urlsplit(image).path,re.I):return None
        try:
            raw=download(image,MAX_IMAGE,())
            if cutout_image(raw):return cache.save(product,raw,source,image)
        except (OSError,ValueError):pass
        return None
    # The same known source is revalidated: an opaque old photo must never be
    # displayed merely because it was cached by an earlier Vitalux version.
    if product['kind']=='gpu' and re.sub(r'[^a-z0-9]','',product['model'].lower())=='sapphirepureradeonrx9070xt':
        saved=image_result(SAPPHIRE_PURE_PAGE,SAPPHIRE_PURE_IMAGE)
        if saved:return saved
    try:pages=search_pages(product,download)
    except (OSError,ValueError):pages=[]
    for source in pages:
        try:
            page=ProductPage();page.feed(download(source,MAX_PAGE,()).decode('utf-8','replace'))
            if not any(matches_product(product,title) for title in page.titles):continue
            images=[url for name,url in page.named_images if matches_product(product,name)]
            images+=page.images+[url for url,alt in page.gallery if matches_product(product,alt) or matches_product(product,unquote(url))]
            for image in list(dict.fromkeys(images))[:6]:
                saved=image_result(source,urljoin(source,image))
                if saved:return saved
        except (OSError,ValueError):continue
    try:
        for source,image in search_images(product,download):
            saved=image_result(source,image)
            if saved:return saved
    except (OSError,ValueError):pass
    return None
