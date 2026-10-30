"""Start the detected launcher without leaking Vitalux's private runtime paths."""
import os
from pathlib import Path
import shutil
import subprocess

from .process_environment import host_environment as environment
FLATPAK={'steam':'com.valvesoftware.Steam','heroic':'com.heroicgameslauncher.hgl','lutris':'net.lutris.Lutris'}


def command(game, env):
    uri=game.get('launcher_uri','')
    store=game['store']
    if store not in FLATPAK or not uri:raise ValueError('Der Spiele-Launcher konnte nicht geöffnet werden.')
    if game.get('flatpak'):
        binary=shutil.which('flatpak',path=env.get('PATH',os.defpath))
        if not binary:raise ValueError('Der Spiele-Launcher konnte nicht geöffnet werden.')
        return [binary,'run',FLATPAK[store],uri]
    binary=shutil.which(store,path=env.get('PATH',os.defpath))
    return [binary,uri] if binary else []


def start(game):
    env=environment();args=command(game,env)
    if not args:
        # Keep URI-only launcher installations, but give the desktop dispatcher
        # the same clean environment and disconnected handles as direct starts.
        opener=shutil.which('xdg-open',path=env.get('PATH',os.defpath))
        if not opener:return False
        args=[opener,game['launcher_uri']]
    subprocess.Popen(args,cwd=Path.home(),env=env,stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                     close_fds=True,start_new_session=True)
    return True
