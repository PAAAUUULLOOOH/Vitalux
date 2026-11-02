"""Private game catalog, bounded session reports and tracked MangoHud log files."""
import hashlib
import csv
import io
import os
from pathlib import Path
import time
import psutil
from . import game_files, game_reports, game_profiles, profiles

MAX_REPORTS = 200
RAW_BUDGET = 512*1024*1024


def _read(path, default=None):
    try:
        value = game_files.read_json(path)
        return value if isinstance(value, dict) else ({} if default is None else default)
    except (OSError, ValueError):
        return {} if default is None else default


def _pid_active(session):
    """A reused PID cannot keep an old session alive."""
    try:
        pid = int((session/'owner.pid').read_text())
        before = (session/'owner.stat').read_text().rsplit(')', 1)[1].split()[19]
        root = Path('/proc')/str(pid)
        if root.stat().st_uid != os.getuid():
            return False
        return root.joinpath('stat').read_text().rsplit(')', 1)[1].split()[19] == before
    except (OSError, ValueError, IndexError):
        return False


def has_frame_data(path):
    try:
        with path.open('rb') as stream:prefix=stream.read(8192)
        header=None
        for row in csv.reader(io.StringIO(prefix.decode('utf-8-sig','replace'))):
            names=[value.strip().casefold() for value in row]
            if 'fps' in names and 'frametime' in names:header=names;continue
            if header and len(row)==len(header):
                duration=game_reports.number(row[header.index('frametime')])
                fps=game_reports.number(row[header.index('fps')])
                if duration is not None and 0<duration<=60000 and fps is not None and fps>0:return True
    except (OSError,csv.Error):pass
    return False


def active_environments(wanted):
    """Inspect own-user processes only while there are actual pending sessions."""
    active = set()
    if not wanted:
        return active
    for process in psutil.process_iter(['uids']):
        try:
            if not process.info['uids'] or process.info['uids'].real != os.getuid():
                continue
            value = process.environ().get('VITALUX_GAME_SESSION')
            if value in wanted:
                active.add(value)
        except (psutil.Error, OSError, KeyError):
            continue
    return active


class GameSessions:
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else profiles.directory('state')/'games'
        self.report_folder = self.root/'reports'
        data = _read(self.root/'catalog.json')
        self.games = data.get('games', {}) if isinstance(data.get('games'), dict) else {}
        self.games={key:value for key,value in self.games.items()
                    if isinstance(value,dict) and value.get('id')==key
                    and isinstance(value.get('name'),str) and value.get('store') in ('steam','heroic','lutris')}
        self.connections = data.get('connections', {}) if isinstance(data.get('connections'), dict) else {}
        self.connections={key:value for key,value in self.connections.items()
                          if key in self.games and isinstance(value,dict) and isinstance(value.get('root'),str)
                          and Path(value['root']).is_absolute() and isinstance(value.get('game'),dict)
                          and value['game'].get('id')==key}
        index = _read(self.root/'sessions.json')
        self.summaries = index.get('sessions', []) if isinstance(index.get('sessions'), list) else []
        self.summaries = [row for row in self.summaries if isinstance(row, dict) and
                          isinstance(row.get('id'), str) and len(row['id']) == 32
                          and all(char in '0123456789abcdef' for char in row['id'])
                          and isinstance(row.get('game_id'),str)][:MAX_REPORTS]
        self._changed_files = {}
        self._session_roots = {}
        self._session_metadata = {}
        self.recording_games = set()

    def _save_catalog(self):
        game_files.write_json(self.root/'catalog.json', dict(schema=1, games=self.games, connections=self.connections))

    def update_inventory(self, installed):
        games = {key: dict(value, installed=False) for key, value in self.games.items()}
        for game in installed:
            connection=self.connections.get(game['id'])
            if connection and game.get('store')=='steam':
                previous=connection['game']
                variant=next((row for row in game.get('steam_installations',[])
                              if bool(row.get('flatpak'))==bool(previous.get('flatpak'))
                              and row.get('launcher_root')==previous.get('launcher_root')),None)
                if variant:game=dict(game,**variant)
            games[game['id']] = dict(game)
        if games != self.games:
            self.games = games
            self._save_catalog()

    def register(self, game, bridge):
        self.games[game['id']] = dict(game)
        self.connections[game['id']] = dict(root=str(bridge), game=dict(game))
        self._save_catalog()

    def unregister(self, game_id):
        self.connections.pop(game_id, None)
        self._save_catalog()

    def catalog(self):
        snapshots={}
        latest = {}
        for row in self.summaries:
            latest.setdefault(row['game_id'], row)
        result = []
        for game in self.games.values():
            item = dict(game)
            connection = self.connections.get(game['id'])
            root = Path(connection['root']) if connection else None
            item['connected'] = bool(root and game_profiles.connected(game,root,snapshots))
            item['overlay_enabled'] = bool(item['connected'] and (root/'enabled').is_file())
            item['latest'] = latest.get(game['id'])
            result.append(item)
        return sorted(result, key=lambda game: (not game.get('installed'), game['name'].casefold(), game['id']))

    def history(self, game_id):
        return [row for row in self.summaries if row.get('game_id') == game_id]

    def report(self, report_id):
        if len(report_id) != 32 or any(character not in '0123456789abcdef' for character in report_id):
            raise ValueError('Invalid game report identifier')
        return game_files.read_json(self.report_folder/(report_id+'.json'))

    def pending(self):
        result = []
        roots = set()
        for game_id, connection in list(self.connections.items())[:4096]:
            root = Path(connection['root'])/'sessions'
            roots.add(root)
            try:
                info = root.stat()
            except OSError:
                self._session_roots.pop(root, None)
                continue
            identity = (info.st_ino, info.st_mtime_ns)
            previous = self._session_roots.get(root)
            if previous is None or previous[0] != identity:
                candidates = set(sorted(root.glob('session.*'))[-1024:])
                self._session_roots[root] = identity, candidates
            else:
                candidates = previous[1]
            for session in list(candidates):
                if session.is_symlink() or not session.is_dir() or (session/'processed').exists():
                    candidates.discard(session)
                    self._session_metadata.pop(session, None)
                    continue
                metadata = self._session_metadata.get(session) or _read(session/'game.json')
                if (not isinstance(metadata.get('game'),dict) or metadata['game'].get('id') != game_id
                        or not isinstance(metadata.get('profile'),dict)):
                    continue
                self._session_metadata[session] = metadata
                result.append((session, metadata))
        for root in set(self._session_roots)-roots:self._session_roots.pop(root, None)
        present = {path for path, _ in result}
        for path in set(self._session_metadata)-present:self._session_metadata.pop(path, None)
        return result

    def ready(self, pending, now=None, active=None):
        now = time.monotonic() if now is None else now
        active = active_environments({str(path) for path, _ in pending}) if active is None else active
        ready, running = [], []
        self.recording_games.clear()
        for session, metadata in pending:
            if _pid_active(session) or str(session) in active:
                running.append(metadata['game']['id'])
                # A launcher connection/owner process is not proof of data.
                # Require actual header + frame bytes in a MangoHud CSV.
                for path in session.glob('*.csv'):
                    if path.is_symlink() or path.name.endswith('_summary.csv'):continue
                    if has_frame_data(path):
                        self.recording_games.add(metadata['game']['id']);break
                self._changed_files.pop(str(session), None)
                continue
            logs = sorted(path for path in session.glob('*.csv')
                          if not path.is_symlink() and not path.name.endswith('_summary.csv'))
            signature = tuple((path.name, path.stat().st_size, path.stat().st_mtime_ns) for path in logs)
            previous = self._changed_files.get(str(session))
            if previous is None or previous[0] != signature:
                self._changed_files[str(session)] = signature, now
                continue
            if now-previous[1] < 3:
                continue
            ready.append((session, metadata, logs))
        return ready, list(dict.fromkeys(running))

    def finish(self, session, metadata, logs, cancelled=None):
        try:
            successful = int((session/'exit-code').read_text()) == 0
        except (OSError, ValueError):
            successful = False
        report = game_reports.analyze_session(logs, target_fps=metadata.get('profile', {}).get('target_fps', 60),
                                      complete=successful, per_frame=metadata.get('per_frame') is True,
                                      cancelled=cancelled)
        try:
            started = float((session/'started').read_text())
        except (OSError, ValueError):
            started = session.stat().st_mtime
        try:
            wall_duration = float((session/'finished').read_text())-started
        except (OSError, ValueError):
            wall_duration = report['duration']
        if report['duration'] >= metadata.get('recording_limit', 14400)-5 and wall_duration > report['duration']+60:
            report['complete'] = False
            report['grade'] = 'incomplete'
            report['warnings'].append('recording_limit')
        report_id = hashlib.sha256(str(session.resolve()).encode()).hexdigest()[:32]
        report.update(id=report_id, game_id=metadata['game']['id'], game_name=metadata['game']['name'],
                      store=metadata['game']['store'], started=started, game_duration=max(0, wall_duration),
                      finished=time.time(), raw_folder=str(session))
        game_files.write_json(self.report_folder/(report_id+'.json'), report)
        summary = {key: value for key, value in report.items() if key != 'plot'}
        self.summaries = [summary]+[row for row in self.summaries if row['id'] != report_id]
        removed, self.summaries = self.summaries[MAX_REPORTS:], self.summaries[:MAX_REPORTS]
        game_files.write_json(self.root/'sessions.json', dict(schema=1, sessions=self.summaries))
        game_files.atomic_write(session/'processed', (report_id+'\n').encode())
        self._changed_files.pop(str(session), None)
        for old in removed:
            path = self.report_folder/(old['id']+'.json')
            if path.parent == self.report_folder and len(old['id']) == 32 and path.suffix == '.json':
                path.unlink(missing_ok=True)
        return report

    def prune_raw(self):
        """Only completed CSVs inside registered private session roots are pruned."""
        files, total = [], 0
        for connection in self.connections.values():
            root = Path(connection['root'])/'sessions'
            for folder in root.glob('session.*'):
                if folder.is_symlink() or not (folder/'processed').is_file():
                    continue
                for path in folder.glob('*.csv'):
                    if path.is_symlink() or not path.is_file():
                        continue
                    size = path.stat().st_size
                    total += size
                    files.append((path.stat().st_mtime_ns, path, size))
        for _stamp, path, size in sorted(files):
            if total <= RAW_BUDGET:
                break
            path.unlink(missing_ok=True)
            total -= size
        # Remove only obsolete, recognised metadata after its CSVs are gone.
        # Retained reports and unknown files are never deleted by this cleanup.
        retained = {row['id'] for row in self.summaries}
        known = {'processed','game.json','started','finished','exit-code','owner.pid','owner.stat'}
        for connection in self.connections.values():
            for folder in (Path(connection['root'])/'sessions').glob('session.*'):
                try:
                    if folder.is_symlink() or time.time()-folder.stat().st_mtime < 30*86400:continue
                    marker = folder/'processed'
                    if not marker.is_file():continue
                    report_id=marker.read_text().strip()
                    expected_id=hashlib.sha256(str(folder.resolve()).encode()).hexdigest()[:32]
                    if report_id!=expected_id or report_id in retained:continue
                    entries = list(folder.iterdir())
                    if folder.stat().st_uid!=os.getuid():continue
                    if any(p.is_symlink() or not p.is_file() or p.name not in known
                           or p.stat().st_uid!=os.getuid() or time.time()-p.stat().st_mtime<30*86400 for p in entries):continue
                    for path in entries:path.unlink()
                    folder.rmdir()
                except OSError:continue
