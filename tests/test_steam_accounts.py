"""Modern Steam account metadata works without MostRecent or numeric ActiveUser."""
import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux.game_steam_accounts import config_path
from vitalux import game_files
with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);(root/'config').mkdir()
    for account in ('0','123','456'):
        path=root/'userdata'/account/'config/localconfig.vdf';path.parent.mkdir(parents=True);path.write_text('"UserLocalConfigStore" {}')
    game=dict(launcher_root=str(root),flatpak=False)
    def users(a='',b=''):
        (root/'config/loginusers.vdf').write_text('"users" { "76561197960265851" { "AccountName" "alpha" '+a+' } "76561197960266184" { "AccountName" "beta" '+b+' } }')
    users('"AutoLogin" "0"','"AutoLogin" "1"')
    assert config_path(game).parent.parent.name=='456'
    registry=root/'registry.vdf'
    registry.write_text('"Registry" { "HKCU" { "Software" { "Valve" { "Steam" { "AutoLoginUser" "ALPHA" } } } } }')
    assert config_path(game).parent.parent.name=='123'
    registry.write_text('"Registry" { "HKCU" { "Software" { "Valve" { "Steam" { "ActiveProcess" { "ActiveUser" "456" } } } } } }')
    assert config_path(game).parent.parent.name=='456'
    registry.unlink();users('"timestamp" "200"','"timestamp" "100"')
    assert config_path(game).parent.parent.name=='123'
    users('"timestamp" "200"','"timestamp" "200"')
    try:config_path(game)
    except ValueError:pass
    else:raise AssertionError('Guessed an account from tied timestamps')
    (root/'userdata/456/config/localconfig.vdf').unlink();(root/'config/loginusers.vdf').unlink()
    assert config_path(game).parent.parent.name=='123','Shared userdata/0 is not a signed-in account'
print('Registry account name, AutoLogin, timestamps, legacy ActiveUser and shared-folder exclusion PASS')
