"""Start the detected launcher without leaking Vitalux's private runtime paths."""
import os
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
FLATPAK={'steam':'com.valvesoftware.Steam','heroic':'com.heroicgameslauncher.hgl','lutris':'net.lutris.Lutris'}


def environment(source=None):
    env=dict(os.environ if source is None else source)
    roots=(ROOT,Path(env.get('APPDIR') or ROOT))
    def owned(value):
        return bool(value) and any(Path(value).is_absolute() and Path(value).is_relative_to(root) for root in roots)
    for key in ('PATH','LD_LIBRARY_PATH','LD_PRELOAD','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','PYTHONPATH'):
        if key not in env:continue
        values=re.split(r'[:\s]+',env[key]) if key=='LD_PRELOAD' else env[key].split(os.pathsep)
        if any(owned(value) for value in values):
            values=[value for value in values if not owned(value)]
            if values:env[key]=os.pathsep.join(values)
            else:env.pop(key,None)
    if source is None:
        from . import renderer
        for key,previous in renderer._saved_environment.items():
            if previous is None:env.pop(key,None)
            else:env[key]=previous
    for key in list(env):
        if key in ('APPDIR','APPIMAGE','PYTHONHOME','PYTHONUSERBASE') or key.startswith('VITALUX_'):env.pop(key,None)
    return env


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
