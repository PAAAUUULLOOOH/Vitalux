"""First-use copying is separate from reset, including the actual guide gate."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QWidget
from vitalux import profiles,settings,guide

app=QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory(prefix='vitalux-profile-reset-') as d,patch.dict(os.environ,{f'XDG_{kind.upper()}_HOME':str(Path(d)/kind) for kind in profiles.KINDS}):
    stable=profiles.directory('config','stable')/'settings.json'
    profiles.atomic_json(stable,dict(theme='glass',lang='de',guide_intro_choice='completed',accent='#123456'))
    original=stable.read_bytes()
    with patch.object(profiles,'__version__','0.9.6.3-unstable.2'):
        profiles.initialize();path=profiles.directory('config')/'settings.json'
        assert profiles.read(path)['theme']=='glass'
        resources=path.parent/'backgrounds';resources.mkdir();(resources/'keep.png').write_bytes(b'owned image')
        with patch.object(settings,'PATH',str(path)):
            parent=QWidget()
            for _ in range(3):
                settings.set_many(dict(theme='light',guide_intro_choice='completed'))
                assert profiles.reset_preferences(path)
                assert path.exists(),'Older builds must also see an existing reset profile'
                profiles.initialize()
                assert settings.get('theme') is None and settings.get('accent') is None
                assert settings.get('guide_intro_choice') is None
                with patch.object(guide.GuideDialog,'exec',return_value=1) as opened:
                    guide.offer_first_start_guide(parent);opened.assert_called_once()
                    assert settings.get('guide_intro_choice')=='completed'
                    guide.offer_first_start_guide(parent);assert opened.call_count==1
                assert stable.read_bytes()==original
            profiles.reset_preferences(path)
            parent._shutdown_pending=True
            with patch.object(guide.GuideDialog,'exec') as opened:
                guide.offer_first_start_guide(parent);opened.assert_not_called()
                assert settings.get('guide_intro_choice') is None
            path.unlink();profiles.initialize()
            assert settings.get('theme') is None,'Missing settings reimported Stable after initialization'
        assert (resources/'keep.png').read_bytes()==b'owned image'
        assert stable.read_bytes()==original
    with patch.object(profiles,'__version__','0.9.6.2'):
        profiles.reset_preferences(stable);profiles.initialize()
        assert profiles.read(stable).get('guide_intro_choice') is None
print('First-use copy, repeated Stable/Unstable reset, guide gate, shutdown guard and profile isolation PASS')
