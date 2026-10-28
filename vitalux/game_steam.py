"""Orderly Steam restarts for explicit overlay setup; never stop a live game."""
import os
import subprocess
import time

import psutil
from . import game_launch

CLIENT_NAMES={'steam','steamwebhelper'}


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
    request=subprocess.Popen(command,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                             start_new_session=True)
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
