"""Orderly Steam restarts for explicit overlay setup; never stop a live game."""
import os
from pathlib import Path
import subprocess
import time

import psutil
from . import game_launch

CLIENT_NAMES={'steam','steamwebhelper'}


def resolve(game):
    """Match discovered variants to an own-user client, never discovery order."""
    candidates=[]
    for item in [game,*game.get('steam_installations',[])]:
        key=(bool(item.get('flatpak')),str(Path(item['launcher_root']).resolve()))
        if not any(key==(bool(row.get('flatpak')),str(Path(row['launcher_root']).resolve())) for row in candidates):
            candidates.append(item)
    clients=[]
    for flatpak in (False,True):
        for process,env in _processes(dict(game,flatpak=flatpak)):
            if (process.info['name'] or '').lower() not in CLIENT_NAMES:continue
            paths=[]
            for getter in (process.exe,process.cwd):
                try:paths.append(Path(getter()).resolve())
                except (psutil.Error,OSError):pass
            for name in ('STEAM_COMPAT_CLIENT_INSTALL_PATH','STEAMROOT','STEAM_HOME'):
                if env.get(name) and Path(env[name]).is_absolute():paths.append(Path(env[name]).resolve())
            clients.append((flatpak,paths))
    kinds={kind for kind,_ in clients}
    if len(kinds)>1:
        raise ValueError('Mehrere Steam-Installationen laufen gleichzeitig. Bitte schließe die nicht verwendete Installation.')
    if not kinds:return dict(game)
    matching=[row for row in candidates if bool(row.get('flatpak')) in kinds]
    located=[row for row in matching if any(path.is_relative_to(Path(row['launcher_root']).resolve())
             for kind,paths in clients for path in paths)]
    if located:matching=located
    if len(matching)!=1:
        raise ValueError('Das Spiel konnte der laufenden Steam-Installation nicht eindeutig zugeordnet werden. Bitte prüfe die Steam-Bibliothek und erkenne die Spiele erneut.')
    return dict(game,**matching[0])


def _processes(game):
    for process in psutil.process_iter(['name','uids','status']):
        try:
            if not process.info['uids'] or process.info['uids'].real!=os.getuid():continue
            if process.info['status'] in (psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD):continue
            try:env=process.environ()
            except psutil.AccessDenied:
                if (process.info['name'] or '').lower() in CLIENT_NAMES:
                    raise ValueError('Der Steam-Status konnte nicht zuverlässig geprüft werden. Bitte Steam einmal selbst beenden.')
                continue
            if bool(env.get('FLATPAK_ID')=='com.valvesoftware.Steam')!=bool(game.get('flatpak')):continue
            yield process,env
        except (psutil.Error,OSError):continue


def running(game):
    return any((process.info['name'] or '').lower() in CLIENT_NAMES for process,env in _processes(game))


def playing(game):
    for process,env in _processes(game):
        if (process.info['name'] or '').lower() in CLIENT_NAMES:continue
        if any(str(env.get(key,'')).isdecimal() and int(env[key])>0
               for key in ('SteamAppId','SteamGameId','STEAM_COMPAT_APP_ID')):return True
    return False


def open_client(game):
    return game_launch.start(dict(game,launcher_uri='steam://open/main'))


def resume(game,cancelled,progress,verify=None,timeout=20):
    """Recheck persisted options after the restarted client has read them."""
    progress('Steam wird wieder geöffnet …')
    if not open_client(game):
        raise ValueError('Steam konnte nach der Einrichtung nicht wieder geöffnet werden.')
    deadline=time.monotonic()+timeout
    while not running(game):
        if cancelled.is_set():raise InterruptedError()
        if time.monotonic()>=deadline:
            raise ValueError('Steam ist noch nicht bereit. Bitte öffne Steam und versuche den Spielstart erneut.')
        cancelled.wait(.1)
    progress('Steam-Startoptionen werden geprüft …')
    until=time.monotonic()+1.5
    while True:
        if cancelled.is_set():raise InterruptedError()
        if verify is not None and not verify():
            raise ValueError('Steam hat die Overlay-Startoptionen nicht übernommen. Das Spiel wurde nicht gestartet. Bitte prüfe das aktive Steam-Konto und die Zugriffsrechte.')
        if time.monotonic()>=until:return
        cancelled.wait(.1)


def stop_for_setup(game,cancelled,progress):
    if game.get('store')!='steam' or not running(game):return False
    if playing(game):
        raise ValueError('Beende zuerst laufende Steam-Spiele. Danach kann Vitalux Steam für die Overlay-Einrichtung neu starten.')
    if cancelled.is_set():raise InterruptedError()
    env=game_launch.environment()
    command=game_launch.command(dict(game,launcher_uri='-shutdown'),env)
    if not command:raise ValueError('Steam konnte für die Overlay-Einrichtung nicht neu gestartet werden.')
    progress('Steam wird für die Overlay-Einrichtung beendet …')
    # This is Steam's own shutdown request, not a signal to its processes.
    request=subprocess.Popen(command,env=env,stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                             close_fds=True,start_new_session=True)
    deadline=time.monotonic()+45
    while running(game):
        if time.monotonic()>deadline:
            raise ValueError('Steam wurde nicht rechtzeitig beendet. Bitte schließe offene Steam-Dialoge und versuche es erneut.')
        if request.poll() not in (None,0):
            raise ValueError('Steam konnte für die Overlay-Einrichtung nicht neu gestartet werden.')
        # Once shutdown was requested, wait for the final settings flush even
        # when Vitalux closes. Reopening too early can race Steam's shutdown.
        if cancelled.wait(.15):time.sleep(.15)
    if cancelled.is_set():
        open_client(game)
        raise InterruptedError()
    progress('Overlay-Verbindung wird eingerichtet …')
    return True
