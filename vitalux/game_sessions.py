"""Private game catalog, bounded session reports and tracked MangoHud log files."""
import hashlib
import os
from pathlib import Path
import time
import psutil
from . import game_files, game_reports, profiles

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

    def _save_catalog(self):
        game_files.write_json(self.root/'catalog.json', dict(schema=1, games=self.games, connections=self.connections))

    def update_inventory(self, installed):
        games = {key: dict(value, installed=False) for key, value in self.games.items()}
        for game in installed:
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
        latest = {}
        for row in self.summaries:
            latest.setdefault(row['game_id'], row)
        result = []
        for game in self.games.values():
            item = dict(game)
            connection = self.connections.get(game['id'])
            root = Path(connection['root']) if connection else None
            item['connected'] = bool(root and (root/'connection.json').is_file())
            item['overlay_enabled'] = bool(root and (root/'enabled').is_file())
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
        for game_id, connection in list(self.connections.items())[:4096]:
            root = Path(connection['root'])/'sessions'
            if not root.is_dir():
                continue
            for session in sorted(root.glob('session.*'))[-1024:]:
                if session.is_symlink() or not session.is_dir() or (session/'processed').exists():
                    continue
                metadata = _read(session/'game.json')
                if (not isinstance(metadata.get('game'),dict) or metadata['game'].get('id') != game_id
                        or not isinstance(metadata.get('profile'),dict)):
                    continue
                result.append((session, metadata))
        return result

    def ready(self, pending, now=None, active=None):
        now = time.monotonic() if now is None else now
        active = active_environments({str(path) for path, _ in pending}) if active is None else active
        ready, running = [], []
        for session, metadata in pending:
            if _pid_active(session) or str(session) in active:
                running.append(metadata['game']['id'])
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
