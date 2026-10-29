"""Per-game MangoHud profiles and reversible, explicit launcher connections."""
import json
import math
import os
from pathlib import Path
import re
import shlex
import psutil
from . import game_files, game_runtime, profiles, settings
from .game_library import file_key

METRICS = ('fps', 'frametime', 'frame_timing', 'cpu_stats', 'cpu_temp', 'cpu_power',
           'gpu_stats', 'gpu_temp', 'gpu_power', 'ram', 'vram', 'io_read', 'io_write')
DEFAULTS = dict(enabled=True, target_fps=60, position='top-left', font_size=20,
                background_alpha=.65, horizontal=False, warmup=5,
                toggle_hud='Shift_R+F12', toggle_logging='Shift_L+F2',
                metrics=['fps', 'frametime', 'frame_timing', 'gpu_stats', 'gpu_temp',
                         'cpu_stats', 'cpu_temp', 'ram', 'vram'])
POSITIONS = ('top-left', 'top-right', 'bottom-left', 'bottom-right', 'top-center', 'bottom-center')


def normalize(value):
    value = value if isinstance(value, dict) else {}
    result = dict(DEFAULTS)
    result['metrics'] = list(DEFAULTS['metrics'])
    for key in ('enabled', 'horizontal'):
        if type(value.get(key)) is bool:
            result[key] = value[key]
    for key, low, high in (('target_fps', 20, 1000), ('font_size', 12, 40), ('warmup', 1, 120)):
        if type(value.get(key)) in (int, float) and math.isfinite(value[key]):
            result[key] = max(low, min(high, int(value[key])))
    alpha = value.get('background_alpha')
    if type(alpha) in (int, float) and 0 <= alpha <= 1:
        result['background_alpha'] = float(alpha)
    if value.get('position') in POSITIONS:
        result['position'] = value['position']
    if isinstance(value.get('metrics'), list):
        result['metrics'] = [key for key in METRICS if key in value['metrics']]
    for key in ('toggle_hud', 'toggle_logging'):
        if re.fullmatch(r'(?:[A-Za-z0-9_]+\+)*[A-Za-z0-9_]+', str(value.get(key, ''))):
            result[key] = value[key][:120]
    return result


def load(game_id):
    entries = settings.get('game_overlay_profiles', {})
    return normalize(entries.get(game_id)) if isinstance(entries, dict) else normalize({})


def save(game_id, value):
    entries = settings.get('game_overlay_profiles', {})
    entries = entries if isinstance(entries, dict) else {}
    entries[game_id] = normalize(value)
    if not settings.set('game_overlay_profiles', entries):
        raise OSError('Overlay profile could not be saved')
    return entries[game_id]


def config_text(profile):
    profile = normalize(profile)
    values = ['permit_upload=0', 'legacy_layout=false', 'log_interval=0', 'log_duration=14400',
              'autostart_log='+str(max(1, profile['warmup'])),
              'position='+profile['position'], 'font_size='+str(profile['font_size']),
              'background_alpha='+str(profile['background_alpha']),
              'toggle_hud='+profile['toggle_hud'], 'toggle_logging='+profile['toggle_logging']]
    values.extend(profile['metrics'])
    if profile['horizontal']:
        values.append('horizontal')
    return '\n'.join(values)+'\n'


def launcher_running(store):
    names = {'steam': ('steam', 'steamwebhelper'), 'heroic': ('heroic',), 'lutris': ('lutris',)}[store]
    for process in psutil.process_iter(['name', 'uids', 'status']):
        try:
            if process.info.get('status') in (psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD):continue
            if process.info['uids'] and process.info['uids'].real != os.getuid():
                continue
            if (process.info['name'] or '').lower() in names:
                return True
        except (psutil.Error, OSError):
            pass
    return False


def available(game):
    return game_runtime.available()


def bridge_root(game, base=None):
    if base is not None:
        return Path(base)/file_key(game['id'])
    if game.get('flatpak'):
        app = {'steam': 'com.valvesoftware.Steam', 'heroic': 'com.heroicgameslauncher.hgl',
               'lutris': 'net.lutris.Lutris'}[game['store']]
        root = Path.home()/'.var/app'/app/'data/vitalux-overlay'/profiles.installed()
    else:
        root = profiles.directory('data')/'game-overlay'
    return root/file_key(game['id'])


def prepare(game, profile=None, base=None):
    profile = normalize(profile if profile is not None else load(game['id']))
    root = bridge_root(game, base)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    engine=game_runtime.ensure(root.parent/'engine')
    game_files.atomic_write(root/'profile.conf', config_text(profile).encode())
    game_files.write_json(root/'game.json', dict(game=game, profile=profile, per_frame=True, recording_limit=14400))
    if profile['enabled']:
        game_files.atomic_write(root/'enabled', b'1\n')
    else:
        (root/'enabled').unlink(missing_ok=True)
    values = dict(VITALUX_OVERLAY_CONFIG=str(root/'profile.conf'),
                  VITALUX_OVERLAY_META=str(root/'game.json'),
                  VITALUX_OVERLAY_ENABLED=str(root/'enabled'),
                  VITALUX_OVERLAY_SESSIONS=str(root/'sessions'),
                  VITALUX_OVERLAY_ENGINE=str(engine/'run'))
    template = (Path(__file__).resolve().parents[1]/'packaging/game-overlay.sh').read_text()
    script = '#!/bin/sh\n'+''.join(key+'='+shlex.quote(value)+'\n' for key, value in values.items())
    script += template.partition('\n')[2]
    game_files.atomic_write(root/'launch.sh', script.encode())
    (root/'launch.sh').chmod(0o700)
    return root


def _steam_path(game):
    from .game_steam_accounts import config_path
    return config_path(game)


def preflight_steam(game):
    """Validate the actual account before asking Steam to shut down."""
    path=_steam_path(game)
    game_files.loads(game_files.read_text(path))
    if not os.access(path,os.R_OK|os.W_OK) or not os.access(path.parent,os.W_OK|os.X_OK):
        raise ValueError('Die Steam-Spieleinstellungen sind nicht schreibbar. Bitte prüfe die Zugriffsrechte des Steam-Kontos.')
    return path


def connected(game, root=None, snapshots=None):
    """Read the actual launcher entry, rather than trusting a backup marker."""
    root=Path(root) if root is not None else bridge_root(game)
    record=profiles.read(root/'connection.json')
    launcher=str(root/'launch.sh')
    if record.get('launcher')!=launcher or not (root/'launch.sh').is_file():return False
    snapshots={} if snapshots is None else snapshots
    try:
        store=game['store']
        path=(_steam_path(game) if store=='steam' else
              Path(game['launcher_root'])/'GamesConfig'/(game['appid']+'.json') if store=='heroic' else
              Path(game['config_file']))
        if store=='steam' and record.get('path')!=str(path):return False
        key=(store,str(path))
        if key not in snapshots:
            text=game_files.read_text(path)
            snapshots[key]=game_files.loads(text) if store=='steam' else json.loads(text) if store=='heroic' else text
        data=snapshots[key]
        if store=='steam':
            for key in ('UserLocalConfigStore','Software','Valve','Steam','apps',game['appid'],'LaunchOptions'):
                data=game_files.get(data,key,{}) if isinstance(data,dict) else {}
            return isinstance(data,str) and launcher in shlex.split(data) and '%command%' in data
        if store=='heroic':
            return any(isinstance(item,dict) and item.get('exe')==launcher
                       for item in data.get(game['appid'],{}).get('wrapperOptions',[]))
        return launcher in shlex.split(_yaml_prefix(data)[0])
    except (OSError,ValueError,TypeError,KeyError,AttributeError):return False


def _yaml_prefix(text, value=None):
    """Edit one generated Lutris scalar, preserving the rest of its YAML."""
    section = re.search(r'^system:[ \t]*(?:#[^\n]*)?$', text, re.M)
    if section:
        tail = text[section.end():]
        following = re.search(r'\n[^\s#][^\n]*:', tail)
        end = section.end()+following.start() if following else len(text)
        match = re.search(r'^( +)prefix_command:[ \t]*(.*)$', text[section.end():end], re.M)
        if match:
            scalar = match[2].strip()
            if scalar.startswith('"'):
                old = json.loads(scalar)
            elif scalar.startswith("'") and scalar.endswith("'"):
                old = scalar[1:-1].replace("''", "'")
            elif scalar in ('', 'null', '~'):
                old = ''
            elif scalar.startswith(('|', '>', '{', '[')) or '#' in scalar:
                raise ValueError('Mehrzeilige Lutris-Startpräfixe bitte zuerst im Launcher vereinfachen.')
            else:
                old = scalar
            if value is None:
                return old, text
            start = section.end()+match.start(2)
            finish = section.end()+match.end(2)
            return old, text[:start]+json.dumps(value, ensure_ascii=False)+text[finish:]
        if value is None:
            return '', text
        return '', text[:end]+'\n  prefix_command: '+json.dumps(value)+'\n'+text[end:]
    if re.search(r'^system:', text, re.M):
        raise ValueError('Dieses Lutris-Konfigurationsformat kann nicht verlustfrei angepasst werden.')
    return ('', text if value is None else text.rstrip()+'\nsystem:\n  prefix_command: '+json.dumps(value)+'\n')


def connect(game, root=None, check_running=True):
    """Explicit UI operation; never called by library discovery."""
    if check_running and launcher_running(game['store']):
        raise ValueError('Beende den Spiele-Launcher vor dem Einrichten oder Entfernen der Verbindung.')
    root = Path(root) if root is not None else prepare(game)
    launcher = str(root/'launch.sh')
    prefix = shlex.quote(launcher)
    backup_path = root/'connection.json'
    old_connection = profiles.read(backup_path)
    store = game['store']
    if store == 'steam':
        path = _steam_path(game)
        raw = path.read_bytes()
        text = raw.decode('utf-8-sig')
        keys = ('UserLocalConfigStore', 'Software', 'Valve', 'Steam', 'apps', game['appid'], 'LaunchOptions')
        data = game_files.loads(text)
        for key in keys:
            data = game_files.get(data, key, {}) if isinstance(data, dict) else {}
        old = data if isinstance(data, str) else ''
        if prefix in old:
            if old_connection.get('launcher')==launcher:return old_connection
            applied=old
            old=old.replace(prefix+' ','',1)
        else:
            applied = (old.replace('%command%', prefix+' %command%', 1) if '%command%' in old
                       else prefix+' %command%'+(' '+old if old else ''))
        updated = game_files.set_string(text, keys, applied).encode()
        if raw.startswith(b'\xef\xbb\xbf'):
            updated = b'\xef\xbb\xbf'+updated
        connection = dict(store=store, path=str(path), original=old, applied=applied, launcher=launcher, keys=list(keys))
    elif store == 'heroic':
        path = Path(game['launcher_root'])/'GamesConfig'/(game['appid']+'.json')
        raw = path.read_bytes()
        data = json.loads(raw)
        config = data.get(game['appid'])
        if not isinstance(config, dict):
            raise ValueError('Öffne und speichere die Spieleinstellungen zuerst einmal in Heroic.')
        wrappers = config.get('wrapperOptions', [])
        if not isinstance(wrappers, list):
            raise ValueError('Ungültige Heroic-Startpräfixe')
        if any(isinstance(item, dict) and item.get('exe') == launcher for item in wrappers):
            if old_connection.get('launcher')==launcher:return old_connection
            original=[item for item in wrappers if not isinstance(item,dict) or item.get('exe')!=launcher]
        else:
            original = list(wrappers)
            config['wrapperOptions'] = [dict(exe=launcher, args='')]+wrappers
        updated = (json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode()
        connection = dict(store=store, path=str(path), original=original, launcher=launcher, appid=game['appid'])
    elif store == 'lutris':
        path = Path(game.get('config_file') or '')
        if not path.is_file():
            raise ValueError('Lutris-Spielekonfiguration nicht gefunden.')
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        original, _ = _yaml_prefix(text)
        if prefix in original:
            if old_connection.get('launcher')==launcher:return old_connection
            applied=original;original=original.replace(prefix+' ','',1).replace(prefix,'',1).strip()
        else:applied = prefix+(' '+original if original else '')
        _, changed = _yaml_prefix(text, applied)
        updated = changed.encode()
        connection = dict(store=store, path=str(path), original=original, applied=applied, launcher=launcher)
    else:
        raise ValueError('Dieser Launcher wird noch nicht unterstützt.')
    # Record recovery information before touching the external launcher file.
    game_files.write_json(backup_path, connection)
    try:
        game_files.atomic_write(path, updated, expected=raw)
    except BaseException:
        if old_connection:
            game_files.write_json(backup_path, old_connection)
        else:
            backup_path.unlink(missing_ok=True)
        raise
    return connection


def disconnect(game, root=None, check_running=True):
    if check_running and launcher_running(game['store']):
        raise ValueError('Beende den Spiele-Launcher vor dem Einrichten oder Entfernen der Verbindung.')
    root = Path(root) if root is not None else bridge_root(game)
    connection = game_files.read_json(root/'connection.json')
    path = Path(connection['path'])
    raw = path.read_bytes()
    launcher = connection['launcher']
    if connection['store'] == 'heroic':
        data = json.loads(raw)
        config = data.get(connection['appid'], {})
        wrappers = config.get('wrapperOptions', [])
        config['wrapperOptions'] = [item for item in wrappers if not isinstance(item, dict) or item.get('exe') != launcher]
        updated = (json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode()
    else:
        text = raw.decode('utf-8-sig')
        if connection['store'] == 'steam':
            value = game_files.loads(text)
            for key in connection['keys']:
                value = game_files.get(value, key, {}) if isinstance(value, dict) else {}
        else:
            value, _ = _yaml_prefix(text)
        if not isinstance(value, str):
            raise ValueError('Der Startpräfix wurde zwischenzeitlich verändert.')
        # Preserve additional user arguments and wrappers added after setup.
        if value == connection['applied']:
            value = connection['original']
        else:
            marker = shlex.quote(launcher)
            if value.count(marker) != 1:
                raise ValueError('Die Verbindung wurde im Launcher verändert; bitte dort prüfen.')
            value = value.replace(marker+' ', '', 1) if marker+' ' in value else value.replace(marker, '', 1).strip()
        if connection['store'] == 'steam':
            updated = game_files.set_string(text, connection['keys'], value).encode()
            if raw.startswith(b'\xef\xbb\xbf'):
                updated = b'\xef\xbb\xbf'+updated
        else:
            updated = _yaml_prefix(text, value)[1].encode()
    game_files.atomic_write(path, updated, expected=raw)
    (root/'enabled').unlink(missing_ok=True)
    (root/'connection.json').unlink(missing_ok=True)
