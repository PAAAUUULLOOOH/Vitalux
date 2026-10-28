"""Start the detected launcher without leaking Vitalux's private runtime paths."""
import os
from pathlib import Path
import shutil

from .process_environment import ROOT, host_environment as environment
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
    from PySide6.QtCore import QProcess,QProcessEnvironment,QUrl
    from PySide6.QtGui import QDesktopServices
    env=environment();args=command(game,env)
    if not args:return QDesktopServices.openUrl(QUrl(game['launcher_uri']))
    process=QProcess();process.setProgram(args[0]);process.setArguments(args[1:])
    process.setWorkingDirectory(str(Path.home()))
    child=QProcessEnvironment()
    for key,value in env.items():child.insert(key,value)
    process.setProcessEnvironment(child)
    result=process.startDetached()
    return result[0] if isinstance(result,tuple) else result
