"""Explicit reversible launcher setup and an argv-safe portable game wrapper."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitalux import game_files, game_profiles as overlay, settings

with tempfile.TemporaryDirectory(prefix='vitalux-games-') as directory:
    root = Path(directory)
    steam = root/'Steam'
    configuration = steam/'userdata/123/config/localconfig.vdf'
    configuration.parent.mkdir(parents=True)
    source = '// preserve me\n"UserLocalConfigStore" { "Software" { "Valve" { "Steam" { "apps" { "42" { "LaunchOptions" "gamemoderun %command% -novid" "other" "unchanged" } } } } } }\n'
    configuration.write_text(source)
    game = dict(id='steam:42', store='steam', appid='42', name='Test', launcher_root=str(steam), flatpak=False)
    with patch.object(settings,'PATH',str(root/'settings.json')):
        profile = overlay.save(game['id'], dict(target_fps=120, position='bottom-right'))
        bridge = overlay.prepare(game, profile, root/"Game's data")
        assert 'log_interval=0' in (bridge/'profile.conf').read_text()
        assert 'autostart_log=5' in (bridge/'profile.conf').read_text()
        assert overlay.load(game['id'])['target_fps']==120
        with patch.object(overlay,'launcher_running',return_value=True):
            try:overlay.connect(game,bridge)
            except ValueError:pass
            else:raise AssertionError('Changed a running Steam configuration')
        assert configuration.read_text()==source
        connection = overlay.connect(game,bridge,check_running=False)
        changed = configuration.read_text()
        assert '// preserve me' in changed and '"other" "unchanged"' in changed
        assert 'gamemoderun' in connection['applied'] and '-novid' in connection['applied']
        assert connection['applied'].count('%command%')==1
        assert overlay.connect(game,bridge,check_running=False)==connection
        # User changes made after connecting survive removal of our own prefix.
        configuration.write_text(game_files.set_string(changed, connection['keys'], connection['applied']+' -new'))
        overlay.disconnect(game,bridge,check_running=False)
        data=game_files.loads(configuration.read_text())
        assert data['UserLocalConfigStore']['Software']['Valve']['Steam']['apps']['42']['LaunchOptions']=='gamemoderun %command% -novid -new'
        assert not (bridge/'connection.json').exists()
        # Plain Steam arguments have an implicit command; keep those arguments.
        configuration.write_text(source.replace('gamemoderun %command% -novid','-novid'))
        connection=overlay.connect(game,bridge,check_running=False)
        assert connection['applied'].endswith('%command% -novid')
        overlay.disconnect(game,bridge,check_running=False)
        assert configuration.read_text()==source.replace('gamemoderun %command% -novid','-novid')
        # A deliberately unusable host command must not be used by the real wrapper.
        binary = root/'bin';binary.mkdir()
        executable = binary/'mangohud';executable.write_text('#!/bin/sh\necho SYSTEM_MANGOHUD_MUST_NOT_BE_USED >&2\nexit 97\n');executable.chmod(0o755)
        bridge = overlay.prepare(game, profile, root/"Game's data")
        payload = 'literal; echo unintended'
        env=dict(os.environ,PATH=str(binary)+':'+os.defpath)
        command=[str(bridge/'launch.sh'),'/bin/sh','-c','printf "%s" "$1" > "$2"; exit 7','game',payload,str(root/'argument.txt')]
        completed=subprocess.run(command,env=env,capture_output=True,text=True,timeout=10)
        assert completed.returncode==7,completed.stderr
        assert 'SYSTEM_MANGOHUD_MUST_NOT_BE_USED' not in completed.stderr
        assert overlay.available(game)
        assert (root/'argument.txt').read_text()==payload
        sessions=list((bridge/'sessions').iterdir());assert len(sessions)==1
        assert (sessions[0]/'exit-code').read_text().strip()=='7'
        assert 'output_folder='+str(sessions[0]) in (sessions[0]/'overlay.conf').read_text()
        assert json.loads((sessions[0]/'game.json').read_text())['game']['id']==game['id']
        assert (sessions[0]/'owner.pid').read_text().strip().isdecimal()
        # An inactive connection launches the original command normally.
        (bridge/'enabled').unlink()
        assert subprocess.run([str(bridge/'launch.sh'),'/bin/true'],env=env,timeout=5).returncode==0
        assert len(list((bridge/'sessions').iterdir()))==1
        # Heroic's own wrapper list and unrelated settings remain intact.
        heroic = root/'heroic';(heroic/'GamesConfig').mkdir(parents=True)
        hgame=dict(id='heroic-legendary:abc',store='heroic',appid='abc',name='Epic',launcher_root=str(heroic))
        hpath=heroic/'GamesConfig/abc.json'
        original={'abc':dict(wrapperOptions=[dict(exe='gamemoderun',args='')],enviromentOptions=[dict(key='EXISTING',value='keep')],winePrefix='/prefix')}
        hpath.write_text(json.dumps(original))
        hbridge=overlay.prepare(hgame,base=root/'bridges')
        overlay.connect(hgame,hbridge,check_running=False)
        linked=json.loads(hpath.read_text());assert linked['abc']['wrapperOptions'][0]['exe']==str(hbridge/'launch.sh')
        assert linked['abc']['enviromentOptions']==original['abc']['enviromentOptions']
        overlay.disconnect(hgame,hbridge,check_running=False)
        assert json.loads(hpath.read_text())==original
        # Lutris config is edited at one scalar, preserving its other lines.
        lpath=root/'lutris.yml';ltxt='game:\n  exe: /a/game.exe\nsystem:\n  prefix_command: gamemoderun\n  env:\n    KEEP: yes\nwine:\n  version: default\n';lpath.write_text(ltxt)
        lgame=dict(id='lutris:7',store='lutris',appid='7',name='Lutris',config_file=str(lpath))
        lbridge=overlay.prepare(lgame,base=root/'bridges');overlay.connect(lgame,lbridge,check_running=False)
        assert '    KEEP: yes\nwine:\n' in lpath.read_text()
        assert overlay._yaml_prefix(lpath.read_text())[0].endswith('gamemoderun')
        overlay.disconnect(lgame,lbridge,check_running=False)
        assert overlay._yaml_prefix(lpath.read_text())[0]=='gamemoderun'
        assert '    KEEP: yes\nwine:\n' in lpath.read_text()
        # Damaged preferences cannot inject arbitrary configuration lines.
        clean=overlay.normalize(dict(target_fps=float('nan'),position='top-left\noutput_folder=/bad',toggle_hud='bad\nkey'))
        assert clean['target_fps']==60 and clean['position']=='top-left'
print('Reversible Steam/Heroic/Lutris setup, preserved launch arguments, running-launcher guard and real shell wrapper lifecycle PASS')

# A completed launcher child must not prevent connecting the next game.
from types import SimpleNamespace
import psutil
uid=SimpleNamespace(real=os.getuid())
with patch.object(psutil,'process_iter',return_value=[SimpleNamespace(info=dict(name='steam',uids=uid,status=psutil.STATUS_ZOMBIE))]):
    assert not overlay.launcher_running('steam')
with patch.object(psutil,'process_iter',return_value=[SimpleNamespace(info=dict(name='steam',uids=uid,status=psutil.STATUS_RUNNING))]):
    assert overlay.launcher_running('steam')
