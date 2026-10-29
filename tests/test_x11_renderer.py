"""X11 preflight selects OpenGL and recovers a failed native driver safely."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux import renderer,settings
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    assert renderer.CHOICES==('software','x11_opengl')
    settings.set_many(dict(render_backend='x11_opengl',gpu_boot_pending=False))
    with patch.dict(os.environ,{'DISPLAY':':42'},clear=True),patch.object(renderer,'_probe',return_value=(True,'')) as probe:
        assert renderer.prepare_start()==renderer.X11_OPENGL
        assert os.environ['QT_QPA_PLATFORM']=='xcb' and os.environ['QSG_RHI_BACKEND']=='opengl'
        probe.assert_called_once();renderer.successful_start();renderer._restore_environment()
        assert 'QT_QPA_PLATFORM' not in os.environ
    for env,reason in (({},''),({'DISPLAY':':42'},'SIGABRT 134')):
        settings.set_many(dict(render_backend='x11_opengl',gpu_boot_pending=False))
        with patch.dict(os.environ,env,clear=True),patch.object(renderer,'_probe',return_value=(False,reason)):
            assert renderer.prepare_start()=='software'
            assert settings.get('render_backend')=='software' and not settings.get('gpu_boot_pending')
    settings.set_many(dict(render_backend='x11_opengl',gpu_boot_pending=True))
    with patch.dict(os.environ,{'DISPLAY':':42'},clear=True):assert renderer.prepare_start()=='software'
print('X11 selection, process-isolated OpenGL preflight and CPU rollback PASS')
