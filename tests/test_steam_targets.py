"""Steam account and installation targeting before any shutdown or edit."""
import json,os,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QCoreApplication
from vitalux import game_files,game_library,game_profiles,game_steam
from vitalux.game_service import GameService
from vitalux.game_sessions import GameSessions

app=QCoreApplication([])
with tempfile.TemporaryDirectory() as folder:
    home=Path(folder)
    native=home/'.local/share/Steam';flat=home/'.var/app/com.valvesoftware.Steam/data/Steam'
    original='"UserLocalConfigStore" { "Software" { "Valve" { "Steam" { "apps" {} } } } }'
    for client in (native,flat):
        (client/'steamapps/common/Test').mkdir(parents=True)
        (client/'steamapps/appmanifest_42.acf').write_text('"AppState" { "appid" "42" "name" "Test" "installdir" "Test" "StateFlags" "4" }')
        config=client/'userdata/123/config/localconfig.vdf';config.parent.mkdir(parents=True);config.write_text(original)
    game=game_library.discover(home=home,config=home/'.config',data=home/'.local/share')[0]
    assert len(game['steam_installations'])==2
    def process(client):
        return SimpleNamespace(info={'name':'steam'},exe=lambda:str(client/'ubuntu12_32/steam'),cwd=lambda:str(client))
    def clients(target):
        return [(process(flat),{})] if target.get('flatpak') else []
    with patch.object(game_steam,'_processes',side_effect=clients):
        selected=game_steam.resolve(game)
    assert selected['flatpak'] and Path(selected['launcher_root'])==flat
    bridge=home/'bridge';bridge.mkdir();(bridge/'launch.sh').write_text('#!/bin/sh\n')
    game_profiles.connect(selected,bridge,check_running=False)
    assert 'launch.sh' in (flat/'userdata/123/config/localconfig.vdf').read_text()
    assert (native/'userdata/123/config/localconfig.vdf').read_text()==original
    catalog=GameSessions(home/'inventory')
    catalog.register(selected,bridge);catalog.update_inventory([game])
    assert catalog.games[game['id']]['flatpak'],'A rescan reverted the connected installation'
    # A stale native connection must not place a Flatpak game's new engine
    # beneath the native bridge directory, which the game cannot access.
    (flat/'userdata/123/config/localconfig.vdf').write_text(original)
    previous=home/'native-bridge';previous.mkdir();(previous/'launch.sh').write_text('#!/bin/sh\n')
    state=home/'worker-state';old=GameSessions(state);old.register(game,previous)
    target=home/'flatpak-bridge';target.mkdir();(target/'launch.sh').write_text('#!/bin/sh\n')
    prepared=[]
    def prepare(chosen,base=None):
        prepared.append((chosen,base));return target
    with patch.object(game_steam,'_processes',side_effect=clients),patch.object(game_steam,'stop_for_setup',return_value=False),patch.object(game_profiles,'prepare',side_effect=prepare):
        worker=GameService(root=state,initial_games=[game]);saved=[];errors=[];catalogs=[]
        worker.profile_saved.connect(saved.append);worker.failed.connect(errors.append)
        worker.catalog_ready.connect(catalogs.append)
        worker.submit('profile',game);worker.start()
        try:
            deadline=time.monotonic()+5
            while not saved and not errors and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
            assert saved and not errors,errors
            assert prepared[0][0]['flatpak'] and prepared[0][1] is None,prepared
            while not any(row.get('flatpak') and row.get('mangohud_available') for row in catalogs[-1]['games']) and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
            assert any(row.get('flatpak') and row.get('mangohud_available') for row in catalogs[-1]['games']),'Lost the bundled engine status after selecting Flatpak'
        finally:worker.shutdown();assert worker.wait(5000)
    with patch.object(game_steam,'_processes',side_effect=lambda target:[(process(flat if target.get('flatpak') else native),{})]):
        try:game_steam.resolve(game)
        except ValueError as error:assert 'gleichzeitig' in str(error)
        else:raise AssertionError('Chose one of two active Steam clients')
    # A known active account must never fall back to somebody else's file.
    (native/'config').mkdir()
    login=native/'config/loginusers.vdf'
    login.write_text('"users" { "76561197960266517" { "MostRecent" "1" } }')
    service=GameService(root=home/'state')
    with patch.object(game_steam,'stop_for_setup') as shutdown:
        try:service._connect(game,bridge)
        except ValueError as error:assert 'aktive Steam-Konto' in str(error)
        else:raise AssertionError('Connected a different Steam account')
        shutdown.assert_not_called()
    assert (native/'userdata/123/config/localconfig.vdf').read_text()==original
    current=native/'userdata/789/config/localconfig.vdf';current.parent.mkdir(parents=True);current.write_text(original)
    assert game_profiles.preflight_steam(game)==current
    game_profiles.connect(game,bridge,check_running=False)
    assert game_profiles.connected(game,bridge)
    record=bridge/'connection.json';data=json.loads(record.read_text());data['path']=str(native/'userdata/123/config/localconfig.vdf');record.write_text(json.dumps(data))
    assert not game_profiles.connected(game,bridge),'Validated a backup from another Steam account'
    assert (native/'userdata/123/config/localconfig.vdf').read_text()==original
print('Active native/Flatpak selection, ambiguous-client refusal, account preflight and exact connection target PASS')
