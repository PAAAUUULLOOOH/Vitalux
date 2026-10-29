"""Read Steam's account metadata without depending on the retired MostRecent key."""
from pathlib import Path
from . import game_files


def _registry_paths(game,root):
    paths=[root/'registry.vdf',root/'config/registry.vdf']
    home=Path.home()
    if game.get('flatpak'):
        paths.append(home/'.var/app/com.valvesoftware.Steam/.steam/registry.vdf')
    else:
        known=(home/'.local/share/Steam',home/'.steam/steam',home/'.steam/root')
        if any(path.resolve()==root.resolve() for path in known):paths.append(home/'.steam/registry.vdf')
    if root.parent.name=='.steam':paths.append(root.parent/'registry.vdf')
    return dict.fromkeys(paths)


def _steam_registry(game,root):
    for path in _registry_paths(game,root):
        try:
            value=game_files.loads(game_files.read_text(path))
            for key in ('Registry','HKCU','Software','Valve','Steam'):
                value=game_files.get(value,key,{}) if isinstance(value,dict) else {}
            if isinstance(value,dict) and value:yield value
        except FileNotFoundError:continue
        except (OSError,ValueError):continue


def _id(value):
    text=str(value)
    if not text.isdecimal() or len(text)>20:return ''
    number=int(text)&0xffffffff
    return str(number) if number else ''


def config_path(game):
    root=Path(game['launcher_root'])
    try:
        users=game_files.get(game_files.loads(game_files.read_text(root/'config/loginusers.vdf')),'users',{})
        if not isinstance(users,dict):raise ValueError('Invalid Steam account table')
    except FileNotFoundError:users={}
    except (OSError,ValueError,AttributeError) as error:
        raise ValueError('Das aktive Steam-Konto konnte nicht gelesen werden. Bitte prüfe die Steam-Kontodaten und versuche es erneut.') from error
    rows=[(account,row) for key,row in users.items() if isinstance(row,dict) and (account:=_id(key))]
    account=''
    # Current Linux clients identify the selected account by name in registry.vdf.
    for registry in _steam_registry(game,root):
        name=str(game_files.get(registry,'AutoLoginUser','')).casefold()
        matching={key for key,row in rows if name and str(game_files.get(row,'AccountName','')).casefold()==name}
        if len(matching)==1:account=matching.pop();break
        active=game_files.get(registry,'ActiveProcess',{})
        if isinstance(active,dict):account=_id(game_files.get(active,'ActiveUser',''))
        if account:break
    if not account:
        for flag in ('AutoLogin','MostRecent'):
            selected={key for key,row in rows if str(game_files.get(row,flag,'0')).casefold() in ('1','true')}
            if len(selected)==1:account=selected.pop();break
    if not account:
        stamps=[]
        for key,row in rows:
            stamp=str(game_files.get(row,'Timestamp','0'))
            if stamp.isdecimal() and len(stamp)<=20 and int(stamp)>0:stamps.append((int(stamp),key))
        if stamps:
            latest=max(stamp for stamp,_ in stamps)
            selected={key for stamp,key in stamps if stamp==latest}
            if len(selected)==1:account=selected.pop()
    candidates=[path for path in (root/'userdata').glob('*/config/localconfig.vdf')
                if path.parent.parent.name.isdecimal() and int(path.parent.parent.name)>0]
    if account:
        selected=root/'userdata'/account/'config/localconfig.vdf'
        if selected in candidates:return selected
        raise ValueError('Für das aktive Steam-Konto fehlen die Spieleinstellungen. Bitte starte das Spiel einmal direkt über Steam.')
    if len(candidates)==1:return candidates[0]
    raise ValueError('Das aktive Steam-Konto konnte aus den Steam-Kontodaten nicht sicher bestimmt werden. Bitte wähle das gewünschte Konto in Steam und versuche es erneut.')
