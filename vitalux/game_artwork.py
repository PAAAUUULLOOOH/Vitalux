"""Wide game capsules with bounded background retrieval and an offline cache."""
import hashlib
import json
from pathlib import Path
from queue import Queue
from threading import Event, Lock
import time
from urllib.parse import urlparse
import urllib.request
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QImageReader
from . import game_files, profiles

MAX_BYTES=8*1024*1024
CACHE_BYTES=64*1024*1024


def dimensions(path):
    try:
        path=Path(path)
        if not path.is_file() or path.stat().st_size>MAX_BYTES:return None
        reader=QImageReader(str(path));size=reader.size()
        if not size.isValid() or size.width()*size.height()>24_000_000:return None
        if size.width()<460 or size.height()<200 or not 1.3<=size.width()/size.height()<=2.6:return None
        return size
    except (OSError,ValueError):return None


def local_candidates(game):
    if game.get('store')=='steam' and str(game.get('appid','')).isdecimal():
        folder=Path(game.get('launcher_root',''))/'appcache/librarycache';appid=str(game['appid'])
        for name in ('capsule_616x353.jpg','header_2x.jpg','header.jpg','library_hero.jpg'):
            yield folder/appid/name
            yield folder/(appid+'_'+name)
        # Current Steam caches include content hashes in the filenames.
        for directory,pattern in ((folder/appid,'*'),(folder,appid+'_*')):
            for candidate in sorted(directory.glob(pattern))[:80]:
                if any(part in candidate.name.lower() for part in ('capsule_616','header')):yield candidate
    if game.get('cover'):yield Path(game['cover'])


def _remote(url):
    parsed=urlparse(url)
    return (parsed.scheme=='https' and not parsed.username and
            (parsed.hostname or '').endswith(('.steamstatic.com','.steamcontent.com')))


def resolve(game, cancelled=None, *, cache=None, offline=False, fetch=None):
    """Never replace a usable cached capsule with a failed network result."""
    cancelled=cancelled or (lambda:False)
    folder=Path(cache) if cache is not None else profiles.directory('cache')/'game-artwork'
    key=hashlib.sha256(game['id'].encode()).hexdigest()[:32]
    target=folder/(key+'.img');meta=folder/(key+'.json')
    if dimensions(target):return str(target)
    # Prefer a capsule over a larger but much flatter library-hero banner.
    # The latter would again look small inside the shared capsule-shaped area.
    for candidate in local_candidates(game):
        if dimensions(candidate):return str(candidate)
    if offline or game.get('store')!='steam' or not str(game.get('appid','')).isdecimal():return ''
    try:
        record=game_files.read_json(meta)
        if isinstance(record,dict) and record.get('schema')==2 and float(record.get('retry_after',0))>time.time():return ''
    except (OSError,ValueError,TypeError):pass
    appid=str(game['appid'])
    urls=[f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/capsule_616x353.jpg',
          f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/header_2x.jpg',
          f'https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg']
    def official_images():
        # Store metadata supplies modern hashed asset paths. No guessed image
        # search, scraped thumbnails, or unrelated game artwork is accepted.
        try:
            request=urllib.request.Request('https://store.steampowered.com/api/appdetails?appids='+appid,
                                          headers={'User-Agent':'Vitalux game artwork'})
            with (fetch or urllib.request.urlopen)(request,timeout=3) as response:
                if urlparse(response.geturl()).hostname!='store.steampowered.com':return []
                raw=response.read(1024*1024+1)
                if len(raw)>1024*1024:return []
                data=json.loads(raw).get(appid,{})
                data=data.get('data',{}) if data.get('success') else {}
            return [data[key] for key in ('capsule_image','header_image','capsule_imagev5')
                    if isinstance(data.get(key),str) and _remote(data[key])]
        except (OSError,ValueError,TypeError,AttributeError):return []
    folder.mkdir(parents=True,exist_ok=True)
    temporary=folder/(key+'.part')
    # Expand this same bounded list after the first legacy capsule misses.
    for index,url in enumerate(urls):
        if cancelled():raise InterruptedError()
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'Vitalux game artwork'})
            with (fetch or urllib.request.urlopen)(request,timeout=3) as response:
                if not _remote(response.geturl()):raise ValueError('Unexpected capsule source')
                total=0
                with temporary.open('wb') as stream:
                    while block:=response.read(64*1024):
                        if cancelled():raise InterruptedError()
                        total+=len(block)
                        if total>MAX_BYTES:raise ValueError('Capsule image exceeds its size limit')
                        stream.write(block)
            if not dimensions(temporary):raise ValueError('Capsule is missing or too small')
            reader=QImageReader(str(temporary));size=reader.size()
            if size.width()>1232 or size.height()>706:
                reader.setScaledSize(size.scaled(1232,706,Qt.KeepAspectRatio))
            if reader.read().isNull():raise ValueError('Invalid capsule image')
            temporary.replace(target)
            game_files.write_json(meta,dict(source=url,saved=time.time()))
            _prune(folder,target)
            return str(target)
        except (OSError,ValueError):pass
        finally:temporary.unlink(missing_ok=True)
        if index==0 and not cancelled():
            urls[1:1]=[candidate for candidate in official_images() if candidate not in urls]
    if not cancelled():game_files.write_json(meta,dict(schema=2,retry_after=time.time()+600))
    return ''


def _prune(folder, keep):
    files=sorted(folder.glob('*.img'),key=lambda p:p.stat().st_mtime,reverse=True)
    total=0
    for index,path in enumerate(files):
        total+=path.stat().st_size
        if path!=keep and (total>CACHE_BYTES or index>=128):
            path.unlink(missing_ok=True);path.with_suffix('.json').unlink(missing_ok=True)


class GameArtworkLoader(QThread):
    ready=Signal(str,str)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.cancelled=Event();self.jobs=Queue();self._lock=Lock()
        self._wanted=set();self._pending=set();self._seen={}

    def request(self,games):
        with self._lock:
            self._wanted={g['id'] for g in games}
            for game in games:
                key=game['id']
                seen=self._seen.get(key)
                if key in self._pending:continue
                if seen and seen[0]>time.monotonic() and (not seen[1] or Path(seen[1]).is_file()):continue
                self._pending.add(key);self.jobs.put(dict(game))
        if games and not self.cancelled.is_set() and not self.isRunning():self.start()

    def run(self):
        import os
        offline=bool(os.environ.get('VITALUX_SPEC_OFFLINE') or os.environ.get('VITALUX_GAME_ART_OFFLINE'))
        while not self.cancelled.is_set():
            game=self.jobs.get()
            if game is None:break
            key=game['id']
            def cancelled():
                with self._lock:return self.cancelled.is_set() or key not in self._wanted
            try:
                if cancelled():continue
                path=resolve(game,cancelled,offline=offline)
                with self._lock:self._seen[key]=(time.monotonic()+(3600 if path else 60),path)
                if not cancelled():self.ready.emit(key,path)
            except InterruptedError:pass
            except (OSError,ValueError):pass
            finally:
                with self._lock:self._pending.discard(key)

    def shutdown(self):
        self.cancelled.set();self.jobs.put(None)
        return not self.isRunning()

    def resume(self):
        if not self.isRunning():
            self.cancelled=Event();self.jobs=Queue();self._pending.clear()
