"""Keep the app's private libraries out of external system/launcher commands."""
import os
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def host_environment(source=None):
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
    # These identify the launching app, not the desktop session. Forwarding
    # Vitalux's identity to Steam/URI handlers can reactivate Vitalux instead.
    origin=('APPDIR','APPIMAGE','APPIMAGE_UUID','TARGET_APPIMAGE','ARGV0','OWD',
            'PYTHONHOME','PYTHONUSERBASE','GIO_LAUNCHED_DESKTOP_FILE',
            'GIO_LAUNCHED_DESKTOP_FILE_PID','BAMF_DESKTOP_FILE_HINT',
            'DESKTOP_STARTUP_ID','XDG_ACTIVATION_TOKEN')
    for key in list(env):
        if key in origin or key.startswith('VITALUX_'):env.pop(key,None)
    return env

