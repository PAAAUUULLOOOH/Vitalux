"""An enabled profile establishes a real launcher link; busy launchers stay intact."""
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QCoreApplication
from vitalux import game_files,game_profiles,profiles,settings
from vitalux.game_service import GameService

app=QCoreApplication([])
def wait(predicate):
    end=time.monotonic()+5
    while not predicate() and time.monotonic()<end:app.processEvents();time.sleep(.005)
    assert predicate(),'Game service did not settle'

with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary);steam=root/'Steam'
    config=steam/'userdata/123/config/localconfig.vdf';config.parent.mkdir(parents=True)
    original='"UserLocalConfigStore" { "Software" { "Valve" { "Steam" { "apps" { "42" { "LaunchOptions" "-novid" } } } } } }\n'
    config.write_text(original)
    game=dict(id='steam:42',appid='42',store='steam',name='Test',launcher_root=str(steam),flatpak=False)
    with patch.object(settings,'PATH',str(root/'settings.json')),patch.object(profiles,'directory',lambda kind:root/kind),patch.object(game_profiles,'launcher_running',return_value=False) as busy:
        service=GameService(root=root/'sessions',initial_games=[game]);catalog=[];errors=[];launches=[]
        service.catalog_ready.connect(catalog.append);service.failed.connect(errors.append)
        service.launch_ready.connect(launches.append)
        service.start()
        try:
            wait(lambda:catalog and any(g['id']==game['id'] for g in catalog[-1]['games']))
            assert config.read_text()==original,'Discovery changed launch options'
            busy.return_value=True
            service.submit('profile',game);wait(lambda:bool(errors))
            assert config.read_text()==original,'Saving edited a running launcher'
            busy.return_value=False;errors.clear()
            service.submit('profile',game)
            wait(lambda:any(g.get('connected') for g in catalog[-1]['games']))
            assert not errors and 'launch.sh' in config.read_text()
            linked=config.read_text()
            busy.return_value=True
            service.submit('launch',game);wait(lambda:bool(launches))
            assert launches[-1]['id']==game['id'] and config.read_text()==linked
            # An old backup file cannot validate a removed launcher prefix.
            config.write_text(original);launches.clear()
            service.submit('launch',game);wait(lambda:bool(errors))
            assert not launches and config.read_text()==original
            wait(lambda:not any(g.get('connected') for g in catalog[-1]['games']))
            busy.return_value=False;errors.clear()
            service.submit('launch',game);wait(lambda:bool(launches))
            assert not errors and config.read_text()==linked
            game_profiles.save(game['id'],dict(enabled=False));service.submit('profile',game)
            wait(lambda:any(g.get('connected') and not g.get('overlay_enabled') for g in catalog[-1]['games']))
            assert config.read_text()==linked,'Disabling lost the reversible launcher connection'
            service.submit('disconnect',game)
            wait(lambda:not any(g.get('connected') for g in catalog[-1]['games']))
            assert config.read_text()==original
        finally:
            service.shutdown();assert service.wait(5000)
print('Discovery is read-only; enabled profile connects, busy-launcher guard, disable and disconnect PASS')
