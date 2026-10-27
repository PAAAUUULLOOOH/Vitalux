"""Installed games are discovered locally; launcher edits preserve other data."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitalux import game_files as files
from vitalux.game_library import discover


with tempfile.TemporaryDirectory() as folder:
    home = Path(folder)
    steam = home/'.local/share/Steam'
    library = home/'Other library'
    (steam/'steamapps').mkdir(parents=True)
    (library/'steamapps/common/Example Game').mkdir(parents=True)
    (steam/'steamapps/libraryfolders.vdf').write_text(
        '"libraryfolders" { "0" { "path" '+files.quote(str(library))+' } }')
    manifest = library/'steamapps/appmanifest_42.acf'
    manifest.write_text('"AppState" { "appid" "42" "name" "Example Game" '
                        '"installdir" "Example Game" "StateFlags" "4" }')
    (library/'steamapps/appmanifest_43.acf').write_text(
        '"AppState" { "appid" "43" "name" "Proton Experimental" '
        '"installdir" "Example Game" "StateFlags" "4" }')
    (library/'steamapps/appmanifest_44.acf').write_text(
        '"AppState" { "appid" "44" "name" "Unfinished" '
        '"installdir" "Example Game" "StateFlags" "2" }')
    config, data = home/'.config', home/'.local/share'
    heroic = config/'heroic'
    source = heroic/'legendaryConfig/legendary/installed.json'
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({'EpicGame': dict(title='Epic Example', install_path=str(library))}))
    lutris = data/'lutris'
    lutris.mkdir()
    with sqlite3.connect(lutris/'pga.db') as database:
        database.execute('CREATE TABLE games(id INTEGER, name TEXT, directory TEXT, installed INTEGER, slug TEXT, configpath TEXT)')
        database.execute('INSERT INTO games VALUES(?,?,?,?,?,?)', (7, 'Lutris Example', str(library), 1, 'example', 'example-123'))
    before = {p: p.read_bytes() for p in home.rglob('*') if p.is_file()}
    games = discover(home, config, data)
    assert {game['id'] for game in games} == {'steam:42', 'heroic-legendary:EpicGame', 'lutris:7'}, games
    assert all(game['installed'] and Path(game['install_path']).is_dir() for game in games)
    assert before == {p: p.read_bytes() for p in before}, 'Discovery changed launcher files'
    assert next(game for game in games if game['store']=='steam')['name']=='Example Game'
    # A missing library or uninstalled manifest is not an installed game.
    manifest.unlink()
    assert 'steam:42' not in {game['id'] for game in discover(home, config, data)}
    # Flatpak Steam uses the same manifest format and retains its provenance.
    flatpak = home/'.var/app/com.valvesoftware.Steam/.local/share/Steam'
    (flatpak/'steamapps/common/Flat Game').mkdir(parents=True)
    (flatpak/'steamapps/appmanifest_77.acf').write_text(
        '"AppState" { "appid" "77" "name" "Flat Game" "installdir" "Flat Game" "StateFlags" "4" }')
    assert next(game for game in discover(home, config, data) if game['id']=='steam:77')['flatpak']

text = '// untouched comment\r\n"Root" { "Other" "unchanged" "Apps" { "42" { "LaunchOptions" "gamemoderun %command% -x" } } }\r\n'
updated = files.set_string(text, ('root', 'apps', '42', 'launchoptions'), 'wrapper %command% -x')
assert updated == text.replace('gamemoderun %command% -x', 'wrapper %command% -x')
added = files.set_string(text, ('Root', 'Apps', '84', 'LaunchOptions'), 'new %command%')
assert '// untouched comment\r\n' in added
assert files.loads(added)['Root']['Apps']['84']['LaunchOptions']=='new %command%'
assert files.loads(added)['Root']['Apps']['42']['LaunchOptions']=='gamemoderun %command% -x'
for bad in ('"root" {', '"root"', '}', '"root" { "key" }'):
    try:
        files.loads(bad)
    except ValueError:
        pass
    else:
        raise AssertionError('Accepted broken Valve metadata: '+bad)
try:
    files.set_string('"root" { "A" "one" "a" "two" }', ('root','a'), 'replace')
except ValueError:
    pass
else:
    raise AssertionError('Ambiguous duplicate key was overwritten')
print('Read-only Steam/Flatpak/Heroic/Lutris discovery, installed-state checks and lossless bounded VDF edits PASS')
