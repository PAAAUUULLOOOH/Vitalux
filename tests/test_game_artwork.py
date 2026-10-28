"""Reject small/portrait art, recover from failures and retain offline capsules."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QColor,QImage
from vitalux.game_artwork import resolve,dimensions,GameArtworkLoader

app=QCoreApplication([])
with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary);cache=root/'cache'
    wide=root/'wide.png';portrait=root/'portrait.png';small=root/'small.png'
    for path,width,height in ((wide,616,353),(portrait,300,450),(small,184,69)):
        image=QImage(width,height,QImage.Format_RGB32);image.fill(QColor('#506080'))
        assert image.save(str(path))
    game=dict(id='steam:42',store='steam',appid='42',cover=str(portrait))
    assert dimensions(portrait) is None and dimensions(small) is None
    assert resolve(game,cache=cache,offline=True)==''
    assert resolve(dict(game,cover=str(wide)),cache=cache,offline=True)==str(wide)
    steam=root/'Steam';capsule=steam/'appcache/librarycache/45/capsule_616x353.jpg'
    capsule.parent.mkdir(parents=True)
    image=QImage(616,353,QImage.Format_RGB32);image.fill(QColor('#506080'));image.save(str(capsule))
    hero=root/'hero.jpg';image=QImage(1920,620,QImage.Format_RGB32);image.fill(QColor('#506080'));image.save(str(hero))
    local=dict(game,id='steam:45',appid='45',launcher_root=str(steam),cover=str(hero))
    assert resolve(local,cache=cache,offline=True)==str(capsule),'Large hero displaced the properly shaped capsule'
    assert dimensions(hero) is None,'Very flat hero artwork was accepted as a capsule'
    hashed=steam/'appcache/librarycache/46/0123_header.jpg';hashed.parent.mkdir()
    image=QImage(920,430,QImage.Format_RGB32);image.fill(QColor('#506080'));image.save(str(hashed))
    assert resolve(dict(local,id='steam:46',appid='46',cover=''),cache=cache,offline=True)==str(hashed)

    class Response(io.BytesIO):
        def geturl(self):return 'https://shared.akamai.steamstatic.com/capsule.jpg'

    requests=[]
    def fetch(request,timeout):
        requests.append(request.full_url)
        return Response(small.read_bytes() if len(requests)==1 else wide.read_bytes())
    cached=resolve(game,cache=cache,fetch=fetch)
    assert cached and len(requests)>=2,'An unusable first image suppressed the fallback'
    assert Path(cached).read_bytes()==wide.read_bytes()
    def forbidden(*args,**kwargs):raise AssertionError('Unnecessary network access')
    assert resolve(game,cache=cache,offline=True,fetch=forbidden)==cached
    assert resolve(game,cache=cache,fetch=forbidden)==cached
    assert resolve(dict(game,id='lutris:1',store='lutris'),cache=cache,fetch=forbidden)==''
    class StoreResponse(io.BytesIO):
        def geturl(self):return 'https://store.steampowered.com/api/appdetails?appids=47'
    modern_url='https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/47/hash/header.jpg'
    requested=[]
    def modern(request,timeout):
        requested.append(request.full_url)
        if 'api/appdetails' in request.full_url:
            return StoreResponse(json.dumps({'47':{'success':True,'data':{'header_image':modern_url}}}).encode())
        if request.full_url==modern_url:return Response(wide.read_bytes())
        raise OSError('Legacy image address missing')
    assert resolve(dict(game,id='steam:47',appid='47'),cache=cache,fetch=modern)
    assert modern_url in requested

    # A failed or malformed lookup must neither crash nor retry on every scan.
    other=dict(game,id='steam:43',appid='43')
    def failed(*args,**kwargs):raise OSError('Offline')
    assert resolve(other,cache=cache,fetch=failed)==''
    assert resolve(other,cache=cache,fetch=forbidden)==''
    key=hashlib.sha256(other['id'].encode()).hexdigest()[:32]
    (cache/(key+'.json')).write_text('[]')
    assert resolve(other,cache=cache,fetch=lambda *a,**k:Response(wide.read_bytes()))
    assert not list(cache.glob('*.part'))
    try:resolve(dict(game,id='steam:44',appid='44'),cache=cache,cancelled=lambda:True)
    except InterruptedError:pass
    else:raise AssertionError('Hidden-page cancellation was ignored')
    # Paging back to an image evicted by the bounded cache must reload it now.
    loader=GameArtworkLoader();received=[];loader.ready.connect(lambda *value:received.append(value))
    loader._seen[game['id']]=(time.monotonic()+3600,str(root/'evicted.img'))
    with patch('vitalux.game_artwork.resolve',return_value=str(wide)):
        try:
            loader.request([game]);deadline=time.monotonic()+3
            while not received and time.monotonic()<deadline:app.processEvents();time.sleep(.005)
            assert received==[(game['id'],str(wide))],'Evicted image remained suppressed for an hour'
        finally:loader.shutdown();assert loader.wait(3000)
print('Wide-art fallback, portrait rejection, offline reuse, retry backoff, damaged metadata and cancellation PASS')
