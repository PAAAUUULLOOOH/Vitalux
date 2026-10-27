"""One cancellable background service for local game discovery and session work."""
from pathlib import Path
from queue import Empty, Queue
from threading import Event
import time
from PySide6.QtCore import QThread, Signal
from . import game_library, game_profiles
from .game_sessions import GameSessions


class GameService(QThread):
    catalog_ready = Signal(object)
    report_ready = Signal(object)
    session_finished = Signal(object)
    activity = Signal(object)
    failed = Signal(str)
    busy = Signal(bool)

    def __init__(self, parent=None, root=None, initial_games=None):
        super().__init__(parent)
        self.root = root
        self.initial_games = initial_games
        self.commands = Queue()
        self.cancelled = Event()
        self._scan_queued = False
        self.started_at = time.time()
        self._availability = {}

    def scan(self):
        if not self._scan_queued:
            self._scan_queued = True
            self.commands.put(('scan', None))

    def submit(self, operation, payload):
        self.commands.put((operation, payload))

    def shutdown(self):
        self.cancelled.set()
        self.requestInterruption()
        self.commands.put(('stop', None))
        return not self.isRunning()

    def _catalog(self, sessions):
        games = sessions.catalog()
        for game in games:
            game['mangohud_available'] = self._availability.get((game['store'], bool(game.get('flatpak'))), False)
        self.catalog_ready.emit(dict(games=games, sessions=sessions.summaries))

    def run(self):
        sessions = GameSessions(self.root)
        self._catalog(sessions)
        next_scan, next_monitor = 0., 0.
        deferred = []
        while not self.cancelled.is_set():
            try:
                operation, payload = self.commands.get(timeout=1.)
            except Empty:
                operation, payload = '', None
            if self.cancelled.is_set() or operation == 'stop':
                break
            try:
                if operation in ('connect', 'disconnect', 'profile'):
                    self.busy.emit(True)
                    game = payload
                    if operation == 'connect':
                        if not game_profiles.available(game):
                            raise ValueError('Die mitgelieferte Overlay-Komponente ist unvollständig. Bitte Vitalux erneut entpacken oder installieren.')
                        bridge = game_profiles.prepare(game)
                        game_profiles.connect(game, bridge)
                        sessions.register(game, bridge)
                    elif operation == 'disconnect':
                        connection = sessions.connections.get(game['id'])
                        if connection:
                            game_profiles.disconnect(game, Path(connection['root']))
                        sessions.unregister(game['id'])
                    else:
                        connection = sessions.connections.get(game['id'])
                        if connection:
                            game_profiles.prepare(connection['game'])
                        elif game_profiles.load(game['id'])['enabled']:
                            # Saving an enabled profile also establishes the
                            # actual launcher connection; a checkmark alone
                            # cannot inject an overlay into a game's process.
                            bridge=game_profiles.prepare(game)
                            game_profiles.connect(game,bridge)
                            sessions.register(game,bridge)
                    self._catalog(sessions)
                elif operation == 'report':
                    self.report_ready.emit(sessions.report(payload))
                if operation == 'scan' or time.monotonic() >= next_scan:
                    self._scan_queued = False
                    installed = self.initial_games if self.initial_games is not None else game_library.discover(cancelled=self.cancelled)
                    self.initial_games = None
                    sessions.update_inventory(installed)
                    # A full preferences reset returns overlay choices to
                    # defaults while retaining reversible launcher connections.
                    if next_scan == 0:
                        for connection in sessions.connections.values():
                            game_profiles.prepare(connection['game'])
                    available = {}
                    for game in installed:
                        key = (game['store'], bool(game.get('flatpak')))
                        if key not in available:
                            available[key] = game_profiles.available(game)
                    self._availability = available
                    self._catalog(sessions)
                    next_scan = time.monotonic()+60
                if time.monotonic() >= next_monitor:
                    pending = sessions.pending()
                    ready, running = sessions.ready(pending)
                    self.activity.emit(running)
                    for folder, metadata, logs in ready:
                        if self.cancelled.is_set():
                            break
                        report = sessions.finish(folder, metadata, logs, self.cancelled)
                        self._catalog(sessions)
                        if report['started'] >= self.started_at-5:
                            deferred.append(report)
                    if deferred and not running:
                        self.session_finished.emit(deferred[-1])
                        deferred.clear()
                    if ready:
                        sessions.prune_raw()
                    next_monitor = time.monotonic()+2
            except InterruptedError:
                break
            except Exception as error:
                if not self.cancelled.is_set():
                    self.failed.emit(str(error))
                if operation == 'scan':
                    self._scan_queued = False
                next_scan = max(next_scan, time.monotonic()+60)
                next_monitor = time.monotonic()+2
            finally:
                if operation in ('connect', 'disconnect', 'profile'):
                    self.busy.emit(False)
