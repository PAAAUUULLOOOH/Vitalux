"""Read-only installed-game discovery for native/Flatpak Steam, Heroic and Lutris."""
import hashlib
import os
from pathlib import Path
import re
from urllib.parse import quote
from . import game_files

_RUNTIME = re.compile(r'^(?:Steam Linux Runtime|Steamworks Common Redistributables|Proton(?:\s|$))', re.I)


def identity(store, appid):
    value = str(appid)
    if not re.fullmatch(r'[\w.:-]{1,180}', value, re.ASCII):
        raise ValueError('Invalid installed game identifier')
    return store + ':' + value


def file_key(game_id):
    return hashlib.sha256(game_id.encode()).hexdigest()[:24]


def _directory(value, base=None):
    path = Path(str(value)).expanduser()
    if not path.is_absolute() and base is not None:
        path = Path(base)/path
    return path.resolve()


def _image(candidates):
    for path in candidates:
        if path.is_file() and path.stat().st_size <= 12*1024*1024:
            return str(path)
    return ''


def _steam(home, cancelled=None):
    roots = [(home/'.local/share/Steam', False), (home/'.steam/steam', False),
             (home/'.steam/root', False),
             (home/'.var/app/com.valvesoftware.Steam/.local/share/Steam', True),
             (home/'.var/app/com.valvesoftware.Steam/data/Steam', True)]
    seen = set()
    for root, flatpak in roots:
        root = root.resolve()
        if root in seen or not (root/'steamapps').is_dir():
            continue
        seen.add(root)
        libraries = [root]
        try:
            data = game_files.loads(game_files.read_text(root/'steamapps/libraryfolders.vdf'))
            entries = game_files.get(data, 'libraryfolders', {})
            for key, value in entries.items():
                if not key.isdecimal():
                    continue
                value = game_files.get(value, 'path', '') if isinstance(value, dict) else value
                if value:
                    path = _directory(value)
                    if path not in libraries:
                        libraries.append(path)
        except (OSError, ValueError, AttributeError):
            pass
        for library in libraries[:128]:
            for manifest in sorted((library/'steamapps').glob('appmanifest_*.acf'))[:12000]:
                if cancelled is not None and cancelled.is_set():raise InterruptedError()
                try:
                    data = game_files.get(game_files.loads(game_files.read_text(manifest)), 'AppState', {})
                    appid = str(game_files.get(data, 'appid', ''))
                    title = str(game_files.get(data, 'name', '')).strip()[:240]
                    directory = game_files.get(data, 'installdir', '')
                    if not isinstance(directory, str) or not directory.strip():
                        continue
                    install = _directory(directory, library/'steamapps/common')
                    state = int(game_files.get(data, 'StateFlags', '0'))
                    if (not appid.isdecimal() or not title or _RUNTIME.match(title)
                            or not state & 4 or not install.is_dir()):
                        continue
                    pictures = [root/'appcache/librarycache'/appid/'library_600x900.jpg',
                                root/'appcache/librarycache'/f'{appid}_library_600x900.jpg',
                                root/'appcache/librarycache'/f'{appid}_header.jpg']
                    yield dict(id=identity('steam', appid), store='steam', appid=appid, name=title,
                               install_path=str(install), launcher_root=str(root), flatpak=flatpak,
                               launcher_uri='steam://rungameid/'+appid, cover=_image(pictures),
                               manifest=str(manifest), installed=True)
                except (OSError, ValueError, TypeError, AttributeError):
                    continue


def _records(value):
    if isinstance(value, list):
        return [(str(index), row) for index, row in enumerate(value) if isinstance(row, dict)]
    if isinstance(value, dict):
        for field in ('installed', 'games'):
            if field in value:
                return _records(value[field])
        return [(str(key), row) for key, row in value.items() if isinstance(row, dict)]
    return []


def _heroic(home, config, cancelled=None):
    roots = [(config/'heroic', False),
             (home/'.var/app/com.heroicgameslauncher.hgl/config/heroic', True)]
    for root, flatpak in roots:
        for runner, files in (
                ('legendary', [root/'legendaryConfig/legendary/installed.json', config/'legendary/installed.json']),
                ('gog', [root/'gog_store/installed.json'])):
            for path in files:
                try:
                    rows = _records(game_files.read_json(path))
                except (OSError, ValueError):
                    continue
                for key, row in rows[:12000]:
                    if cancelled is not None and cancelled.is_set():raise InterruptedError()
                    appid = str(row.get('app_name') or row.get('appName') or row.get('id') or key)
                    title = str(row.get('title') or row.get('name') or row.get('appName') or appid)[:240]
                    location = row.get('install_path') or row.get('installPath') or row.get('path')
                    if not location or not Path(location).is_dir():
                        continue
                    try:
                        game_id = identity('heroic-'+runner, appid)
                    except ValueError:
                        continue
                    yield dict(id=game_id, store='heroic', runner=runner, appid=appid, name=title,
                               install_path=str(_directory(location)), launcher_root=str(root), flatpak=flatpak,
                               launcher_uri='heroic://launch/'+runner+'/'+quote(appid, safe=''),
                               cover='', manifest=str(path), installed=True)


def _lutris(home, config, data, cancelled=None):
    roots = [(config/'lutris', data/'lutris', False),
             (home/'.var/app/net.lutris.Lutris/config/lutris',
              home/'.var/app/net.lutris.Lutris/data/lutris', True)]
    try:
        import sqlite3
    except ImportError:
        return
    for configuration, storage, flatpak in roots:
        database = storage/'pga.db'
        if not database.is_file():
            continue
        try:
            with sqlite3.connect(database.as_uri()+'?mode=ro', uri=True, timeout=.4) as connection:
                connection.row_factory = sqlite3.Row
                rows = [dict(row) for row in connection.execute('SELECT * FROM games LIMIT 12000')]
        except (OSError, sqlite3.Error, ValueError):
            continue
        for row in rows:
            if cancelled is not None and cancelled.is_set():raise InterruptedError()
            appid = str(row.get('id') or '')
            location = row.get('directory')
            if not appid.isdecimal() or not location or not Path(location).is_dir() or row.get('installed') == 0:
                continue
            slug = str(row.get('slug') or '')
            config_file = str(row.get('configpath') or row.get('config_path') or '')
            if config_file and Path(config_file).name != config_file:
                config_file = ''
            yield dict(id=identity('lutris', appid), store='lutris', appid=appid,
                       name=str(row.get('name') or slug or appid)[:240], runner=str(row.get('runner') or ''),
                       install_path=str(_directory(location)), launcher_root=str(configuration), flatpak=flatpak,
                       launcher_uri='lutris:rungameid/'+appid,
                       config_file=str(configuration/'games'/(config_file if config_file.endswith('.yml') else config_file+'.yml')) if config_file else '',
                       cover=_image([storage/'coverart'/(slug+'.jpg'), storage/'icons'/(slug+'.png')]),
                       manifest=str(database), installed=True)


def discover(home=None, config=None, data=None, cancelled=None):
    """Return local installed games only, without changing any launcher state."""
    home = Path(home) if home is not None else Path.home()
    config = Path(config) if config is not None else Path(os.environ.get('XDG_CONFIG_HOME', home/'.config'))
    data = Path(data) if data is not None else Path(os.environ.get('XDG_DATA_HOME', home/'.local/share'))
    games = {}
    for iterator in (_steam(home,cancelled), _heroic(home,config,cancelled), _lutris(home,config,data,cancelled)):
        for game in iterator:
            games.setdefault(game['id'], game)
    return sorted(games.values(), key=lambda game: (game['name'].casefold(), game['id']))
